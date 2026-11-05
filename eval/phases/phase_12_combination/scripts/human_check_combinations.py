#!/usr/bin/env python3
"""
Blinded human check for the combination experiment: 15 questions x 2 LLMs on one retrieval pipeline.

Pipeline choice (context-retention rule, fixed before looking at answers): the retrieval pipeline with the
highest CEC@0.5, ties broken by nDCG@10. Both LLMs answered from exactly the same retrieved context, so the
check compares the two models on that context. Questions: seed 42, stratified by answer type (5 extractive,
5 abstractive, 5 yes/no; if a type has fewer, the rest is filled from the other types).
Same 6-label rubric as the generation human check; judge against the RETRIEVED context, not general knowledge.
Single reviewer, qualitative and supplementary; not a statistically representative evaluation.

Usage (backend/venv):
  python .../human_check_combinations.py package     [--run DIR]   -> <run>/human_check/ (sheet, template, mapping)
  python .../human_check_combinations.py summarize   [--run DIR]   -> <run>/human_check/human_check_summary.json
"""

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "eval" / "phases" / "phase_12_combination" / "artifacts" / "combinations"
QASPER = ROOT / "eval" / "data" / "qasper_official"
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))
from generate_human_review_package_extra import RUBRIC  # noqa: E402  (same rubric as the generation check)

LLMS = ["LLAMA3B", "QWEN15B"]
LABELS = ["Model_Zeta", "Model_Eta"]
SEED, PER_TYPE = 42, 5
TYPES = ["extractive", "abstractive", "boolean"]
RUBRIC_HERE = RUBRIC.replace("annotation_template_40a.csv` (or .jsonl)", "annotation_template_30a.csv`")


def read_jsonl(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]


def choose_pipeline(run):
    rows = list(csv.DictReader(open(run / "retrieval.csv", encoding="utf-8")))
    best = max(rows, key=lambda r: (float(r["cec_0.5"]), float(r["ndcg10"])))
    return best["retrieval_pipeline"], rows


def package(run):
    pipe, rows = choose_pipeline(run)
    gens = [r for r in read_jsonl(run / "generation_per_query.jsonl") if r["retrieval_pipeline"] == pipe]
    by_q = {}
    for r in gens:
        by_q.setdefault(r["question_id"], {})[r["config"].rsplit("_", 1)[1]] = r
    complete = sorted(q for q, d in by_q.items() if all(m in d for m in LLMS))
    rng = random.Random(SEED)
    pools = {t: [q for q in complete if by_q[q][LLMS[0]]["question_type"] == t] for t in TYPES}
    for t in TYPES:
        rng.shuffle(pools[t])
    picked = [q for t in TYPES for q in pools[t][:PER_TYPE]]
    rest = [q for t in TYPES for q in pools[t][PER_TYPE:]]
    rng.shuffle(rest)
    picked += rest[:PER_TYPE * len(TYPES) - len(picked)]
    rng.shuffle(picked)

    ctx = {r["question_id"]: r for r in read_jsonl(run / "contexts.jsonl") if r["retrieval_pipeline"] == pipe}
    papers = {}
    for s in ("train", "dev", "test"):
        papers.update(json.load(open(QASPER / f"qasper-{s}-v0.3.json", encoding="utf-8")))

    orders = [tuple(LLMS), tuple(reversed(LLMS))] * ((len(picked) + 1) // 2)
    orders = orders[:len(picked)]
    rng.shuffle(orders)
    out = run / "human_check"
    out.mkdir(parents=True, exist_ok=True)
    md = [f"# Human check: combination experiment ({len(picked)} questions x 2 answers)", "",
          "Answers are shown as `Model_Zeta` and `Model_Eta`; which model is which changes from question to",
          "question. Both answers were generated from the **same retrieved context** shown below. Judge each",
          "answer only against that context. Do not open `restricted_model_label_mapping.json` before finishing.",
          "", RUBRIC_HERE, "## Questions", ""]
    template, mapping = [], []
    for n, (qid, order) in enumerate(zip(picked, orders), start=1):
        rid = f"CMB-{n:02d}"
        r0 = by_q[qid][LLMS[0]]
        p = papers[r0["paper_id"]]
        qtext = next(qa["question"] for qa in p["qas"] if qa["question_id"] == qid)
        context = "\n\n---\n\n".join(d["text"] for d in ctx[qid]["docs"]) if qid in ctx else ""
        md += [f"### {rid} (arXiv:{r0['paper_id']}, {r0['split']})", f"**Paper:** *{p['title']}*  ",
               f"**Question:** {qtext}", "", "<details><summary>Retrieved context given to both models</summary>",
               "", "```text", context or "(no context: refused by the similarity gate)", "```", "</details>", ""]
        for lbl, llm in zip(LABELS, order):
            rec = by_q[qid][llm]
            ans = (rec["prediction"] or "").strip()
            md += [f"**{lbl}:**", ""] + [f"> {x}" if x else ">" for x in ans.split("\n")] + [""]
            template.append({"review_item_id": rid, "question_id": qid, "paper_id": r0["paper_id"], "blind_label": lbl,
                             "question_text": qtext, "context_text": context, "model_answer": ans, "primary_label": "",
                             "secondary_label": "", "supporting_evidence": "", "reviewer_notes": ""})
            mapping.append({"review_item_id": rid, "question_id": qid, "blind_label": lbl, "config": rec["config"],
                            "llm": rec["llm"], "question_type": rec["question_type"], "split": rec["split"],
                            "refusal": rec.get("refusal"), "token_f1": rec.get("token_f1")})
        md += ["---", ""]
    (out / "REVIEW_SHEET.md").write_text("\n".join(md), encoding="utf-8")
    with open(out / "annotation_template_30a.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(template[0]))
        w.writeheader()
        w.writerows(template)
    json.dump({"seed": SEED, "retrieval_pipeline": pipe,
               "rule": "highest CEC@0.5, ties by nDCG@10",
               "candidates": {r["retrieval_pipeline"]: [float(r["cec_0.5"]), float(r["ndcg10"])] for r in rows},
               "question_types": dict(Counter(m["question_type"] for m in mapping[::2])),
               "labels": LABELS, "mapping": mapping},
              open(out / "restricted_model_label_mapping.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"pipeline {pipe}; {len(picked)} questions, {len(template)} answers -> {out}")
    print("types:", dict(Counter(by_q[q][LLMS[0]]["question_type"] for q in picked)))


def summarize(run):
    out = run / "human_check"
    mp = json.load(open(out / "restricted_model_label_mapping.json", encoding="utf-8"))
    who = {(m["review_item_id"], m["blind_label"]): m for m in mp["mapping"]}
    rows = list(csv.DictReader(open(out / "annotation_template_30a.csv", encoding="utf-8-sig")))
    missing = [r["review_item_id"] for r in rows if not r["primary_label"].strip()]
    if missing:
        sys.exit(f"unlabelled rows: {missing}")
    per = {}
    unblind = []
    for r in rows:
        m = who[(r["review_item_id"], r["blind_label"])]
        per.setdefault(m["llm"], Counter())[r["primary_label"].strip()] += 1
        unblind.append({**{k: r[k] for k in ("review_item_id", "question_id", "primary_label", "secondary_label",
                                             "reviewer_notes")}, **m})
    with open(out / "annotations_unblinded.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(unblind[0]))
        w.writeheader()
        w.writerows(unblind)
    summ = {"retrieval_pipeline": mp["retrieval_pipeline"], "n_questions": len(rows) // 2,
            "per_model": {k: dict(v) for k, v in per.items()}}
    json.dump(summ, open(out / "human_check_summary.json", "w", encoding="utf-8"), indent=2)
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["package", "summarize"])
    ap.add_argument("--run", type=Path, default=RUN)
    a = ap.parse_args()
    (package if a.mode == "package" else summarize)(a.run)
