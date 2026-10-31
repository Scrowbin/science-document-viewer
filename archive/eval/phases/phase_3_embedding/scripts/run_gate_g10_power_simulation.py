#!/usr/bin/env python3
"""
Gate G10 Monte Carlo Power Simulation & Gate G13 Pre-Flight Sizing Lock
Protocol: EMBEDDING_EVAL_PLAN.md Version 3.5 (§7.1, §7.2, §7.3, §11)

Execution:
1. Audits empirical development residuals of Top-N dense candidates vs. all-MiniLM-L6-v2.
2. Identifies the candidate exhibiting maximum between-paper cluster SD (s_{Delta,paper}).
3. Centers cluster residuals strictly at SESOI = 0.030 (eliminating in-sample optimism).
4. Simulates S = 2,000 Monte Carlo draws per sample size K in {200, 300, 400, 416, 500, 597, 700, 800}.
5. Evaluates statistical power at alpha_min = 0.01667 (Holm-adjusted first threshold for m = 3 primary family).
6. Executes the pre-registered piecewise sizing decision formula.
7. Serializes results to `eval/prepared/expansion_decision.json` and updates `manifest.json`.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.audit.verify_gate_g14_spot_check import compute_hc1_cluster_se, sha256_file


def load_dev_cluster_residuals(
    results_path: Path,
) -> Tuple[str, float, List[Dict[str, Any]], Dict[str, float]]:
    """
    Load development split results, compute paired difference residuals vs MiniLM,
    and select candidate pair with maximum between-paper cluster standard deviation.
    """
    with results_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    baseline_model = "all-MiniLM-L6-v2"
    baseline_papers = data["models"][baseline_model]["within_paper"]["scores_by_paper"]

    candidate_models = ["e5-small-v2", "bge-small-en-v1.5", "all-mpnet-base-v2"]
    cluster_sd_dict: Dict[str, float] = {}
    candidate_paper_diffs: Dict[str, Dict[str, np.ndarray]] = {}

    for cname in candidate_models:
        cand_papers = data["models"][cname]["within_paper"]["scores_by_paper"]
        paper_means = []
        diffs_by_paper: Dict[str, np.ndarray] = {}

        for pid, b_scores in baseline_papers.items():
            if pid in cand_papers:
                b_arr = np.array(b_scores, dtype=np.float64)
                c_arr = np.array(cand_papers[pid], dtype=np.float64)
                d_arr = c_arr - b_arr
                diffs_by_paper[pid] = d_arr
                paper_means.append(float(np.mean(d_arr)))

        s_cluster = float(np.std(paper_means, ddof=1))
        cluster_sd_dict[cname] = s_cluster
        candidate_paper_diffs[cname] = diffs_by_paper

    # Top-N rule: Argmax candidate
    worst_case_candidate = max(cluster_sd_dict, key=lambda k: cluster_sd_dict[k])
    max_sd = cluster_sd_dict[worst_case_candidate]

    # Extract cluster residuals: e_{k,i} = d_{k,i} - mean(d)
    diffs = candidate_paper_diffs[worst_case_candidate]
    all_query_diffs = np.concatenate(list(diffs.values()))
    grand_mean = float(np.mean(all_query_diffs))

    clusters_list: List[Dict[str, Any]] = []
    for pid, d_arr in diffs.items():
        residuals = d_arr - grand_mean
        clusters_list.append({
            "paper_id": pid,
            "m_k": len(residuals),
            "residuals": residuals,
        })

    return worst_case_candidate, max_sd, clusters_list, cluster_sd_dict


def run_power_simulation(
    clusters: List[Dict[str, np.ndarray]],
    k_targets: List[int],
    sesoi: float = 0.030,
    alpha_min: float = 0.016666666666666666,
    s_sims: int = 2000,
    seed: int = 42,
) -> Dict[int, Dict[str, float]]:
    """
    Monte Carlo simulation modeling cluster-level ratio-estimator hypothesis testing.
    Resamples paper clusters with replacement, centers residuals at SESOI,
    and computes empirical rejection rates under cluster-robust inference.
    """
    rng = np.random.default_rng(seed)
    n_dev_clusters = len(clusters)
    res_dict: Dict[int, Dict[str, float]] = {}

    # Critical two-sided z value for alpha_min = 0.01667 (z = 2.3925)
    # Using normal approximation for K >= 200 degrees of freedom
    # scipy.stats.norm.ppf(1 - 0.0166667 / 2) = 2.3925
    z_crit = 2.3925

    print(f"Executing Gate G10 Power Simulation (S={s_sims} draws, seed={seed}, SESOI={sesoi:.3f}, alpha_min={alpha_min:.5f})")

    for k in k_targets:
        rejections = 0
        deltas = []
        ses = []

        for _ in range(s_sims):
            # Draw K cluster indices with replacement
            sampled_indices = rng.integers(0, n_dev_clusters, size=k)

            # Accumulate per-cluster totals and query counts
            d_k = np.zeros(k, dtype=np.float64)
            m_k = np.zeros(k, dtype=np.float64)

            for i, c_idx in enumerate(sampled_indices):
                c = clusters[c_idx]
                m = c["m_k"]
                m_k[i] = m
                # Center residuals at SESOI
                d_k[i] = np.sum(sesoi + c["residuals"])

            n_total = float(np.sum(m_k))
            delta_hat = float(np.sum(d_k)) / n_total

            # Analytical HC1 cluster-robust standard error
            se_hc1 = compute_hc1_cluster_se(d_k, m_k)

            deltas.append(delta_hat)
            ses.append(se_hc1)

            # Two-sided Wald test against null Delta = 0 under cluster-robust SE
            if se_hc1 > 1e-12:
                z_stat = delta_hat / se_hc1
                if abs(z_stat) >= z_crit:
                    rejections += 1

        power = rejections / s_sims
        mc_se = math.sqrt(power * (1.0 - power) / s_sims)
        mean_delta = float(np.mean(deltas))
        mean_se = float(np.mean(ses))

        res_dict[k] = {
            "k_papers": k,
            "estimated_queries": int(k * 3.05),  # empirical avg ~3.05 queries/paper in QASPER
            "power": round(power, 4),
            "mc_se": round(mc_se, 4),
            "mean_delta": round(mean_delta, 4),
            "mean_se": round(mean_se, 5),
            "power_percent": round(power * 100.0, 2),
        }
        print(f"  K = {k:3d} papers (~{int(k*3.05):4d} queries): Power = {power*100.5:5.1f}% ± {mc_se*100.0:4.2f}% (Mean SE = {mean_se:.5f})")

    return res_dict


def make_expansion_decision(
    power_results: Dict[int, Dict[str, float]],
    target_power: float = 0.80,
) -> Dict[str, Any]:
    """
    Apply pre-registered piecewise sizing decision formula (§7.3).
    """
    pow_416 = power_results[416]["power"]
    pow_597 = power_results[597]["power"]
    pow_800 = power_results[800]["power"]

    if pow_416 >= target_power:
        chosen_tier = "Tier 0"
        k_selected = 416
        decision_code = "TIER_0_PRISTINE_TEST_SUFFICIENT"
        cohort_desc = "official_qasper_test_split (416 papers, ~1270 answerable queries; 0 dev overlap)"
        justification = (
            f"Achieved statistical power at K=416 ({pow_416*100:.1f}%) meets or exceeds the pre-registered "
            f"target of {target_power*100:.0f}% under Holm-adjusted alpha_min=0.01667."
        )
    elif pow_597 >= target_power:
        chosen_tier = "Tier 1"
        k_selected = 597
        decision_code = "TIER_1_EXPANSION_TRIGGERED"
        cohort_desc = "pool_tier_0_with_untouched_validation (597 papers, ~1830 queries; 0 dev overlap)"
        justification = (
            f"Power at Tier 0 K=416 ({pow_416*100:.1f}%) is below 80%; Tier 1 pooling of 181 untouched "
            f"validation papers achieves {pow_597*100:.1f}% >= 80% power."
        )
    elif pow_800 >= target_power:
        chosen_tier = "Tier 2"
        k_selected = 800
        decision_code = "TIER_2_EXPANSION_TRIGGERED"
        cohort_desc = "pool_tier_1_with_untouched_train (800 papers, ~2400 queries; leaves 385 train untouched; 0 dev overlap)"
        justification = (
            f"Power at Tier 1 K=597 ({pow_597*100:.1f}%) is below 80%; Tier 2 pooling of 203 untouched "
            f"train papers achieves {pow_800*100:.1f}% >= 80% power."
        )
    else:
        chosen_tier = "Tier 2 (Proceed & Report Limitation)"
        k_selected = 800
        decision_code = "PROCEED_AND_REPORT_LIMITATION"
        cohort_desc = "pool_tier_1_with_untouched_train (800 papers, ~2400 queries; leaves 385 train untouched; 0 dev overlap)"
        justification = (
            f"Simulated power remains below 80% across all ladder steps (achieving {pow_800*100:.1f}% at K=800). "
            f"Per protocol §7.3, ad-hoc data hunting is barred; study proceeds with K=800 and reports power as thesis limitation."
        )

    return {
        "chosen_tier": chosen_tier,
        "k_selected": k_selected,
        "decision_code": decision_code,
        "cohort_description": cohort_desc,
        "target_power": target_power,
        "power_at_k416": pow_416,
        "power_at_k597": pow_597,
        "power_at_k800": pow_800,
        "justification": justification,
    }


def main() -> int:
    now_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dev_results_path = (
        REPO_ROOT
        / "eval"
        / "phases"
        / "phase_3_embedding"
        / "artifacts"
        / "expanded_160_papers_benchmark_results.json"
    )

    if not dev_results_path.exists():
        print(f"Error: Dev benchmark results not found at {dev_results_path}", file=sys.stderr)
        return 1

    # 1. Load Dev Residuals and Select Worst-Case Candidate
    worst_cand, max_sd, clusters, cluster_sds = load_dev_cluster_residuals(dev_results_path)

    print("=" * 80)
    print("GATE G10 PRE-FINALIST TOP-N RESIDUAL AUDIT & POWER SIMULATION")
    print("=" * 80)
    print(f"Dev Split Benchmark Source: {dev_results_path.relative_to(REPO_ROOT)}")
    print(f"Baseline Control Model:    sentence-transformers/all-MiniLM-L6-v2")
    print(f"Evaluated Candidate Pairs: {list(cluster_sds.keys())}")
    for c, s in cluster_sds.items():
        print(f"  - {c:20s}: Between-paper cluster SD = {s:.4f}")
    print(f"Top-N Max Cluster SD Winner: {worst_cand} (s_cluster = {max_sd:.4f})")
    print(f"Note on In-Sample Status:   {worst_cand} dev performance is in-sample; residuals centered at SESOI=0.030")
    print("=" * 80)

    # 2. Run Monte Carlo Power Curve Simulation
    k_targets = [200, 300, 400, 416, 500, 597, 700, 800]
    power_results = run_power_simulation(
        clusters=clusters,
        k_targets=k_targets,
        sesoi=0.030,
        alpha_min=0.016666666666666666,
        s_sims=2000,
        seed=42,
    )

    # 3. Apply Pre-Registered Sizing Decision Formula
    decision = make_expansion_decision(power_results, target_power=0.80)

    # 4. Serialize to eval/prepared/expansion_decision.json
    output_dir = REPO_ROOT / "eval" / "prepared"
    output_dir.mkdir(parents=True, exist_ok=True)
    decision_file = output_dir / "expansion_decision.json"

    payload = {
        "gate": "Gate G10 & Gate G13",
        "protocol_version": "3.5-preregistered",
        "timestamp_iso": now_iso,
        "dgp_specification": {
            "method": "empirical_cluster_residual_resampling",
            "candidate_selection_rule": "top_n_max_cluster_sd",
            "selected_worst_case_candidate": worst_cand,
            "selected_cluster_sd": max_sd,
            "all_evaluated_candidates_sd": cluster_sds,
            "sesoi_ndcg_10": 0.030,
            "in_sample_bias_mitigation": "residuals_centered_strictly_at_sesoi",
        },
        "simulation_parameters": {
            "monte_carlo_draws_s": 2000,
            "random_seed": 42,
            "alpha_min_holm": 0.016666666666666666,
            "primary_family_m": 3,
        },
        "power_curve": {str(k): v for k, v in power_results.items()},
        "expansion_decision": decision,
        "lock_status": "FROZEN_BEFORE_STAGE_2",
    }

    with decision_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    decision_sha256 = sha256_file(decision_file)
    print("=" * 80)
    print(f"EXPANSION DECISION SUMMARY: {decision['chosen_tier']} ({decision['k_selected']} papers)")
    print(f"Decision Code:  {decision['decision_code']}")
    print(f"Cohort Scope:   {decision['cohort_description']}")
    print(f"Power at K=416: {decision['power_at_k416']*100:.2f}%")
    print(f"Power at K=597: {decision['power_at_k597']*100:.2f}%")
    print(f"Power at K=800: {decision['power_at_k800']*100:.2f}%")
    print(f"Serialized to:  {decision_file.relative_to(REPO_ROOT)}")
    print(f"SHA-256 Digest: {decision_sha256}")
    print("=" * 80)

    # 5. Lock into manifest.json
    manifest_path = REPO_ROOT / "manifest.json"
    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["files"]["eval/prepared/expansion_decision.json"] = {
        "path": "eval/prepared/expansion_decision.json",
        "sha256": decision_sha256,
        "role": "Pre-flight Gate G10 Monte Carlo Power Simulation and Sizing Lock",
        "chosen_tier": decision["chosen_tier"],
        "k_papers": decision["k_selected"],
    }

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Updated manifest.json with expansion_decision.json SHA-256 lock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
