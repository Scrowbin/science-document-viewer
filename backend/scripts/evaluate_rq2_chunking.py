"""
RQ2: Controlled Chunking Strategy Ablation Study (Retrieval Performance Only).
Compares 6 chunking strategies across fixed extractor and fixed dense representation:
  1. fixed_size (Baseline): Continuous sliding window across full text, strictly ignoring headings, zero overlap (max_tokens=400).
  2. fixed_size_overlap: Continuous sliding window across full text with overlap (max_tokens=400, overlap=80).
  3. semantic: Sentence splitting + consecutive sentence embedding similarity + drop thresholding (percentile-based, pre-registered at 25th percentile) with max_tokens ceiling (400).
  4. section: Pure section-level chunks (1 chunk per section).
  5. section_token: Section-aware chunking bounded to max_tokens (400), zero overlap.
  6. section_overlap: Section-aware chunking with token limits and sliding window overlap (max_tokens=400, overlap=80).

Experimental Controls:
  - Extractor: Fixed to chosen extractor from RQ1 (PyMuPDF Layout-Aware).
  - Dense Representation: Fixed champion intfloat/e5-small-v2 (384-dim, 512-token context window).
  - Search Engine: Exact Brute-Force Cosine Similarity (NumPy BLAS FP32 unit-normalized vectors).
  - CPU Threads: Fixed torch.set_num_threads(4) on AMD Ryzen 5 5600.
  - Uniform Relevance Rule: Evidence containment threshold tau = X (tested with primary X=0.50 and sensitivity X=0.30).
  - Statistical Rigor: 95% Confidence Intervals via Paper-Cluster Bootstrap (B=2000, seed=42) and paired test vs fixed_size.

Scope Notice:
  "RQ2 hien chi danh gia hieu qua truy xuat; phan answer quality de dot sau."
  (Answer quality evaluation with LLM generation is explicitly deferred to later work).
"""

import argparse
import gc
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

os.environ["HF_HUB_OFFLINE"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

import numpy as np
import psutil
import torch
from sentence_transformers import SentenceTransformer

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from apps.documents.services.chunkers import (
    chunk_document_unified,
    estimate_tokens,
)
from apps.documents.services.chunking_utils import extract_sections_from_pdf
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
    paired_cluster_bootstrap,
)

CHUNK_STRATEGIES = [
    "fixed_size",
    "fixed_size_overlap",
    "semantic",
    "section",
    "section_token",
    "section_overlap",
]


def evaluate_retrieval_with_matrix(
    sim_matrix: np.ndarray,
    chunks: List[Dict[str, Any]],
    queries: List[Dict[str, Any]],
    paper_id: str,
    tau: float = 0.50,
    context_budget_tokens: int = 1600,
) -> Dict[str, Any]:
    """
    Evaluates dense retrieval across precomputed similarity matrix for given paper and queries.
    Avoids re-encoding chunks or queries when evaluating sensitivity thresholds or different metrics.
    """
    if len(chunks) == 0 or len(queries) == 0:
        return {
            "ndcg4": [],
            "ndcg10": [],
            "recall20": [],
            "mrr10": [],
            "budget_coverages": [],
            "query_records": [],
        }

    ndcg4_list = []
    ndcg10_list = []
    rec20_list = []
    mrr10_list = []
    budget_cov_list = []
    query_records = []

    for q_idx, q in enumerate(queries):
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        R_q = count_relevant_chunks(chunks, paper_id, quote, ev_list, tau=tau)

        ranked_indices = np.argsort(-sim_matrix[q_idx])
        ranked_rels = [
            1 if is_chunk_hit(chunks[i], paper_id, quote, ev_list, tau=tau) else 0
            for i in ranked_indices
        ]

        ndcg4 = compute_ndcg(ranked_rels, R_q, k=4)
        ndcg10 = compute_ndcg(ranked_rels, R_q, k=10)
        rec20 = compute_recall(ranked_rels, R_q, k=20)
        mrr10 = compute_mrr(ranked_rels, k=10)

        # Equal Token Budget Context Coverage:
        # Accumulate top-ranked chunks until total tokens reach context_budget_tokens
        accum_tokens = 0
        budget_has_evidence = 0
        for r_idx in ranked_indices:
            c = chunks[r_idx]
            accum_tokens += c.get("token_count", estimate_tokens(c.get("text", "")))
            if is_chunk_hit(c, paper_id, quote, ev_list, tau=tau):
                budget_has_evidence = 1
            if accum_tokens >= context_budget_tokens:
                break

        ndcg4_list.append(ndcg4)
        ndcg10_list.append(ndcg10)
        rec20_list.append(rec20)
        mrr10_list.append(mrr10)
        budget_cov_list.append(budget_has_evidence)

        query_records.append({
            "paper_arxiv_id": paper_id,
            "query_id": q.get("id", q.get("query_id")),
            "ndcg4": round(ndcg4, 4),
            "ndcg10": round(ndcg10, 4),
            "recall20": round(rec20, 4),
            "mrr10": round(mrr10, 4),
            "budget_covered": budget_has_evidence,
            "R_q": R_q,
        })

    return {
        "ndcg4": ndcg4_list,
        "ndcg10": ndcg10_list,
        "recall20": rec20_list,
        "mrr10": mrr10_list,
        "budget_coverages": budget_cov_list,
        "query_records": query_records,
    }


def run_rq2_chunking_benchmark(
    limit: Optional[int] = None,
    dry_run: bool = False,
    tau_primary: float = 0.50,
    tau_secondary: float = 0.30,
    context_budget_tokens: int = 1600,
    seed: int = 42,
) -> Dict[str, Any]:
    torch.set_num_threads(4)
    np.random.seed(seed)

    print("=" * 80)
    print("RQ2: COMPREHENSIVE DOCUMENT CHUNKING BENCHMARK (RETRIEVAL ONLY)")
    print("Strategies: fixed_size, fixed_size_overlap, semantic, section, section_token, section_overlap")
    print(f"Fixed Embedding: intfloat/e5-small-v2 (CPU 4 threads) | Equal Context Budget: {context_budget_tokens} tokens")
    print(f"Relevance Thresholds: Primary tau={tau_primary:.2f}, Sensitivity tau={tau_secondary:.2f}")
    print(f"Scope: RQ2 hiện chỉ đánh giá hiệu quả truy xuất; phần answer quality để đợt sau.")
    print("=" * 80)

    # Load Ground Truth
    dev_split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(dev_split_path, "r", encoding="utf-8") as f:
        dev_papers = json.load(f)["dev_papers"]
    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)

    pdf_dirs = [
        WORKSPACE_ROOT / "eval" / "pdfs" / "dev",
        WORKSPACE_ROOT / "eval" / "data" / "pdfs",
        WORKSPACE_ROOT / "sample__papers",
    ]
    available_pdfs: Dict[str, Path] = {}
    for aid in dev_papers:
        for d in pdf_dirs:
            cand = d / f"{aid}.pdf"
            if cand.exists() and cand.stat().st_size > 10000:
                available_pdfs[aid] = cand
                break

    paper_ids = [aid for aid in dev_papers if aid in available_pdfs]
    if limit:
        paper_ids = paper_ids[:limit]

    print(f"Evaluated Papers: {len(paper_ids)} (physical PDFs found on disk)")
    if dry_run:
        print("[DRY-RUN] Verification complete. Exiting without execution.")
        return {"status": "dry_run_success", "paper_count": len(paper_ids)}

    # Filter QA
    paper_queries_map: Dict[str, List[Dict[str, Any]]] = {}
    for q in qa_all:
        aid = q.get("paper_arxiv_id")
        if aid in paper_ids and q.get("question_type") != "unanswerable":
            paper_queries_map.setdefault(aid, []).append(q)

    # Initialize SentenceTransformer (intfloat/e5-small-v2)
    print("\n[INIT] Loading intfloat/e5-small-v2 from local cache...")
    embedder = SentenceTransformer("intfloat/e5-small-v2")

    # Metrics container per strategy
    strat_data: Dict[str, Dict[str, Any]] = {}
    for st in CHUNK_STRATEGIES:
        strat_data[st] = {
            "total_chunks": 0,
            "total_tokens": 0,
            "truncated_chunks_512": 0,
            "queries_by_paper_ndcg10_pri": {aid: [] for aid in paper_ids},
            "queries_by_paper_ndcg4_pri": {aid: [] for aid in paper_ids},
            "queries_by_paper_rec20_pri": {aid: [] for aid in paper_ids},
            "queries_by_paper_mrr10_pri": {aid: [] for aid in paper_ids},
            "queries_by_paper_budget_pri": {aid: [] for aid in paper_ids},
            # Sensitivity run
            "queries_by_paper_ndcg10_sec": {aid: [] for aid in paper_ids},
            "queries_by_paper_ndcg4_sec": {aid: [] for aid in paper_ids},
            "queries_by_paper_rec20_sec": {aid: [] for aid in paper_ids},
            "queries_by_paper_mrr10_sec": {aid: [] for aid in paper_ids},
            "queries_by_paper_budget_sec": {aid: [] for aid in paper_ids},
        }

    detailed_jsonl_rows: List[Dict[str, Any]] = []

    # Process Each Paper
    for p_idx, aid in enumerate(paper_ids, start=1):
        pdf_path = available_pdfs[aid]
        queries = paper_queries_map.get(aid, [])
        print(f"[{p_idx}/{len(paper_ids)}] Processing arXiv:{aid} ({len(queries)} queries)...")

        # 1. Extract sections using fixed layout-aware extractor
        sections = extract_sections_from_pdf(str(pdf_path))

        # 2. Encode queries for this paper once (reused across all 6 chunking strategies and both taus)
        if queries:
            q_texts = [f"query: {q['question']}" for q in queries]
            q_mat = embedder.encode(
                q_texts,
                batch_size=32,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        else:
            q_mat = np.zeros((0, 384), dtype=np.float32)

        # 3. Run Each Chunking Strategy
        for st in CHUNK_STRATEGIES:
            t0_chk = time.perf_counter()
            chunks = chunk_document_unified(
                sections=sections,
                strategy=st,
                max_tokens=400,
                overlap=80,
                embedder=embedder,
                semantic_percentile=25.0,
                paper_id=aid,
            )

            # Record chunk structural properties
            strat_data[st]["total_chunks"] += len(chunks)
            for c in chunks:
                t_count = c.get("token_count", estimate_tokens(c.get("text", "")))
                strat_data[st]["total_tokens"] += t_count
                if t_count > 512:
                    strat_data[st]["truncated_chunks_512"] += 1

            # Encode chunks once with passage prefix
            if chunks and len(queries) > 0:
                chunk_texts = [f"passage: {c['text']}" for c in chunks]
                chunk_mat = embedder.encode(
                    chunk_texts,
                    batch_size=32,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                sim_matrix = np.dot(q_mat, chunk_mat.T)
            else:
                sim_matrix = np.zeros((len(queries), len(chunks)), dtype=np.float32)

            # 4. Evaluate Retrieval under Primary tau (0.50)
            res_pri = evaluate_retrieval_with_matrix(
                sim_matrix=sim_matrix,
                chunks=chunks,
                queries=queries,
                paper_id=aid,
                tau=tau_primary,
                context_budget_tokens=context_budget_tokens,
            )
            strat_data[st]["queries_by_paper_ndcg10_pri"][aid].extend(res_pri["ndcg10"])
            strat_data[st]["queries_by_paper_ndcg4_pri"][aid].extend(res_pri["ndcg4"])
            strat_data[st]["queries_by_paper_rec20_pri"][aid].extend(res_pri["recall20"])
            strat_data[st]["queries_by_paper_mrr10_pri"][aid].extend(res_pri["mrr10"])
            strat_data[st]["queries_by_paper_budget_pri"][aid].extend(res_pri["budget_coverages"])

            # 5. Evaluate Retrieval under Secondary Sensitivity tau (0.30) reusing sim_matrix
            res_sec = evaluate_retrieval_with_matrix(
                sim_matrix=sim_matrix,
                chunks=chunks,
                queries=queries,
                paper_id=aid,
                tau=tau_secondary,
                context_budget_tokens=context_budget_tokens,
            )
            strat_data[st]["queries_by_paper_ndcg10_sec"][aid].extend(res_sec["ndcg10"])
            strat_data[st]["queries_by_paper_ndcg4_sec"][aid].extend(res_sec["ndcg4"])
            strat_data[st]["queries_by_paper_rec20_sec"][aid].extend(res_sec["recall20"])
            strat_data[st]["queries_by_paper_mrr10_sec"][aid].extend(res_sec["mrr10"])
            strat_data[st]["queries_by_paper_budget_sec"][aid].extend(res_sec["budget_coverages"])

            # Output query-level JSONL
            for q_rec in res_pri["query_records"]:
                q_rec["strategy"] = st
                q_rec["tau"] = tau_primary
                detailed_jsonl_rows.append(q_rec)

    # Summary Statistics & Paired Statistical Significance vs fixed_size baseline
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = WORKSPACE_ROOT / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_json_path = results_dir / f"rq2_chunking_{timestamp}.json"
    out_jsonl_path = results_dir / f"rq2_chunking_queries_{timestamp}.jsonl"

    baseline_strat = "fixed_size"
    base_scores_pri = strat_data[baseline_strat]["queries_by_paper_ndcg10_pri"]
    summary_table = []

    for st in CHUNK_STRATEGIES:
        d = strat_data[st]
        n_chunks = d["total_chunks"]
        avg_tokens = round(d["total_tokens"] / max(1, n_chunks), 1)
        trunc_rate = round((d["truncated_chunks_512"] / max(1, n_chunks)) * 100.0, 2)

        # Primary metrics
        flat_ndcg10 = [s for p in d["queries_by_paper_ndcg10_pri"].values() for s in p]
        flat_ndcg4 = [s for p in d["queries_by_paper_ndcg4_pri"].values() for s in p]
        flat_rec20 = [s for p in d["queries_by_paper_rec20_pri"].values() for s in p]
        flat_mrr10 = [s for p in d["queries_by_paper_mrr10_pri"].values() for s in p]
        flat_budget = [s for p in d["queries_by_paper_budget_pri"].values() for s in p]

        mean_ndcg10 = float(np.mean(flat_ndcg10)) if flat_ndcg10 else 0.0
        mean_ndcg4 = float(np.mean(flat_ndcg4)) if flat_ndcg4 else 0.0
        mean_rec20 = float(np.mean(flat_rec20)) if flat_rec20 else 0.0
        mean_mrr10 = float(np.mean(flat_mrr10)) if flat_mrr10 else 0.0
        budget_cov_pct = round(float(np.mean(flat_budget)) * 100.0, 2) if flat_budget else 0.0

        # Sensitivity metrics
        flat_ndcg10_sec = [s for p in d["queries_by_paper_ndcg10_sec"].values() for s in p]
        flat_rec20_sec = [s for p in d["queries_by_paper_rec20_sec"].values() for s in p]
        mean_ndcg10_sec = float(np.mean(flat_ndcg10_sec)) if flat_ndcg10_sec else 0.0
        mean_rec20_sec = float(np.mean(flat_rec20_sec)) if flat_rec20_sec else 0.0

        # Clustered Bootstrap CI (95%)
        _, ci_low, ci_high = cluster_bootstrap_ci(d["queries_by_paper_ndcg10_pri"], n_bootstraps=2000, seed=seed)

        # Paired test vs baseline
        if st == baseline_strat:
            diff, (p_ci_l, p_ci_h), p_val = 0.0, (0.0, 0.0), 1.0
        else:
            diff, (p_ci_l, p_ci_h), p_val = paired_cluster_bootstrap(
                base_scores_pri, d["queries_by_paper_ndcg10_pri"], n_bootstraps=2000, seed=seed
            )

        summary_table.append({
            "strategy": st,
            "total_chunks": n_chunks,
            "avg_tokens_per_chunk": avg_tokens,
            "subword_truncation_rate_pct": trunc_rate,
            "primary_metrics": {
                "tau": tau_primary,
                "ndcg10": {
                    "mean": round(mean_ndcg10, 4),
                    "ci_95": [round(ci_low, 4), round(ci_high, 4)],
                },
                "ndcg4": round(mean_ndcg4, 4),
                "recall20": round(mean_rec20, 4),
                "mrr10": round(mean_mrr10, 4),
                "context_budget_coverage_pct": budget_cov_pct,
            },
            "sensitivity_metrics": {
                "tau": tau_secondary,
                "ndcg10": round(mean_ndcg10_sec, 4),
                "recall20": round(mean_rec20_sec, 4),
            },
            "stats_vs_baseline": {
                "diff_ndcg10": round(diff, 4),
                "ci_95": [round(p_ci_l, 4), round(p_ci_h, 4)],
                "p_value": round(p_val, 4),
                "significant_05": bool(p_val < 0.05),
            },
        })

    # Pick champion chunker strictly by primary nDCG@10
    champion = max(summary_table, key=lambda x: x["primary_metrics"]["ndcg10"]["mean"])

    final_payload = {
        "metadata": {
            "experiment": "RQ2 Document Chunking Strategy Evaluation",
            "scope_notice": "RQ2 hiện chỉ đánh giá hiệu quả truy xuất; phần answer quality để đợt sau.",
            "timestamp": timestamp,
            "seed": seed,
            "torch_threads": 4,
            "papers_evaluated": len(paper_ids),
            "context_budget_tokens": context_budget_tokens,
            "baseline_strategy": baseline_strat,
            "champion_selected": champion["strategy"],
            "champion_rationale": (
                f"Selected {champion['strategy']} with top nDCG@10 = {champion['primary_metrics']['ndcg10']['mean']}, "
                f"Recall@20 = {champion['primary_metrics']['recall20']}, "
                f"Truncation Rate = {champion['subword_truncation_rate_pct']}%."
            ),
        },
        "summary": summary_table,
    }

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    with open(out_jsonl_path, "w", encoding="utf-8") as f:
        for row in detailed_jsonl_rows:
            f.write(json.dumps(row) + "\n")

    print("\n" + "=" * 80)
    print("RQ2 BENCHMARK SUMMARY TABLE (EQUAL TOKEN BUDGET = 1600 TOKENS)")
    print("=" * 80)
    print(f"{'Strategy':<20} {'Chunks':>7} {'AvgTok':>7} {'Trunc %':>8} {'BudgetCov':>10} {'nDCG@4':>8} {'nDCG@10 [95% CI]':>26} {'p-val':>8}")
    print("-" * 105)
    for row in summary_table:
        m = row["primary_metrics"]
        ndcg_str = f"{m['ndcg10']['mean']:.4f} [{m['ndcg10']['ci_95'][0]:.4f}, {m['ndcg10']['ci_95'][1]:.4f}]"
        sig_str = f"{row['stats_vs_baseline']['p_value']:.4f}{' *' if row['stats_vs_baseline']['significant_05'] else ''}"
        print(f"{row['strategy']:<20} {row['total_chunks']:>7} {row['avg_tokens_per_chunk']:>7.1f} {row['subword_truncation_rate_pct']:>7.1f}% {m['context_budget_coverage_pct']:>9.1f}% {m['ndcg4']:>8.4f} {ndcg_str:>26} {sig_str:>8}")

    print(f"\n[CHAMPION] RQ2 Selected Chunker: {champion['strategy']}")
    print(f"[SERIALIZATION] Master JSON: {out_json_path.relative_to(WORKSPACE_ROOT)}")
    print(f"[SERIALIZATION] Query JSONL: {out_jsonl_path.relative_to(WORKSPACE_ROOT)}")
    return final_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RQ2 Document Chunking Benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of papers to evaluate")
    parser.add_argument("--dry-run", action="store_true", help="Perform sanity check and print configuration without full run")
    parser.add_argument("--tau-primary", type=float, default=0.50, help="Primary evidence containment threshold (default: 0.50)")
    parser.add_argument("--tau-secondary", type=float, default=0.30, help="Secondary sensitivity threshold (default: 0.30)")
    parser.add_argument("--context-budget", type=int, default=1600, help="Equal token budget for prompt context (default: 1600)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for bootstrap resampling")
    args = parser.parse_args()

    run_rq2_chunking_benchmark(
        limit=args.limit,
        dry_run=args.dry_run,
        tau_primary=args.tau_primary,
        tau_secondary=args.tau_secondary,
        context_budget_tokens=args.context_budget,
        seed=args.seed,
    )
