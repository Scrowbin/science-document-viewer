"""
QASPER Dataset Preparation & Exploratory Data Analysis (EDA) Harness (Option 1).
Fetches and standardizes scientific Q&A benchmark datasets (QASPER format),
performs comprehensive EDA on text statistics, filters out figure/table floats,
and freezes a stratified sample for reproducible RAG evaluations.

Outputs:
  - eval/prepared/sample_ids.json (Frozen stratified sample IDs)
  - eval/prepared/qasper_sampled.json (Processed query-evidence ground truth)
  - eval/prepared/eda_summary.json (Corpus text statistics & distribution)
"""

import argparse
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

# Candidate directories
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
EVAL_DIR = os.path.join(ROOT_DIR, "eval")
PREPARED_DIR = os.path.join(EVAL_DIR, "prepared")


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\w+", text.lower())


def run_exploratory_data_analysis(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs Exploratory Data Analysis (EDA) over benchmark scientific QA pairs:
      1. Question type distribution (extractive, abstractive, yes_no, unanswerable).
      2. Evidence stats: text evidence vs figure/table floats (FLOAT SELECTED).
      3. Evidence token length distribution (min, max, mean, p50).
      4. Question-evidence lexical token overlap (Jaccard similarity).
    """
    total_q = len(records)
    if total_q == 0:
        return {"total_questions": 0}

    q_types: Counter = Counter()
    papers: Set[str] = set()
    ev_lengths: List[int] = []
    lexical_overlaps: List[float] = []
    float_selected_count = 0
    unanswerable_count = 0

    for rec in records:
        qid = rec.get("id", "")
        pid = rec.get("paper_arxiv_id", "") or rec.get("paper_id", "")
        if pid:
            papers.add(pid)

        q_type = rec.get("question_type", "factoid")
        q_types[q_type] += 1

        if q_type == "unanswerable":
            unanswerable_count += 1
            continue

        q_text = rec.get("question", "")
        ev_text = rec.get("expected_answer", "") or rec.get("verbatim_evidence_quote", "")

        # Check for figure/table float selection
        if ev_text.startswith("FLOAT SELECTED") or rec.get("is_float_evidence", False):
            float_selected_count += 1
            continue

        q_toks = set(tokenize(q_text))
        ev_toks = tokenize(ev_text)
        ev_lengths.append(len(ev_toks))

        if q_toks and ev_toks:
            ev_tok_set = set(ev_toks)
            overlap = len(q_toks & ev_tok_set) / max(1, len(q_toks | ev_tok_set))
            lexical_overlaps.append(overlap)

    ev_lengths.sort()
    avg_ev_len = round(sum(ev_lengths) / max(1, len(ev_lengths)), 1)
    p50_ev_len = ev_lengths[len(ev_lengths) // 2] if ev_lengths else 0
    max_ev_len = max(ev_lengths) if ev_lengths else 0
    min_ev_len = min(ev_lengths) if ev_lengths else 0

    avg_overlap = round(sum(lexical_overlaps) / max(1, len(lexical_overlaps)), 3)

    return {
        "total_questions": total_q,
        "unique_papers": len(papers),
        "question_type_distribution": dict(q_types),
        "unanswerable_count": unanswerable_count,
        "unanswerable_pct": round((unanswerable_count / total_q) * 100, 1),
        "float_selected_count": float_selected_count,
        "float_selected_pct": round((float_selected_count / total_q) * 100, 1),
        "text_evidence_questions": len(ev_lengths),
        "evidence_tokens": {
            "min": min_ev_len,
            "max": max_ev_len,
            "mean": avg_ev_len,
            "p50": p50_ev_len,
        },
        "mean_question_evidence_lexical_overlap": avg_overlap,
    }


def prepare_benchmark_dataset(
    input_path: Optional[str] = None,
    output_dir: str = PREPARED_DIR,
    sample_size: int = 50,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Standardizes benchmark records, applies stratified sampling,
    excludes pure float figures/tables, and freezes sample into output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Use seed benchmark as default seed records
    default_input = os.path.join(BACKEND_DIR, "data", "eval_benchmark_seed.json")
    src_file = input_path or default_input

    if not os.path.exists(src_file):
        raise FileNotFoundError(f"Input benchmark file not found: {src_file}")

    with open(src_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"\n[QASPER-PREP] Loaded {len(records)} candidate questions from {src_file}")

    # 1. Run EDA on raw records
    eda_stats = run_exploratory_data_analysis(records)

    print("\n[EDA-STATS] Exploratory Data Analysis Results:")
    print("=" * 75)
    print(f"  * Total Questions:              {eda_stats['total_questions']}")
    print(f"  * Unique Papers:                {eda_stats['unique_papers']}")
    print(f"  * Question Type Mix:            {eda_stats['question_type_distribution']}")
    print(f"  * Unanswerable Questions:       {eda_stats['unanswerable_count']} ({eda_stats['unanswerable_pct']}%)")
    print(f"  * Float (Table/Figure) Excluded:{eda_stats['float_selected_count']} ({eda_stats['float_selected_pct']}%)")
    print(f"  * Text Evidence Tokens:         Mean: {eda_stats['evidence_tokens']['mean']}, P50: {eda_stats['evidence_tokens']['p50']}")
    print(f"  * Lexical Question-Ev Overlap:  {eda_stats['mean_question_evidence_lexical_overlap']}")
    print("=" * 75)

    # 2. Filter out pure float evidence
    filtered_records: List[Dict[str, Any]] = []
    for r in records:
        ev = r.get("expected_answer", "") or r.get("verbatim_evidence_quote", "")
        if ev.startswith("FLOAT SELECTED") or r.get("is_float_evidence", False):
            continue
        filtered_records.append(r)

    # 3. Stratified sampling with fixed seed
    rng = random.Random(seed)
    if len(filtered_records) > sample_size:
        sampled_records = rng.sample(filtered_records, sample_size)
    else:
        sampled_records = list(filtered_records)

    sampled_ids = [r.get("id") for r in sampled_records if r.get("id")]

    # 4. Save frozen files
    sample_ids_path = os.path.join(output_dir, "sample_ids.json")
    dataset_path = os.path.join(output_dir, "qasper_sampled.json")
    eda_path = os.path.join(output_dir, "eda_summary.json")

    with open(sample_ids_path, "w", encoding="utf-8") as f:
        json.dump({"sample_size": len(sampled_ids), "seed": seed, "ids": sampled_ids}, f, indent=2)

    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(sampled_records, f, indent=2)

    with open(eda_path, "w", encoding="utf-8") as f:
        json.dump(eda_stats, f, indent=2)

    print(f"[QASPER-PREP] Exported frozen sample artifacts to: {output_dir}")
    print(f"  * Sample IDs: {sample_ids_path}")
    print(f"  * Dataset:    {dataset_path}")
    print(f"  * EDA stats:  {eda_path}")

    return {
        "eda": eda_stats,
        "sample_size": len(sampled_records),
        "paths": {
            "sample_ids": sample_ids_path,
            "dataset": dataset_path,
            "eda": eda_path,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="QASPER Dataset Preparation & EDA Harness.")
    parser.add_argument(
        "--input",
        default=None,
        help="Path to input benchmark JSON (defaults to eval_benchmark_seed.json)",
    )
    parser.add_argument(
        "--output-dir",
        default=PREPARED_DIR,
        help="Directory to store frozen prepared datasets",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=50,
        help="Number of questions in frozen sample (default: 50)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic sampling",
    )
    args = parser.parse_args()

    prepare_benchmark_dataset(
        input_path=args.input,
        output_dir=args.output_dir,
        sample_size=args.sample_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
