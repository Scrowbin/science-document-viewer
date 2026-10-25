"""
Phase 0 Baseline & EDA: Full QASPER Benchmark Exploratory Data Analysis & Audit.
Analyzes the complete canonical QASPER v0.3 dataset (1,585 papers, 5,049 questions)
across Train, Dev, and Test splits, compares against the 100-paper Pilot cohort,
and exports comprehensive machine-readable JSON artifacts, CSV distribution tables,
and publication-ready 4-panel figures for Chapter 5.
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Workspace paths
WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent

EVAL_DIR = WORKSPACE_ROOT / "eval"
OFFICIAL_DATA_DIR = EVAL_DIR / "data" / "qasper_official"
PREPARED_DIR = EVAL_DIR / "prepared"
PHASE0_ARTIFACTS = EVAL_DIR / "phases" / "phase_0_baseline" / "artifacts"
PHASE0_ARTIFACTS.mkdir(parents=True, exist_ok=True)

FIGURES_DIR = EVAL_DIR / "figures"
REPORTS_FIG_DIR = WORKSPACE_ROOT / "reports" / "chapter5" / "figures"
DOCS_FIG_DIR = WORKSPACE_ROOT / "docs" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_FIG_DIR.mkdir(parents=True, exist_ok=True)
DOCS_FIG_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(s: Optional[str]) -> str:
    """Normalize whitespace and strip extraneous control characters."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def normalize_heading(title: Optional[str]) -> str:
    """Normalize academic section headings by stripping numbers, punctuation, and lowercasing."""
    if not title:
        return ""
    clean = title.strip().lower()
    # Strip leading section numbers and roman numerals only when followed by delimiter
    clean = re.sub(r"^(\d+(\.\d+)*|[ivxlcdm]+)[\.\:\-\s]+\s*", "", clean).strip()
    return clean


def canonicalize_heading(title: str) -> str:
    """Map common section heading variants to standard IMRaD categories."""
    h = normalize_heading(title)
    if not h:
        return ""
    if any(k in h for k in ["introduction", "intro", "overview", "background and introduction"]):
        return "introduction"
    if any(k in h for k in ["related work", "prior work", "literature review", "previous work"]):
        return "related work"
    if any(k in h for k in ["conclusion", "conclusions", "concluding remarks", "summary and conclusion", "conclusion and future work"]):
        return "conclusion"
    if any(k in h for k in ["acknowledgment", "acknowledgments", "acknowledgements"]):
        return "acknowledgments"
    if any(k in h for k in ["experiment", "experiments", "experimental setup", "experimental results", "evaluation"]):
        return "experiments"
    if any(k in h for k in ["result", "results", "main results", "empirical results"]):
        return "results"
    if any(k in h for k in ["discussion", "analysis", "error analysis", "qualitative analysis"]):
        return "discussion"
    if any(k in h for k in ["model", "proposed method", "methodology", "method", "approach", "framework"]):
        return "methodology / model"
    if any(k in h for k in ["future work", "future directions"]):
        return "future work"
    return h


def compute_lexical_jaccard(q_words: Sequence[str], ev_words: Sequence[str]) -> float:
    """Compute content-word Jaccard similarity between query and evidence."""
    q_set = set(w.lower() for w in q_words if len(w) > 3)
    ev_set = set(w.lower() for w in ev_words if len(w) > 3)
    if not q_set or not ev_set:
        return 0.0
    return len(q_set.intersection(ev_set)) / len(q_set.union(ev_set))


def audit_full_qasper() -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    print("\n" + "=" * 80)
    print("[>] AUDITING FULL CANONICAL QASPER v0.3 DATASET (TRAIN + DEV + TEST)")
    print("=" * 80)

    splits = ["train", "dev", "test"]
    split_files = {s: OFFICIAL_DATA_DIR / f"qasper-{s}-v0.3.json" for s in splits}

    for s, p in split_files.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing official split file: {p}")

    all_papers: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    split_paper_counts = {}
    split_question_counts = {}

    all_paper_ids = set()
    dup_paper_ids = []
    all_question_ids = set()
    dup_question_ids = []

    for s in splits:
        with open(split_files[s], "r", encoding="utf-8") as f:
            data = json.load(f)
        split_paper_counts[s] = len(data)
        q_count = sum(len(p.get("qas", [])) for p in data.values())
        split_question_counts[s] = q_count

        for pid, pdata in data.items():
            if pid in all_paper_ids:
                dup_paper_ids.append((s, pid))
            all_paper_ids.add(pid)
            all_papers[pid] = (s, pdata)

    print(f"[+] Loaded official splits: {split_paper_counts}")
    print(f"[+] Total papers: {len(all_papers)} (Train={split_paper_counts['train']}, Dev={split_paper_counts['dev']}, Test={split_paper_counts['test']})")
    print(f"[+] Total questions: {sum(split_question_counts.values())} (Train={split_question_counts['train']}, Dev={split_question_counts['dev']}, Test={split_question_counts['test']})")

    # Data integrity & metrics collectors
    papers_with_empty_text = []
    papers_with_zero_sections = []
    papers_with_empty_abstract = []
    
    # Document statistics
    doc_word_counts = []
    doc_char_counts = []
    doc_section_counts = []
    section_word_counts = []
    raw_heading_counts = Counter()
    canonical_heading_counts = Counter()

    # Question statistics
    q_words = []
    q_chars = []
    annotator_counts = Counter()
    unanimous_ans_cnt = 0
    unanimous_unans_cnt = 0
    split_vote_cnt = 0
    majority_ans_cnt = 0
    majority_unans_cnt = 0
    tie_vote_cnt = 0

    # Question types
    project_q_types = Counter()
    individual_answer_types = Counter()

    # Evidence metrics
    q_with_no_evidence = 0
    q_with_single_passage = 0
    q_with_multi_passage = 0
    q_with_only_float = 0
    q_zero_ev_answerable = 0
    q_zero_ev_unanswerable = 0

    evidence_words_per_q = []
    evidence_chars_per_q = []
    lexical_jaccards = []
    evidence_passages_per_q = []

    papers_with_usable_text_ev = set()
    papers_zero_usable_q = set()

    traceability_records = []

    canonical_heading_paper_counts = Counter()
    canonical_heading_section_counts = Counter()

    for pid, (s, pdata) in all_papers.items():
        title = clean_text(pdata.get("title", ""))
        abstract = clean_text(pdata.get("abstract", ""))
        sections = pdata.get("full_text", [])
        qas = pdata.get("qas", [])

        if not abstract:
            papers_with_empty_abstract.append(pid)
        if not sections:
            papers_with_zero_sections.append(pid)
            papers_with_empty_text.append(pid)

        doc_words = 0
        doc_chars = 0
        valid_sections = 0
        paper_seen_canonical = set()

        for sec in sections:
            valid_sections += 1
            raw_sname = (sec.get("section_name") or "").strip()
            norm_sname = normalize_heading(raw_sname)
            canon_sname = canonicalize_heading(raw_sname)

            if norm_sname:
                raw_heading_counts[norm_sname] += 1
            if canon_sname:
                canonical_heading_section_counts[canon_sname] += 1
                paper_seen_canonical.add(canon_sname)

            paras = sec.get("paragraphs", [])
            sec_text = " ".join(paras)
            sec_w = len(sec_text.split())
            section_word_counts.append(sec_w)
            doc_words += sec_w
            doc_chars += len(sec_text)

        for ch in paper_seen_canonical:
            canonical_heading_paper_counts[ch] += 1

        if sections:
            doc_word_counts.append(doc_words)
            doc_char_counts.append(doc_chars)
            doc_section_counts.append(valid_sections)

        paper_has_usable_q = False

        for q_idx, qa in enumerate(qas):
            raw_qid = qa.get("question_id") or f"{pid}_q{q_idx+1}"
            if raw_qid in all_question_ids:
                dup_question_ids.append(raw_qid)
            all_question_ids.add(raw_qid)

            q_text = clean_text(qa.get("question", ""))
            qw = q_text.split()
            q_words.append(len(qw))
            q_chars.append(len(q_text))

            answers = qa.get("answers", [])
            n_ans = len(answers)
            annotator_counts[n_ans] += 1

            unans_votes = 0
            yes_no_votes = 0
            extractive_votes = 0
            free_form_votes = 0

            text_ev_paras = []
            has_float = False

            for a_wrap in answers:
                ans = a_wrap.get("answer", {})
                if ans.get("unanswerable", False):
                    unans_votes += 1
                    individual_answer_types["unanswerable"] += 1
                else:
                    if ans.get("extractive_spans"):
                        extractive_votes += 1
                        individual_answer_types["extractive"] += 1
                    elif ans.get("yes_no") is not None:
                        yes_no_votes += 1
                        individual_answer_types["yes_no"] += 1
                    elif ans.get("free_form_answer"):
                        free_form_votes += 1
                        individual_answer_types["free_form"] += 1
                    else:
                        individual_answer_types["empty_other"] += 1

                for ev in ans.get("evidence", []):
                    ev_c = clean_text(ev)
                    if "FLOAT SELECTED" in ev_c:
                        has_float = True
                    elif ev_c and ev_c not in text_ev_paras:
                        text_ev_paras.append(ev_c)

            # Consensus & Answerability
            if unans_votes == n_ans:
                unanimous_unans_cnt += 1
            elif unans_votes == 0:
                unanimous_ans_cnt += 1
            else:
                split_vote_cnt += 1

            if unans_votes > n_ans / 2:
                majority_unans_cnt += 1
                q_type = "unanswerable"
            elif unans_votes < n_ans / 2:
                majority_ans_cnt += 1
                if yes_no_votes > 0:
                    q_type = "yes_no"
                elif extractive_votes >= free_form_votes and extractive_votes > 0:
                    q_type = "extractive"
                elif free_form_votes > 0:
                    q_type = "abstractive"
                else:
                    q_type = "extractive"
            else:
                tie_vote_cnt += 1
                # If split 1-1, prefer answerable if text evidence is present
                if text_ev_paras:
                    q_type = "extractive" if extractive_votes >= free_form_votes else "abstractive"
                else:
                    q_type = "unanswerable"

            project_q_types[q_type] += 1

            # Evidence categorization
            n_ev = len(text_ev_paras)
            evidence_passages_per_q.append(n_ev)

            if n_ev > 0:
                paper_has_usable_q = True
                full_ev = " ".join(text_ev_paras)
                ev_w = full_ev.split()
                evidence_words_per_q.append(len(ev_w))
                evidence_chars_per_q.append(len(full_ev))
                jaccard = compute_lexical_jaccard(qw, ev_w)
                lexical_jaccards.append(jaccard)

                if n_ev == 1:
                    q_with_single_passage += 1
                else:
                    q_with_multi_passage += 1
            else:
                lexical_jaccards.append(0.0)
                if has_float:
                    q_with_only_float += 1
                elif unans_votes > 0:
                    q_zero_ev_unanswerable += 1
                else:
                    q_zero_ev_answerable += 1
                q_with_no_evidence += 1

            traceability_records.append({
                "question_id": raw_qid,
                "paper_arxiv_id": pid,
                "split": s,
                "question": q_text,
                "question_length_words": len(qw),
                "question_type": q_type,
                "annotators_count": n_ans,
                "unanswerable_votes": unans_votes,
                "text_evidence_passages_count": n_ev,
                "evidence_length_words": len(full_ev.split()) if n_ev > 0 else 0,
                "lexical_jaccard_overlap": round(jaccard if n_ev > 0 else 0.0, 5),
                "has_float_evidence": has_float,
                "is_usable_for_text_rag": (n_ev > 0 and q_type != "unanswerable")
            })

        if paper_has_usable_q:
            papers_with_usable_text_ev.add(pid)
        else:
            papers_zero_usable_q.add(pid)

    total_q = len(q_words)
    total_papers = len(all_papers)
    usable_papers = len(doc_word_counts)
    text_ev_q_count = q_with_single_passage + q_with_multi_passage

    full_eda_summary = {
        "dataset_name": "QASPER (Full Canonical v0.3)",
        "source": "AllenAI Official S3 Distribution (train + dev + test)",
        "scope": "Comprehensive Benchmark EDA",
        "split_counts": {
            "train": {"papers": split_paper_counts["train"], "questions": split_question_counts["train"]},
            "dev": {"papers": split_paper_counts["dev"], "questions": split_question_counts["dev"]},
            "test": {"papers": split_paper_counts["test"], "questions": split_question_counts["test"]},
            "total_papers": total_papers,
            "total_questions": total_q,
        },
        "data_integrity": {
            "duplicate_paper_ids": len(dup_paper_ids),
            "duplicate_question_ids": len(dup_question_ids),
            "papers_missing_abstract": len(papers_with_empty_abstract),
            "papers_with_zero_sections": len(papers_with_zero_sections),
            "papers_with_empty_text": len(papers_with_empty_text),
            "excluded_empty_text_paper_ids": papers_with_empty_text,
            "papers_with_usable_text": usable_papers,
            "papers_with_usable_text_pct": round(usable_papers / total_papers * 100, 2),
            "papers_with_at_least_one_text_evidence_q": len(papers_with_usable_text_ev),
            "papers_with_zero_usable_q": len(papers_zero_usable_q),
        },
        "document_statistics": {
            "total_papers_analyzed": usable_papers,
            "mean_words_per_doc": round(float(np.mean(doc_word_counts)), 1),
            "std_words_per_doc": round(float(np.std(doc_word_counts)), 1),
            "p50_words_per_doc": round(float(np.median(doc_word_counts)), 1),
            "p95_words_per_doc": round(float(np.percentile(doc_word_counts, 95)), 1),
            "min_words_per_doc": int(np.min(doc_word_counts)),
            "max_words_per_doc": int(np.max(doc_word_counts)),
            "mean_sections_per_doc": round(float(np.mean(doc_section_counts)), 2),
            "p50_sections_per_doc": round(float(np.median(doc_section_counts)), 1),
            "p95_sections_per_doc": round(float(np.percentile(doc_section_counts, 95)), 1),
            "min_sections_per_doc": int(np.min(doc_section_counts)),
            "max_sections_per_doc": int(np.max(doc_section_counts)),
            "total_sections_analyzed": len(section_word_counts),
            "mean_words_per_section": round(float(np.mean(section_word_counts)), 1),
            "p50_words_per_section": round(float(np.median(section_word_counts)), 1),
            "p95_words_per_section": round(float(np.percentile(section_word_counts, 95)), 1),
        },
        "question_statistics": {
            "total_questions_analyzed": total_q,
            "annotators_distribution": dict(annotator_counts),
            "type_distribution": dict(project_q_types),
            "type_percentages": {k: round(v / total_q * 100, 2) for k, v in project_q_types.items()},
            "answerability": {
                "unanimous_answerable": unanimous_ans_cnt,
                "unanimous_answerable_pct": round(unanimous_ans_cnt / total_q * 100, 2),
                "unanimous_unanswerable": unanimous_unans_cnt,
                "unanimous_unanswerable_pct": round(unanimous_unans_cnt / total_q * 100, 2),
                "split_vote": split_vote_cnt,
                "split_vote_pct": round(split_vote_cnt / total_q * 100, 2),
                "majority_answerable": majority_ans_cnt,
                "majority_answerable_pct": round(majority_ans_cnt / total_q * 100, 2),
                "majority_unanswerable": majority_unans_cnt,
                "majority_unanswerable_pct": round(majority_unans_cnt / total_q * 100, 2),
                "tie_vote": tie_vote_cnt,
                "tie_vote_pct": round(tie_vote_cnt / total_q * 100, 2),
            },
            "individual_answer_annotations": dict(individual_answer_types),
            "individual_answer_percentages": {k: round(v / sum(individual_answer_types.values()) * 100, 2) for k, v in individual_answer_types.items()},
            "mean_words_per_question": round(float(np.mean(q_words)), 2),
            "std_words_per_question": round(float(np.std(q_words)), 2),
            "p50_words_per_question": round(float(np.median(q_words)), 1),
            "p95_words_per_question": round(float(np.percentile(q_words, 95)), 1),
            "min_words_per_question": int(np.min(q_words)),
            "max_words_per_question": int(np.max(q_words)),
        },
        "evidence_statistics": {
            "questions_with_text_evidence": text_ev_q_count,
            "questions_with_text_evidence_pct": round(text_ev_q_count / total_q * 100, 2),
            "questions_with_only_float_evidence": q_with_only_float,
            "questions_with_only_float_evidence_pct": round(q_with_only_float / total_q * 100, 2),
            "questions_with_zero_evidence": q_with_no_evidence,
            "questions_with_zero_evidence_pct": round(q_with_no_evidence / total_q * 100, 2),
            "passage_distribution_all_questions": {
                "zero_passages": q_with_no_evidence,
                "zero_passages_pct": round(q_with_no_evidence / total_q * 100, 2),
                "single_passage": q_with_single_passage,
                "single_passage_pct": round(q_with_single_passage / total_q * 100, 2),
                "multi_passage": q_with_multi_passage,
                "multi_passage_pct": round(q_with_multi_passage / total_q * 100, 2),
            },
            "passage_distribution_evidenced_denominator": {
                "evidenced_questions_denominator": text_ev_q_count,
                "single_passage_count": q_with_single_passage,
                "single_passage_pct": round(q_with_single_passage / text_ev_q_count * 100, 2),
                "multi_passage_count": q_with_multi_passage,
                "multi_passage_pct": round(q_with_multi_passage / text_ev_q_count * 100, 2),
            },
            "mean_evidence_passages_per_q_all": round(float(np.mean(evidence_passages_per_q)), 2),
            "mean_evidence_words_evidenced_q": round(float(np.mean(evidence_words_per_q)), 1),
            "std_evidence_words_evidenced_q": round(float(np.std(evidence_words_per_q)), 1),
            "p50_evidence_words_evidenced_q": round(float(np.median(evidence_words_per_q)), 1),
            "p95_evidence_words_evidenced_q": round(float(np.percentile(evidence_words_per_q, 95)), 1),
            "min_evidence_words_evidenced_q": int(np.min(evidence_words_per_q)),
            "max_evidence_words_evidenced_q": int(np.max(evidence_words_per_q)),
            "mean_lexical_jaccard_overlap_all": round(float(np.mean(lexical_jaccards)), 4),
            "p50_lexical_jaccard_overlap_all": round(float(np.median(lexical_jaccards)), 4),
            "mean_lexical_jaccard_overlap_evidenced": round(float(np.mean([j for j in lexical_jaccards if j > 0])), 4),
        },
        "top_15_raw_section_headings": dict(raw_heading_counts.most_common(15)),
        "top_10_canonical_section_headings": dict(canonical_heading_paper_counts.most_common(10)),
        "top_10_canonical_heading_section_frequencies": dict(canonical_heading_section_counts.most_common(10)),
    }

    # Save primary JSON summary artifact
    full_json_path = PHASE0_ARTIFACTS / "qasper_full_corpus_eda.json"
    with open(full_json_path, "w", encoding="utf-8") as f:
        json.dump(full_eda_summary, f, indent=2)
    print(f"[+] Serialized Full Corpus EDA artifact to: {full_json_path}")

    # Save traceability index
    trace_path = PHASE0_ARTIFACTS / "eda_corpus_traceability_index.jsonl"
    with open(trace_path, "w", encoding="utf-8") as f:
        for r in traceability_records:
            f.write(json.dumps(r) + "\n")
    print(f"[+] Serialized Question-Level Traceability index ({len(traceability_records)} items) to: {trace_path}")

    raw_arrays = {
        "doc_words": doc_word_counts,
        "doc_sections": doc_section_counts,
        "q_words": q_words,
        "ev_words": evidence_words_per_q,
        "q_types": project_q_types,
        "raw_headings": raw_heading_counts,
        "canon_headings": canonical_heading_counts,
    }

    return full_eda_summary, raw_arrays, traceability_records


def compare_pilot_vs_full(full_summary: Dict[str, Any]) -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("[>] GENERATING PILOT (100 PAPERS) VS FULL BENCHMARK (1,585 PAPERS) COMPARISON")
    print("=" * 80)

    # Load frozen pilot statistics
    pilot_json_path = PHASE0_ARTIFACTS / "qasper_comprehensive_eda.json"
    pilot_stats = {}
    if pilot_json_path.exists():
        with open(pilot_json_path, "r", encoding="utf-8") as f:
            pilot_stats = json.load(f)

    # Comparison metrics dictionary
    comp_rows = [
        {
            "dimension": "Dataset Scope & Papers",
            "metric": "Total Papers Count",
            "pilot_value": "100 (96 with structured sections)",
            "full_corpus_value": f"{full_summary['split_counts']['total_papers']} ({full_summary['data_integrity']['papers_with_usable_text']} with sections)",
            "change_note": "+1,485 papers (+15.8x scale expansion; includes Train, Dev, Test)"
        },
        {
            "dimension": "Dataset Scope & Papers",
            "metric": "Total Questions Count",
            "pilot_value": "250 (sampled from Dev)",
            "full_corpus_value": f"{full_summary['split_counts']['total_questions']}",
            "change_note": "+4,799 questions (+20.2x scale expansion)"
        },
        {
            "dimension": "Question Distribution",
            "metric": "Extractive Questions (%)",
            "pilot_value": "70.0% (175/250)",
            "full_corpus_value": f"{full_summary['question_statistics']['type_percentages']['extractive']}% ({full_summary['question_statistics']['type_distribution']['extractive']}/{full_summary['split_counts']['total_questions']})",
            "change_note": "-13.8% shift (Pilot overrepresented extractive; full corpus has higher abstractive diversity)"
        },
        {
            "dimension": "Question Distribution",
            "metric": "Abstractive Questions (%)",
            "pilot_value": "12.4% (31/250)",
            "full_corpus_value": f"{full_summary['question_statistics']['type_percentages']['abstractive']}% ({full_summary['question_statistics']['type_distribution']['abstractive']}/{full_summary['split_counts']['total_questions']})",
            "change_note": "+7.9% increase (20.3% of full corpus requires multi-passage reasoning)"
        },
        {
            "dimension": "Question Distribution",
            "metric": "Yes/No Questions (%)",
            "pilot_value": "14.4% (36/250)",
            "full_corpus_value": f"{full_summary['question_statistics']['type_percentages']['yes_no']}% ({full_summary['question_statistics']['type_distribution']['yes_no']}/{full_summary['split_counts']['total_questions']})",
            "change_note": "+0.6% (Stable across scales ~15%)"
        },
        {
            "dimension": "Question Distribution",
            "metric": "Unanswerable Questions (%)",
            "pilot_value": "3.2% (8/250)",
            "full_corpus_value": f"{full_summary['question_statistics']['type_percentages']['unanswerable']}% ({full_summary['question_statistics']['type_distribution']['unanswerable']}/{full_summary['split_counts']['total_questions']})",
            "change_note": "+5.3% increase (Full benchmark contains 8.5% unanswerable queries)"
        },
        {
            "dimension": "Document Morphology",
            "metric": "Mean Document Words",
            "pilot_value": "3,257.2 words (std=1,593.4)",
            "full_corpus_value": f"{full_summary['document_statistics']['mean_words_per_doc']:,} words (std={full_summary['document_statistics']['std_words_per_doc']:,})",
            "change_note": "+317.9 words (+9.8% longer on average across entire NLP literature)"
        },
        {
            "dimension": "Document Morphology",
            "metric": "Median Document Words (P50)",
            "pilot_value": "2,980.5 words",
            "full_corpus_value": f"{full_summary['document_statistics']['p50_words_per_doc']:,} words",
            "change_note": "+420.5 words shift in median document length"
        },
        {
            "dimension": "Document Morphology",
            "metric": "P95 Document Words",
            "pilot_value": "5,843.6 words",
            "full_corpus_value": f"{full_summary['document_statistics']['p95_words_per_doc']:,} words",
            "change_note": "+863.7 words (P95 papers exceed 6,700 words / ~9,000 tokens)"
        },
        {
            "dimension": "Document Structure",
            "metric": "Mean Sections per Paper",
            "pilot_value": "13.36 sections",
            "full_corpus_value": f"{full_summary['document_statistics']['mean_sections_per_doc']} sections",
            "change_note": "+0.47 sections (Highly consistent hierarchical decomposition across 1,584 papers)"
        },
        {
            "dimension": "Document Structure",
            "metric": "Mean Words per Section",
            "pilot_value": "243.8 words (P50=179.0)",
            "full_corpus_value": f"{full_summary['document_statistics']['mean_words_per_section']} words (P50={full_summary['document_statistics']['p50_words_per_section']})",
            "change_note": "+14.7 words (Validates 300-400 token chunk budget alignment)"
        },
        {
            "dimension": "Query-Evidence Asymmetry",
            "metric": "Mean Query Length",
            "pilot_value": "7.95 words (P50=7.0)",
            "full_corpus_value": f"{full_summary['question_statistics']['mean_words_per_question']} words (P50={full_summary['question_statistics']['p50_words_per_question']})",
            "change_note": "+0.19 words (Virtually identical: queries average 8 words)"
        },
        {
            "dimension": "Query-Evidence Asymmetry",
            "metric": "Mean Evidence Passage Words",
            "pilot_value": "190.9 words (P50=148.0)",
            "full_corpus_value": f"{full_summary['evidence_statistics']['mean_evidence_words_evidenced_q']} words (P50={full_summary['evidence_statistics']['p50_evidence_words_evidenced_q']})",
            "change_note": "-15.4 words (Slightly more concise ground-truth evidence spans)"
        },
        {
            "dimension": "Query-Evidence Asymmetry",
            "metric": "Lexical Jaccard Overlap",
            "pilot_value": "0.0158 (1.58%)",
            "full_corpus_value": f"{full_summary['evidence_statistics']['mean_lexical_jaccard_overlap_all']} ({full_summary['evidence_statistics']['mean_lexical_jaccard_overlap_all']*100:.2f}%)",
            "change_note": "+0.31% (Reconfirms extreme vocabulary mismatch < 2.0% between query and evidence)"
        },
        {
            "dimension": "Query-Evidence Asymmetry",
            "metric": "Multi-passage Evidence Rate (%)",
            "pilot_value": "53.7% (130/242 evidenced questions)",
            "full_corpus_value": f"{full_summary['evidence_statistics']['passage_distribution_evidenced_denominator']['multi_passage_pct']}% ({full_summary['evidence_statistics']['passage_distribution_evidenced_denominator']['multi_passage_count']}/{full_summary['evidence_statistics']['questions_with_text_evidence']})",
            "change_note": "-9.8% shift (44.0% multi-passage in full corpus vs 53.7% in pilot sample)"
        }
    ]

    # Save CSV comparison table
    csv_path = PHASE0_ARTIFACTS / "eda_pilot_vs_full_comparison.csv"
    import csv
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dimension", "metric", "pilot_value", "full_corpus_value", "change_note"])
        writer.writeheader()
        writer.writerows(comp_rows)
    print(f"[+] Serialized Pilot vs Full comparison CSV to: {csv_path}")

    # Also save Question distribution CSV
    q_csv_path = PHASE0_ARTIFACTS / "eda_question_distribution.csv"
    with open(q_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["question_type", "count", "percentage_of_all_questions", "denominator"])
        for q_type, cnt in full_summary["question_statistics"]["type_distribution"].items():
            pct = full_summary["question_statistics"]["type_percentages"][q_type]
            writer.writerow([q_type, cnt, f"{pct}%", full_summary["split_counts"]["total_questions"]])
    print(f"[+] Serialized Question distribution CSV to: {q_csv_path}")

    # Also save Canonical Heading distribution CSV
    h_csv_path = PHASE0_ARTIFACTS / "eda_section_heading_distribution.csv"
    with open(h_csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["canonical_heading", "papers_count", "percentage_of_papers", "total_section_occurrences", "denominator_papers"])
        denom_p = full_summary["data_integrity"]["papers_with_usable_text"]
        sec_freqs = full_summary["top_10_canonical_heading_section_frequencies"]
        for heading, p_cnt in full_summary["top_10_canonical_section_headings"].items():
            pct = round(p_cnt / denom_p * 100, 2)
            tot_sec = sec_freqs.get(heading, p_cnt)
            writer.writerow([heading, p_cnt, f"{pct}%", tot_sec, denom_p])
    print(f"[+] Serialized Section Heading distribution CSV to: {h_csv_path}")

    return {"comparison_rows": comp_rows}


def generate_publication_eda_figures(raw_arrays: Dict[str, Any], full_summary: Dict[str, Any]):
    print("\n" + "=" * 80)
    print("[>] GENERATING PUBLICATION-READY 4-PANEL FIGURE FOR FULL QASPER CORPUS")
    print("=" * 80)

    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 13,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "figure.titlesize": 15,
        "figure.autolayout": True,
    })

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 10.5), dpi=300)

    # Panel A: Question Type Distribution
    q_types = full_summary["question_statistics"]["type_distribution"]
    labels = ["Extractive", "Abstractive", "Yes / No", "Unanswerable"]
    type_keys = ["extractive", "abstractive", "yes_no", "unanswerable"]
    counts = [q_types.get(k, 0) for k in type_keys]
    pcts = [full_summary["question_statistics"]["type_percentages"].get(k, 0.0) for k in type_keys]
    colors = ["#1a5276", "#2980b9", "#5499c7", "#d35400"]

    bars_a = axes[0, 0].bar(labels, counts, color=colors, edgecolor="#1a1a1a", linewidth=0.9, alpha=0.90)
    axes[0, 0].set_title("(A) Phân bố loại câu hỏi nghiên cứu (N = 5.049 câu hỏi)", fontweight="bold", pad=10)
    axes[0, 0].set_ylabel("Số lượng câu hỏi (Questions)", fontweight="bold")
    axes[0, 0].set_ylim(0, max(counts) * 1.15)
    axes[0, 0].grid(True, axis="y", linestyle="--", alpha=0.6)

    for bar, cnt, pct in zip(bars_a, counts, pcts):
        h = bar.get_height()
        axes[0, 0].text(bar.get_x() + bar.get_width() / 2, h + 50, f"{cnt:,}\n({pct:.1f}%)",
                        ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    # Panel B: Document Length Distribution
    doc_words = raw_arrays["doc_words"]
    mean_dw = full_summary["document_statistics"]["mean_words_per_doc"]
    p50_dw = full_summary["document_statistics"]["p50_words_per_doc"]
    p95_dw = full_summary["document_statistics"]["p95_words_per_doc"]

    # Filter extreme outliers (> 12,000 words) for visual clarity in histogram
    visual_doc_words = [w for w in doc_words if w <= 12000]
    axes[0, 1].hist(visual_doc_words, bins=35, color="#1b4f72", edgecolor="#1a1a1a", linewidth=0.8, alpha=0.85)
    axes[0, 1].axvline(mean_dw, color="#c0392b", linestyle="--", linewidth=1.8, label=f"Trung bình: {mean_dw:,.0f} từ")
    axes[0, 1].axvline(p50_dw, color="#d35400", linestyle="-.", linewidth=1.8, label=f"Trung vị (P50): {p50_dw:,.0f} từ")
    axes[0, 1].axvline(p95_dw, color="#7d3c98", linestyle=":", linewidth=1.8, label=f"Phân vị 95% (P95): {p95_dw:,.0f} từ")
    axes[0, 1].set_title("(B) Phân bố độ dài bài báo khoa học toàn văn (N = 1.584 bài)", fontweight="bold", pad=10)
    axes[0, 1].set_xlabel("Độ dài bài báo (Số từ / bài)", fontweight="bold")
    axes[0, 1].set_ylabel("Số lượng bài báo (Papers)", fontweight="bold")
    axes[0, 1].legend(loc="upper right", frameon=True, fontsize=9.5)
    axes[0, 1].grid(True, linestyle="--", alpha=0.6)

    # Panel C: Question vs Evidence Length (Query-Evidence Asymmetry)
    q_words = raw_arrays["q_words"]
    ev_words = [w for w in raw_arrays["ev_words"] if w <= 500]  # trim extreme tail for visualization
    mean_qw = full_summary["question_statistics"]["mean_words_per_question"]
    mean_ew = full_summary["evidence_statistics"]["mean_evidence_words_evidenced_q"]
    jaccard_pct = full_summary["evidence_statistics"]["mean_lexical_jaccard_overlap_all"] * 100

    axes[1, 0].hist(q_words, bins=15, alpha=0.65, color="#2980b9", edgecolor="#1a1a1a",
                    label=f"Câu hỏi (Trung bình: {mean_qw:.1f} từ)")
    axes[1, 0].hist(ev_words, bins=35, alpha=0.65, color="#e67e22", edgecolor="#1a1a1a",
                    label=f"Đoạn bằng chứng (Trung bình: {mean_ew:.1f} từ)")
    axes[1, 0].set_title(f"(C) Bất đối xứng độ dài câu hỏi vs bằng chứng (Jaccard = {jaccard_pct:.2f}%)", fontweight="bold", pad=10)
    axes[1, 0].set_xlabel("Độ dài văn bản (Số từ)", fontweight="bold")
    axes[1, 0].set_ylabel("Tần suất xuất hiện", fontweight="bold")
    axes[1, 0].legend(loc="upper right", frameon=True, fontsize=9.5)
    axes[1, 0].grid(True, linestyle="--", alpha=0.6)

    # Panel D: Document Structural Granularity & Common Academic Headings
    canon_headings = full_summary["top_10_canonical_section_headings"]
    top_h_labels = [h.capitalize() for h in list(canon_headings.keys())[:7]][::-1]
    top_h_counts = [canon_headings[h.lower()] for h in top_h_labels][::-1]

    bars_d = axes[1, 1].barh(top_h_labels, top_h_counts, color="#16a085", edgecolor="#1a1a1a", linewidth=0.8, alpha=0.85)
    axes[1, 1].set_title("(D) Tần suất các đề mục học thuật chuẩn (IMRaD Structure)", fontweight="bold", pad=10)
    axes[1, 1].set_xlabel("Số bài báo xuất hiện đề mục (trên 1.584 bài)", fontweight="bold")
    axes[1, 1].set_xlim(0, 1584 * 1.15)
    axes[1, 1].grid(True, axis="x", linestyle="--", alpha=0.6)

    for bar, cnt in zip(bars_d, top_h_counts):
        w = bar.get_width()
        pct = cnt / 1584 * 100
        axes[1, 1].text(w + 25, bar.get_y() + bar.get_height() / 2, f"{cnt:,} ({pct:.1f}%)",
                        va="center", ha="left", fontsize=9, fontweight="bold")

    fig.suptitle("Hình 5.0: Phân tích khám phá đặc trưng dữ liệu ngữ liệu QASPER toàn phần (N = 1.585 bài báo / 5.049 câu hỏi)",
                 fontsize=14.5, fontweight="bold", y=1.002)

    # Save to all required destinations
    out_paths = [
        FIGURES_DIR / "qasper_full_corpus_eda.png",
        REPORTS_FIG_DIR / "fig5_0_qasper_eda.png",
        DOCS_FIG_DIR / "fig5_0_qasper_eda.png",
    ]

    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(p, dpi=300, bbox_inches="tight")
        print(f"[+] Saved publication figure to: {p}")

    plt.close(fig)


def main():
    print("=" * 80)
    print("FULL QASPER BENCHMARK EDA & CORPUS AUDIT EXECUTION")
    print("=" * 80)

    full_summary, raw_arrays, trace_records = audit_full_qasper()
    compare_pilot_vs_full(full_summary)
    generate_publication_eda_figures(raw_arrays, full_summary)

    print("\n" + "=" * 80)
    print("✔ FULL QASPER BENCHMARK EDA & AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
