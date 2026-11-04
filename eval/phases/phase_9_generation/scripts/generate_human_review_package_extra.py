"""Blinded human-check package for the two extra generation models (qwen2.5:1.5b, phi4-mini).

Uses the same 20 questions as the first human check (stride 25 over the 500-question
generation manifest), the same gold-evidence contexts and the same 6-label rubric. Answers
come from the existing extra-LLM run (generation_extra_llms/checkpoint.jsonl); no new
inference is done.

Each question shows the two answers as Model_Delta / Model_Epsilon; the order is balanced
(each model is Delta on 10 questions) and shuffled with seed 42. The label-to-model mapping
is written to a separate restricted file that the reviewer should not open before labelling.

Outputs (artifacts/human_faithfulness_review/extra_models/):
  REVIEW_SHEET.md                         reviewer sheet (rubric + 20 questions x 2 answers)
  annotation_template_40a.csv / .jsonl    blank labels to fill in
  restricted_model_label_mapping.json     blind label -> model (do not open before labelling)
"""
import csv
import json
import random
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parents[1]
ART = PHASE_DIR / "artifacts"
MANIFEST = ART / "eval_sample_manifest_500q.json"
CHECKPOINT = ART / "generation_extra_llms" / "checkpoint.jsonl"
OUT = ART / "human_faithfulness_review" / "extra_models"

MODELS = ["qwen2.5:1.5b", "phi4-mini"]
LABELS = ["Model_Delta", "Model_Epsilon"]
SEED = 42
STRIDE, COUNT = 25, 20  # same sample as the first human check

RUBRIC = """\
## How to label

Judge each answer **only against the context shown** (no outside knowledge). Give one
primary label; if several problems occur, use the first that applies in this order:
CONTRADICTED > UNSUPPORTED > MISSING_INFO - UNJUSTIFIED_REFUSAL > MISSING_INFO - PARTIAL >
REFUSAL_VALID > SUPPORTED. Other problems go in the secondary label / notes.

| Label | Meaning |
| :--- | :--- |
| `SUPPORTED` | Every substantive claim is stated in or follows from the context. |
| `REFUSAL_VALID` | The model refused, and the context really does not contain the answer. |
| `MISSING_INFO - PARTIAL` | Grounded, but leaves out a key part of the answer that the context contains. |
| `MISSING_INFO - UNJUSTIFIED_REFUSAL` | The model refused although the context contains the answer. |
| `UNSUPPORTED` | At least one claim is not in the context (but does not contradict it). |
| `CONTRADICTED` | At least one claim conflicts with the context. |

Fill in `primary_label`, optionally `secondary_label`, a short `supporting_evidence` quote
for supported claims, and `reviewer_notes`, in `annotation_template_40a.csv` (or .jsonl).
"""


def main():
    items = json.load(open(MANIFEST, encoding="utf-8"))["selected_eval_items"]
    assert len(items) == 500, len(items)
    preds = {}
    with open(CHECKPOINT, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                if r["model"] in MODELS:
                    preds[(r["model"], r["question_id"])] = r

    sample = [items[i * STRIDE] for i in range(COUNT)]
    orders = [tuple(MODELS), tuple(reversed(MODELS))] * (COUNT // 2)
    random.Random(SEED).shuffle(orders)

    OUT.mkdir(parents=True, exist_ok=True)
    md = ["# Human check: extra generation models (20 questions x 2 answers)", "",
          "Answers are shown as `Model_Delta` and `Model_Epsilon`; which model is which changes",
          "from question to question. Do not open `restricted_model_label_mapping.json` before",
          "finishing the labels.", "", RUBRIC, "## Questions", ""]
    template, mapping = [], []
    for n, (it, order) in enumerate(zip(sample, orders), start=1):
        rid = f"REV-{n:02d}"
        ctx = "\n\n".join(it["ground_truth_evidence"])
        md += [f"### {rid} (manifest item #{it['item_index']}, arXiv:{it['paper_arxiv_id']})",
               f"**Paper:** *{it.get('paper_title', '')}*  ", f"**Question:** {it['question_text']}", "",
               "<details><summary>Context given to the model</summary>", "", "```text", ctx, "```",
               "</details>", ""]
        for lbl, model in zip(LABELS, order):
            rec = preds[(model, it["question_id"])]
            ans = rec["prediction"].strip()
            md += [f"**{lbl}:**", ""] + [f"> {x}" if x else ">" for x in ans.split("\n")] + [""]
            template.append({"review_item_id": rid, "manifest_item_index": it["item_index"],
                             "question_id": it["question_id"], "paper_arxiv_id": it["paper_arxiv_id"],
                             "blind_label": lbl, "question_text": it["question_text"],
                             "context_text": ctx, "model_answer": ans, "primary_label": "",
                             "secondary_label": "", "supporting_evidence": "", "reviewer_notes": ""})
            mapping.append({"review_item_id": rid, "question_id": it["question_id"], "blind_label": lbl,
                            "actual_model": model, "question_type": rec.get("question_type"),
                            "is_refusal": rec.get("is_refusal"), "token_f1": rec.get("token_f1")})
        md += ["---", ""]

    (OUT / "REVIEW_SHEET.md").write_text("\n".join(md), encoding="utf-8")
    with open(OUT / "annotation_template_40a.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(template[0]))
        w.writeheader()
        w.writerows(template)
    with open(OUT / "annotation_template_40a.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in template)
    json.dump({"seed": SEED, "models": MODELS, "labels": LABELS, "mapping": mapping},
              open(OUT / "restricted_model_label_mapping.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"{len(sample)} questions, {len(template)} answers -> {OUT}")
    for m in MODELS:
        print(m, "as Delta:", sum(1 for o in orders if o[0] == m))


if __name__ == "__main__":
    main()
