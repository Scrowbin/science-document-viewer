#!/usr/bin/env python3
"""
Memory check for the combination run's generation phase (before the full run).

Generates ~100 llama3.2:3b answers from the contexts saved by the profile run (artifacts/combinations/profile/),
with the runner's own prompt, options and unload-every-UNLOAD_EVERY behaviour. Records time per answer and
memory (Python, Ollama process tree, lowest system available memory, pagefile growth) per block of 25 answers,
to confirm that unloading stops the prompt-cache growth seen in the profile run.

Output: eval/phases/phase_12_combination/artifacts/combinations/memory_check/summary.json
Usage:  backend/venv/Scripts/python.exe eval/phases/phase_12_combination/scripts/check_generation_memory.py [--n 100]
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_combinations as rc  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--llm", default="LLAMA3B")
    a = ap.parse_args()
    from eval_common import reval_pipeline as rp
    rp.setup_django()
    from django.conf import settings
    from langchain_core.documents import Document
    from apps.documents.services.rag_service import build_answer_prompt
    from profile_generation_resources import unload_all

    prof = rc.OUT / "profile"
    ctxs = [r for r in rc.read_jsonl(prof / "contexts.jsonl") if r["docs"]]
    qids = {c["question_id"] for c in ctxs}
    ds = json.load(open(rc.DATASET, encoding="utf-8"))
    papers = {ds["questions"][q]["paper_id"] for q in qids}
    items = {it["question_id"]: it for it in rc.load_items(papers_subset=papers)}
    llm = rc.LLMS[a.llm]
    timeout_s = float(getattr(settings, "OLLAMA_TIMEOUT", 60))
    out = rc.OUT / "memory_check"
    out.mkdir(parents=True, exist_ok=True)

    unload_all()
    blocks, times, failures = [], [], 0
    sampler = rc.SystemSampler()
    for k, c in enumerate(ctxs[: a.n], 1):
        it = items[c["question_id"]]
        docs = [Document(page_content=d["text"], metadata={"page": d["page"], "section": d["section"]}) for d in c["docs"]]
        prompt = build_answer_prompt(it["question"], it["paper_title"], docs, rc.REFUSAL)
        g = rc.generate(llm, prompt, timeout_s)
        times.append(g["wall_s"])
        failures += bool(g["error"])
        if k % rc.UNLOAD_EVERY == 0:
            res = sampler.stop()
            block = times[-rc.UNLOAD_EVERY:]
            blocks.append({"answers": k, "median_s": round(statistics.median(block), 1),
                           "max_s": round(max(block), 1), **res})
            print(json.dumps(blocks[-1]), flush=True)
            unload_all()
            sampler = rc.SystemSampler()
    sampler.stop()
    unload_all()
    summary = {"llm": llm, "answers": len(times), "unload_every": rc.UNLOAD_EVERY, "failures": failures,
               "median_s": round(statistics.median(times), 1), "mean_s": round(statistics.mean(times), 1),
               "blocks": blocks}
    (out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "blocks"}, indent=1))


if __name__ == "__main__":
    main()
