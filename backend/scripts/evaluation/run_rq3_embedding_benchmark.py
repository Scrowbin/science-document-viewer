"""
RQ3: Dense Embedding Representation Benchmark for Academic Passage Retrieval.
Evaluates 5 candidate open-source models:
  1. sentence-transformers/all-MiniLM-L6-v2 (Baseline, 384-dim, Apache-2.0, max_seq=256)
  2. intfloat/e5-small-v2 (384-dim, MIT, max_seq=512)
  3. BAAI/bge-small-en-v1.5 (384-dim, MIT, max_seq=512)
  4. Snowflake/snowflake-arctic-embed-s (384-dim, Apache-2.0, max_seq=512)
  5. nomic-ai/modernbert-embed-base (768-dim, Apache-2.0, max_seq=8192)

Experimental Controls:
  - Extractor: Fixed to chosen extractor from RQ1.
  - Chunker: Fixed to chosen chunker from RQ2.
  - Search Engine: Exact Brute-Force Cosine Similarity (NumPy BLAS on FP32 unit-normalized vectors).
  - CPU Threads: Fixed torch.set_num_threads(4) on AMD Ryzen 5 5600.
  - Asymmetric Prefix Integrity: Query and passage prefixes enforced via MODEL_PREFIX_SPECS.
  - Token Context Limits: Evaluates subword token truncation rate per model context window.
  - Statistical Rigor: 95% Confidence Intervals via Paper-Cluster Bootstrap (B=2000, seed=42)
    and paired tests vs all-MiniLM-L6-v2 with Holm-Bonferroni correction.
  - Isolated Efficiency Profiling: Peak RSS measured in dedicated standalone subprocess per model.
  - Dual-Axis Reporting: Separates (a) Best Retrieval Quality vs (b) Production Deployment Selection.

Scope Notice:
  "RQ3 hien chi danh gia hieu qua truy xuat; phan answer quality voi LLM de dot sau."
"""

import argparse
import gc
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

# Subprocess worker for isolated peak RSS measurement
if "--measure-rss-worker" in sys.argv:
    import psutil
    import torch
    from sentence_transformers import SentenceTransformer

    torch.set_num_threads(4)
    proc = psutil.Process()
    target_model_name = sys.argv[2]
    target_q_prefix = sys.argv[3]
    target_doc_prefix = sys.argv[4]

    model = SentenceTransformer(target_model_name)
    sample_docs = [target_doc_prefix + "Sample scientific paragraph for isolated RSS profiling."] * 32
    _ = model.encode(sample_docs, batch_size=32, show_progress_bar=False)
    _ = model.encode([target_q_prefix + "Sample retrieval query."], batch_size=1, show_progress_bar=False)

    peak_rss = proc.memory_info().rss / (1024 * 1024)
    print(f"PEAK_RSS_MB:{peak_rss:.2f}")
    sys.exit(0)

import numpy as np
import psutil
import torch
from sentence_transformers import SentenceTransformer

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
EVAL_DIR = WORKSPACE_ROOT / "eval"
PREPARED_DIR = EVAL_DIR / "prepared"
RESULTS_DIR = EVAL_DIR / "results"
PDFS_DIR = WORKSPACE_ROOT / "data" / "sample_academic_pdfs"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from apps.documents.services.chunkers import chunk_document_unified
from apps.documents.services.chunking_utils import extract_sections_from_pdf
from apps.documents.services.rag_service import MODEL_PREFIX_SPECS, get_model_prefix
from eval_common.relevance import (
    clean_evidence,
    count_relevant_chunks,
    is_chunk_hit,
)
from eval_common.stats import (
    cluster_bootstrap_ci,
    compute_hit_at_k,
    compute_mrr,
    compute_ndcg,
    compute_recall,
    holm_bonferroni_correction,
    paired_cluster_bootstrap,
)

MODELS_TO_BENCHMARK = [
    {
        "id": "all-MiniLM-L6-v2",
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "short_name": "MiniLM-L6-v2",
        "dim": 384,
        "params_m": 22.7,
        "license": "Apache-2.0",
        "max_seq_length": 256,
        "is_baseline": True,
    },
    {
        "id": "e5-small-v2",
        "name": "intfloat/e5-small-v2",
        "short_name": "E5-Small-v2",
        "dim": 384,
        "params_m": 33.4,
        "license": "MIT",
        "max_seq_length": 512,
        "is_baseline": False,
    },
    {
        "id": "bge-small-en-v1.5",
        "name": "BAAI/bge-small-en-v1.5",
        "short_name": "BGE-Small-v1.5",
        "dim": 384,
        "params_m": 33.4,
        "license": "MIT",
        "max_seq_length": 512,
        "is_baseline": False,
    },
    {
        "id": "snowflake-arctic-embed-s",
        "name": "Snowflake/snowflake-arctic-embed-s",
        "short_name": "Arctic-Embed-S",
        "dim": 384,
        "params_m": 33.2,
        "license": "Apache-2.0",
        "max_seq_length": 512,
        "is_baseline": False,
    },
    {
        "id": "modernbert-embed-base",
        "name": "nomic-ai/modernbert-embed-base",
        "short_name": "ModernBERT-Embed",
        "dim": 768,
        "params_m": 149.0,
        "license": "Apache-2.0",
        "max_seq_length": 8192,
        "is_baseline": False,
    },
]


def measure_isolated_rss(model_name: str, q_prefix: str, doc_prefix: str) -> float:
    """Invokes worker subprocess to measure isolated peak RSS."""
    try:
        cmd = [
            sys.executable,
            __file__,
            "--measure-rss-worker",
            model_name,
            q_prefix,
            doc_prefix,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        for line in res.stdout.strip().splitlines():
            if line.startswith("PEAK_RSS_MB:"):
                return float(line.split(":")[1].strip())
    except Exception as exc:
        print(f"  [WARN] Failed to measure isolated RSS: {exc}")
    return 0.0


def check_subword_truncation(model: SentenceTransformer, max_seq_length: int, formatted_chunks: List[str]) -> Tuple[int, float]:
    """Computes exact count and percentage of chunks exceeding model's max token capacity."""
    tokenizer = getattr(model, "tokenizer", None)
    if tokenizer is None:
        return 0, 0.0
    truncated_count = 0
    for chunk_text in formatted_chunks:
        tokens = tokenizer.encode(chunk_text, truncation=False)
        if len(tokens) > max_seq_length:
            truncated_count += 1
    pct = (truncated_count / max(1, len(formatted_chunks))) * 100.0
    return truncated_count, pct


def load_corpus_papers_and_queries(
    extractor_name: str = "pymupdf_layout",
    chunk_strategy: str = "section_token",
    split: str = "dev",
    limit: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    Loads papers and extracts sections using the fixed extractor from RQ1,
    then chunks them using the winning chunker from RQ2.
    """
    with open(PREPARED_DIR / "dev_held_out_split.json", "r", encoding="utf-8") as f:
        dev_pids = json.load(f)["dev_papers"]

    with open(PREPARED_DIR / "qasper_sampled.json", "r", encoding="utf-8") as f:
        dev_queries_all = json.load(f)

    # Find physical PDFs across candidate directories
    pdf_dirs = [
        WORKSPACE_ROOT / "eval" / "pdfs" / "dev",
        WORKSPACE_ROOT / "eval" / "data" / "pdfs",
        WORKSPACE_ROOT / "sample__papers",
    ]
    available_pdfs: Dict[str, Path] = {}
    for aid in dev_pids:
        for d in pdf_dirs:
            cand = d / f"{aid}.pdf"
            if cand.exists() and cand.stat().st_size > 10000:
                available_pdfs[aid] = cand
                break

    selected_pids = [pid for pid in dev_pids if pid in available_pdfs]
    if limit is not None and limit > 0:
        selected_pids = selected_pids[:limit]

    print(f"[DATASET] Loading {len(selected_pids)} papers with extractor '{extractor_name}' and chunker '{chunk_strategy}'...")

    all_chunks: List[Dict[str, Any]] = []
    paper_chunks_map: Dict[str, List[Dict[str, Any]]] = {}

    for idx, aid in enumerate(selected_pids):
        pdf_path = available_pdfs[aid]
        # RQ1 extractor: PyMuPDF Layout
        sections = extract_sections_from_pdf(str(pdf_path))
        # RQ2 chunker
        chunks = chunk_document_unified(
            sections=sections,
            strategy=chunk_strategy,
            max_tokens=400,
            overlap=80,
            semantic_percentile=25.0,
            paper_id=aid,
        )
        for c_idx, c in enumerate(chunks):
            c["paper_arxiv_id"] = aid
            c["chunk_id"] = f"{aid}_c_{c_idx}"
            all_chunks.append(c)
        paper_chunks_map[aid] = chunks

    # Prepare queries
    queries: List[Dict[str, Any]] = []
    for q in dev_queries_all:
        aid = q.get("paper_arxiv_id", q.get("arxiv_id"))
        if aid in paper_chunks_map and len(paper_chunks_map[aid]) > 0 and q.get("question_type") != "unanswerable":
            ev_list = q.get("evidence_list", [])
            if not ev_list and q.get("verbatim_evidence_quote"):
                ev_list = [q["verbatim_evidence_quote"]]
            queries.append({
                "query_id": q.get("id", q.get("query_id")),
                "paper_arxiv_id": aid,
                "question": q["question"],
                "question_type": q.get("question_type", "factoid"),
                "verbatim_evidence_quote": q.get("verbatim_evidence_quote", ""),
                "evidence_list": ev_list,
                "evidence": ev_list,
            })

    print(f"[DATASET] Extracted {len(all_chunks)} chunks for {len(paper_chunks_map)} papers across {len(queries)} queries.")
    return queries, all_chunks, paper_chunks_map


def main():
    parser = argparse.ArgumentParser(description="RQ3: Dense Embedding Representation Benchmark")
    parser.add_argument("--extractor", type=str, default="pymupdf_layout", help="Fixed extractor from RQ1")
    parser.add_argument("--chunker", type=str, default="section_token", help="Fixed chunker from RQ2")
    parser.add_argument("--tau", type=float, default=0.50, help="Relevance containment threshold")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of papers for quick run")
    parser.add_argument("--dry-run", action="store_true", help="Quick dry run on 2 papers")
    args = parser.parse_args()

    torch.set_num_threads(4)

    limit = 2 if args.dry_run else args.limit

    print("=" * 80)
    print("RQ3: DENSE EMBEDDING REPRESENTATION BENCHMARK (RETRIEVAL ONLY)")
    print(f"Extractor: {args.extractor} | Chunker: {args.chunker} | Tau: {args.tau}")
    print("=" * 80)

    queries, all_chunks, paper_chunks_map = load_corpus_papers_and_queries(
        extractor_name=args.extractor,
        chunk_strategy=args.chunker,
        limit=limit,
    )

    if not queries or not all_chunks:
        print("[ERROR] No queries or chunks found.")
        sys.exit(1)

    # Pre-calculate R_q
    print("[EVAL] Pre-computing relevance counts R_q across queries...")
    for q in queries:
        cand_chunks = paper_chunks_map[q["paper_arxiv_id"]]
        q["R_q"] = count_relevant_chunks(
            cand_chunks,
            q["paper_arxiv_id"],
            verbatim_evidence_quote=q.get("verbatim_evidence_quote", ""),
            evidence_list=q.get("evidence_list", []),
            tau=args.tau,
        )

    results_data: Dict[str, Any] = {
        "metadata": {
            "title": "RQ3: Dense Embedding Representation Benchmark (Retrieval Only)",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scope_notice": "RQ3 hien chi danh gia hieu qua truy xuat; phan answer quality voi LLM de dot sau.",
            "experimental_controls": {
                "extractor": args.extractor,
                "chunker": args.chunker,
                "relevance_tau": args.tau,
                "torch_threads": 4,
                "similarity": "exact_brute_force_cosine (NumPy BLAS FP32)",
                "bootstrap_resamples": 2000,
                "bootstrap_seed": 42,
            },
            "dataset_consistency": {
                "active_papers": len(paper_chunks_map),
                "total_chunks": len(all_chunks),
                "total_queries": len(queries),
            },
        },
        "models": [],
    }

    all_models_ndcg10_by_paper: Dict[str, Dict[str, List[float]]] = {}
    detailed_query_records: List[Dict[str, Any]] = []

    for m_idx, spec in enumerate(MODELS_TO_BENCHMARK):
        m_id = spec["id"]
        m_name = spec["name"]
        short_name = spec["short_name"]
        q_prefix = get_model_prefix(m_name, is_query=True)
        doc_prefix = get_model_prefix(m_name, is_query=False)

        print(f"\n[{m_idx + 1}/{len(MODELS_TO_BENCHMARK)}] Benchmarking: {short_name} ({m_name})")
        print(f"  Prefixes -> query: '{q_prefix}', doc: '{doc_prefix}'")

        # Isolated Peak RSS
        print("  Measuring isolated Peak RSS via dedicated subprocess...")
        peak_rss_mb = measure_isolated_rss(m_name, q_prefix, doc_prefix)
        print(f"  Peak RSS: {peak_rss_mb:.1f} MB")

        # Load Model in main process for retrieval and throughput
        t0_load = time.perf_counter()
        model = SentenceTransformer(m_name)
        t_load_sec = time.perf_counter() - t0_load

        # Check Token Truncation
        formatted_chunks = [doc_prefix + c.get("text", "") for c in all_chunks]
        trunc_count, trunc_pct = check_subword_truncation(model, spec["max_seq_length"], formatted_chunks)
        print(f"  Context window: {spec['max_seq_length']} | Truncated chunks: {trunc_count}/{len(all_chunks)} ({trunc_pct:.1f}%)")

        # Measure Indexing Throughput (batch_size=32)
        print(f"  Encoding {len(formatted_chunks)} chunks (batch=32)...")
        t0_idx = time.perf_counter()
        chunk_embeddings = model.encode(formatted_chunks, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        t_idx_sec = time.perf_counter() - t0_idx
        throughput = round(len(all_chunks) / max(0.001, t_idx_sec), 1)
        print(f"  Indexing throughput: {throughput} chunks/s ({t_idx_sec:.2f}s)")

        # Measure Single-Query Latency (batch=1, 100 queries, 10 warm-up)
        sample_queries = [q["question"] for q in queries[:100]]
        for wq in sample_queries[:10]:
            _ = model.encode([q_prefix + wq], batch_size=1, show_progress_bar=False, normalize_embeddings=True)

        timed_latencies: List[float] = []
        for sq in sample_queries:
            t0_q = time.perf_counter()
            _ = model.encode([q_prefix + sq], batch_size=1, show_progress_bar=False, normalize_embeddings=True)
            timed_latencies.append((time.perf_counter() - t0_q) * 1000.0)

        lat_p50 = float(np.percentile(timed_latencies, 50))
        lat_p95 = float(np.percentile(timed_latencies, 95))
        print(f"  Query Latency: P50={lat_p50:.1f}ms, P95={lat_p95:.1f}ms")

        # Partition embeddings by paper
        paper_embs_map: Dict[str, np.ndarray] = {}
        offset = 0
        for p_id in paper_chunks_map:
            p_len = len(paper_chunks_map[p_id])
            paper_embs_map[p_id] = chunk_embeddings[offset:offset + p_len]
            offset += p_len

        # Encode all queries
        formatted_queries = [q_prefix + q["question"] for q in queries]
        query_embeddings = model.encode(formatted_queries, batch_size=32, show_progress_bar=False, normalize_embeddings=True)

        # Retrieval Evaluation
        paper_ndcg10: Dict[str, List[float]] = {p: [] for p in paper_chunks_map}
        all_ndcg4: List[float] = []
        all_ndcg10: List[float] = []
        all_recall20: List[float] = []
        all_mrr10: List[float] = []
        all_hit1: List[float] = []
        all_hit3: List[float] = []
        all_hit5: List[float] = []

        for q_idx, q in enumerate(queries):
            p_id = q["paper_arxiv_id"]
            cand_chunks = paper_chunks_map[p_id]
            cand_embs = paper_embs_map[p_id]
            q_vec = query_embeddings[q_idx]

            scores = np.dot(cand_embs, q_vec)
            ranked_indices = np.argsort(-scores)

            ev_list = q.get("evidence_list", [])
            ranked_relevances = [
                1 if is_chunk_hit(
                    cand_chunks[i],
                    p_id,
                    verbatim_evidence_quote=q.get("verbatim_evidence_quote", ""),
                    evidence_list=ev_list,
                    tau=args.tau,
                ) else 0
                for i in ranked_indices
            ]

            R_q = q["R_q"]
            n10 = compute_ndcg(ranked_relevances, R_q, k=10)
            n4 = compute_ndcg(ranked_relevances, R_q, k=4)
            r20 = compute_recall(ranked_relevances, R_q, k=20)
            m10 = compute_mrr(ranked_relevances, k=10)
            h1 = compute_hit_at_k(ranked_relevances, k=1)
            h3 = compute_hit_at_k(ranked_relevances, k=3)
            h5 = compute_hit_at_k(ranked_relevances, k=5)

            paper_ndcg10[p_id].append(n10)
            all_ndcg4.append(n4)
            all_ndcg10.append(n10)
            all_recall20.append(r20)
            all_mrr10.append(m10)
            all_hit1.append(h1)
            all_hit3.append(h3)
            all_hit5.append(h5)

            detailed_query_records.append({
                "model_id": m_id,
                "query_id": q["query_id"],
                "paper_arxiv_id": p_id,
                "question": q["question"],
                "question_type": q["question_type"],
                "R_q": R_q,
                "ndcg4": n4,
                "ndcg10": n10,
                "recall20": r20,
                "mrr10": m10,
                "hit1": h1,
            })

        all_models_ndcg10_by_paper[m_id] = paper_ndcg10

        # Cluster bootstrap CI
        mean_ndcg10, ci_low, ci_high = cluster_bootstrap_ci(paper_ndcg10, n_bootstraps=2000, seed=42)

        model_stat = {
            "id": m_id,
            "name": m_name,
            "short_name": short_name,
            "dim": spec["dim"],
            "params_m": spec["params_m"],
            "license": spec["license"],
            "max_seq_length": spec["max_seq_length"],
            "truncation": {
                "truncated_chunks": trunc_count,
                "total_chunks": len(all_chunks),
                "truncation_rate_pct": round(trunc_pct, 2),
            },
            "metrics": {
                "ndcg10": round(float(np.mean(all_ndcg10)), 4),
                "ndcg10_ci95": [round(ci_low, 4), round(ci_high, 4)],
                "ndcg4": round(float(np.mean(all_ndcg4)), 4),
                "recall20": round(float(np.mean(all_recall20)), 4),
                "mrr10": round(float(np.mean(all_mrr10)), 4),
                "hit1": round(float(np.mean(all_hit1)), 4),
                "hit3": round(float(np.mean(all_hit3)), 4),
                "hit5": round(float(np.mean(all_hit5)), 4),
            },
            "efficiency": {
                "latency_p50_ms": round(lat_p50, 2),
                "latency_p95_ms": round(lat_p95, 2),
                "throughput_chunks_sec": throughput,
                "peak_rss_mb": round(peak_rss_mb, 1),
            },
            "paired_test_vs_baseline": None,
        }
        results_data["models"].append(model_stat)
        print(f"  Results -> nDCG@10: {model_stat['metrics']['ndcg10']} (95% CI [{ci_low:.4f}, {ci_high:.4f}]), Recall@20: {model_stat['metrics']['recall20']}")

        # Clean memory
        del model, chunk_embeddings, query_embeddings
        gc.collect()

    # Paired Statistical Tests vs all-MiniLM-L6-v2 with Holm-Bonferroni Correction
    base_scores = all_models_ndcg10_by_paper["all-MiniLM-L6-v2"]
    p_values_to_adjust: List[Tuple[int, float]] = []

    for idx, m_stat in enumerate(results_data["models"]):
        m_id = m_stat["id"]
        if m_id == "all-MiniLM-L6-v2":
            m_stat["paired_test_vs_baseline"] = {
                "delta_ndcg10": 0.0,
                "p_value_raw": 1.0,
                "p_value_adjusted": 1.0,
                "significant_05": False,
                "correction": "Holm-Bonferroni",
            }
        else:
            diff, ci_pair, p_val = paired_cluster_bootstrap(base_scores, all_models_ndcg10_by_paper[m_id], n_bootstraps=2000, seed=42)
            p_values_to_adjust.append((idx, p_val))
            m_stat["paired_test_vs_baseline"] = {
                "delta_ndcg10": round(diff, 4),
                "delta_ndcg10_ci95": [round(ci_pair[0], 4), round(ci_pair[1], 4)],
                "p_value_raw": round(p_val, 4),
                "p_value_adjusted": None,
                "significant_05": False,
                "correction": "Holm-Bonferroni",
            }

    # Apply Holm-Bonferroni correction
    if p_values_to_adjust:
        raw_ps = [p for _, p in p_values_to_adjust]
        adj_results = holm_bonferroni_correction(raw_ps)
        for (m_idx, _), r_dict in zip(p_values_to_adjust, adj_results):
            results_data["models"][m_idx]["paired_test_vs_baseline"]["p_value_adjusted"] = round(float(r_dict["adj_p"]), 4)
            results_data["models"][m_idx]["paired_test_vs_baseline"]["significant_05"] = bool(r_dict["significant"])

    # Dual-Axis Analysis: Best Quality vs Chosen Deployment
    sorted_by_quality = sorted(results_data["models"], key=lambda m: m["metrics"]["ndcg10"], reverse=True)
    best_quality_model = sorted_by_quality[0]

    # Criteria for deployment: high accuracy + lowest latency/RAM
    deployment_candidates = [m for m in results_data["models"] if m["efficiency"]["latency_p50_ms"] < 30.0 and m["efficiency"]["peak_rss_mb"] < 1000]
    chosen_deployment = max(deployment_candidates, key=lambda m: m["metrics"]["ndcg10"]) if deployment_candidates else best_quality_model

    results_data["dual_axis_conclusions"] = {
        "best_retrieval_quality": {
            "model_id": best_quality_model["id"],
            "model_name": best_quality_model["name"],
            "ndcg10": best_quality_model["metrics"]["ndcg10"],
            "rationale": "Highest retrieval nDCG@10 rank performance across evaluation set.",
        },
        "chosen_deployment_model": {
            "model_id": chosen_deployment["id"],
            "model_name": chosen_deployment["name"],
            "ndcg10": chosen_deployment["metrics"]["ndcg10"],
            "latency_p50_ms": chosen_deployment["efficiency"]["latency_p50_ms"],
            "peak_rss_mb": chosen_deployment["efficiency"]["peak_rss_mb"],
            "rationale": "Optimal Pareto trade-off between statistical accuracy, low CPU latency, and low memory footprint.",
        },
    }

    # Save outputs
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json_path = RESULTS_DIR / f"rq3_embedding_{timestamp_str}.json"
    out_jsonl_path = RESULTS_DIR / f"rq3_embedding_queries_{timestamp_str}.jsonl"

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    with open(out_jsonl_path, "w", encoding="utf-8") as f:
        for r in detailed_query_records:
            f.write(json.dumps(r) + "\n")

    print("\n" + "=" * 80)
    print("RQ3 BENCHMARK COMPLETE")
    print(f"Summary JSON: {out_json_path}")
    print(f"Query Logs:   {out_jsonl_path}")
    print(f"Best Quality Model:    {best_quality_model['name']} (nDCG@10={best_quality_model['metrics']['ndcg10']})")
    print(f"Chosen Deployment:     {chosen_deployment['name']} (nDCG@10={chosen_deployment['metrics']['ndcg10']}, Latency P50={chosen_deployment['efficiency']['latency_p50_ms']}ms, Peak RSS={chosen_deployment['efficiency']['peak_rss_mb']}MB)")
    print("=" * 80)


if __name__ == "__main__":
    main()
