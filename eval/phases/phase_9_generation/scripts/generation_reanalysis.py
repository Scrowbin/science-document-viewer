#!/usr/bin/env python3
"""
generation re-analysis: reanalysis of the stored the generation experiment generations (no inference). Pre-registered in
protocol rq5_rq6.json (archived) "generation re-analysis". Historical files are read only.

1. Boolean accuracy on the Boolean manifest items: first yes/no token of the prediction vs the majority
   yes/no reference; refusals count as wrong; answers with no yes/no token are reported as unparseable (wrong).
2. Paired paper-cluster bootstrap (B = 10,000) of refusal-rate differences between models.
3. Token F1 on questions answered by both models of a pair (selection-affected; descriptive).
4. Human review counts per model with Wilson 95% intervals (corrected attribution).
Output: eval/phases/phase_9_generation/artifacts/generation_reanalysis/
"""

import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common.stats import paired_cluster_bootstrap  # noqa: E402

ART = ROOT / "eval" / "phases" / "phase_9_generation" / "artifacts"
OUT = ART / "generation_reanalysis"
MODELS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"]
B, SEED = 10000, 42


def yes_no(text):
    m = re.search(r"\b(yes|no)\b", text.lower())
    if not m:
        return None
    return "Yes" if m.group(1) == "yes" else "No"


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def main():
    bench = json.load(open(ART / "rq5_llm_generation_benchmark_500q.json", encoding="utf-8"))
    man = {i["question_id"]: i for i in json.load(open(ART / "eval_sample_manifest_500q.json", encoding="utf-8"))["selected_eval_items"]}
    recs = {m: {r["question_id"]: r for r in bench["detailed_records"][m]} for m in MODELS}

    # 1. Boolean accuracy
    boolean = {}
    for m in MODELS:
        rows = []
        for qid, item in man.items():
            if item["question_type"] != "boolean":
                continue
            gold = Counter(r["answer"] for r in item["ground_truth_references"] if r.get("type") == "boolean").most_common(1)[0][0]
            r = recs[m][qid]
            pred = None if r["is_refusal"] else yes_no(r["prediction"])
            rows.append({"paper_id": item["paper_arxiv_id"], "question_id": qid, "gold": gold, "pred": pred,
                         "refusal": r["is_refusal"], "correct": int(pred == gold)})
        n = len(rows)
        k = sum(r["correct"] for r in rows)
        boolean[m] = {"n": n, "correct": k, "accuracy": round(k / n, 4), "wilson95": wilson(k, n),
                      "refusals": sum(r["refusal"] for r in rows),
                      "unparseable": sum(1 for r in rows if not r["refusal"] and r["pred"] is None),
                      "token_f1_same_items": round(sum(recs[m][r["question_id"]]["token_f1"] for r in rows) / n, 4)}

    def paper_scores(m, field):
        out = {}
        for qid, item in man.items():
            out.setdefault(item["paper_arxiv_id"], []).append(float(recs[m][qid][field]))
        return out

    pairs = [("llama3.2:3b", "llama3.2:1b"), ("llama3.2:3b", "qwen2.5:0.5b"), ("llama3.2:1b", "qwen2.5:0.5b")]
    refusal = {}
    for a, b in pairs:
        d, ci, p = paired_cluster_bootstrap(paper_scores(b, "is_refusal"), paper_scores(a, "is_refusal"), n_bootstraps=B, seed=SEED)
        refusal[f"{a} - {b}"] = {"diff_refusal_rate": round(d, 4), "ci95": [round(ci[0], 4), round(ci[1], 4)], "p_raw": round(p, 4)}

    both = {}
    for a, b in pairs:
        qids = [q for q in man if not recs[a][q]["is_refusal"] and not recs[b][q]["is_refusal"]]
        pa, pb = {}, {}
        for q in qids:
            p = man[q]["paper_arxiv_id"]
            pa.setdefault(p, []).append(recs[a][q]["token_f1"])
            pb.setdefault(p, []).append(recs[b][q]["token_f1"])
        d, ci, pv = paired_cluster_bootstrap(pb, pa, n_bootstraps=B, seed=SEED)
        both[f"{a} - {b}"] = {"questions": len(qids), "papers": len(pa),
                              "mean_f1": {a: round(sum(recs[a][q]["token_f1"] for q in qids) / len(qids), 4),
                                          b: round(sum(recs[b][q]["token_f1"] for q in qids) / len(qids), 4)},
                              "diff": round(d, 4), "ci95": [round(ci[0], 4), round(ci[1], 4)],
                              "note": "selection-affected: the subset depends on both models' refusal behaviour"}

    rows = list(csv.DictReader(open(ART / "human_faithfulness_review" / "correction" / "faithfulness_annotations_unblinded_corrected.csv", encoding="utf-8")))
    canon = lambda s: s.replace("MISSING_INFO - ", "")
    human = {}
    for m in MODELS:
        labels = Counter(canon(r["final_primary_label"]) for r in rows if r["actual_model"] == m)
        n = sum(labels.values())
        groups = {"SUPPORTED": labels["SUPPORTED"], "UNSUPPORTED_OR_CONTRADICTED": labels["UNSUPPORTED"] + labels["CONTRADICTED"],
                  "UNJUSTIFIED_REFUSAL": labels["UNJUSTIFIED_REFUSAL"], "GROUNDED_COMPLIANCE": labels["SUPPORTED"] + labels["REFUSAL_VALID"]}
        human[m] = {"n": n, "labels": dict(labels), **{g: {"k": k, "wilson95": wilson(k, n)} for g, k in groups.items()}}

    summary = {"experiment": "RQ5-R", "inference": False, "boolean_accuracy": boolean,
               "refusal_rate_differences": refusal, "answered_by_both_token_f1": both, "human_review_wilson": human,
               "bootstrap": {"B": B, "seed": SEED, "unit": "paper (250 clusters)"}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({"boolean_accuracy": {m: (v["accuracy"], v["wilson95"]) for m, v in boolean.items()}}, indent=1))


if __name__ == "__main__":
    main()
