"""
Embedded RAG Service for Scientific Document Analysis (Phase 2B / Step 4).
Provides:
  - Local dense embedding generation via SentenceTransformer (champion intfloat/e5-small-v2)
    with FastEmbed fallback for non-e5 models.
  - Embedded local vector store indexing via Qdrant (in-memory or persistent SQLite exact search)
  - Dense cosine similarity retrieval with document-level metadata filtering
  - Equal Token Budget accumulation
  - Hybrid lexical-dense Reciprocal Rank Fusion (RRF) with collision-free chunk identifiers
  - Document-level in-memory hybrid search & local Ollama QA / summarization helpers

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

import numpy as np
import requests
from django.conf import settings
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from rank_bm25 import BM25Okapi

from .chunking_utils import chunk_document, estimate_tokens

logger = logging.getLogger(__name__)

# Model dimension mapping
MODEL_DIMENSIONS: Dict[str, int] = {
    "intfloat/e5-small-v2": 384,
    "BAAI/bge-small-en-v1.5": 384,
    "all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "thenlper/gte-small": 384,
    "Snowflake/snowflake-arctic-embed-s": 384,
    "Snowflake/snowflake-arctic-embed-m-v1.5": 768,
    "nomic-ai/nomic-embed-text-v1.5": 768,
    "nomic-ai/modernbert-embed-base": 768,
    "Snowflake/snowflake-arctic-embed-m-v2.0": 768,
    "mixedbread-ai/mxbai-embed-large-v1": 1024,
}

# Centralized model prefix specifications for asymmetric dense embeddings
MODEL_PREFIX_SPECS: Dict[str, Dict[str, str]] = {
    "intfloat/e5-small-v2": {"query": "query: ", "passage": "passage: "},
    "BAAI/bge-small-en-v1.5": {"query": "Represent this sentence for searching relevant passages: ", "passage": ""},
    "sentence-transformers/all-MiniLM-L6-v2": {"query": "", "passage": ""},
    "all-MiniLM-L6-v2": {"query": "", "passage": ""},
    "thenlper/gte-small": {"query": "", "passage": ""},
    "Snowflake/snowflake-arctic-embed-s": {"query": "Represent this sentence for searching relevant passages: ", "passage": ""},
    "Snowflake/snowflake-arctic-embed-m-v1.5": {"query": "Represent this sentence for searching relevant passages: ", "passage": ""},
    "Snowflake/snowflake-arctic-embed-m-v2.0": {"query": "Represent this sentence for searching relevant passages: ", "passage": ""},
    "nomic-ai/nomic-embed-text-v1.5": {"query": "search_query: ", "passage": "search_document: "},
    "nomic-ai/modernbert-embed-base": {"query": "search_query: ", "passage": "search_document: "},
    "mixedbread-ai/mxbai-embed-large-v1": {"query": "Represent this sentence for searching relevant passages: ", "passage": ""},
}


def get_model_prefix(model_name: str, is_query: bool = False) -> str:
    """
    Returns model-specific prefix for query or passage/document embedding.
    Centralized mapping preventing silent representation space corruption.
    """
    for key, spec in MODEL_PREFIX_SPECS.items():
        if key in model_name:
            return spec["query"] if is_query else spec["passage"]
    if "e5" in model_name:
        return "query: " if is_query else "passage: "
    if any(k in model_name for k in ["bge", "arctic", "mxbai"]):
        return "Represent this sentence for searching relevant passages: " if is_query else ""
    if any(k in model_name for k in ["nomic", "modernbert"]):
        return "search_query: " if is_query else "search_document: "
    return ""



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

    def embed(self, text_or_texts: Any, is_query: bool = False) -> Any:
        """
        Public embedding method with centralized asymmetric prefix application.
        Accepts single str or list of str; returns single vector or list of vectors.
        """
        if isinstance(text_or_texts, str):
            res = self._embed_texts([text_or_texts], is_query=is_query)
            return res[0] if res else []
        elif isinstance(text_or_texts, list):
            return self._embed_texts(text_or_texts, is_query=is_query)
        else:
            raise TypeError(f"Expected str or List[str], got {type(text_or_texts)}")

    def _embed_texts(self, texts: List[str], is_query: bool = False) -> List[List[float]]:
        """
        Embeds texts with proper model-specific asymmetrical prefixing and normalization.
        Uses centralized get_model_prefix mapping.
        """
        if not texts:
            return []

        prefix = get_model_prefix(self.model_name, is_query=is_query)
        formatted_texts = [prefix + t if not t.startswith(prefix) else t for t in texts] if prefix else texts

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


# ─────────────────────────────────────────────────────────────────────────────
# Document-Level Local RAG & Ollama Helpers (used by views: chat / summarize)
# ─────────────────────────────────────────────────────────────────────────────

# Global in-memory RAG index cache: doc_id -> DocumentRAG instance
_rag_instances: Dict[int, "DocumentRAG"] = {}

# Shared embedding model instance to avoid re-loading weights for every doc
_shared_embedding_model: Optional[Any] = None


def get_embedding_model() -> Any:
    global _shared_embedding_model
    if _shared_embedding_model is None:
        model_name = getattr(settings, "EMBEDDING_MODEL", "intfloat/e5-small-v2")
        logger.info("Loading SentenceTransformer model: %s", model_name)
        try:
            from sentence_transformers import SentenceTransformer
            _shared_embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            logger.warning("Failed to load %s, falling back to all-MiniLM-L6-v2: %s", model_name, e)
            try:
                from sentence_transformers import SentenceTransformer
                _shared_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                _shared_embedding_model = None
    return _shared_embedding_model


class DocumentRAG:
    """
    RAG engine for a single document combining dense vector embedding + BM25 sparse search
    with Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, document_id: int, documents: List[Document]) -> None:
        self.document_id = document_id
        self.documents = documents
        self.content = [doc.page_content for doc in self.documents]
        self.model_name = getattr(settings, "EMBEDDING_MODEL", "intfloat/e5-small-v2")

        # BM25 setup
        tokenized_corpus = [text.lower().split() for text in self.content]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Dense embedding setup with proper passage prefixing
        self.embedding_model = get_embedding_model()
        if self.content:
            passage_prefix = get_model_prefix(self.model_name, is_query=False)
            formatted_content = [
                passage_prefix + t if passage_prefix and not t.startswith(passage_prefix) else t
                for t in self.content
            ]
            self.embeddings = self.embedding_model.encode(
                formatted_content,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        else:
            self.embeddings = np.array([])

    def embed(self, text: str, is_query: bool = True) -> np.ndarray:
        """
        Embeds a single query or passage string using model-specific asymmetric prefixes.
        Defaults to is_query=True for retrieval similarity searches.
        """
        prefix = get_model_prefix(self.model_name, is_query=is_query)
        formatted_text = prefix + text if prefix and not text.startswith(prefix) else text
        return self.embedding_model.encode(
            [formatted_text], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )[0]

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        if not self.documents or len(self.embeddings) == 0:
            return []

        num_docs = len(self.documents)
        retrieve_k = min(50, num_docs)

        # 1. Dense retrieval
        query_emb = self.embed(query)
        dense_scores = self.embeddings @ query_emb
        dense_top = np.argsort(dense_scores)[::-1][:retrieve_k]

        # 2. Sparse retrieval (BM25)
        bm25_scores = self.bm25.get_scores(query.lower().split())
        bm25_top = np.argsort(bm25_scores)[::-1][:retrieve_k]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {}
        k_const = 60

        for rank, idx in enumerate(dense_top):
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0.0) + 1.0 / (k_const + rank + 1)

        for rank, idx in enumerate(bm25_top):
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0.0) + 1.0 / (k_const + rank + 1)

        ranked_indices = sorted(
            rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True
        )[: min(top_k, num_docs)]

        return [(self.documents[i], float(rrf_scores[i])) for i in ranked_indices]


def get_or_create_rag(doc_id: int, file_path: str) -> Optional[DocumentRAG]:
    """
    Returns existing DocumentRAG instance from cache or creates a new one by chunking.
    """
    if doc_id in _rag_instances:
        return _rag_instances[doc_id]

    if not file_path or not os.path.exists(file_path):
        logger.warning(f"File path missing or invalid for doc {doc_id}: {file_path}")
        return None

    logger.info(f"Indexing document {doc_id} from {file_path}...")
    chunks = chunk_document(file_path)
    if not chunks:
        logger.warning(f"No chunks generated for doc {doc_id}")
        return None

    rag = DocumentRAG(doc_id, chunks)
    _rag_instances[doc_id] = rag

    # Update database status
    try:
        from ..models import Document as DocModel
        DocModel.objects.filter(id=doc_id).update(rag_status="INDEXED")
    except Exception as e:
        logger.warning(f"Failed to update rag_status in DB for doc {doc_id}: {e}")

    return rag


def reindex_document(doc_id: int, file_path: str) -> Optional[DocumentRAG]:
    """
    Clears cache for doc_id and re-runs chunking & embedding.
    """
    if doc_id in _rag_instances:
        del _rag_instances[doc_id]
    return get_or_create_rag(doc_id, file_path)


def _generate_with_ollama(prompt: str, model_name: str, ollama_url: str) -> Optional[str]:
    """Calls Ollama /api/generate and returns response text or None."""
    try:
        timeout = getattr(settings, "OLLAMA_TIMEOUT", 60)
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("response", "").strip()
            return answer if answer else None
    except Exception as e:
        logger.info(f"Ollama offline/failed: {e}")
    return None


def query_document(
    doc_id: int, file_path: str, question: str, doc_title: str = ""
) -> Dict[str, Any]:
    """
    Queries document RAG index, retrieves top chunks, and returns a response structure.
    """
    rag = get_or_create_rag(doc_id, file_path)
    if not rag or not rag.documents:
        return {
            "answer": "No indexed content could be retrieved for this document.",
            "sources": [],
            "model": "Local RAG Engine",
        }

    top_chunks = rag.hybrid_search(question, top_k=5)

    sources = []
    for doc, score in top_chunks:
        page = doc.metadata.get("page", 1)
        chunk_id = doc.metadata.get("chunk_id", f"chunk-p{page}")
        snippet = doc.page_content.strip().replace("\n", " ")
        if len(snippet) > 180:
            snippet = snippet[:180] + "..."
        sources.append({"page": page, "chunk_id": chunk_id, "snippet": snippet})

    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = getattr(settings, "OLLAMA_MODEL", "llama3.2:3b")

    context_str = "\n\n".join(
        f"--- Snippet (Page {doc.metadata.get('page', 1)}, Section: {doc.metadata.get('section', 'Main')}) ---\n{doc.page_content}"
        for doc, _ in top_chunks
    )

    prompt = (
        f'You are a precise academic research assistant reading "{doc_title or "the document"}".\n'
        f"Use ONLY the provided context below to answer the user's question clearly and accurately.\n"
        f"If the answer is not contained in the context, synthesize the most relevant details available.\n\n"
        f"Context:\n{context_str}\n\nQuestion: {question}\n\nAnswer:"
    )

    answer = _generate_with_ollama(prompt, model_name, ollama_url)
    if answer:
        return {"answer": answer, "sources": sources, "model": f"{model_name} (Local RAG)"}

    # Grounded synthesis fallback
    snippets = []
    for doc, _ in top_chunks[:3]:
        sec = doc.metadata.get("section", f"Page {doc.metadata.get('page', 1)}")
        text = doc.page_content.strip().replace("\n", " ")[:250]
        snippets.append(f"- **{sec}**: {text}...")

    fallback_answer = (
        f"Based on retrieved context from **{doc_title or 'the document'}**:\n\n"
        + "\n\n".join(snippets)
    )
    return {"answer": fallback_answer, "sources": sources, "model": "Grounded Hybrid RAG (Local)"}


def summarize_document(
    doc_id: int, file_path: str, doc_title: str = ""
) -> Dict[str, Any]:
    """
    Generates a structured technical summary of the document.
    """
    rag = get_or_create_rag(doc_id, file_path)
    if not rag or not rag.documents:
        return {
            "summary": "No content available to summarize.",
            "sources": [],
            "model": "Local RAG Engine",
        }

    # Select representative chunks: start, quarter, mid, three-quarter, end
    total = len(rag.documents)
    indices = sorted(set([0, total // 4, total // 2, 3 * total // 4, total - 1]))
    rep_chunks = [(rag.documents[i], 1.0) for i in indices]

    sources = []
    for doc, _ in rep_chunks:
        page = doc.metadata.get("page", 1)
        chunk_id = doc.metadata.get("chunk_id", f"summary-p{page}")
        snippet = doc.page_content.strip().replace("\n", " ")
        if len(snippet) > 150:
            snippet = snippet[:150] + "..."
        sources.append({"page": page, "chunk_id": chunk_id, "snippet": snippet})

    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = getattr(settings, "OLLAMA_MODEL", "llama3.2:3b")

    context_str = "\n\n".join(doc.page_content for doc, _ in rep_chunks)
    prompt = (
        f'Summarize the document "{doc_title or "Selected Paper"}" into 3 clear markdown sections:\n'
        f"### 1. Problem Statement\n### 2. Proposed Architecture & Methodology\n### 3. Empirical Results & Findings\n\n"
        f"Document Excerpts:\n{context_str}\n\nSummary:"
    )

    summary = _generate_with_ollama(prompt, model_name, ollama_url)
    if summary:
        return {"summary": summary, "sources": sources, "model": f"{model_name} (Local RAG)"}

    # Grounded fallback
    doc_name = doc_title or "this document"
    first = rag.documents[0].page_content.strip().replace("\n", " ")[:300]
    mid = rag.documents[total // 2].page_content.strip().replace("\n", " ")[:300]
    last = rag.documents[-1].page_content.strip().replace("\n", " ")[:300]

    fallback = (
        f"### 1. Problem Statement & Overview\n{first}...\n\n"
        f"### 2. Proposed Methodology & Key Concepts\n{mid}...\n\n"
        f"### 3. Key Findings & Discussion\n{last}..."
    )
    return {"summary": fallback, "sources": sources, "model": "Grounded Hybrid RAG (Local)"}

