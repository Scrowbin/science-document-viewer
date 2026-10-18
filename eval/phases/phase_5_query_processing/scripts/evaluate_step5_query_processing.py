"""
Phase 5 Evaluation: Academic Query Processing & Technical Acronym Expansion (Step 5 / RAG-5).
Evaluates whether technical acronym expansion and conversational filler stripping
improve academic retrieval accuracy on the 160-paper / 487-query high-power cohort.

Ablation Arms:
  1. Arm 1 (Baseline): Raw Query
  2. Arm 2: Conversational Filler Stripping
  3. Arm 3: Acronym Expansion Inline: 'LoRA' -> 'LoRA (Low-Rank Adaptation)'
  4. Arm 4: Acronym Expansion Append: 'query... Low-Rank Adaptation'
  5. Arm 5: Combined (Inline Expansion + Filler Stripping)

Evaluates under:
  - Dense champion: intfloat/e5-small-v2 (FP32, 384-dim, asymmetric 'query: ' prefix)
  - Lexical: BM25 with WordPiece subword tokenization
Hypothesis Testing:
  - Paired paper-cluster bootstrap (B=2,000) comparing each arm to Arm 1.
"""

import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Set, Tuple

import numpy as np
import psutil

WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from apps.documents.services.chunking_utils import chunk_sections
from apps.documents.services.query_processing import (
    ACADEMIC_ACRONYMS,
    QueryPreprocessor,
    get_query_preprocessor,
)
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

PHASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PHASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

PHASE3_ARTIFACTS = WORKSPACE_ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts"
EVAL_PREPARED = WORKSPACE_ROOT / "eval" / "prepared"

TOP_K = 20


def get_process_rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024.0 * 1024.0)


# ─── Load Data ──────────────────────────────────────────────────────────────
def load_data():
    split_file = PHASE3_ARTIFACTS / "expanded_held_out_split.json"
    if not split_file.exists():
        split_file = EVAL_PREPARED / "expanded_held_out_split.json"

    corpus_file = EVAL_PREPARED / "expanded_corpus.json"
    queries_file = EVAL_PREPARED / "expanded_qasper_sampled.json"

    with open(split_file, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    held_out_aids = set(split_data.get("held_out_papers", []) or 
                        (split_data.get("frozen_cohort_1_papers", []) + split_data.get("cohort_2_papers", [])))

    with open(corpus_file, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)
        if isinstance(corpus_data, dict):
            corpus = [v for k, v in corpus_data.items() if k in held_out_aids]
        else:
            corpus = [p for p in corpus_data if p.get("arxiv_id", p.get("paper_arxiv_id")) in held_out_aids]

    with open(queries_file, "r", encoding="utf-8") as f:
        queries = [q for q in json.load(f) if q["paper_arxiv_id"] in held_out_aids]

    return held_out_aids, corpus, queries


def precompute_rq(queries: List[Dict[str, Any]], chunks: List[Dict[str, Any]],
                  paper_chunk_map: Dict[str, List[int]], tau: float = 0.55) -> Dict[int, int]:
    rq_map: Dict[int, int] = {}
    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        cand_indices = paper_chunk_map.get(aid, [])
        cand_chunks = [chunks[i] for i in cand_indices]
        rq_map[q_idx] = count_relevant_chunks(cand_chunks, aid, quote, ev_list, tau=tau)
    return rq_map


def compute_query_metrics(ranked_chunks: List[Dict[str, Any]], query: Dict[str, Any],
                          rq: int, tau: float = 0.55) -> Dict[str, float]:
    aid = query["paper_arxiv_id"]
    quote = query.get("verbatim_evidence_quote", "")
    ev_list = query.get("evidence_list", [])

    hits: List[int] = [1 if is_chunk_hit(c, aid, quote, ev_list, tau=tau) else 0 for c in ranked_chunks]
    dcg4 = compute_dcg(hits[:4], k=4)
    idcg4 = sum(1.0 / np.log2(i + 2) for i in range(min(rq, 4))) if rq > 0 else 1.0
    ndcg4 = dcg4 / idcg4 if idcg4 > 0 else 0.0

    mrr5 = 0.0
    for rank_idx, h in enumerate(hits[:5]):
        if h:
            mrr5 = 1.0 / (rank_idx + 1)
            break

    hit5 = 1.0 if any(hits[:5]) else 0.0
    rec20 = (sum(hits[:20]) / float(rq)) if rq > 0 else 0.0

    return {
        "ndcg4": float(ndcg4),
        "mrr5": float(mrr5),
        "hit5": float(hit5),
        "recall20": float(rec20),
    }


def _aggregate_metrics(metrics: List[Dict[str, float]], scores_by_paper: Dict[str, List[float]]) -> Dict[str, Any]:
    return {
        "ndcg4": float(np.mean([m["ndcg4"] for m in metrics])),
        "mrr5": float(np.mean([m["mrr5"] for m in metrics])),
        "hit5": float(np.mean([m["hit5"] for m in metrics]) * 100.0),
        "recall20": float(np.mean([m["recall20"] for m in metrics])),
        "scores_by_paper": scores_by_paper,
    }


# ─── Simple BM25 Implementation ─────────────────────────────────────────────
class SimpleBM25:
    def __init__(self, corpus: List[Dict[str, Any]], tokenizer_fn: Callable[[str], List[str]],
                 k1: float = 1.5, b: float = 0.75):
        self.tokenizer_fn = tokenizer_fn
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lens: List[int] = []
        self.doc_freqs: Dict[str, int] = {}
        self.postings: Dict[str, List[Tuple[int, int]]] = {}

        for doc_id, item in enumerate(corpus):
            tokens = self.tokenizer_fn(item["text"])
            self.doc_lens.append(len(tokens))
            term_counts: Dict[str, int] = {}
            for t in tokens:
                term_counts[t] = term_counts.get(t, 0) + 1
            for term, count in term_counts.items():
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
                self.postings.setdefault(term, []).append((doc_id, count))

        self.avg_doc_len = sum(self.doc_lens) / max(1, self.corpus_size)
        self.idf: Dict[str, float] = {}
        for term, df in self.doc_freqs.items():
            self.idf[term] = np.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

    def retrieve(self, query_text: str, cand_indices: List[int], top_k: int = 20) -> List[int]:
        q_tokens = self.tokenizer_fn(query_text)
        cand_set = set(cand_indices)
        scores: Dict[int, float] = {doc_id: 0.0 for doc_id in cand_indices}

        for token in q_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for doc_id, tf in self.postings.get(token, []):
                if doc_id in cand_set:
                    L_d = self.doc_lens[doc_id]
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (L_d / self.avg_doc_len))
                    score = idf_val * (tf * (self.k1 + 1.0)) / max(1e-12, denom)
                    scores[doc_id] += score

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [doc_id for doc_id, _ in ranked[:top_k]]


# ─── Query Transformation Arm Runner ─────────────────────────────────────────
def run_query_processing_evaluation():
    print("=" * 110)
    print("PHASE 5: ACADEMIC QUERY PROCESSING & ACRONYM EXPANSION BENCHMARK")
    print("Cohort: 160 Papers | 487 Queries | 4,108 Chunks | Strict Containment tau*=0.55")
    print("=" * 110)

    held_out_aids, corpus, queries = load_data()
    print(f"Loaded {len(held_out_aids)} papers, {len(queries)} answerable queries.")

    # 1. Load or build chunks
    chunk_file = PHASE3_ARTIFACTS / "expanded_160_chunks.json"
    if chunk_file.exists():
        with open(chunk_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        print(f"Loaded {len(chunks)} cached chunks from Phase 3.")
    else:
        chunks = chunk_sections(corpus, strategy="section_overlap", max_tokens=350, overlap=70)
        print(f"Generated {len(chunks)} chunks.")

    paper_chunk_map: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_map.setdefault(c["paper_arxiv_id"], []).append(idx)

    print("Pre-computing relevant chunk count R_q...")
    rq_map = precompute_rq(queries, chunks, paper_chunk_map, tau=0.55)

    # 2. Preprocessor Instance
    qp = get_query_preprocessor()

    # Preprocessing Arms
    arms: List[Tuple[str, str, bool]] = [
        ("Arm 1: Raw Query", "raw", False),
        ("Arm 2: Filler Stripping", "raw", True),
        ("Arm 3: Acronym Inline", "expand_inline", False),
        ("Arm 4: Acronym Append", "expand_append", False),
        ("Arm 5: Combined (Inline + Strip)", "expand_inline", True),
    ]

    # Pre-generate transformed queries
    transformed_queries_by_arm: Dict[str, List[str]] = {}
    acronym_hits_count = 0
    total_expanded_terms = 0

    for arm_name, mode, strip_f in arms:
        t_queries = []
        for q in queries:
            raw_text = q["question"]
            processed = qp.preprocess(raw_text, mode=mode, strip_fillers=strip_f)
            t_queries.append(processed)
        transformed_queries_by_arm[arm_name] = t_queries

    # Acronym statistics on raw queries
    for q in queries:
        matches = qp.extract_acronyms(q["question"])
        if matches:
            acronym_hits_count += 1
            total_expanded_terms += len(matches)

    print(f"\n[QUERY CORPUS STATS]")
    print(f"  Total queries: {len(queries)}")
    print(f"  Queries with acronyms: {acronym_hits_count}/{len(queries)} ({acronym_hits_count/len(queries)*100:.1f}%)")
    print(f"  Total acronym mentions: {total_expanded_terms}")

    # 3. Dense Embeddings Setup (using champion intfloat/e5-small-v2)
    doc_embs_file = PHASE3_ARTIFACTS / "expanded_160_e5_doc_embs.npy"
    if doc_embs_file.exists():
        doc_embs = np.load(doc_embs_file)
        print(f"\nLoaded {doc_embs.shape} precomputed E5 document embeddings from Phase 3.")
    else:
        print("\nEncoding document chunks via intfloat/e5-small-v2...")
        model = SentenceTransformer("intfloat/e5-small-v2")
        doc_texts = ["passage: " + c["text"] for c in chunks]
        doc_embs = model.encode(doc_texts, batch_size=32, normalize_embeddings=True)

    print("\nLoading SentenceTransformer for query embedding inference...")
    model = SentenceTransformer("intfloat/e5-small-v2")

    # 4. BM25 Tokenizer
    from transformers import AutoTokenizer
    bge_tok = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
    wp_tokenizer = lambda text: [t for t in bge_tok.tokenize(text.lower()) if len(t) > 1]
    bm25 = SimpleBM25(chunks, wp_tokenizer)

    dense_results: Dict[str, Dict[str, Any]] = {}
    bm25_results: Dict[str, Dict[str, Any]] = {}

    for arm_name, mode, strip_f in arms:
        t_queries = transformed_queries_by_arm[arm_name]
        print(f"\n--- Evaluating {arm_name} ---")

        # Dense Evaluation
        t0 = time.time()
        q_texts = ["query: " + tq for tq in t_queries]
        q_embs = model.encode(q_texts, batch_size=32, normalize_embeddings=True)
        q_enc_time = time.time() - t0

        dense_metrics = []
        dense_scores_by_paper: Dict[str, List[float]] = {}
        wp_lat = 0.0

        for q_idx, q in enumerate(queries):
            aid = q["paper_arxiv_id"]
            cand_indices = paper_chunk_map.get(aid, [])
            rq = rq_map[q_idx]

            if cand_indices:
                cand_embs = doc_embs[cand_indices]
                t_search_0 = time.time()
                sims = np.dot(cand_embs, q_embs[q_idx])
                top_indices = np.argsort(sims)[::-1][:TOP_K]
                wp_lat += time.time() - t_search_0
                ranked_chunks = [chunks[cand_indices[i]] for i in top_indices]
            else:
                ranked_chunks = []

            m = compute_query_metrics(ranked_chunks, q, rq, tau=0.55)
            dense_metrics.append(m)
            dense_scores_by_paper.setdefault(aid, []).append(m["ndcg4"])

        dense_agg = _aggregate_metrics(dense_metrics, dense_scores_by_paper)
        dense_agg["query_encode_latency_ms"] = round(q_enc_time / len(queries) * 1000, 2)
        dense_agg["avg_query_len_chars"] = float(np.mean([len(tq) for tq in t_queries]))
        dense_results[arm_name] = dense_agg

        # BM25 Evaluation
        bm25_metrics = []
        bm25_scores_by_paper: Dict[str, List[float]] = {}
        for q_idx, q in enumerate(queries):
            aid = q["paper_arxiv_id"]
            cand_indices = paper_chunk_map.get(aid, [])
            rq = rq_map[q_idx]
            ranked_indices = bm25.retrieve(t_queries[q_idx], cand_indices=cand_indices, top_k=TOP_K)
            ranked_chunks = [chunks[i] for i in ranked_indices]
            m = compute_query_metrics(ranked_chunks, q, rq, tau=0.55)
            bm25_metrics.append(m)
            bm25_scores_by_paper.setdefault(aid, []).append(m["ndcg4"])

        bm25_agg = _aggregate_metrics(bm25_metrics, bm25_scores_by_paper)
        bm25_results[arm_name] = bm25_agg

    # 5. Bootstrap Hypothesis Testing vs Arm 1 (Baseline)
    base_dense_scores = dense_results["Arm 1: Raw Query"]["scores_by_paper"]
    dense_comparisons: List[Dict[str, Any]] = []

    for arm_name, _, _ in arms[1:]:
        cand_scores = dense_results[arm_name]["scores_by_paper"]
        diff, ci, p_val = paired_cluster_bootstrap(base_dense_scores, cand_scores, n_bootstraps=2000)
        dense_comparisons.append({
            "arm_name": arm_name,
            "delta_ndcg4": diff,
            "ci_95": [ci[0], ci[1]],
            "p_value": p_val,
            "is_significant": p_val <= 0.05,
        })

    # 6. Print Master Results Table
    print("\n" + "=" * 130)
    print("STEP 5: QUERY PROCESSING ABLATION RESULTS (DENSE E5-SMALL-V2)")
    print("=" * 130)
    print(f"{'Arm':<32} | {'nDCG@4':<8} | {'MRR@5':<8} | {'Hit@5':<7} | {'Rec@20':<8} | {'Delta':<8} | {'95% CI':<19} | {'p-value':<7} | {'Sig*'}")
    print("-" * 130)

    base_d = dense_results["Arm 1: Raw Query"]
    print(f"{'Arm 1: Raw Query (Baseline)':<32} | {base_d['ndcg4']:>8.4f} | {base_d['mrr5']:>8.4f} | {base_d['hit5']:>6.1f}% | {base_d['recall20']:>8.4f} | {'Base':<8} | {'Reference':<19} | {'-':<7} | {'-'}")

    for comp in dense_comparisons:
        arm_name = comp["arm_name"]
        d = dense_results[arm_name]
        ci_str = f"[{comp['ci_95'][0]:+.4f}, {comp['ci_95'][1]:+.4f}]"
        sig_str = "YES*" if comp["is_significant"] else "No"
        print(f"{arm_name:<32} | {d['ndcg4']:>8.4f} | {d['mrr5']:>8.4f} | {d['hit5']:>6.1f}% | {d['recall20']:>8.4f} | {comp['delta_ndcg4']:>+8.4f} | {ci_str:<19} | {comp['p_value']:>7.4f} | {sig_str}")

    print("\n" + "=" * 130)
    print("STEP 5: QUERY PROCESSING ABLATION RESULTS (LEXICAL BM25)")
    print("=" * 130)
    print(f"{'Arm':<32} | {'nDCG@4':<8} | {'MRR@5':<8} | {'Hit@5':<7} | {'Rec@20':<8}")
    print("-" * 130)
    for arm_name, _, _ in arms:
        b = bm25_results[arm_name]
        print(f"{arm_name:<32} | {b['ndcg4']:>8.4f} | {b['mrr5']:>8.4f} | {b['hit5']:>6.1f}% | {b['recall20']:>8.4f}")

    # Serialize Artifact
    out_payload = {
        "benchmark": "Step 5 Query Processing & Technical Acronym Expansion Benchmark",
        "cohort": "QASPER Expanded Split (160 Papers, 487 Queries)",
        "acronym_stats": {
            "total_queries": len(queries),
            "queries_with_acronyms": acronym_hits_count,
            "acronym_hit_rate": acronym_hits_count / len(queries),
            "total_acronym_mentions": total_expanded_terms,
        },
        "dense_e5_results": {k: {m: v for m, v in val.items() if m != "scores_by_paper"} for k, val in dense_results.items()},
        "bm25_results": {k: {m: v for m, v in val.items() if m != "scores_by_paper"} for k, val in bm25_results.items()},
        "dense_hypothesis_tests": dense_comparisons,
    }

    out_file = ARTIFACTS_DIR / "step5_query_processing_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nSaved Step 5 benchmark artifact to: {out_file}")


if __name__ == "__main__":
    run_query_processing_evaluation()
