"""
Evaluation Harness for ResearchQA Full Dataset: Paper-Level Citation Retrieval.

Given a research query from the real realliyifei/ResearchQA HuggingFace dataset,
evaluates whether BM25 / TF-IDF / Hybrid RRF retrieval surfaces the cited papers
from the query's rubric into the top-k candidate set.

Ground-truth: rubric items with citation_metadata (type=Citation).
Corpus: one stub entry per unique cited paper (title + metadata as text).

Metrics:
  - Paper_Recall@k  (k in 1, 5, 10, 20) : fraction of required papers in top-k
  - Full_Coverage@k : ALL required papers appear in top-k
  - Citation_Hit@k  : at least 1 required paper in top-k
  - nDCG@10, MRR@10

Outputs:
  - eval/results/researchqa_full_benchmark_<strategy>_<ts>.json
  - eval/results/researchqa_full_queries_<strategy>_<ts>.jsonl
  - eval/results/RESEARCHQA_FULL_REPORT.md
"""

import argparse
import json
import math
import sys
import time
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

from eval_common.relevance import STOPWORDS, tokenize_regex
from eval_common.stats import compute_hit_at_k, compute_mrr, compute_ndcg, compute_recall


# ---------------------------------------------------------------------------
# Chunking (same sliding-window as other evaluators)
# ---------------------------------------------------------------------------

def chunk_corpus(
    corpus: Dict[str, Dict[str, Any]],
    max_words: int = 120,
    overlap_words: int = 25,
) -> List[Dict[str, Any]]:
    """Chunk all corpus entries into retrievable units."""
    chunks: List[Dict[str, Any]] = []
    step = max(1, max_words - overlap_words)

    for pid, paper in corpus.items():
        texts_to_chunk = []
        abstract = paper.get("abstract", "")
        if abstract:
            texts_to_chunk.append(("Abstract", abstract))
        for sec in paper.get("sections", []):
            heading = sec.get("heading") or sec.get("title") or "Section"
            text = sec.get("text", "")
            if text:
                texts_to_chunk.append((heading, text))

        for section_label, text in texts_to_chunk:
            words = text.split()
            if not words:
                continue
            start = 0
            c_idx = 0
            while start < len(words):
                end = min(start + max_words, len(words))
                chunk_words = words[start:end]
                chunk_text = " ".join(chunk_words)
                chunks.append({
                    "chunk_id": f"{pid}_s{section_label[:15].replace(' ','_')}_c{c_idx:03d}",
                    "paper_id": pid,          # <-- matched against query target_paper_ids
                    "section": section_label,
                    "text": f"[{section_label}]\n{chunk_text}",
                    "raw_text": chunk_text,
                    "token_count": len(chunk_words),
                })
                c_idx += 1
                if end >= len(words):
                    break
                start += step

    return chunks


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------

class BM25Engine:
    def __init__(self, chunks: List[Dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        N = len(chunks)
        self.N = N
        doc_lens = [len(c["text"].split()) for c in chunks]
        self.avg_dl = sum(doc_lens) / max(1, N)
        self.doc_lens = doc_lens

        df: Counter = Counter()
        self.doc_tfs: List[Counter] = []
        for c in chunks:
            tokens = [t for t in tokenize_regex(c["text"]) if t not in STOPWORDS]
            tf = Counter(tokens)
            self.doc_tfs.append(tf)
            for t in tf:
                df[t] += 1

        self.idf = {
            t: math.log(1.0 + (N - cnt + 0.5) / (cnt + 0.5))
            for t, cnt in df.items()
        }

    def score(self, query: str) -> List[Tuple[int, float]]:
        q_tokens = [t for t in tokenize_regex(query) if t not in STOPWORDS]
        results = []
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
# TF-IDF Dense (fallback)
# ---------------------------------------------------------------------------

class TFIDFEngine:
    def __init__(self, chunks: List[Dict[str, Any]]):
        self.chunks = chunks
        N = len(chunks)
        df: Counter = Counter()
        doc_vecs: List[Dict[str, float]] = []

        for c in chunks:
            tokens = [t for t in tokenize_regex(c["text"]) if t not in STOPWORDS]
            tf = Counter(tokens)
            total = max(1, sum(tf.values()))
            tf_norm = {t: v / total for t, v in tf.items()}
            doc_vecs.append(tf_norm)
            for t in tf:
                df[t] += 1

        self.idf = {t: math.log((N + 1) / (cnt + 1)) + 1.0 for t, cnt in df.items()}
        self.tfidf_vecs: List[Dict[str, float]] = []
        self.norms: List[float] = []
        for dv in doc_vecs:
            vec = {t: dv[t] * self.idf.get(t, 1.0) for t in dv}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.tfidf_vecs.append(vec)
            self.norms.append(norm)

    def score(self, query: str) -> List[Tuple[int, float]]:
        q_tokens = [t for t in tokenize_regex(query) if t not in STOPWORDS]
        q_tf = Counter(q_tokens)
        total_q = max(1, sum(q_tf.values()))
        q_tfidf = {t: (q_tf[t] / total_q) * self.idf.get(t, 1.0) for t in q_tf}
        q_norm = math.sqrt(sum(v * v for v in q_tfidf.values())) or 1.0
        results = []
        for i, (vec, norm) in enumerate(zip(self.tfidf_vecs, self.norms)):
            dot = sum(q_tfidf.get(t, 0.0) * vec.get(t, 0.0) for t in q_tfidf)
            results.append((i, dot / (q_norm * norm)))
        return sorted(results, key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# RRF fusion
# ---------------------------------------------------------------------------

def rrf_fuse(
    ranks_a: List[Tuple[int, float]],
    ranks_b: List[Tuple[int, float]],
    k: int = 60,
) -> List[Tuple[int, float]]:
    rrf: Dict[int, float] = {}
    for rank, (idx, _) in enumerate(ranks_a):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)
    for rank, (idx, _) in enumerate(ranks_b):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (k + rank + 1)
    return sorted(rrf.items(), key=lambda x: -x[1])


# ---------------------------------------------------------------------------
# Paper-level metrics
# ---------------------------------------------------------------------------

def paper_metrics(
    ordered_chunks: List[Dict[str, Any]],
    target_paper_ids: List[str],
    ks: List[int] = [1, 5, 10, 20],
) -> Dict[str, Any]:
    """Compute paper-level retrieval metrics from an ordered chunk list."""
    target_set = set(target_paper_ids)
    n_targets = max(1, len(target_set))

    # De-duplicate: first chunk per paper in ranked order
    seen_papers: Dict[str, int] = {}  # paper_id -> rank of first retrieved chunk (1-indexed)
    for rank, chunk in enumerate(ordered_chunks, 1):
        pid = chunk.get("paper_id", "")
        if pid not in seen_papers:
            seen_papers[pid] = rank

    # Relevance binary over unique papers (by first appearance rank)
    max_k = max(ks)
    paper_rank_hits: List[int] = []  # 1 if target, 0 otherwise, indexed by paper discovery order
    discovered_order: List[str] = sorted(seen_papers.keys(), key=lambda p: seen_papers[p])
    for pid in discovered_order:
        paper_rank_hits.append(1 if pid in target_set else 0)

    metrics: Dict[str, Any] = {}
    for k in ks:
        found_at_k = set(p for p in discovered_order[:k] if p in target_set)
        metrics[f"paper_recall@{k}"] = len(found_at_k) / n_targets
        metrics[f"full_coverage@{k}"] = 1.0 if len(found_at_k) == len(target_set) else 0.0
        metrics[f"citation_hit@{k}"] = 1.0 if len(found_at_k) > 0 else 0.0

    # nDCG@10 and MRR@10 over the paper-level ranked list
    metrics["ndcg@10"] = compute_ndcg(paper_rank_hits, total_relevant=n_targets, k=10)
    metrics["mrr@10"] = compute_mrr(paper_rank_hits, k=10)
    return metrics


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def evaluate(
    queries: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    strategy: str,
    split_map: Dict[str, List[str]],
) -> Dict[str, Any]:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    # Build query-id → split lookup
    qid_to_split: Dict[str, str] = {}
    for split_name, qids in split_map.items():
        for qid in qids:
            qid_to_split[qid] = split_name

    # Build retrieval engines
    print(f"  Building {strategy} engine over {len(chunks)} chunks ...")
    t0 = time.time()
    bm25: Optional[BM25Engine] = None
    dense: Optional[TFIDFEngine] = None
    if strategy in ("bm25", "hybrid_rrf"):
        bm25 = BM25Engine(chunks)
    if strategy in ("dense", "hybrid_rrf"):
        dense = TFIDFEngine(chunks)
    print(f"  Index built in {time.time()-t0:.1f}s")

    all_metric_keys = [
        "paper_recall@1", "paper_recall@5", "paper_recall@10", "paper_recall@20",
        "full_coverage@5", "full_coverage@10", "full_coverage@20",
        "citation_hit@1", "citation_hit@5", "citation_hit@10", "citation_hit@20",
        "ndcg@10", "mrr@10",
    ]
    aggregate: Dict[str, List[float]] = {k: [] for k in all_metric_keys}
    split_agg: Dict[str, Dict[str, List[float]]] = {}
    per_query_logs: List[Dict[str, Any]] = []

    print(f"  Evaluating {len(queries)} queries ...")
    for i, q in enumerate(queries):
        if (i + 1) % 100 == 0:
            print(f"  ... {i+1}/{len(queries)}", end="\r")

        question = q["question"]
        target_ids = q.get("target_paper_ids", [])
        if not target_ids:
            continue

        if strategy == "bm25":
            ranked = bm25.score(question)
        elif strategy == "dense":
            ranked = dense.score(question)
        else:
            bm25_ranks = bm25.score(question)
            dense_ranks = dense.score(question)
            ranked = rrf_fuse(bm25_ranks, dense_ranks)

        ordered_chunks = [chunks[idx] for idx, _ in ranked]
        m = paper_metrics(ordered_chunks, target_ids)

        sp = qid_to_split.get(q["id"], "unknown")
        if sp not in split_agg:
            split_agg[sp] = {k: [] for k in all_metric_keys}

        for mk in all_metric_keys:
            val = m.get(mk, 0.0)
            aggregate[mk].append(val)
            split_agg[sp][mk].append(val)

        per_query_logs.append({
            "id": q["id"],
            "question": q["question"][:120],
            "field": q.get("field", ""),
            "split": sp,
            "n_targets": len(target_ids),
            "cited_papers": [p["title"][:60] for p in q.get("cited_papers", [])],
            **m,
        })

    print(f"  Done. {len(per_query_logs)} queries evaluated.     ")

    def mean(lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0

    global_metrics = {f"mean_{k}": round(mean(aggregate[k]), 4) for k in all_metric_keys}
    global_metrics["n_queries"] = len(per_query_logs)

    split_metrics = {
        sp: {f"mean_{k}": round(mean(vals[k]), 4) for k in all_metric_keys}
        for sp, vals in split_agg.items()
    }
    for sp in split_metrics:
        split_metrics[sp]["n_queries"] = len(split_agg[sp][all_metric_keys[0]])

    return {
        "strategy": strategy,
        "timestamp": timestamp,
        "global_metrics": global_metrics,
        "split_metrics": split_metrics,
        "per_query": per_query_logs,
    }


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def write_report(all_results: List[Dict[str, Any]], path: Path) -> None:
    now = datetime.utcnow().isoformat()
    lines = [
        "# ResearchQA Full Dataset — Paper-Level Citation Retrieval Report",
        "",
        f"> **Generated:** `{now} UTC`  ",
        f"> **Dataset:** `realliyifei/ResearchQA` (real HuggingFace data)  ",
        f"> **Task:** Given a research query, retrieve the cited paper(s) from the rubric",
        "",
        "> [!NOTE]",
        "> ResearchQA contains rubric-based evaluation criteria, not verbatim evidence passages.",
        "> Ground-truth = papers cited in rubric items (type=Citation). Corpus = stub entries",
        "> (title + metadata) for each unique cited paper. This evaluates whether lexical/",
        "> semantic matching on paper titles is sufficient to retrieve the right paper given",
        "> the query — a necessary but not sufficient condition for full RAG retrieval.",
        "",
        "---",
        "",
        "## 1. Overall Results",
        "",
        "| Strategy | Paper Recall@5 | Paper Recall@10 | Paper Recall@20 | Full Coverage@10 | Citation Hit@5 | nDCG@10 | MRR@10 |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in all_results:
        gm = r["global_metrics"]
        lines.append(
            f"| `{r['strategy']}` "
            f"| {gm['mean_paper_recall@5']:.4f} "
            f"| {gm['mean_paper_recall@10']:.4f} "
            f"| {gm['mean_paper_recall@20']:.4f} "
            f"| {gm['mean_full_coverage@10']:.4f} "
            f"| {gm['mean_citation_hit@5']:.4f} "
            f"| {gm['mean_ndcg@10']:.4f} "
            f"| {gm['mean_mrr@10']:.4f} |"
        )

    lines.extend(["", "---", "", "## 2. Split Breakdown", ""])
    for r in all_results:
        lines.append(f"### `{r['strategy']}`")
        lines.append("")
        lines.append("| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for sp, sm in r["split_metrics"].items():
            lines.append(
                f"| {sp} | {sm['n_queries']} "
                f"| {sm['mean_paper_recall@5']:.4f} "
                f"| {sm['mean_paper_recall@10']:.4f} "
                f"| {sm['mean_full_coverage@10']:.4f} "
                f"| {sm['mean_citation_hit@5']:.4f} "
                f"| {sm['mean_ndcg@10']:.4f} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Methodology Notes",
        "",
        "- **Corpus limitation:** Only paper title + metadata available (no full text).",
        "  Retrieval is title-matching, not passage retrieval. Results represent an upper-bound",
        "  estimate of what title-level lexical retrieval can achieve.",
        "- **Ground truth:** Rubric items with `type=Citation` and non-null `citation_metadata`.",
        "  Queries with zero citation rubric items are excluded (no retrievable ground truth).",
        "- **BM25:** Okapi BM25 (k₁=1.5, b=0.75) with regex tokenisation.",
        "- **Dense:** TF-IDF cosine similarity (no GPU required).",
        "- **Hybrid RRF:** Reciprocal Rank Fusion of BM25 + TF-IDF (k=60).",
        "",
    ])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Saved report → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate ResearchQA full dataset paper retrieval.")
    parser.add_argument("--strategy", choices=["bm25", "dense", "hybrid_rrf", "all"], default="all")
    parser.add_argument("--queries", type=Path, default=EVAL_PREP_DIR / "researchqa_full_queries.json")
    parser.add_argument("--corpus", type=Path, default=EVAL_PREP_DIR / "researchqa_full_corpus.json")
    parser.add_argument("--split", type=Path, default=EVAL_PREP_DIR / "researchqa_full_split.json")
    parser.add_argument("--output-dir", type=Path, default=EVAL_RESULTS_DIR / "researchqa_full")
    args = parser.parse_args()

    for p, name in [(args.queries, "queries"), (args.corpus, "corpus"), (args.split, "split")]:
        if not p.exists():
            print(f"[ERROR] Missing {name}: {p}")
            print("  → Run `python3 backend/scripts/data_prep/download_researchqa_full.py` first.")
            sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    with open(args.queries, encoding="utf-8") as f:
        queries: List[Dict[str, Any]] = json.load(f)
    with open(args.corpus, encoding="utf-8") as f:
        corpus: Dict[str, Any] = json.load(f)
    with open(args.split, encoding="utf-8") as f:
        split_map: Dict[str, List[str]] = json.load(f)

    chunks = chunk_corpus(corpus)
    print(f"[INFO] {len(queries)} queries | {len(corpus)} corpus papers | {len(chunks)} chunks")

    strategies = ["bm25", "dense", "hybrid_rrf"] if args.strategy == "all" else [args.strategy]
    all_results: List[Dict[str, Any]] = []
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    for strat in strategies:
        print(f"\n{'='*65}")
        print(f"  Strategy: {strat.upper()}")
        print(f"{'='*65}")
        result = evaluate(queries, chunks, strat, split_map)
        all_results.append(result)

        json_path = args.output_dir / f"researchqa_full_benchmark_{strat}_{timestamp}.json"
        jsonl_path = args.output_dir / f"researchqa_full_queries_{strat}_{timestamp}.jsonl"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for log in result["per_query"]:
                f.write(json.dumps(log) + "\n")

        gm = result["global_metrics"]
        print(f"\n  Recall@5={gm['mean_paper_recall@5']:.4f}  Recall@10={gm['mean_paper_recall@10']:.4f}  "
              f"Recall@20={gm['mean_paper_recall@20']:.4f}  FullCov@10={gm['mean_full_coverage@10']:.4f}  "
              f"nDCG@10={gm['mean_ndcg@10']:.4f}  MRR@10={gm['mean_mrr@10']:.4f}")

    report_path = args.output_dir / "RESEARCHQA_FULL_REPORT.md"
    write_report(all_results, report_path)

    combined_path = args.output_dir / f"researchqa_full_all_{timestamp}.json"
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump({"strategies": all_results, "timestamp": timestamp}, f, indent=2)

    print("\n" + "=" * 65)
    print("  RESEARCHQA FULL — PAPER-LEVEL CITATION RETRIEVAL")
    print("=" * 65)
    print(f"  {'Strategy':<14} {'Recall@5':>9} {'Recall@10':>10} {'Recall@20':>10} {'nDCG@10':>9}")
    print("  " + "-" * 55)
    for r in all_results:
        gm = r["global_metrics"]
        print(f"  {r['strategy']:<14} {gm['mean_paper_recall@5']:>9.4f} {gm['mean_paper_recall@10']:>10.4f} "
              f"{gm['mean_paper_recall@20']:>10.4f} {gm['mean_ndcg@10']:>9.4f}")
    print("=" * 65)


if __name__ == "__main__":
    main()
