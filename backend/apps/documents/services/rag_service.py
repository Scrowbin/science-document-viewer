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
import threading
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
from .question_guard import screen_question

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


def window_around_child(
    parent_text: str,
    char_start: int,
    char_end: int,
    pad_words: int = 250,
) -> Tuple[str, bool]:
    """
    Windows an over-long parent section around the matched child text span.
    Preserves exact evidence span while bounding prompt token consumption.
    Returns (windowed_text, is_windowed).
    """
    if not parent_text:
        return "", False

    char_start = max(0, min(char_start, len(parent_text)))
    char_end = max(char_start, min(char_end, len(parent_text)))
    matched_span = parent_text[char_start:char_end]

    words_before = parent_text[:char_start].split()
    words_after = parent_text[char_end:].split()

    if len(words_before) <= pad_words and len(words_after) <= pad_words:
        return parent_text, False

    slice_before = " ".join(words_before[-pad_words:]) if words_before else ""
    slice_after = " ".join(words_after[:pad_words]) if words_after else ""

    prefix = f"... {slice_before} " if len(words_before) > pad_words else (f"{slice_before} " if slice_before else "")
    suffix = f" {slice_after} ..." if len(words_after) > pad_words else (f" {slice_after}" if slice_after else "")
    windowed = f"{prefix}{matched_span}{suffix}".strip()
    return windowed, True


class RagService:
    """
    Modular in-process RAG Service powering semantic search and QA over academic PDFs.
    Step 4 Production Implementation with champion model intfloat/e5-small-v2.
    """

    _instance: Optional["RagService"] = None
    _lock: threading.Lock = threading.Lock()

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
    def get_instance(cls, **kwargs) -> "RagService":
        """Thread-safe lazy singleton accessor for shared Django application lifecycle."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets singleton instance (useful for test isolation)."""
        with cls._lock:
            cls._instance = None

    def ensure_collection(self, collection_name: str, is_vectorless: bool = False) -> None:
        """
        Creates collection if it does not already exist.
        Supports standard vector collections (384-dim COSINE) and vectorless companion collections
        (vectors_config={}) used for hierarchical parent metadata storage.
        """
        collections = [c.name for c in self.client.get_collections().collections]
        if collection_name not in collections:
            if is_vectorless:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config={},
                )
            else:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=self.vector_dim,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
            # Create payload indices
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
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="parent_id",
                    field_schema=qmodels.PayloadSchemaType.KEYWORD,
                )
            except Exception as e:
                logger.debug("Payload index creation note: %s", e)

    def index_chunks(
        self,
        collection_name: str,
        chunks: List[Dict[str, Any]],
        recreate: bool = False,
        chunking_strategy: Optional[str] = None,
    ) -> int:
        """
        Embeds a list of text chunks and indexes them into Qdrant.
        When chunks belong to hierarchical strategy (carry 'parent_id' and 'parent_text'):
          1. Embeds and indexes fine-grained child chunks into collection_name.
          2. Extracts unique parent sections and indexes them into companion collection {collection_name}_parents.
        Point IDs are deterministic across document and chunk IDs to guarantee cross-document
        isolation and re-indexing idempotency.
        """
        parents_collection = f"{collection_name}_parents"
        if recreate:
            if self.client.collection_exists(collection_name):
                self.client.delete_collection(collection_name)
            if self.client.collection_exists(parents_collection):
                self.client.delete_collection(parents_collection)

        self.ensure_collection(collection_name)
        if not chunks:
            return 0

        # Detect hierarchical strategy
        is_hierarchical = any(
            c.get("strategy") == "hierarchical" or (bool(c.get("parent_id")) and bool(c.get("parent_text")))
            for c in chunks
        )

        # Extract texts for batch embedding with passage prefix
        texts = [c.get("text", "") for c in chunks]
        embeddings = self._embed_texts(texts, is_query=False)

        points: List[qmodels.PointStruct] = []
        unique_parents: Dict[str, Dict[str, Any]] = {}

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

            strat = "hierarchical" if is_hierarchical else chunk.get("strategy", "section_overlap")
            payload = {
                "chunk_id": chunk_id,
                "child_id": chunk.get("child_id", chunk_id),
                "parent_id": str(chunk.get("parent_id", "")),
                "document_id": str(chunk.get("document_id", "")),
                "text": chunk_text,
                "child_text": chunk.get("child_text", chunk_text),
                "section": chunk.get("section", ""),
                "section_title": chunk.get("section", ""),
                "char_start": chunk.get("char_start", 0),
                "char_end": chunk.get("char_end", len(chunk.get("child_text", chunk_text))),
                "chunk_index": chunk.get("chunk_index", idx),
                "page_start": page_start,
                "page_end": page_end,
                "page_number": page_start,
                "token_count": chunk.get("token_count", estimate_tokens(chunk_text)),
                "paper_arxiv_id": str(chunk.get("paper_arxiv_id", "")),
                "strategy": strat,
                "version": "1.0",
            }
            # Citation location (PDF points, top-left origin); display only, not used in retrieval or prompts
            for key in ("loc_page_start", "loc_page_end", "locations"):
                if chunk.get(key) is not None:
                    payload[key] = chunk[key]

            # If hierarchical, record parent
            if is_hierarchical:
                p_id = chunk.get("parent_id")
                p_text = chunk.get("parent_text", "")
                if p_id and p_text and p_id not in unique_parents:
                    unique_parents[p_id] = {
                        "parent_id": p_id,
                        "document_id": str(chunk.get("document_id", "")),
                        "paper_arxiv_id": str(chunk.get("paper_arxiv_id", "")),
                        "section": chunk.get("section", ""),
                        "section_title": chunk.get("section", ""),
                        "parent_text": p_text,
                        "text": p_text,
                        "token_count": chunk.get("parent_tokens", estimate_tokens(p_text)),
                        "page_start": page_start,
                        "page_end": page_end,
                        "page_number": page_start,
                        "strategy": "hierarchical",
                        "version": "1.0",
                        "_doc_ident": doc_ident_str,
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

        # Batch upsert child points
        self.client.upsert(collection_name=collection_name, points=points)

        # Batch upsert unique parents to companion collection (Option b)
        if unique_parents:
            self.ensure_collection(parents_collection, is_vectorless=True)
            parent_points: List[qmodels.PointStruct] = []
            for p_id, p_info in unique_parents.items():
                p_doc_ident = p_info.pop("_doc_ident", "doc")
                p_pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{parents_collection}::{p_doc_ident}::{p_id}"))
                parent_points.append(
                    qmodels.PointStruct(
                        id=p_pt_id,
                        vector={},
                        payload=p_info,
                    )
                )
            self.client.upsert(collection_name=parents_collection, points=parent_points)
            logger.info(
                "Indexed %d child vectors into '%s' and %d parents into companion '%s'",
                len(points), collection_name, len(parent_points), parents_collection
            )
        else:
            logger.info("Successfully indexed %d chunks into collection '%s'", len(points), collection_name)

        return len(points)

    def delete_document_index(self, doc_id: int) -> None:
        """
        Permanently deletes all vectors and parent payloads for a given document.
        Deletes collection 'doc_{doc_id}' and companion 'doc_{doc_id}_parents'.
        """
        coll_name = f"doc_{doc_id}"
        parents_coll = f"{coll_name}_parents"
        try:
            if self.client.collection_exists(coll_name):
                self.client.delete_collection(coll_name)
        except Exception as e:
            logger.warning(f"Failed to delete Qdrant collection {coll_name}: {e}")

        try:
            if self.client.collection_exists(parents_coll):
                self.client.delete_collection(parents_coll)
        except Exception as e:
            logger.warning(f"Failed to delete Qdrant collection {parents_coll}: {e}")

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

    def search_hierarchical(
        self,
        collection_name: str,
        query: str,
        token_budget: int = 1600,
        candidate_pool: int = 20,
        max_parent_tokens: int = 800,
        filter_arxiv_id: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        preprocess_mode: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Hierarchical Small-to-Big retrieval:
          1. Dense search on fine-grained child vectors in collection_name (top-K candidate pool).
          2. Group hits by parent_id, ranking parents by their highest child similarity score.
          3. Deduplicate parents and expand: fetch full parent discourse text from companion
             collection f"{collection_name}_parents" (or fallback to child payload).
          4. Over-long parent windowing guardrail: If a parent section exceeds max_parent_tokens,
             window around the matched child with context padding to prevent context starvation.
          5. Context budget enforcement: Accumulate parent blocks until token_budget (1,600 tokens) is reached.
          6. Returns (score, context_block) containing parent text for LLM generation while preserving
             matched child text and character offsets for in-canvas PDF citation highlighting.
        """
        if not self.client.collection_exists(collection_name):
            return []

        # 1. Search child candidates
        child_candidates = self.search_dense(
            collection_name=collection_name,
            query=query,
            top_k=candidate_pool,
            filter_arxiv_id=filter_arxiv_id,
            filter_document_id=filter_document_id,
            preprocess_mode=preprocess_mode,
        )
        if not child_candidates:
            return []

        # 2. Group by parent_id, keeping the best child score and metadata
        parent_hits: Dict[str, Dict[str, Any]] = {}
        for score, child_payload in child_candidates:
            p_id = child_payload.get("parent_id") or child_payload.get("chunk_id", "")
            if p_id not in parent_hits:
                parent_hits[p_id] = {
                    "score": score,
                    "best_child": child_payload,
                    "child_count": 1,
                }
            else:
                parent_hits[p_id]["child_count"] += 1

        # 3. Retrieve unique parents from companion collection
        parents_col = f"{collection_name}_parents"
        has_parents_col = self.client.collection_exists(parents_col)
        parent_records_map: Dict[str, Dict[str, Any]] = {}

        if has_parents_col:
            point_ids_to_fetch = []
            id_to_pid_map = {}
            for p_id, item in parent_hits.items():
                best_c = item["best_child"]
                doc_ident = best_c.get("document_id") or best_c.get("paper_arxiv_id") or "doc"
                pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{parents_col}::{doc_ident}::{p_id}"))
                point_ids_to_fetch.append(pt_id)
                id_to_pid_map[pt_id] = p_id

            if point_ids_to_fetch:
                try:
                    retrieved_pts = self.client.retrieve(collection_name=parents_col, ids=point_ids_to_fetch)
                    for rec in retrieved_pts:
                        p_payload = rec.payload or {}
                        p_id = p_payload.get("parent_id") or id_to_pid_map.get(str(rec.id))
                        if p_id:
                            parent_records_map[p_id] = p_payload
                except Exception as e:
                    logger.warning("Failed to retrieve parent records from '%s': %s", parents_col, e)

        # 4. Expand context and enforce token budget
        accumulated: List[Tuple[float, Dict[str, Any]]] = []
        accum_tokens = 0

        for p_id, item in parent_hits.items():
            best_c = item["best_child"]
            p_payload = parent_records_map.get(p_id, {})

            parent_text = p_payload.get("parent_text") or best_c.get("parent_text") or best_c.get("text", "")
            parent_tokens = p_payload.get("token_count") or best_c.get("parent_tokens") or estimate_tokens(parent_text)
            char_start = best_c.get("char_start", 0)
            char_end = best_c.get("char_end", len(parent_text))

            # Guardrail against over-long parents
            if parent_tokens > max_parent_tokens:
                context_text, is_win = window_around_child(parent_text, char_start, char_end, pad_words=200)
                used_tokens = estimate_tokens(context_text)
            else:
                context_text = parent_text
                is_win = False
                used_tokens = parent_tokens

            if accum_tokens + used_tokens > token_budget and accumulated:
                logger.debug("Hierarchical retrieval budget filled (%d + %d > %d)", accum_tokens, used_tokens, token_budget)
                break

            context_block = {
                "parent_id": p_id,
                "parent_text": parent_text,
                "text": context_text,
                "section": p_payload.get("section") or best_c.get("section", ""),
                "page": best_c.get("page_start", best_c.get("page", 1)),
                "page_start": best_c.get("page_start", best_c.get("page", 1)),
                "page_end": best_c.get("page_end", best_c.get("page_start", 1)),
                "token_count": used_tokens,
                "parent_tokens": parent_tokens,
                "is_windowed": is_win,
                "score": item["score"],
                "strategy": "hierarchical",
                "matched_child_id": best_c.get("chunk_id"),
                "matched_child_text": best_c.get("child_text") or best_c.get("text"),
                "char_start": char_start,
                "char_end": char_end,
                "document_id": best_c.get("document_id", ""),
                "paper_arxiv_id": best_c.get("paper_arxiv_id", ""),
                "paper_title": best_c.get("paper_title", ""),
            }
            accumulated.append((item["score"], context_block))
            accum_tokens += used_tokens

        return accumulated

    def search_dense_with_token_budget(
        self,
        collection_name: str,
        query: str,
        token_budget: int = 1500,
        candidate_pool: int = 25,
        filter_arxiv_id: Optional[str] = None,
        filter_document_id: Optional[str] = None,
        preprocess_mode: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Retrieves top candidate chunks and accumulates them until the prompt token budget is filled.
        Supports both flat and hierarchical strategies (dispatches to search_hierarchical if
        strategy='hierarchical' or companion parents collection exists).
        """
        has_parents = self.client.collection_exists(f"{collection_name}_parents")
        active_strategy = strategy or getattr(settings, "CHUNKING_STRATEGY", "hierarchical")
        if has_parents and (active_strategy == "hierarchical" or strategy == "hierarchical"):
            return self.search_hierarchical(
                collection_name=collection_name,
                query=query,
                token_budget=token_budget,
                candidate_pool=candidate_pool,
                filter_arxiv_id=filter_arxiv_id,
                filter_document_id=filter_document_id,
                preprocess_mode=preprocess_mode,
            )

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
    with Reciprocal Rank Fusion (RRF). Supports both flat and hierarchical (small-to-big) chunking.
    Dense candidates are retrieved from Qdrant (filtered to document), with in-memory matrix fallback.
    """

    def __init__(
        self,
        document_id: int,
        documents: List[Document],
        embeddings: Optional[np.ndarray] = None,
        unique_parents: Optional[Dict[str, Dict[str, Any]]] = None,
        collection_name: Optional[str] = None,
    ) -> None:
        self.document_id = document_id
        self.documents = documents
        self.collection_name = collection_name or f"doc_{document_id}"
        self.content = [doc.page_content for doc in self.documents]
        self.model_name = getattr(settings, "EMBEDDING_MODEL", "intfloat/e5-small-v2")

        # Hierarchical parent metadata compilation
        self.is_hierarchical = any(
            doc.metadata.get("strategy") == "hierarchical" or bool(doc.metadata.get("parent_id"))
            for doc in self.documents
        )
        if unique_parents is not None:
            self.unique_parents = unique_parents
        else:
            self.unique_parents = {}
            if self.is_hierarchical:
                for doc in self.documents:
                    p_id = doc.metadata.get("parent_id")
                    p_text = doc.metadata.get("parent_text", "")
                    if p_id and p_text and p_id not in self.unique_parents:
                        self.unique_parents[p_id] = {
                            "parent_id": p_id,
                            "parent_text": p_text,
                            "token_count": doc.metadata.get("parent_tokens", estimate_tokens(p_text)),
                            "section": doc.metadata.get("section", ""),
                            "page": doc.metadata.get("page", 1),
                        }

        # Build lookup table for mapping chunk_id and child_id to document index
        self.chunk_id_to_idx: Dict[Any, int] = {}
        for idx, doc in enumerate(self.documents):
            cid = doc.metadata.get("chunk_id")
            if cid is not None:
                self.chunk_id_to_idx[cid] = idx
                self.chunk_id_to_idx[str(cid)] = idx
            chid = doc.metadata.get("child_id")
            if chid is not None:
                self.chunk_id_to_idx[chid] = idx
                self.chunk_id_to_idx[str(chid)] = idx

        # BM25 setup (rebuilt from child texts in self.content)
        tokenized_corpus = [text.lower().split() for text in self.content]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Dense embedding setup
        self._embedding_model: Optional[Any] = None
        if embeddings is not None and len(embeddings) > 0:
            self.embeddings = embeddings
        elif self.content:
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

    @property
    def embedding_model(self) -> Any:
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()
        return self._embedding_model

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
        if not self.documents:
            return []

        num_docs = len(self.documents)
        retrieve_k = min(50, num_docs)

        # 1. Dense retrieval via Qdrant (query_points filtered to document)
        rag_service = RagService.get_instance()
        dense_top: List[int] = []
        try:
            dense_candidates = rag_service.search_dense(
                collection_name=self.collection_name,
                query=query,
                top_k=retrieve_k,
                filter_document_id=str(self.document_id),
            )
            if not dense_candidates and rag_service.client.collection_exists(self.collection_name):
                # Fallback to search without filter if collection is dedicated to this doc
                dense_candidates = rag_service.search_dense(
                    collection_name=self.collection_name,
                    query=query,
                    top_k=retrieve_k,
                )

            seen_dense_idx = set()
            dense_scores_by_idx: Dict[int, float] = {}
            for score, payload in dense_candidates:
                idx = None
                cid = payload.get("chunk_id")
                if cid in self.chunk_id_to_idx:
                    idx = self.chunk_id_to_idx[cid]
                elif cid is not None and str(cid) in self.chunk_id_to_idx:
                    idx = self.chunk_id_to_idx[str(cid)]
                else:
                    chid = payload.get("child_id")
                    if chid in self.chunk_id_to_idx:
                        idx = self.chunk_id_to_idx[chid]
                    elif chid is not None and str(chid) in self.chunk_id_to_idx:
                        idx = self.chunk_id_to_idx[str(chid)]
                    elif "chunk_seq" in payload:
                        seq = payload["chunk_seq"]
                        if 0 <= int(seq) < num_docs:
                            idx = int(seq)
                    else:
                        c_idx = payload.get("chunk_index")
                        if c_idx is not None and 0 <= int(c_idx) < num_docs:
                            idx = int(c_idx)

                if idx is not None and idx not in seen_dense_idx:
                    dense_top.append(idx)
                    dense_scores_by_idx[idx] = float(score)
                    seen_dense_idx.add(idx)
        except Exception as e:
            logger.warning("Qdrant dense search failed for doc %s: %s", self.document_id, e)
            dense_top = []
            dense_scores_by_idx = {}

        # Fallback to in-memory vector dot product if Qdrant returned nothing
        if not dense_top and len(self.embeddings) > 0:
            query_emb = self.embed(query)
            dense_scores = self.embeddings @ query_emb
            dense_top = list(np.argsort(dense_scores)[::-1][:retrieve_k])
            for idx in dense_top:
                dense_scores_by_idx[idx] = float(dense_scores[idx])

        # 2. Sparse retrieval (BM25)
        bm25_scores = self.bm25.get_scores(query.lower().split())
        bm25_top = list(np.argsort(bm25_scores)[::-1][:retrieve_k])

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[int, float] = {}
        k_const = 60

        for rank, idx in enumerate(dense_top):
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0.0) + 1.0 / (k_const + rank + 1)

        for rank, idx in enumerate(bm25_top):
            rrf_scores[int(idx)] = rrf_scores.get(int(idx), 0.0) + 1.0 / (k_const + rank + 1)

        ranked_indices = sorted(
            rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True
        )

        # If hierarchical: Expand child hits to unique parent sections, windowing over-long parents
        if self.is_hierarchical:
            parent_results: List[Tuple[Document, float]] = []
            seen_parents = set()
            accum_tokens = 0
            token_budget = getattr(settings, "RAG_CONTEXT_BUDGET", 1600)
            max_parent_tokens = getattr(settings, "RAG_MAX_PARENT_TOKENS", 800)

            for idx in ranked_indices:
                child_doc = self.documents[idx]
                p_id = child_doc.metadata.get("parent_id")
                if not p_id or p_id in seen_parents:
                    continue
                seen_parents.add(p_id)

                parent_info = self.unique_parents.get(p_id, {})
                parent_text = parent_info.get("parent_text") or child_doc.metadata.get("parent_text", child_doc.page_content)
                p_tokens = parent_info.get("token_count", estimate_tokens(parent_text))

                char_start = child_doc.metadata.get("char_start", 0)
                char_end = child_doc.metadata.get("char_end", len(parent_text))
                if p_tokens > max_parent_tokens:
                    context_text, is_win = window_around_child(parent_text, char_start, char_end, pad_words=200)
                    used_tokens = estimate_tokens(context_text)
                else:
                    context_text = parent_text
                    is_win = False
                    used_tokens = p_tokens

                if accum_tokens + used_tokens > token_budget and parent_results:
                    break

                meta = dict(child_doc.metadata)
                meta["parent_text"] = parent_text
                meta["matched_child_id"] = child_doc.metadata.get("chunk_id")
                meta["matched_child_text"] = child_doc.metadata.get("child_text", child_doc.page_content)
                meta["token_count"] = used_tokens
                meta["parent_tokens"] = p_tokens
                meta["is_windowed"] = is_win
                meta["strategy"] = "hierarchical"
                meta["dense_score"] = dense_scores_by_idx.get(idx, 0.0)

                parent_doc = Document(page_content=context_text, metadata=meta)
                parent_results.append((parent_doc, float(rrf_scores[idx])))
                accum_tokens += used_tokens

            return parent_results[:top_k]

        flat_results = []
        for i in ranked_indices[: min(top_k, num_docs)]:
            d = self.documents[i]
            meta = dict(d.metadata)
            meta["dense_score"] = dense_scores_by_idx.get(i, 0.0)
            flat_results.append((Document(page_content=d.page_content, metadata=meta), float(rrf_scores[i])))
        return flat_results


def evict_rag_instance(doc_id: int) -> None:
    """Evicts cached in-memory DocumentRAG instance."""
    if doc_id in _rag_instances:
        del _rag_instances[doc_id]


def delete_document_qdrant_data(doc_id: int) -> None:
    """Deletes Qdrant collections for a document using RagService."""
    rag_service = RagService.get_instance()
    rag_service.delete_document_index(doc_id)


def build_rag_from_qdrant(doc_id: int, coll_name: Optional[str] = None) -> Optional[DocumentRAG]:
    """
    Reconstructs a DocumentRAG instance entirely from persistent Qdrant storage.
    Loads child points (vectors and payloads) and parent texts from {collection}_parents,
    rebuilds BM25 from child texts, and instantiates DocumentRAG without re-parsing
    or re-embedding the document.
    Returns None if the collection is missing or incomplete.
    """
    rag_service = RagService.get_instance()
    collection_name = coll_name or f"doc_{doc_id}"

    try:
        if not rag_service.client.collection_exists(collection_name):
            return None

        count_info = rag_service.client.count(collection_name)
        if count_info.count == 0:
            return None

        # 1. Scroll all child points with payload and vectors
        records = []
        offset = None
        while True:
            batch, offset = rag_service.client.scroll(
                collection_name=collection_name,
                offset=offset,
                limit=1000,
                with_payload=True,
                with_vectors=True,
            )
            records.extend(batch)
            if offset is None or not batch:
                break

        if not records:
            return None

        # Completeness check: points must have vectors
        first_vec = records[0].vector
        if first_vec is None or (isinstance(first_vec, (list, np.ndarray)) and len(first_vec) == 0):
            return None

        # Sort points by chunk_seq (or chunk_index) to restore original document sequence
        records.sort(
            key=lambda r: (r.payload or {}).get("chunk_seq", (r.payload or {}).get("chunk_index", 0))
        )

        # 2. Scroll parent texts from companion collection if it exists
        parents_collection = f"{collection_name}_parents"
        unique_parents: Dict[str, Dict[str, Any]] = {}
        if rag_service.client.collection_exists(parents_collection):
            p_offset = None
            while True:
                p_batch, p_offset = rag_service.client.scroll(
                    collection_name=parents_collection,
                    offset=p_offset,
                    limit=1000,
                    with_payload=True,
                    with_vectors=False,
                )
                for rec in p_batch:
                    p_payload = rec.payload or {}
                    p_id = p_payload.get("parent_id")
                    if p_id:
                        p_text = p_payload.get("parent_text") or p_payload.get("text", "")
                        unique_parents[p_id] = {
                            "parent_id": p_id,
                            "parent_text": p_text,
                            "token_count": p_payload.get("token_count", estimate_tokens(p_text)),
                            "section": p_payload.get("section", ""),
                            "page": p_payload.get("page_start", p_payload.get("page_number", 1)),
                        }
                if p_offset is None or not p_batch:
                    break

        # 3. Reconstruct Document objects and vector array
        documents: List[Document] = []
        vectors: List[List[float]] = []

        is_hierarchical_detected = False
        for rec in records:
            payload = rec.payload or {}
            chunk_text = payload.get("text", "")
            meta = dict(payload)
            page_start = meta.get("page_start", meta.get("page_number", meta.get("page", 1)))
            meta["page"] = page_start
            meta["page_start"] = page_start
            meta["page_end"] = meta.get("page_end", page_start)
            meta["page_number"] = page_start

            p_id = meta.get("parent_id")
            if p_id:
                is_hierarchical_detected = True
                if p_id in unique_parents and not meta.get("parent_text"):
                    meta["parent_text"] = unique_parents[p_id]["parent_text"]

            documents.append(Document(page_content=chunk_text, metadata=meta))
            vectors.append(rec.vector if isinstance(rec.vector, list) else list(rec.vector))

        # Check for completeness of hierarchical data
        if is_hierarchical_detected and not unique_parents:
            for doc in documents:
                p_id = doc.metadata.get("parent_id")
                p_text = doc.metadata.get("parent_text", "")
                if p_id and p_text and p_id not in unique_parents:
                    unique_parents[p_id] = {
                        "parent_id": p_id,
                        "parent_text": p_text,
                        "token_count": doc.metadata.get("parent_tokens", estimate_tokens(p_text)),
                        "section": doc.metadata.get("section", ""),
                        "page": doc.metadata.get("page", 1),
                    }
            if not unique_parents:
                logger.warning(
                    "Qdrant collection %s has hierarchical child chunks but parent texts are missing",
                    collection_name,
                )
                return None

        embeddings = np.array(vectors, dtype=np.float32)

        rag = DocumentRAG(
            document_id=doc_id,
            documents=documents,
            embeddings=embeddings,
            unique_parents=unique_parents,
            collection_name=collection_name,
        )
        return rag
    except Exception as e:
        logger.warning("Failed to build DocumentRAG from Qdrant for doc %s: %s", doc_id, e)
        return None


def ingest_document(
    doc_id: int, file_path: str, strategy: Optional[str] = None
) -> Tuple[int, Optional[DocumentRAG]]:
    """
    Full ingestion pipeline matching thesis specification:
    1. Extracts sections and chunks text (hierarchical Small-to-Big by default).
    2. Writes 384-dim dense vectors & payloads to Qdrant collection 'doc_{doc_id}',
       and parent texts to companion collection 'doc_{doc_id}_parents'.
    3. Builds in-memory DocumentRAG instance from Qdrant vectors and payloads,
       cached in _rag_instances[doc_id] for sub-ms chat.
    Returns (num_indexed_points, rag_instance).
    """
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"File path missing or invalid for doc {doc_id}: {file_path}")
        return 0, None

    active_strategy = strategy or getattr(settings, "CHUNKING_STRATEGY", "hierarchical")
    logger.info(f"Ingesting document {doc_id} from {file_path} (strategy={active_strategy})...")
    chunks = chunk_document(file_path, strategy=active_strategy)
    if not chunks:
        logger.warning(f"No chunks generated for doc {doc_id}")
        return 0, None

    # Transform Document objects into chunk dicts with document identifiers
    chunks_data = []
    for idx, d in enumerate(chunks):
        item = dict(d.metadata)
        item["text"] = d.page_content
        item["document_id"] = str(doc_id)
        item["paper_arxiv_id"] = f"doc_{doc_id}"
        item["chunk_seq"] = idx
        item["chunk_index"] = idx
        d.metadata["chunk_seq"] = idx
        d.metadata["chunk_index"] = idx
        d.metadata["document_id"] = str(doc_id)
        chunks_data.append(item)

    # 1. Index into persistent Qdrant collection
    coll_name = f"doc_{doc_id}"
    rag_service = RagService.get_instance()
    indexed_count = rag_service.index_chunks(
        collection_name=coll_name,
        chunks=chunks_data,
        recreate=True,
        chunking_strategy=active_strategy,
    )

    # 2. Build DocumentRAG instance from persistent Qdrant storage (without duplicate embedding)
    rag = build_rag_from_qdrant(doc_id, coll_name=coll_name)
    if rag is None:
        logger.warning("Falling back to in-memory DocumentRAG creation for doc %s", doc_id)
        rag = DocumentRAG(doc_id, chunks, collection_name=coll_name)

    _rag_instances[doc_id] = rag
    return indexed_count, rag


def get_or_create_rag(
    doc_id: int, file_path: str, strategy: Optional[str] = None
) -> Optional[DocumentRAG]:
    """
    Returns existing DocumentRAG instance from cache or rebuilds from Qdrant.
    Re-parses and re-embeds ONLY if the document's collection is missing or incomplete.
    Supports strategy override ('section_overlap' or 'hierarchical').
    """
    if doc_id in _rag_instances:
        return _rag_instances[doc_id]

    coll_name = f"doc_{doc_id}"
    rag_service = RagService.get_instance()

    # Try rebuilding from persistent Qdrant first
    rag = None
    try:
        if rag_service.client.collection_exists(coll_name):
            rag = build_rag_from_qdrant(doc_id, coll_name=coll_name)
    except Exception as e:
        logger.warning(f"Failed to rebuild DocumentRAG from Qdrant for doc {doc_id}: {e}")
        rag = None

    if rag is not None:
        _rag_instances[doc_id] = rag
        return rag

    # Collection missing or incomplete: re-parse and re-embed from physical file
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"File path missing or invalid for doc {doc_id}: {file_path}")
        return None

    indexed_count, rag = ingest_document(doc_id, file_path, strategy=strategy)
    if rag:
        try:
            from ..models import Document as DocModel
            DocModel.objects.filter(id=doc_id).update(rag_status="INDEXED")
        except Exception as e:
            logger.warning(f"Failed to update rag_status in DB for doc {doc_id}: {e}")

    return rag


def reindex_document(
    doc_id: int, file_path: str, strategy: Optional[str] = None
) -> Optional[DocumentRAG]:
    """
    Clears cache for doc_id and re-runs ingestion & embedding with specified or default strategy.
    """
    evict_rag_instance(doc_id)
    indexed_count, rag = ingest_document(doc_id, file_path, strategy=strategy)
    if rag:
        try:
            from ..models import Document as DocModel
            DocModel.objects.filter(id=doc_id).update(rag_status="INDEXED")
        except Exception as e:
            logger.warning(f"Failed to update rag_status in DB for doc {doc_id}: {e}")
    return rag


def _generate_with_ollama(prompt: str, model_name: str, ollama_url: str) -> Optional[str]:
    """Calls Ollama /api/generate and returns response text or None."""
    try:
        read_timeout = getattr(settings, "OLLAMA_TIMEOUT", 60)
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=(3.0, read_timeout),
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

    REFUSAL_MESSAGE = "The document does not contain sufficient relevant information to answer this question."

    # NFR-07: obscene or app-sensitive questions are refused before retrieval (terms the paper itself uses pass)
    guard_reason = screen_question(question, (d.page_content for d in rag.documents))
    if guard_reason:
        logger.info("Question refused by scope guard for doc %s (reason=%s).", doc_id, guard_reason)
        return {
            "answer": REFUSAL_MESSAGE,
            "sources": [],
            "model": "Grounded Hybrid RAG (Local)",
            "refused": True,
            "refusal_reason": guard_reason,
        }

    top_chunks = rag.hybrid_search(question, top_k=5)


    min_similarity = getattr(settings, "RAG_MIN_SIMILARITY_SCORE", 0.80)
    top_dense_score = max(
        (float(doc.metadata.get("dense_score", 0.0)) for doc, _ in top_chunks),
        default=0.0,
    )

    if not top_chunks or top_dense_score < min_similarity:
        logger.info(
            "Query relevance below threshold for doc %s (top_dense_score=%.4f < %.4f). Returning refusal response.",
            doc_id,
            top_dense_score,
            min_similarity,
        )
        return {
            "answer": REFUSAL_MESSAGE,
            "sources": [],
            "model": "Grounded Hybrid RAG (Local)",
        }

    sources = []
    for doc, score in top_chunks:
        page = doc.metadata.get("page", 1)
        chunk_id = doc.metadata.get("matched_child_id", doc.metadata.get("chunk_id", f"chunk-p{page}"))
        section = doc.metadata.get("section", "")
        # For citation highlighting, preserve exact matched child text and offsets
        matched_text = doc.metadata.get("matched_child_text", doc.page_content).strip()
        raw_text = doc.page_content.strip()
        snippet = matched_text.replace("\n", " ")
        if len(snippet) > 180:
            snippet = snippet[:180] + "..."
        sources.append({
            "page": page,
            "chunk_id": chunk_id,
            "section": section,
            "snippet": snippet,
            "text": matched_text,
            "parent_id": doc.metadata.get("parent_id"),
            "char_start": doc.metadata.get("char_start"),
            "char_end": doc.metadata.get("char_end"),
            # Citation location for the viewer (null for documents indexed before locations existed)
            "page_start": doc.metadata.get("loc_page_start"),
            "page_end": doc.metadata.get("loc_page_end"),
            "locations": doc.metadata.get("locations"),
        })

    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = getattr(settings, "OLLAMA_MODEL", "llama3.2:3b")

    context_str = "\n\n".join(
        f"--- Snippet (Page {doc.metadata.get('page', 1)}, Section: {doc.metadata.get('section', 'Main')}) ---\n{doc.page_content}"
        for doc, _ in top_chunks
    )

    prompt = (
        f'You are a precise academic research assistant reading "{doc_title or "the document"}".\n'
        f"Use ONLY the provided context below to answer the user's question clearly and accurately.\n"
        f"Respond in the same language as the user's question (e.g. if the question is in Vietnamese, answer in Vietnamese using the English context as the factual ground).\n"
        f"If the answer is not contained in the context, state clearly: '{REFUSAL_MESSAGE}'\n"
        f"Do NOT extrapolate, speculate, or fabricate details beyond the provided context.\n\n"
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
        chunk_id = doc.metadata.get("matched_child_id", doc.metadata.get("chunk_id", f"summary-p{page}"))
        section = doc.metadata.get("section", "")
        # child_text has no "[heading]" prefix, so the viewer can match it against the page text
        matched_text = (doc.metadata.get("matched_child_text") or doc.metadata.get("child_text") or doc.page_content).strip()
        raw_text = doc.page_content.strip()
        snippet = matched_text.replace("\n", " ")
        if len(snippet) > 150:
            snippet = snippet[:150] + "..."
        sources.append({
            "page": page,
            "chunk_id": chunk_id,
            "section": section,
            "snippet": snippet,
            "text": matched_text,
            "parent_id": doc.metadata.get("parent_id"),
            "char_start": doc.metadata.get("char_start"),
            "char_end": doc.metadata.get("char_end"),
            # Citation location for the viewer (null for documents indexed before locations existed)
            "page_start": doc.metadata.get("loc_page_start"),
            "page_end": doc.metadata.get("loc_page_end"),
            "locations": doc.metadata.get("locations"),
        })

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

