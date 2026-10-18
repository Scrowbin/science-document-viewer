from typing import List, Tuple

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document

EMBEDDING_MODEL = "ibm-granite/granite-embedding-125m-english"


class RAG:
    def __init__(self, documents, reranker=None) -> None:
        self.documents = documents
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.content = [content.page_content for content in self.documents]
        self.tokenized_document = [content.lower().split() for content in self.content]
        self.bm25 = BM25Okapi(self.tokenized_document)

        self.embeddings = self.embedding_model.encode(
            self.content,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        self.reranker = reranker

    def embed(self, text):
        return self.embedding_model.encode(
            text, normalize_embeddings=True, convert_to_numpy=True
        )

    def retrieve(self, query, top_k=10):
        embedded_query = self.embed(query)
        scores = self.embeddings @ embedded_query
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.documents[i], float(scores[i])) for i in top_indices]

    def bm25_search(self, query, top_k):
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(self.documents[i], float(scores[i])) for i in top_indices]

    def hybrid_search(self, query, top_k=5):
        # 1. Dense retrieval
        query_emb = self.embed([query])[0]
        dense_scores = self.embeddings @ query_emb
        dense_top = np.argsort(dense_scores)[::-1][:50]

        # 2. Sparse retrieval (BM25)
        bm25_scores = self.bm25.get_scores(query.lower().split())
        bm25_top = np.argsort(bm25_scores)[::-1][:50]

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        k = 60  # standard RRF constant

        for rank, doc_id in enumerate(dense_top):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

        for rank, doc_id in enumerate(bm25_top):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

        ranked_indices = sorted(
            rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True
        )[:top_k]
        return [(self.documents[i], rrf_scores[i]) for i in ranked_indices]

    def hybrid_search_embed_and_rerank(self, query, retrieve_k=20, rerank_k=5):
        # ---------------------------------------------------------
        # Stage 1: Parallel First-Stage Retrieval (Dense + BM25)
        # ---------------------------------------------------------
        query_embedding = self.embed([query])[0]
        dense_scores = self.embeddings @ query_embedding
        dense_top = np.argsort(dense_scores)[::-1][:retrieve_k]

        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top = np.argsort(bm25_scores)[::-1][:retrieve_k]

        # ---------------------------------------------------------
        # Stage 2: Reciprocal Rank Fusion (RRF) to merge candidates
        # ---------------------------------------------------------
        rrf_k = 60  # Standard smoothing constant
        fused_scores = {}

        for rank, idx in enumerate(dense_top):
            fused_scores[idx] = fused_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)

        for rank, idx in enumerate(bm25_top):
            fused_scores[idx] = fused_scores.get(idx, 0.0) + 1.0 / (rrf_k + rank + 1)

        # Get the top candidates to feed into the reranker
        candidate_indices = sorted(
            fused_scores.keys(), key=lambda i: fused_scores[i], reverse=True
        )[:retrieve_k]

        candidate_docs = [self.documents[i] for i in candidate_indices]

        # ---------------------------------------------------------
        # Stage 3: Second-Stage Reranking
        # ---------------------------------------------------------
        # Case A: If you have a cross-encoder model (e.g., CrossEncoder, Cohere, BGE)
        if hasattr(self, "reranker") and self.reranker is not None:
            pairs = [[query, doc] for doc in candidate_docs]
            rerank_scores = self.reranker.predict(pairs)
            ranked_order = np.argsort(rerank_scores)[::-1][:rerank_k]

            return [
                (
                    candidate_docs[i],
                    float(rerank_scores[i]),
                )
                for i in ranked_order
            ]

        # Case B: Fallback to the top RRF fused candidates if no reranker is loaded
        return [
            (self.documents[i], float(fused_scores[i]))
            for i in candidate_indices[:rerank_k]
        ]

    def bm25_embed_and_rerank(self, query, retrieve_k=20, rerank_k=5):
        query_embedding = self.embed([query])[0]
        dense_scores = self.embeddings @ query_embedding
        candidate_indices = np.argsort(dense_scores)[::-1][:retrieve_k]

        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        reranked = sorted(
            candidate_indices,
            key=lambda i: bm25_scores[i],
            reverse=True,
        )

        reranked = reranked[:rerank_k]

        return [(self.documents[i], float(bm25_scores[i])) for i in reranked]
