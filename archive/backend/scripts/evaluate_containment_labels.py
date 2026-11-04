"""
Evaluation and Validation of Ground-Truth Evidence Containment Matcher
Evaluates calibration set (N=80) and fresh validation queue (N=35 / N=34 sanitized)
using user labels to compute out-of-sample precision, recall, and F1 under
the pre-registered strict evidence containment formula (eval_common.py).
"""

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "backend" / "scripts"))

from eval_common import is_chunk_hit, clean_evidence, STOPWORDS

EVAL_PREP = WORKSPACE_ROOT / "eval" / "prepared"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def evaluate_items_strict(items, label_key_fn):
    """Evaluate items using the canonical is_chunk_hit function across tau values."""
    results = {}
    for tau in [0.20, 0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80]:
        tp = fp = tn = fn = 0
        for item in items:
            chunk = {"text": item.get("chunk_text", ""), "paper_arxiv_id": item.get("aid", "")}
            pred = 1 if is_chunk_hit(
                chunk,
                item.get("aid", ""),
                verbatim_evidence_quote=item.get("ev_ref", ""),
                tau=tau,
            ) else 0
            actual = label_key_fn(item)
            if pred == 1 and actual == 1:
                tp += 1
            elif pred == 1 and actual == 0:
                fp += 1
            elif pred == 0 and actual == 0:
                tn += 1
            else:
                fn += 1
        total = len(items)
        acc = (tp + tn) / total if total > 0 else 0.0
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        results[f"{tau:.2f}"] = {
            "tau": tau,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "accuracy": round(acc * 100, 2),
            "precision": round(prec * 100, 2),
            "recall": round(rec * 100, 2),
            "f1": round(f1 * 100, 2),
        }
    return results


def print_table(title, res):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print("tau\tTP\tFP\tTN\tFN\tAcc\tPrec\tRec\tF1")
    for tau_str, m in res.items():
        print(
            f"{m['tau']:.2f}\t{m['tp']}\t{m['fp']}\t{m['tn']}\t{m['fn']}\t"
            f"{m['accuracy']}%\t{m['precision']}%\t{m['recall']}%\t{m['f1']}%"
        )


def main():
    calib_file = EVAL_PREP / "containment_label_queue_labeled.json"
    fresh_file = EVAL_PREP / "new_containment_validation_queue.json"

    with open(calib_file, "r", encoding="utf-8") as f:
        calib_items = json.load(f)

    with open(fresh_file, "r", encoding="utf-8") as f:
        fresh_items_raw = json.load(f)

    # Sanitize Pair 13 (FLOAT SELECTED: Table 1: Dataset)
    fresh_items_sanitized = [
        item for item in fresh_items_raw
        if not item.get("ev_ref", "").strip().upper().startswith("FLOAT SELECTED")
    ]

    print(f"[CONTAINMENT-EVAL] Loaded {len(calib_items)} calibration pairs.")
    print(f"[CONTAINMENT-EVAL] Loaded {len(fresh_items_raw)} fresh validation pairs (raw).")
    print(f"[CONTAINMENT-EVAL] Filtered {len(fresh_items_raw) - len(fresh_items_sanitized)} contaminated float pair(s) -> {len(fresh_items_sanitized)} sanitized pairs.")
    print(f"[CONTAINMENT-EVAL] Canonical stopwords: {len(STOPWORDS)} words.")

    calib_res = evaluate_items_strict(calib_items, lambda x: x["human_label"])
    fresh_raw_res = evaluate_items_strict(fresh_items_raw, lambda x: x["user_label"])
    fresh_sanitized_res = evaluate_items_strict(fresh_items_sanitized, lambda x: x["user_label"])

    combined_raw = calib_items + fresh_items_raw
    combined_raw_res = evaluate_items_strict(
        combined_raw,
        lambda x: x.get("user_label", x.get("human_label"))
    )

    combined_sanitized = calib_items + fresh_items_sanitized
    combined_sanitized_res = evaluate_items_strict(
        combined_sanitized,
        lambda x: x.get("user_label", x.get("human_label"))
    )

    print_table("CALIBRATION SET (N=80) -- STRICT FORMULA", calib_res)
    print_table("FRESH OUT-OF-SAMPLE VALIDATION QUEUE (RAW N=35) -- STRICT FORMULA", fresh_raw_res)
    print_table("FRESH OUT-OF-SAMPLE VALIDATION QUEUE (SANITIZED N=34) -- STRICT FORMULA", fresh_sanitized_res)
    print_table("COMBINED SET (RAW N=115) -- STRICT FORMULA", combined_raw_res)
    print_table("COMBINED SET (SANITIZED N=114) -- STRICT FORMULA", combined_sanitized_res)

    # Output detailed discrepancy breakdown for fresh sanitized set at tau*=0.55
    print("\n" + "=" * 80)
    print("DISCREPANCY AUDIT ON FRESH SANITIZED SET AT tau* = 0.55")
    print("=" * 80)
    for idx, item in enumerate(fresh_items_sanitized, 1):
        chunk = {"text": item.get("chunk_text", ""), "paper_arxiv_id": item.get("aid", "")}
        pred = 1 if is_chunk_hit(
            chunk,
            item.get("aid", ""),
            verbatim_evidence_quote=item.get("ev_ref", ""),
            tau=0.55,
        ) else 0
        actual = item["user_label"]
        if pred != actual:
            err_type = "FALSE POSITIVE (Pred=1, User=0)" if pred == 1 else "FALSE NEGATIVE (Pred=0, User=1)"
            print(f"\nPair {idx:02d} [{err_type}]")
            print(f"  QID: {item['qid']} | Paper: {item['aid']}")
            print(f"  Question: {item['question']}")
            print(f"  User Reason: {item.get('user_reason', 'N/A')}")
            print(f"  Gold Evidence ({len(item['ev_ref'].split())} w): \"{item['ev_ref'][:120]}...\"")
            print(f"  Chunk Preview: \"{item['chunk_text'][:120]}...\"")

    out_metrics = {
        "calibration_n80": calib_res,
        "fresh_validation_raw_n35": fresh_raw_res,
        "fresh_validation_sanitized_n34": fresh_sanitized_res,
        "combined_raw_n115": combined_raw_res,
        "combined_sanitized_n114": combined_sanitized_res,
    }
    out_file = EVAL_PREP / "containment_validation_metrics.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_metrics, f, indent=2)

    print(f"\n[CONTAINMENT-EVAL] Saved metrics artifact to {out_file.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()

