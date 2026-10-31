#!/usr/bin/env python3
"""
Builds the 30-case human check of Context Evidence Coverage (CEC) on the the chunking experiment Dev papers (diagnostic data).

For the 47 the chunking experiment Dev papers / 127 questions: production chunking (fixed_size, section_overlap, hierarchical) of
pymupdf_layout sections, dense e5-small-v2 ranking, production context assembly (1,600 tokens, <= 5 units).
CEC (tau = 0.50) is computed per (question, strategy). 30 cases are drawn with seed 42: for each strategy,
5 covered and 5 not covered. The annotator sees the question, the reference answer(s), the gold evidence and
the context, but not the strategy or the CEC value.

Pre-registered decision (fixed before judgments are seen): if human YES/NO agrees with CEC on < 80% of the
cases (UNSURE counted as disagreement), budgeted nDCG@10 becomes the chunking experiment's primary metric and CEC is secondary.

Outputs (eval/phases/phase_2_chunking/artifacts/cec_human_check/):
  CEC_CHECK_SHEET.md          sheet for the annotator
  cec_check_key.json          hidden key (strategy, CEC) - do not open before annotating
  dev_contexts.jsonl          all 381 (question, strategy) contexts with CEC at tau 0.3/0.5/0.7
"""

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402

rp.setup_django()
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402
from eval_common.revalidation import qasper_text_evidence  # noqa: E402

OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "cec_human_check"
E5 = "intfloat/e5-small-v2"
STRATEGIES = ["fixed_size", "section_overlap", "hierarchical"]


def references(qa):
    refs = []
    for ann in qa["answers"]:
        a = ann["answer"]
        if a.get("unanswerable"):
            continue
        if a.get("extractive_spans"):
            refs.append(" | ".join(s for s in a["extractive_spans"] if s.strip()))
        elif a.get("free_form_answer", "").strip():
            refs.append(a["free_form_answer"].strip())
        elif a.get("yes_no") is not None:
            refs.append("Yes" if a["yes_no"] else "No")
    return [r for r in dict.fromkeys(refs) if r]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dev = json.load(open(ROOT / "eval/data/qasper_official/qasper-dev-v0.3.json", encoding="utf-8"))
    rows = [json.loads(line) for line in open(ROOT / "eval/results/rq2_chunking_queries_20261024_013443.jsonl")]
    inhouse = {q["id"]: q["original_id"] for q in json.load(open(ROOT / "eval/prepared/qasper_sampled.json", encoding="utf-8"))}
    by_paper = {}
    for r in rows:
        by_paper.setdefault(r["paper_arxiv_id"], set()).add(r["query_id"])

    contexts = []
    for aid in sorted(by_paper):
        qas = {qa["question_id"]: qa for qa in dev[aid]["qas"]}
        qs = [qas[inhouse[i]] for i in sorted(by_paper[aid])]
        qs = [qa for qa in qs if qasper_text_evidence(qa)]
        sections = extract_sections_from_pdf(str(ROOT / "eval" / "pdfs" / "dev" / f"{aid}.pdf"))
        qm = rp.cached_embed(E5, [qa["question"] for qa in qs], True, f"dev47_{aid}")
        for st in STRATEGIES:
            units = rp.build_units(sections, st, aid)
            um = rp.cached_embed(E5, [u["text"] for u in units], False, f"dev47_{aid}_{st}")
            cand = rp.candidate_units_for_relevance(units, st)
            for qa, qv in zip(qs, qm):
                ctx = rp.assemble(rp.rank("dense", um @ qv, [u["text"] for u in units], qa["question"]), units, st)
                ev = qasper_text_evidence(qa)
                m = rp.question_metrics(ctx, cand, ev)
                contexts.append({"paper_arxiv_id": aid, "question_id": qa["question_id"], "strategy": st,
                                 "question": qa["question"], "references": references(qa), "evidence": ev,
                                 "context": [c["text"] for c in ctx], **m})
        print(f"{aid}: {len(qs)} questions", flush=True)

    with open(OUT / "dev_contexts.jsonl", "w", encoding="utf-8") as f:
        for c in contexts:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    rng = random.Random(42)
    picked = []
    for st in STRATEGIES:
        for cov in (1, 0):
            pool = [c for c in contexts if c["strategy"] == st and c["cec_0.5"] == cov]
            picked += rng.sample(pool, min(5, len(pool)))
    rng.shuffle(picked)

    key, lines = [], [
        "# CEC Human Check (30 cases)",
        "",
        "For each case, read the question, the reference answer(s) and the gold evidence, then the **context**.",
        "Decide: **does the context contain enough information for a reader to answer the question?**",
        "Mark exactly one box. Use UNSURE only if you really cannot decide. Do not open `cec_check_key.json`.",
        "",
    ]
    for n, c in enumerate(picked, 1):
        cid = f"CEC-{n:02d}"
        key.append({"case_id": cid, "paper_arxiv_id": c["paper_arxiv_id"], "question_id": c["question_id"],
                    "strategy": c["strategy"], "cec_0.5": c["cec_0.5"], "cec_0.3": c["cec_0.3"], "cec_0.7": c["cec_0.7"]})
        lines += [f"## {cid}", "", f"**Question:** {c['question']}", "",
                  "**Reference answer(s):** " + " ‖ ".join(c["references"]), "",
                  "<details><summary>Gold evidence</summary>", "", *[f"> {e}" for e in c["evidence"]], "", "</details>", "",
                  "<details><summary>Context (as the language model would receive it)</summary>", "", "```text",
                  "\n\n---\n\n".join(c["context"]), "```", "</details>", "",
                  "- **Judgment:** `[ ] YES   [ ] NO   [ ] UNSURE`", "- **Note (optional):** ", ""]
    (OUT / "CEC_CHECK_SHEET.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "cec_check_key.json").write_text(json.dumps({"seed": 42, "cases": key}, indent=1), encoding="utf-8")
    print(f"contexts: {len(contexts)}; sheet cases: {len(picked)}")


if __name__ == "__main__":
    main()
