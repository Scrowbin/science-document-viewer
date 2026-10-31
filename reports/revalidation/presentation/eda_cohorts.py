#!/usr/bin/env python3
"""Descriptive statistics (EDA) of the revalidation cohorts for the progress-report presentation.
Output: reports/revalidation/presentation/eda_cohorts.json"""

import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_runner as rr  # noqa: E402

TOK = re.compile(r"[a-z0-9]+")
STOP = set("a an the of in on for to and or is are was were be by with as at from that this which it its we our their "
           "what how do does did".split())


def words(s):
    return len(s.split()) if s else None


def content(s):
    return {t for t in TOK.findall(s.lower()) if t not in STOP}


def jacc(a, b):
    a, b = content(a), content(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def qtype(qa):
    for ans in qa["answers"]:
        a = ans["answer"]
        if a.get("unanswerable"):
            continue
        if a.get("yes_no") is not None:
            return "boolean"
        if a.get("extractive_spans"):
            return "extractive"
        if a.get("free_form_answer"):
            return "abstractive"
    return "unanswerable"


def pages(pdf):
    try:
        import fitz
        with fitz.open(pdf) as d:
            return d.page_count
    except Exception:
        return None


def summ(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None
    xs = sorted(xs)
    return {"mean": round(st.mean(xs), 1), "median": round(st.median(xs), 1),
            "p95": round(xs[min(len(xs) - 1, int(0.95 * len(xs)))], 1), "min": xs[0], "max": xs[-1]}


def main():
    train = json.load(open(ROOT / "eval/data/qasper_official/qasper-train-v0.3.json", encoding="utf-8"))
    qa_by_id = {qa["question_id"]: (p, qa) for p, d in train.items() for qa in d["qas"]}
    out = {}
    for name in ["C-RET", "C-RET-150", "C-INT"]:
        c = rr.load_cohort(name)
        g = rr.group_items(c)
        items = c["items"]
        types = Counter(it.get("question_type") or qtype(qa_by_id[it["question_id"]][1]) for it in items)
        out[name] = {
            "role": c.get("role"), "papers": len(g), "questions": len(items),
            "questions_per_paper": dict(sorted(Counter(len(v) for v in g.values()).items())),
            "question_types": dict(types),
            "question_words": summ([words(it["question"]) for it in items]),
            "evidence_paragraphs_per_question": summ([len(it["retrieval_evidence"]) for it in items]),
            "evidence_words_per_question": summ([sum(words(e) or 0 for e in it["retrieval_evidence"]) for it in items]),
            "question_evidence_jaccard_mean": round(st.mean(max(jacc(it["question"], e) for e in it["retrieval_evidence"])
                                                            for it in items), 4),
            "paper_words": summ([sum(words(p) or 0 for s in train[pid]["full_text"] for p in s["paragraphs"]) for pid in g]),
            "paper_sections": summ([len(train[pid]["full_text"]) for pid in g]),
            "pdf_pages": summ([pages(rr.pdf_path("C-RET", pid, v[0].get("pdf_version", "latest"))) for pid, v in g.items()]),
        }
    c = rr.load_cohort("PEERQA-PDF")
    g = rr.group_items(c)
    items = c["items"]
    venues = Counter(pid.split("/")[0] if "/" in pid else pid.split("_")[0] for pid in g)
    out["PEERQA-PDF"] = {
        "role": c.get("role"), "license": c.get("license"), "papers": len(g), "questions": len(items),
        "venues": dict(venues),
        "questions_per_paper": summ([len(v) for v in g.values()]),
        "question_words": summ([words(it["question"]) for it in items]),
        "answer_words": summ([words(it["answer_free_form"]) for it in items]),
        "questions_without_free_form_answer": sum(1 for it in items if not it.get("answer_free_form")),
        "evidence_sentences_per_question": summ([len(it["retrieval_evidence"]) for it in items]),
        "question_evidence_jaccard_mean": round(st.mean(max(jacc(it["question"], e) for e in it["retrieval_evidence"])
                                                        for it in items), 4),
        "pdf_pages": summ([pages(rr.pdf_path("PEERQA-PDF", pid)) for pid in g]),
    }
    man = json.load(open(ROOT / "eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json", encoding="utf-8"))
    sel = man["selected_eval_items"]
    out["RQ5-500Q"] = {
        "papers": len({i["paper_arxiv_id"] for i in sel}), "questions": len(sel),
        "question_types": dict(Counter(i["question_type"] for i in sel)),
        "gold_evidence_words": summ([sum(words(e) or 0 for e in i["ground_truth_evidence"]) for i in sel]),
    }
    p = Path(__file__).with_name("eda_cohorts.json")
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
