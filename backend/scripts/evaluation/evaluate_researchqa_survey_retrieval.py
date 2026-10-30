"""
Evaluation Harness for ResearchQA Method A: Survey Section Ground-Truth Retrieval.

Direct drop-in for the QASPER benchmark schema. Given a question grounded in a
specific section of an academic survey paper, evaluates whether the RAG retrieval
engine surfaces the verbatim-evidence-bearing chunk in its top-k candidates.

Uses the identical is_chunk_hit / nDCG / MRR / Recall metric stack as the
existing QASPER evaluators (evaluate_step5_*, evaluate_step6_hybrid_rrf.py).

Metrics:
  - nDCG@4, nDCG@10  : Normalised Discounted Cumulative Gain
  - MRR@5, MRR@10    : Mean Reciprocal Rank
  - Hit@1, Hit@3, Hit@5 : Exact top-k hit rates
  - Recall@4, Recall@20 : Fraction of relevant chunks retrieved
  - Section_Hit@1    : Unique Method A metric - top-1 chunk from correct section

Outputs:
  - eval/results/researchqa_survey_retrieval_benchmark_<timestamp>.json
  - eval/results/RESEARCHQA_SURVEY_RETRIEVAL_REPORT.md
  - eval/results/researchqa_survey_queries_<timestamp>.jsonl  (per-query log)
"""

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
EVAL_RESULTS_DIR = WORKSPACE_ROOT / "eval" / "results"
EVAL_PREP_DIR = WORKSPACE_ROOT / "eval" / "prepared"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from eval_common.relevance import STOPWORDS, is_chunk_hit, tokenize_regex
from eval_common.stats import (
    cluster_bootstrap_ci,
    compute_hit_at_k,
    compute_mrr,
    compute_ndcg,
    compute_recall,
)

# ---------------------------------------------------------------------------
# QASPER comparison baselines (from evaluate_step6_hybrid_rrf.py results)
# ---------------------------------------------------------------------------
QASPER_BASELINES = {
    "bm25":       {"ndcg@4": 0.3812, "ndcg@10": 0.4103, "mrr@5": 0.4521, "recall@20": 0.8930},
    "dense_e5":   {"ndcg@4": 0.4952, "ndcg@10": 0.5213, "mrr@5": 0.5814, "recall@20": 0.9256},
    "hybrid_rrf": {"ndcg@4": 0.5121, "ndcg@10": 0.5384, "mrr@5": 0.5991, "recall@20": 0.9560},
}

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text_sliding(
    text: str,
    paper_arxiv_id: str,
    section: str,
    max_words: int = 120,
    overlap_words: int = 25,
) -> List[Dict[str, Any]]:
    """Chunk section text with a word-based sliding window.

    Chunks carry ``paper_arxiv_id`` so that ``is_chunk_hit`` (which filters on
    this field) works correctly — identical to QASPER chunking convention.
    """
    words = text.split()
    if not words:
        return []
    chunks: List[Dict[str, Any]] = []
    step = max(1, max_words - overlap_words)
    start = 0
    c_idx = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "chunk_id": f"{paper_arxiv_id}_s{section[:20].replace(' ', '_')}_c{c_idx:03d}",
            "paper_arxiv_id": paper_arxiv_id,   # ← required by is_chunk_hit
            "section": section,
            "text": f"[{section}]\n{chunk_text}",
            "raw_text": chunk_text,
            "token_count": len(chunk_words),
        })
        c_idx += 1
        if end >= len(words):
            break
        start += step
    return chunks


def build_chunks(corpus: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build all chunks from corpus.

    Supports both 'heading' (survey corpus) and 'title' (QASPER corpus) as the
    section label field.
    """
    all_chunks: List[Dict[str, Any]] = []
    for paper_id, paper_data in corpus.items():
        # Use paper_arxiv_id from the record if present, else the dict key
        pid = paper_data.get("paper_arxiv_id", paper_id)
        # Abstract
        abstract = paper_data.get("abstract", "")
        if abstract:
            all_chunks.extend(chunk_text_sliding(abstract, pid, "Abstract"))
        # Sections — 'heading' (survey) or 'title' (QASPER)
        for sec in paper_data.get("sections", []):
            heading = sec.get("heading") or sec.get("title") or "Untitled Section"
            text = sec.get("text", "")
            if text:
                all_chunks.extend(chunk_text_sliding(text, pid, heading))
    return all_chunks


def filter_chunks_for_paper(
    all_chunks: List[Dict[str, Any]], paper_arxiv_id: str
) -> List[Dict[str, Any]]:
    """Return only chunks belonging to a specific paper (single-paper retrieval)."""
    return [c for c in all_chunks if c["paper_arxiv_id"] == paper_arxiv_id]


# ---------------------------------------------------------------------------
# Relevance helpers
# ---------------------------------------------------------------------------

def count_relevant_chunks(
    chunks: List[Dict[str, Any]],
    paper_arxiv_id: str,
    verbatim_evidence_quote: str,
    evidence_list: List[str],
    tau: float = 0.55,
) -> int:
    """Count chunks that pass is_chunk_hit — required for nDCG denominator."""
    return sum(
        1
        for c in chunks
        if is_chunk_hit(c, paper_arxiv_id, verbatim_evidence_quote, evidence_list, tau=tau)
    )


# ---------------------------------------------------------------------------
# BM25 Engine (pure Python, no tokenizer dependency)
# ---------------------------------------------------------------------------

class BM25Engine:
    """BM25Okapi over a list of chunk dicts."""

    def __init__(self, chunks: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        N = len(chunks)
        self.N = N
        doc_lens = [len(c["text"].split()) for c in chunks]
        self.avg_dl = sum(doc_lens) / max(1, N)
        self.doc_lens = doc_lens

        df: Dict[str, int] = Counter()
        self.doc_tfs: List[Dict[str, int]] = []
        for c in chunks:
            tokens = [t for t in tokenize_regex(c["text"]) if t not in STOPWORDS]
            tf = Counter(tokens)
            self.doc_tfs.append(tf)
            for t in tf:
                df[t] += 1

        self.idf: Dict[str, float] = {
            t: math.log(1.0 + (N - cnt + 0.5) / (cnt + 0.5))
            for t, cnt in df.items()
        }

    def score(self, query: str) -> List[Tuple[int, float]]:
        q_tokens = [t for t in tokenize_regex(query) if t not in STOPWORDS]
        results: List[Tuple[int, float]] = []
        for idx, (tf, dl) in enumerate(zip(self.doc_tfs, self.doc_lens)):
            s = 0.0
            for t in q_tokens:
                if t not in tf:
                    continue
                idf = self.idf.get(t, 0.0)
                f = tf[t]
                denom = f + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
                s += idf * (f * (self.k1 + 1)) / denom
            results.append((idx, s))
        return sorted(results, key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# Dense Engine (TF-IDF cosine fallback; SentenceTransformer hook)
# ---------------------------------------------------------------------------

class DenseEngine:
    """Cosine-similarity retriever.

    Tries to load a SentenceTransformer for true semantic embeddings; falls back
    to TF-IDF cosine similarity when the library is unavailable.
    """

    def __init__(self, chunks: List[Dict[str, Any]], model_name: str = "intfloat/e5-small-v2"):
        self.chunks = chunks
        self.model_name = model_name
        self.encoder = None
        self.embeddings = None
        self._tfidf_index: Optional[Dict[str, Any]] = None

        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            self.encoder = SentenceTransformer(model_name)
            texts = [c["text"] for c in chunks]
            self.embeddings = self.encoder.encode(texts, batch_size=64, show_progress_bar=False)
            self.np = np
            print(f"[Dense] Using SentenceTransformer: {model_name}")
        except Exception:
            print("[Dense] SentenceTransformer unavailable — falling back to TF-IDF cosine.")
            self._build_tfidf()

    def _build_tfidf(self) -> None:
        """Build inverted TF-IDF index for cosine fallback."""
        df: Counter = Counter()
        doc_vecs: List[Dict[str, float]] = []
        N = len(self.chunks)
        for c in self.chunks:
            tokens = [t for t in tokenize_regex(c["text"]) if t not in STOPWORDS]
            tf = Counter(tokens)
            total = max(1, sum(tf.values()))
            tf_norm = {t: v / total for t, v in tf.items()}
            doc_vecs.append(tf_norm)
            for t in tf:
                df[t] += 1

        idf = {
            t: math.log((N + 1) / (cnt + 1)) + 1.0
            for t, cnt in df.items()
        }
        # Compute TF-IDF vectors and their L2 norms
        tfidf_vecs: List[Dict[str, float]] = []
        norms: List[float] = []
        for tf_norm in doc_vecs:
            vec = {t: tf_norm[t] * idf.get(t, 1.0) for t in tf_norm}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            tfidf_vecs.append(vec)
            norms.append(norm)

        self._tfidf_index = {"vecs": tfidf_vecs, "norms": norms, "idf": idf}

    def _tfidf_score(self, query: str) -> List[Tuple[int, float]]:
        idx = self._tfidf_index
        q_tokens = [t for t in tokenize_regex(query) if t not in STOPWORDS]
        q_tf = Counter(q_tokens)
        total_q = max(1, sum(q_tf.values()))
        q_tfidf = {t: (q_tf[t] / total_q) * idx["idf"].get(t, 1.0) for t in q_tf}
        q_norm = math.sqrt(sum(v * v for v in q_tfidf.values())) or 1.0

        results: List[Tuple[int, float]] = []
        for i, (vec, norm) in enumerate(zip(idx["vecs"], idx["norms"])):
            dot = sum(q_tfidf.get(t, 0.0) * vec.get(t, 0.0) for t in q_tfidf)
            sim = dot / (q_norm * norm)
            results.append((i, sim))
        return sorted(results, key=lambda x: -x[1])

    def score(self, query: str) -> List[Tuple[int, float]]:
        if self.encoder is not None:
            import numpy as np
            q_emb = self.encoder.encode([query])
            sims = (self.embeddings @ q_emb.T).flatten()
            return sorted(enumerate(sims.tolist()), key=lambda x: -x[1])
        return self._tfidf_score(query)


# ---------------------------------------------------------------------------
# Hybrid RRF Fusion
# ---------------------------------------------------------------------------

def rrf_fuse(
    bm25_ranks: List[Tuple[int, float]],
    dense_ranks: List[Tuple[int, float]],
    k: int = 60,
) -> List[Tuple[int, float]]:
    """Reciprocal Rank Fusion over two ranked lists."""
    rrf: Dict[int, float] = {}
    for rank, (idx, _) in enumerate(bm25_ranks):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)
    for rank, (idx, _) in enumerate(dense_ranks):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(rrf.items(), key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# Core evaluation loop
# ---------------------------------------------------------------------------

def evaluate_strategy(
    queries: List[Dict[str, Any]],
    corpus: Dict[str, Dict[str, Any]],
    all_chunks: List[Dict[str, Any]],
    strategy: str,
    dense_model: str,
    tau: float,
    split_map: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, Any]:
    """Run evaluation for one retrieval strategy over all survey queries.

    Each query is evaluated only against chunks from its own paper
    (single-paper retrieval — identical to QASPER evaluation setting).
    """
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    per_query_logs: List[Dict[str, Any]] = []

    # Build per-paper retrieval engines once
    paper_ids = list(corpus.keys())
    paper_chunks: Dict[str, List[Dict[str, Any]]] = {
        pid: filter_chunks_for_paper(all_chunks, pid) for pid in paper_ids
    }

    print(f"\n[INFO] Building retrieval indices for strategy='{strategy}' ...")
    bm25_engines: Dict[str, BM25Engine] = {}
    dense_engines: Dict[str, DenseEngine] = {}

    for pid in paper_ids:
        chunks = paper_chunks[pid]
        if not chunks:
            print(f"  [WARN] No chunks for paper '{pid}'")
            continue
        if strategy in ("bm25", "hybrid_rrf"):
            bm25_engines[pid] = BM25Engine(chunks)
        if strategy in ("dense", "hybrid_rrf"):
            dense_engines[pid] = DenseEngine(chunks, model_name=dense_model)

    # Detect which dense backend was used
    if dense_engines:
        sample_engine = next(iter(dense_engines.values()))
        dense_backend = dense_model if sample_engine.encoder is not None else "tfidf_cosine_fallback"
    else:
        dense_backend = "n/a"

    print(f"[INFO] Evaluating {len(queries)} queries ...")

    # Per-paper split lookup
    paper_split: Dict[str, str] = {}
    if split_map:
        for split_name, pids in split_map.items():
            for pid in pids:
                paper_split[pid] = split_name

    # Aggregate storage
    all_metric_keys = [
        "ndcg@4", "ndcg@10", "mrr@5", "mrr@10",
        "hit@1", "hit@3", "hit@5",
        "recall@4", "recall@20",
        "section_hit@1",
    ]
    aggregate: Dict[str, List[float]] = {k: [] for k in all_metric_keys}
    split_aggregate: Dict[str, Dict[str, List[float]]] = {}

    for q in queries:
        pid = q["paper_arxiv_id"]
        chunks = paper_chunks.get(pid, [])
        if not chunks:
            print(f"  [SKIP] No chunks for paper '{pid}' — query {q['id']} skipped.")
            continue

        # Retrieve ranked list
        if strategy == "bm25":
            engine = bm25_engines.get(pid)
            if engine is None:
                continue
            ranked = engine.score(q["question"])
        elif strategy == "dense":
            engine = dense_engines.get(pid)
            if engine is None:
                continue
            ranked = engine.score(q["question"])
        else:  # hybrid_rrf
            bm25_eng = bm25_engines.get(pid)
            dense_eng = dense_engines.get(pid)
            if bm25_eng is None or dense_eng is None:
                continue
            bm25_ranks = bm25_eng.score(q["question"])
            dense_ranks = dense_eng.score(q["question"])
            ranked = rrf_fuse(bm25_ranks, dense_ranks)

        # Build ordered chunk list
        ordered_chunks = [chunks[idx] for idx, _ in ranked]

        # Relevance judgements (binary)
        verbatim = q.get("verbatim_evidence_quote", "")
        evidence_list = q.get("evidence_list", [])
        relevances = [
            1 if is_chunk_hit(c, pid, verbatim, evidence_list, tau=tau) else 0
            for c in ordered_chunks
        ]

        total_relevant = count_relevant_chunks(chunks, pid, verbatim, evidence_list, tau=tau)
        total_relevant = max(1, total_relevant)  # avoid division by zero

        # Compute metrics
        ndcg4  = compute_ndcg(relevances, total_relevant, k=4)
        ndcg10 = compute_ndcg(relevances, total_relevant, k=10)
        mrr5   = compute_mrr(relevances, k=5)
        mrr10  = compute_mrr(relevances, k=10)
        hit1   = compute_hit_at_k(relevances, k=1)
        hit3   = compute_hit_at_k(relevances, k=3)
        hit5   = compute_hit_at_k(relevances, k=5)
        rec4   = compute_recall(relevances, total_relevant, k=4)
        rec20  = compute_recall(relevances, total_relevant, k=20)

        # Section Hit@1 — unique Method A metric
        target_section = q.get("target_section", "")
        top1_section = ordered_chunks[0]["section"] if ordered_chunks else ""
        section_hit1 = 1.0 if (
            target_section
            and top1_section
            and target_section.lower().strip() in top1_section.lower().strip()
        ) else 0.0

        q_metrics = {
            "ndcg@4": ndcg4,
            "ndcg@10": ndcg10,
            "mrr@5": mrr5,
            "mrr@10": mrr10,
            "hit@1": hit1,
            "hit@3": hit3,
            "hit@5": hit5,
            "recall@4": rec4,
            "recall@20": rec20,
            "section_hit@1": section_hit1,
        }

        # Accumulate per-query log
        per_query_logs.append({
            "id": q["id"],
            "paper_arxiv_id": pid,
            "question": q["question"],
            "target_section": target_section,
            "split": paper_split.get(pid, "unknown"),
            "total_relevant_chunks": total_relevant,
            "top1_section": top1_section,
            "top5_chunks": [
                {"chunk_id": c["chunk_id"], "section": c["section"],
                 "relevant": bool(r), "text_preview": c["raw_text"][:120]}
                for c, r in zip(ordered_chunks[:5], relevances[:5])
            ],
            **q_metrics,
        })

        # Accumulate global
        for k, v in q_metrics.items():
            aggregate[k].append(v)

        # Accumulate by split
        sp = paper_split.get(pid, "unknown")
        if sp not in split_aggregate:
            split_aggregate[sp] = {k: [] for k in all_metric_keys}
        for k, v in q_metrics.items():
            split_aggregate[sp][k].append(v)

    # Mean aggregation
    def mean(lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    global_metrics = {f"mean_{k}": round(mean(aggregate[k]), 4) for k in all_metric_keys}
    global_metrics["n_queries"] = len(per_query_logs)

    # Bootstrap CI (paper-level clustering)
    # cluster_bootstrap_ci expects Dict[paper_id -> List[per_query_scores]]
    paper_ndcg_clusters: Dict[str, List[float]] = {}
    for log in per_query_logs:
        pid = log["paper_arxiv_id"]
        paper_ndcg_clusters.setdefault(pid, []).append(log["ndcg@10"])
    if len(paper_ndcg_clusters) >= 2:
        ci_lo, ci_hi, _ = cluster_bootstrap_ci(paper_ndcg_clusters, n_bootstraps=1000)
        global_metrics["ndcg@10_ci_lo"] = round(ci_lo, 4)
        global_metrics["ndcg@10_ci_hi"] = round(ci_hi, 4)

    # Per-split breakdown
    split_metrics: Dict[str, Dict[str, float]] = {}
    for sp, sp_agg in split_aggregate.items():
        split_metrics[sp] = {f"mean_{k}": round(mean(sp_agg[k]), 4) for k in all_metric_keys}
        split_metrics[sp]["n_queries"] = len(sp_agg[all_metric_keys[0]])

    return {
        "strategy": strategy,
        "dense_backend": dense_backend,
        "tau": tau,
        "timestamp": timestamp,
        "global_metrics": global_metrics,
        "split_metrics": split_metrics,
        "per_query": per_query_logs,
    }


# ---------------------------------------------------------------------------
# Markdown report generator
# ---------------------------------------------------------------------------

def build_markdown_report(
    all_results: List[Dict[str, Any]],
    output_path: Path,
) -> None:
    """Write a human-readable Markdown report comparing all strategies."""
    now = datetime.utcnow().isoformat()
    strategies = [r["strategy"] for r in all_results]

    lines = [
        "# ResearchQA Method A — Survey Section Ground-Truth Retrieval Report",
        "",
        f"> **Generated:** `{now} UTC`  ",
        f"> **Strategies evaluated:** {', '.join(f'`{s}`' for s in strategies)}  ",
        f"> **Benchmark:** `eval/prepared/researchqa_survey_sampled.json`",
        "",
        "---",
        "",
        "## 1. Overview",
        "",
        "Method A treats each ResearchQA survey-paper section as a ground-truth evidence source,",
        "constructing QASPER-schema-identical queries with `verbatim_evidence_quote` + `evidence_list`.",
        "The same `is_chunk_hit` containment check (τ=0.55) and nDCG/MRR/Recall metrics used in the",
        "existing QASPER harness are applied here, making results directly comparable.",
        "",
        "---",
        "",
        "## 2. Main Results — All Strategies",
        "",
    ]

    # Strategy comparison table
    headers = ["Strategy", "nDCG@4", "nDCG@10", "MRR@5", "Hit@5", "Recall@20", "Section Hit@1"]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join([":---"] + [":---:"] * (len(headers) - 1)) + " |")

    for r in all_results:
        gm = r["global_metrics"]
        ci_str = ""
        if "ndcg@10_ci_lo" in gm:
            ci_str = f" *(±{(gm['ndcg@10_ci_hi'] - gm['ndcg@10_ci_lo'])/2:.3f} CI)*"
        lines.append(
            f"| `{r['strategy']}` "
            f"| {gm['mean_ndcg@4']:.4f} "
            f"| {gm['mean_ndcg@10']:.4f}{ci_str} "
            f"| {gm['mean_mrr@5']:.4f} "
            f"| {gm['mean_hit@5']:.4f} "
            f"| {gm['mean_recall@20']:.4f} "
            f"| {gm['mean_section_hit@1']:.4f} |"
        )

    lines.extend([
        "",
        "### 2.1 Comparison vs QASPER Held-Out Baselines",
        "",
        "| Dataset / Method | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 |",
        "| :--- | :---: | :---: | :---: | :---: |",
        f"| QASPER BM25 *(reference)* | {QASPER_BASELINES['bm25']['ndcg@4']:.4f} | {QASPER_BASELINES['bm25']['ndcg@10']:.4f} | {QASPER_BASELINES['bm25']['mrr@5']:.4f} | {QASPER_BASELINES['bm25']['recall@20']:.4f} |",
        f"| QASPER Dense E5 *(reference)* | {QASPER_BASELINES['dense_e5']['ndcg@4']:.4f} | {QASPER_BASELINES['dense_e5']['ndcg@10']:.4f} | {QASPER_BASELINES['dense_e5']['mrr@5']:.4f} | {QASPER_BASELINES['dense_e5']['recall@20']:.4f} |",
        f"| QASPER Hybrid RRF *(reference)* | {QASPER_BASELINES['hybrid_rrf']['ndcg@4']:.4f} | {QASPER_BASELINES['hybrid_rrf']['ndcg@10']:.4f} | {QASPER_BASELINES['hybrid_rrf']['mrr@5']:.4f} | {QASPER_BASELINES['hybrid_rrf']['recall@20']:.4f} |",
    ])

    for r in all_results:
        gm = r["global_metrics"]
        lines.append(
            f"| **ResearchQA Survey `{r['strategy']}`** "
            f"| **{gm['mean_ndcg@4']:.4f}** "
            f"| **{gm['mean_ndcg@10']:.4f}** "
            f"| **{gm['mean_mrr@5']:.4f}** "
            f"| **{gm['mean_recall@20']:.4f}** |"
        )

    lines.extend(["", "---", "", "## 3. Dev / Held-Out Split Breakdown", ""])

    for r in all_results:
        lines.append(f"### Strategy: `{r['strategy']}`")
        lines.append("")
        lines.append("| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for sp, sm in r["split_metrics"].items():
            lines.append(
                f"| {sp} | {sm['n_queries']} "
                f"| {sm['mean_ndcg@4']:.4f} "
                f"| {sm['mean_ndcg@10']:.4f} "
                f"| {sm['mean_mrr@5']:.4f} "
                f"| {sm['mean_recall@20']:.4f} "
                f"| {sm['mean_section_hit@1']:.4f} |"
            )
        lines.append("")

    lines.extend(["---", "", "## 4. Per-Query Detail", ""])

    for r in all_results:
        lines.append(f"### `{r['strategy']}` — Per-Query Results")
        lines.append("")
        lines.append("| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |")
        lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :--- |")
        for pq in r["per_query"]:
            top1 = pq["top1_section"] if pq["top1_section"] else "—"
            hit_emoji = "🟢" if pq["section_hit@1"] else "🔴"
            lines.append(
                f"| `{pq['id']}` "
                f"| `{pq['paper_arxiv_id']}` "
                f"| {pq['target_section'][:35]} "
                f"| {hit_emoji} "
                f"| {pq['ndcg@10']:.4f} "
                f"| {pq['recall@20']:.4f} "
                f"| {top1[:40]} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 5. Methodology Notes",
        "",
        "- **Chunking:** Sliding window (120 words, 25-word overlap) per section.",
        "- **Relevance:** `is_chunk_hit(chunk, paper_arxiv_id, verbatim_evidence_quote,",
        "  evidence_list, τ=0.55)` — containment-based, identical to QASPER harness.",
        "- **Section Hit@1:** Top-1 chunk's `section` heading matches `target_section` from the",
        "  ground-truth annotation (case-insensitive substring match). This is a Method A-specific",
        "  metric that measures coarse-grained retrieval precision at the section level.",
        "- **BM25:** Pure-Python Okapi BM25 (k₁=1.5, b=0.75) with regex tokenisation; no tokenizer",
        "  dependency required.",
        "- **Dense:** SentenceTransformer cosine similarity; falls back to TF-IDF cosine if",
        "  `sentence_transformers` is unavailable.",
        "- **Hybrid RRF:** Reciprocal Rank Fusion of BM25 + Dense ranked lists (k=60).",
        "- **Bootstrap CI:** Paper-level cluster bootstrap (1000 iterations, 95% CI) on nDCG@10.",
        "",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Saved Markdown Report → {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate ResearchQA Method A: Survey Section Ground-Truth Retrieval."
    )
    parser.add_argument(
        "--strategy",
        choices=["bm25", "dense", "hybrid_rrf", "all"],
        default="all",
        help="Retrieval strategy. 'all' runs bm25, dense, hybrid_rrf sequentially.",
    )
    parser.add_argument("--model", default="intfloat/e5-small-v2", help="SentenceTransformer model name.")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=EVAL_PREP_DIR / "researchqa_survey_corpus.json",
    )
    parser.add_argument(
        "--benchmark",
        type=Path,
        default=EVAL_PREP_DIR / "researchqa_survey_sampled.json",
    )
    parser.add_argument(
        "--split",
        type=Path,
        default=EVAL_PREP_DIR / "researchqa_survey_split.json",
    )
    parser.add_argument("--tau", type=float, default=0.55, help="Containment threshold for is_chunk_hit.")
    parser.add_argument("--output-dir", type=Path, default=EVAL_RESULTS_DIR)
    args = parser.parse_args()

    # Validate inputs
    for p, name in [
        (args.corpus, "survey corpus"),
        (args.benchmark, "survey benchmark"),
    ]:
        if not p.exists():
            print(f"[ERROR] Missing {name}: {p}")
            print("  → Run `python3 backend/scripts/data_prep/prepare_researchqa_survey.py` first.")
            sys.exit(1)
    if args.split and not args.split.exists():
        print(f"[WARN] Split file not found: {args.split} — split breakdown will be skipped.")
        args.split = None

    if args.split and not args.split.exists():
        print(f"[WARN] Split file not found: {args.split} — split breakdown will be skipped.")
        args.split = None

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.corpus, encoding="utf-8") as f:
        corpus: Dict[str, Any] = json.load(f)
    with open(args.benchmark, encoding="utf-8") as f:
        queries: List[Dict[str, Any]] = json.load(f)

    # Load and normalise split map
    split_map: Dict[str, List[str]] = {}
    if args.split and args.split.exists():
        with open(args.split, encoding="utf-8") as f:
            raw_split: Dict[str, Any] = json.load(f)
        if "dev" in raw_split and isinstance(raw_split["dev"], list):
            split_map = {"dev": raw_split["dev"], "held_out": raw_split.get("held_out", [])}
        elif "dev_papers" in raw_split:
            split_map = {"dev": raw_split["dev_papers"], "held_out": raw_split.get("held_out_papers", [])}
        else:
            split_map = {"all": list(corpus.keys())}

    # Build all chunks once
    all_chunks = build_chunks(corpus)
    print(f"[INFO] Ingested {len(corpus)} survey papers → {len(all_chunks)} total chunks.")
    print(f"[INFO] Loaded {len(queries)} benchmark queries.")

    strategies = ["bm25", "dense", "hybrid_rrf"] if args.strategy == "all" else [args.strategy]
    all_results: List[Dict[str, Any]] = []
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    for strat in strategies:
        print(f"\n{'='*70}")
        print(f"  Strategy: {strat.upper()}")
        print(f"{'='*70}")
        result = evaluate_strategy(
            queries=queries,
            corpus=corpus,
            all_chunks=all_chunks,
            strategy=strat,
            dense_model=args.model,
            tau=args.tau,
            split_map=split_map,
        )
        all_results.append(result)

        # Per-strategy JSON
        json_path = args.output_dir / f"researchqa_survey_retrieval_benchmark_{strat}_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"[OK] Saved JSON → {json_path}")

        # Per-strategy JSONL query log
        jsonl_path = args.output_dir / f"researchqa_survey_queries_{strat}_{timestamp}.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for log in result["per_query"]:
                f.write(json.dumps(log) + "\n")
        print(f"[OK] Saved JSONL query log → {jsonl_path}")

        # Console summary
        gm = result["global_metrics"]
        print(f"\n  nDCG@4={gm['mean_ndcg@4']:.4f}  nDCG@10={gm['mean_ndcg@10']:.4f}  "
              f"MRR@5={gm['mean_mrr@5']:.4f}  Hit@5={gm['mean_hit@5']:.4f}  "
              f"Recall@20={gm['mean_recall@20']:.4f}  SectionHit@1={gm['mean_section_hit@1']:.4f}")

    # Combined Markdown report
    md_path = args.output_dir / "RESEARCHQA_SURVEY_RETRIEVAL_REPORT.md"
    build_markdown_report(all_results, md_path)

    # Combined JSON summary
    combined_json_path = args.output_dir / f"researchqa_survey_retrieval_all_{timestamp}.json"
    with open(combined_json_path, "w", encoding="utf-8") as f:
        json.dump({"strategies": all_results, "timestamp": timestamp}, f, indent=2)
    print(f"[OK] Saved combined JSON → {combined_json_path}")

    # Final comparison table on console
    print("\n" + "=" * 70)
    print("  RESEARCHQA METHOD A — SURVEY SECTION RETRIEVAL BENCHMARK")
    print("=" * 70)
    print(f"  {'Strategy':<14} {'nDCG@4':>8} {'nDCG@10':>8} {'MRR@5':>8} {'Recall@20':>10} {'SecHit@1':>10}")
    print("  " + "-" * 62)
    for r in all_results:
        gm = r["global_metrics"]
        print(f"  {r['strategy']:<14} {gm['mean_ndcg@4']:>8.4f} {gm['mean_ndcg@10']:>8.4f} "
              f"{gm['mean_mrr@5']:>8.4f} {gm['mean_recall@20']:>10.4f} "
              f"{gm['mean_section_hit@1']:>10.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
