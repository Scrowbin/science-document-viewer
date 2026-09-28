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


def run_organic_evaluation(
    benchmark_path: str,
    custom_pdf_dir: Optional[str] = None,
    max_tokens: int = 350,
    overlap: int = 70,
) -> Dict[str, Any]:
    """
    Runs organic evaluation by parsing real PDFs and searching over a unified corpus of chunks.
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

    strategies = ["section", "section_token", "section_overlap"]
    results: Dict[str, Any] = {}

    for strat in strategies:
        start_time = time.time()
        print(f"\n[EVAL] Processing strategy: '{strat}' (max_tokens={max_tokens}, overlap={overlap})...")

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
        latencies: List[float] = []
        chunk_token_counts = [c.get("token_count", 0) for c in corpus]

        for q in queries:
            target_aid = q.get("paper_arxiv_id", "")
            target_sec = q.get("target_section", "")
            evidence_kws = q.get("evidence_keywords", [])
            query_str = q.get("question", "")

            # Measure retrieval latency
            q_start = time.time()
            top_retrieved = retrieve_top_k(query_str, corpus, k=5)
            latencies.append((time.time() - q_start) * 1000.0)

            # Evaluate top-k accuracy
            found_rank: Optional[int] = None
            for rank_idx, (score, chunk) in enumerate(top_retrieved):
                if is_chunk_hit(chunk, target_aid, target_sec, evidence_kws):
                    found_rank = rank_idx + 1
                    break

            if found_rank == 1:
                hit_at_1 += 1
            if found_rank is not None and found_rank <= 3:
                hit_at_3 += 1
            if found_rank is not None and found_rank <= 5:
                hit_at_5 += 1

            if found_rank is not None:
                reciprocal_ranks.append(1.0 / found_rank)
            else:
                reciprocal_ranks.append(0.0)

        total_queries = len(queries)
        total_eval_time = time.time() - start_time

        results[strat] = {
            "strategy": strat,
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

    return results


def print_comparison_table(results: Dict[str, Any]) -> None:
    """Prints a formatted ASCII comparison table for the midterm presentation."""
    header = (
        "+--------------------+--------+------------+------------+------------+-------+------------------+--------------+\n"
        "| Strategy           | Chunks | Hit Rate@1 | Hit Rate@3 | Hit Rate@5 |  MRR  | Avg Tokens/Chunk | Latency (ms) |\n"
        "+--------------------+--------+------------+------------+------------+-------+------------------+--------------+"
    )
    print("\n" + "=" * 115)
    print("           SCIENTIFIC DOCUMENT RETRIEVAL (RAG) -- ORGANIC BENCHMARK EVALUATION (REAL PDFs)")
    print("=" * 115)
    print(header)

    labels = {
        "section": "1. Section (Base)   ",
        "section_token": "2. Section + Token  ",
        "section_overlap": "3. Section + Overlap",
    }

    for strat, data in results.items():
        name = labels.get(strat, strat.ljust(20))
        chunks = f"{data['total_corpus_chunks']}".rjust(6)
        hr1 = f"{data['hit_rate_at_1']}%".rjust(10)
        hr3 = f"{data['hit_rate_at_3']}%".rjust(10)
        hr5 = f"{data['hit_rate_at_5']}%".rjust(10)
        mrr = f"{data['mrr']:.3f}".rjust(5)
        tokens = f"{data['avg_chunk_tokens']}".rjust(16)
        lat = f"{data['avg_latency_ms']:.2f} ms".rjust(12)
        print(f"| {name} | {chunks} | {hr1} | {hr3} | {hr5} | {mrr} | {tokens} | {lat} |")

    footer = "+--------------------+--------+------------+------------+------------+-------+------------------+--------------+"
    print(footer)

    # Dynamic conclusion based on real numbers
    sec_mrr = results.get("section", {}).get("mrr", 0)
    tok_mrr = results.get("section_token", {}).get("mrr", 0)
    ov_mrr = results.get("section_overlap", {}).get("mrr", 0)

    print("\nEmpirical Findings from Real PDFs:")
    if ov_mrr >= tok_mrr >= sec_mrr:
        print("  * 'section_overlap' achieved the highest MRR by maintaining boundary context across split sections.")
    elif tok_mrr > sec_mrr:
        print("  * Token boundary limits significantly improve Hit Rate over giant unsplit section blocks.")
    print(f"  * Baseline 'section' produced larger chunks (avg {results['section']['avg_chunk_tokens']} tokens),")
    print(f"    whereas 'section_overlap' produced {results['section_overlap']['total_corpus_chunks']} focused chunks with {results['section_overlap']['avg_chunk_tokens']} tokens.")
    print("=" * 115 + "\n")


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
    )
    print_comparison_table(results)

    # Save to JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[EVAL] Structured evaluation report saved to: {args.output}")


if __name__ == "__main__":
    main()
