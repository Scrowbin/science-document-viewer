#!/usr/bin/env python3
"""
EXT-RQ5-LLM: additional local LLMs on the frozen RQ5 500-question manifest (extension; registered in
reports/revalidation/protocol/ext_rq5_llm.json before running). SELECTION-STAGE comparison: the manifest
was evaluated before and is not an independent confirmation set. C-INT is never used.

Candidates: phi4-mini (3.8B, MIT; another family at the production tier) and qwen2.5:1.5b (Apache-2.0;
separates family from size within Qwen). Reference: llama3.2:3b re-run in the same session (stored RQ5
answers come from another machine/Ollama version, so they are not used for the paired comparison).

Identical to RQ5: prompt (evaluate_rq5_llm_generation.build_prompt), gold-evidence context, temperature 0,
num_predict 256, Ollama default context window, max-over-annotator Token F1, exact-substring refusal flag,
lexical containment proxy. Boolean accuracy as in RQ5-R (first yes/no token; refusals wrong).
Decision: a candidate is an RQ6 candidate only if Token F1 - llama3.2:3b >= +0.03 with CI lower bound > 0
(paper-cluster bootstrap B=10,000 seed 42, Holm m=2). Even then it is an EXTRA RQ6 condition, never the
production default (no human faithfulness review exists for it).

Usage: python rq5ext_llm_candidates.py [--limit N]
Output: eval/phases/phase_9_generation/artifacts/rq5_ext_llm/   (resumable checkpoint.jsonl)
"""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from evaluate_rq5_llm_generation import (REFUSAL_MESSAGE, build_prompt,  # noqa: E402
                                         compute_context_containment_proxy, score_prediction_max_annotator)
from rq5_reanalysis import wilson, yes_no  # noqa: E402
from rq5_resource_profile import TreeSampler, unload_all  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

ART = ROOT / "eval" / "phases" / "phase_9_generation" / "artifacts"
URL = "http://localhost:11434"
REFERENCE = "llama3.2:3b"
CANDIDATES = ["phi4-mini", "qwen2.5:1.5b"]
OPTIONS = {"temperature": 0, "num_predict": 256}


def generate(model, prompt):
    last = None
    for attempt in range(3):
        try:
            t = time.perf_counter()
            r = requests.post(f"{URL}/api/generate", json={"model": model, "prompt": prompt, "stream": False,
                                                           "options": OPTIONS, "keep_alive": "10m"}, timeout=600)
            r.raise_for_status()
            d = r.json()
            d["wall_s"] = time.perf_counter() - t
            d["retries"] = attempt
            return d
        except Exception as e:  # logged in the record, never dropped
            last = f"{type(e).__name__}: {e}"[:300]
            time.sleep(5)
    return {"response": "", "error": last, "wall_s": None, "retries": 3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    out = ART / "rq5_ext_llm" / (f"smoke_{args.limit}" if args.limit else "")
    out.mkdir(parents=True, exist_ok=True)
    items = json.load(open(ART / "eval_sample_manifest_500q.json", encoding="utf-8"))["selected_eval_items"]
    items = items[: args.limit] if args.limit else items
    version = requests.get(f"{URL}/api/version", timeout=10).json().get("version")
    tags = {m["name"]: m["digest"] for m in requests.get(f"{URL}/api/tags", timeout=10).json()["models"]}
    models = [REFERENCE] + CANDIDATES
    for m in models:
        assert any(t == m or t == m + ":latest" for t in tags), f"model not pulled: {m}"

    ckpt = out / "checkpoint.jsonl"
    done = {}
    if ckpt.exists():
        for line in open(ckpt, encoding="utf-8"):
            r = json.loads(line)
            done[(r["model"], r["question_id"])] = r
    resources = {}
    for m in models:
        unload_all()  # no other model resident -> cold start, clean memory peak
        time.sleep(3)
        sampler = TreeSampler()
        ps = None
        with open(ckpt, "a", encoding="utf-8") as f:
            for n, it in enumerate(items, 1):
                if (m, it["question_id"]) in done:
                    continue
                ctx = "\n\n".join(it["ground_truth_evidence"])
                d = generate(m, build_prompt(it.get("paper_title", "Scientific Document"), ctx, it["question_text"]))
                if ps is None:
                    ps = requests.get(f"{URL}/api/ps", timeout=10).json().get("models", [])
                ans = d.get("response", "")
                f1, p, r, _ = score_prediction_max_annotator(ans, it["ground_truth_references"])
                rec = {"model": m, "paper_id": it["paper_arxiv_id"], "question_id": it["question_id"],
                       "question_type": it["question_type"], "prediction": ans,
                       "is_refusal": bool(REFUSAL_MESSAGE.lower() in ans.lower() or "does not contain sufficient" in ans.lower()),
                       "token_f1": round(f1, 4), "containment_proxy": round(compute_context_containment_proxy(ans, ctx), 4),
                       "wall_s": d.get("wall_s"), "load_s": (d.get("load_duration") or 0) / 1e9,
                       "eval_count": d.get("eval_count"), "eval_s": (d.get("eval_duration") or 0) / 1e9,
                       "prompt_eval_count": d.get("prompt_eval_count"), "error": d.get("error"), "retries": d.get("retries")}
                done[(m, it["question_id"])] = rec
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                if n % 50 == 0:
                    print(f"[{m}] {n}/{len(items)}", flush=True)
        mem = sampler.stop()
        resources[m] = {"digest": tags.get(m) or tags.get(m + ":latest"), "memory_this_session": mem,
                        "size_vram": next((x.get("size_vram") for x in (ps or []) if x["name"].startswith(m)), None)}
        unload_all()

    # rows per question with every model as an arm (rr.compare format)
    rows = []
    for it in items:
        rec = {"paper_id": it["paper_arxiv_id"], "question_id": it["question_id"]}
        for m in models:
            r = done[(m, it["question_id"])]
            rec[m] = {"token_f1": r["token_f1"], "is_refusal": int(r["is_refusal"]),
                      "containment_proxy": r["containment_proxy"], "error": int(bool(r["error"]))}
        rows.append(rec)
    pairs = [(c, REFERENCE) for c in CANDIDATES]
    primary = rr.family(rows, pairs, "token_f1")
    for r in primary:
        r["ci95_half_width"] = round((r["ci95"][1] - r["ci95"][0]) / 2, 4)

    per_model = {}
    for m in models:
        recs = [done[(m, it["question_id"])] for it in items]
        by_type = {}
        for t in ("extractive", "abstractive", "boolean"):
            sub = [r["token_f1"] for r in recs if r["question_type"] == t]
            by_type[t] = round(sum(sub) / len(sub), 4) if sub else None
        boo = []
        for it, r in zip(items, recs):
            if it["question_type"] == "boolean":
                gold = Counter(x["answer"] for x in it["ground_truth_references"] if x.get("type") == "boolean").most_common(1)[0][0]
                pred = None if r["is_refusal"] else yes_no(r["prediction"])
                boo.append(int(pred == gold))
        walls = sorted(r["wall_s"] for r in recs if r["wall_s"])
        tps = [r["eval_count"] / r["eval_s"] for r in recs if r.get("eval_s")]
        per_model[m] = {"token_f1_by_type": by_type, "refusals": sum(r["is_refusal"] for r in recs),
                        "errors": sum(1 for r in recs if r["error"]),
                        "boolean_accuracy": {"n": len(boo), "correct": sum(boo),
                                             "accuracy": round(sum(boo) / len(boo), 4) if boo else None,
                                             "wilson95": wilson(sum(boo), len(boo))},
                        "latency_wall_s_p50": round(walls[len(walls) // 2], 2) if walls else None,
                        "latency_wall_s_p95": round(walls[int(0.95 * (len(walls) - 1))], 2) if walls else None,
                        "tokens_per_s_mean": round(sum(tps) / len(tps), 1) if tps else None,
                        **resources.get(m, {})}
    eligible = [r["comparison"].split(" - ")[0] for r in primary if r["diff"] >= 0.03 and r["ci95"][0] > 0 and r["p_holm"] < 0.05]
    summary = {
        "experiment": "EXT-RQ5-LLM", "role": "SELECTION-STAGE EXTENSION (not independent confirmation)",
        "manifest": "eval_sample_manifest_500q.json", "questions": len(rows), "papers": len({r["paper_id"] for r in rows}),
        "ollama_version": version, "options": OPTIONS, "num_ctx": "Ollama default (same as RQ5)",
        "means": rr.arm_means(rows, models, ["token_f1", "is_refusal", "containment_proxy"]),
        "primary_family_token_f1_vs_llama3.2:3b": primary,
        "secondary_refusal_rate": rr.family(rows, pairs, "is_refusal"),
        "per_model": per_model,
        "decision_rule": "RQ6 extra condition only if Token F1 diff >= +0.03, CI lower bound > 0, Holm p < 0.05; never the production default",
        "rq6_extra_condition": eligible[0] if eligible else None,
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper"},
    }
    rr.write_outputs(out, rows, summary)
    print(json.dumps({k: summary[k] for k in ("questions", "means", "primary_family_token_f1_vs_llama3.2:3b", "rq6_extra_condition")}, indent=1))


if __name__ == "__main__":
    main()
