"""
Phase 6: Multi-Stage Hybrid Retrieval Benchmark on the Full Canonical QASPER Benchmark.
Evaluates Dense Semantic Vector Retrieval (intfloat/e5-small-v2) and Lexical Keyword Retrieval (BM25)
fused via Reciprocal Rank Fusion (RRF k=60) across the entire QASPER dataset (1,585 papers, 5,049 questions).

Research Hypotheses (RQ4):
  H4.1 (Hybrid Superiority): Combining Dense Cosine Similarity and Sparse Lexical BM25 via RRF (k=60)
       statistically significantly improves nDCG@10, nDCG@4, and Recall@20 over both pure dense and pure lexical baselines.
  H4.2 (Hierarchical Small-to-Big Synergy): Hybrid retrieval on child chunks (150 words) successfully expands
       to higher-quality parent sections under the 1,600-token context budget compared to single-mode retrieval.
  H4.3 (Scale Generalizability): The hybrid advantage is robust and statistically verified across all 1,585 papers
       using paper-cluster bootstrap hypothesis testing (B=2,000, seed=42) and Holm-Bonferroni FWER control.

Ablation Arms:
  1. Dense Only: intfloat/e5-small-v2 (exact cosine similarity on FP32 unit-normalized vectors)
  2. BM25 Only: WordPiece BM25 (k1=1.5, b=0.75, 39 canonical stopwords)
  3. Hybrid RRF (k=60): Production default Reciprocal Rank Fusion [1/(60 + rank_dense) + 1/(60 + rank_bm25)]
  4. Hybrid RRF (k=20): Aggressive top-rank Reciprocal Rank Fusion
  5. Hybrid Convex (alpha=0.7): Min-max normalized linear combination (0.7 * Dense + 0.3 * BM25)

Output Artifacts:
  - eval/phases/phase_6_hybrid_retrieval/artifacts/full_qasper_rq4_hybrid_benchmark.json
  - eval/phases/phase_6_hybrid_retrieval/artifacts/FULL_QASPER_RQ4_REPORT.md
"""

import argparse
import gc
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
torch.set_num_threads(4)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

# Path setup
WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent

BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
EVAL_DIR = WORKSPACE_ROOT / "eval"
OFFICIAL_DATA_DIR = EVAL_DIR / "data" / "qasper_official"

PHASE6_DIR = EVAL_DIR / "phases" / "phase_6_hybrid_retrieval"
ARTIFACTS_DIR = PHASE6_DIR / "artifacts"
CACHE_DIR = ARTIFACTS_DIR / "cache"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from apps.documents.services.chunkers import chunk_document_unified, estimate_tokens
from eval_common import (
    STOPWORDS,
    clean_evidence,
    compute_dcg,
    compute_ndcg,
    count_relevant_chunks,
    is_chunk_hit,
    paired_cluster_bootstrap,
    holm_bonferroni_correction,
    tokenize_regex,
)

TOP_K = 20
CONTEXT_BUDGET_TOKENS = 1600
MAX_PARENTS = 5


# -----------------------------------------------------------------------------
# 1. Fast WordPiece BM25 Implementation
# -----------------------------------------------------------------------------
class WordPieceBM25:
    """Fast in-memory WordPiece BM25 index with inverted index and stopword filtering."""

    def __init__(self, chunks: List[Dict[str, Any]], tokenizer):
        self.chunks = chunks
        self.tokenizer = tokenizer
        self.doc_tokens: List[List[str]] = []
        for c in chunks:
            raw_text = c.get("text", "")
            tokens = [t.lower() for t in tokenizer.tokenize(raw_text) if t.lower() not in STOPWORDS]
            self.doc_tokens.append(tokens)

        self.doc_len = [len(t) for t in self.doc_tokens]
        self.avg_dl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.total_docs = len(self.doc_tokens)

        self.df: Dict[str, int] = {}
        self.postings: Dict[str, List[Tuple[int, int]]] = {}

        for doc_id, tokens in enumerate(self.doc_tokens):
            counts: Dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            for t, count in counts.items():
                self.df[t] = self.df.get(t, 0) + 1
                self.postings.setdefault(t, []).append((doc_id, count))

    def score_query(self, query: str, cand_indices: List[int], k1: float = 1.5, b: float = 0.75) -> Dict[int, float]:
        q_tokens = [t.lower() for t in self.tokenizer.tokenize(query) if t.lower() not in STOPWORDS]
        scores: Dict[int, float] = {i: 0.0 for i in cand_indices}
        cand_set = set(cand_indices)
        N = self.total_docs

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


# -----------------------------------------------------------------------------
# 2. Hybrid Fusion Algorithms
# -----------------------------------------------------------------------------
def rrf_fuse(dense_ranked: List[int], bm25_ranked: List[int], k_rrf: int = 60, top_k: int = TOP_K) -> List[int]:
    """Reciprocal Rank Fusion across Dense and BM25 ranked candidate lists."""
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
    if not cand_ids:
        return []
    d_vals = np.array([dense_scores[i] for i in cand_ids])
    b_vals = np.array([bm25_scores.get(i, 0.0) for i in cand_ids])

    # Min-max normalization
    d_min, d_max = d_vals.min(), d_vals.max()
    d_norm = (d_vals - d_min) / max(d_max - d_min, 1e-6) if d_max > d_min else np.zeros_like(d_vals)

    b_min, b_max = b_vals.min(), b_vals.max()
    b_norm = (b_vals - b_min) / max(b_max - b_min, 1e-6) if b_max > b_min else np.zeros_like(b_vals)

    combined = alpha * d_norm + (1.0 - alpha) * b_norm
    ranked_indices = np.argsort(combined)[::-1][:top_k]
    return [cand_ids[i] for i in ranked_indices]


# -----------------------------------------------------------------------------
# 3. Small-to-Big Parent Expansion & Context Packing
# -----------------------------------------------------------------------------
def expand_to_parents(
    ranked_child_indices: List[int],
    chunks: List[Dict[str, Any]],
    budget_tokens: int = CONTEXT_BUDGET_TOKENS,
    max_parents: int = MAX_PARENTS,
) -> List[Dict[str, Any]]:
    """
    Expands top-ranked child chunks to unique parent sections,
    deduplicating sections in ranking order and enforcing the 1,600-token context budget.
    """
    seen_parents: Set[str] = set()
    parent_passages: List[Dict[str, Any]] = []
    accumulated_tokens = 0

    for c_idx in ranked_child_indices:
        c = chunks[c_idx]
        parent_id = c.get("parent_id") or c.get("chunk_id")
        if parent_id in seen_parents:
            continue
        seen_parents.add(parent_id)

        parent_text = c.get("parent_text") or c.get("text", "")
        p_tokens = c.get("parent_tokens") or estimate_tokens(parent_text)

        # Truncate/window parent if exceptionally long (> 800 tokens windowing)
        if p_tokens > 800:
            words = parent_text.split()
            # 400 words ~ 530 tokens around center
            trimmed_text = " ".join(words[:400])
            p_tokens = estimate_tokens(trimmed_text)
            passage_text = trimmed_text
        else:
            passage_text = parent_text

        if accumulated_tokens + p_tokens > budget_tokens and len(parent_passages) > 0:
            break

        parent_passages.append({
            "parent_id": parent_id,
            "paper_arxiv_id": c.get("paper_arxiv_id", ""),
            "section": c.get("section", ""),
            "text": passage_text,
            "tokens": p_tokens,
            "child_rank": len(parent_passages) + 1,
        })
        accumulated_tokens += p_tokens

        if len(parent_passages) >= max_parents:
            break

    return parent_passages


# -----------------------------------------------------------------------------
# 4. Data Loader & Corpus Preparation for Official QASPER
# -----------------------------------------------------------------------------
def load_official_qasper_corpus(
    splits: List[str] = ["train", "dev", "test"],
    strategy: str = "hierarchical",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, List[int]], Dict[str, Dict[str, Any]]]:
    """
    Loads official QASPER v0.3 data files and generates standardized chunks.
    Returns:
      (queries, chunks, paper_chunks_map, paper_meta_map)
    """
    print(f"\n[+] Loading official QASPER splits: {splits}...")
    all_papers: Dict[str, Dict[str, Any]] = {}
    all_queries: List[Dict[str, Any]] = []

    for s in splits:
        split_file = OFFICIAL_DATA_DIR / f"qasper-{s}-v0.3.json"
        if not split_file.exists():
            raise FileNotFoundError(f"Missing official split file: {split_file}")
        with open(split_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"    - Split '{s}': {len(data)} papers")
        for pid, pdata in data.items():
            all_papers[pid] = pdata
            for qa in pdata.get("qas", []):
                # Filter for answerable questions with non-empty text evidence
                text_evidence: List[str] = []
                for ans in qa.get("answers", []):
                    a = ans.get("answer", {})
                    if not a.get("unanswerable", False):
                        ev_raw = a.get("evidence", [])
                        for ev in ev_raw:
                            if not ev.startswith("FLOAT SELECTED") and ev.strip():
                                text_evidence.append(ev.strip())
                if text_evidence:
                    all_queries.append({
                        "query_id": qa.get("question_id", ""),
                        "paper_arxiv_id": pid,
                        "question": qa.get("question", "").strip(),
                        "evidence_list": text_evidence,
                        "verbatim_evidence_quote": text_evidence[0] if text_evidence else "",
                        "split": s,
                    })

    print(f"[+] Total papers loaded: {len(all_papers)}")
    print(f"[+] Total text-evidenced answerable queries: {len(all_queries)}")

    # Build chunks
    print(f"\n[+] Chunking {len(all_papers)} papers using strategy='{strategy}'...")
    chunks: List[Dict[str, Any]] = []
    paper_chunks_map: Dict[str, List[int]] = {}
    paper_meta_map: Dict[str, Dict[str, Any]] = {}

    for pid, pdata in all_papers.items():
        sections = []
        for s_idx, sec in enumerate(pdata.get("full_text", [])):
            s_title = sec.get("section_name") or f"Section {s_idx+1}"
            s_text = "\n\n".join(sec.get("paragraphs", []))
            if s_text.strip():
                sections.append({
                    "title": s_title,
                    "text": s_text,
                    "section_id": f"{pid}_sec_{s_idx}",
                    "page": 1,
                })
        paper_meta_map[pid] = {
            "title": pdata.get("title", ""),
            "sections": sections,
        }

        # Use unified chunking
        if strategy == "hierarchical":
            c_list = chunk_document_unified(sections, strategy="hierarchical", paper_id=pid)
        else:
            c_list = chunk_document_unified(sections, strategy="section_overlap", max_tokens=350, overlap=70, paper_id=pid)

        start_idx = len(chunks)
        for c in c_list:
            c["paper_arxiv_id"] = pid
            chunks.append(c)
        paper_chunks_map[pid] = list(range(start_idx, len(chunks)))

    print(f"[+] Created {len(chunks)} total chunks across {len(all_papers)} papers (avg {len(chunks)/len(all_papers):.1f} chunks/paper).")

    # Filter queries whose papers produced at least 1 chunk
    valid_queries = [q for q in all_queries if len(paper_chunks_map.get(q["paper_arxiv_id"], [])) > 0]
    print(f"[+] Retained {len(valid_queries)} active queries matching chunked papers.")

    return valid_queries, chunks, paper_chunks_map, paper_meta_map


# -----------------------------------------------------------------------------
# 5. Core Evaluation Runner
# -----------------------------------------------------------------------------
def evaluate_full_qasper_rq4(
    split: str = "all",
    strategy: str = "hierarchical",
    tau: float = 0.50,
    k_rrf: int = 60,
    batch_size: int = 64,
    n_bootstraps: int = 2000,
    force_recompute: bool = False,
) -> Dict[str, Any]:
    start_time = time.time()
    splits_to_load = ["train", "dev", "test"] if split == "all" else [split]

    queries, chunks, paper_chunks_map, paper_meta_map = load_official_qasper_corpus(
        splits=splits_to_load,
        strategy=strategy,
    )

    # 1. Embedding Cache Management
    cache_prefix = f"full_qasper_{split}_{strategy}"
    doc_embs_file = CACHE_DIR / f"{cache_prefix}_doc_embs.npy"
    query_embs_file = CACHE_DIR / f"{cache_prefix}_query_embs.npy"

    model_name = "intfloat/e5-small-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if not force_recompute and doc_embs_file.exists() and query_embs_file.exists():
        print(f"\n[+] Loading cached embeddings from {CACHE_DIR.name}/...")
        doc_embs = np.load(doc_embs_file)
        query_embs = np.load(query_embs_file)
        if len(doc_embs) != len(chunks) or len(query_embs) != len(queries):
            print(f"[!] Cache size mismatch (docs: {len(doc_embs)} vs {len(chunks)}, queries: {len(query_embs)} vs {len(queries)}). Recomputing...")
            force_recompute = True
        else:
            print(f"    - Loaded {len(doc_embs)} passage vectors and {len(query_embs)} query vectors.")

    if force_recompute or not (doc_embs_file.exists() and query_embs_file.exists()):
        print(f"\n[+] Computing E5 embeddings using {model_name} on 4 CPU threads (batch_size={batch_size})...")
        t_enc = time.time()
        embedder = SentenceTransformer(model_name)

        doc_texts = ["passage: " + c["text"] for c in chunks]
        doc_embs = embedder.encode(doc_texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True)
        np.save(doc_embs_file, doc_embs)

        query_texts = ["query: " + q["question"] for q in queries]
        query_embs = embedder.encode(query_texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True)
        np.save(query_embs_file, query_embs)

        print(f"[+] Embedding completed in {time.time()-t_enc:.2f}s and cached to {doc_embs_file.name}.")

    # 2. Build BM25 Index
    print(f"\n[+] Building WordPiece BM25 index over {len(chunks)} chunks...")
    t_bm25 = time.time()
    bm25 = WordPieceBM25(chunks, tokenizer)
    print(f"[+] BM25 index built in {time.time()-t_bm25:.2f}s.")

    # 3. Pre-compute Ground-Truth Relevance Counts (R_q)
    print(f"\n[+] Pre-computing ground-truth relevance counts for {len(queries)} queries (tau={tau})...")
    rq_map: Dict[str, int] = {}
    q_idx_map = {q["query_id"]: idx for idx, q in enumerate(queries)}

    for q in queries:
        qid = q["query_id"]
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        p_cands = [chunks[i] for i in paper_chunks_map.get(aid, [])]

        if strategy == "hierarchical":
            # For hierarchical, unique parent sections are the evaluation units
            seen_p: Set[str] = set()
            parent_units: List[Dict[str, Any]] = []
            for c in p_cands:
                pid = c.get("parent_id")
                if pid not in seen_p:
                    seen_p.add(pid)
                    parent_units.append({
                        "paper_arxiv_id": aid,
                        "text": c.get("parent_text") or c.get("text", ""),
                        "section": c.get("section", ""),
                    })
            r_cnt = count_relevant_chunks(parent_units, aid, quote, ev_list, tau=tau)
        else:
            r_cnt = count_relevant_chunks(p_cands, aid, quote, ev_list, tau=tau)
        rq_map[qid] = max(1, r_cnt)  # Floor at 1 to prevent division by zero

    # 4. Define Retrieval Strategies (Frozen Dev-Selected Arms)
    arms = [
        "Dense Only (e5-small-v2)",
        "BM25 Only (WordPiece)",
        f"Hybrid RRF (k={k_rrf}) [Prod]",
        "Hybrid Convex (alpha=0.7)",
    ]

    print(f"\n[+] Executing benchmark across all {len(arms)} locked arms on {len(queries)} queries...")
    results_by_arm: Dict[str, Dict[str, Any]] = {
        arm: {
            "ndcg4": [],
            "ndcg10": [],
            "mrr10": [],
            "recall4": [],
            "recall20": [],
            "hit1": [],
            "hit3": [],
            "hit5": [],
            "scores_by_paper": defaultdict(list),
        }
        for arm in arms
    }

    t_eval = time.time()
    for q_i, q in enumerate(queries):
        if (q_i + 1) % 500 == 0 or q_i == len(queries) - 1:
            print(f"    - Processed {q_i+1}/{len(queries)} queries ({100*(q_i+1)/len(queries):.1f}%)...")

        qid = q["query_id"]
        aid = q["paper_arxiv_id"]
        q_idx = q_idx_map[qid]
        q_vec = query_embs[q_idx]
        total_relevant = rq_map[qid]

        cand_indices = paper_chunks_map[aid]
        if not cand_indices:
            continue

        # Dense Cosine
        cand_vecs = doc_embs[cand_indices]
        dense_sims = np.dot(cand_vecs, q_vec)
        dense_ranked = [cand_indices[i] for i in np.argsort(dense_sims)[::-1]]
        dense_scores = {cand_indices[i]: float(dense_sims[i]) for i in range(len(cand_indices))}

        # BM25 Lexical
        bm25_scores = bm25.score_query(q["question"], cand_indices)
        bm25_ranked = sorted(cand_indices, key=lambda idx: bm25_scores.get(idx, 0.0), reverse=True)

        # Fusions
        rrf_prod_ranked = rrf_fuse(dense_ranked, bm25_ranked, k_rrf=k_rrf, top_k=TOP_K)
        convex_ranked = convex_fuse(dense_scores, bm25_scores, alpha=0.7, top_k=TOP_K)

        arm_rankings = {
            "Dense Only (e5-small-v2)": dense_ranked[:TOP_K],
            "BM25 Only (WordPiece)": bm25_ranked[:TOP_K],
            f"Hybrid RRF (k={k_rrf}) [Prod]": rrf_prod_ranked,
            "Hybrid Convex (alpha=0.7)": convex_ranked,
        }

        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])

        for arm, child_ranks in arm_rankings.items():
            if strategy == "hierarchical":
                # Small-to-Big Parent Expansion under 1,600 token budget
                passages = expand_to_parents(child_ranks, chunks, budget_tokens=CONTEXT_BUDGET_TOKENS, max_parents=MAX_PARENTS)
                rel_scores = [1 if is_chunk_hit(p, aid, quote, ev_list, tau=tau) else 0 for p in passages]
            else:
                rel_scores = [1 if is_chunk_hit(chunks[idx], aid, quote, ev_list, tau=tau) else 0 for idx in child_ranks]

            while len(rel_scores) < TOP_K:
                rel_scores.append(0)

            n4 = compute_ndcg(rel_scores[:4], total_relevant, k=4)
            n10 = compute_ndcg(rel_scores[:10], total_relevant, k=10)

            # MRR@10
            mrr = 0.0
            for r_idx, r_val in enumerate(rel_scores[:10]):
                if r_val > 0:
                    mrr = 1.0 / (r_idx + 1)
                    break

            rec4 = min(1.0, sum(rel_scores[:4]) / total_relevant)
            rec20 = min(1.0, sum(rel_scores[:20]) / total_relevant)

            h1 = 1.0 if any(rel_scores[:1]) else 0.0
            h3 = 1.0 if any(rel_scores[:3]) else 0.0
            h5 = 1.0 if any(rel_scores[:5]) else 0.0

            collector = results_by_arm[arm]
            collector["ndcg4"].append(n4)
            collector["ndcg10"].append(n10)
            collector["mrr10"].append(mrr)
            collector["recall4"].append(rec4)
            collector["recall20"].append(rec20)
            collector["hit1"].append(h1)
            collector["hit3"].append(h3)
            collector["hit5"].append(h5)
            collector["scores_by_paper"][aid].append(n10)

    print(f"[+] All queries evaluated in {time.time()-t_eval:.2f}s.")

    # 5. Compute Paired Paper-Cluster Bootstraps (B=2,000) vs Dense Only and BM25 Only
    print(f"\n[+] Running Paired Paper-Cluster Bootstraps (B={n_bootstraps}, seed=42)...")
    dense_scores_by_paper = results_by_arm["Dense Only (e5-small-v2)"]["scores_by_paper"]
    bm25_scores_by_paper = results_by_arm["BM25 Only (WordPiece)"]["scores_by_paper"]

    stats_vs_dense: Dict[str, Dict[str, Any]] = {}
    stats_vs_bm25: Dict[str, Dict[str, Any]] = {}

    for arm in arms:
        if arm != "Dense Only (e5-small-v2)":
            diff_d, ci_d, p_d = paired_cluster_bootstrap(
                dense_scores_by_paper,
                results_by_arm[arm]["scores_by_paper"],
                n_bootstraps=n_bootstraps,
                seed=42,
            )
            stats_vs_dense[arm] = {"diff": diff_d, "ci": ci_d, "p_raw": p_d}

        if arm != "BM25 Only (WordPiece)":
            diff_b, ci_b, p_b = paired_cluster_bootstrap(
                bm25_scores_by_paper,
                results_by_arm[arm]["scores_by_paper"],
                n_bootstraps=n_bootstraps,
                seed=42,
            )
            stats_vs_bm25[arm] = {"diff": diff_b, "ci": ci_b, "p_raw": p_b}

    # Apply Holm-Bonferroni correction across the 3 planned comparisons vs Dense Only
    candidate_arms = [a for a in arms if a != "Dense Only (e5-small-v2)"]
    raw_p_list = [stats_vs_dense[a]["p_raw"] for a in candidate_arms]
    holm_results = holm_bonferroni_correction(raw_p_list, alpha=0.05)
    for a, h_res in zip(candidate_arms, holm_results):
        stats_vs_dense[a]["p_adj"] = h_res["adj_p"]
        stats_vs_dense[a]["significant"] = h_res["significant"]

    # 6. Aggregate Summary Table
    summary: Dict[str, Any] = {
        "metadata": {
            "benchmark": "RQ4 Multi-Stage Hybrid Retrieval Benchmark",
            "dataset": f"QASPER v0.3 Canonical [{split.upper()}]",
            "total_papers": len(set(q["paper_arxiv_id"] for q in queries)),
            "total_queries": len(queries),
            "total_chunks": len(chunks),
            "chunking_strategy": strategy,
            "containment_tau": tau,
            "k_rrf": k_rrf,
            "context_budget_tokens": CONTEXT_BUDGET_TOKENS,
            "n_bootstraps": n_bootstraps,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": round(time.time() - start_time, 2),
        },
        "arms": {},
    }

    print("\n" + "=" * 130)
    print(f"RQ4 HYBRID RETRIEVAL BENCHMARK RESULTS — QASPER {split.upper()} ({summary['metadata']['total_papers']} Papers / {summary['metadata']['total_queries']} Queries / Strategy={strategy})")
    print("=" * 130)
    print(f"{'Strategy / Arm':<32} {'nDCG@10':>9} {'nDCG@4':>8} {'Recall@20':>10} {'MRR@10':>8} {'Hit@5':>7} {'Delta vs Dense':>16} {'p-raw':>8} {'p-adj':>8}")
    print("-" * 130)

    for arm in arms:
        res = results_by_arm[arm]
        m_ndcg10 = float(np.mean(res["ndcg10"]))
        m_ndcg4 = float(np.mean(res["ndcg4"]))
        m_rec20 = float(np.mean(res["recall20"]))
        m_mrr10 = float(np.mean(res["mrr10"]))
        m_hit5 = float(np.mean(res["hit5"])) * 100

        vs_d = stats_vs_dense.get(arm, {"diff": 0.0, "ci": (0.0, 0.0), "p_raw": 1.0, "p_adj": 1.0})
        delta_str = f"{vs_d['diff']:+.4f} [{vs_d['ci'][0]:+.4f}; {vs_d['ci'][1]:+.4f}]" if arm != "Dense Only (e5-small-v2)" else "Baseline (0.0)"
        p_raw_str = f"{vs_d['p_raw']:.4f}" if arm != "Dense Only (e5-small-v2)" else "—"
        p_adj_str = f"{vs_d.get('p_adj', 1.0):.4f}" if arm != "Dense Only (e5-small-v2)" else "—"

        summary["arms"][arm] = {
            "ndcg10": round(m_ndcg10, 4),
            "ndcg4": round(m_ndcg4, 4),
            "recall20": round(m_rec20, 4),
            "mrr10": round(m_mrr10, 4),
            "hit1": round(float(np.mean(res["hit1"])) * 100, 2),
            "hit3": round(float(np.mean(res["hit3"])) * 100, 2),
            "hit5": round(m_hit5, 2),
            "delta_vs_dense": vs_d["diff"],
            "ci_vs_dense": vs_d["ci"],
            "p_raw_vs_dense": vs_d["p_raw"],
            "p_adj_vs_dense": vs_d.get("p_adj", 1.0) if arm != "Dense Only (e5-small-v2)" else 1.0,
            "significant_vs_dense": vs_d.get("significant", False) if arm != "Dense Only (e5-small-v2)" else False,
            "delta_vs_bm25": stats_vs_bm25.get(arm, {}).get("diff", 0.0),
            "p_raw_vs_bm25": stats_vs_bm25.get(arm, {}).get("p_raw", 1.0),
        }

        print(f"{arm:<32} {m_ndcg10:>9.4f} {m_ndcg4:>8.4f} {m_rec20:>10.4f} {m_mrr10:>8.4f} {m_hit5:>6.1f}% {delta_str:>16} {p_raw_str:>8} {p_adj_str:>8}")

    print("=" * 130)

    # 7. Serialize Artifacts
    output_json = ARTIFACTS_DIR / f"rq4_qasper_{split}_{strategy}_benchmark.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[+] Saved structured benchmark JSON to: {output_json}")

    # Generate Markdown Report
    report_md = ARTIFACTS_DIR / f"RQ4_QASPER_{split.upper()}_{strategy.upper()}_REPORT.md"
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(f"# RQ4 Hybrid Retrieval Benchmark Report\n\n")
        f.write(f"- **Benchmark Scope:** Official QASPER v0.3 `{split.upper()}` Split ({summary['metadata']['total_papers']} papers, {summary['metadata']['total_queries']} queries)\n")
        f.write(f"- **Chunking Architecture:** `{strategy}` (Small-to-Big Parent Expansion under 1,600-token context budget, 5-parent cap)\n")
        f.write(f"- **Evidence Containment Threshold:** $\\tau = {tau}$\n")
        f.write(f"- **Bootstrap Samples:** $B = {n_bootstraps}$ (Paper-cluster level, seed=42)\n")
        f.write(f"- **Multiple Comparisons:** Holm-Bonferroni correction applied across the 3 planned comparisons against Dense Only\n\n")
        f.write(f"| Strategy / Retrieval Arm | nDCG@10 (Primary) | nDCG@4 | Recall@20 | MRR@10 | Hit@5 (%) | $\\Delta$ vs Dense [95% CI] | $p$-raw | $p$-adj (Holm) |\n")
        f.write(f"| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for arm in arms:
            d = summary["arms"][arm]
            ci_s = f"[{d['ci_vs_dense'][0]:+.4f}; {d['ci_vs_dense'][1]:+.4f}]" if arm != "Dense Only (e5-small-v2)" else "—"
            p_raw_s = f"{d['p_raw_vs_dense']:.4f}" if arm != "Dense Only (e5-small-v2)" else "—"
            p_adj_s = f"{d.get('p_adj_vs_dense', 1.0):.4f}" if arm != "Dense Only (e5-small-v2)" else "—"
            f.write(f"| `{arm}` | **{d['ndcg10']:.4f}** | {d['ndcg4']:.4f} | {d['recall20']:.4f} | {d['mrr10']:.4f} | {d['hit5']:.1f}% | {d['delta_vs_dense']:+.4f} {ci_s} | {p_raw_s} | {p_adj_s} |\n")
        f.write("\n")
        f.write("*Note: Metrics are calculated end-to-end after Small-to-Big parent expansion, the 5-parent cap, and the 1,600-token context budget. They evaluate assembled prompt context quality rather than unrestricted candidate retrieval.*\n")
    print(f"[+] Saved publication-ready Markdown report to: {report_md}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RQ4 Multi-Stage Hybrid Retrieval Benchmark on Full QASPER Dataset")
    parser.add_argument("--split", choices=["all", "dev", "test", "train"], default="all", help="Dataset split to evaluate")
    parser.add_argument("--strategy", choices=["hierarchical", "section_overlap"], default="hierarchical", help="Chunking strategy to evaluate")
    parser.add_argument("--tau", type=float, default=0.50, help="Relevance containment threshold")
    parser.add_argument("--k_rrf", type=int, default=60, help="Smoothing constant for Reciprocal Rank Fusion")
    parser.add_argument("--batch_size", type=int, default=64, help="Embedding batch size")
    parser.add_argument("--n_bootstraps", type=int, default=2000, help="Number of paper-cluster bootstrap iterations")
    parser.add_argument("--force_recompute", action="store_true", help="Force recomputation of embeddings")
    args = parser.parse_args()

    evaluate_full_qasper_rq4(
        split=args.split,
        strategy=args.strategy,
        tau=args.tau,
        k_rrf=args.k_rrf,
        batch_size=args.batch_size,
        n_bootstraps=args.n_bootstraps,
        force_recompute=args.force_recompute,
    )
