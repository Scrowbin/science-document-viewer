#!/usr/bin/env python3
"""
RQ6 blinded human-review package (registered: reports/revalidation/protocol/rq6_amendment.json "human_review").

Draws 34 C-INT questions (seed 42, stratified by question type in proportion to C-INT), takes the answers of the
3 NEW conditions (one per RQ6 LLM) from the RQ6 C-INT checkpoint, and writes 3 sheets. Each sheet holds one answer
per question; the condition shown for each question rotates across sheets, so every sheet mixes all models.
Labels are hidden; the mapping goes to a restricted file. 20 of the 102 answers (seeded) are marked for a second
reviewer, in a separate sheet. Run after RQ6 C-INT, before anyone reads the answers.

Usage: python rq6_review_package.py
Output: eval/phases/phase_11_integrated/artifacts/rq6_human_review/
"""

import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_runner as rr  # noqa: E402

ART = ROOT / "eval" / "phases" / "phase_11_integrated" / "artifacts"
CKPT = ART / "rq6_C-INT" / "checkpoint.jsonl"
CONFIG = ROOT / "reports" / "revalidation" / "protocol" / "rq6_config.json"
OUT = ART / "rq6_human_review"
N_Q, N_SECOND, SEED = 34, 20, 42
LABELS = ["SUPPORTED", "PARTIAL", "UNSUPPORTED", "CONTRADICTED", "REFUSAL_VALID", "UNJUSTIFIED_REFUSAL"]
RUBRIC = """**Labels** (judge only against the context shown, not your own knowledge):
- **SUPPORTED**: every claim in the answer is stated in or directly follows from the context.
- **PARTIAL**: the main point is supported, but the answer adds a claim the context doesn't support, or misses a key part.
- **UNSUPPORTED**: the main point is not in the context (made up or from outside knowledge).
- **CONTRADICTED**: the answer says something the context contradicts.
- **REFUSAL_VALID**: the answer refuses, and the context really doesn't contain the answer.
- **UNJUSTIFIED_REFUSAL**: the answer refuses, but the context does contain the answer.
"""


def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"{OUT} already exists; refusing to overwrite a frozen package")
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    new_conds = [c["name"] for c in cfg["conditions"]["C-INT"] if c["system"] == "NEW"]
    assert len(new_conds) == 3, new_conds
    recs = {}
    for line in open(CKPT, encoding="utf-8"):
        r = json.loads(line)
        recs[(r["condition"], r["question_id"])] = r
    items = {it["question_id"]: it for it in rr.load_cohort("C-INT")["items"]}
    complete = sorted(q for q in items if all((c, q) in recs for c in new_conds))

    # Stratified draw by question type, proportional to C-INT
    rng = random.Random(SEED)
    by_type = {}
    for q in complete:
        by_type.setdefault(items[q]["question_type"], []).append(q)
    total = len(complete)
    quota = {t: round(N_Q * len(v) / total) for t, v in by_type.items()}
    while sum(quota.values()) != N_Q:
        t = max(by_type, key=lambda k: len(by_type[k])) if sum(quota.values()) < N_Q else max(quota, key=quota.get)
        quota[t] += 1 if sum(quota.values()) < N_Q else -1
    chosen = []
    for t in sorted(by_type):
        chosen += rng.sample(by_type[t], quota[t])
    rng.shuffle(chosen)

    # Rotate conditions across 3 sheets: sheet s shows condition (i + s) % 3 for question i
    entries, mapping = [], {}
    for i, q in enumerate(chosen):
        for s in range(3):
            cond = new_conds[(i + s) % 3]
            r = recs[(cond, q)]
            aid = f"A{len(entries) + 1:03d}"
            entries.append({"answer_id": aid, "sheet": s + 1, "question_id": q, "answer": r["prediction"],
                            "context": r.get("context_text", ""), "question": items[q]["question"]})
            mapping[aid] = {"condition": cond, "llm": r["llm"], "question_id": q,
                            "answer_sha256": hashlib.sha256(r["prediction"].encode("utf-8")).hexdigest()}
    second = sorted(random.Random(SEED + 1).sample([e["answer_id"] for e in entries], N_SECOND))

    OUT.mkdir(parents=True, exist_ok=True)

    def sheet(title, es):
        lines = [f"# {title}", "", "Read the question and the context, then judge the answer. Tick exactly one label.", "",
                 RUBRIC, ""]
        for e in es:
            lines += [f"## {e['answer_id']}", "", f"**Question:** {e['question']}", "",
                      "<details><summary>Context given to the model</summary>", "", "```text", e["context"] or "(no context: the system refused before generation)", "```", "</details>", "",
                      "**Answer:**", "", "> " + (e["answer"] or "(empty)").replace("\n", "\n> "), "",
                      "- **Label:** " + "   ".join(f"`[ ] {l}`" for l in LABELS),
                      "- **Note (optional):** ", ""]
        return "\n".join(lines)

    for s in (1, 2, 3):
        (OUT / f"REVIEW_SHEET_{s}.md").write_text(sheet(f"RQ6 Human Review: Sheet {s} of 3 (complete in separate sittings)",
                                                        [e for e in entries if e["sheet"] == s]), encoding="utf-8")
    (OUT / "REVIEW_SHEET_SECOND_REVIEWER.md").write_text(
        sheet("RQ6 Human Review: Second Reviewer (20 answers)", [e for e in entries if e["answer_id"] in second]), encoding="utf-8")
    (OUT / "restricted_mapping.json").write_text(json.dumps(mapping, indent=1), encoding="utf-8")
    manifest = {"seed": SEED, "questions": chosen, "question_types": dict(Counter(items[q]["question_type"] for q in chosen)),
                "new_conditions": new_conds, "answers": len(entries), "second_reviewer_ids": second,
                "checkpoint_sha256": hashlib.sha256(CKPT.read_bytes()).hexdigest(),
                "note": "Do not open restricted_mapping.json before all labels are recorded."}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"{len(entries)} answers on 3 sheets; second reviewer: {len(second)}; types {manifest['question_types']}")


if __name__ == "__main__":
    main()
