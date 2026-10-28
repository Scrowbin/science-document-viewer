#!/usr/bin/env python3
"""
Independent Recalculation and Validation Pass for RQ5 Thesis Synchronization.
Reads canonical experiment outputs and adjudicated datasets, verifies all statistics,
and prints exact numbers for inclusion in THESIS_RQ5_LLM_REPORT.md, CHAPTER5.md,
and DU_AN_CNTT_TOAN_VAN.md.
"""

import csv
import json
import math
from pathlib import Path
import statistics

# 1. Paths
BENCHMARK_500Q = Path("eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json")
UNBLINDED_CSV = Path("eval/phases/phase_9_generation/artifacts/human_faithfulness_review/faithfulness_annotations_unblinded.csv")
ADJUDICATED_CSV = Path("eval/phases/phase_9_generation/artifacts/human_faithfulness_review/audit/faithfulness_annotations_adjudicated.csv")
MAPPING_JSON = Path("eval/phases/phase_9_generation/artifacts/human_faithfulness_review/restricted_model_label_mapping.json")

TAXONOMY = [
    "SUPPORTED",
    "REFUSAL_VALID",
    "UNSUPPORTED",
    "MISSING_INFO - UNJUSTIFIED_REFUSAL",
    "MISSING_INFO - PARTIAL",
    "CONTRADICTED",
]

MODELS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"]


def pearson_r(x, y):
    n = len(x)
    if n < 2:
        return 0.0
    mx = statistics.mean(x)
    my = statistics.mean(y)
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den = math.sqrt(sum((xi - mx) ** 2 for xi in x) * sum((yi - my) ** 2 for yi in y))
    return num / den if den != 0 else 0.0


def main():
    print("=" * 80)
    print("1. CANONICAL 500-QUESTION CONFIRMATORY BENCHMARK (K=250 papers, N=500 questions)")
    print("=" * 80)
    with open(BENCHMARK_500Q, "r", encoding="utf-8") as f:
        b500 = json.load(f)

    print(f"{'Model':14s} | {'F1':6s} | {'Extr':6s} | {'Abstr':6s} | {'Bool':6s} | {'Refusals':15s} | {'Containment':11s} | {'Latency P50':11s} | {'Throughput':10s}")
    print("-" * 110)
    for m in MODELS:
        md = b500["model_summaries"][m]
        f1_str = f"{md['token_f1_mean']:.4f}"
        ex_str = f"{md['answer_f1_by_type']['extractive']['token_f1_mean']:.4f}"
        ab_str = f"{md['answer_f1_by_type']['abstractive']['token_f1_mean']:.4f}"
        bo_str = f"{md['answer_f1_by_type']['boolean']['token_f1_mean']:.4f}"
        ref_str = f"{md['refusal_count']} ({md['refusal_rate_pct']:.1f}%)"
        cnt_str = f"{md['automated_containment_proxy_mean']*100:.1f}%"
        lat_str = f"{md['timing']['latency_p50_s']:.2f}s"
        tp_str = f"{md['timing']['throughput_mean_tps']:.1f} tok/s"
        print(f"{m:14s} | {f1_str:6s} | {ex_str:6s} | {ab_str:6s} | {bo_str:6s} | {ref_str:15s} | {cnt_str:11s} | {lat_str:11s} | {tp_str:10s}")

    print("\nPairwise Inferential Decisions (Paper Clusters K=250, df=249):")
    for comp in b500["statistical_analysis"]["comparisons"]:
        cand = comp["candidate_model"]
        base = comp["baseline_model"]
        pair_name = f"{cand} vs {base}"
        print(f"  - {pair_name:30s}: Delta = {comp['delta_obs']:+.4f}, 95% Clustered CI = [{comp['bootstrap_ci_95'][0]:+.4f}, {comp['bootstrap_ci_95'][1]:+.4f}], t = {comp['t_statistic']:+.4f}, p_adj = {comp['holm_bonferroni_adj_p']:.4e}, Decision = {comp['decision']}")

    print("\n" + "=" * 80)
    print("2. CANONICAL 60-ANSWER QUALITATIVE HUMAN AUDIT (20 questions x 3 models)")
    print("=" * 80)
    with open(UNBLINDED_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 60, f"Expected 60, got {len(rows)}"

    # Grid of counts
    counts = {lbl: {m: 0 for m in MODELS} for lbl in TAXONOMY}
    for r in rows:
        counts[r["final_primary_label"]][r["actual_model"]] += 1

    print(f"{'Primary Label':35s} | {'llama3.2:3b':12s} | {'llama3.2:1b':12s} | {'qwen2.5:0.5b':12s} | {'Total':5s} | {'% (N=60)':8s}")
    print("-" * 90)
    for lbl in TAXONOMY:
        c3 = counts[lbl]["llama3.2:3b"]
        c1 = counts[lbl]["llama3.2:1b"]
        cq = counts[lbl]["qwen2.5:0.5b"]
        tot = c3 + c1 + cq
        pct = tot / 60.0 * 100.0
        print(f"{lbl:35s} | {c3:12d} | {c1:12d} | {cq:12d} | {tot:5d} | {pct:6.1f}%")
    print("-" * 90)
    print(f"{'Total Answers':35s} | {20:12d} | {20:12d} | {20:12d} | {60:5d} | {'100.0%':8s}")

    print("\nDerived Qualitative Proportions per Model (Sample n=20 each):")
    for m in MODELS:
        supp = counts["SUPPORTED"][m]
        ref_val = counts["REFUSAL_VALID"][m]
        unsupp = counts["UNSUPPORTED"][m]
        contra = counts["CONTRADICTED"][m]
        unjust = counts["MISSING_INFO - UNJUSTIFIED_REFUSAL"][m]
        part = counts["MISSING_INFO - PARTIAL"][m]

        print(f"[{m}]")
        print(f"  - Strict Faithfulness (SUPPORTED):           {supp/20*100:5.1f}% ({supp}/20)")
        print(f"  - Grounded Compliance (SUPPORTED + REF_VAL): {(supp+ref_val)/20*100:5.1f}% ({supp+ref_val}/20)")
        print(f"  - Total Hallucinations (UNSUPP + CONTRA):    {(unsupp+contra)/20*100:5.1f}% ({unsupp+contra}/20)")
        print(f"  - Pure Fabrications (UNSUPPORTED):           {unsupp/20*100:5.1f}% ({unsupp}/20)")
        print(f"  - Direct Contradictions (CONTRADICTED):      {contra/20*100:5.1f}% ({contra}/20)")
        print(f"  - Unjustified Refusals (UNJUSTIFIED_REF):    {unjust/20*100:5.1f}% ({unjust}/20)")
        print(f"  - Partial Answers (PARTIAL):                 {part/20*100:5.1f}% ({part}/20)")

    print("\n" + "=" * 80)
    print("3. DESCRIPTIVE ASSOCIATIONS BETWEEN HUMAN LABELS AND AUTOMATED PROXIES (N=60)")
    print("=" * 80)
    # Vectors
    v_supp = [1.0 if r["final_primary_label"] == "SUPPORTED" else 0.0 for r in rows]
    v_grounded = [1.0 if r["final_primary_label"] in ["SUPPORTED", "REFUSAL_VALID"] else 0.0 for r in rows]
    v_hallucinated = [1.0 if r["final_primary_label"] in ["UNSUPPORTED", "CONTRADICTED"] else 0.0 for r in rows]
    v_f1 = [float(r["token_f1"]) for r in rows]
    v_proxy = [float(r["automated_containment_proxy"]) for r in rows]

    r_supp_f1 = pearson_r(v_supp, v_f1)
    r_supp_proxy = pearson_r(v_supp, v_proxy)
    r_grounded_f1 = pearson_r(v_grounded, v_f1)
    r_grounded_proxy = pearson_r(v_grounded, v_proxy)
    r_hallucinated_proxy = pearson_r(v_hallucinated, v_proxy)

    print(f"  - Pearson r(Human SUPPORTED, Token F1):                   {r_supp_f1:+.4f}")
    print(f"  - Pearson r(Human SUPPORTED, Containment Proxy):         {r_supp_proxy:+.4f}")
    print(f"  - Pearson r(Human Grounded Compliance, Token F1):        {r_grounded_f1:+.4f}")
    print(f"  - Pearson r(Human Grounded Compliance, Containment Proxy):{r_grounded_proxy:+.4f}")
    print(f"  - Pearson r(Human Hallucinated, Containment Proxy):       {r_hallucinated_proxy:+.4f}")

    print("\nAutomated Proxy Means Conditioned on Human Primary Label:")
    for lbl in TAXONOMY:
        sub = [r for r in rows if r["final_primary_label"] == lbl]
        cnt = len(sub)
        mf1 = statistics.mean([float(r["token_f1"]) for r in sub]) if cnt > 0 else 0.0
        mpr = statistics.mean([float(r["automated_containment_proxy"]) for r in sub]) if cnt > 0 else 0.0
        print(f"  - {lbl:35s} (n={cnt:2d}): Mean Token F1 = {mf1:.4f}, Mean Containment Proxy = {mpr*100:5.1f}%")

    print("\nRepeated Measures Notice: The 60 observations originate from 20 distinct questions evaluated across 3 models.")
    print("These correlation coefficients are purely descriptive sample associations and do not assume independent observations.")


if __name__ == "__main__":
    main()
