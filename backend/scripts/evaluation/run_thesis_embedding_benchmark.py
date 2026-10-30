"""
Unified Open-Source Embedding Benchmark for Computer Science Thesis.

Evaluates 11 open-source MIT / Apache-2.0 models (<= 335M params) on the complete
unified 207-paper / 615-query / 5,207-chunk academic corpus on disk:
  - Exact brute-force cosine similarity (NumPy BLAS on FP32 unit-normalized vectors).
  - Accuracy: nDCG@10 (primary), nDCG@4, Recall@20, MRR@10.
  - Paper-cluster bootstrap (B=2,000, seed=42) 95% CIs and two-sided paired p-values vs all-MiniLM-L6-v2.
  - Hardware efficiency profiling on AMD Ryzen 5 5600 (torch.set_num_threads(4)):
    * Indexing throughput (chunks/sec, batch_size=32)
    * Single-query encoding latency (P50/P95 in ms, batch_size=1 across 100 queries with 10 warm-up)
    * Peak resident memory (RSS in MB via psutil)

Outputs:
  - eval/results/thesis_embedding_benchmark.json
"""

import gc
import json
import os
import signal
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import torch
import torch.nn.functional as F

# Fix Windows SIGALRM missing attribute for transformers dynamic module resolution
if not hasattr(signal, "SIGALRM"):
    setattr(signal, "SIGALRM", getattr(signal, "SIGABRT", 6))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# Allocate fixed 4 CPU threads for reproducible Ryzen 5 5600 profiling
torch.set_num_threads(4)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Monorepo path resolution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.dirname(SCRIPTS_DIR)
REPO_ROOT = os.path.dirname(BACKEND_DIR)
EVAL_DIR = os.path.join(REPO_ROOT, "eval")
RESULTS_DIR = os.path.join(EVAL_DIR, "results")
PREPARED_DIR = os.path.join(EVAL_DIR, "prepared")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from apps.documents.services.chunking_utils import chunk_sections
from eval_common import (
    compute_ndcg,
    count_relevant_chunks,
    is_chunk_hit,
    paired_cluster_bootstrap,
    tokenize_regex,
)
from sentence_transformers import SentenceTransformer
from transformers import AutoConfig, AutoModel, AutoTokenizer

# -----------------------------------------------------------------------------
# 11 Open-Source Model Registry (MIT / Apache-2.0 <= 335M parameters)
# -----------------------------------------------------------------------------
MODELS_SPECS: List[Dict[str, Any]] = [
    {
        "id": "bm25",
        "name": "BM25 [WordPiece Subwords]",
        "short_name": "BM25",
        "type": "sparse",
        "dim": None,
        "params_m": 0.0,
        "license": "MIT",
        "query_prefix": "",
        "doc_prefix": "",
    },
    {
        "id": "all-MiniLM-L6-v2",
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "short_name": "MiniLM-L6",
        "type": "dense",
        "dim": 384,
        "params_m": 22.7,
        "license": "Apache-2.0",
        "query_prefix": "",
        "doc_prefix": "",
    },
    {
        "id": "e5-small-v2",
        "name": "intfloat/e5-small-v2",
        "short_name": "E5-Small-v2",
        "type": "dense",
        "dim": 384,
        "params_m": 33.4,
        "license": "MIT",
        "query_prefix": "query: ",
        "doc_prefix": "passage: ",
    },
    {
        "id": "bge-small-en-v1.5",
        "name": "BAAI/bge-small-en-v1.5",
        "short_name": "BGE-Small-v1.5",
        "type": "dense",
        "dim": 384,
        "params_m": 33.4,
        "license": "MIT",
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "doc_prefix": "",
    },
    {
        "id": "gte-small",
        "name": "thenlper/gte-small",
        "short_name": "GTE-Small",
        "type": "dense",
        "dim": 384,
        "params_m": 33.4,
        "license": "Apache-2.0",
        "query_prefix": "",
        "doc_prefix": "",
    },
    {
        "id": "snowflake-arctic-embed-s",
        "name": "Snowflake/snowflake-arctic-embed-s",
        "short_name": "Arctic-Embed-S",
        "type": "dense",
        "dim": 384,
        "params_m": 33.2,
        "license": "Apache-2.0",
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "doc_prefix": "",
    },
    {
        "id": "snowflake-arctic-embed-m-v1.5",
        "name": "Snowflake/snowflake-arctic-embed-m-v1.5",
        "short_name": "Arctic-Embed-M-v1.5",
        "type": "dense",
        "dim": 768,
        "params_m": 108.9,
        "license": "Apache-2.0",
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "doc_prefix": "",
    },
    {
        "id": "nomic-embed-text-v1.5",
        "name": "nomic-ai/nomic-embed-text-v1.5",
        "short_name": "Nomic-Embed-v1.5",
        "type": "dense",
        "dim": 768,
        "params_m": 137.0,
        "license": "Apache-2.0",
        "query_prefix": "search_query: ",
        "doc_prefix": "search_document: ",
        "trust_remote_code": True,
    },
    {
        "id": "modernbert-embed-base",
        "name": "nomic-ai/modernbert-embed-base",
        "short_name": "ModernBERT-Embed",
        "type": "dense",
        "dim": 768,
        "params_m": 149.0,
        "license": "Apache-2.0",
        "query_prefix": "search_query: ",
        "doc_prefix": "search_document: ",
    },
    {
        "id": "snowflake-arctic-embed-m-v2.0",
        "name": "Snowflake/snowflake-arctic-embed-m-v2.0",
        "short_name": "Arctic-Embed-M-v2.0",
        "type": "dense_custom",
        "dim": 768,
        "params_m": 305.0,
        "license": "Apache-2.0",
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "doc_prefix": "",
    },
    {
        "id": "mxbai-embed-large-v1",
        "name": "mixedbread-ai/mxbai-embed-large-v1",
        "short_name": "MXBAI-Large-v1",
        "type": "dense",
        "dim": 1024,
        "params_m": 335.1,
        "license": "Apache-2.0",
        "query_prefix": "Represent this sentence for searching relevant passages: ",
        "doc_prefix": "",
    },
]


def load_unified_dataset() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Loads and assembles the complete unified 207-paper dataset on disk:
      - 48 Dev papers (128 queries, 1,099 chunks from qasper_corpus.json sections)
      - 160 Held-out papers (159 active, 487 queries, 4,108 chunks from expanded_160_chunks.json)
    Returns: (all_queries, all_chunks, paper_chunks_map)
    """
    # 1. Dev split
    with open(os.path.join(PREPARED_DIR, "dev_held_out_split.json"), "r", encoding="utf-8") as f:
        dev_pids = set(json.load(f)["dev_papers"])

    with open(os.path.join(PREPARED_DIR, "qasper_corpus.json"), "r", encoding="utf-8") as f:
        dev_corpus_all = json.load(f)
    dev_corpus = {k: v for k, v in dev_corpus_all.items() if k in dev_pids}

    with open(os.path.join(PREPARED_DIR, "qasper_sampled.json"), "r", encoding="utf-8") as f:
        dev_queries_all = json.load(f)
    dev_queries = [q for q in dev_queries_all if q.get("paper_arxiv_id") in dev_pids and q.get("question_type") != "unanswerable"]

    dev_chunks = []
    for aid, doc in dev_corpus.items():
        chunks = chunk_sections(doc.get("sections", []), strategy="section_overlap", max_tokens=350, overlap=70)
        for idx, c in enumerate(chunks):
            c["paper_arxiv_id"] = aid
            c["chunk_id"] = f"{aid}_c_{idx}"
            dev_chunks.append(c)

    # 2. Held-out split
    with open(os.path.join(PREPARED_DIR, "expanded_held_out_split.json"), "r", encoding="utf-8") as f:
        held_out_aids = set(json.load(f)["held_out_papers"])

    with open(os.path.join(PREPARED_DIR, "expanded_corpus.json"), "r", encoding="utf-8") as f:
        held_out_corpus_all = json.load(f)
    held_out_corpus = {k: v for k, v in held_out_corpus_all.items() if k in held_out_aids}

    with open(os.path.join(PREPARED_DIR, "expanded_qasper_sampled.json"), "r", encoding="utf-8") as f:
        held_out_queries_all = json.load(f)
    held_out_queries = [q for q in held_out_queries_all if q.get("paper_arxiv_id") in held_out_aids and q.get("question_type") != "unanswerable"]

    held_out_chunks = []
    for aid, doc in held_out_corpus.items():
        chunks = chunk_sections(doc.get("sections", []), strategy="section_overlap", max_tokens=350, overlap=70)
        for idx, c in enumerate(chunks):
            c["paper_arxiv_id"] = aid
            c["chunk_id"] = f"{aid}_c_{idx}"
            held_out_chunks.append(c)

    # Combine queries and standardize schema
    all_queries = []
    for q in dev_queries:
        ev_list = q.get("evidence_list", [])
        if not ev_list and q.get("verbatim_evidence_quote"):
            ev_list = [q["verbatim_evidence_quote"]]
        all_queries.append({
            "query_id": q.get("id", q.get("query_id")),
            "paper_arxiv_id": q.get("paper_arxiv_id", q.get("arxiv_id")),
            "question": q["question"],
            "verbatim_evidence_quote": q.get("verbatim_evidence_quote", ""),
            "evidence_list": ev_list,
            "evidence": ev_list,
            "split": "dev",
        })

    for q in held_out_queries:
        ev_list = q.get("evidence_list", [])
        if not ev_list and q.get("verbatim_evidence_quote"):
            ev_list = [q["verbatim_evidence_quote"]]
        all_queries.append({
            "query_id": q.get("id", q.get("query_id")),
            "paper_arxiv_id": q.get("paper_arxiv_id", q.get("arxiv_id")),
            "question": q["question"],
            "verbatim_evidence_quote": q.get("verbatim_evidence_quote", ""),
            "evidence_list": ev_list,
            "evidence": ev_list,
            "split": "held_out",
        })

    all_chunks = dev_chunks + held_out_chunks

    # Group chunks by paper_arxiv_id
    paper_chunks_map: Dict[str, List[Dict[str, Any]]] = {}
    for c in all_chunks:
        p_id = c.get("paper_arxiv_id", "")
        paper_chunks_map.setdefault(p_id, []).append(c)

    # Filter out any query whose paper has 0 chunks
    valid_queries = [q for q in all_queries if q["paper_arxiv_id"] in paper_chunks_map and len(paper_chunks_map[q["paper_arxiv_id"]]) > 0]

    unique_papers = len(set(q["paper_arxiv_id"] for q in valid_queries))
    print(f"[DATASET] Unified Corpus: {unique_papers} active papers, {len(valid_queries)} queries, {len(all_chunks)} chunks.")

    return valid_queries, all_chunks, paper_chunks_map


# -----------------------------------------------------------------------------
# BM25 Sparse Baseline Implementation
# -----------------------------------------------------------------------------
class LocalBM25:
    def __init__(self, chunks: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.total_docs = len(chunks)
        self.doc_tokens = [tokenize_regex(c.get("text", "") + " " + c.get("section", "")) for c in chunks]
        self.doc_lens = [len(t) for t in self.doc_tokens]
        self.avg_len = sum(self.doc_lens) / max(1, self.total_docs)
        self.df: Dict[str, int] = {}
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.df[token] = self.df.get(token, 0) + 1

    def score(self, query: str) -> np.ndarray:
        q_tokens = tokenize_regex(query)
        scores = np.zeros(self.total_docs, dtype=np.float32)
        if not q_tokens or self.total_docs == 0:
            return scores

        for t in q_tokens:
            df_val = self.df.get(t, 0)
            if df_val == 0:
                continue
            idf = np.log((self.total_docs - df_val + 0.5) / (df_val + 0.5) + 1.0)
            for idx, d_tokens in enumerate(self.doc_tokens):
                tf = d_tokens.count(t)
                if tf > 0:
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_lens[idx] / max(1.0, self.avg_len)))
                    scores[idx] += idf * (tf * (self.k1 + 1.0) / denom)
        return scores


# -----------------------------------------------------------------------------
# Evaluation Runner
# -----------------------------------------------------------------------------
def run_benchmark():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    benchmark_json_path = os.path.join(RESULTS_DIR, "thesis_embedding_benchmark.json")

    print("=" * 80)
    print("UNIFIED THESIS EMBEDDING BENCHMARK (11 OPEN-SOURCE MODELS <= 335M)")
    print("Exact Cosine Similarity (NumPy BLAS FP32) | AMD Ryzen 5 5600 (4 Threads)")
    print("=" * 80)

    queries, all_chunks, paper_chunks_map = load_unified_dataset()
    chunk_texts = [c.get("text", "") for c in all_chunks]
    sample_queries = [q["question"] for q in queries[:100]]

    # Pre-compute R_q for all queries to ensure global IDCG calculation
    print("[EVAL] Pre-computing global R_q relevance counts for 615 queries...")
    for q in queries:
        p_id = q["paper_arxiv_id"]
        cand_chunks = paper_chunks_map[p_id]
        ev_list = q["evidence"] if isinstance(q["evidence"], list) else [q["evidence"]]
        q["R_q"] = count_relevant_chunks(cand_chunks, p_id, verbatim_evidence_quote=q.get("verbatim_evidence_quote", ""), evidence_list=ev_list, tau=0.55)

    benchmark_results: Dict[str, Any] = {
        "metadata": {
            "title": "Unified Open-Source Embedding Benchmark for Academic Passage Retrieval",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "corpus": {
                "active_papers": len(set(q["paper_arxiv_id"] for q in queries)),
                "total_queries": len(queries),
                "total_chunks": len(all_chunks),
                "tau_threshold": 0.55,
            },
            "hardware": {
                "cpu": "AMD Ryzen 5 5600 6-Core Processor",
                "threads": 4,
                "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            },
            "eval_framework": {
                "metric_primary": "nDCG@10",
                "metrics_secondary": ["nDCG@4", "Recall@20", "MRR@10"],
                "similarity": "exact_brute_force_cosine (NumPy BLAS on FP32)",
                "bootstrap_resamples": 2000,
                "bootstrap_seed": 42,
            },
        },
        "models": [],
    }

    # Model evaluation loop
    all_models_query_ndcg10: Dict[str, Dict[str, List[float]]] = {}
    base_model_id = "all-MiniLM-L6-v2"

    for spec in MODELS_SPECS:
        m_id: str = str(spec["id"])
        name: str = str(spec["name"])
        short_name: str = str(spec["short_name"])
        m_type: str = str(spec["type"])
        q_prefix: str = str(spec["query_prefix"])
        doc_prefix: str = str(spec["doc_prefix"])
        trust_remote: bool = bool(spec.get("trust_remote_code", False))

        print("\n" + "-" * 70)
        print(f"BENCHMARKING MODEL [{m_id}] -> {name} ({spec['params_m']}M params)")
        print("-" * 70)

        process = psutil.Process()
        gc.collect()
        rss_start_mb = process.memory_info().rss / (1024 * 1024)

        query_scores_ndcg10: Dict[str, List[float]] = {}
        query_scores_ndcg4: Dict[str, List[float]] = {}
        query_scores_rec20: Dict[str, List[float]] = {}
        query_scores_mrr10: Dict[str, List[float]] = {}

        for p_id in paper_chunks_map:
            query_scores_ndcg10[p_id] = []
            query_scores_ndcg4[p_id] = []
            query_scores_rec20[p_id] = []
            query_scores_mrr10[p_id] = []

        if m_type == "sparse":
            # BM25 Sparse
            t0_build = time.perf_counter()
            bm25_indices = {p_id: LocalBM25(paper_chunks_map[p_id]) for p_id in paper_chunks_map}
            t_build_sec = time.perf_counter() - t0_build
            throughput_chunks_sec = round(len(all_chunks) / max(0.001, t_build_sec), 1)

            # Single-query latency profiling
            warmup_q = sample_queries[:10]
            for wq in warmup_q:
                _ = bm25_indices[queries[0]["paper_arxiv_id"]].score(wq)

            timed_latencies_ms = []
            for sq in sample_queries:
                t0_q = time.perf_counter()
                _ = bm25_indices[queries[0]["paper_arxiv_id"]].score(sq)
                timed_latencies_ms.append((time.perf_counter() - t0_q) * 1000.0)

            lat_p50 = float(np.percentile(timed_latencies_ms, 50))
            lat_p95 = float(np.percentile(timed_latencies_ms, 95))
            peak_rss_mb = process.memory_info().rss / (1024 * 1024)

            # Accuracy retrieval across 615 queries
            for q in queries:
                p_id = q["paper_arxiv_id"]
                cand_chunks = paper_chunks_map[p_id]
                idx = bm25_indices[p_id]
                scores = idx.score(q["question"])
                ranked_indices = np.argsort(-scores)

                ev_list = q["evidence"] if isinstance(q["evidence"], list) else [q["evidence"]]
                ranked_relevances = [
                    1 if is_chunk_hit(cand_chunks[i], p_id, verbatim_evidence_quote=q.get("verbatim_evidence_quote", ""), evidence_list=ev_list, tau=0.55) else 0
                    for i in ranked_indices
                ]

                R_q = q["R_q"]
                ndcg10 = compute_ndcg(ranked_relevances, R_q, k=10)
                ndcg4 = compute_ndcg(ranked_relevances, R_q, k=4)
                rec20 = float(sum(ranked_relevances[:20]) / max(1, R_q)) if R_q > 0 else 0.0

                first_hit_rank = next((idx for idx, r in enumerate(ranked_relevances[:10]) if r > 0), None)
                mrr10 = 1.0 / (first_hit_rank + 1) if first_hit_rank is not None else 0.0

                query_scores_ndcg10[p_id].append(ndcg10)
                query_scores_ndcg4[p_id].append(ndcg4)
                query_scores_rec20[p_id].append(rec20)
                query_scores_mrr10[p_id].append(mrr10)

        elif m_type == "dense_custom":
            # Arctic m-v2.0 Custom Loader
            cfg = AutoConfig.from_pretrained(name, trust_remote_code=True)
            cfg.use_memory_efficient_attention = False
            custom_model = AutoModel.from_pretrained(name, config=cfg, trust_remote_code=True)
            custom_model.eval()
            custom_tok = AutoTokenizer.from_pretrained(name)

            def encode_custom(texts: List[str], batch_size: int = 32) -> np.ndarray:
                all_embs = []
                for i in range(0, len(texts), batch_size):
                    batch_texts = texts[i:i + batch_size]
                    inp = custom_tok(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
                    with torch.no_grad():
                        out = custom_model(**inp)
                        embs = F.normalize(out[0][:, 0], p=2, dim=1)
                        all_embs.append(embs.cpu().numpy())
                return np.vstack(all_embs).astype(np.float32)

            # Profile Indexing Throughput
            formatted_chunks = [doc_prefix + t for t in chunk_texts]
            t0_idx = time.perf_counter()
            chunk_embeddings = encode_custom(formatted_chunks, batch_size=32)
            t_idx_sec = time.perf_counter() - t0_idx
            throughput_chunks_sec = round(len(all_chunks) / max(0.001, t_idx_sec), 1)

            # Profile Query Latency
            for wq in sample_queries[:10]:
                _ = encode_custom([q_prefix + wq], batch_size=1)

            timed_latencies_ms = []
            for sq in sample_queries:
                t0_q = time.perf_counter()
                _ = encode_custom([q_prefix + sq], batch_size=1)
                timed_latencies_ms.append((time.perf_counter() - t0_q) * 1000.0)

            lat_p50 = float(np.percentile(timed_latencies_ms, 50))
            lat_p95 = float(np.percentile(timed_latencies_ms, 95))
            peak_rss_mb = process.memory_info().rss / (1024 * 1024)

            # Partition embeddings by paper
            paper_embs_map: Dict[str, np.ndarray] = {}
            offset = 0
            for p_id in paper_chunks_map:
                p_len = len(paper_chunks_map[p_id])
                paper_embs_map[p_id] = chunk_embeddings[offset:offset + p_len]
                offset += p_len

            # Accuracy Retrieval
            q_formatted = [q_prefix + q["question"] for q in queries]
            q_embeddings = encode_custom(q_formatted, batch_size=32)

            for idx, q in enumerate(queries):
                p_id = q["paper_arxiv_id"]
                cand_chunks = paper_chunks_map[p_id]
                cand_embs = paper_embs_map[p_id]
                q_vec = q_embeddings[idx]

                scores = np.dot(cand_embs, q_vec)
                ranked_indices = np.argsort(-scores)

                ev_list = q["evidence"] if isinstance(q["evidence"], list) else [q["evidence"]]
                ranked_relevances = [
                    1 if is_chunk_hit(cand_chunks[i], p_id, verbatim_evidence_quote=q.get("verbatim_evidence_quote", ""), evidence_list=ev_list, tau=0.55) else 0
                    for i in ranked_indices
                ]

                R_q = q["R_q"]
                ndcg10 = compute_ndcg(ranked_relevances, R_q, k=10)
                ndcg4 = compute_ndcg(ranked_relevances, R_q, k=4)
                rec20 = float(sum(ranked_relevances[:20]) / max(1, R_q)) if R_q > 0 else 0.0

                first_hit_rank = next((r_idx for r_idx, r in enumerate(ranked_relevances[:10]) if r > 0), None)
                mrr10 = 1.0 / (first_hit_rank + 1) if first_hit_rank is not None else 0.0

                query_scores_ndcg10[p_id].append(ndcg10)
                query_scores_ndcg4[p_id].append(ndcg4)
                query_scores_rec20[p_id].append(rec20)
                query_scores_mrr10[p_id].append(mrr10)

            del custom_model, custom_tok
            gc.collect()

        else:
            # Standard SentenceTransformers
            model = SentenceTransformer(name, trust_remote_code=trust_remote)

            # Profile Indexing Throughput
            formatted_chunks = [doc_prefix + t for t in chunk_texts]
            t0_idx = time.perf_counter()
            chunk_embeddings = model.encode(
                formatted_chunks,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            t_idx_sec = time.perf_counter() - t0_idx
            throughput_chunks_sec = round(len(all_chunks) / max(0.001, t_idx_sec), 1)

            # Profile Query Latency
            for wq in sample_queries[:10]:
                _ = model.encode([q_prefix + wq], batch_size=1, normalize_embeddings=True, show_progress_bar=False)

            timed_latencies_ms = []
            for sq in sample_queries:
                t0_q = time.perf_counter()
                _ = model.encode([q_prefix + sq], batch_size=1, normalize_embeddings=True, show_progress_bar=False)
                timed_latencies_ms.append((time.perf_counter() - t0_q) * 1000.0)

            lat_p50 = float(np.percentile(timed_latencies_ms, 50))
            lat_p95 = float(np.percentile(timed_latencies_ms, 95))
            peak_rss_mb = process.memory_info().rss / (1024 * 1024)

            # Partition embeddings by paper
            paper_embs_map: Dict[str, np.ndarray] = {}
            offset = 0
            for p_id in paper_chunks_map:
                p_len = len(paper_chunks_map[p_id])
                paper_embs_map[p_id] = chunk_embeddings[offset:offset + p_len]
                offset += p_len

            # Accuracy Retrieval
            q_formatted = [q_prefix + q["question"] for q in queries]
            q_embeddings = model.encode(
                q_formatted,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

            for idx, q in enumerate(queries):
                p_id = q["paper_arxiv_id"]
                cand_chunks = paper_chunks_map[p_id]
                cand_embs = paper_embs_map[p_id]
                q_vec = q_embeddings[idx]

                scores = np.dot(cand_embs, q_vec)
                ranked_indices = np.argsort(-scores)

                ev_list = q["evidence"] if isinstance(q["evidence"], list) else [q["evidence"]]
                ranked_relevances = [
                    1 if is_chunk_hit(cand_chunks[i], p_id, verbatim_evidence_quote=q.get("verbatim_evidence_quote", ""), evidence_list=ev_list, tau=0.55) else 0
                    for i in ranked_indices
                ]

                R_q = q["R_q"]
                ndcg10 = compute_ndcg(ranked_relevances, R_q, k=10)
                ndcg4 = compute_ndcg(ranked_relevances, R_q, k=4)
                rec20 = float(sum(ranked_relevances[:20]) / max(1, R_q)) if R_q > 0 else 0.0

                first_hit_rank = next((r_idx for r_idx, r in enumerate(ranked_relevances[:10]) if r > 0), None)
                mrr10 = 1.0 / (first_hit_rank + 1) if first_hit_rank is not None else 0.0

                query_scores_ndcg10[p_id].append(ndcg10)
                query_scores_ndcg4[p_id].append(ndcg4)
                query_scores_rec20[p_id].append(rec20)
                query_scores_mrr10[p_id].append(mrr10)

            del model
            gc.collect()

        # Save query nDCG@10 for cluster bootstrap comparisons
        all_models_query_ndcg10[m_id] = query_scores_ndcg10

        # Calculate macro means across all 615 queries
        flat_ndcg10 = [score for p_scores in query_scores_ndcg10.values() for score in p_scores]
        flat_ndcg4 = [score for p_scores in query_scores_ndcg4.values() for score in p_scores]
        flat_rec20 = [score for p_scores in query_scores_rec20.values() for score in p_scores]
        flat_mrr10 = [score for p_scores in query_scores_mrr10.values() for score in p_scores]

        mean_ndcg10 = float(np.mean(flat_ndcg10))
        mean_ndcg4 = float(np.mean(flat_ndcg4))
        mean_rec20 = float(np.mean(flat_rec20))
        mean_mrr10 = float(np.mean(flat_mrr10))

        # Paper-cluster bootstrap 95% CIs for nDCG@10
        # Compute bootstrap distribution for candidate model alone
        rng = np.random.default_rng(42)
        paper_keys = sorted(list(query_scores_ndcg10.keys()))
        boot_ndcg10 = []
        for _ in range(2000):
            sample_p = rng.choice(paper_keys, size=len(paper_keys), replace=True)
            resampled = [s for p in sample_p for s in query_scores_ndcg10[p]]
            boot_ndcg10.append(float(np.mean(resampled)))
        ci_lower = float(np.percentile(boot_ndcg10, 2.5))
        ci_upper = float(np.percentile(boot_ndcg10, 97.5))

        model_entry = {
            "id": m_id,
            "name": name,
            "short_name": short_name,
            "type": m_type,
            "dim": spec["dim"],
            "params_m": spec["params_m"],
            "license": spec["license"],
            "metrics": {
                "ndcg10": {
                    "mean": round(mean_ndcg10, 4),
                    "ci_95": [round(ci_lower, 4), round(ci_upper, 4)],
                },
                "ndcg4": {
                    "mean": round(mean_ndcg4, 4),
                },
                "recall20": {
                    "mean": round(mean_rec20, 4),
                },
                "mrr10": {
                    "mean": round(mean_mrr10, 4),
                },
            },
            "efficiency": {
                "indexing_throughput_chunks_sec": throughput_chunks_sec,
                "query_latency_p50_ms": round(lat_p50, 2),
                "query_latency_p95_ms": round(lat_p95, 2),
                "peak_ram_mb": round(peak_rss_mb, 1),
            },
        }

        print(f"[RESULT] {short_name:22s} | nDCG@10: {mean_ndcg10:.4f} [{ci_lower:.4f}, {ci_upper:.4f}] | nDCG@4: {mean_ndcg4:.4f} | Rec@20: {mean_rec20:.4f} | Throughput: {throughput_chunks_sec:5.1f} ch/s | Latency P50: {lat_p50:5.2f} ms")
        benchmark_results["models"].append(model_entry)

    # -------------------------------------------------------------
    # Compute Paired Statistical Comparisons vs all-MiniLM-L6-v2
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PAIRED PAPER-CLUSTER BOOTSTRAP SIGNIFICANCE VS all-MiniLM-L6-v2 (nDCG@10)")
    print("=" * 80)

    base_scores = all_models_query_ndcg10[base_model_id]

    for m_dict in benchmark_results["models"]:
        m_id = m_dict["id"]
        cand_scores = all_models_query_ndcg10[m_id]

        if m_id == base_model_id:
            m_dict["stats_vs_baseline"] = {
                "diff_ndcg10": 0.0,
                "ci_95": [0.0, 0.0],
                "p_value": 1.0,
                "significant_05": False,
            }
            continue

        mean_diff, (ci_low, ci_high), p_val = paired_cluster_bootstrap(
            paper_scores_base=base_scores,
            paper_scores_cand=cand_scores,
            n_bootstraps=2000,
            seed=42,
            estimand="query",
        )

        sig = bool(p_val < 0.05)
        m_dict["stats_vs_baseline"] = {
            "diff_ndcg10": round(mean_diff, 4),
            "ci_95": [round(ci_low, 4), round(ci_high, 4)],
            "p_value": round(p_val, 4),
            "significant_05": sig,
        }

        sig_flag = "(*)" if sig else "(ns)"
        print(f"  {m_dict['short_name']:22s} vs MiniLM: Delta={mean_diff:+.4f} [{ci_low:+.4f}, {ci_high:+.4f}], p={p_val:.4f} {sig_flag}")

    # Save to JSON
    with open(benchmark_json_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_results, f, indent=2)

    print(f"\n[OK] Serialized full benchmark results to: {benchmark_json_path}")
    return benchmark_results


if __name__ == "__main__":
    run_benchmark()
