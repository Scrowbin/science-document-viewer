"""
eval_common package initialization.
Exports all canonical statistical metrics, bootstrap tests, and relevance functions.
"""

from .stats import (
    compute_dcg,
    compute_ndcg,
    compute_mrr,
    compute_recall,
    compute_hit_at_k,
    cluster_bootstrap_ci,
    paired_cluster_bootstrap,
    holm_bonferroni_correction,
)

from .relevance import (
    STOPWORDS,
    tokenize_regex,
    clean_evidence,
    is_chunk_hit,
    count_relevant_chunks,
)

__all__ = [
    "compute_dcg",
    "compute_ndcg",
    "compute_mrr",
    "compute_recall",
    "compute_hit_at_k",
    "cluster_bootstrap_ci",
    "paired_cluster_bootstrap",
    "holm_bonferroni_correction",
    "STOPWORDS",
    "tokenize_regex",
    "clean_evidence",
    "is_chunk_hit",
    "count_relevant_chunks",
]
