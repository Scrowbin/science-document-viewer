import logging
import os
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import requests
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from django.conf import settings
from langchain_core.documents import Document

from .chunking_utils import chunk_document

logger = logging.getLogger(__name__)

# Global in-memory RAG index cache: doc_id -> DocumentRAG instance
_rag_instances: Dict[int, "DocumentRAG"] = {}

# Shared embedding model instance to avoid re-loading weights for every doc
_shared_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    global _shared_embedding_model
    if _shared_embedding_model is None:
        model_name = getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Loading SentenceTransformer model: {model_name}")
        try:
            _shared_embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            logger.warning(f"Failed to load {model_name}, falling back to all-MiniLM-L6-v2: {e}")
            _shared_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
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

        # BM25 setup
        tokenized_corpus = [text.lower().split() for text in self.content]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Dense embedding setup
        self.embedding_model = get_embedding_model()
        if self.content:
            self.embeddings = self.embedding_model.encode(
                self.content,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        else:
            self.embeddings = np.array([])

    def embed(self, text: str) -> np.ndarray:
        return self.embedding_model.encode(
            [text], normalize_embeddings=True, convert_to_numpy=True
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
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k_const + rank + 1)

        for rank, idx in enumerate(bm25_top):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (k_const + rank + 1)

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


def generate_answer_with_ollama(
    question: str, chunks: List[Tuple[Document, float]], doc_title: str
) -> Tuple[str, str]:
    """
    Queries Ollama LLM endpoint with retrieved context chunks.
    Returns (answer_text, model_name).
    """
    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = getattr(settings, "OLLAMA_MODEL", "llama3.2:3b")

    context_str = "\n\n".join(
        [
            f"--- Snippet (Page {doc.metadata.get('page', 1)}, Section: {doc.metadata.get('section', 'Main')}) ---\n{doc.page_content}"
            for doc, _ in chunks
        ]
    )

    prompt = f"""You are a precise academic research assistant reading "{doc_title or 'the document'}".
Use ONLY the provided context below to answer the user's question clearly and accurately.
If the answer is not contained in the context, synthesize the most relevant details available from the context.

Context:
{context_str}

Question: {question}

Answer:"""

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            answer = data.get("response", "").strip()
            if answer:
                return answer, f"{model_name} (Local RAG)"
    except Exception as e:
        logger.info(f"Ollama generation offline/failed ({e}), using grounded context synthesis.")

    # Grounded synthesis fallback if Ollama is offline
    synthesis_snippets = []
    for doc, score in chunks[:3]:
        sec = doc.metadata.get("section", f"Page {doc.metadata.get('page', 1)}")
        snippet = doc.page_content.strip().replace("\n", " ")
        if len(snippet) > 250:
            snippet = snippet[:250] + "..."
        synthesis_snippets.append(f"- **{sec}**: {snippet}")

    fallback_answer = (
        f"Based on retrieved context from **{doc_title or 'the document'}**:\n\n"
        + "\n\n".join(synthesis_snippets)
    )
    return fallback_answer, "Grounded Hybrid RAG (Local)"


def query_document(
    doc_id: int, file_path: str, question: str, doc_title: str = ""
) -> Dict[str, Any]:
    """
    Queries document RAG index, retrieves top chunks, and returns response structure.
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
        sources.append(
            {
                "page": page,
                "chunk_id": chunk_id,
                "snippet": snippet,
            }
        )

    answer, model_used = generate_answer_with_ollama(question, top_chunks, doc_title)

    return {
        "answer": answer,
        "sources": sources,
        "model": model_used,
    }


def summarize_document(
    doc_id: int, file_path: str, doc_title: str = ""
) -> Dict[str, Any]:
    """
    Generates a 1-click structured technical summary of the document.
    """
    rag = get_or_create_rag(doc_id, file_path)
    if not rag or not rag.documents:
        return {
            "summary": "No content available to summarize.",
            "sources": [],
            "model": "Local RAG Engine",
        }

    # Select representative chunks across start, middle, and end
    total = len(rag.documents)
    indices = []
    if total <= 5:
        indices = list(range(total))
    else:
        indices = [0, 1, total // 2, max(0, total - 2), total - 1]
    
    rep_chunks = [(rag.documents[i], 1.0) for i in sorted(set(indices))]

    sources = []
    for doc, _ in rep_chunks:
        page = doc.metadata.get("page", 1)
        chunk_id = doc.metadata.get("chunk_id", f"summary-p{page}")
        snippet = doc.page_content.strip().replace("\n", " ")
        if len(snippet) > 150:
            snippet = snippet[:150] + "..."
        sources.append(
            {
                "page": page,
                "chunk_id": chunk_id,
                "snippet": snippet,
            }
        )

    ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = getattr(settings, "OLLAMA_MODEL", "llama3.2:3b")

    context_str = "\n\n".join([doc.page_content for doc, _ in rep_chunks])
    prompt = f"""Summarize the document "{doc_title or 'Selected Paper'}" into 3 clear markdown sections:
### 1. Problem Statement
### 2. Proposed Architecture & Methodology
### 3. Empirical Results & Findings

Document Excerpts:
{context_str}

Summary:"""

    try:
        resp = requests.post(
            f"{ollama_url}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            summary_text = data.get("response", "").strip()
            if summary_text:
                return {
                    "summary": summary_text,
                    "sources": sources,
                    "model": f"{model_name} (Local RAG)",
                }
    except Exception as e:
        logger.info(f"Ollama summary offline/failed ({e}), using grounded template fallback.")

    # Grounded synthesis summary fallback
    doc_name = doc_title or "this document"
    first_chunk = rag.documents[0].page_content.strip().replace("\n", " ")[:300]
    mid_chunk = rag.documents[total // 2].page_content.strip().replace("\n", " ")[:300]
    last_chunk = rag.documents[-1].page_content.strip().replace("\n", " ")[:300]

    fallback_summary = f"""### 1. Problem Statement & Overview
{first_chunk}...

### 2. Proposed Methodology & Key Concepts
{mid_chunk}...

### 3. Key Findings & Discussion
{last_chunk}..."""

    return {
        "summary": fallback_summary,
        "sources": sources,
        "model": "Grounded Hybrid RAG (Local)",
    }
