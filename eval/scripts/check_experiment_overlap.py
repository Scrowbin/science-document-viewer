#!/usr/bin/env python3
"""
Reusable Overlap and Contamination Audit Tool.

Queries candidate paper and question cohorts against the canonical
Experiment Provenance and Contamination Registry (eval/experiment_provenance_registry.json).

Usage:
  # Check paper IDs passed via CLI:
  python check_experiment_overlap.py --papers 1706.03762 1909.00694

  # Check paper IDs from a JSON manifest:
  python check_experiment_overlap.py --manifest path/to/sample_manifest.json

  # Run built-in self-test:
  python check_experiment_overlap.py --test
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "experiment_provenance_registry.json"


def load_registry(registry_path: Path = REGISTRY_PATH) -> Dict[str, Any]:
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry not found at: {registry_path}")
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def audit_cohort(
    paper_ids: List[str],
    registry: Dict[str, Any],
    question_ids: List[str] = None
) -> Dict[str, Any]:
    """
    Audit a list of paper IDs and optional question IDs against the registry.
    Returns detailed exposure breakdown, per-item audit logs, and pass/fail verdict.
    """
    paper_index = registry.get("paper_index", {})
    registered_experiments = registry.get("registered_experiments", {})

    clean_pids = sorted(list(set(p.strip() for p in paper_ids if p.strip())))
    clean_qids = sorted(list(set(q.strip() for q in question_ids if q.strip()))) if question_ids else []
    total_requested = len(clean_pids)

    unexposed_pids = []
    exposed_pids = []
    unknown_pids = []

    exposure_by_experiment: Dict[str, List[str]] = {}
    detailed_log = []

    for pid in clean_pids:
        record = paper_index.get(pid)
        if not record:
            unknown_pids.append(pid)
            detailed_log.append({
                "paper_arxiv_id": pid,
                "status": "UNKNOWN_NOT_IN_REGISTRY",
                "exposure_classifications": ["HISTORICAL_UNCERTAIN_PROVENANCE"],
                "events": []
            })
            continue

        classifications = record.get("exposure_classifications", [])
        events = record.get("exposure_events", [])

        # Historical events only (exclude current study registration)
        hist_events = [
            ev for ev in events
            if ev.get("experiment_id") not in ("EXP-RQ5-MAIN-PLANNED", "EXP-RQ5-MAIN-SAMPLED")
        ]

        if not hist_events and record.get("is_unexposed_to_repository_experiments", False):
            unexposed_pids.append(pid)
            detailed_log.append({
                "paper_arxiv_id": pid,
                "status": "UNEXPOSED_REPOSITORY",
                "rq5_main_eligibility": record.get("rq5_main_eligibility"),
                "rq5_sampling_status": record.get("rq5_sampling_status"),
                "events": []
            })
        else:
            exposed_pids.append(pid)
            for ev in hist_events:
                exp_id = ev.get("experiment_id", "UNKNOWN")
                exposure_by_experiment.setdefault(exp_id, []).append(pid)
            detailed_log.append({
                "paper_arxiv_id": pid,
                "status": "EXPOSED_PREVIOUS_EXPERIMENT",
                "exposure_classifications": classifications,
                "events": hist_events
            })

    # Optional question ID audit against historical experiments
    q_exposed = []
    if clean_qids:
        # Build question lookup map from registered historical experiments
        historical_experiments = {
            exp_id: exp_data for exp_id, exp_data in registered_experiments.items()
            if exp_id not in ("EXP-RQ5-MAIN-PLANNED", "EXP-RQ5-MAIN-SAMPLED")
        }
        q_exp_map = {}
        for exp_id, exp_data in historical_experiments.items():
            for qid in exp_data.get("question_ids", []):
                q_exp_map.setdefault(qid, []).append(exp_id)

        for qid in clean_qids:
            if qid in q_exp_map:
                q_exposed.append({"question_id": qid, "exposed_in": q_exp_map[qid]})

    verdict_clean = (len(exposed_pids) == 0 and len(unknown_pids) == 0 and len(q_exposed) == 0)

    return {
        "verdict": "PASS_UNEXPOSED" if verdict_clean else "FAIL_EXPOSURE_DETECTED",
        "total_papers_audited": total_requested,
        "unexposed_count": len(unexposed_pids),
        "exposed_count": len(exposed_pids),
        "unknown_count": len(unknown_pids),
        "unexposed_paper_ids": unexposed_pids,
        "exposed_paper_ids": exposed_pids,
        "unknown_paper_ids": unknown_pids,
        "exposures_by_experiment": {k: len(v) for k, v in exposure_by_experiment.items()},
        "questions_audited": len(question_ids) if question_ids else 0,
        "questions_exposed_count": len(q_exposed),
        "questions_exposed_details": q_exposed,
        "item_details": detailed_log
    }


def run_self_test():
    """Deterministic validation test using known fixtures."""
    print("[*] Running check_experiment_overlap self-test...")
    reg = load_registry()

    # 1. Known RQ3 exposed train paper
    known_rq3_paper = "1602.08741"  # Exposed in RQ3
    # 2. Known Seed pilot paper
    known_pilot_paper = "1512.03385" # Exposed in RQ5 Pilot (ResNet)
    # 3. Known Test paper evaluated in RQ4 Test
    known_test_paper = "1601.03313"  # In QASPER Test & RQ4 Test
    # 4. Known unexposed Train paper
    known_unexposed_paper = "1601.00901" # Unexposed Train candidate (eligible for RQ5)

    res = audit_cohort([known_unexposed_paper], reg)
    assert res["verdict"] == "PASS_UNEXPOSED", f"Expected PASS for {known_unexposed_paper}"
    assert res["unexposed_count"] == 1

    res_fail = audit_cohort([known_rq3_paper, known_pilot_paper, known_test_paper, known_unexposed_paper], reg)
    assert res_fail["verdict"] == "FAIL_EXPOSURE_DETECTED"
    assert res_fail["unexposed_count"] == 1
    assert res_fail["exposed_count"] == 3
    assert known_rq3_paper in res_fail["exposed_paper_ids"]
    assert known_pilot_paper in res_fail["exposed_paper_ids"]
    assert known_test_paper in res_fail["exposed_paper_ids"]

    print("[+] All self-test assertions PASSED successfully!")


def main():
    parser = argparse.ArgumentParser(description="Query paper/question overlap against Experiment Provenance Registry")
    parser.add_argument("--papers", nargs="*", help="Paper arXiv IDs to check")
    parser.add_argument("--manifest", type=str, help="Path to JSON manifest containing paper_arxiv_id or candidate_pool_paper_ids")
    parser.add_argument("--test", action="store_true", help="Run deterministic self-test")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.test:
        run_self_test()
        sys.exit(0)

    pids_to_check = []
    qids_to_check = []

    if args.papers:
        pids_to_check.extend(args.papers)

    if args.manifest:
        mpath = Path(args.manifest)
        if not mpath.exists():
            print(f"Error: manifest file {mpath} does not exist.")
            sys.exit(2)
        with open(mpath, "r", encoding="utf-8") as f:
            mdata = json.load(f)

        if isinstance(mdata, dict):
            # Check standard manifest schema
            if "selected_eval_items" in mdata:
                for item in mdata["selected_eval_items"]:
                    pids_to_check.append(item.get("paper_arxiv_id"))
                    qids_to_check.append(item.get("question_id"))
            elif "candidate_pool_paper_ids" in mdata:
                pids_to_check.extend(mdata["candidate_pool_paper_ids"])
            elif "paper_ids" in mdata:
                pids_to_check.extend(mdata["paper_ids"])
        elif isinstance(mdata, list):
            for item in mdata:
                if isinstance(item, dict):
                    pids_to_check.append(item.get("paper_arxiv_id") or item.get("paper_id"))
                    if item.get("question_id"):
                        qids_to_check.append(item.get("question_id"))
                elif isinstance(item, str):
                    pids_to_check.append(item)

    if not pids_to_check:
        parser.print_help()
        sys.exit(1)

    reg = load_registry()
    result = audit_cohort(pids_to_check, reg, qids_to_check if qids_to_check else None)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\n=======================================================")
        print(f"  EXPERIMENT PROVENANCE AUDIT REPORT: {result['verdict']}")
        print(f"=======================================================")
        print(f"Total Papers Audited : {result['total_papers_audited']}")
        print(f"  - Unexposed Papers : {result['unexposed_count']}")
        print(f"  - Exposed Papers   : {result['exposed_count']}")
        print(f"  - Unknown Papers   : {result['unknown_count']}")
        if result["questions_audited"]:
            print(f"Total Questions      : {result['questions_audited']}")
            print(f"  - Exposed Questions: {result['questions_exposed_count']}")

        if result["exposed_count"] > 0:
            print(f"\nExposures by Experiment:")
            for exp, count in result["exposures_by_experiment"].items():
                print(f"  * {exp}: {count} paper(s)")
            print(f"\nExposed Paper IDs: {result['exposed_paper_ids'][:20]}...")

        if result["unknown_count"] > 0:
            print(f"\nUnknown Paper IDs (not in registry): {result['unknown_paper_ids']}")

    sys.exit(0 if result["verdict"] == "PASS_UNEXPOSED" else 1)


if __name__ == "__main__":
    main()
