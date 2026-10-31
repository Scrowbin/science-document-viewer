#!/usr/bin/env python3
"""
RQ5 human-review correction: re-attribute adjudicated labels to models by answer text.

Background (audit 2026-10-29): the signed review sheet (`artifacts/review_and_signed.md`)
lists the three answers of many review items in a different Alpha/Beta/Gamma order than
the blinded package (`HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md`) and the restricted
mapping. `unblind_and_analyze_faithfulness.py` joined labels to models on
(review_id, blind_label), so labels landed on the wrong model wherever the order differed.

The label a reviewer assigned belongs to the answer text printed next to it. This script
matches every adjudicated answer to the inference-checkpoint prediction for the same
question and model, requires a unique one-to-one assignment, and only then writes a
corrected unblinded dataset plus independently recomputed summaries.

Original files are never modified. Outputs (all new):
  human_faithfulness_review/correction/remap_validation_report.csv / .json
  human_faithfulness_review/correction/faithfulness_annotations_unblinded_corrected.csv / .jsonl
  human_faithfulness_review/correction/corrected_human_review_summary.json

Run from the repository root:
  python eval/phases/phase_9_generation/scripts/remap_human_labels_by_answer.py
"""

import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ARTIFACTS = Path("eval/phases/phase_9_generation/artifacts")
REVIEW_DIR = ARTIFACTS / "human_faithfulness_review"
ADJUDICATED_CSV = REVIEW_DIR / "audit" / "faithfulness_annotations_adjudicated.csv"
PARSED_JSON = REVIEW_DIR / "audit" / "parsed_annotations_60.json"
TEMPLATE_CSV = REVIEW_DIR / "faithfulness_annotation_template_60a.csv"
MAPPING_JSON = REVIEW_DIR / "restricted_model_label_mapping.json"
CHECKPOINT_JSONL = ARTIFACTS / "rq5_inference_checkpoint.jsonl"
OUT_DIR = REVIEW_DIR / "correction"

MODELS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"]
LABELS = [
    "SUPPORTED",
    "REFUSAL_VALID",
    "MISSING_INFO - PARTIAL",
    "MISSING_INFO - UNJUSTIFIED_REFUSAL",
    "UNSUPPORTED",
    "CONTRADICTED",
]


def normalize(text: str) -> str:
    """Formatting-only normalization: blockquote markers, whitespace, surrounding quotes.

    Content (words, numbers, punctuation inside the text, case) is left untouched.
    """
    lines = [re.sub(r"^\s*>\s?", "", ln) for ln in text.replace("\r\n", "\n").split("\n")]
    s = " ".join(lines)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'`":
        s = s[1:-1].strip()
    return s


def load_inputs():
    with open(ADJUDICATED_CSV, encoding="utf-8") as f:
        adjudicated = list(csv.DictReader(f))
    with open(PARSED_JSON, encoding="utf-8") as f:
        parsed = json.load(f)
    with open(TEMPLATE_CSV, encoding="utf-8") as f:
        template = list(csv.DictReader(f))
    with open(MAPPING_JSON, encoding="utf-8") as f:
        mapping = json.load(f)["records"]
    checkpoint = []
    with open(CHECKPOINT_JSONL, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                checkpoint.append(json.loads(line))
    return adjudicated, parsed, template, mapping, checkpoint


def build_assignment(adjudicated, parsed, template, mapping, checkpoint):
    """Return (rows, problems). rows: one validation row per adjudicated record."""
    problems = []

    qid_by_review = {}
    mapping_model = {}
    for r in mapping:
        prev = qid_by_review.setdefault(r["review_item_id"], r["question_id"])
        if prev != r["question_id"]:
            problems.append(f"{r['review_item_id']}: mapping has inconsistent question_id")
        mapping_model[(r["review_item_id"], r["blind_label"])] = r["actual_model"]

    template_ctx = {}
    template_q = {}
    for t in template:
        template_ctx.setdefault(t["review_item_id"], normalize(t["context_text"]))
        template_q.setdefault(t["review_item_id"], normalize(t["question_text"]))

    parsed_by_key = {(p["review_id"], p["blind_label"]): p for p in parsed}

    ckpt = defaultdict(dict)  # question_id -> model -> record
    for rec in checkpoint:
        if rec["model"] in ckpt[rec["question_id"]]:
            problems.append(f"checkpoint: duplicate record for {rec['question_id']} / {rec['model']}")
        ckpt[rec["question_id"]][rec["model"]] = rec

    by_review = defaultdict(list)
    for a in adjudicated:
        by_review[a["review_id"]].append(a)

    rows = []
    for review_id in sorted(by_review):
        items = by_review[review_id]
        qid = qid_by_review.get(review_id)
        preds = ckpt.get(qid, {})
        if qid is None or set(preds) != set(MODELS):
            problems.append(f"{review_id}: missing checkpoint records (question_id={qid}, models={sorted(preds)})")
            continue
        if len(items) != 3 or {i["blind_label"] for i in items} != {"Model_Alpha", "Model_Beta", "Model_Gamma"}:
            problems.append(f"{review_id}: expected one row per blind label, got {[i['blind_label'] for i in items]}")

        norm_pred = {m: normalize(preds[m]["prediction"] or "") for m in MODELS}
        # Two models producing the same text cannot be told apart by answer matching.
        collisions = [m for m in MODELS if list(norm_pred.values()).count(norm_pred[m]) > 1]

        question_text = normalize(preds[MODELS[0]]["question_text"])
        assigned = []
        for a in items:
            p = parsed_by_key.get((review_id, a["blind_label"]), {})
            checks = []
            if normalize(p.get("question", "")) != question_text:
                checks.append("question_text_mismatch")
            if template_q.get(review_id) != question_text:
                checks.append("template_question_mismatch")
            if normalize(a["relevant_context"]) != template_ctx.get(review_id):
                checks.append("context_mismatch")

            ans_raw = a["answer"]
            ans_norm = normalize(ans_raw)
            exact = [m for m in MODELS if (preds[m]["prediction"] or "") == ans_raw]
            normed = [m for m in MODELS if norm_pred[m] == ans_norm]
            if exact:
                matches, method = exact, "exact"
            else:
                matches, method = normed, "normalized"

            status = "VALID"
            if len(matches) == 0:
                status = "UNRESOLVED_NO_MATCH"
            elif len(matches) > 1:
                labels = {
                    b["final_primary_label"] for b in items if normalize(b["answer"]) == ans_norm
                }
                # Identical answers: harmless only if every copy received the same label.
                status = "VALID_IDENTICAL_ANSWERS_SAME_LABEL" if len(labels) == 1 else "UNRESOLVED_MULTIPLE_MATCH"
            if checks:
                status = "UNRESOLVED_" + "+".join(checks) if status.startswith("VALID") else status

            rows.append({
                "review_id": review_id,
                "question_id": qid,
                "blind_label_in_signed_sheet": a["blind_label"],
                "model_by_original_mapping": mapping_model.get((review_id, a["blind_label"])),
                "matched_models": ";".join(matches),
                "matched_checkpoint_item_index": ";".join(str(preds[m]["item_index"]) for m in matches),
                "match_method": method,
                "identical_answer_collision": bool(collisions),
                "status": status,
                "final_primary_label": a["final_primary_label"],
            })
            assigned.append(rows[-1])

        # Enforce a bijection among answers of this question.
        single = [r["matched_models"] for r in assigned if r["status"] == "VALID"]
        dup = [m for m, c in Counter(single).items() if c > 1]
        for r in assigned:
            if r["status"] == "VALID" and r["matched_models"] in dup:
                r["status"] = "UNRESOLVED_CONFLICTING_ASSIGNMENT"
        if collisions:
            # Assign identical-answer rows to the remaining models deterministically: the label is the
            # same for all copies (checked above), so attribution cannot change any count.
            taken = {r["matched_models"] for r in assigned if r["status"] == "VALID"}
            remaining = [m for m in MODELS if m not in taken]
            for r in assigned:
                if r["status"] == "VALID_IDENTICAL_ANSWERS_SAME_LABEL":
                    cands = [m for m in str(r["matched_models"]).split(";") if m in remaining]
                    r["assigned_model"] = cands[0] if cands else ""
                    if cands:
                        remaining.remove(cands[0])
        for r in assigned:
            if r["status"] == "VALID":
                r["assigned_model"] = r["matched_models"]
            r.setdefault("assigned_model", "")
            if r["status"] == "VALID_IDENTICAL_ANSWERS_SAME_LABEL":
                # Attribution among identical answers is arbitrary and cannot affect any count.
                r["attribution_changed"] = "n/a_identical_answer"
            else:
                r["attribution_changed"] = (
                    r["assigned_model"] != r["model_by_original_mapping"] if r["assigned_model"] else ""
                )

    return rows, problems


def label_moves(rows):
    """Per-model label count differences, original join vs corrected attribution."""
    orig = Counter((r["model_by_original_mapping"], r["final_primary_label"]) for r in rows)
    corr = Counter((r["assigned_model"], r["final_primary_label"]) for r in rows if r["assigned_model"])
    return {
        f"{m} | {lbl}": {"original": orig.get((m, lbl), 0), "corrected": corr.get((m, lbl), 0)}
        for m in MODELS for lbl in LABELS
        if orig.get((m, lbl), 0) != corr.get((m, lbl), 0)
    }


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def summarize(records):
    """Independent recomputation of the human-review summaries (no reuse of old scripts)."""
    out: dict = {"per_model": {}, "per_label": {}, "correlations": {}}
    for m in MODELS:
        sub = [r for r in records if r["actual_model"] == m]
        n = len(sub)
        c = Counter(r["final_primary_label"] for r in sub)
        out["per_model"][m] = {
            "n": n,
            "counts": {lbl: c.get(lbl, 0) for lbl in LABELS},
            "supported_rate": c["SUPPORTED"] / n,
            "grounded_compliance_rate": (c["SUPPORTED"] + c["REFUSAL_VALID"]) / n,
            "unsupported_or_contradicted_rate": (c["UNSUPPORTED"] + c["CONTRADICTED"]) / n,
            "unjustified_refusal_rate": c["MISSING_INFO - UNJUSTIFIED_REFUSAL"] / n,
            "partial_rate": c["MISSING_INFO - PARTIAL"] / n,
            "sample_mean_token_f1": sum(r["token_f1"] for r in sub) / n,
            "sample_mean_containment_proxy": sum(r["automated_containment_proxy"] for r in sub) / n,
            "sample_refusals_by_detector": sum(1 for r in sub if r["is_refusal"]),
        }
    for lbl in LABELS:
        sub = [r for r in records if r["final_primary_label"] == lbl]
        out["per_label"][lbl] = {
            "count": len(sub),
            "mean_token_f1": (sum(r["token_f1"] for r in sub) / len(sub)) if sub else None,
            "mean_containment_proxy": (sum(r["automated_containment_proxy"] for r in sub) / len(sub)) if sub else None,
        }
    f1 = [r["token_f1"] for r in records]
    cp = [r["automated_containment_proxy"] for r in records]
    is_sup = [1.0 if r["final_primary_label"] == "SUPPORTED" else 0.0 for r in records]
    is_grd = [1.0 if r["final_primary_label"] in ("SUPPORTED", "REFUSAL_VALID") else 0.0 for r in records]
    is_hal = [1.0 if r["final_primary_label"] in ("UNSUPPORTED", "CONTRADICTED") else 0.0 for r in records]
    out["correlations"] = {
        "point_biserial_supported_vs_token_f1": pearson(is_sup, f1),
        "point_biserial_supported_vs_containment": pearson(is_sup, cp),
        "point_biserial_grounded_vs_token_f1": pearson(is_grd, f1),
        "point_biserial_grounded_vs_containment": pearson(is_grd, cp),
        "point_biserial_unsupported_or_contradicted_vs_containment": pearson(is_hal, cp),
        "n": len(records),
    }
    return out


def main():
    adjudicated, parsed, template, mapping, checkpoint = load_inputs()
    if len(adjudicated) != 60:
        sys.exit(f"Expected 60 adjudicated rows, found {len(adjudicated)}")

    rows, problems = build_assignment(adjudicated, parsed, template, mapping, checkpoint)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0].keys()) if rows else []
    with open(OUT_DIR / "remap_validation_report.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    status_counts = Counter(r["status"] for r in rows)
    assigned = [r for r in rows if r["status"].startswith("VALID")]
    per_q_models = defaultdict(list)
    for r in assigned:
        per_q_models[r["review_id"]].append(r["assigned_model"])
    bijective = all(sorted(v) == sorted(MODELS) for v in per_q_models.values()) and len(per_q_models) == 20
    accepted = len(rows) == 60 and len(assigned) == 60 and bijective and not problems

    report = {
        "accepted": accepted,
        "records": len(rows),
        "status_counts": dict(status_counts),
        "bijective_per_question": bijective,
        "attribution_changed_vs_original_mapping": sum(1 for r in rows if r.get("attribution_changed") is True),
        "attribution_unchanged_vs_original_mapping": sum(1 for r in rows if r.get("attribution_changed") is False),
        # Labels that end up on a different model than the original join put them on.
        "label_moved_to_different_model": label_moves(rows),
        "match_method_counts": dict(Counter(r["match_method"] for r in rows)),
        "identical_answer_collision_questions": sorted({r["review_id"] for r in rows if r["identical_answer_collision"]}),
        "problems": problems,
    }
    with open(OUT_DIR / "remap_validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if not accepted:
        print("\nCorrection NOT accepted: unblinded analysis stopped. See remap_validation_report.csv.")
        sys.exit(1)

    ckpt = {(r["question_id"], r["model"]): r for r in checkpoint}
    adj = {(a["review_id"], a["blind_label"]): a for a in adjudicated}
    corrected = []
    for r in rows:
        a = adj[(r["review_id"], r["blind_label_in_signed_sheet"])]
        c = ckpt[(r["question_id"], r["assigned_model"])]
        corrected.append({
            "review_id": r["review_id"],
            "question_id": r["question_id"],
            "paper_arxiv_id": c["paper_arxiv_id"],
            "manifest_item_index": c["item_index"],
            "actual_model": r["assigned_model"],
            "blind_label_in_signed_sheet": r["blind_label_in_signed_sheet"],
            "model_by_original_mapping": r["model_by_original_mapping"],
            "attribution_changed": r["attribution_changed"],
            "match_method": r["match_method"],
            "final_primary_label": a["final_primary_label"],
            "final_secondary_label": a["final_secondary_label"],
            "is_adjudicated_change": a["is_adjudicated_change"],
            "original_primary_label": a["original_primary_label"],
            "is_refusal": c["is_refusal"],
            "token_f1": c["token_f1"],
            "automated_containment_proxy": c["automated_containment_proxy"],
            "latency_s": c["latency_s"],
            "tokens_per_second": c["tokens_per_second"],
            "answer": a["answer"],
        })
    with open(OUT_DIR / "faithfulness_annotations_unblinded_corrected.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(corrected[0].keys()))
        w.writeheader()
        w.writerows(corrected)
    with open(OUT_DIR / "faithfulness_annotations_unblinded_corrected.jsonl", "w", encoding="utf-8") as f:
        for rec in corrected:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    summary = summarize(corrected)
    summary["source"] = "faithfulness_annotations_unblinded_corrected.csv (answer-text attribution)"
    with open(OUT_DIR / "corrected_human_review_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
