"""
Canonical Statistical Evaluation & Hypothesis Testing Module.
Shared across RQ1, RQ2, and RQ3 benchmarks.

Provides:
  - Metric computation: compute_dcg, compute_ndcg, compute_mrr, compute_recall, compute_hit_at_k
  - Clustered bootstrap 95% CI (Paper-cluster resampling, B=2000, seed=42)
  - Paired cluster bootstrap difference & two-sided p-value vs baseline
  - Multiple comparison corrections (Holm-Bonferroni and Bonferroni)
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np


def compute_dcg(relevances: List[int], k: int = 10) -> float:
    """Compute Discounted Cumulative Gain at position k."""
    dcg = 0.0
    for idx, rel in enumerate(relevances[:k]):
        if rel > 0:
            dcg += float(rel) / np.log2(idx + 2)
    return float(dcg)


def compute_ndcg(relevances: List[int], total_relevant: int, k: int = 10) -> float:
    """
    Compute Normalized Discounted Cumulative Gain at rank k using GLOBAL ideal DCG (IDCG).
    Global IDCG is based on total_relevant (R_q) in the paper's candidate pool,
    preventing score inflation when the candidate pool contains fewer than k items.
    """
    if total_relevant <= 0:
        return 0.0
    dcg = compute_dcg(relevances, k=k)
    ideal_k = min(total_relevant, k)
    idcg = sum(1.0 / np.log2(idx + 2) for idx in range(ideal_k))
    return float(dcg / idcg) if idcg > 0.0 else 0.0


def compute_mrr(relevances: List[int], k: int = 10) -> float:
    """
    Compute Mean Reciprocal Rank at position k.
    Returns 1.0 / rank of first relevant item in top-k, or 0.0 if none found.
    """
    for idx, rel in enumerate(relevances[:k]):
        if rel > 0:
            return float(1.0 / (idx + 1))
    return 0.0


def compute_recall(relevances: List[int], total_relevant: int, k: int = 20) -> float:
    """
    Compute Recall at position k (fraction of relevant chunks retrieved in top-k).
    """
    if total_relevant <= 0:
        return 0.0
    hits = sum(1 for r in relevances[:k] if r > 0)
    return float(hits / total_relevant)


def compute_hit_at_k(relevances: List[int], k: int = 5) -> int:
    """
    Compute Hit@k indicator (1 if at least one relevant item in top-k, else 0).
    """
    return 1 if any(r > 0 for r in relevances[:k]) else 0


def cluster_bootstrap_ci(
    paper_scores: Dict[str, List[float]],
    n_bootstraps: int = 2000,
    seed: int = 42,
    alpha: float = 0.05,
) -> Tuple[float, float, float]:
    """
    Computes paper-cluster bootstrap mean and (1 - alpha) confidence interval.
    Resamples paper clusters with replacement (B=2000).

    Args:
        paper_scores: Mapping from paper_id -> list of query scores.
        n_bootstraps: Number of bootstrap resamples (default: 2000).
        seed: Random seed for reproducibility (default: 42).
        alpha: Significance level (default: 0.05 for 95% CI).

    Returns:
        (observed_mean, ci_lower, ci_upper)
    """
    paper_keys = sorted(list(paper_scores.keys()))
    if not paper_keys:
        return 0.0, 0.0, 0.0

    all_scores = [s for p in paper_keys for s in paper_scores[p]]
    if not all_scores:
        return 0.0, 0.0, 0.0
    observed_mean = float(np.mean(all_scores))

    rng = np.random.default_rng(seed)
    K = len(paper_keys)
    boot_means = []

    for _ in range(n_bootstraps):
        sampled_papers = rng.choice(paper_keys, size=K, replace=True)
        resampled_scores = [s for p in sampled_papers for s in paper_scores[p]]
        if resampled_scores:
            boot_means.append(float(np.mean(resampled_scores)))

    if not boot_means:
        return observed_mean, observed_mean, observed_mean

    ci_lower = float(np.percentile(boot_means, (alpha / 2.0) * 100))
    ci_upper = float(np.percentile(boot_means, (1.0 - alpha / 2.0) * 100))
    return observed_mean, ci_lower, ci_upper


def paired_cluster_bootstrap(
    paper_scores_base: Dict[str, List[float]],
    paper_scores_cand: Dict[str, List[float]],
    n_bootstraps: int = 2000,
    seed: int = 42,
    estimand: str = "query",
) -> Tuple[float, Tuple[float, float], float]:
    """
    Computes paired cluster bootstrap difference (candidate - baseline) and 95% CI.
    Resamples at the paper cluster level (B=2000, seed=42).

    Args:
        paper_scores_base: Mapping from paper_id to list of query scores for baseline.
        paper_scores_cand: Mapping from paper_id to list of query scores for candidate.
        n_bootstraps: Number of cluster bootstrap iterations.
        seed: Random seed for reproducibility.
        estimand: 'query' (default; query-weighted, pooling queries across sampled papers)
                  or 'paper' (paper-weighted, averaging queries within each paper first).

    Returns:
        (mean_diff, (ci_lower, ci_upper), p_value)

    P-value uses the standard finite-sample Monte Carlo bound:
      p = min(1.0, 2 * (r + 1) / (B + 1))
    where r is the number of bootstrap resamples with mean_diff on the opposite
    side of zero from the observed mean_diff.
    """
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
        paper_means_map = {
            p: float(np.mean(paper_scores_cand[p])) - float(np.mean(paper_scores_base[p]))
            for p in paper_keys
        }
    else:
        all_diffs_actual = []
        for p in paper_keys:
            all_diffs_actual.extend(
                np.array(paper_scores_cand[p]) - np.array(paper_scores_base[p])
            )
        mean_diff = float(np.mean(all_diffs_actual)) if all_diffs_actual else 0.0

    rng = np.random.default_rng(seed)
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


def holm_bonferroni_correction(
    raw_p_values: List[float],
    alpha: float = 0.05,
) -> List[Dict[str, Union[float, bool]]]:
    """
    Applies Holm-Bonferroni step-down multiple comparison correction.
    Strongly controls family-wise error rate (FWER) without Bonferroni's excessive conservatism.

    Args:
        raw_p_values: List of raw p-values from multiple candidate models vs baseline.
        alpha: Overall family-wise significance level (default: 0.05).

    Returns:
        List of dicts in the original order with:
          - 'raw_p': float
          - 'adj_p': float (adjusted p-value bounded in [0, 1])
          - 'significant': bool
    """
    m = len(raw_p_values)
    if m == 0:
        return []

    # Sort indices by p-value
    sorted_indices = sorted(range(m), key=lambda i: raw_p_values[i])
    sorted_p = [raw_p_values[i] for i in sorted_indices]

    adj_p_sorted = [0.0] * m
    accum = 0.0
    for rank, p in enumerate(sorted_p):
        step_factor = m - rank
        adj_p = min(1.0, max(accum, p * step_factor))
        adj_p_sorted[rank] = adj_p
        accum = adj_p

    # Reconstruct original order
    results = [None] * m
    for rank, orig_idx in enumerate(sorted_indices):
        adj_val = adj_p_sorted[rank]
        results[orig_idx] = {
            "raw_p": round(raw_p_values[orig_idx], 6),
            "adj_p": round(adj_val, 6),
            "significant": bool(adj_val < alpha),
        }
    return results
