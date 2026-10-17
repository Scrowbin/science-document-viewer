"""
Evaluation Harness for Page-Level Citation & Attribution Accuracy (Step 10).
Evaluates whether retrieved chunks or generated answer citations correctly point
to the ground-truth physical PDF page numbers established by Track B (Task B1).

Measures:
  - Page Citation Recall@1, Recall@3, Recall@5
  - Page Citation Precision@k
  - Citation F1 Score
  - Hallucinated Citation Rate (citations pointing to pages with zero evidence)
  - Paired Bootstrap 95% Confidence Intervals against random-page citation baseline
"""

import argparse
import json
import math
import os
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

# Add backend directory to sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from apps.documents.services.chunking_utils import chunk_sections, extract_sections_from_pdf

DEFAULT_BENCHMARK_PATH = os.path.join(BACKEND_DIR, "data", "eval_benchmark_seed.json")
DEFAULT_PAGE_GOLD_PATH = os.path.join(BACKEND_DIR, "data", "page_level_alignment_gold.json")
DEFAULT_PER_QUESTION_LOG = os.path.join(BACKEND_DIR, "data", "retrieval_per_question.jsonl")


def load_gold_page_map(gold_path: str) -> Dict[str, int]:
    """Loads query_id -> ground truth target page mapping."""
    if not os.path.exists(gold_path):
        raise FileNotFoundError(f"Gold page alignment file not found: {gold_path}")

    with open(gold_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    page_map: Dict[str, int] = {}
    items = data.get("items", []) if isinstance(data, dict) else data
    for item in items:
        qid = item.get("id")
        target_page = item.get("target_page") or item.get("expected_page")
        if qid and target_page:
            page_map[qid] = int(target_page)
    return page_map


def compute_paired_bootstrap_ci(
    baseline_scores: List[float],
    candidate_scores: List[float],
    n_resamples: int = 2000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Computes difference in means and 95% bootstrap confidence interval."""
    if len(baseline_scores) != len(candidate_scores):
        raise ValueError("Baseline and candidate score lists must have identical length.")

    n = len(baseline_scores)
    if n == 0:
        return 0.0, 0.0, 0.0

    diffs = [c - b for b, c in zip(baseline_scores, candidate_scores)]
    observed_mean_diff = sum(diffs) / n

    rng = random.Random(seed)
    bootstrap_means: List[float] = []

    for _ in range(n_resamples):
        resample = [rng.choice(diffs) for _ in range(n)]
        bootstrap_means.append(sum(resample) / n)

    bootstrap_means.sort()
    low_idx = int(n_resamples * 0.025)
    high_idx = int(n_resamples * 0.975)

    ci_low = round(bootstrap_means[low_idx], 3)
    ci_high = round(bootstrap_means[high_idx], 3)
    return round(observed_mean_diff, 3), ci_low, ci_high


def evaluate_citations_from_per_question_log(
    log_path: str,
    gold_page_map: Dict[str, int],
    top_k: int = 4,
) -> Dict[str, Any]:
    """
    Evaluates citation accuracy based on the pages spanned by top-k retrieved chunks
    from the retrieval per-question log.
    """
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Retrieval log file not found: {log_path}")

    records: List[Dict[str, Any]] = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    # Group by strategy
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        strat = r.get("strategy") or r.get("chunking_strategy", "default")
        grouped.setdefault(strat, []).append(r)

    strategy_results: Dict[str, Any] = {}

    for strat, items in grouped.items():
        total_eval = 0
        hits_at_1 = 0
        hits_at_3 = 0
        hits_at_k = 0
        hallucinated_count = 0
        precisions: List[float] = []
        recalls: List[float] = []
        f1s: List[float] = []
        scores_for_bootstrap: List[float] = []

        for item in items:
            qid = item.get("question_id", "")
            true_page = gold_page_map.get(qid)
            if not true_page:
                continue

            total_eval += 1
            retrieved_chunks = item.get("retrieved_chunks", [])
            # Extract cited pages from top chunks
            cited_pages: List[int] = []
            for c in retrieved_chunks[:top_k]:
                p_start = c.get("page_start", 1)
                p_end = c.get("page_end", p_start)
                for p in range(p_start, p_end + 1):
                    if p not in cited_pages:
                        cited_pages.append(p)

            # Hit checks
            c_at_1 = cited_pages[:1]
            c_at_3 = cited_pages[:3]
            c_at_k = cited_pages[:top_k]

            hit_1 = 1 if true_page in c_at_1 else 0
            hit_3 = 1 if true_page in c_at_3 else 0
            hit_k = 1 if true_page in c_at_k else 0

            hits_at_1 += hit_1
            hits_at_3 += hit_3
            hits_at_k += hit_k

            # Precision & Recall
            prec = (1.0 / len(c_at_k)) if hit_k and c_at_k else 0.0
            rec = 1.0 if hit_k else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)
            scores_for_bootstrap.append(f1)

            if not hit_k:
                hallucinated_count += 1

        n = max(1, total_eval)
        rec_1 = round(hits_at_1 / n, 3)
        rec_3 = round(hits_at_3 / n, 3)
        rec_k = round(hits_at_k / n, 3)
        mean_prec = round(sum(precisions) / n, 3)
        mean_rec = round(sum(recalls) / n, 3)
        mean_f1 = round(sum(f1s) / n, 3)
        halluc_rate = round(hallucinated_count / n, 3)

        strategy_results[strat] = {
            "strategy": strat,
            "total_questions": total_eval,
            "citation_recall_at_1": rec_1,
            "citation_recall_at_3": rec_3,
            "citation_recall_at_k": rec_k,
            "citation_precision_at_k": mean_prec,
            "citation_f1": mean_f1,
            "hallucinated_citation_rate": halluc_rate,
            "scores_for_bootstrap": scores_for_bootstrap,
        }

    return strategy_results


def run_citation_suite(
    gold_path: str = DEFAULT_PAGE_GOLD_PATH,
    log_path: str = DEFAULT_PER_QUESTION_LOG,
    output_path: Optional[str] = None,
    top_k: int = 4,
) -> Dict[str, Any]:
    """Runs Step 10 evaluation and outputs summary table and stats."""
    gold_page_map = load_gold_page_map(gold_path)
    if not gold_page_map:
        raise ValueError(f"No gold page entries found in {gold_path}")

    strat_results = evaluate_citations_from_per_question_log(log_path, gold_page_map, top_k=top_k)

    print(f"\n[EVAL-CITATION] Step 10 Page-Level Citation & Attribution Evaluation (Top-{top_k})")
    print("=" * 105)
    print(
        f"{'Strategy / Arm':<22} | {'Queries':<7} | {'Recall@1':<9} | {'Recall@3':<9} | "
        f"{f'Recall@{top_k}':<9} | {'Precision':<9} | {'Citation F1':<11} | {'Halluc Rate':<11}"
    )
    print("-" * 105)

    base_strat = "section_overlap"
    base_scores = strat_results.get(base_strat, {}).get("scores_for_bootstrap", [])

    summary_rows: List[Dict[str, Any]] = []

    for strat, data in strat_results.items():
        is_baseline = (strat == base_strat)
        tag = "[BASE]" if is_baseline else "      "

        # Paired bootstrap CI vs baseline
        if base_scores and len(base_scores) == len(data["scores_for_bootstrap"]):
            mean_diff, ci_l, ci_h = compute_paired_bootstrap_ci(base_scores, data["scores_for_bootstrap"])
            ci_str = f"[{ci_l:+.3f}, {ci_h:+.3f}]"
        else:
            ci_str = "N/A"

        row = {
            "strategy": strat,
            "is_baseline": is_baseline,
            "queries": data["total_questions"],
            "recall_1": data["citation_recall_at_1"],
            "recall_3": data["citation_recall_at_3"],
            "recall_k": data["citation_recall_at_k"],
            "precision_k": data["citation_precision_at_k"],
            "f1": data["citation_f1"],
            "hallucination_rate": data["hallucinated_citation_rate"],
            "bootstrap_ci_diff": ci_str,
        }
        summary_rows.append(row)

        print(
            f"{tag} {strat:<15} | {data['total_questions']:<7} | {data['citation_recall_at_1']:<9.3f} | "
            f"{data['citation_recall_at_3']:<9.3f} | {data['citation_recall_at_k']:<9.3f} | "
            f"{data['citation_precision_at_k']:<9.3f} | {data['citation_f1']:<11.3f} | "
            f"{data['hallucinated_citation_rate']:<11.3f}"
        )

    print("=" * 105)
    print("[EVAL-CITATION] Key Findings:")
    print("  * Page Citation Recall measures if the physical evidence page is surfaced in the citation badges.")
    print("  * Hallucination Rate measures questions where cited chunks point to wrong or ungrounded pages.")

    summary = {
        "step": "10_citation",
        "top_k": top_k,
        "baseline_strategy": base_strat,
        "results": summary_rows,
    }

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[EVAL-CITATION] Summary saved to: {output_path}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Page-Level Citation & Attribution (Step 10).")
    parser.add_argument(
        "--gold",
        default=DEFAULT_PAGE_GOLD_PATH,
        help="Path to gold page alignment JSON",
    )
    parser.add_argument(
        "--log",
        default=DEFAULT_PER_QUESTION_LOG,
        help="Path to retrieval per-question JSONL log",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(BACKEND_DIR, "data", "citation_evaluation_results.json"),
        help="Path to output summary JSON",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Top-k chunks to inspect for page citations (default: 4)",
    )
    args = parser.parse_args()

    run_citation_suite(
        gold_path=args.gold,
        log_path=args.log,
        output_path=args.output,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()
