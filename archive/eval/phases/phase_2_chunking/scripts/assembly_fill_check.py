#!/usr/bin/env python3
"""
Fill-budget assembly, step 1: descriptive retrieval check (registered:
protocol assembly_fill_amendment.json (archived)). Not a decision; stage 2 decides on answers.

Cohort the QASPER component set (selection). pymupdf_layout sections -> hierarchical 200/40 -> e5-small-v2 dense ranking (vectors
from the chunking experiment cache) -> two assemblies on the same ranking:
  stop : production assembly (reval_pipeline.assemble)
  fill : skip a parent that does not fit and continue (eval_common.assembly_fill.assemble_fill)
Measures context tokens, units, early-stop rate, CEC@0.3/0.5/0.7, budgeted nDCG@10, gate score;
fill - stop paired paper-cluster bootstrap B=10,000 seed 42 (descriptive).

Usage: python assembly_fill_check.py [--limit N]
Output: eval/phases/phase_2_chunking/artifacts/assembly_fill_check/
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
import numpy as np  # noqa: E402
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402
from eval_common.assembly_fill import assemble_fill  # noqa: E402

E5 = "intfloat/e5-small-v2"
ARMS = ["stop", "fill"]
METRICS = ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7", "context_tokens", "n_units", "early_stop", "gate_score"]
OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "assembly_fill_check"


def metrics(ctx, cand, evidence, dense, idx):
    m = rp.question_metrics(ctx, cand, evidence)
    m["early_stop"] = int(len(ctx) < 5 and sum(c["tokens"] for c in ctx) < 1400)
    m["gate_score"] = round(max((float(dense[i]) for i in idx), default=0.0), 5)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    groups = rr.group_items(rr.load_cohort("C-RET"))
    papers = sorted(groups)[: args.limit] if args.limit else sorted(groups)
    rows, failures = [], []
    t0 = time.time()
    with rr.MemorySampler() as mem:
        for n, pid in enumerate(papers, 1):
            items = groups[pid]
            try:
                sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, items[0]["pdf_version"])))
                units = rp.build_units(sections, "hierarchical", pid)
                assert units, "no units"
            except Exception as e:
                failures.append({"paper_id": pid, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            texts = [u["text"] for u in units]
            um = rp.cached_embed(E5, texts, False, f"cret_{pid}_hierarchical")
            qv = rp.cached_embed(E5, [it["question"] for it in items], True, f"cret_{pid}")
            cand = rp.candidate_units_for_relevance(units, "hierarchical")
            for it, q in zip(items, qv):
                dense = um @ q
                ranked = rp.rank("dense", dense, texts, it["question"])
                stop = rp.assemble(ranked, units, "hierarchical")
                # production gate: matched child of each parent in the context (stop: first parents in rank order)
                seen, stop_idx = set(), []
                for i in ranked:
                    p = units[i].get("parent_id")
                    if p and p not in seen:
                        seen.add(p)
                        stop_idx.append(int(i))
                    if len(stop_idx) >= len(stop):
                        break
                fill = assemble_fill(ranked, units, "hierarchical")
                ev = it["retrieval_evidence"]
                rows.append({"paper_id": pid, "question_id": it["question_id"],
                             "stop": metrics(stop, cand, ev, dense, stop_idx),
                             "fill": metrics(fill, cand, ev, dense, [c["idx"] for c in fill])})
            if n % 50 == 0:
                print(f"[{n}/{len(papers)}] {time.time() - t0:.0f}s", flush=True)

    summary = {
        "experiment": "ASSEMBLY-FILL-CHECK", "cohort": "C-RET", "role": "SELECTION, descriptive (stage 2 decides)",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
        "means": rr.arm_means(rows, ARMS, METRICS),
        "fill_minus_stop": {m: rr.compare(rows, "stop", "fill", m) for m in ["cec_0.5", "ndcg10", "context_tokens", "n_units"]},
        "questions_with_identical_context": int(sum(r["stop"]["context_tokens"] == r["fill"]["context_tokens"]
                                                    and r["stop"]["n_units"] == r["fill"]["n_units"] for r in rows)),
        "memory": mem.report(), "elapsed_s": round(time.time() - t0, 1), "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    rr.write_outputs(OUT if not args.limit else OUT / f"smoke_{args.limit}", rows, summary)
    print({k: summary[k] for k in ("papers", "questions", "questions_with_identical_context")})


if __name__ == "__main__":
    main()
