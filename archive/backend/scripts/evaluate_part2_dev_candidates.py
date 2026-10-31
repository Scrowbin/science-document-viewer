"""
Part 2: Pre-Registered Dense Embedding Model Comparison on Dev Set (48 Papers, 128 Queries)
Evaluates candidate sentence-level embedding models against registered baseline (all-MiniLM-L6-v2)
using paper-level cluster bootstrap (B=2,000), Holm-Bonferroni correction, and calibrated tau* = 0.55.

Remediated with:
  Fix 1: Global IDCG nDCG@4 and nDCG@10 (based on total relevant chunks R_q) + Zero-Relevant Query Guard
  Fix 2: Canonical 39 stopwords
  Fix 3: Strict evidence containment with chunk-length guard & FLOAT stripping
  Fix 4: Standardized retrieval latency (query encode + similarity ranking)
  Fix 5a: Corrected Monte Carlo p-value bound
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure root and backend are on sys.path
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


# ─── BM25 Lexical Baseline ───────────────────────────────────────────────────
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

    def retrieve(
        self, query: str, cand_indices: Optional[List[int]] = None,
        top_k: int = TOP_K, k1: float = 1.5, b: float = 0.75
    ) -> List[int]:
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
def load_dev_data():
    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    dev_aids = set(split_data["dev_papers"])

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)
    dev_corpus = {k: v for k, v in corpus_all.items() if k in dev_aids}

    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)
    dev_queries = [
        q for q in qa_all
        if q.get("paper_arxiv_id") in dev_aids and q.get("question_type") != "unanswerable"
    ]
    return dev_aids, dev_corpus, dev_queries


def build_dev_corpus_chunks(dev_corpus):
    chunks = []
    for aid, doc in dev_corpus.items():
        sec_list = doc.get("sections", [])
        base_chunks = chunk_sections(sec_list, strategy="section_overlap", max_tokens=350, overlap=70)
        for c_idx, c in enumerate(base_chunks):
            c["chunk_id"] = f"{aid}_c_{c_idx}"
            c["paper_arxiv_id"] = aid
            chunks.append(c)
    return chunks


# ─── Pre-compute R_q per query ──────────────────────────────────────────────
def precompute_rq(queries, chunks, paper_chunk_map, tau=0.55):
    rq_map = {}
    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        paper_chunks = [chunks[i] for i in paper_chunk_map.get(aid, [])]
        rq_map[q_idx] = count_relevant_chunks(paper_chunks, aid, quote, ev_list, tau=tau)
    return rq_map


# ─── Query Metrics Computation ──────────────────────────────────────────────
def compute_query_metrics(ranked_chunks, q, rq, tau=0.55):
    aid = q["paper_arxiv_id"]
    quote = q.get("verbatim_evidence_quote", "")
    ev_list = q.get("evidence_list", [])

    rels = [1 if is_chunk_hit(c, aid, quote, ev_list, tau=tau) else 0 for c in ranked_chunks[:TOP_K]]

    ndcg4 = compute_ndcg(rels, total_relevant=rq, k=4)
    ndcg10 = compute_ndcg(rels, total_relevant=rq, k=10)

    found_rank = None
    for i, r in enumerate(rels[:5]):
        if r == 1:
            found_rank = i + 1
            break
    mrr5 = 1.0 / found_rank if found_rank else 0.0

    hit1 = 1 if found_rank == 1 else 0
    hit3 = 1 if found_rank and found_rank <= 3 else 0
    hit5 = 1 if found_rank and found_rank <= 5 else 0

    recall4 = sum(rels[:4]) / rq if rq > 0 else 0.0
    recall20 = sum(rels[:20]) / rq if rq > 0 else 0.0

    return {
        "ndcg4": ndcg4,
        "ndcg10": ndcg10,
        "mrr5": mrr5,
        "hit1": hit1,
        "hit3": hit3,
        "hit5": hit5,
        "recall4": recall4,
        "recall20": recall20,
        "rq": rq,
    }


def _aggregate_metrics(metrics_list, scores_by_paper):
    n = len(metrics_list)
    rq_values = [m["rq"] for m in metrics_list]
    rq_zero = sum(1 for r in rq_values if r == 0)
    pos_metrics = [m for m in metrics_list if m["rq"] > 0]

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
        "ndcg4_pos_rq_only": float(np.mean([m["ndcg4"] for m in pos_metrics])) if pos_metrics else 0.0,
        "scores_by_paper": scores_by_paper,
    }


# ─── Lexical BM25 Evaluation ────────────────────────────────────────────────
def evaluate_bm25(chunks, queries, rq_map, tokenizer_fn, name, tau=0.55):
    bm25 = SimpleBM25(chunks, tokenizer_fn)
    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    wp_metrics, xp_metrics = [], []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    xp_scores_by_paper: Dict[str, List[float]] = {}
    wp_lat, xp_lat = 0.0, 0.0

    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        q_text = q["question"]
        rq = rq_map[q_idx]

        # Within-paper
        cand_idx = paper_chunk_indices.get(aid, [])
        t0 = time.perf_counter()
        ranked_wp_idx = bm25.retrieve(q_text, cand_indices=cand_idx, top_k=TOP_K)
        wp_lat += time.perf_counter() - t0
        ranked_wp = [chunks[i] for i in ranked_wp_idx]
        m_wp = compute_query_metrics(ranked_wp, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

        # Cross-paper
        t0 = time.perf_counter()
        ranked_xp_idx = bm25.retrieve(q_text, cand_indices=None, top_k=TOP_K)
        xp_lat += time.perf_counter() - t0
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


# ─── Dense Model Evaluation ─────────────────────────────────────────────────
def evaluate_model(
    model_name: str,
    chunks: List[Dict[str, Any]],
    dev_queries: List[Dict[str, Any]],
    rq_map: Dict[int, int],
    query_prefix: str = "",
    passage_prefix: str = "",
    tau: float = 0.55,
):
    print(f"\n[EVAL-MODEL] Loading: {model_name}...")
    model = SentenceTransformer(model_name)

    print(f"  Encoding {len(chunks)} Dev chunks (passage prefix: '{passage_prefix}')...")
    doc_texts = [passage_prefix + c["text"] for c in chunks]
    doc_embs = model.encode(doc_texts, batch_size=16, show_progress_bar=False, normalize_embeddings=True)

    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        aid = c["paper_arxiv_id"]
        paper_chunk_indices.setdefault(aid, []).append(idx)

    print(f"  Encoding {len(dev_queries)} queries (query prefix: '{query_prefix}')...")
    q_texts = [query_prefix + q["question"] for q in dev_queries]
    q_embs = model.encode(q_texts, batch_size=16, show_progress_bar=False, normalize_embeddings=True)

    wp_metrics, xp_metrics = [], []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    xp_scores_by_paper: Dict[str, List[float]] = {}
    wp_lat, xp_lat = 0.0, 0.0

    for q_idx, q in enumerate(dev_queries):
        aid = q["paper_arxiv_id"]
        q_emb = q_embs[q_idx]
        rq = rq_map[q_idx]

        # Within-paper search (timed)
        cand_indices = paper_chunk_indices.get(aid, [])
        if cand_indices:
            cand_embs = doc_embs[cand_indices]
            t0 = time.perf_counter()
            sims = np.dot(cand_embs, q_emb)
            ranked_local = np.argsort(-sims)[:TOP_K]
            wp_lat += time.perf_counter() - t0
            ranked_chunks = [chunks[cand_indices[i]] for i in ranked_local]
        else:
            ranked_chunks = []

        m_wp = compute_query_metrics(ranked_chunks, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

        # Cross-paper search (timed)
        t0 = time.perf_counter()
        all_sims = np.dot(doc_embs, q_emb)
        ranked_global = np.argsort(-all_sims)[:TOP_K]
        xp_lat += time.perf_counter() - t0
        ranked_xp_chunks = [chunks[i] for i in ranked_global]

        m_xp = compute_query_metrics(ranked_xp_chunks, q, rq, tau=tau)
        xp_metrics.append(m_xp)
        xp_scores_by_paper.setdefault(aid, []).append(m_xp["ndcg4"])

    n = len(dev_queries)

    # Standardized single-query encoding latency (batch_size=1)
    t0 = time.perf_counter()
    sample_q = q_texts[:10]
    for sq in sample_q:
        model.encode([sq], batch_size=1, show_progress_bar=False, normalize_embeddings=True)
    single_q_lat_ms = (time.perf_counter() - t0) / len(sample_q) * 1000.0

    return {
        "model_name": model_name,
        "single_query_encode_ms": round(single_q_lat_ms, 2),
        "wp_latency_ms": round(wp_lat / n * 1000, 2),
        "xp_latency_ms": round(xp_lat / n * 1000, 2),
        "total_retrieval_latency_ms": round(single_q_lat_ms + (wp_lat / n * 1000), 2),
        "within_paper": _aggregate_metrics(wp_metrics, wp_scores_by_paper),
        "cross_paper": _aggregate_metrics(xp_metrics, xp_scores_by_paper),
    }


def main():
    print("[PART-2-DEV] Loading Dev Dataset (48 Papers, 128 Queries)...")
    dev_aids, dev_corpus, dev_queries = load_dev_data()
    chunks = build_dev_corpus_chunks(dev_corpus)
    print(f"  Generated {len(chunks)} chunks across {len(dev_aids)} papers.")

    paper_chunk_map: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_map.setdefault(c["paper_arxiv_id"], []).append(idx)

    # Pre-compute R_q for all queries under strict containment
    print("  Pre-computing R_q per query (strict containment, tau*=0.55)...")
    rq_map = precompute_rq(dev_queries, chunks, paper_chunk_map, tau=0.55)
    rq_zero_cnt = sum(1 for r in rq_map.values() if r == 0)
    print(f"  R_q distribution: {len(rq_map) - rq_zero_cnt} queries with R_q > 0, {rq_zero_cnt} queries with R_q = 0.")

    # 0. Lexical Baselines on Dev
    print("\n[PART-2-DEV] Evaluating Lexical Baselines (Regex BM25)...")
    bm25_res = evaluate_bm25(chunks, dev_queries, rq_map, tokenize_regex, "BM25 [Regex + 39 Stopwords]", tau=0.55)

    # 1. Registered Baseline
    base_res = evaluate_model(
        "sentence-transformers/all-MiniLM-L6-v2",
        chunks, dev_queries, rq_map,
        query_prefix="", passage_prefix="", tau=0.55
    )

    # 2. Candidate 1 (BAAI/bge-small-en-v1.5)
    bge_res = evaluate_model(
        "BAAI/bge-small-en-v1.5",
        chunks, dev_queries, rq_map,
        query_prefix="Represent this sentence for searching relevant passages: ",
        passage_prefix="", tau=0.55
    )

    # 3. Candidate 2 (intfloat/e5-small-v2)
    e5_res = evaluate_model(
        "intfloat/e5-small-v2",
        chunks, dev_queries, rq_map,
        query_prefix="query: ",
        passage_prefix="passage: ", tau=0.55
    )

    # 4. Candidate 3 (sentence-transformers/all-mpnet-base-v2)
    mpnet_res = evaluate_model(
        "sentence-transformers/all-mpnet-base-v2",
        chunks, dev_queries, rq_map,
        query_prefix="", passage_prefix="", tau=0.55
    )

    # Statistical hypothesis comparisons against baseline (all-MiniLM-L6-v2)
    candidates = [
        ("BAAI/bge-small-en-v1.5", bge_res),
        ("intfloat/e5-small-v2", e5_res),
        ("sentence-transformers/all-mpnet-base-v2", mpnet_res),
    ]

    stat_results = []
    for name, c_res in candidates:
        diff, ci, p_val = paired_cluster_bootstrap(
            base_res["within_paper"]["scores_by_paper"],
            c_res["within_paper"]["scores_by_paper"],
            n_bootstraps=2000,
            seed=42,
        )
        stat_results.append({
            "model_name": name,
            "res": c_res,
            "diff": diff,
            "ci_lower": ci[0],
            "ci_upper": ci[1],
            "p_val": p_val,
        })

    # Sort by p-value for Holm-Bonferroni step-down (M=3)
    stat_results.sort(key=lambda x: x["p_val"])
    M = len(stat_results)
    for rank_idx, item in enumerate(stat_results):
        alpha_k = 0.05 / (M - rank_idx)
        item["holm_alpha"] = alpha_k
        item["is_sig"] = item["p_val"] <= alpha_k
        item["meets_sesoi"] = item["diff"] >= 0.030

    # Display Master Benchmark Table
    print("\n" + "=" * 115)
    print("PART 2: PRE-REGISTERED DENSE MODEL COMPARISON ON DEV SET (N=128, 48 Papers, tau*=0.55)")
    print("Corrected for: Global IDCG, Canonical 39 Stopwords, Strict Containment & Standardized Latency")
    print("=" * 115)
    print(f"Model\t\t\tnDCG@4\tnDCG@10\tMRR@5\tHit@1\tHit@5\tRec@20\tDelta nDCG@4 [95% CI]\tp-val\tHolm Sig?")
    print("-" * 115)

    # Lexical baseline row
    bm_wp = bm25_res["within_paper"]
    print(f"{bm25_res['model_name']:<24}\t{bm_wp['ndcg4']:.4f}\t{bm_wp['ndcg10']:.4f}\t{bm_wp['mrr5']:.4f}\t"
          f"{bm_wp['hit1']:.1f}%\t{bm_wp['hit5']:.1f}%\t{bm_wp['recall20']:.4f}\tLexical Ref\t\t-\t-")

    # Dense baseline row
    b_wp = base_res["within_paper"]
    print(f"all-MiniLM-L6-v2 [Base]\t{b_wp['ndcg4']:.4f}\t{b_wp['ndcg10']:.4f}\t{b_wp['mrr5']:.4f}\t"
          f"{b_wp['hit1']:.1f}%\t{b_wp['hit5']:.1f}%\t{b_wp['recall20']:.4f}\tReference\t\t-\t-")

    for item in stat_results:
        m_name = item["model_name"].split("/")[-1]
        wp = item["res"]["within_paper"]
        sig_str = "YES*" if item["is_sig"] else "No"
        sesoi_str = " (>=SESOI)" if item["meets_sesoi"] else ""
        print(f"{m_name:<24}\t{wp['ndcg4']:.4f}\t{wp['ndcg10']:.4f}\t{wp['mrr5']:.4f}\t"
              f"{wp['hit1']:.1f}%\t{wp['hit5']:.1f}%\t{wp['recall20']:.4f}\t"
              f"{item['diff']:+.4f} [{item['ci_lower']:+.4f}, {item['ci_upper']:+.4f}]\t{item['p_val']:.4f}\t{sig_str}{sesoi_str}")
    print("=" * 115)

    # Latency comparison table
    print("\n" + "=" * 80)
    print("RETRIEVAL LATENCY BENCHMARK ON DEV SET (Mean ms/query)")
    print("=" * 80)
    print(f"Model\t\t\tEncode (ms)\tWithin-Paper Search\tTotal Retrieval")
    print("-" * 80)
    print(f"{'BM25 (Regex)':<24}\tN/A (lexical)\t{bm25_res['wp_latency_ms']:.2f} ms\t\t{bm25_res['wp_latency_ms']:.2f} ms")
    for r in [base_res, bge_res, e5_res, mpnet_res]:
        m_name = r["model_name"].split("/")[-1]
        print(f"{m_name:<24}\t{r['single_query_encode_ms']:.2f} ms\t\t{r['wp_latency_ms']:.2f} ms\t\t{r['total_retrieval_latency_ms']:.2f} ms")
    print("=" * 80)

    # Save to JSON
    out_payload = {
        "lexical_baseline": bm25_res,
        "dense_baseline": base_res,
        "candidates": [item["res"] for item in stat_results],
        "hypothesis_tests": [
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
    }
    out_file = WORKSPACE_ROOT / "eval" / "prepared" / "part2_dev_candidates_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\n[PART-2-DEV] Saved results artifact to: {out_file.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()
