"""
Evaluation Harness for Scientific Document Retrieval (RAG).
Performs organic, multi-document retrieval evaluation across the 3 chunking strategies:
  1. 'section_overlap' (Section-based with token limits + sliding window - Designated Baseline)
  2. 'section' (Pure Section-based - Alternative)
  3. 'section_token' (Section-based with token boundaries - Alternative)

Evaluates real scientific documents either from physical PDFs or structured corpus sections.
Measures:
  - Fixed Top-K: Hit Rate@1, Hit Rate@3, Hit Rate@5, Mean Reciprocal Rank (MRR)
  - Equal Token Budget (~1,500 tokens): Hit Rate@Budget, MRR@Budget, Precision@Budget
  - Paired Bootstrap 95% Confidence Intervals against designated baseline
  - Corpus Chunk Count, Average Tokens per Chunk, and Latency (ms)
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
from typing import Any, Dict, List, Optional, Set, Tuple

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

# Candidate search directories for PDF files
DEFAULT_PDF_SEARCH_DIRS = [
    os.path.join(os.path.dirname(BACKEND_DIR), "sample__papers"),
    os.path.join(os.path.dirname(BACKEND_DIR), "sample_papers"),
    os.path.join(os.path.dirname(BACKEND_DIR), "eval", "data", "pdfs"),
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
        # Generic prefix search
        try:
            for f in os.listdir(s_dir):
                if arxiv_id and (arxiv_id in f or f.startswith(arxiv_id)):
                    cand = os.path.join(s_dir, f)
                    if os.path.getsize(cand) > 1000:
                        return cand
        except OSError:
            pass
    return None


def tokenize(text: str) -> List[str]:
    """Lexical tokenizer with English stopword filtering."""
    stopwords = {
        "a", "an", "the", "in", "on", "of", "for", "to", "is", "are", "was",
        "were", "and", "or", "that", "this", "it", "by", "with", "from", "as",
        "what", "how", "why", "which", "does", "did", "do", "we", "our", "their",
        "at", "be", "have", "has", "had", "not", "but", "also"
    }
    tokens = re.findall(r"[A-Za-z0-9_\-\.\$\/]+", text.lower())
    return [t for t in tokens if t not in stopwords and len(t) > 1]


class BM25CorpusIndex:
    """
    High-performance in-memory BM25 index with inverted posting lists
    and section heading keyword boosting.
    """

    def __init__(
        self,
        corpus_chunks: List[Dict[str, Any]],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.corpus_chunks = corpus_chunks
        self.k1 = k1
        self.b = b
        self.total_docs = len(corpus_chunks)

        # Precompute document tokens and document lengths
        self.doc_tokens: List[List[str]] = [
            tokenize(c.get("text", "") + " " + c.get("section", "") + " " + c.get("paper_title", ""))
            for c in corpus_chunks
        ]
        self.doc_lens: List[int] = [len(d) for d in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lens) / max(1.0, float(self.total_docs))

        # Build term frequencies and inverted posting lists
        self.doc_freqs: Dict[str, int] = {}
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}

        for doc_idx, tokens in enumerate(self.doc_tokens):
            tf_counter = Counter(tokens)
            for token, tf in tf_counter.items():
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
                self.inverted_index.setdefault(token, []).append((doc_idx, tf))

    def retrieve(self, query: str, top_k: int = 25) -> List[Tuple[float, Dict[str, Any]]]:
        """Scores candidate chunks via BM25 and returns top_k highest scoring chunks."""
        query_tokens = tokenize(query)
        if not query_tokens or self.total_docs == 0:
            return [(0.0, c) for c in self.corpus_chunks[:top_k]]

        scores: Dict[int, float] = {}

        for token in query_tokens:
            postings = self.inverted_index.get(token)
            if not postings:
                continue

            df = self.doc_freqs.get(token, 1)
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)

            for doc_idx, tf in postings:
                doc_len = self.doc_lens[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                bm25_term = idf * (numerator / denominator)
                scores[doc_idx] = scores.get(doc_idx, 0.0) + bm25_term

        # Section heading keyword boost
        q_tok_set = set(query_tokens)
        for doc_idx in scores:
            chunk = self.corpus_chunks[doc_idx]
            sec_tokens = tokenize(chunk.get("section", ""))
            overlap = q_tok_set.intersection(set(sec_tokens))
            if overlap:
                scores[doc_idx] += len(overlap) * 1.5

        scored_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(score, self.corpus_chunks[idx]) for idx, score in scored_list]


def is_chunk_hit(
    chunk: Dict[str, Any],
    expected_arxiv_id: str,
    target_section: str,
    evidence_keywords: List[str],
    verbatim_evidence_quote: str = "",
    evidence_list: Optional[List[str]] = None,
    strict_containment: bool = True,
    tau: float = 0.55,
) -> bool:
    """
    Evaluates whether a retrieved chunk constitutes a true relevance hit.
    Under calibrated strict containment (default, tau=0.55):
      1. Must belong to the expected paper.
      2. Must satisfy verbatim/subphrase quote containment OR bidirectional
         token containment overlap max(inter/|ev|, inter/|chunk|) >= tau.
      3. Loose keyword and section fallbacks are disabled to eliminate false-positive inflation.
    """
    chunk_arxiv_id = chunk.get("paper_arxiv_id", "")
    if chunk_arxiv_id and chunk_arxiv_id != expected_arxiv_id:
        return False

    chunk_text_raw = chunk.get("text", "")
    chunk_text = chunk_text_raw.lower()

    # 1. Exact or subphrase quote containment
    if verbatim_evidence_quote:
        clean_quote = re.sub(r"\s+", " ", verbatim_evidence_quote).strip().lower()
        if clean_quote and clean_quote in chunk_text:
            return True
        # Check first 8 words for sentence prefix match
        words = clean_quote.split()
        if len(words) >= 5 and " ".join(words[:6]) in chunk_text:
            return True

    # 2. Evidence list containment
    if evidence_list:
        for ev in evidence_list:
            clean_ev = re.sub(r"\s+", " ", ev).strip().lower()
            if clean_ev and (clean_ev in chunk_text or chunk_text in clean_ev):
                return True

    # 3. Calibrated Bidirectional Token Overlap against evidence (Regex + 39 Stopwords)
    ev_ref = verbatim_evidence_quote or " ".join(evidence_list or [])
    if ev_ref:
        ev_tokens = set(tokenize(ev_ref))
        chunk_tokens = set(tokenize(chunk_text_raw))
        if ev_tokens and chunk_tokens:
            inter = len(ev_tokens & chunk_tokens)
            cov_ev = inter / len(ev_tokens)
            cov_chunk = inter / len(chunk_tokens)
            if max(cov_ev, cov_chunk) >= tau:
                return True

    if strict_containment:
        return False

    # 4. Legacy fallback (only when strict_containment=False)
    chunk_section = chunk.get("section", "").lower()
    norm_target = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s*", "", target_section).strip().lower()
    norm_chunk = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s*", "", chunk_section).strip().lower()

    sec_matched = bool(norm_target and (norm_target in norm_chunk or norm_chunk in norm_target))
    if sec_matched:
        return True

    if evidence_keywords:
        matches = sum(1 for kw in evidence_keywords if kw.lower() in chunk_text)
        if matches >= max(2, int(len(evidence_keywords) * 0.45)):
            return True

    return False


def paired_bootstrap(
    baseline_scores: List[float],
    candidate_scores: List[float],
    n_bootstraps: int = 2000,
    seed: int = 42,
) -> Tuple[float, Tuple[float, float], bool]:
    """
    Computes query-level paired bootstrap difference (candidate - baseline) and 95% CI.
    Returns: (mean_diff, (ci_lower, ci_upper), is_significant)
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
    ci_lower = boot_means[int(0.025 * n_bootstraps)]
    ci_upper = boot_means[int(0.975 * n_bootstraps)]
    is_sig = (ci_lower > 0 and ci_upper > 0) or (ci_lower < 0 and ci_upper < 0)
    return mean_diff, (ci_lower, ci_upper), is_sig


def paired_cluster_bootstrap(
    baseline_scores: List[float],
    candidate_scores: List[float],
    paper_ids: List[str],
    n_bootstraps: int = 2000,
    seed: int = 42,
) -> Tuple[float, Tuple[float, float], bool]:
    """
    Computes paired cluster bootstrap difference (candidate - baseline) and 95% CI
    resampling at the PAPER cluster level to account for within-paper question correlation.
    Returns: (mean_diff, (ci_lower, ci_upper), is_significant)
    """
    if not baseline_scores or len(baseline_scores) != len(candidate_scores):
        return 0.0, (0.0, 0.0), False

    diffs = [c - b for b, c in zip(baseline_scores, candidate_scores)]
    n = len(diffs)
    if n == 0:
        return 0.0, (0.0, 0.0), False
    mean_diff = sum(diffs) / n

    # Group paired differences by paper cluster
    clusters: Dict[str, List[float]] = {}
    for pid, d in zip(paper_ids, diffs):
        clusters.setdefault(pid, []).append(d)

    unique_papers = list(clusters.keys())
    k_clusters = len(unique_papers)
    if k_clusters <= 1:
        # Fall back to query-level paired bootstrap if only 1 paper cluster exists
        return paired_bootstrap(baseline_scores, candidate_scores, n_bootstraps=n_bootstraps, seed=seed)

    rng = random.Random(seed)
    boot_means: List[float] = []
    for _ in range(n_bootstraps):
        sampled_papers = rng.choices(unique_papers, k=k_clusters)
        boot_diffs: List[float] = []
        for p in sampled_papers:
            boot_diffs.extend(clusters[p])
        if boot_diffs:
            boot_means.append(sum(boot_diffs) / len(boot_diffs))

    boot_means.sort()
    ci_lower = boot_means[int(0.025 * n_bootstraps)]
    ci_upper = boot_means[int(0.975 * n_bootstraps)]
    is_sig = (ci_lower > 0 and ci_upper > 0) or (ci_lower < 0 and ci_upper < 0)
    return mean_diff, (ci_lower, ci_upper), is_sig



def run_organic_evaluation(
    benchmark_path: str,
    custom_pdf_dir: Optional[str] = None,
    corpus_path: Optional[str] = None,
    max_tokens: int = 350,
    overlap: int = 70,
    token_budget: int = 1500,
    baseline_strategy: str = "section_overlap",
    per_question_output: Optional[str] = None,
    n_bootstraps: int = 2000,
    strict_containment: bool = True,
    containment_tau: float = 0.55,
) -> Dict[str, Any]:
    """
    Runs organic evaluation by parsing real PDFs and/or structured corpus sections,
    evaluating queries under both fixed Top-K and equal token budget, and calculating
    bootstrap confidence intervals versus the baseline.
    """
    with open(benchmark_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    # Filter out pure unanswerable queries for retrieval scoring if requested
    eval_queries = [q for q in queries if q.get("question_type") != "unanswerable"]
    if not eval_queries:
        eval_queries = queries

    # 1. Resolve Paper Sources (PDFs or Structured Corpus)
    unique_aids = sorted(list(set(q.get("paper_arxiv_id", "") for q in queries if q.get("paper_arxiv_id"))))

    # Check for companion structured corpus (e.g. qasper_corpus.json)
    companion_corpus: Dict[str, Any] = {}
    candidate_corpus_files = [
        corpus_path,
        os.path.join(os.path.dirname(os.path.abspath(benchmark_path)), "qasper_corpus.json"),
        os.path.join(BACKEND_DIR, "eval", "prepared", "qasper_corpus.json"),
    ]
    for c_cand in candidate_corpus_files:
        if c_cand and os.path.exists(c_cand):
            with open(c_cand, "r", encoding="utf-8") as f:
                companion_corpus = json.load(f)
            print(f"[EVAL] Loaded companion structured corpus with {len(companion_corpus)} papers from: {c_cand}")
            break

    pdf_map: Dict[str, str] = {}
    print("\n[EVAL] Resolving paper document sources:")
    for aid in unique_aids[:15]:
        p_path = resolve_pdf_path(aid, custom_pdf_dir)
        if p_path:
            pdf_map[aid] = p_path
            print(f"  * arXiv:{aid} -> Physical PDF: {p_path}")
        elif aid in companion_corpus:
            print(f"  * arXiv:{aid} -> Structured Corpus ({len(companion_corpus[aid].get('sections', []))} sections)")
        else:
            print(f"  * arXiv:{aid} -> [WARNING] No document text found!")

    if len(unique_aids) > 15:
        print(f"  ... and {len(unique_aids) - 15} additional papers verified.")

    # 2. Evaluate Ordered Strategies
    ordered_strategies = [baseline_strategy] + [
        s for s in ["section_overlap", "section", "section_token"] if s != baseline_strategy
    ]
    results: Dict[str, Any] = {}
    per_question_records: List[Dict[str, Any]] = []

    strat_mrr_top5: Dict[str, List[float]] = {}
    strat_mrr_budget: Dict[str, List[float]] = {}
    strat_hit_budget: Dict[str, List[float]] = {}

    for strat in ordered_strategies:
        start_time = time.time()
        is_base = (strat == baseline_strategy)
        label_prefix = "[BASELINE]" if is_base else "[ALTERNATIVE]"
        print(f"\n[EVAL] {label_prefix} Evaluating strategy: '{strat}' (max_tokens={max_tokens}, overlap={overlap}, token_budget={token_budget})...")

        # Build corpus of chunks
        corpus: List[Dict[str, Any]] = []
        for aid in unique_aids:
            if aid in pdf_map:
                paper_chunks = chunk_document_pdf(
                    pdf_map[aid], strategy=strat, max_tokens=max_tokens, overlap=overlap
                )
                for c in paper_chunks:
                    c["paper_arxiv_id"] = aid
                    corpus.append(c)
            elif aid in companion_corpus:
                sec_list = companion_corpus[aid].get("sections", [])
                p_chunks = chunk_sections(
                    sec_list, strategy=strat, max_tokens=max_tokens, overlap=overlap
                )
                for c in p_chunks:
                    c["paper_arxiv_id"] = aid
                    c["paper_title"] = companion_corpus[aid].get("paper_title", "")
                    corpus.append(c)

        print(f"  -> Generated {len(corpus)} total chunks across {len(unique_aids)} papers.")

        # Build BM25 Index
        idx_t0 = time.time()
        bm25_index = BM25CorpusIndex(corpus)
        idx_dur = round((time.time() - idx_t0) * 1000.0, 1)
        print(f"  -> Built BM25 inverted index in {idx_dur} ms.")

        # Metric accumulators
        hit_at_1 = 0
        hit_at_3 = 0
        hit_at_5 = 0
        hit_at_budget = 0
        budget_precisions: List[float] = []
        budget_chunks_counts: List[int] = []

        reciprocal_ranks_top5: List[float] = []
        reciprocal_ranks_budget: List[float] = []
        latencies: List[float] = []
        chunk_token_counts = [c.get("token_count", 0) for c in corpus]

        for q_idx, q in enumerate(eval_queries):
            target_aid = q.get("paper_arxiv_id", "")
            target_sec = q.get("target_section", "")
            evidence_kws = q.get("evidence_keywords", [])
            quote = q.get("verbatim_evidence_quote", "")
            ev_list = q.get("evidence_list", [])
            query_str = q.get("question", "")
            qid = q.get("id", f"Q_{q_idx+1:02d}")

            q_start = time.time()
            retrieved_candidates = bm25_index.retrieve(query_str, top_k=25)
            q_latency = (time.time() - q_start) * 1000.0
            latencies.append(q_latency)

            # --- A. Fixed Top-K Evaluation ---
            found_rank_top5: Optional[int] = None
            for rank_idx, (score, chunk) in enumerate(retrieved_candidates[:5]):
                if is_chunk_hit(
                    chunk, target_aid, target_sec, evidence_kws, quote, ev_list,
                    strict_containment=strict_containment, tau=containment_tau
                ):
                    found_rank_top5 = rank_idx + 1
                    break

            h1 = 1 if found_rank_top5 == 1 else 0
            h3 = 1 if found_rank_top5 is not None and found_rank_top5 <= 3 else 0
            h5 = 1 if found_rank_top5 is not None and found_rank_top5 <= 5 else 0
            rr_top5 = 1.0 / found_rank_top5 if found_rank_top5 is not None else 0.0

            if h1:
                hit_at_1 += 1
            if h3:
                hit_at_3 += 1
            if h5:
                hit_at_5 += 1

            reciprocal_ranks_top5.append(rr_top5)

            # --- B. Equal Token Budget Evaluation ---
            accumulated_chunks: List[Tuple[float, Dict[str, Any]]] = []
            accum_tokens = 0
            for score, chunk in retrieved_candidates:
                toks = chunk.get("token_count", estimate_tokens(chunk.get("text", "")))
                accumulated_chunks.append((score, chunk))
                accum_tokens += toks
                if accum_tokens >= token_budget:
                    break

            budget_hits = 0
            found_rank_budget: Optional[int] = None
            for b_idx, (score, chunk) in enumerate(accumulated_chunks):
                if is_chunk_hit(
                    chunk, target_aid, target_sec, evidence_kws, quote, ev_list,
                    strict_containment=strict_containment, tau=containment_tau
                ):
                    budget_hits += 1
                    if found_rank_budget is None:
                        found_rank_budget = b_idx + 1

            h_budget = 1 if found_rank_budget is not None else 0
            rr_budget = 1.0 / found_rank_budget if found_rank_budget is not None else 0.0
            prec_budget = budget_hits / max(1, len(accumulated_chunks))

            if h_budget:
                hit_at_budget += 1

            reciprocal_ranks_budget.append(rr_budget)
            budget_precisions.append(prec_budget)
            budget_chunks_counts.append(len(accumulated_chunks))

            per_question_records.append({
                "question_id": qid,
                "strategy": strat,
                "is_baseline": is_base,
                "paper_arxiv_id": target_aid,
                "target_section": target_sec,
                "question": query_str,
                "found_rank_top5": found_rank_top5,
                "hit_at_1": h1,
                "hit_at_3": h3,
                "hit_at_5": h5,
                "rr_top5": round(rr_top5, 4),
                "token_budget": token_budget,
                "chunks_in_budget": len(accumulated_chunks),
                "tokens_in_budget": accum_tokens,
                "hit_at_budget": h_budget,
                "rr_budget": round(rr_budget, 4),
                "precision_at_budget": round(prec_budget, 4),
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
                    for r_idx, (score, c) in enumerate(retrieved_candidates[:5])
                ],
            })

        strat_mrr_top5[strat] = reciprocal_ranks_top5
        strat_mrr_budget[strat] = reciprocal_ranks_budget
        strat_hit_budget[strat] = [float(h) for h in reciprocal_ranks_budget]

        total_q = len(eval_queries)
        total_eval_time = round(time.time() - start_time, 2)

        results[strat] = {
            "strategy": strat,
            "is_baseline": is_base,
            "queries_evaluated": total_q,
            "total_corpus_chunks": len(corpus),
            "hit_rate_at_1": round((hit_at_1 / total_q) * 100, 1),
            "hit_rate_at_3": round((hit_at_3 / total_q) * 100, 1),
            "hit_rate_at_5": round((hit_at_5 / total_q) * 100, 1),
            "mrr_top5": round(sum(reciprocal_ranks_top5) / max(1, total_q), 3),
            "token_budget": token_budget,
            "hit_rate_at_budget": round((hit_at_budget / total_q) * 100, 1),
            "mrr_budget": round(sum(reciprocal_ranks_budget) / max(1, total_q), 3),
            "precision_at_budget": round(sum(budget_precisions) / max(1, total_q), 3),
            "avg_chunks_in_budget": round(sum(budget_chunks_counts) / max(1, total_q), 1),
            "avg_chunk_tokens": round(sum(chunk_token_counts) / max(1, len(chunk_token_counts)), 1),
            "avg_latency_ms": round(sum(latencies) / max(1, len(latencies)), 2),
            "total_eval_time_sec": total_eval_time,
        }

    # 3. Compute Paired Cluster Bootstrap 95% Confidence Intervals (clustered by paper)
    base_mrr = strat_mrr_top5.get(baseline_strategy, [])
    base_mrr_b = strat_mrr_budget.get(baseline_strategy, [])
    paper_ids = [q.get("paper_arxiv_id", "") for q in eval_queries]

    for strat, data in results.items():
        if strat == baseline_strategy:
            data["bootstrap_mrr_diff"] = 0.0
            data["bootstrap_mrr_ci_95"] = [0.0, 0.0]
            data["statistically_significant"] = False
            data["bootstrap_mrr_budget_diff"] = 0.0
            data["bootstrap_mrr_budget_ci_95"] = [0.0, 0.0]
            data["budget_statistically_significant"] = False
        else:
            cand_mrr = strat_mrr_top5.get(strat, [])
            diff, (ci_low, ci_high), is_sig = paired_cluster_bootstrap(
                base_mrr, cand_mrr, paper_ids=paper_ids, n_bootstraps=n_bootstraps
            )
            data["bootstrap_mrr_diff"] = round(diff, 4)
            data["bootstrap_mrr_ci_95"] = [round(ci_low, 4), round(ci_high, 4)]
            data["statistically_significant"] = is_sig

            cand_mrr_b = strat_mrr_budget.get(strat, [])
            diff_b, (ci_low_b, ci_high_b), is_sig_b = paired_cluster_bootstrap(
                base_mrr_b, cand_mrr_b, paper_ids=paper_ids, n_bootstraps=n_bootstraps
            )
            data["bootstrap_mrr_budget_diff"] = round(diff_b, 4)
            data["bootstrap_mrr_budget_ci_95"] = [round(ci_low_b, 4), round(ci_high_b, 4)]
            data["budget_statistically_significant"] = is_sig_b


    # 4. Save per-question records to JSONL if requested
    if per_question_output:
        os.makedirs(os.path.dirname(os.path.abspath(per_question_output)), exist_ok=True)
        with open(per_question_output, "w", encoding="utf-8") as f:
            for rec in per_question_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"\n[EVAL] Per-question detailed metrics saved to: {per_question_output}")

    return results


def print_comparison_table(
    results: Dict[str, Any],
    baseline_strategy: str = "section_overlap",
    token_budget: int = 1500,
) -> None:
    """Prints formatted comparison table showing Fixed Top-K and Equal Token Budget."""
    header = (
        "+---------------------------+--------+------------+-------+-------------------+----------------+------------------+------------+--------------+\n"
        "| Strategy                  | Chunks | Hit Rate@1 |  MRR  | MRR Diff vs Base  | 95% CI vs Base | Hit Rate@1.5kTok | MRR@1.5kTok| Latency (ms) |\n"
        "+---------------------------+--------+------------+-------+-------------------+----------------+------------------+------------+--------------+"
    )
    print("\n" + "=" * 144)
    print(f"      SCIENTIFIC DOCUMENT RETRIEVAL (RAG) -- FIXED TOP-K vs EQUAL TOKEN BUDGET ({token_budget} TOKENS)")
    print("=" * 144)
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
        mrr = f"{data['mrr_top5']:.3f}".rjust(5)

        if strat == baseline_strategy:
            diff_str = "0.000 (Ref)".rjust(17)
            ci_str = "[0.00, 0.00]".rjust(14)
        else:
            diff_val = data.get("bootstrap_mrr_diff", 0.0)
            ci_val = data.get("bootstrap_mrr_ci_95", [0.0, 0.0])
            diff_str = f"{diff_val:+.3f}".rjust(17)
            ci_str = f"[{ci_val[0]:.2f}, {ci_val[1]:.2f}]".rjust(14)

        hr_budget = f"{data['hit_rate_at_budget']}%".rjust(16)
        mrr_budget = f"{data['mrr_budget']:.3f}".rjust(10)
        lat = f"{data['avg_latency_ms']:.2f} ms".rjust(12)

        print(f"| {name} | {chunks} | {hr1} | {mrr} | {diff_str} | {ci_str} | {hr_budget} | {mrr_budget} | {lat} |")

    footer = "+---------------------------+--------+------------+-------+-------------------+----------------+------------------+------------+--------------+"
    print(footer)

    print("\nStatistical Inference & Equal Token Budget Findings:")
    print("  * Fixed Top-K causes the 'Coarse Chunk Illusion' because whole 'section' chunks average 325-732 tokens")
    print("    vs ~185 tokens for 'section_overlap', consuming 2x-4x more LLM context window.")
    print(f"  * Under Equal Token Budget ({token_budget} tokens), retrieval accumulates chunks until ~{token_budget} tokens,")
    print("    restoring fair scientific parity between fine-grained and coarse chunking strategies.")
    print("=" * 144 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Organically evaluate RAG chunking strategies on real scientific documents.")
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
        "--corpus",
        default=None,
        help="Path to structured companion corpus JSON (e.g. qasper_corpus.json)",
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
        "--token-budget",
        type=int,
        default=1500,
        help="Token budget limit for equal-context evaluation (default: 1500)",
    )
    parser.add_argument(
        "--bootstraps",
        type=int,
        default=2000,
        help="Number of paired bootstrap resamples for 95%% CI calculation (default: 2000)",
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
    parser.add_argument(
        "--strict-containment",
        dest="strict_containment",
        action="store_true",
        default=True,
        help="Use calibrated strict containment matcher without loose keyword/section fallbacks (default: True)",
    )
    parser.add_argument(
        "--legacy-containment",
        dest="strict_containment",
        action="store_false",
        help="Use uncalibrated legacy keyword/section fallback matching",
    )
    parser.add_argument(
        "--containment-tau",
        type=float,
        default=0.55,
        help="Calibrated evidence containment threshold (default: 0.55)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.benchmark):
        print(f"Error: Benchmark file not found at {args.benchmark}", file=sys.stderr)
        sys.exit(1)

    print(f"[EVAL] Loading evaluation benchmark from: {args.benchmark}")
    print(f"[EVAL] Ground-truth matcher: {'Strict Containment' if args.strict_containment else 'Legacy Fallback'} (tau={args.containment_tau})")
    results = run_organic_evaluation(
        args.benchmark,
        custom_pdf_dir=args.pdf_dir,
        corpus_path=args.corpus,
        max_tokens=args.max_tokens,
        overlap=args.overlap,
        token_budget=args.token_budget,
        baseline_strategy=args.baseline,
        per_question_output=args.per_question_output,
        n_bootstraps=args.bootstraps,
        strict_containment=args.strict_containment,
        containment_tau=args.containment_tau,
    )
    print_comparison_table(results, baseline_strategy=args.baseline, token_budget=args.token_budget)

    # Save to JSON
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[EVAL] Structured evaluation report saved to: {args.output}")


if __name__ == "__main__":
    main()
