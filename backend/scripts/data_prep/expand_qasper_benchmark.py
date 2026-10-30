"""
Step 3 Statistical Power Expansion: QASPER Benchmark Scaling (Workstream 4).
Scales the held-out evaluation corpus from 48 papers (N=114 queries)
to K = 160 papers (N = 487 answerable queries; 78.3%-85.5% power at observed delta >= 0.049,
38.6% power at prespecified SESOI = 0.030 under paper-cluster resampling).

Guarantees:
  1. Preserves the original 48 Held-Out papers (114 queries) strictly intact as 'Frozen Cohort 1'.
  2. Strictly excludes all 48 Dev papers to avoid data snooping.
  3. Filters for answerable questions with non-float evidence spans.
  4. Generates:
     - eval/prepared/expanded_held_out_split.json
     - eval/prepared/expanded_corpus.json
     - eval/prepared/expanded_qasper_sampled.json
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import requests

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from prepare_qasper import clean_text, process_qasper_rows

SPLIT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
CORPUS_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
SAMPLED_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"
RAW_CACHE_PATH = WORKSPACE_ROOT / "eval" / "data" / "qasper_raw.json"

EXPANDED_SPLIT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_held_out_split.json"
EXPANDED_CORPUS_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_corpus.json"
EXPANDED_SAMPLED_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_qasper_sampled.json"

HF_BASE_URL = "https://datasets-server.huggingface.co/rows?dataset=allenai%2Fqasper&config=qasper"


def fetch_extra_qasper_rows(existing_aids: Set[str], target_extra_papers: int = 120) -> List[Dict[str, Any]]:
    """Fetches additional QASPER papers from Hugging Face dataset splits without duplicating existing papers."""
    collected_rows: List[Dict[str, Any]] = []
    seen_ids = set(existing_aids)

    # 1. First check if cached raw rows have extra papers
    if RAW_CACHE_PATH.exists():
        try:
            with open(RAW_CACHE_PATH, "r", encoding="utf-8") as f:
                raw_rows = json.load(f)
            for r in raw_rows:
                aid = r.get("id")
                if aid and aid not in seen_ids:
                    collected_rows.append(r)
                    seen_ids.add(aid)
            print(f"[EXPAND] Found {len(collected_rows)} extra candidate papers from local raw cache.")
        except Exception as e:
            print(f"[EXPAND] Note reading raw cache: {e}")

    # 2. If needed, stream from train split via HF API
    if len(collected_rows) < target_extra_papers:
        needed = target_extra_papers - len(collected_rows)
        print(f"[EXPAND] Streaming {needed} additional papers from Hugging Face train split...")
        splits_to_try = [("train", 0), ("train", 100), ("train", 200)]

        for split_name, offset in splits_to_try:
            if len(collected_rows) >= target_extra_papers:
                break
            url = f"{HF_BASE_URL}&split={split_name}&offset={offset}&limit=100"
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200:
                    data = r.json()
                    rows = [row_obj.get("row", {}) for row_obj in data.get("rows", [])]
                    for r_obj in rows:
                        aid = r_obj.get("id")
                        if aid and aid not in seen_ids:
                            collected_rows.append(r_obj)
                            seen_ids.add(aid)
                            if len(collected_rows) >= target_extra_papers:
                                break
                    print(f"  Streamed {len(rows)} rows from {split_name} (offset={offset}). Total collected: {len(collected_rows)}")
                time.sleep(1)
            except Exception as exc:
                print(f"  [WARN] Failed to stream from {url}: {exc}")

    return collected_rows


def main():
    parser = argparse.ArgumentParser(description="Expand QASPER Held-Out Benchmark for High Statistical Power")
    parser.add_argument("--target-total-papers", type=int, default=160, help="Target total papers in expanded held-out split")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic sampling")
    args = parser.parse_args()

    random.seed(args.seed)

    print("=== EXPANDING HELD-OUT QASPER BENCHMARK (HIGH STATISTICAL POWER) ===")
    with open(SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    dev_papers = set(split_data.get("dev_papers", []))
    frozen_held_out = list(split_data.get("held_out_papers", []))

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)

    with open(SAMPLED_PATH, "r", encoding="utf-8") as f:
        qa_all = json.load(f)

    frozen_queries = [q for q in qa_all if q.get("paper_arxiv_id") in set(frozen_held_out) and q.get("question_type") != "unanswerable"]

    print(f"Frozen Cohort 1: {len(frozen_held_out)} papers, {len(frozen_queries)} answerable queries.")
    print(f"Dev Exclusion Set: {len(dev_papers)} papers.")

    target_extra = max(0, args.target_total_papers - len(frozen_held_out))
    existing_all = dev_papers.union(set(frozen_held_out))

    raw_candidates = fetch_extra_qasper_rows(existing_all, target_extra_papers=target_extra * 2)

    # Process candidate rows
    extra_records, extra_corpus, _ = process_qasper_rows(raw_candidates)

    # Filter answerable queries with valid non-float evidence
    extra_answerable = [
        q for q in extra_records
        if q.get("question_type") != "unanswerable" and q.get("verbatim_evidence_quote") and not q.get("is_float_only_evidence")
    ]

    # Group by paper
    paper_query_map: Dict[str, List[Dict[str, Any]]] = {}
    for q in extra_answerable:
        aid = q["paper_arxiv_id"]
        paper_query_map.setdefault(aid, []).append(q)

    # Filter papers with at least 1 valid query and substantial corpus
    valid_extra_papers = [
        aid for aid, q_list in paper_query_map.items()
        if aid in extra_corpus and len(extra_corpus[aid].get("sections", [])) >= 2
    ]

    random.shuffle(valid_extra_papers)
    selected_extra_papers = valid_extra_papers[:target_extra]

    cohort_2_queries: List[Dict[str, Any]] = []
    cohort_2_corpus: Dict[str, Any] = {}
    for aid in selected_extra_papers:
        cohort_2_queries.extend(paper_query_map[aid])
        cohort_2_corpus[aid] = extra_corpus[aid]

    # Combine into Expanded Benchmark
    expanded_held_out_papers = frozen_held_out + selected_extra_papers
    expanded_corpus = dict(corpus_all)
    expanded_corpus.update(cohort_2_corpus)

    expanded_queries = frozen_queries + cohort_2_queries

    print(f"\nExpanded Benchmark Created:")
    print(f"  Frozen Cohort 1 Papers: {len(frozen_held_out)} ({len(frozen_queries)} queries)")
    print(f"  Added Cohort 2 Papers:  {len(selected_extra_papers)} ({len(cohort_2_queries)} queries)")
    print(f"  Total Expanded Papers:  {len(expanded_held_out_papers)}")
    print(f"  Total Expanded Queries: {len(expanded_queries)}")

    # Statistical power note (Rigorous Audit 2026-10-17):
    # Historical note: An unvalidated heuristic formula `26.3 * (n_k / 48) ** 0.85`
    # was previously used to roughly extrapolate power, producing 73.2% - 82.5%.
    # Full cluster-resampling Monte Carlo simulation (audit_and_correct_statistics.py)
    # reveals:
    # 1. At prespecified SESOI = 0.030, cluster-level power is 38.6% (+/- 1.09%).
    # 2. At the observed effect size (Delta = +0.0493 query / +0.0555 paper),
    #    cluster-level power is 78.3% - 85.5%.
    # 3. Achieving >= 80% power at SESOI = 0.030 requires K ≈ 500 paper clusters.
    n_k = len(expanded_held_out_papers)

    # Serialize artifacts
    split_payload = {
        "benchmark": "Expanded High-Power Held-Out Split",
        "date": "2026-10-17",
        "seed": args.seed,
        "frozen_cohort_1_papers": frozen_held_out,
        "cohort_2_papers": selected_extra_papers,
        "total_held_out_papers": len(expanded_held_out_papers),
        "total_answerable_queries": len(expanded_queries),
        "statistical_power_audit": {
            "power_at_prespecified_sesoi_0_030": "38.6% (MC 95% CI [36.5%, 40.7%])",
            "power_at_observed_delta_0_0493": "78.3% (MC 95% CI [76.5%, 80.1%])",
            "power_at_observed_delta_0_0555": "85.5% (MC 95% CI [84.0%, 87.1%])",
            "required_k_for_80pct_power_at_0_030": "~500 papers",
            "historical_heuristic_warning": "Deprecated heuristic `26.3 * (n_k/48)**0.85` replaced with Monte Carlo cluster simulation in audit_and_correct_statistics.py",
        },
        "held_out_papers": expanded_held_out_papers,
    }

    with open(EXPANDED_SPLIT_PATH, "w", encoding="utf-8") as f:
        json.dump(split_payload, f, indent=2)

    with open(EXPANDED_CORPUS_PATH, "w", encoding="utf-8") as f:
        json.dump(expanded_corpus, f, indent=2)

    with open(EXPANDED_SAMPLED_PATH, "w", encoding="utf-8") as f:
        json.dump(expanded_queries, f, indent=2)

    print(f"\n[SUCCESS] Saved Expanded Split to: {EXPANDED_SPLIT_PATH.relative_to(WORKSPACE_ROOT)}")
    print(f"[SUCCESS] Saved Expanded Corpus to: {EXPANDED_CORPUS_PATH.relative_to(WORKSPACE_ROOT)}")
    print(f"[SUCCESS] Saved Expanded Queries to: {EXPANDED_SAMPLED_PATH.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()
