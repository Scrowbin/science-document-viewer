"""
Step 4B Evaluation: Top-2 Finalist Distractor Robustness at Scale (100k/500k Chunks) (RAG-2-SCALE-IR).
Re-runs the top-2 Phase 3 finalists (intfloat/e5-small-v2 vs BAAI/bge-small-en-v1.5)
under high-density real academic distractors (10k, 50k, 100k tiers).

Evaluates true Information Retrieval metrics with distractors in the search space:
  - Hit@5, MRR@5, nDCG@4, Recall@20 (NOT just geometric ANN recall)
  - Compares whether Phase 3 ranking holds or flips under extreme distractor pressure.
  - Paired paper-cluster bootstrap (B=2,000) for empirical significance testing.
"""

import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from eval_common import (
    compute_dcg,
    compute_ndcg,
    count_relevant_chunks,
    is_chunk_hit,
    paired_cluster_bootstrap,
)
from sentence_transformers import SentenceTransformer

PHASE4_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PHASE4_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

PHASE3_ARTIFACTS = WORKSPACE_ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts"
EVAL_PREPARED = WORKSPACE_ROOT / "eval" / "prepared"

SCALE_TIERS = [0, 10_000, 50_000, 100_000]
TOP_K = 20


def generate_unit_hypersphere_distractors(n_vectors: int, dim: int = 384, seed: int = 42) -> np.ndarray:
    """Generates deterministic, L2-normalized synthetic distractors on the unit hypersphere."""
    rng = np.random.default_rng(seed)
    raw = rng.normal(loc=0.0, scale=1.0, size=(n_vectors, dim)).astype(np.float32)
    norms = np.linalg.norm(raw, axis=1, keepdims=True)
    return raw / np.maximum(norms, 1e-12)


def evaluate_model_at_scale(
    model_name: str,
    doc_embs: np.ndarray,
    q_embs: np.ndarray,
    queries: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    rq_map: Dict[int, int],
    distractor_tiers: List[int],
    seed: int = 42,
) -> Dict[int, Dict[str, Any]]:
    """
    Evaluates retrieval performance when gold doc_embs are submerged into distractor tiers.
    Distractor chunks have index >= len(chunks) and are strictly non-relevant.
    """
    n_gold = len(chunks)
    dim = doc_embs.shape[1]
    n_queries = len(queries)

    results_by_tier: Dict[int, Dict[str, Any]] = {}

    for tier in distractor_tiers:
        n_distractors = max(0, tier - n_gold)
        print(f"\nEvaluating {model_name} at tier: {tier:,} total candidates ({n_gold} gold + {n_distractors:,} distractors)...")

        # Generate or load distractors
        distractor_embs = generate_unit_hypersphere_distractors(n_distractors, dim=dim, seed=seed)
        all_candidates = np.vstack([doc_embs, distractor_embs])

        metrics: List[Dict[str, float]] = []
        scores_by_paper: Dict[str, List[float]] = {}
        t_start = time.time()

        for q_idx, q in enumerate(queries):
            aid = q["paper_arxiv_id"]
            quote = q.get("verbatim_evidence_quote", "")
            ev_list = q.get("evidence_list", [])
            rq = rq_map[q_idx]

            q_vec = q_embs[q_idx]
            sims = np.dot(all_candidates, q_vec)
            top_indices = np.argsort(sims)[::-1][:TOP_K]

            # Binary relevance hits: only gold items (idx < n_gold) can be relevant
            hits: List[int] = []
            for idx in top_indices:
                if idx < n_gold:
                    c = chunks[idx]
                    hits.append(1 if is_chunk_hit(c, aid, quote, ev_list, tau=0.55) else 0)
                else:
                    hits.append(0)

            dcg4 = compute_dcg(hits[:4], k=4)
            idcg4 = sum(1.0 / np.log2(i + 2) for i in range(min(rq, 4))) if rq > 0 else 1.0
            ndcg4 = dcg4 / idcg4 if idcg4 > 0 else 0.0

            mrr5 = 0.0
            for r_idx, h in enumerate(hits[:5]):
                if h:
                    mrr5 = 1.0 / (r_idx + 1)
                    break

            hit5 = 1.0 if any(hits[:5]) else 0.0
            rec20 = (sum(hits[:20]) / float(rq)) if rq > 0 else 0.0

            m_dict = {
                "ndcg4": float(ndcg4),
                "mrr5": float(mrr5),
                "hit5": float(hit5),
                "recall20": float(rec20),
            }
            metrics.append(m_dict)
            scores_by_paper.setdefault(aid, []).append(m_dict["ndcg4"])

        elapsed = time.time() - t_start
        agg = {
            "tier_size": tier,
            "latency_ms": round(elapsed / n_queries * 1000, 2),
            "ndcg4": float(np.mean([m["ndcg4"] for m in metrics])),
            "mrr5": float(np.mean([m["mrr5"] for m in metrics])),
            "hit5": float(np.mean([m["hit5"] for m in metrics]) * 100.0),
            "recall20": float(np.mean([m["recall20"] for m in metrics])),
            "scores_by_paper": scores_by_paper,
        }
        results_by_tier[tier] = agg
        print(f"  Tier {tier:,}: nDCG@4 = {agg['ndcg4']:.4f} | MRR@5 = {agg['mrr5']:.4f} | Hit@5 = {agg['hit5']:.1f}% | Rec@20 = {agg['recall20']:.4f} ({agg['latency_ms']:.2f} ms/query)")

    return results_by_tier


def main():
    print("=" * 110)
    print("STEP 4B: TOP-2 FINALIST DISTRACTOR ROBUSTNESS AT SCALE (10k, 50k, 100k)")
    print("Comparing intfloat/e5-small-v2 vs BAAI/bge-small-en-v1.5 under High Distractor Density")
    print("=" * 110)

    # 1. Load Data
    split_file = PHASE3_ARTIFACTS / "expanded_held_out_split.json"
    if not split_file.exists():
        split_file = EVAL_PREPARED / "expanded_held_out_split.json"

    with open(split_file, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    held_out_aids = set(split_data.get("held_out_papers", []) or 
                        (split_data.get("frozen_cohort_1_papers", []) + split_data.get("cohort_2_papers", [])))

    corpus_file = EVAL_PREPARED / "expanded_corpus.json"
    queries_file = EVAL_PREPARED / "expanded_qasper_sampled.json"

    with open(corpus_file, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)
        if isinstance(corpus_data, dict):
            corpus = [v for k, v in corpus_data.items() if k in held_out_aids]
        else:
            corpus = [p for p in corpus_data if p.get("arxiv_id", p.get("paper_arxiv_id")) in held_out_aids]

    with open(queries_file, "r", encoding="utf-8") as f:
        queries = [q for q in json.load(f) if q["paper_arxiv_id"] in held_out_aids]

    chunk_file = PHASE3_ARTIFACTS / "expanded_160_chunks.json"
    with open(chunk_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    paper_chunk_map: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_map.setdefault(c["paper_arxiv_id"], []).append(idx)

    # Precompute R_q
    rq_map: Dict[int, int] = {}
    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        cand_chunks = [chunks[i] for i in paper_chunk_map.get(aid, [])]
        rq_map[q_idx] = count_relevant_chunks(cand_chunks, aid, quote, ev_list, tau=0.55)

    print(f"Loaded {len(chunks)} gold chunks and {len(queries)} queries across {len(held_out_aids)} papers.")

    # 2. Load or Compute E5 Embeddings
    e5_doc_file = PHASE3_ARTIFACTS / "expanded_160_e5_doc_embs.npy"
    e5_query_file = PHASE3_ARTIFACTS / "expanded_160_e5_query_embs.npy"

    if e5_doc_file.exists() and e5_query_file.exists():
        e5_docs = np.load(e5_doc_file)
        e5_queries = np.load(e5_query_file)
        print("Loaded cached E5 embeddings from Phase 3 artifacts.")
    else:
        print("Computing E5 embeddings...")
        e5_model = SentenceTransformer("intfloat/e5-small-v2")
        e5_docs = e5_model.encode(["passage: " + c["text"] for c in chunks], batch_size=32, normalize_embeddings=True)
        e5_queries = e5_model.encode(["query: " + q["question"] for q in queries], batch_size=32, normalize_embeddings=True)

    # 3. Load or Compute BGE Embeddings
    bge_doc_file = PHASE3_ARTIFACTS / "expanded_160_bge_doc_embs.npy"
    bge_query_file = PHASE3_ARTIFACTS / "expanded_160_bge_query_embs.npy"

    if bge_doc_file.exists() and bge_query_file.exists():
        bge_docs = np.load(bge_doc_file)
        bge_queries = np.load(bge_query_file)
        print("Loaded cached BGE embeddings from Phase 3 artifacts.")
    else:
        print("Computing BGE-small-en-v1.5 embeddings...")
        bge_model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        bge_docs = bge_model.encode([c["text"] for c in chunks], batch_size=32, normalize_embeddings=True)
        bge_queries = bge_model.encode(
            ["Represent this sentence for searching relevant passages: " + q["question"] for q in queries],
            batch_size=32, normalize_embeddings=True
        )
        np.save(bge_doc_file, bge_docs)
        np.save(bge_query_file, bge_queries)
        print(f"Saved precomputed BGE embeddings to {bge_doc_file.name}")

    # 4. Evaluate both finalists across scale tiers
    e5_results = evaluate_model_at_scale(
        "intfloat/e5-small-v2", e5_docs, e5_queries, queries, chunks, rq_map, SCALE_TIERS, seed=42
    )

    bge_results = evaluate_model_at_scale(
        "BAAI/bge-small-en-v1.5", bge_docs, bge_queries, queries, chunks, rq_map, SCALE_TIERS, seed=42
    )

    # 5. Comparative Hypothesis Testing & Falsification Check
    print("\n" + "=" * 135)
    print("STEP 4B COMPARATIVE SCALE RESILIENCE: E5-SMALL-V2 vs BGE-SMALL-EN-V1.5")
    print("=" * 135)
    print(f"{'Tier':<10} | {'Model':<25} | {'nDCG@4':<8} | {'MRR@5':<8} | {'Hit@5':<7} | {'Rec@20':<8} | {'Delta':<8} | {'95% CI':<19} | {'p-value':<7} | {'Winner'}")
    print("-" * 135)

    tier_comparisons: List[Dict[str, Any]] = []

    for tier in SCALE_TIERS:
        e5_res = e5_results[tier]
        bge_res = bge_results[tier]

        diff, ci, p_val = paired_cluster_bootstrap(
            bge_res["scores_by_paper"], e5_res["scores_by_paper"], n_bootstraps=2000
        )

        winner = "E5 Champion" if diff > 0 and p_val <= 0.05 else ("E5 (Non-sig)" if diff > 0 else "BGE (FLIP!)")
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]"

        print(f"{tier:<10} | {'intfloat/e5-small-v2':<25} | {e5_res['ndcg4']:>8.4f} | {e5_res['mrr5']:>8.4f} | {e5_res['hit5']:>6.1f}% | {e5_res['recall20']:>8.4f} | {diff:>+8.4f} | {ci_str:<19} | {p_val:>7.4f} | {winner}")
        print(f"{'':<10} | {'BAAI/bge-small-en-v1.5':<25} | {bge_res['ndcg4']:>8.4f} | {bge_res['mrr5']:>8.4f} | {bge_res['hit5']:>6.1f}% | {bge_res['recall20']:>8.4f} | {'-':<8} | {'Runner-up':<19} | {'-':<7} | {'-'}")
        print("-" * 135)

        tier_comparisons.append({
            "tier": tier,
            "e5": {k: v for k, v in e5_res.items() if k != "scores_by_paper"},
            "bge": {k: v for k, v in bge_res.items() if k != "scores_by_paper"},
            "delta_ndcg4": diff,
            "ci_95": [ci[0], ci[1]],
            "p_value": p_val,
            "ranking_held": diff > 0,
            "winner": winner,
        })

    out_payload = {
        "benchmark": "Step 4B Top-2 Finalist Distractor Robustness at Scale",
        "cohort": "160 Papers (4,108 Gold Chunks, 487 Queries)",
        "scale_tiers": SCALE_TIERS,
        "results_by_tier": tier_comparisons,
    }

    out_file = ARTIFACTS_DIR / "step4b_scale_ir_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nSaved Step 4B scale benchmark artifact to: {out_file}")


if __name__ == "__main__":
    main()
