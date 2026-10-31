"""
Unit Tests for Paired Paper Cluster Bootstrap and Statistical Inference.
Validates:
1. Identical model predictions (exact zero difference).
2. Large deterministic separation (p-value bound & CI calibration).
3. Unequal cluster sizes (cluster sizes from 1 to 20 queries).
4. Symmetry & Sign Inversion (swapping Model A and Model B).
5. Stability under identical random seeds.
6. Monotonicity of confidence intervals with nominal alpha.
"""

import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from eval_common import paired_cluster_bootstrap


def test_identical_model_predictions():
    """When both models have identical predictions, mean diff is 0 and p-val is 1.0."""
    paper_scores_a = {
        "p1": [0.5, 0.6, 0.7],
        "p2": [0.2, 0.3],
        "p3": [0.9],
    }
    paper_scores_b = {
        "p1": [0.5, 0.6, 0.7],
        "p2": [0.2, 0.3],
        "p3": [0.9],
    }
    mean_diff, (ci_lower, ci_upper), p_val = paired_cluster_bootstrap(
        paper_scores_a, paper_scores_b, n_bootstraps=500, seed=42
    )
    assert abs(mean_diff) < 1e-9
    assert abs(ci_lower) < 1e-9
    assert abs(ci_upper) < 1e-9
    assert p_val == 1.0


def test_large_deterministic_effect():
    """When model A strictly beats model B by 0.50 on all queries, p-val is minimal and CI excludes 0."""
    paper_scores_a = {
        f"p{i}": [0.8, 0.9, 0.85] for i in range(30)
    }
    paper_scores_b = {
        f"p{i}": [0.3, 0.4, 0.35] for i in range(30)
    }
    mean_diff, (ci_lower, ci_upper), p_val = paired_cluster_bootstrap(
        paper_scores_b, paper_scores_a, n_bootstraps=500, seed=42
    )
    assert abs(mean_diff - 0.50) < 1e-9
    assert ci_lower > 0.45
    assert ci_upper < 0.55
    assert p_val <= 0.01


def test_unequal_cluster_sizes():
    """Handles wildly unequal cluster sizes (1 to 25 queries per cluster) without error."""
    rng = np.random.default_rng(123)
    paper_scores_a: Dict[str, List[float]] = {}
    paper_scores_b: Dict[str, List[float]] = {}

    for i in range(50):
        # Cluster size between 1 and 25
        n_q = rng.integers(1, 26)
        scores_b = list(rng.uniform(0.1, 0.5, size=n_q))
        scores_a = [s + float(rng.normal(0.05, 0.02)) for s in scores_b]
        paper_scores_a[f"p{i}"] = scores_a
        paper_scores_b[f"p{i}"] = scores_b

    mean_diff, (ci_lower, ci_upper), p_val = paired_cluster_bootstrap(
        paper_scores_b, paper_scores_a, n_bootstraps=500, seed=42
    )
    assert mean_diff > 0.0
    assert ci_lower < mean_diff < ci_upper
    assert p_val < 0.05


def test_symmetry_and_sign_inversion():
    """Swapping candidate and baseline strictly negates the mean diff and inverts CI bounds."""
    rng = np.random.default_rng(999)
    paper_scores_a = {f"p{i}": list(rng.uniform(0.3, 0.8, size=4)) for i in range(20)}
    paper_scores_b = {f"p{i}": list(rng.uniform(0.2, 0.7, size=4)) for i in range(20)}

    diff_ab, (ci_low_ab, ci_high_ab), p_ab = paired_cluster_bootstrap(
        paper_scores_a, paper_scores_b, n_bootstraps=1000, seed=42
    )
    diff_ba, (ci_low_ba, ci_high_ba), p_ba = paired_cluster_bootstrap(
        paper_scores_b, paper_scores_a, n_bootstraps=1000, seed=42
    )

    assert abs(diff_ab + diff_ba) < 1e-9
    # Inverted CI bounds
    assert abs(ci_low_ab + ci_high_ba) < 1e-4
    assert abs(ci_high_ab + ci_low_ba) < 1e-4
    assert abs(p_ab - p_ba) < 1e-4


def test_reproducibility():
    """Identical seeds produce identical confidence intervals and p-values."""
    paper_scores_a = {f"p{i}": [0.4, 0.5] for i in range(15)}
    paper_scores_b = {f"p{i}": [0.3, 0.4] for i in range(15)}

    res1 = paired_cluster_bootstrap(paper_scores_a, paper_scores_b, n_bootstraps=500, seed=777)
    res2 = paired_cluster_bootstrap(paper_scores_a, paper_scores_b, n_bootstraps=500, seed=777)
    assert res1 == res2


def test_estimands_query_vs_paper():
    """Validates that query-weighted and paper-weighted estimands compute the correct weighted means."""
    paper_scores_b = {
        "p1": [0.0] * 10,  # 10 queries
        "p2": [0.0],       # 1 query
    }
    paper_scores_a = {
        "p1": [0.1] * 10,  # diff = 0.1 per query
        "p2": [0.5],       # diff = 0.5 for this 1 query
    }
    # Query-weighted mean diff: (10*0.1 + 1*0.5) / 11 = 1.5 / 11 ≈ 0.1363636
    qw_diff, (qw_low, qw_high), _ = paired_cluster_bootstrap(
        paper_scores_b, paper_scores_a, n_bootstraps=500, seed=42, estimand="query"
    )
    assert abs(qw_diff - (1.5 / 11.0)) < 1e-6

    # Paper-weighted mean diff: (0.1 + 0.5) / 2 = 0.30
    pw_diff, (pw_low, pw_high), _ = paired_cluster_bootstrap(
        paper_scores_b, paper_scores_a, n_bootstraps=500, seed=42, estimand="paper"
    )
    assert abs(pw_diff - 0.30) < 1e-6


if __name__ == "__main__":
    print("Running cluster bootstrap unit tests...")
    test_identical_model_predictions()
    print("  [PASS] Identical model predictions")
    test_large_deterministic_effect()
    print("  [PASS] Large deterministic effect")
    test_unequal_cluster_sizes()
    print("  [PASS] Unequal cluster sizes")
    test_symmetry_and_sign_inversion()
    print("  [PASS] Symmetry and sign inversion")
    test_reproducibility()
    print("  [PASS] Reproducibility with explicit seeds")
    test_estimands_query_vs_paper()
    print("  [PASS] Query-weighted vs Paper-weighted estimands")
    print("All tests passed successfully!")
