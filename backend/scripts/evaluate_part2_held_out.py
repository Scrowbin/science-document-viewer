"""
Definitive Unblinded Held-Out Benchmark Run (48 Papers, 114 Queries)
Pre-registered evaluation of sentence-level dense embedding models and lexical baselines
under calibrated strict containment (tau* = 0.55), paper-level cluster bootstrap (B=2,000),
and Holm-Bonferroni family-wise error rate control.

Audit Remediation (2026-10-15):
  Fix 1: Global IDCG based on R_q (total relevant chunks per query).
  Fix 2: Canonical 39-stopword set via eval_common.
  Fix 3: Strict evidence containment; FLOAT evidence stripping.
  Fix 4: Standardized latency (retrieval-only, excludes evaluation overhead).
  Fix 5: Corrected MC p-value; both as-is + minimal-intervention chunk arms;
         top_k=20 with secondary metrics (Recall@4, Recall@20, MRR@5, nDCG@10).
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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
from sentence_transformers import SentenceTransformer

TOP_K = 20  # Retrieve top-20 for secondary metrics


# ─── BM25 Implementation ────────────────────────────────────────────────────
class SimpleBM25:
    def __init__(self, corpus_chunks: List[Dict[str, Any]], tokenizer_fn):
        self.chunks = corpus_chunks
        self.tokenizer_fn = tokenizer_fn
        self.doc_len = [len(tokenizer_fn(c["text"])) for c in corpus_chunks]
        self.avg_dl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.df: Dict[str, int] = {}
        self.postings: Dict[str, List[Tuple[int, int]]] = {}

        for doc_id, c in enumerate(corpus_chunks):
            tokens = tokenizer_fn(c["text"])
            counts: Dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            for t, cnt in counts.items():
                self.df[t] = self.df.get(t, 0) + 1
                self.postings.setdefault(t, []).append((doc_id, cnt))

    def retrieve(self, query: str, cand_indices: Optional[List[int]] = None,
                 top_k: int = TOP_K, k1: float = 1.5, b: float = 0.75) -> List[int]:
        """Returns list of chunk indices ranked by BM25 score."""
        q_tokens = self.tokenizer_fn(query)
        scores = {}
        valid_set = set(cand_indices) if cand_indices is not None else None
        N = len(self.chunks)

        for t in q_tokens:
            if t not in self.df:
                continue
            df_t = self.df[t]
            idf = np.log((N - df_t + 0.5) / (df_t + 0.5) + 1.0)
            for doc_id, tf in self.postings[t]:
                if valid_set is not None and doc_id not in valid_set:
                    continue
                dl = self.doc_len[doc_id]
                denom = tf + k1 * (1.0 - b + b * (dl / self.avg_dl))
                num = tf * (k1 + 1.0)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (num / denom)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [doc_id for doc_id, _ in ranked]


# ─── Data Loading ────────────────────────────────────────────────────────────
def load_held_out_data():
    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    held_out_aids = set(split_data["held_out_papers"])

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)
    held_out_corpus = {k: v for k, v in corpus_all.items() if k in held_out_aids}

    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)
    held_out_queries = [
        q for q in qa_all
        if q.get("paper_arxiv_id") in held_out_aids and q.get("question_type") != "unanswerable"
    ]
    return held_out_aids, held_out_corpus, held_out_queries


def build_chunks(corpus, strategy="section_overlap", max_tokens=350, overlap=70):
    """Build standard as-is chunks from corpus sections."""
    chunks = []
    for aid, doc in corpus.items():
        sec_list = doc.get("sections", [])
        base_chunks = chunk_sections(sec_list, strategy=strategy,
                                     max_tokens=max_tokens, overlap=overlap)
        for c_idx, c in enumerate(base_chunks):
            c["chunk_id"] = f"{aid}_c_{c_idx}"
            c["paper_arxiv_id"] = aid
            chunks.append(c)
    return chunks


def build_chunk_arms(corpus, model_name="sentence-transformers/all-MiniLM-L6-v2",
                     max_subwords=256):
    """Build both as-is and minimal-intervention chunk arms."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(model_name)

    as_is_chunks = []
    min_interv_chunks = []

    for aid, doc in corpus.items():
        sec_list = doc.get("sections", [])
        base_chunks = chunk_sections(sec_list, strategy="section_overlap",
                                     max_tokens=350, overlap=70)

        for c_idx, c in enumerate(base_chunks):
            c_text = c.get("text", "")
            tokens = tok.encode(c_text, add_special_tokens=False)

            as_is_item = {
                "chunk_id": f"{aid}_asis_{c_idx}",
                "paper_arxiv_id": aid,
                "text": c_text,
                "section": c.get("section", ""),
                "subword_len": len(tokens),
                "is_truncated": len(tokens) > max_subwords,
            }
            as_is_chunks.append(as_is_item)

            if len(tokens) <= max_subwords:
                min_interv_chunks.append(as_is_item)
            else:
                # Re-split oversized chunk into 2 overlapping halves
                words = c_text.split()
                mid = len(words) // 2
                part1 = " ".join(words[:mid + 20])
                part2 = " ".join(words[max(0, mid - 20):])
                for part_i, part_text in enumerate([part1, part2], 1):
                    part_toks = tok.encode(part_text, add_special_tokens=False)
                    min_interv_chunks.append({
                        "chunk_id": f"{aid}_resplit_{c_idx}_{part_i}",
                        "paper_arxiv_id": aid,
                        "text": part_text,
                        "section": c.get("section", ""),
                        "subword_len": len(part_toks),
                        "is_truncated": len(part_toks) > max_subwords,
                        "is_resplit": True,
                    })

    return as_is_chunks, min_interv_chunks


# ─── Pre-compute R_q per query ──────────────────────────────────────────────
def precompute_rq(queries, chunks, paper_chunk_map, tau=0.55):
    """
    Pre-compute R_q (total relevant chunks in the paper) for each query.
    Returns dict mapping query index -> R_q.
    """
    rq_map = {}
    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        paper_chunks = [chunks[i] for i in paper_chunk_map.get(aid, [])]
        rq_map[q_idx] = count_relevant_chunks(paper_chunks, aid, quote, ev_list, tau=tau)
    return rq_map


# ─── Evaluation Functions ───────────────────────────────────────────────────
def compute_query_metrics(ranked_chunks, q, rq, tau=0.55):
    """
    Compute all primary and secondary metrics for a single query
    given a ranked list of up to TOP_K retrieved chunks.
    """
    aid = q["paper_arxiv_id"]
    quote = q.get("verbatim_evidence_quote", "")
    ev_list = q.get("evidence_list", [])

    rels = [1 if is_chunk_hit(c, aid, quote, ev_list, tau=tau) else 0 for c in ranked_chunks[:TOP_K]]

    # Primary: nDCG@4
    ndcg4 = compute_ndcg(rels, total_relevant=rq, k=4)
    # Secondary: nDCG@10
    ndcg10 = compute_ndcg(rels, total_relevant=rq, k=10)

    # MRR@5 (first relevant in top-5)
    found_rank = None
    for i, r in enumerate(rels[:5]):
        if r == 1:
            found_rank = i + 1
            break
    mrr5 = 1.0 / found_rank if found_rank else 0.0

    # Hit@k
    hit1 = 1 if found_rank == 1 else 0
    hit3 = 1 if found_rank and found_rank <= 3 else 0
    hit5 = 1 if found_rank and found_rank <= 5 else 0

    # Recall@4: fraction of R_q found in top-4
    recall4 = sum(rels[:4]) / rq if rq > 0 else 0.0
    # Recall@20: fraction of R_q found in top-20
    recall20 = sum(rels[:20]) / rq if rq > 0 else 0.0

    return {
        "ndcg4": ndcg4, "ndcg10": ndcg10, "mrr5": mrr5,
        "hit1": hit1, "hit3": hit3, "hit5": hit5,
        "recall4": recall4, "recall20": recall20, "rq": rq,
    }


def evaluate_bm25(chunks, queries, rq_map, tokenizer_fn, name, tau=0.55):
    bm25 = SimpleBM25(chunks, tokenizer_fn)
    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    wp_metrics = []
    xp_metrics = []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    xp_scores_by_paper: Dict[str, List[float]] = {}

    # Fix 4: measure retrieval-only latency
    wp_lat, xp_lat = 0.0, 0.0

    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        q_text = q["question"]
        rq = rq_map[q_idx]

        # Within-paper retrieval (timed)
        cand_idx = paper_chunk_indices.get(aid, [])
        t0 = time.time()
        ranked_wp_idx = bm25.retrieve(q_text, cand_indices=cand_idx, top_k=TOP_K)
        wp_lat += time.time() - t0
        ranked_wp = [chunks[i] for i in ranked_wp_idx]
        m_wp = compute_query_metrics(ranked_wp, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

        # Cross-paper retrieval (timed)
        t0 = time.time()
        ranked_xp_idx = bm25.retrieve(q_text, cand_indices=None, top_k=TOP_K)
        xp_lat += time.time() - t0
        ranked_xp = [chunks[i] for i in ranked_xp_idx]
        m_xp = compute_query_metrics(ranked_xp, q, rq, tau=tau)
        xp_metrics.append(m_xp)
        xp_scores_by_paper.setdefault(aid, []).append(m_xp["ndcg4"])

    n = len(queries)
    return {
        "model_name": name,
        "wp_latency_ms": round(wp_lat / n * 1000, 2),
        "xp_latency_ms": round(xp_lat / n * 1000, 2),
        "within_paper": _aggregate_metrics(wp_metrics, wp_scores_by_paper),
        "cross_paper": _aggregate_metrics(xp_metrics, xp_scores_by_paper),
    }


def evaluate_dense_model(model_name, chunks, queries, rq_map,
                         query_prefix="", passage_prefix="", tau=0.55):
    print(f"\n[HELD-OUT EVAL] Loading: {model_name}...")
    model = SentenceTransformer(model_name)

    print(f"  Encoding {len(chunks)} chunks (passage prefix: '{passage_prefix}')...")
    doc_texts = [passage_prefix + c["text"] for c in chunks]
    doc_embs = model.encode(doc_texts, batch_size=16, show_progress_bar=False,
                            normalize_embeddings=True)

    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    print(f"  Encoding {len(queries)} queries (query prefix: '{query_prefix}')...")
    q_texts = [query_prefix + q["question"] for q in queries]
    q_embs = model.encode(q_texts, batch_size=16, show_progress_bar=False,
                          normalize_embeddings=True)

    wp_metrics, xp_metrics = [], []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    xp_scores_by_paper: Dict[str, List[float]] = {}
    wp_lat, xp_lat = 0.0, 0.0

    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        q_emb = q_embs[q_idx]
        rq = rq_map[q_idx]

        # Within-paper retrieval (timed: dot product + sort only)
        cand_idx = paper_chunk_indices.get(aid, [])
        if cand_idx:
            cand_embs = doc_embs[cand_idx]
            t0 = time.time()
            sims = np.dot(cand_embs, q_emb)
            ranked_local = np.argsort(-sims)[:TOP_K]
            wp_lat += time.time() - t0
            ranked_wp = [chunks[cand_idx[i]] for i in ranked_local]
        else:
            ranked_wp = []

        m_wp = compute_query_metrics(ranked_wp, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

        # Cross-paper retrieval (timed)
        t0 = time.time()
        all_sims = np.dot(doc_embs, q_emb)
        ranked_global = np.argsort(-all_sims)[:TOP_K]
        xp_lat += time.time() - t0
        ranked_xp = [chunks[i] for i in ranked_global]

        m_xp = compute_query_metrics(ranked_xp, q, rq, tau=tau)
        xp_metrics.append(m_xp)
        xp_scores_by_paper.setdefault(aid, []).append(m_xp["ndcg4"])

    n = len(queries)
    # Also measure single-query encode latency (batch_size=1)
    t0 = time.time()
    for q_text in q_texts[:10]:
        model.encode([query_prefix + q_text], batch_size=1, show_progress_bar=False,
                     normalize_embeddings=True)
    single_q_lat = (time.time() - t0) / 10 * 1000

    return {
        "model_name": model_name,
        "wp_latency_ms": round(wp_lat / n * 1000, 2),
        "xp_latency_ms": round(xp_lat / n * 1000, 2),
        "single_query_encode_ms": round(single_q_lat, 2),
        "within_paper": _aggregate_metrics(wp_metrics, wp_scores_by_paper),
        "cross_paper": _aggregate_metrics(xp_metrics, xp_scores_by_paper),
    }


def _aggregate_metrics(metrics_list, scores_by_paper):
    """Aggregate per-query metrics into mean values."""
    n = len(metrics_list)
    rq_values = [m["rq"] for m in metrics_list]
    rq_zero = sum(1 for r in rq_values if r == 0)
    return {
        "ndcg4": float(np.mean([m["ndcg4"] for m in metrics_list])),
        "ndcg10": float(np.mean([m["ndcg10"] for m in metrics_list])),
        "mrr5": float(np.mean([m["mrr5"] for m in metrics_list])),
        "hit1": float(np.mean([m["hit1"] for m in metrics_list]) * 100),
        "hit3": float(np.mean([m["hit3"] for m in metrics_list]) * 100),
        "hit5": float(np.mean([m["hit5"] for m in metrics_list]) * 100),
        "recall4": float(np.mean([m["recall4"] for m in metrics_list])),
        "recall20": float(np.mean([m["recall20"] for m in metrics_list])),
        "n_queries": n,
        "n_rq_zero": rq_zero,
        "rq_mean": float(np.mean(rq_values)),
        "rq_median": float(np.median(rq_values)),
        "scores_by_paper": scores_by_paper,
    }


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 100)
    print("DEFINITIVE UNBLINDED HELD-OUT BENCHMARK (48 PAPERS)")
    print("Audit-Remediated: Global IDCG | Canonical Stopwords | Strict Containment | MC p-value")
    print("=" * 100)

    held_out_aids, held_out_corpus, held_out_queries = load_held_out_data()
    print(f"  {len(held_out_aids)} Held-Out papers, {len(held_out_queries)} answerable queries.")

    # Build both chunk arms
    print("\n[HELD-OUT] Building chunk arms...")
    as_is_chunks, min_interv_chunks = build_chunk_arms(held_out_corpus)
    n_trunc_asis = sum(1 for c in as_is_chunks if c.get("is_truncated"))
    n_trunc_min = sum(1 for c in min_interv_chunks if c.get("is_truncated"))
    print(f"  As-Is: {len(as_is_chunks)} chunks, {n_trunc_asis} truncated ({n_trunc_asis/len(as_is_chunks)*100:.1f}%)")
    print(f"  Minimal-Intervention: {len(min_interv_chunks)} chunks, {n_trunc_min} truncated ({n_trunc_min/len(min_interv_chunks)*100:.1f}%)")

    # We run the primary benchmark on as-is chunks (production config)
    # AND the pre-registered primary testbed on minimal-intervention chunks
    for arm_name, chunks in [("as-is", as_is_chunks), ("minimal-intervention", min_interv_chunks)]:
        print(f"\n{'='*100}")
        print(f"BENCHMARK ARM: {arm_name.upper()} CHUNKS ({len(chunks)} chunks)")
        print(f"{'='*100}")

        # Build paper-chunk index
        paper_chunk_map: Dict[str, List[int]] = {}
        for idx, c in enumerate(chunks):
            paper_chunk_map.setdefault(c["paper_arxiv_id"], []).append(idx)

        # Pre-compute R_q for all queries
        print("[HELD-OUT] Pre-computing R_q (total relevant per query)...")
        rq_map = precompute_rq(held_out_queries, chunks, paper_chunk_map, tau=0.55)
        rq_vals = list(rq_map.values())
        rq_0 = sum(1 for r in rq_vals if r == 0)
        rq_1 = sum(1 for r in rq_vals if r == 1)
        rq_ge2 = sum(1 for r in rq_vals if r >= 2)
        n_q = len(rq_vals)
        print(f"  R_q breakdown on {arm_name.upper()} (N={n_q}):")
        print(f"    R_q = 0:   {rq_0:2d} queries ({rq_0/n_q*100:5.1f}%)")
        print(f"    R_q = 1:   {rq_1:2d} queries ({rq_1/n_q*100:5.1f}%)")
        print(f"    R_q >= 2:  {rq_ge2:2d} queries ({rq_ge2/n_q*100:5.1f}%)")
        print(f"    Summary: mean={np.mean(rq_vals):.2f}, median={np.median(rq_vals):.1f}, min={min(rq_vals)}, max={max(rq_vals)}")

        # 1. Lexical baselines
        from transformers import AutoTokenizer
        bge_tok = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
        wp_tokenizer = lambda text: [t for t in bge_tok.tokenize(text.lower()) if len(t) > 1]

        print("\n[HELD-OUT] 1. Lexical Reference Baselines...")
        bm25_wp = evaluate_bm25(chunks, held_out_queries, rq_map, wp_tokenizer,
                                "BM25 [WordPiece Subwords]", tau=0.55)
        bm25_regex = evaluate_bm25(chunks, held_out_queries, rq_map, tokenize_regex,
                                   "BM25 [Regex + 39 Stopwords]", tau=0.55)

        # 2. Dense models
        print("\n[HELD-OUT] 2. Registered Baseline: all-MiniLM-L6-v2...")
        base_res = evaluate_dense_model(
            "sentence-transformers/all-MiniLM-L6-v2", chunks, held_out_queries, rq_map,
            query_prefix="", passage_prefix="", tau=0.55
        )

        bge_res = evaluate_dense_model(
            "BAAI/bge-small-en-v1.5", chunks, held_out_queries, rq_map,
            query_prefix="Represent this sentence for searching relevant passages: ",
            passage_prefix="", tau=0.55
        )

        e5_res = evaluate_dense_model(
            "intfloat/e5-small-v2", chunks, held_out_queries, rq_map,
            query_prefix="query: ", passage_prefix="passage: ", tau=0.55
        )

        mpnet_res = evaluate_dense_model(
            "sentence-transformers/all-mpnet-base-v2", chunks, held_out_queries, rq_map,
            query_prefix="", passage_prefix="", tau=0.55
        )

        # 3. Exploratory: SPECTER2 (unadapted base model — no adapter installed)
        specter_res = evaluate_dense_model(
            "allenai/specter2_base", chunks, held_out_queries, rq_map,
            query_prefix="", passage_prefix="", tau=0.55
        )

        # 4. Hypothesis testing (Holm-Bonferroni M=3)
        candidates = [
            ("intfloat/e5-small-v2", e5_res),
            ("BAAI/bge-small-en-v1.5", bge_res),
            ("sentence-transformers/all-mpnet-base-v2", mpnet_res),
        ]

        stat_results = []
        for name, c_res in candidates:
            diff, ci, p_val = paired_cluster_bootstrap(
                base_res["within_paper"]["scores_by_paper"],
                c_res["within_paper"]["scores_by_paper"],
                n_bootstraps=2000,
            )
            stat_results.append({
                "model_name": name, "res": c_res,
                "diff": diff, "ci_lower": ci[0], "ci_upper": ci[1], "p_val": p_val,
            })

        stat_results.sort(key=lambda x: x["p_val"])
        M = len(stat_results)
        for rank_idx, item in enumerate(stat_results):
            alpha_k = 0.05 / (M - rank_idx)
            item["holm_alpha"] = alpha_k
            item["is_sig"] = item["p_val"] <= alpha_k
            item["meets_sesoi"] = item["diff"] >= 0.030

        # Direct Head-to-Head Bootstrap: E5 vs BGE
        diff_e5_bge, ci_e5_bge, p_val_e5_bge = paired_cluster_bootstrap(
            bge_res["within_paper"]["scores_by_paper"],
            e5_res["within_paper"]["scores_by_paper"],
            n_bootstraps=2000,
        )

        # 5. Print results
        print(f"\n{'='*130}")
        print(f"HELD-OUT BENCHMARK RESULTS [{arm_name.upper()}] (K=48 Papers, N={len(held_out_queries)} Queries, tau=0.55)")
        print(f"{'='*130}")
        _print_table(base_res, stat_results, specter_res, bm25_wp, bm25_regex)
        print(f"\n[DIRECT HEAD-TO-HEAD] intfloat/e5-small-v2 vs BAAI/bge-small-en-v1.5:")
        print(f"  Delta nDCG@4: {diff_e5_bge:+.4f} [95% CI: {ci_e5_bge[0]:+.4f}, {ci_e5_bge[1]:+.4f}] | p-value: {p_val_e5_bge:.4f} | Significant (alpha=0.05): {'YES*' if p_val_e5_bge <= 0.05 else 'No'}")

        # 6. Save JSON
        out_payload = {
            "arm": arm_name,
            "dataset": f"QASPER Held-Out (48 Papers, {len(held_out_queries)} Queries)",
            "protocol": "Pre-registered single-unblinded benchmark (audit-remediated)",
            "containment_tau": 0.55,
            "n_bootstraps": 2000,
            "cluster_level": "paper",
            "rq_distribution": {
                "mean": float(np.mean(rq_vals)),
                "median": float(np.median(rq_vals)),
                "min": int(min(rq_vals)),
                "max": int(max(rq_vals)),
                "n_rq_zero": rq_0,
                "n_rq_one": rq_1,
                "n_rq_ge2": rq_ge2,
            },
            "baseline": {k: v for k, v in base_res.items() if k != "within_paper" or True},
            "candidates": [item["res"] for item in stat_results],
            "exploratory": specter_res,
            "lexical_baselines": [bm25_wp, bm25_regex],
            "primary_hypothesis_tests": [
                {
                    "model_name": item["model_name"],
                    "delta_ndcg4": item["diff"],
                    "ci_lower": item["ci_lower"],
                    "ci_upper": item["ci_upper"],
                    "p_value": item["p_val"],
                    "holm_alpha": item["holm_alpha"],
                    "is_significant": item["is_sig"],
                    "meets_sesoi_0_03": item["meets_sesoi"],
                }
                for item in stat_results
            ],
            "direct_pairwise_head_to_head": {
                "test": "intfloat/e5-small-v2 vs BAAI/bge-small-en-v1.5",
                "delta_ndcg4": diff_e5_bge,
                "ci_lower": ci_e5_bge[0],
                "ci_upper": ci_e5_bge[1],
                "p_value": p_val_e5_bge,
                "is_significant_at_0_05": p_val_e5_bge <= 0.05,
            },
        }

        # Remove scores_by_paper from JSON output to keep size manageable
        for section in ["within_paper", "cross_paper"]:
            for res in [out_payload["baseline"], out_payload["exploratory"]] + out_payload["candidates"] + out_payload["lexical_baselines"]:
                if section in res and "scores_by_paper" in res[section]:
                    del res[section]["scores_by_paper"]

        suffix = arm_name.replace("-", "_")
        out_file = WORKSPACE_ROOT / "eval" / "prepared" / f"held_out_final_benchmark_{suffix}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out_payload, f, indent=2)
        print(f"\n[HELD-OUT] Results saved to: {out_file.relative_to(WORKSPACE_ROOT)}")


def _print_table(base_res, stat_results, specter_res, bm25_wp, bm25_regex):
    """Print the master benchmark table for both Within-Paper and Cross-Paper scopes."""
    all_models = [
        ("all-MiniLM-L6-v2 [Base]", base_res, True),
        ("intfloat/e5-small-v2", [item for item in stat_results if "e5" in item["model_name"]][0]["res"], False),
        ("BAAI/bge-small-en-v1.5", [item for item in stat_results if "bge" in item["model_name"]][0]["res"], False),
        ("all-mpnet-base-v2", [item for item in stat_results if "mpnet" in item["model_name"]][0]["res"], False),
        ("specter2_base [Explor/Unadapted]", specter_res, False),
        ("BM25 [WordPiece Subwords]", bm25_wp, False),
        ("BM25 [Regex + 39 Stopwords]", bm25_regex, False),
    ]

    header = (f"{'Model':<35} {'nDCG@4':>7} {'nDCG@10':>8} {'MRR@5':>7} "
              f"{'Hit@1':>6} {'Hit@3':>6} {'Hit@5':>6} {'Rec@4':>6} {'Rec@20':>7} "
              f"{'Delta nDCG@4 [95% CI]':>30} {'p-val':>8} {'Holm?':>8}")

    print("\n--- 1. WITHIN-PAPER RETRIEVAL (PRIMARY SCOPE) ---")
    print(header)
    print("-" * len(header))

    def _render_row(name, res, scope, delta_str="", p_str="", holm_str=""):
        s = res[scope]
        print(f"{name:<35} {s['ndcg4']:>7.4f} {s['ndcg10']:>8.4f} {s['mrr5']:>7.4f} "
              f"{s['hit1']:>5.1f}% {s['hit3']:>5.1f}% {s['hit5']:>5.1f}% {s['recall4']:>6.3f} {s['recall20']:>7.3f} "
              f"{delta_str:>30} {p_str:>8} {holm_str:>8}")

    _render_row("all-MiniLM-L6-v2 [Base]", base_res, "within_paper", "Reference", "-", "-")

    for item in stat_results:
        m_name = item["model_name"].split("/")[-1][:32]
        d = f"{item['diff']:+.4f} [{item['ci_lower']:+.4f},{item['ci_upper']:+.4f}]"
        sig = "YES*" if item["is_sig"] else "No"
        sesoi = " (>=SESOI)" if item["meets_sesoi"] else ""
        _render_row(m_name, item["res"], "within_paper", d, f"{item['p_val']:.4f}", sig + sesoi)

    _render_row("specter2_base [Explor/Unadapted]", specter_res, "within_paper", "[Exploratory]", "-", "-")
    print("-" * len(header))
    _render_row("BM25 [WordPiece Subwords]", bm25_wp, "within_paper", "[Lexical Ref]", "-", "-")
    _render_row("BM25 [Regex + 39 Stopwords]", bm25_regex, "within_paper", "[Lexical Ref]", "-", "-")

    # Cross-Paper Retrieval
    print("\n--- 2. CROSS-PAPER RETRIEVAL (SECONDARY SCOPE) ---")
    print(header)
    print("-" * len(header))
    _render_row("all-MiniLM-L6-v2 [Base]", base_res, "cross_paper", "Reference", "-", "-")
    for name, r, is_base in all_models[1:]:
        # Paired bootstrap for cross-paper against base
        diff_xp, ci_xp, p_xp = paired_cluster_bootstrap(
            base_res["cross_paper"]["scores_by_paper"],
            r["cross_paper"]["scores_by_paper"],
            n_bootstraps=2000,
            seed=42,
        )
        d_str = f"{diff_xp:+.4f} [{ci_xp[0]:+.4f},{ci_xp[1]:+.4f}]"
        p_str = f"{p_xp:.4f}"
        sig_str = "YES*" if p_xp <= 0.05 else "No"
        if "specter2" in name.lower():
            m_label = "specter2_base [Unadapted]"
        elif "/" in name:
            m_label = name.split("/")[-1][:32]
        else:
            m_label = name[:32]
        _render_row(m_label, r, "cross_paper", d_str, p_str, sig_str)

    # Retrieval Latency
    print("\n--- 3. STANDARDIZED RETRIEVAL LATENCY (MEAN MS/QUERY) ---")
    lat_header = f"{'Model':<35} {'Single Q Encode (ms)':>22} {'Within-Paper Search':>20} {'Cross-Paper Search':>20}"
    print(lat_header)
    print("-" * len(lat_header))
    for name, r, _ in all_models:
        if "specter2" in name.lower():
            m_label = "specter2_base [Unadapted]"
        elif "/" in name:
            m_label = name.split("/")[-1][:32]
        else:
            m_label = name[:32]
        enc_str = f"{r.get('single_query_encode_ms', 0.0):.2f} ms" if "single_query_encode_ms" in r else "N/A (lexical)"
        wp_str = f"{r.get('wp_latency_ms', 0.0):.2f} ms"
        xp_str = f"{r.get('xp_latency_ms', 0.0):.2f} ms"
        print(f"{m_label:<35} {enc_str:>22} {wp_str:>20} {xp_str:>20}")
    print("-" * len(lat_header))


if __name__ == "__main__":
    main()
