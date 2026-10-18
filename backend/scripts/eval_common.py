"""
Canonical shared evaluation utilities for the RAG pipeline benchmark.
All evaluation scripts MUST import from this module to ensure identical
tokenization, relevance labeling, metric computation, and statistical testing.

Fixes applied (2026-10-15 Audit Remediation):
  Fix 1: Global IDCG based on total relevant chunks R_q, not local top-k.
  Fix 2: Canonical 39-stopword set from evaluate_retrieval.py.
  Fix 3: Strict evidence containment with chunk-length guard; FLOAT stripping.
  Fix 5a: Corrected two-sided Monte Carlo p-value bound.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# =============================================================================
# Fix 2: Canonical 39-Stopword Set (from evaluate_retrieval.py)
# =============================================================================
STOPWORDS = {
    "a", "an", "the", "in", "on", "of", "for", "to", "is", "are", "was",
    "were", "and", "or", "that", "this", "it", "by", "with", "from", "as",
    "what", "how", "why", "which", "does", "did", "do", "we", "our", "their",
    "at", "be", "have", "has", "had", "not", "but", "also"
}


def tokenize_regex(text: str) -> List[str]:
    """Canonical lexical tokenizer with 39 English stopwords and min-length 2."""
    tokens = re.findall(r"[A-Za-z0-9_\-\.\$\/]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


# =============================================================================
# Fix 3: FLOAT Evidence Stripping
# =============================================================================
def clean_evidence(
    verbatim_evidence_quote: str,
    evidence_list: Optional[List[str]],
) -> Tuple[str, List[str]]:
    """
    Strip FLOAT SELECTED markers from evidence spans.
    Returns (cleaned_quote, cleaned_evidence_list).
    """
    cleaned_quote = ""
    if verbatim_evidence_quote and not verbatim_evidence_quote.strip().upper().startswith("FLOAT SELECTED"):
        cleaned_quote = verbatim_evidence_quote

    cleaned_list = []
    if evidence_list:
        for ev in evidence_list:
            if ev and not ev.strip().upper().startswith("FLOAT SELECTED"):
                cleaned_list.append(ev)

    return cleaned_quote, cleaned_list


# =============================================================================
# Fix 3: Strict Evidence Containment (Pre-Registered Formula)
# =============================================================================
def is_chunk_hit(
    chunk: Dict[str, Any],
    expected_arxiv_id: str,
    verbatim_evidence_quote: str = "",
    evidence_list: Optional[List[str]] = None,
    tau: float = 0.55,
) -> bool:
    """
    Evaluates whether a retrieved chunk constitutes a true relevance hit
    using the pre-registered calibrated Evidence Containment rule.

    Formula: cov_ev >= tau  OR  (|C_tok| >= 20  AND  cov_chunk >= tau  AND  cov_ev >= 0.20)

    All heuristic fallbacks (6-word prefix, reverse substring, keyword match,
    section-title match) are permanently excised.
    """
    # Paper-ID gate
    chunk_arxiv_id = chunk.get("paper_arxiv_id", "")
    if chunk_arxiv_id and chunk_arxiv_id != expected_arxiv_id:
        return False

    chunk_text_raw = chunk.get("text", "")
    chunk_text_lower = chunk_text_raw.lower()

    # Clean evidence (strip FLOAT SELECTED markers)
    clean_quote, clean_list = clean_evidence(verbatim_evidence_quote, evidence_list)

    # Collect all valid evidence spans to evaluate
    evidence_spans: List[str] = []
    if clean_list:
        evidence_spans.extend(clean_list)
    elif clean_quote:
        # Only use verbatim_evidence_quote if evidence_list is empty/invalid
        evidence_spans.append(clean_quote)

    if not evidence_spans:
        return False

    # Evaluate each evidence span independently
    for ev_span in evidence_spans:
        clean_ev = re.sub(r"\s+", " ", ev_span).strip().lower()
        if not clean_ev:
            continue

        # Exact substring containment (evidence fully inside chunk)
        if clean_ev in chunk_text_lower:
            return True

        # Token-level containment with guards
        ev_tokens = set(tokenize_regex(ev_span))
        chunk_tokens = set(tokenize_regex(chunk_text_raw))

        if not ev_tokens or not chunk_tokens:
            continue

        inter = len(ev_tokens & chunk_tokens)
        cov_ev = inter / len(ev_tokens)
        cov_chunk = inter / len(chunk_tokens)

        # Pre-registered formula:
        # cov_ev >= tau  OR  (|C_tok| >= 20  AND  cov_chunk >= tau  AND  cov_ev >= 0.20)
        if cov_ev >= tau:
            return True
        if len(chunk_tokens) >= 20 and cov_chunk >= tau and cov_ev >= 0.20:
            return True

    return False


def count_relevant_chunks(
    chunks: List[Dict[str, Any]],
    paper_arxiv_id: str,
    verbatim_evidence_quote: str = "",
    evidence_list: Optional[List[str]] = None,
    tau: float = 0.55,
) -> int:
    """
    Pre-compute R_q: total number of relevant chunks in the candidate pool
    for a given query, used to compute the global IDCG.
    """
    count = 0
    for c in chunks:
        if is_chunk_hit(c, paper_arxiv_id, verbatim_evidence_quote, evidence_list, tau=tau):
            count += 1
    return count


# =============================================================================
# Fix 1: Global IDCG Metric Computation
# =============================================================================
def compute_dcg(relevances: List[int], k: int = 4) -> float:
    """Compute Discounted Cumulative Gain at position k."""
    dcg = 0.0
    for idx, rel in enumerate(relevances[:k]):
        if rel > 0:
            dcg += rel / np.log2(idx + 2)
    return dcg


def compute_ndcg(relevances: List[int], total_relevant: int, k: int = 4) -> float:
    """
    Compute nDCG@k using the GLOBAL ideal DCG based on total_relevant (R_q),
    not just the relevance labels of the retrieved results.

    IDCG@k = sum_{i=0}^{min(R_q, k)-1} 1/log2(i+2)
    """
    if total_relevant == 0:
        return 0.0
    dcg = compute_dcg(relevances, k=k)
    ideal_k = min(total_relevant, k)
    idcg = sum(1.0 / np.log2(idx + 2) for idx in range(ideal_k))
    return dcg / idcg if idcg > 0.0 else 0.0


# =============================================================================
# Fix 5a: Corrected Paired Cluster Bootstrap
# =============================================================================
def paired_cluster_bootstrap(
    paper_scores_base: Dict[str, List[float]],
    paper_scores_cand: Dict[str, List[float]],
    n_bootstraps: int = 2000,
    seed: int = 42,
    estimand: str = "query",
) -> Tuple[float, Tuple[float, float], float]:
    """
    Computes paired cluster bootstrap difference (candidate - baseline) and 95% CI.
    Resamples at the paper cluster level (B=2000).

    Args:
        paper_scores_base: Mapping from paper_id to list of query scores for baseline.
        paper_scores_cand: Mapping from paper_id to list of query scores for candidate.
        n_bootstraps: Number of cluster bootstrap iterations.
        seed: Random seed for reproducibility.
        estimand: 'query' (default; query-weighted, pooling queries across sampled papers)
                  or 'paper' (paper-weighted, averaging queries within each paper first).

    Returns: (mean_diff, (ci_lower, ci_upper), p_value)

    P-value uses the standard finite-sample Monte Carlo bound:
      p = min(1.0, 2 * (r + 1) / (B + 1))
    where r is the number of bootstrap resamples with mean_diff on the opposite
    side of zero from the observed mean_diff.
    Confidence intervals are computed using np.percentile with symmetric 2.5% and 97.5% cutoffs.
    """
    rng = np.random.default_rng(seed)
    paper_keys = sorted(list(paper_scores_base.keys()))
    K = len(paper_keys)
    if K == 0:
        return 0.0, (0.0, 0.0), 1.0

    # Observed mean difference
    if estimand == "paper":
        paper_diffs_actual = [
            float(np.mean(paper_scores_cand[p])) - float(np.mean(paper_scores_base[p]))
            for p in paper_keys
            if len(paper_scores_base[p]) > 0
        ]
        mean_diff = float(np.mean(paper_diffs_actual)) if paper_diffs_actual else 0.0
    else:
        all_diffs_actual = []
        for p in paper_keys:
            all_diffs_actual.extend(
                np.array(paper_scores_cand[p]) - np.array(paper_scores_base[p])
            )
        mean_diff = float(np.mean(all_diffs_actual)) if all_diffs_actual else 0.0

    # Precompute per-paper diffs for fast paper-weighted bootstrap
    if estimand == "paper":
        paper_means_map = {
            p: float(np.mean(paper_scores_cand[p])) - float(np.mean(paper_scores_base[p]))
            for p in paper_keys
        }

    # Bootstrap resampling
    boot_diffs = []
    for _ in range(n_bootstraps):
        sampled_papers = rng.choice(paper_keys, size=K, replace=True)
        if estimand == "paper":
            boot_diffs.append(float(np.mean([paper_means_map[p] for p in sampled_papers])))
        else:
            resampled_diffs = []
            for p in sampled_papers:
                diffs_p = np.array(paper_scores_cand[p]) - np.array(paper_scores_base[p])
                resampled_diffs.extend(diffs_p)
            boot_diffs.append(float(np.mean(resampled_diffs)))

    ci_lower = float(np.percentile(boot_diffs, 2.5))
    ci_upper = float(np.percentile(boot_diffs, 97.5))

    # Two-sided p-value with corrected Monte Carlo bound
    if mean_diff >= 0:
        r = sum(1 for d in boot_diffs if d <= 0)
    else:
        r = sum(1 for d in boot_diffs if d >= 0)
    p_val = min(1.0, 2.0 * (r + 1) / (n_bootstraps + 1))

    return mean_diff, (ci_lower, ci_upper), p_val
