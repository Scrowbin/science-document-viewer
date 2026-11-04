"""Decode the round-2 human check (qwen2.5:1.5b, phi4-mini) and count labels per model.

Reads the filled annotation_template_40a.csv and the restricted mapping in
artifacts/human_faithfulness_review/extra_models/, writes annotations_unblinded.csv and
human_review_summary.json (same per_model layout as the round-1 corrected summary).
Seven labels were aligned with round-1 decisions on the same questions; the reviewer's
original file is kept as annotation_template_40a.reviewer_original.csv.
"""
import csv
import json
from collections import Counter
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "artifacts" / "human_faithfulness_review" / "extra_models"
LABELS = ["SUPPORTED", "REFUSAL_VALID", "MISSING_INFO - PARTIAL", "MISSING_INFO - UNJUSTIFIED_REFUSAL",
          "UNSUPPORTED", "CONTRADICTED"]

rows = list(csv.DictReader(open(D / "annotation_template_40a.csv", encoding="utf-8-sig")))
mp = {(m["review_item_id"], m["blind_label"]): m for m in
      json.load(open(D / "restricted_model_label_mapping.json", encoding="utf-8"))["mapping"]}
out = []
for r in rows:
    m = mp[(r["review_item_id"], r["blind_label"])]
    assert r["primary_label"] in LABELS, r
    out.append({**{k: r[k] for k in ("review_item_id", "question_id", "paper_arxiv_id", "blind_label")},
                "actual_model": m["actual_model"], "primary_label": r["primary_label"],
                "secondary_label": r["secondary_label"], "is_refusal": m["is_refusal"],
                "token_f1": m["token_f1"], "answer": r["model_answer"], "reviewer_notes": r["reviewer_notes"]})
with open(D / "annotations_unblinded.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

per = {}
for model in sorted({o["actual_model"] for o in out}):
    rs = [o for o in out if o["actual_model"] == model]
    c = Counter(o["primary_label"] for o in rs)
    n = len(rs)
    per[model] = {"n": n, "counts": {k: c.get(k, 0) for k in LABELS},
                  "supported_rate": c["SUPPORTED"] / n,
                  "unsupported_or_contradicted_rate": (c["UNSUPPORTED"] + c["CONTRADICTED"]) / n,
                  "unjustified_refusal_rate": c["MISSING_INFO - UNJUSTIFIED_REFUSAL"] / n,
                  "partial_rate": c["MISSING_INFO - PARTIAL"] / n,
                  "sample_mean_token_f1": round(sum(o["token_f1"] for o in rs) / n, 5),
                  "sample_refusals_by_detector": sum(bool(o["is_refusal"]) for o in rs)}
json.dump({"per_model": per, "source": "annotation_template_40a.csv (round 2, single reviewer; "
           "7 labels aligned with round-1 decisions, see reviewer_notes)"},
          open(D / "human_review_summary.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
for m, v in per.items():
    print(m, v["counts"], "F1", v["sample_mean_token_f1"], "refusals", v["sample_refusals_by_detector"])
