"""
Canonical shared evaluation utilities for the RAG pipeline benchmark.
Backwards-compatibility shim re-exporting from eval_common package.
"""

from eval_common.stats import (
    compute_dcg,
    compute_ndcg,
    compute_mrr,
    compute_recall,
    compute_hit_at_k,
    cluster_bootstrap_ci,
    paired_cluster_bootstrap,
    holm_bonferroni_correction,
)

from eval_common.relevance import (
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
