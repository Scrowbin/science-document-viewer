"""
Unit tests for eval_common.stats and eval_common.relevance.
Validates nDCG, MRR, Recall, Hit@k, paper-cluster bootstrap, Holm-Bonferroni correction, and relevance rules.
"""

import math
import sys
from pathlib import Path
import numpy as np

# Ensure backend/scripts is on sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

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
    is_chunk_hit,
    count_relevant_chunks,
    tokenize_regex,
    clean_evidence,
)


def test_ndcg_perfect_ranking():
    # Rank 1 hit out of 1 relevant item
    rels = [1, 0, 0, 0]
    ndcg = compute_ndcg(rels, total_relevant=1, k=4)
    assert math.isclose(ndcg, 1.0, rel_tol=1e-5)


def test_ndcg_second_rank():
    # Rank 2 hit out of 1 relevant item
    # DCG = 1 / log2(3); IDCG = 1 / log2(2) = 1.0
    # Expected: 1.0 / log2(3) approx 0.63092975
    rels = [0, 1, 0, 0]
    ndcg = compute_ndcg(rels, total_relevant=1, k=4)
    expected = 1.0 / math.log2(3)
    assert math.isclose(ndcg, expected, rel_tol=1e-4)


def test_ndcg_zero_relevant():
    rels = [0, 0, 0]
    assert compute_ndcg(rels, total_relevant=0, k=4) == 0.0


def test_mrr_first_rank():
    assert math.isclose(compute_mrr([1, 0, 0], k=10), 1.0)


def test_mrr_second_rank():
    assert math.isclose(compute_mrr([0, 1, 0], k=10), 0.5)


def test_mrr_no_hits():
    assert compute_mrr([0, 0, 0], k=10) == 0.0


def test_recall():
    rels = [1, 0, 1, 0, 0]
    # 2 hits out of 4 relevant items
    assert math.isclose(compute_recall(rels, total_relevant=4, k=5), 0.5)
    # Total relevant = 0
    assert compute_recall(rels, total_relevant=0, k=5) == 0.0


def test_hit_at_k():
    assert compute_hit_at_k([0, 0, 1, 0], k=3) == 1
    assert compute_hit_at_k([0, 0, 1, 0], k=2) == 0


def test_cluster_bootstrap_ci():
    # 10 papers, each with scores around 0.5
    rng = np.random.default_rng(42)
    paper_scores = {
        f"p{i}": list(rng.normal(0.5, 0.05, size=5))
        for i in range(10)
    }
    mean, ci_low, ci_high = cluster_bootstrap_ci(paper_scores, n_bootstraps=500, seed=42)
    assert 0.45 <= mean <= 0.55
    assert ci_low <= mean <= ci_high


def test_paired_cluster_bootstrap_identical():
    # Baseline vs itself should give diff=0, p=1.0
    paper_scores = {f"p{i}": [0.4, 0.6] for i in range(8)}
    diff, (ci_low, ci_high), p_val = paired_cluster_bootstrap(
        paper_scores, paper_scores, n_bootstraps=500, seed=42
    )
    assert math.isclose(diff, 0.0, abs_tol=1e-5)
    assert p_val == 1.0


def test_paired_cluster_bootstrap_superior():
    # Candidate strictly outperforms baseline on all queries
    base = {f"p{i}": [0.3, 0.4] for i in range(15)}
    cand = {f"p{i}": [0.7, 0.8] for i in range(15)}
    diff, (ci_low, ci_high), p_val = paired_cluster_bootstrap(
        base, cand, n_bootstraps=500, seed=42
    )
    assert diff > 0.35
    assert ci_low > 0.2
    assert p_val < 0.05


def test_holm_bonferroni_correction():
    raw_p = [0.001, 0.04, 0.03, 0.80]
    res = holm_bonferroni_correction(raw_p, alpha=0.05)
    assert len(res) == 4
    # The smallest raw p should remain significant
    assert res[0]["significant"] is True
    # The largest raw p should not be significant
    assert res[3]["significant"] is False
    # Adjusted p-values must be >= raw p-values
    for r in res:
        assert r["adj_p"] >= r["raw_p"] - 1e-6


def test_relevance_substring_hit():
    chunk = {
        "paper_arxiv_id": "1706.03762",
        "text": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
    }
    quote = "sequence transduction models are based on complex"
    assert is_chunk_hit(chunk, "1706.03762", verbatim_evidence_quote=quote, tau=0.55) is True


def test_relevance_wrong_paper():
    chunk = {
        "paper_arxiv_id": "1706.03762",
        "text": "The dominant sequence transduction models are based on complex recurrent neural networks.",
    }
    assert is_chunk_hit(chunk, "1512.03385", verbatim_evidence_quote="transduction models") is False


def test_count_relevant_chunks():
    chunks = [
        {"paper_arxiv_id": "p1", "text": "Deep residual learning for image recognition."},
        {"paper_arxiv_id": "p1", "text": "Unrelated paragraph about breakfast cereals."},
        {"paper_arxiv_id": "p1", "text": "Residual networks are easier to optimize and gain accuracy from increased depth."},
    ]
    quote = "residual learning and residual networks"
    count = count_relevant_chunks(chunks, "p1", verbatim_evidence_quote=quote, tau=0.30)
    assert count >= 1
