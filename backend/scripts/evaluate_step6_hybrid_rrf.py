"""
Step 6: Multi-Stage & Hybrid Retrieval Benchmark (Dense + BM25 RRF).
Pre-registered evaluation of Reciprocal Rank Fusion (RRF) on the 48 Held-Out Papers (114 Queries)
under strict calibrated containment (tau* = 0.55) and paired paper-level cluster bootstrap (B=2,000).

Hypothesis (RESEARCH_PLAN_IMPLEMENTATION_AUDIT.md line 370):
  Hybrid RRF (k_rrf = 60) achieves higher Recall@20 and nDCG@4 than either dense (intfloat/e5-small-v2)
  or lexical (WordPiece BM25) retrieval alone by capturing both semantic paraphrases and exact symbolic matches.

Ablations Tested:
  1. Dense Only: intfloat/e5-small-v2 (cosine similarity)
  2. BM25 Only: WordPiece BM25 (k1=1.5, b=0.75, canonical 39 stopwords)
  3. Hybrid RRF (k=20): Reciprocal Rank Fusion with k_rrf=20
  4. Hybrid RRF (k=60): Reciprocal Rank Fusion with k_rrf=60 (production default)
  5. Hybrid Convex (alpha=0.7): Score-normalized linear convex combination (0.7 * Dense + 0.3 * BM25)

Output Artifact:
  - eval/prepared/step6_hybrid_rrf_benchmark.json
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKSPACE_ROOT / "backend" / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from apps.documents.services.chunking_utils import chunk_sections
from eval_common import (
    STOPWORDS,
    clean_evidence,
    compute_dcg,
    compute_ndcg,
    count_relevant_chunks,
    is_chunk_hit,
    paired_cluster_bootstrap,
    tokenize_regex,
)
from transformers import AutoTokenizer

SPLIT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
CORPUS_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
QA_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"
DOC_EMBS_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "step4_e5_doc_embs.npy"
QUERY_EMBS_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "step4_e5_query_embs.npy"
OUTPUT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "step6_hybrid_rrf_benchmark.json"

TOP_K = 20


class WordPieceBM25:
    """Fast WordPiece BM25 with canonical stopword filtering."""

    def __init__(self, corpus_chunks: List[Dict[str, Any]], tokenizer):
        self.chunks = corpus_chunks
        self.tokenizer = tokenizer
        self.doc_tokens = []
        for c in corpus_chunks:
            tokens = [t.lower() for t in tokenizer.tokenize(c["text"]) if t.lower() not in STOPWORDS]
            self.doc_tokens.append(tokens)

        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avg_dl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.df: Dict[str, int] = {}
        self.postings: Dict[str, List[Tuple[int, int]]] = {}

        for doc_id, tokens in enumerate(self.doc_tokens):
            counts: Dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            for t, cnt in counts.items():
                self.df[t] = self.df.get(t, 0) + 1
                self.postings.setdefault(t, []).append((doc_id, cnt))

    def score_candidates(self, query: str, cand_indices: List[int], k1: float = 1.5, b: float = 0.75) -> Dict[int, float]:
        q_tokens = [t.lower() for t in self.tokenizer.tokenize(query) if t.lower() not in STOPWORDS]
        scores = {idx: 0.0 for idx in cand_indices}
        cand_set = set(cand_indices)
        N = len(self.chunks)

        for t in q_tokens:
            if t not in self.df:
                continue
            df_t = self.df[t]
            idf = np.log((N - df_t + 0.5) / (df_t + 0.5) + 1.0)
            for doc_id, tf in self.postings.get(t, []):
                if doc_id in cand_set:
                    denom = tf + k1 * (1.0 - b + b * (self.doc_len[doc_id] / self.avg_dl))
                    scores[doc_id] += idf * (tf * (k1 + 1.0)) / max(denom, 1e-6)

        return scores


def rrf_fuse(
    dense_ranked: List[int],
    bm25_ranked: List[int],
    k_rrf: int = 60,
    top_k: int = TOP_K,
) -> List[int]:
    """Reciprocal Rank Fusion across two ranked candidate lists."""
    scores: Dict[int, float] = {}

    for rank, doc_id in enumerate(dense_ranked):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k_rrf + rank + 1)

    for rank, doc_id in enumerate(bm25_ranked):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k_rrf + rank + 1)

    sorted_docs = sorted(scores.keys(), key=lambda d: scores[d], reverse=True)
    return sorted_docs[:top_k]


def convex_fuse(
    dense_scores: Dict[int, float],
    bm25_scores: Dict[int, float],
    alpha: float = 0.7,
    top_k: int = TOP_K,
) -> List[int]:
    """Score-normalized linear convex combination: alpha * dense_norm + (1 - alpha) * bm25_norm."""
    cand_ids = list(dense_scores.keys())
    d_vals = np.array([dense_scores[i] for i in cand_ids])
    b_vals = np.array([bm25_scores.get(i, 0.0) for i in cand_ids])

    # Min-max normalization
    d_min, d_max = d_vals.min(), d_vals.max()
    d_norm = (d_vals - d_min) / max(d_max - d_min, 1e-6) if d_max > d_min else d_vals

    b_min, b_max = b_vals.min(), b_vals.max()
    b_norm = (b_vals - b_min) / max(b_max - b_min, 1e-6) if b_max > b_min else b_vals

    combined = alpha * d_norm + (1.0 - alpha) * b_norm
    ranked_indices = np.argsort(combined)[::-1][:top_k]
    return [cand_ids[i] for i in ranked_indices]


def evaluate_retrieval_strategy(
    strategy_fn,
    held_out_queries: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    rq_map: Dict[str, int],
    scope: str = "within_paper",
) -> Dict[str, Any]:
    """Evaluates a retrieval strategy function returning ranking metrics."""
    ndcg4_list, ndcg10_list, mrr5_list = [], [], []
    hit1_list, hit3_list, hit5_list = [], [], []
    rec4_list, rec20_list = [], []
    scores_by_paper: Dict[str, List[float]] = {}

    for q in held_out_queries:
        qid = str(q.get("id") or q.get("question_id") or "")
        aid = q["paper_arxiv_id"]
        total_relevant = rq_map.get(qid, 0)
        if total_relevant == 0:
            continue

        ranked_cand_indices = strategy_fn(q, scope=scope)

        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])

        # Relevance judgments
        rel_scores = []
        for c_idx in ranked_cand_indices:
            c = chunks[c_idx]
            rel = 1 if is_chunk_hit(c, aid, quote, ev_list, tau=0.55) else 0
            rel_scores.append(rel)

        rel_scores = rel_scores[:TOP_K]
        while len(rel_scores) < TOP_K:
            rel_scores.append(0)

        # NDCG
        n4 = compute_ndcg(rel_scores[:4], total_relevant, k=4)
        n10 = compute_ndcg(rel_scores[:10], total_relevant, k=10)
        ndcg4_list.append(n4)
        ndcg10_list.append(n10)
        scores_by_paper.setdefault(aid, []).append(n4)

        # MRR@5
        mrr = 0.0
        for r_i, r_val in enumerate(rel_scores[:5]):
            if r_val > 0:
                mrr = 1.0 / (r_i + 1)
                break
        mrr5_list.append(mrr)

        # Hits
        hit1_list.append(1.0 if any(rel_scores[:1]) else 0.0)
        hit3_list.append(1.0 if any(rel_scores[:3]) else 0.0)
        hit5_list.append(1.0 if any(rel_scores[:5]) else 0.0)

        # Recalls
        rec4 = sum(rel_scores[:4]) / total_relevant
        rec20 = sum(rel_scores[:20]) / total_relevant
        rec4_list.append(rec4)
        rec20_list.append(rec20)

    return {
        "ndcg4": float(np.mean(ndcg4_list)),
        "ndcg10": float(np.mean(ndcg10_list)),
        "mrr5": float(np.mean(mrr5_list)),
        "hit1": float(np.mean(hit1_list)) * 100.0,
        "hit3": float(np.mean(hit3_list)) * 100.0,
        "hit5": float(np.mean(hit5_list)) * 100.0,
        "recall4": float(np.mean(rec4_list)),
        "recall20": float(np.mean(rec20_list)),
        "scores_by_paper": scores_by_paper,
        "n_queries": len(ndcg4_list),
    }


def main():
    print("=" * 100)
    print("STEP 6: MULTI-STAGE & HYBRID RETRIEVAL BENCHMARK (DENSE + BM25 RRF)")
    print("Pre-registered on 48 Held-Out Papers (114 Queries) | Strict Containment tau*=0.55")
    print("=" * 100)

    # 1. Load data
    with open(SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    held_out_papers = set(split_data.get("held_out_papers", []))

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    with open(QA_PATH, "r", encoding="utf-8") as f:
        all_qa = json.load(f)

    held_out_queries = [
        q for q in all_qa
        if q.get("paper_arxiv_id") in held_out_papers and q.get("question_type") != "unanswerable"
    ]

    print(f"Loaded {len(held_out_papers)} held-out papers and {len(held_out_queries)} answerable queries.")

    # 2. Build chunks
    chunks: List[Dict[str, Any]] = []
    paper_chunks_map: Dict[str, List[int]] = {}
    for aid in held_out_papers:
        paper_data = corpus.get(aid, {})
        c_list = chunk_sections(paper_data.get("sections", []), strategy="section_overlap", max_tokens=350, overlap=70)
        start_idx = len(chunks)
        for c in c_list:
            c["paper_arxiv_id"] = aid
            chunks.append(c)
        paper_chunks_map[aid] = list(range(start_idx, len(chunks)))

    print(f"Corpus chunks: {len(chunks)} total across 48 papers.")

    # 3. Load or compute E5 embeddings
    tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-small-v2")
    bm25 = WordPieceBM25(chunks, tokenizer)

    if DOC_EMBS_PATH.exists() and QUERY_EMBS_PATH.exists():
        print(f"Loading cached E5 embeddings from: {DOC_EMBS_PATH.name} and {QUERY_EMBS_PATH.name}")
        doc_embs = np.load(DOC_EMBS_PATH)
        query_embs = np.load(QUERY_EMBS_PATH)
    else:
        print("Computing E5 embeddings...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("intfloat/e5-small-v2")
        doc_texts = ["passage: " + c["text"] for c in chunks]
        doc_embs = model.encode(doc_texts, batch_size=64, normalize_embeddings=True)
        q_texts = ["query: " + q["question"] for q in held_out_queries]
        query_embs = model.encode(q_texts, batch_size=64, normalize_embeddings=True)
        np.save(DOC_EMBS_PATH, doc_embs)
        np.save(QUERY_EMBS_PATH, query_embs)

    # Pre-compute R_q
    rq_map = {}
    for q in held_out_queries:
        qid = q.get("id") or q.get("question_id")
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        paper_chunks = [chunks[i] for i in paper_chunks_map.get(aid, [])]
        rq_map[qid] = count_relevant_chunks(paper_chunks, aid, quote, ev_list, tau=0.55)

    q_idx_map = {(q.get("id") or q.get("question_id")): i for i, q in enumerate(held_out_queries)}

    # Pre-compute dense and BM25 candidate ranks for each query
    dense_rankings_wp = {}
    dense_scores_wp = {}
    bm25_rankings_wp = {}
    bm25_scores_wp = {}

    dense_rankings_xp = {}
    dense_scores_xp = {}
    bm25_rankings_xp = {}
    bm25_scores_xp = {}

    all_chunk_indices = list(range(len(chunks)))

    print("\nPre-computing Dense and BM25 retrieval for all 114 queries...")
    for q in held_out_queries:
        qid = q.get("id") or q.get("question_id")
        aid = q["paper_arxiv_id"]
        q_idx = q_idx_map[qid]
        q_vec = query_embs[q_idx]

        # Within-paper candidate pool
        wp_cands = paper_chunks_map[aid]

        # Dense WP
        wp_vecs = doc_embs[wp_cands]
        wp_sims = np.dot(wp_vecs, q_vec)
        wp_dense_sorted = [wp_cands[i] for i in np.argsort(wp_sims)[::-1]]
        dense_rankings_wp[qid] = wp_dense_sorted
        dense_scores_wp[qid] = {wp_cands[i]: float(wp_sims[i]) for i in range(len(wp_cands))}

        # BM25 WP
        wp_bm25_scores = bm25.score_candidates(q["question"], wp_cands)
        wp_bm25_sorted = sorted(wp_cands, key=lambda i: wp_bm25_scores.get(i, 0.0), reverse=True)
        bm25_rankings_wp[qid] = wp_bm25_sorted
        bm25_scores_wp[qid] = wp_bm25_scores

        # Cross-paper candidate pool
        all_sims = np.dot(doc_embs, q_vec)
        top_xp_dense = [int(i) for i in np.argsort(all_sims)[::-1][:100]]
        dense_rankings_xp[qid] = top_xp_dense
        dense_scores_xp[qid] = {i: float(all_sims[i]) for i in top_xp_dense}

        xp_bm25_scores = bm25.score_candidates(q["question"], all_chunk_indices)
        top_xp_bm25 = sorted(all_chunk_indices, key=lambda i: xp_bm25_scores.get(i, 0.0), reverse=True)[:100]
        bm25_rankings_xp[qid] = top_xp_bm25
        bm25_scores_xp[qid] = xp_bm25_scores

    # Define retrieval arms
    def _qid(q):
        return q.get("id") or q.get("question_id")

    arms = {
        "Dense Only (e5-small-v2)": lambda q, scope: (
            dense_rankings_wp[_qid(q)][:TOP_K] if scope == "within_paper" else dense_rankings_xp[_qid(q)][:TOP_K]
        ),
        "BM25 Only (WordPiece)": lambda q, scope: (
            bm25_rankings_wp[_qid(q)][:TOP_K] if scope == "within_paper" else bm25_rankings_xp[_qid(q)][:TOP_K]
        ),
        "Hybrid RRF (k=20)": lambda q, scope: (
            rrf_fuse(dense_rankings_wp[_qid(q)], bm25_rankings_wp[_qid(q)], k_rrf=20, top_k=TOP_K)
            if scope == "within_paper"
            else rrf_fuse(dense_rankings_xp[_qid(q)], bm25_rankings_xp[_qid(q)], k_rrf=20, top_k=TOP_K)
        ),
        "Hybrid RRF (k=60) [Prod]": lambda q, scope: (
            rrf_fuse(dense_rankings_wp[_qid(q)], bm25_rankings_wp[_qid(q)], k_rrf=60, top_k=TOP_K)
            if scope == "within_paper"
            else rrf_fuse(dense_rankings_xp[_qid(q)], bm25_rankings_xp[_qid(q)], k_rrf=60, top_k=TOP_K)
        ),
        "Hybrid Convex (alpha=0.7)": lambda q, scope: (
            convex_fuse(dense_scores_wp[_qid(q)], bm25_scores_wp[_qid(q)], alpha=0.7, top_k=TOP_K)
            if scope == "within_paper"
            else convex_fuse(dense_scores_xp[_qid(q)], bm25_scores_xp[_qid(q)], alpha=0.7, top_k=TOP_K)
        ),
    }

    # Evaluate all arms
    results_wp: Dict[str, Any] = {}
    results_xp: Dict[str, Any] = {}

    print("\nRunning evaluations across all 5 arms...")
    for arm_name, fn in arms.items():
        res_w = evaluate_retrieval_strategy(fn, held_out_queries, chunks, rq_map, scope="within_paper")
        results_wp[arm_name] = res_w
        res_x = evaluate_retrieval_strategy(fn, held_out_queries, chunks, rq_map, scope="cross_paper")
        results_xp[arm_name] = res_x

    # Compute paired cluster bootstraps (B=2,000) against Dense Only
    base_wp = results_wp["Dense Only (e5-small-v2)"]["scores_by_paper"]
    base_xp = results_xp["Dense Only (e5-small-v2)"]["scores_by_paper"]

    bootstraps_wp = {}
    for arm_name, r in results_wp.items():
        if arm_name == "Dense Only (e5-small-v2)":
            continue
        diff, ci, p_val = paired_cluster_bootstrap(base_wp, r["scores_by_paper"], n_bootstraps=2000, seed=42)
        bootstraps_wp[arm_name] = {"diff": diff, "ci": ci, "p_val": p_val}

    # Print summary tables
    header = (
        f"{'Strategy / Arm':<32} {'nDCG@4':>8} {'nDCG@10':>9} {'MRR@5':>8} "
        f"{'Hit@1':>7} {'Hit@3':>7} {'Hit@5':>7} {'Rec@4':>7} {'Rec@20':>8} "
        f"{'Delta nDCG@4 [95% CI]':>30} {'p-val':>8}"
    )

    print("\n" + "=" * 130)
    print("TABLE 1: WITHIN-PAPER RETRIEVAL (PRIMARY EVALUATION SCOPE)")
    print("=" * 130)
    print(header)
    print("-" * 130)

    for arm_name, r in results_wp.items():
        d_str = "Reference (Base)" if arm_name == "Dense Only (e5-small-v2)" else (
            f"{bootstraps_wp[arm_name]['diff']:+.4f} [{bootstraps_wp[arm_name]['ci'][0]:+.4f},{bootstraps_wp[arm_name]['ci'][1]:+.4f}]"
        )
        p_str = "-" if arm_name == "Dense Only (e5-small-v2)" else f"{bootstraps_wp[arm_name]['p_val']:.4f}"
        print(
            f"{arm_name:<32} {r['ndcg4']:>8.4f} {r['ndcg10']:>9.4f} {r['mrr5']:>8.4f} "
            f"{r['hit1']:>6.1f}% {r['hit3']:>6.1f}% {r['hit5']:>6.1f}% {r['recall4']:>7.3f} {r['recall20']:>8.3f} "
            f"{d_str:>30} {p_str:>8}"
        )

    print("\n" + "=" * 130)
    print("TABLE 2: CROSS-PAPER RETRIEVAL (GLOBAL SEARCH SCOPE)")
    print("=" * 130)
    print(header)
    print("-" * 130)

    for arm_name, r in results_xp.items():
        print(
            f"{arm_name:<32} {r['ndcg4']:>8.4f} {r['ndcg10']:>9.4f} {r['mrr5']:>8.4f} "
            f"{r['hit1']:>6.1f}% {r['hit3']:>6.1f}% {r['hit5']:>6.1f}% {r['recall4']:>7.3f} {r['recall20']:>8.3f} "
            f"{'—':>30} {'—':>8}"
        )

    # Save JSON artifact
    clean_wp = {k: {m: v for m, v in val.items() if m != "scores_by_paper"} for k, val in results_wp.items()}
    clean_xp = {k: {m: v for m, v in val.items() if m != "scores_by_paper"} for k, val in results_xp.items()}

    out_payload = {
        "benchmark": "Step 6 Multi-Stage & Hybrid Retrieval Benchmark (Dense + BM25 RRF)",
        "dataset": "QASPER Held-Out (48 Papers, 114 Queries)",
        "containment_tau": 0.55,
        "n_bootstraps": 2000,
        "within_paper_results": clean_wp,
        "cross_paper_results": clean_xp,
        "paired_bootstrap_vs_dense": {
            k: {
                "delta_ndcg4": v["diff"],
                "ci_lower": v["ci"][0],
                "ci_upper": v["ci"][1],
                "p_value": v["p_val"],
                "is_significant_0_05": v["p_val"] <= 0.05,
            }
            for k, v in bootstraps_wp.items()
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)

    print(f"\n[SUCCESS] Serialized Step 6 Benchmark to: {OUTPUT_PATH.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()
