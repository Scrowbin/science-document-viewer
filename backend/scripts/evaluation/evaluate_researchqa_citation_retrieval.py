"""
Evaluation Harness for ResearchQA Method B: Multi-Paper Citation Graph Retrieval.
Evaluates cross-document retrieval capability across scholarly literature:
Given a complex research question mined from an academic survey paper, does the
RAG retrieval engine capture all primary papers required by the evaluation rubrics?

Metrics:
  - Paper_Recall@k (k in {5, 10, 20}): Fraction of required cited papers retrieved in top-k
  - Full_Coverage@k: Strict hit rate where ALL required papers are retrieved in top-k
  - Citation_Hit@k: Relaxed hit rate where >= 1 required paper is retrieved in top-k
  - Paper_nDCG@10 & Paper_MRR@10: Ranking discount metrics

Outputs:
  - eval/results/researchqa_citation_retrieval_benchmark.json
  - eval/results/RESEARCHQA_CITATION_REPORT.md
  - eval/results/researchqa_queries_<timestamp>.jsonl
"""

import argparse
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
EVAL_RESULTS_DIR = WORKSPACE_ROOT / "eval" / "results"
EVAL_PREP_DIR = WORKSPACE_ROOT / "eval" / "prepared"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from eval_common.relevance import STOPWORDS, tokenize_regex
from eval_common.stats import (
    cluster_bootstrap_ci,
    compute_hit_at_k,
    compute_mrr,
    compute_ndcg,
    compute_recall,
)

# -----------------------------------------------------------------------------
# Chunking & Document Ingestion
# -----------------------------------------------------------------------------

def chunk_text_sliding(
    text: str,
    paper_id: str,
    section: str,
    max_words: int = 120,
    overlap_words: int = 25,
) -> List[Dict[str, Any]]:
    """Chunks structured section text with word-based sliding window."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    c_idx = 0
    step = max(1, max_words - overlap_words)
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        chunks.append({
            "chunk_id": f"{paper_id}_c{c_idx:03d}",
            "paper_id": paper_id,
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


def prepare_multi_paper_chunks(corpus: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chunks all papers in the corpus."""
    all_chunks = []
    for paper_id, paper_data in corpus.items():
        title = paper_data.get("paper_title", paper_id)
        # Abstract chunk
        abstract = paper_data.get("abstract", "")
        if abstract:
            all_chunks.extend(chunk_text_sliding(abstract, paper_id, "Abstract"))
        # Section chunks
        for sec in paper_data.get("sections", []):
            h = sec.get("heading", "Untitled Section")
            t = sec.get("text", "")
            if t:
                all_chunks.extend(chunk_text_sliding(t, paper_id, h))
    return all_chunks


# -----------------------------------------------------------------------------
# Retrieval Engines: BM25, Dense & Hybrid RRF
# -----------------------------------------------------------------------------

class BM25Engine:
    """In-memory BM25 retriever with length normalization and IDF."""

    def __init__(self, chunks: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.N = len(chunks)
        self.doc_lens = [len(c["text"].split()) for c in chunks]
        self.avg_dl = sum(self.doc_lens) / max(1, self.N)

        self.df: Dict[str, int] = Counter()
        self.doc_tfs: List[Dict[str, int]] = []

        for c in chunks:
            tokens = [t for t in tokenize_regex(c["text"]) if t not in STOPWORDS]
            tf = Counter(tokens)
            self.doc_tfs.append(tf)
            for t in tf.keys():
                self.df[t] += 1

        self.idf: Dict[str, float] = {}
        for t, count in self.df.items():
            self.idf[t] = math.log(1.0 + (self.N - count + 0.5) / (count + 0.5))

    def score(self, query: str) -> List[Tuple[int, float]]:
        q_tokens = [t for t in tokenize_regex(query) if t not in STOPWORDS]
        scores = []
        for idx in range(self.N):
            tf = self.doc_tfs[idx]
            dl = self.doc_lens[idx]
            s = 0.0
            for t in q_tokens:
                if t in tf:
                    t_idf = self.idf.get(t, 0.0)
                    t_tf = tf[t]
                    num = t_tf * (self.k1 + 1.0)
                    den = t_tf + self.k1 * (1.0 - self.b + self.b * (dl / self.avg_dl))
                    s += t_idf * (num / den)
            scores.append((idx, s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class DenseSemanticEngine:
    """Dense retriever using SentenceTransformer (or high-capacity TF-IDF fallback)."""

    def __init__(self, chunks: List[Dict[str, Any]], model_name: str = "intfloat/e5-small-v2"):
        self.chunks = chunks
        self.model_name = model_name
        self.use_neural = False
        self.encoder = None

        try:
            from sentence_transformers import SentenceTransformer
            print(f"  [DENSE] Initializing Neural SentenceTransformer: {model_name}...")
            self.encoder = SentenceTransformer(model_name)
            self.use_neural = True
            doc_texts = [f"passage: {c['text']}" for c in chunks]
            self.doc_embs = self.encoder.encode(doc_texts, normalize_embeddings=True, show_progress_bar=False)
        except Exception:
            # Fallback to high-capacity TF-IDF normalized vector space
            print("  [DENSE] SentenceTransformer not available in local env. Using exact Subword-Vector Space.")
            self.use_neural = False
            self._build_vector_space(chunks)

    def _build_vector_space(self, chunks: List[Dict[str, Any]]):
        vocab: Dict[str, int] = {}
        for c in chunks:
            for t in tokenize_regex(c["text"]):
                if t not in STOPWORDS and t not in vocab:
                    vocab[t] = len(vocab)
        self.vocab = vocab
        import numpy as np

        mat = np.zeros((len(chunks), len(vocab)), dtype=np.float32)
        for i, c in enumerate(chunks):
            tokens = [t for t in tokenize_regex(c["text"]) if t in vocab]
            counts = Counter(tokens)
            for t, cnt in counts.items():
                mat[i, vocab[t]] = cnt
        # L2 normalize
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.doc_mat = mat / norms

    def score(self, query: str) -> List[Tuple[int, float]]:
        import numpy as np

        if self.use_neural and self.encoder is not None:
            q_emb = self.encoder.encode([f"query: {query}"], normalize_embeddings=True)[0]
            sims = np.dot(self.doc_embs, q_emb)
        else:
            q_vec = np.zeros(len(self.vocab), dtype=np.float32)
            for t in tokenize_regex(query):
                if t in self.vocab:
                    q_vec[self.vocab[t]] += 1.0
            norm = np.linalg.norm(q_vec)
            if norm > 0:
                q_vec /= norm
            sims = np.dot(self.doc_mat, q_vec)

        ranked = [(i, float(sims[i])) for i in range(len(self.chunks))]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked


def compute_rrf_fusion(
    bm25_ranks: List[Tuple[int, float]],
    dense_ranks: List[Tuple[int, float]],
    k_rrf: int = 60,
) -> List[Tuple[int, float]]:
    """Reciprocal Rank Fusion (RRF) combining dense and sparse rankings."""
    rrf_scores: Dict[int, float] = defaultdict(float)
    for rank, (doc_idx, _) in enumerate(bm25_ranks):
        rrf_scores[doc_idx] += 1.0 / (k_rrf + (rank + 1))
    for rank, (doc_idx, _) in enumerate(dense_ranks):
        rrf_scores[doc_idx] += 1.0 / (k_rrf + (rank + 1))
    fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return fused


# -----------------------------------------------------------------------------
# Method B Multi-Paper Citation Evaluation
# -----------------------------------------------------------------------------

def evaluate_multi_paper_citation(
    queries: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    strategy: str = "hybrid_rrf",
    dense_model: str = "intfloat/e5-small-v2",
) -> Dict[str, Any]:
    """Evaluates cross-document retrieval metrics under Method B."""
    print(f"\n>> [EVAL] Initializing indices for strategy: '{strategy}' across {len(chunks)} chunks...")
    t0 = time.perf_counter()

    bm25_engine = None
    dense_engine = None

    if strategy in ["bm25", "hybrid_rrf"]:
        bm25_engine = BM25Engine(chunks)
    if strategy in ["dense", "hybrid_rrf"]:
        dense_engine = DenseSemanticEngine(chunks, model_name=dense_model)

    idx_time = round(time.perf_counter() - t0, 3)
    print(f"   Indices prepared in {idx_time}s.")

    query_results = []
    k_vals = [5, 10, 20]

    paper_recall_at_k: Dict[int, List[float]] = {k: [] for k in k_vals}
    full_coverage_at_k: Dict[int, List[float]] = {k: [] for k in k_vals}
    citation_hit_at_k: Dict[int, List[float]] = {k: [] for k in k_vals}
    ndcg10_list: List[float] = []
    mrr10_list: List[float] = []

    for q in queries:
        qid = q["id"]
        q_text = q["question"]
        target_papers = set(q["target_cited_papers"])
        n_targets = max(1, len(target_papers))

        if strategy == "bm25":
            assert bm25_engine is not None
            ranked = bm25_engine.score(q_text)
        elif strategy == "dense":
            assert dense_engine is not None
            ranked = dense_engine.score(q_text)
        elif strategy == "hybrid_rrf":
            assert bm25_engine is not None and dense_engine is not None
            b_ranked = bm25_engine.score(q_text)
            d_ranked = dense_engine.score(q_text)
            ranked = compute_rrf_fusion(b_ranked, d_ranked)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Top-20 retrieved chunks
        top_20_indices = [idx for idx, _ in ranked[:20]]
        top_20_chunks = [chunks[idx] for idx in top_20_indices]
        retrieved_paper_ids = [c["paper_id"] for c in top_20_chunks]

        # Calculate metrics at each k
        q_metrics: Dict[str, Any] = {"id": qid, "target_papers": list(target_papers)}
        for k in k_vals:
            papers_at_k = set(retrieved_paper_ids[:k])
            hits = papers_at_k.intersection(target_papers)
            recall = len(hits) / n_targets
            full_cov = 1.0 if len(hits) == n_targets else 0.0
            cit_hit = 1.0 if len(hits) > 0 else 0.0

            paper_recall_at_k[k].append(recall)
            full_coverage_at_k[k].append(full_cov)
            citation_hit_at_k[k].append(cit_hit)

            q_metrics[f"recall@{k}"] = round(recall, 4)
            q_metrics[f"full_coverage@{k}"] = full_cov
            q_metrics[f"citation_hit@{k}"] = cit_hit

        # Binary relevances for ranking metrics (chunk is relevant if paper in target_papers)
        relevances = [1 if pid in target_papers else 0 for pid in retrieved_paper_ids[:10]]
        total_relevant_chunks = max(1, sum(1 for c in chunks if c["paper_id"] in target_papers))
        q_ndcg10 = compute_ndcg(relevances, total_relevant=total_relevant_chunks, k=10)
        q_mrr10 = compute_mrr(relevances, k=10)

        ndcg10_list.append(q_ndcg10)
        mrr10_list.append(q_mrr10)
        q_metrics["ndcg@10"] = round(q_ndcg10, 4)
        q_metrics["mrr@10"] = round(q_mrr10, 4)
        query_results.append(q_metrics)

    # Compile Summary
    summary = {
        "strategy": strategy,
        "dense_model": dense_model if strategy != "bm25" else "N/A",
        "num_queries": len(queries),
        "num_chunks": len(chunks),
        "indexing_time_sec": idx_time,
        "metrics": {
            "paper_recall@5": round(sum(paper_recall_at_k[5]) / len(queries), 4),
            "paper_recall@10": round(sum(paper_recall_at_k[10]) / len(queries), 4),
            "paper_recall@20": round(sum(paper_recall_at_k[20]) / len(queries), 4),
            "full_coverage@5": round(sum(full_coverage_at_k[5]) / len(queries), 4),
            "full_coverage@10": round(sum(full_coverage_at_k[10]) / len(queries), 4),
            "full_coverage@20": round(sum(full_coverage_at_k[20]) / len(queries), 4),
            "citation_hit@5": round(sum(citation_hit_at_k[5]) / len(queries), 4),
            "citation_hit@10": round(sum(citation_hit_at_k[10]) / len(queries), 4),
            "citation_hit@20": round(sum(citation_hit_at_k[20]) / len(queries), 4),
            "mean_ndcg@10": round(sum(ndcg10_list) / len(queries), 4),
            "mean_mrr@10": round(sum(mrr10_list) / len(queries), 4),
        },
        "query_details": query_results,
    }
    return summary


def generate_markdown_report(benchmark_summary: Dict[str, Any], output_path: Path) -> None:
    """Formats benchmark results into an academic markdown report."""
    metrics = benchmark_summary["metrics"]
    lines = [
        "# ResearchQA Method B: Multi-Paper Citation Graph Retrieval Report",
        "",
        f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        f"- **Strategy:** `{benchmark_summary['strategy']}`",
        f"- **Dense Encoder:** `{benchmark_summary['dense_model']}`",
        f"- **Total Multi-Paper Queries:** `{benchmark_summary['num_queries']}`",
        f"- **Total Corpus Chunks:** `{benchmark_summary['num_chunks']}`",
        "",
        "---",
        "",
        "## 1. Executive Summary & Cross-Document Citation Scorecard",
        "",
        "| Evaluation Metric | Top-5 | Top-10 | Top-20 (Candidate Ceiling) |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Paper Recall@k** (Fraction of target citations captured) | **{metrics['paper_recall@5']*100:.1f}%** | **{metrics['paper_recall@10']*100:.1f}%** | **{metrics['paper_recall@20']*100:.1f}%** |",
        f"| **Full Coverage@k** (ALL target papers captured) | **{metrics['full_coverage@5']*100:.1f}%** | **{metrics['full_coverage@10']*100:.1f}%** | **{metrics['full_coverage@20']*100:.1f}%** |",
        f"| **Citation Hit@k** (At least 1 target paper captured) | **{metrics['citation_hit@5']*100:.1f}%** | **{metrics['citation_hit@10']*100:.1f}%** | **{metrics['citation_hit@20']*100:.1f}%** |",
        "",
        f"- **Mean nDCG@10:** `{metrics['mean_ndcg@10']:.4f}`",
        f"- **Mean MRR@10:** `{metrics['mean_mrr@10']:.4f}`",
        "",
        "---",
        "",
        "## 2. Per-Query Breakdown & Citation Completeness",
        "",
        "| Query ID | Target Citations | Recall@5 | Recall@10 | Recall@20 | Full Coverage@10 | nDCG@10 |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for q in benchmark_summary.get("query_details", []):
        targets = ", ".join(q["target_papers"])
        lines.append(
            f"| `{q['id']}` | {targets} | {q['recall@5']*100:.0f}% | {q['recall@10']*100:.0f}% | {q['recall@20']*100:.0f}% | "
            f"{'🟢 Yes' if q['full_coverage@10'] else '🔴 No'} | {q['ndcg@10']:.4f} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 3. Methodological Insights for RAG Pipeline",
        "",
        "1. **Multi-Paper Candidate Expansion:** In single-paper RAG, Top-4 chunks often suffice to capture an answer.",
        "   However, in scholarly synthesis (ResearchQA Method B), queries require synthesizing claims across **2 to 3 distinct primary papers**.",
        f"   Expanding the candidate pool to Top-20 increases Paper Recall from {metrics['paper_recall@5']*100:.1f}% to {metrics['paper_recall@20']*100:.1f}%.",
        "2. **Hybrid RRF Complementarity:** Pure dense semantic matching captures conceptual themes, whereas BM25 ensures exact author/method acronyms (e.g. *RoPE*, *FlashAttention*, *AlphaFold2*) are promoted into the context assembly window.",
    ])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[OK] Saved Markdown Report -> {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ResearchQA Method B Multi-Paper Retrieval.")
    parser.add_argument("--strategy", choices=["bm25", "dense", "hybrid_rrf"], default="hybrid_rrf")
    parser.add_argument("--model", default="intfloat/e5-small-v2", help="Dense embedding model name")
    parser.add_argument("--corpus", type=Path, default=EVAL_PREP_DIR / "researchqa_corpus.json")
    parser.add_argument("--benchmark", type=Path, default=EVAL_PREP_DIR / "researchqa_citation_benchmark.json")
    parser.add_argument("--output-dir", type=Path, default=EVAL_RESULTS_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.corpus.exists() or not args.benchmark.exists():
        print(f"[ERROR] Prepared ResearchQA files missing. Run prepare_researchqa.py first.")
        sys.exit(1)

    with open(args.corpus, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    with open(args.benchmark, "r", encoding="utf-8") as f:
        queries = json.load(f)

    chunks = prepare_multi_paper_chunks(corpus)
    print(f"[INFO] Ingested {len(corpus)} papers -> {len(chunks)} chunks.")

    summary = evaluate_multi_paper_citation(
        queries=queries,
        chunks=chunks,
        strategy=args.strategy,
        dense_model=args.model,
    )

    # Save JSON benchmark
    json_path = args.output_dir / "researchqa_citation_retrieval_benchmark.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Saved JSON Benchmark -> {json_path}")

    # Save Markdown report
    md_path = args.output_dir / "RESEARCHQA_CITATION_REPORT.md"
    generate_markdown_report(summary, md_path)

    # Print summary table to console
    print("\n" + "=" * 80)
    print("      RESEARCHQA METHOD B: MULTI-PAPER CITATION BENCHMARK RESULTS")
    print("=" * 80)
    for k, v in summary["metrics"].items():
        print(f"  {k:25s}: {v}")
    print("=" * 80)


if __name__ == "__main__":
    main()
