#!/usr/bin/env python3
"""
Build the QASPER evaluation set for the 16-configuration combination experiment.

Inclusion (applied to every QASPER v0.3 split; no other cohort restrictions):
  paper    : the latest arXiv PDF (eval/pdfs/<split dir>/<id>.pdf) was downloaded, opens, and pymupdf_layout
             extracted non-empty text from it. No fallback to older versions (e.g. a local <id>v1.pdf).
  question : at least one annotator gave both an answer and text evidence (figure/table-only evidence excluded);
             the same rule as the generation experiment (is_atomic_eligible), so every question has gold answers.
No PDF version check against gold evidence is done; a PDF can be a later version than the annotated text
(documented limitation). Duplicate question texts with different IDs are kept and listed.
Split precedence if an ID ever appears in two splits: train > dev > test (each conflict is listed).

Output: eval/phases/phase_0_baseline/artifacts/combination_set.json (all counts computed here).
Usage:  backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/build_combination_set.py
"""

import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))
from eval_common.revalidation import qasper_text_evidence  # noqa: E402
from generate_sample_manifest_250 import is_atomic_eligible  # noqa: E402

QASPER = ROOT / "eval" / "data" / "qasper_official"
EXTRACT = ROOT / "eval" / "data" / "revalidation_cache" / "extract"
OUT = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "combination_set.json"
SPLITS = ["train", "dev", "test"]                       # precedence order
PDF_DIR = {"train": "train_reservoir", "dev": "dev", "test": "test"}
CACHE_SET = {"train": "reservoir", "dev": "dev", "test": "test"}
MIN_TEXT_CHARS = 500


def choose_pdf(split, pid):
    pdf = ROOT / "eval" / "pdfs" / PDF_DIR[split] / f"{pid}.pdf"
    return (pdf, "latest") if pdf.exists() else (None, None)


def load_download_manifest(split):
    p = ROOT / "eval" / "pdfs" / PDF_DIR[split] / "download_manifest.json"
    return json.load(open(p, encoding="utf-8"))["papers"] if p.exists() else {}


def load_extraction(split):
    p = EXTRACT / CACHE_SET[split] / "latest" / "pymupdf_layout.jsonl"
    out = {}
    if p.exists():
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            out[r["paper_id"]] = r
    return out


def question_status(qa):
    answerable = [a["answer"] for a in qa.get("answers", []) if not a["answer"].get("unanswerable", False)]
    if not answerable:
        return "unanswerable"
    if not qasper_text_evidence(qa):
        return "figure_or_table_only_evidence"
    if is_atomic_eligible(qa)[0]:
        return "included"
    return "no_answer_with_text_evidence"


def main():
    data = {s: json.load(open(QASPER / f"qasper-{s}-v0.3.json", encoding="utf-8")) for s in SPLITS}
    papers, questions, excluded_papers, excluded_questions = {}, {}, [], []
    conflicts, seen_paper, seen_q = [], {}, {}
    counts = {s: defaultdict(int) for s in SPLITS}

    for split in SPLITS:
        extraction = load_extraction(split)
        downloaded = load_download_manifest(split)
        for pid, paper in sorted(data[split].items()):
            c = counts[split]
            c["qasper_papers"] += 1
            c["qasper_questions"] += len(paper["qas"])
            if pid in seen_paper:
                conflicts.append({"type": "paper_in_two_splits", "id": pid, "kept": seen_paper[pid], "dropped": split})
                continue
            seen_paper[pid] = split
            pdf, version = choose_pdf(split, pid)
            rec = extraction.get(pid)
            if pdf is None:
                reason = "latest_pdf_unavailable" if pid in downloaded else "pdf_not_downloaded"
            elif rec is None:
                reason = "pdf_not_extracted"
            elif not rec.get("ok"):
                reason = "extraction_failed"
            elif len((rec.get("full_text") or "").strip()) < MIN_TEXT_CHARS:
                reason = "no_extractable_text"
            else:
                reason = None
            if reason:
                excluded_papers.append({"paper_id": pid, "split": split, "reason": reason})
                c[f"papers_excluded_{reason}"] += 1
                continue
            c["papers_with_usable_pdf"] += 1
            kept_q = []
            for qa in paper["qas"]:
                qid = qa["question_id"]
                if qid in seen_q:
                    conflicts.append({"type": "question_id_in_two_places", "id": qid, "kept": seen_q[qid], "dropped": pid})
                    continue
                seen_q[qid] = pid
                status = question_status(qa)
                if status != "included":
                    excluded_questions.append({"question_id": qid, "paper_id": pid, "split": split, "reason": status})
                    c[f"questions_excluded_{status}"] += 1
                    continue
                questions[qid] = {"paper_id": pid, "split": split, "question": qa["question"]}
                kept_q.append(qid)
            if not kept_q:
                excluded_papers.append({"paper_id": pid, "split": split, "reason": "no_evaluable_question"})
                c["papers_excluded_no_evaluable_question"] += 1
                continue
            c["papers_included"] += 1
            c["questions_included"] += len(kept_q)
            papers[pid] = {"split": split, "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "pdf_version": version,
                           "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                           "extraction_cache": f"{CACHE_SET[split]}/latest/pymupdf_layout.jsonl",
                           "questions": kept_q}

    dup_texts = defaultdict(list)
    for qid, q in questions.items():
        dup_texts[(q["paper_id"], q["question"].strip().lower())].append(qid)
    duplicate_text_groups = [{"paper_id": k[0], "question": k[1], "question_ids": v}
                             for k, v in dup_texts.items() if len(v) > 1]

    out = {
        "description": "QASPER evaluation set for the combination experiment (all splits, usable latest PDFs).",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script": "eval/phases/phase_0_baseline/scripts/build_combination_set.py",
        "qasper_source": [f"eval/data/qasper_official/qasper-{s}-v0.3.json" for s in SPLITS],
        "inclusion": {
            "paper": "latest local PDF downloaded, opens, pymupdf_layout extracts >= 500 characters",
            "question": "an annotator gave both an answer and text (non-figure) evidence (is_atomic_eligible)",
            "pdf_rule": "latest arXiv PDF (<id>.pdf) only; no older-version fallback; no version check against gold",
            "split_precedence": SPLITS,
            "train_scope": "Train papers are the previously downloaded subset in eval/pdfs/train_reservoir, not all of Train",
        },
        "counts_by_split": {s: dict(counts[s]) for s in SPLITS},
        "totals": {"papers": len(papers), "questions": len(questions)},
        "conflicts": conflicts,
        "duplicate_question_texts": duplicate_text_groups,
        "excluded_papers": excluded_papers,
        "excluded_questions": excluded_questions,
        "papers": papers,
        "questions": questions,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"totals": out["totals"], "counts_by_split": out["counts_by_split"],
                      "conflicts": len(conflicts), "duplicate_text_groups": len(duplicate_text_groups)}, indent=1))


if __name__ == "__main__":
    main()
