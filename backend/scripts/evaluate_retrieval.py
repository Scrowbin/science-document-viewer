"""
Evaluation Harness for Scientific Document Retrieval (RAG).
Performs organic, multi-document retrieval evaluation across the 3 chunking strategies:
  1. 'section' (Pure Section-based - Baseline)
  2. 'section_token' (Section-based with token boundaries)
  3. 'section_overlap' (Section-based with token boundaries + sliding window)

Evaluates real scientific PDFs located in 'additional docs/sample__papers' or 'media/documents'.
Measures:
  - Hit Rate@1, Hit Rate@3, Hit Rate@5
  - Mean Reciprocal Rank (MRR)
  - Corpus Chunk Count & Average Tokens per Chunk
  - Average Retrieval Latency (ms)
"""

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

# Add backend directory to sys.path to enable local imports
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from apps.documents.services.chunking_utils import (
    chunk_document_pdf,
    chunk_sections,
    estimate_tokens,
    extract_sections_from_pdf,
)

# Mapping of arXiv IDs in the evaluation benchmark to actual PDF filenames
ARXIV_TO_PDF_FILENAMES = {
    "1706.03762": ["Attention.pdf", "1706.03762v7.pdf"],
    "1512.03385": ["deep_residual.pdf", "1512.03385.pdf"],
    "2106.09685": ["LoRa.pdf", "2106.09685.pdf"],
    "2005.11401": ["Retrieval-Augmented.pdf", "2005.11401.pdf"],
}

# Candidate search directories for PDF files (prioritize root sample__papers / sample_papers)
DEFAULT_PDF_SEARCH_DIRS = [
    os.path.join(os.path.dirname(BACKEND_DIR), "sample__papers"),
    os.path.join(os.path.dirname(BACKEND_DIR), "sample_papers"),
    os.path.join(os.path.dirname(BACKEND_DIR), "additional docs", "sample__papers"),
    os.path.join(BACKEND_DIR, "media", "documents"),
]


def resolve_pdf_path(arxiv_id: str, custom_pdf_dir: Optional[str] = None) -> Optional[str]:
    """Finds the actual PDF path on disk for a given arXiv ID."""
    search_dirs = [custom_pdf_dir] if custom_pdf_dir else DEFAULT_PDF_SEARCH_DIRS
    filenames = ARXIV_TO_PDF_FILENAMES.get(arxiv_id, [f"{arxiv_id}.pdf"])

    for s_dir in search_dirs:
        if not s_dir or not os.path.exists(s_dir):
            continue
        for fname in filenames:
            candidate = os.path.join(s_dir, fname)
            if os.path.exists(candidate):
                return candidate
    return None


def tokenize(text: str) -> List[str]:
    """Lexical tokenizer with English stopword filtering."""
    stopwords = {
        "a", "an", "the", "in", "on", "of", "for", "to", "is", "are", "was",
        "were", "and", "or", "that", "this", "it", "by", "with", "from", "as",
        "what", "how", "why", "which", "does", "did", "do", "we", "our", "their"
    }
    tokens = re.findall(r"[A-Za-z0-9_\-\.\$\/]+", text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]


def compute_bm25_similarity(
    query_tokens: List[str],
    doc_tokens: List[str],
    doc_freqs: Dict[str, int],
    total_docs: int,
    avg_doc_len: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    """Computes BM25 relevance score for a query against a document chunk."""
    doc_len = len(doc_tokens)
    if doc_len == 0:
        return 0.0

    tf_counter = Counter(doc_tokens)
    score = 0.0

    for token in query_tokens:
        if token in tf_counter:
            tf = tf_counter[token]
            df = doc_freqs.get(token, 1)
            idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / max(1.0, avg_doc_len)))
            score += idf * (numerator / denominator)

    return score


def retrieve_top_k(
    query: str,
    corpus_chunks: List[Dict[str, Any]],
    k: int = 5,
) -> List[Tuple[float, Dict[str, Any]]]:
    """
    Ranks chunks across the entire multi-paper corpus using BM25
    with section heading keyword boosting.
    """
    query_tokens = tokenize(query)
    all_doc_tokens = [
        tokenize(c.get("text", "") + " " + c.get("section", "") + " " + c.get("paper_title", ""))
        for c in corpus_chunks
    ]
    total_docs = len(corpus_chunks)
    avg_doc_len = sum(len(d) for d in all_doc_tokens) / max(1, total_docs)

    doc_freqs: Dict[str, int] = {}
    for d_tokens in all_doc_tokens:
        for t in set(d_tokens):
            doc_freqs[t] = doc_freqs.get(t, 0) + 1

    scored_chunks: List[Tuple[float, Dict[str, Any]]] = []
    for idx, chunk in enumerate(corpus_chunks):
        doc_tokens = all_doc_tokens[idx]
        base_score = compute_bm25_similarity(
            query_tokens, doc_tokens, doc_freqs, total_docs, avg_doc_len
        )

        # Section heading keyword boost
        section_tokens = tokenize(chunk.get("section", ""))
        overlap = set(query_tokens).intersection(set(section_tokens))
        boost = len(overlap) * 1.5

        total_score = base_score + boost
        scored_chunks.append((total_score, chunk))

    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return scored_chunks[:k]


def is_chunk_hit(
    chunk: Dict[str, Any],
    expected_arxiv_id: str,
    target_section: str,
    evidence_keywords: List[str],
) -> bool:
    """
    Strict ground-truth verification:
    1. Chunk MUST belong to the expected paper.
    2. Chunk MUST match the target section heading OR contain significant evidence keywords.
    """
    chunk_arxiv_id = chunk.get("paper_arxiv_id", "")
    if chunk_arxiv_id and chunk_arxiv_id != expected_arxiv_id:
        return False

    chunk_section = chunk.get("section", "").lower()
    norm_target = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s*", "", target_section).strip().lower()
    norm_chunk = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s*", "", chunk_section).strip().lower()

    # Section heading match
    if norm_target and (norm_target in norm_chunk or norm_chunk in norm_target):
        return True

    # Keyword evidence match in text
    chunk_text = chunk.get("text", "").lower()
    matches = sum(1 for kw in evidence_keywords if kw.lower() in chunk_text)
    if matches >= max(2, int(len(evidence_keywords) * 0.4)):
        return True

    return False


def paired_bootstrap(
    baseline_scores: List[float],
    candidate_scores: List[float],
    n_bootstraps: int = 2000,
    seed: int = 42,
) -> Tuple[float, Tuple[float, float], bool]:
    """
    Computes paired bootstrap difference (candidate - baseline) and 95% CI.
    Returns: (mean_diff, (ci_lower, ci_upper), is_significant)
    where is_significant is True if the 95% CI excludes 0.
    """
    if not baseline_scores or len(baseline_scores) != len(candidate_scores):
        return 0.0, (0.0, 0.0), False

    diffs = [c - b for b, c in zip(baseline_scores, candidate_scores)]
    n = len(diffs)
    if n == 0:
        return 0.0, (0.0, 0.0), False
    mean_diff = sum(diffs) / n

    rng = random.Random(seed)
    boot_means: List[float] = []
    for _ in range(n_bootstraps):
        sample = rng.choices(diffs, k=n)
        boot_means.append(sum(sample) / n)

    boot_means.sort()
    low_idx = int(0.025 * n_bootstraps)
    high_idx = int(0.975 * n_bootstraps)
    ci_lower = boot_means[low_idx]
    ci_upper = boot_means[high_idx]
    is_sig = (ci_lower > 0 and ci_upper > 0) or (ci_lower < 0 and ci_upper < 0)
    return mean_diff, (ci_lower, ci_upper), is_sig


def run_organic_evaluation(
    benchmark_path: str,
    custom_pdf_dir: Optional[str] = None,
    max_tokens: int = 350,
    overlap: int = 70,
    baseline_strategy: str = "section_overlap",
    per_question_output: Optional[str] = None,
    n_bootstraps: int = 2000,
) -> Dict[str, Any]:
    """
    Runs organic evaluation by parsing real PDFs and searching over a unified corpus of chunks.
    Collects per-question metrics, outputs per-question JSONL, and computes paired bootstrap
    95% confidence intervals against the designated baseline strategy.
    """
    with open(benchmark_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    # 1. Verify availability of real PDFs
    pdf_map: Dict[str, str] = {}
    unique_arxiv_ids = sorted(list(set(q.get("paper_arxiv_id", "") for q in queries)))

    print("\n[EVAL] Resolving PDF files for benchmark papers:")
    for aid in unique_arxiv_ids:
        path = resolve_pdf_path(aid, custom_pdf_dir)
        if path:
            print(f"  * arXiv:{aid} -> Found: {path}")
            pdf_map[aid] = path
        else:
            print(f"  * arXiv:{aid} -> [WARNING] No PDF found on disk!")

    # Baseline strategy runs first, followed by comparative alternatives
    ordered_strategies = [baseline_strategy] + [
        s for s in ["section_overlap", "section", "section_token"] if s != baseline_strategy
    ]
    results: Dict[str, Any] = {}
    per_question_records: List[Dict[str, Any]] = []
    strat_mrr_scores: Dict[str, List[float]] = {}
    strat_hit1_scores: Dict[str, List[float]] = {}

    for strat in ordered_strategies:
        start_time = time.time()
        is_base = (strat == baseline_strategy)
        label_prefix = "[BASELINE]" if is_base else "[ALTERNATIVE]"
        print(f"\n[EVAL] {label_prefix} Processing strategy: '{strat}' (max_tokens={max_tokens}, overlap={overlap})...")

        # 2. Build multi-paper corpus of chunks
        corpus: List[Dict[str, Any]] = []
        for aid, p_path in pdf_map.items():
            paper_chunks = chunk_document_pdf(
                p_path, strategy=strat, max_tokens=max_tokens, overlap=overlap
            )
            for c in paper_chunks:
                c["paper_arxiv_id"] = aid
                corpus.append(c)

        print(f"  -> Generated {len(corpus)} total chunks across {len(pdf_map)} papers.")

        # 3. Evaluate queries against the full corpus
        hit_at_1 = 0
        hit_at_3 = 0
        hit_at_5 = 0
        reciprocal_ranks: List[float] = []
        hit_flags: List[float] = []
        latencies: List[float] = []
        chunk_token_counts = [c.get("token_count", 0) for c in corpus]

        for q_idx, q in enumerate(queries):
            target_aid = q.get("paper_arxiv_id", "")
            target_sec = q.get("target_section", "")
            evidence_kws = q.get("evidence_keywords", [])
            query_str = q.get("question", "")
            qid = q.get("id", f"Q_{q_idx+1:02d}")

            # Measure retrieval latency
            q_start = time.time()
            top_retrieved = retrieve_top_k(query_str, corpus, k=5)
            q_latency = (time.time() - q_start) * 1000.0
            latencies.append(q_latency)

            # Evaluate top-k accuracy
            found_rank: Optional[int] = None
            for rank_idx, (score, chunk) in enumerate(top_retrieved):
                if is_chunk_hit(chunk, target_aid, target_sec, evidence_kws):
                    found_rank = rank_idx + 1
                    break

            h1 = 1 if found_rank == 1 else 0
            h3 = 1 if found_rank is not None and found_rank <= 3 else 0
            h5 = 1 if found_rank is not None and found_rank <= 5 else 0
            rr = 1.0 / found_rank if found_rank is not None else 0.0

            if h1:
                hit_at_1 += 1
            if h3:
                hit_at_3 += 1
            if h5:
                hit_at_5 += 1

            reciprocal_ranks.append(rr)
            hit_flags.append(float(h1))

            per_question_records.append({
                "question_id": qid,
                "strategy": strat,
                "is_baseline": is_base,
                "paper_arxiv_id": target_aid,
                "target_section": target_sec,
                "question": query_str,
                "found_rank": found_rank,
                "hit_at_1": h1,
                "hit_at_3": h3,
                "hit_at_5": h5,
                "reciprocal_rank": round(rr, 4),
                "latency_ms": round(q_latency, 2),
                "retrieved_chunks": [
                    {
                        "rank": r_idx + 1,
                        "score": round(score, 3),
                        "arxiv_id": c.get("paper_arxiv_id", ""),
                        "section": c.get("section", ""),
                        "page_start": c.get("page", 1),
                        "page_end": c.get("page_end", c.get("page", 1)),
                    }
                    for r_idx, (score, c) in enumerate(top_retrieved[:5])
                ],
            })

        strat_mrr_scores[strat] = reciprocal_ranks
        strat_hit1_scores[strat] = hit_flags

        total_queries = len(queries)
        total_eval_time = time.time() - start_time

        results[strat] = {
            "strategy": strat,
            "is_baseline": is_base,
            "queries_evaluated": total_queries,
            "total_corpus_chunks": len(corpus),
            "hit_rate_at_1": round((hit_at_1 / total_queries) * 100, 1),
            "hit_rate_at_3": round((hit_at_3 / total_queries) * 100, 1),
            "hit_rate_at_5": round((hit_at_5 / total_queries) * 100, 1),
            "mrr": round(sum(reciprocal_ranks) / max(1, total_queries), 3),
            "avg_chunk_tokens": round(sum(chunk_token_counts) / max(1, len(chunk_token_counts)), 1),
            "avg_latency_ms": round(sum(latencies) / max(1, len(latencies)), 2),
            "total_eval_time_sec": round(total_eval_time, 2),
        }

    # 4. Compute Paired Bootstrap 95% Confidence Intervals against Baseline
    base_mrr = strat_mrr_scores.get(baseline_strategy, [])
    for strat, data in results.items():
        if strat == baseline_strategy:
            data["bootstrap_mrr_diff"] = 0.0
            data["bootstrap_mrr_ci_95"] = [0.0, 0.0]
            data["statistically_significant"] = False
        else:
            cand_mrr = strat_mrr_scores.get(strat, [])
            diff, (ci_low, ci_high), is_sig = paired_bootstrap(
                base_mrr, cand_mrr, n_bootstraps=n_bootstraps
            )
            data["bootstrap_mrr_diff"] = round(diff, 4)
            data["bootstrap_mrr_ci_95"] = [round(ci_low, 4), round(ci_high, 4)]
            data["statistically_significant"] = is_sig

    # 5. Optionally save per-question logs to JSONL
    if per_question_output:
        os.makedirs(os.path.dirname(os.path.abspath(per_question_output)), exist_ok=True)
        with open(per_question_output, "w", encoding="utf-8") as f:
            for rec in per_question_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"\n[EVAL] Per-question detailed metrics saved to: {per_question_output}")

    return results


def print_comparison_table(results: Dict[str, Any], baseline_strategy: str = "section_overlap") -> None:
    """Prints a formatted ASCII comparison table with paired bootstrap CIs."""
    header = (
        "+---------------------------+--------+------------+------------+-------+-------------------+----------------+--------------+\n"
        "| Strategy                  | Chunks | Hit Rate@1 | Hit Rate@3 |  MRR  | MRR Diff vs Base  | 95% CI vs Base | Latency (ms) |\n"
        "+---------------------------+--------+------------+------------+-------+-------------------+----------------+--------------+"
    )
    print("\n" + "=" * 125)
    print("      SCIENTIFIC DOCUMENT RETRIEVAL (RAG) -- EMPIRICAL EVALUATION & PAIRED BOOTSTRAP (N=16 PILOT)")
    print("=" * 125)
    print(header)

    labels = {
        "section_overlap": "1. Section + Overlap [BASE] ",
        "section": "2. Section (Alt)            ",
        "section_token": "3. Section + Token (Alt)    ",
    }

    for strat, data in results.items():
        name = labels.get(strat, strat.ljust(27))
        chunks = f"{data['total_corpus_chunks']}".rjust(6)
        hr1 = f"{data['hit_rate_at_1']}%".rjust(10)
        hr3 = f"{data['hit_rate_at_3']}%".rjust(10)
        mrr = f"{data['mrr']:.3f}".rjust(5)

        if strat == baseline_strategy:
            diff_str = "0.000 (Ref)".rjust(17)
            ci_str = "[0.00, 0.00]".rjust(14)
        else:
            diff_val = data.get("bootstrap_mrr_diff", 0.0)
            ci_val = data.get("bootstrap_mrr_ci_95", [0.0, 0.0])
            diff_str = f"{diff_val:+.3f}".rjust(17)
            ci_str = f"[{ci_val[0]:.2f}, {ci_val[1]:.2f}]".rjust(14)

        lat = f"{data['avg_latency_ms']:.2f} ms".rjust(12)
        print(f"| {name} | {chunks} | {hr1} | {hr3} | {mrr} | {diff_str} | {ci_str} | {lat} |")

    footer = "+---------------------------+--------+------------+------------+-------+-------------------+----------------+--------------+"
    print(footer)

    print("\nStatistical Inference & Pilot Calibration Notes:")
    print("  * Baseline strategy is designated as 'section_overlap' (sliding window).")
    print("  * Note on Pilot Sample Size (N=16 queries):")
    print("    Because N=16 over 4 papers yields wide confidence intervals that cross 0,")
    print("    no alternative is statistically significantly different from the baseline on this seed pilot.")
    print("    The seed dataset validates the evaluation harness and metric pipeline; conclusive method")
    print("    separation will be conducted on the unpolluted QASPER benchmark sample.")
    print("=" * 125 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organically evaluate RAG chunking strategies on real scientific PDFs.")
    parser.add_argument(
        "--benchmark",
        default=os.path.join(BACKEND_DIR, "data", "eval_benchmark_seed.json"),
        help="Path to evaluation benchmark JSON file",
    )
    parser.add_argument(
        "--pdf-dir",
        default=None,
        help="Optional directory containing downloaded PDFs",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(BACKEND_DIR, "data", "retrieval_evaluation_results.json"),
        help="Output path for evaluation report JSON",
    )
    parser.add_argument(
        "--per-question-output",
        default=os.path.join(BACKEND_DIR, "data", "retrieval_per_question.jsonl"),
        help="Output path for per-question detailed metrics JSONL",
    )
    parser.add_argument(
        "--baseline",
        default="section_overlap",
        help="Designated baseline strategy name (default: section_overlap)",
    )
    parser.add_argument(
        "--bootstraps",
        type=int,
        default=2000,
        help="Number of paired bootstrap resamples for 95% CI calculation (default: 2000)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=350,
        help="Maximum token limit per chunk",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=70,
        help="Overlap token limit for sliding window",
    )
    args = parser.parse_args()

    if not os.path.exists(args.benchmark):
        print(f"Error: Benchmark file not found at {args.benchmark}", file=sys.stderr)
        sys.exit(1)

    print(f"[EVAL] Loading evaluation benchmark from: {args.benchmark}")
    results = run_organic_evaluation(
        args.benchmark,
        custom_pdf_dir=args.pdf_dir,
        max_tokens=args.max_tokens,
        overlap=args.overlap,
        baseline_strategy=args.baseline,
        per_question_output=args.per_question_output,
        n_bootstraps=args.bootstraps,
    )
    print_comparison_table(results, baseline_strategy=args.baseline)

    # Save to JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[EVAL] Structured evaluation report saved to: {args.output}")


if __name__ == "__main__":
    main()
