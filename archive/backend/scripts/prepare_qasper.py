"""
QASPER Dataset Preparation & Exploratory Data Analysis (EDA) Harness (Option 1).
Fetches and standardizes scientific Q&A benchmark datasets (QASPER format),
performs comprehensive EDA on text statistics, filters out figure/table floats,
and freezes a stratified sample for reproducible RAG evaluations.

Outputs:
  - eval/prepared/sample_ids.json (Frozen stratified sample IDs)
  - eval/prepared/qasper_sampled.json (Processed query-evidence ground truth)
  - eval/prepared/qasper_corpus.json (Structured paper sections & corpus text)
  - eval/prepared/eda_summary.json (Corpus text statistics & distribution)
  - eval/prepared/human_review_needed.json (Flagged questions requiring human inspection)
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
from typing import Any, Dict, List, Optional, Set, Tuple

# Candidate directories
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
EVAL_DIR = os.path.join(ROOT_DIR, "eval")
DATA_DIR = os.path.join(EVAL_DIR, "data")
PREPARED_DIR = os.path.join(EVAL_DIR, "prepared")

HF_QASPER_URL = "https://datasets-server.huggingface.co/rows?dataset=allenai%2Fqasper&config=qasper&split=validation&offset=0&limit=100"


def clean_text(s: str) -> str:
    """Normalize whitespace and strip extraneous control characters."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    return re.findall(r"\w+", text.lower())


def extract_keywords(text: str, max_kws: int = 8) -> List[str]:
    """Extract informative non-stopword keywords from text."""
    stopwords = {
        "a", "an", "the", "in", "on", "of", "for", "to", "is", "are", "was",
        "were", "and", "or", "that", "this", "it", "by", "with", "from", "as",
        "what", "how", "why", "which", "does", "did", "do", "we", "our", "their",
        "at", "be", "have", "has", "had", "not", "but", "also", "then", "into",
        "more", "such", "than", "used", "using", "paper", "model", "approach"
    }
    words = re.findall(r"[A-Za-z0-9_\-\$]{3,}", text.lower())
    counts = Counter(w for w in words if w not in stopwords)
    return [w for w, _ in counts.most_common(max_kws)]


def fetch_qasper_from_hf(
    cache_path: Optional[str] = None,
    timeout: int = 45,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """
    Streams QASPER validation papers from the Hugging Face datasets server.
    Caches raw rows locally to avoid repeated network overhead.
    """
    import requests

    if cache_path and os.path.exists(cache_path):
        print(f"[QASPER-PREP] Loading cached raw QASPER rows from: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"[QASPER-PREP] Streaming QASPER dataset from Hugging Face server ({HF_QASPER_URL})...")
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(HF_QASPER_URL, timeout=timeout)
            if r.status_code == 200:
                data = r.json()
                rows = [row_obj.get("row", {}) for row_obj in data.get("rows", [])]
                print(f"[QASPER-PREP] Successfully retrieved {len(rows)} paper rows (HTTP 200).")
                if cache_path:
                    os.makedirs(os.path.dirname(os.path.abspath(cache_path)), exist_ok=True)
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(rows, f, indent=2)
                    print(f"[QASPER-PREP] Cached raw rows to: {cache_path}")
                return rows
            else:
                print(f"[QASPER-PREP] [WARNING] Attempt {attempt}: HTTP {r.status_code}: {r.text[:200]}")
        except Exception as exc:
            print(f"[QASPER-PREP] [WARNING] Attempt {attempt} failed: {exc}")
        time.sleep(2)

    raise ConnectionError(f"Failed to fetch QASPER rows from Hugging Face after {max_retries} attempts.")


def process_qasper_rows(
    raw_rows: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
    """
    Transforms raw QASPER rows into:
      1. Standardized query-evidence ground-truth records.
      2. Structured paper corpus with section headings and paragraphs.
      3. Flagged review items requiring human inspection.
    """
    records: List[Dict[str, Any]] = []
    corpus_papers: Dict[str, Any] = {}
    human_review_items: List[Dict[str, Any]] = []

    for row_idx, row in enumerate(raw_rows):
        paper_id = row.get("id", f"paper_{row_idx:03d}")
        title = clean_text(row.get("title", ""))
        abstract = clean_text(row.get("abstract", ""))
        full_text = row.get("full_text", {})

        # 1. Parse structured sections for this paper
        sec_names = full_text.get("section_name", [])
        sec_paras = full_text.get("paragraphs", [])
        paper_sections: List[Dict[str, Any]] = []

        for s_idx, sname in enumerate(sec_names):
            paras = sec_paras[s_idx] if s_idx < len(sec_paras) else []
            clean_paras = [clean_text(p) for p in paras if clean_text(p)]
            combined_text = "\n\n".join(clean_paras)
            if combined_text:
                paper_sections.append({
                    "title": clean_text(sname),
                    "text": combined_text,
                    "paragraphs": clean_paras,
                    "page_start": 1,
                    "page_end": 1,
                })

        corpus_papers[paper_id] = {
            "paper_arxiv_id": paper_id,
            "paper_title": title,
            "abstract": abstract,
            "sections": paper_sections,
        }

        # 2. Process QA pairs
        qas = row.get("qas", {})
        questions = qas.get("question", [])
        q_ids = qas.get("question_id", [])
        answers_list = qas.get("answers", [])

        for q_idx, q_text in enumerate(questions):
            raw_qid = q_ids[q_idx] if q_idx < len(q_ids) else f"{paper_id}_q{q_idx+1:02d}"
            clean_q = clean_text(q_text)
            ans_objs = answers_list[q_idx].get("answer", []) if q_idx < len(answers_list) else []

            # Check annotator votes
            unans_count = sum(1 for a in ans_objs if a.get("unanswerable", False))
            ans_count = len(ans_objs)
            is_majority_unans = (unans_count > ans_count / 2) if ans_count else False
            is_split_vote = (0 < unans_count < ans_count)

            # Determine question type
            q_type = "factoid"
            if is_majority_unans:
                q_type = "unanswerable"
            else:
                yes_no_count = sum(1 for a in ans_objs if a.get("yes_no") is not None)
                extractive_count = sum(1 for a in ans_objs if a.get("extractive_spans") and not a.get("free_form_answer"))
                abstractive_count = sum(1 for a in ans_objs if a.get("free_form_answer") and not a.get("extractive_spans"))
                if yes_no_count > 0:
                    q_type = "yes_no"
                elif extractive_count >= abstractive_count and extractive_count > 0:
                    q_type = "extractive"
                elif abstractive_count > 0:
                    q_type = "abstractive"

            # Aggregate evidence & answers across annotators
            all_evidence: List[str] = []
            highlighted: List[str] = []
            expected_answers: List[str] = []
            has_float = False

            for a in ans_objs:
                if a.get("unanswerable", False):
                    continue
                for ev in a.get("evidence", []):
                    ev_clean = clean_text(ev)
                    if "FLOAT SELECTED" in ev_clean:
                        has_float = True
                    elif ev_clean and ev_clean not in all_evidence:
                        all_evidence.append(ev_clean)
                for hl in a.get("highlighted_evidence", []):
                    hl_clean = clean_text(hl)
                    if hl_clean and hl_clean not in highlighted:
                        highlighted.append(hl_clean)
                if a.get("free_form_answer"):
                    expected_answers.append(clean_text(a["free_form_answer"]))
                elif a.get("extractive_spans"):
                    expected_answers.extend([clean_text(s) for s in a["extractive_spans"]])
                elif a.get("yes_no") is not None:
                    expected_answers.append("Yes" if a["yes_no"] else "No")

            # Filter out questions where evidence is exclusively table/figure floats
            if not all_evidence and has_float:
                continue
            if not all_evidence and q_type != "unanswerable":
                continue

            # Identify target section from the paper's structured text
            target_section = "Introduction"
            primary_quote = highlighted[0] if highlighted else (all_evidence[0] if all_evidence else "")
            if primary_quote:
                found_sec = None
                for sec in paper_sections:
                    for para in sec["paragraphs"]:
                        if primary_quote[:50].lower() in para.lower():
                            found_sec = sec["title"]
                            break
                    if found_sec:
                        break
                if found_sec:
                    target_section = found_sec

            kws = extract_keywords(f"{clean_q} {' '.join(all_evidence)}")

            rec = {
                "id": f"Q_QASP_{len(records)+1:03d}",
                "original_id": raw_qid,
                "paper_arxiv_id": paper_id,
                "paper_title": title,
                "question": clean_q,
                "question_type": q_type,
                "expected_answer": " | ".join(expected_answers) if expected_answers else ("This information is not provided in the paper." if q_type == "unanswerable" else ""),
                "verbatim_evidence_quote": primary_quote,
                "evidence_list": all_evidence,
                "highlighted_evidence": highlighted,
                "target_section": target_section,
                "target_page": 1,
                "evidence_keywords": kws,
                "annotators_count": ans_count,
                "unanswerable_votes": unans_count,
            }
            records.append(rec)

            # Flag edge cases for human review
            if is_split_vote:
                human_review_items.append({
                    "type": "annotator_split",
                    "question_id": rec["id"],
                    "paper_id": paper_id,
                    "paper_title": title,
                    "question": clean_q,
                    "issue": f"{unans_count} of {ans_count} annotators voted unanswerable; resolved as '{q_type}'.",
                    "evidence_preview": primary_quote[:180],
                })
            elif q_type == "unanswerable":
                human_review_items.append({
                    "type": "unanswerable_consensus",
                    "question_id": rec["id"],
                    "paper_id": paper_id,
                    "paper_title": title,
                    "question": clean_q,
                    "issue": "Unanswerable consensus query (reserved for abstention benchmark).",
                    "evidence_preview": "N/A",
                })
            elif len(tokenize(primary_quote)) < 10:
                human_review_items.append({
                    "type": "short_evidence",
                    "question_id": rec["id"],
                    "paper_id": paper_id,
                    "paper_title": title,
                    "question": clean_q,
                    "issue": f"Evidence is very brief ({len(tokenize(primary_quote))} tokens).",
                    "evidence_preview": primary_quote,
                })

    return records, corpus_papers, human_review_items


def run_exploratory_data_analysis(
    records: List[Dict[str, Any]],
    raw_total_questions: int,
    float_excluded_count: int,
) -> Dict[str, Any]:
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
    unanswerable_count = 0

    for rec in records:
        pid = rec.get("paper_arxiv_id", "")
        if pid:
            papers.add(pid)

        q_type = rec.get("question_type", "factoid")
        q_types[q_type] += 1

        if q_type == "unanswerable":
            unanswerable_count += 1
            continue

        q_text = rec.get("question", "")
        ev_text = rec.get("verbatim_evidence_quote", "") or rec.get("expected_answer", "")

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
        "raw_total_questions": raw_total_questions,
        "valid_benchmark_questions": total_q,
        "unique_papers": len(papers),
        "question_type_distribution": dict(q_types),
        "unanswerable_count": unanswerable_count,
        "unanswerable_pct": round((unanswerable_count / total_q) * 100, 1),
        "float_selected_count": float_excluded_count,
        "float_selected_pct": round((float_excluded_count / max(1, raw_total_questions)) * 100, 1),
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
    sample_size: int = 250,
    seed: int = 42,
    cache_dir: str = DATA_DIR,
) -> Dict[str, Any]:
    """
    Standardizes benchmark records, applies stratified sampling,
    excludes pure float figures/tables, and freezes sample into output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    cache_file = os.path.join(cache_dir, "qasper_raw.json")

    # 1. Acquire raw records
    if input_path and os.path.exists(input_path):
        print(f"[QASPER-PREP] Loading candidate questions from input path: {input_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if isinstance(raw_data, list) and raw_data and "qas" in raw_data[0]:
                raw_rows = raw_data
            else:
                raw_rows = []
    else:
        raw_rows = fetch_qasper_from_hf(cache_path=cache_file)

    # 2. Process rows into structured benchmarks
    records, corpus_papers, human_review_items = process_qasper_rows(raw_rows)

    raw_total_q = sum(len(r.get("qas", {}).get("question", [])) for r in raw_rows)
    float_excluded = raw_total_q - len(records)

    # 3. Stratified sampling with fixed seed if requested
    rng = random.Random(seed)
    if len(records) > sample_size:
        # Stratify by question type
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            by_type.setdefault(r["question_type"], []).append(r)

        sampled_records: List[Dict[str, Any]] = []
        for q_type, type_recs in by_type.items():
            type_sample_count = max(1, int(len(type_recs) * (sample_size / len(records))))
            sampled_records.extend(rng.sample(type_recs, min(len(type_recs), type_sample_count)))

        # Fill remaining slots up to sample_size
        remaining = [r for r in records if r not in sampled_records]
        if len(sampled_records) < sample_size and remaining:
            sampled_records.extend(rng.sample(remaining, min(len(remaining), sample_size - len(sampled_records))))
        sampled_records.sort(key=lambda x: x["id"])
    else:
        sampled_records = list(records)

    # 4. Run EDA over final benchmark records
    eda_stats = run_exploratory_data_analysis(
        sampled_records,
        raw_total_questions=raw_total_q,
        float_excluded_count=float_excluded,
    )

    print("\n[EDA-STATS] Exploratory Data Analysis Results:")
    print("=" * 80)
    print(f"  * Raw Questions in Stream:      {eda_stats['raw_total_questions']}")
    print(f"  * Valid Ground-Truth QA:        {eda_stats['valid_benchmark_questions']}")
    print(f"  * Unique Papers:                {eda_stats['unique_papers']}")
    print(f"  * Question Type Mix:            {eda_stats['question_type_distribution']}")
    print(f"  * Unanswerable Questions:       {eda_stats['unanswerable_count']} ({eda_stats['unanswerable_pct']}%)")
    print(f"  * Pure Float Figures/Tables:    {eda_stats['float_selected_count']} ({eda_stats['float_selected_pct']}%)")
    print(f"  * Text Evidence Tokens:         Mean: {eda_stats['evidence_tokens']['mean']}, P50: {eda_stats['evidence_tokens']['p50']}")
    print(f"  * Lexical Question-Ev Overlap:  {eda_stats['mean_question_evidence_lexical_overlap']}")
    print("=" * 80)

    sampled_ids = [r.get("id") for r in sampled_records if r.get("id")]

    # 5. Save frozen artifacts
    sample_ids_path = os.path.join(output_dir, "sample_ids.json")
    dataset_path = os.path.join(output_dir, "qasper_sampled.json")
    corpus_path = os.path.join(output_dir, "qasper_corpus.json")
    eda_path = os.path.join(output_dir, "eda_summary.json")
    review_path = os.path.join(output_dir, "human_review_needed.json")

    with open(sample_ids_path, "w", encoding="utf-8") as f:
        json.dump({"sample_size": len(sampled_ids), "seed": seed, "ids": sampled_ids}, f, indent=2)

    with open(dataset_path, "w", encoding="utf-8") as f:
        json.dump(sampled_records, f, indent=2)

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus_papers, f, indent=2)

    with open(eda_path, "w", encoding="utf-8") as f:
        json.dump(eda_stats, f, indent=2)

    with open(review_path, "w", encoding="utf-8") as f:
        json.dump({
            "total_flagged": len(human_review_items),
            "annotator_split_count": sum(1 for x in human_review_items if x["type"] == "annotator_split"),
            "unanswerable_count": sum(1 for x in human_review_items if x["type"] == "unanswerable_consensus"),
            "short_evidence_count": sum(1 for x in human_review_items if x["type"] == "short_evidence"),
            "items": human_review_items,
        }, f, indent=2)

    print(f"\n[QASPER-PREP] Exported frozen sample artifacts to: {output_dir}")
    print(f"  * Sample IDs:           {sample_ids_path}")
    print(f"  * Dataset (QA Gold):    {dataset_path}")
    print(f"  * Corpus (Full Text):   {corpus_path}")
    print(f"  * EDA stats:            {eda_path}")
    print(f"  * Human Review Flagged: {review_path} ({len(human_review_items)} items)")

    return {
        "eda": eda_stats,
        "sample_size": len(sampled_records),
        "paths": {
            "sample_ids": sample_ids_path,
            "dataset": dataset_path,
            "corpus": corpus_path,
            "eda": eda_path,
            "review": review_path,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="QASPER Dataset Preparation & EDA Harness.")
    parser.add_argument(
        "--input",
        default=None,
        help="Path to input benchmark JSON or raw QASPER file (if none, streams from HF)",
    )
    parser.add_argument(
        "--output-dir",
        default=PREPARED_DIR,
        help="Directory to store frozen prepared datasets",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=250,
        help="Target number of questions in frozen sample (default: 250)",
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
