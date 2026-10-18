"""
Embedded RAG Service for Scientific Document Analysis (Phase 2B / Step 4).
Provides:
  - Local dense embedding generation via SentenceTransformer (champion intfloat/e5-small-v2)
    with FastEmbed fallback for non-e5 models.
  - Embedded local vector store indexing via Qdrant (in-memory or persistent SQLite exact search)
  - Dense cosine similarity retrieval with document-level metadata filtering
  - Equal Token Budget accumulation
  - Hybrid lexical-dense Reciprocal Rank Fusion (RRF) with collision-free chunk identifiers

Task 1D Infrastructure Finding:
  - In local embedded mode (QdrantClient(path=...)), Qdrant takes an exclusive SQLite file lock
    on the storage folder (settings.QDRANT_STORAGE_PATH).
  - In development, Django runserver autoreloader spawns two processes (monitor + worker), but only
    the worker serving requests or running background tasks initializes RagService.get_instance().
  - Caution: If an external CLI script, Celery worker, or multi-worker WSGI server accesses the same
    folder concurrently while the Django server holds an open client instance, Qdrant will raise
    a storage lock collision error. For multi-process deployments, a dedicated Qdrant server instance
    (via QdrantClient(url=...)) or in-process queue ownership is required.
"""

import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from .chunking_utils import estimate_tokens

logger = logging.getLogger(__name__)

# Model dimension mapping
MODEL_DIMENSIONS = {
    "intfloat/e5-small-v2": 384,
    "BAAI/bge-small-en-v1.5": 384,
    "all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
}


class RagService:
    """
    Modular in-process RAG Service powering semantic search and QA over academic PDFs.
    Step 4 Production Implementation with champion model intfloat/e5-small-v2.
    """

    _instance: Optional["RagService"] = None

    def __init__(
        self,
        storage_path: Optional[str] = None,
        embedding_model_name: Optional[str] = None,
        in_memory: bool = False,
        mode: Optional[str] = None,
        server_url: Optional[str] = None,
        prefer_grpc: Optional[bool] = None,
    ) -> None:
        self.in_memory = in_memory
        q_mode = mode or getattr(settings, "QDRANT_MODE", "local")

        if in_memory:
            self.client = QdrantClient(location=":memory:")
        elif q_mode == "server":
            url = server_url or getattr(settings, "QDRANT_URL", "http://localhost:6333")
            grpc = prefer_grpc if prefer_grpc is not None else getattr(settings, "QDRANT_PREFER_GRPC", False)
            grpc_port = getattr(settings, "QDRANT_GRPC_PORT", 6334)
            logger.info("Initializing QdrantClient in SERVER mode at %s (prefer_grpc=%s)", url, grpc)
            self.client = QdrantClient(url=url, prefer_grpc=grpc, grpc_port=grpc_port)
        else:
            path = storage_path or getattr(settings, "QDRANT_STORAGE_PATH", "media/qdrant_db")
            os.makedirs(path, exist_ok=True)
            self.client = QdrantClient(path=path)

        self.model_name = embedding_model_name or getattr(settings, "EMBEDDING_MODEL", "intfloat/e5-small-v2")
        self.vector_dim = MODEL_DIMENSIONS.get(self.model_name, 384)
        self._embedder: Any = None
        self._is_st_model: bool = False

    @property
    def embedder(self) -> Any:
        """Lazy-loaded model instance (SentenceTransformer for e5/MiniLM or FastEmbed)."""
        if self._embedder is None:
            if "e5" in self.model_name or "sentence-transformers" in self.model_name:
                try:
                    from sentence_transformers import SentenceTransformer
                    logger.info("Initializing SentenceTransformer embedding model: %s", self.model_name)
                    self._embedder = SentenceTransformer(self.model_name)
                    self._is_st_model = True
                except Exception as e:
                    logger.error("Failed to load SentenceTransformer for %s: %s", self.model_name, e)
                    raise RuntimeError(
                        f"Cannot load required embedding model '{self.model_name}'. "
                        f"SentenceTransformer failed with: {e}. "
                        "Aborting to prevent silent embedding space corruption."
                    )
            else:
                logger.info("Initializing FastEmbed text embedding model: %s", self.model_name)
                from fastembed import TextEmbedding
                self._embedder = TextEmbedding(model_name=self.model_name)
                self._is_st_model = False
        return self._embedder

    def _embed_texts(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        """
        Embeds texts with proper model-specific asymmetrical prefixing and normalization.
        e5-small-v2 requires 'passage: ' for documents and 'query: ' for queries.
        """
        if not texts:
            return []

        if "e5" in self.model_name:
            prefix = "query: " if is_query else "passage: "
            formatted_texts = [prefix + t for t in texts]
        elif "bge" in self.model_name and is_query:
            formatted_texts = ["Represent this sentence for searching relevant passages: " + t for t in texts]
        else:
            formatted_texts = texts

        embedder_inst = self.embedder
        if self._is_st_model:
            embs = embedder_inst.encode(formatted_texts, normalize_embeddings=True, show_progress_bar=False)
            return [v.tolist() for v in embs]
        else:
            return [v.tolist() for v in embedder_inst.embed(formatted_texts)]

    @classmethod
    def get_instance(cls) -> "RagService":
        """Singleton accessor for shared Django application lifecycle."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def ensure_collection(self, collection_name: str) -> None:
        """
        Creates collection if it does not already exist.
        In Qdrant local embedded mode, storage is SQLite/exact brute-force by design.
        HNSW parameters are omitted to reflect embedded exact search semantics.
        """
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self.vector_dim,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            # Create payload indices (note: payload indices are documented for server Qdrant;
            # in local mode Qdrant performs in-process linear payload filtering)
            try:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="paper_arxiv_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="document_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
            except Exception as e:
                logger.debug("Payload index creation note: %s", e)

    def index_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        recreate: bool = False,
    ) -> int:
        """
        Embeds a list of text chunks and indexes them into Qdrant.
        Each chunk is required to have 'text' and at least one of 'document_id' or 'paper_arxiv_id'.
        Point IDs are deterministic across document and chunk IDs to guarantee cross-document
        isolation and re-indexing idempotency.
        """
        if recreate and self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)

        self.ensure_collection(collection_name)
        if not chunks:
            return 0

        # Extract texts for batch embedding with passage prefix
        texts = [c.get("text", "") for c in chunks]
        embeddings = self._embed_texts(texts, is_query=False)

        points: List[qmodels.PointStruct] = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            chunk_text = chunk.get("text", "")

            # Task 1A: Validate document identifier
            doc_ident = chunk.get("document_id") or chunk.get("paper_arxiv_id")
            if not doc_ident:
                raise ValueError(
                    f"Chunk at index {idx} has neither 'document_id' nor 'paper_arxiv_id'. "
                    f"Chunk snippet: {chunk_text[:60]!r}"
                )
            doc_ident_str = str(doc_ident)
            chunk_id = chunk.get("chunk_id", idx)

            # Task 1B: Fallback to 'page' when 'page_start' is absent
            page_start = chunk.get("page_start", chunk.get("page", 1))
            page_end = chunk.get("page_end", page_start)

            payload = {
                "chunk_id": chunk_id,
                "document_id": str(chunk.get("document_id", "")),
                "text": chunk_text,
                "section": chunk.get("section", ""),
                "page_start": page_start,
                "page_end": page_end,
                "token_count": chunk.get("token_count", estimate_tokens(chunk_text)),
                "paper_arxiv_id": str(chunk.get("paper_arxiv_id", "")),
                "paper_title": chunk.get("paper_title", ""),
            }

            # Task 1A: Deterministic, idempotent UUID without idx
            pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{collection_name}::{doc_ident_str}::{chunk_id}"))
            points.append(
                qmodels.PointStruct(
                    id=pt_id,
                    vector=vector,
                    payload=payload,
                )
            )

        # Batch upsert points
        self.client.upsert(collection_name=collection_name, points=points)
        logger.info("Successfully indexed %d chunks into collection '%s'", len(points), collection_name)
        return len(points)

    def search_dense(
        self,
        collection_name: str,
        query: str,
        top_k: int = 10,
        score_threshold: Optional[float] = None,
        filter_arxiv_id: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        preprocess_mode: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Performs dense semantic vector search with cosine distance and optional payload filtering.
        In local embedded mode, Qdrant executes exact cosine scanning.
        Returns list of (score, payload_dict).
        """
        if not self.client.collection_exists(collection_name):
            return []

        if preprocess_mode:
            from .query_processing import preprocess_query
            query = preprocess_query(query, mode=preprocess_mode)

        query_vectors = self._embed_texts([query], is_query=True)
        if not query_vectors:
            return []
        q_vector = query_vectors[0]

        must_filters = []
        if filter_arxiv_id:
            must_filters.append(qmodels.FieldCondition(key="paper_arxiv_id", match=qmodels.MatchValue(value=filter_arxiv_id)))
        if filter_document_id:
            must_filters.append(qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=str(filter_document_id))))

        query_filter = qmodels.Filter(must=must_filters) if must_filters else None

        search_result = self.client.query_points(
            collection_name=collection_name,
            query=q_vector,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold,
        )

        results: List[Tuple[float, Dict[str, Any]]] = []
        for hit in search_result.points:
            payload = hit.payload or {}
            payload["_point_id"] = str(hit.id)
            results.append((float(hit.score), payload))
        return results

    def search_dense_with_token_budget(
        self,
        collection_name: str,
        query: str,
        token_budget: int = 1500,
        candidate_pool: int = 25,
        filter_arxiv_id: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        preprocess_mode: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Retrieves top candidate chunks and accumulates them until the prompt token budget is filled.
        Guarantees scientific parity across differing chunk sizes and supports document scoping.
        """
        candidates = self.search_dense(
            collection_name=collection_name,
            query=query,
            top_k=candidate_pool,
            filter_arxiv_id=filter_arxiv_id,
            filter_document_id=filter_document_id,
            preprocess_mode=preprocess_mode,
        )
        accumulated: List[Tuple[float, Dict[str, Any]]] = []
        current_tokens = 0

        for score, payload in candidates:
            tok = payload.get("token_count", estimate_tokens(payload.get("text", "")))
            if current_tokens + tok > token_budget and accumulated:
                break
            accumulated.append((score, payload))
            current_tokens += tok

        return accumulated

    def search_hybrid_rrf(
        self,
        collection_name: str,
        query: str,
        bm25_candidates: List[Tuple[float, Dict[str, Any]]],
        top_k: int = 5,
        rrf_k: int = 60,
        filter_arxiv_id: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        preprocess_mode: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Hybrid Reciprocal Rank Fusion combining lexical BM25 and dense embeddings.
        RRF Score = 1 / (k + rank_bm25) + 1 / (k + rank_dense)
        Chunks are keyed by globally unique identifiers (doc_id + chunk_id) to prevent multi-document collisions.
        """
        dense_candidates = self.search_dense(
            collection_name=collection_name,
            query=query,
            top_k=top_k * 2,
            filter_arxiv_id=filter_arxiv_id,
            filter_document_id=filter_document_id,
            preprocess_mode=preprocess_mode,
        )

        scores: Dict[str, float] = {}
        payload_map: Dict[str, Dict[str, Any]] = {}

        def _get_unique_key(c: Dict[str, Any], default_rank: int) -> str:
            doc_id = c.get("document_id") or c.get("paper_arxiv_id")
            chunk_id = c.get("chunk_id")
            if doc_id and chunk_id is not None:
                return f"{doc_id}::{chunk_id}"
            if c.get("_point_id"):
                return str(c["_point_id"])
            if c.get("id"):
                return str(c["id"])
            raise ValueError(
                f"Cannot generate unique key for chunk without document_id/paper_arxiv_id or point ID: {c}"
            )

        # BM25 ranks
        for rank, (score, c) in enumerate(bm25_candidates):
            uid = _get_unique_key(c, rank)
            payload_map[uid] = c
            scores[uid] = scores.get(uid, 0.0) + (1.0 / (rrf_k + rank + 1))

        # Dense ranks
        for rank, (score, c) in enumerate(dense_candidates):
            uid = _get_unique_key(c, rank)
            if uid not in payload_map:
                payload_map[uid] = c
            scores[uid] = scores.get(uid, 0.0) + (1.0 / (rrf_k + rank + 1))

        sorted_uids = sorted(scores.keys(), key=lambda uid: scores[uid], reverse=True)
        return [(scores[uid], payload_map[uid]) for uid in sorted_uids[:top_k]]
