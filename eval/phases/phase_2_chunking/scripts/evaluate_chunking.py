#!/usr/bin/env python3
"""
chunking experiment: chunking strategies under the production context budget (pre-registered:
protocol rq1_rq4.json (archived) "chunking experiment").

Cohort the QASPER component set (selection). pymupdf_layout sections -> {fixed_size, section_overlap, hierarchical} ->
e5-small-v2 dense ranking -> production context assembly (1,600 est. tokens, <= 5 units, windowing).
Primary: CEC@0.5. Family: hierarchical vs fixed_size, hierarchical vs section_overlap (Holm m=2), SESOI 0.05.
Descriptive extra: the same strategies with the production rrf_prod ranking.

Usage: python evaluate_chunking.py [--limit N]
Output: eval/phases/phase_2_chunking/artifacts/chunking/
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

E5 = "intfloat/e5-small-v2"
STRATEGIES = ["fixed_size", "section_overlap", "hierarchical"]
OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "chunking"
METRICS = ["cec_0.5", "cec_0.3", "cec_0.7", "ndcg10", "context_tokens", "n_units"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    cohort = rr.load_cohort("C-RET")
    groups = rr.group_items(cohort)
    papers = sorted(groups)[: args.limit] if args.limit else sorted(groups)
    rows, index_stats, failures, lat = [], {s: {"units": 0, "embed_s": 0.0} for s in STRATEGIES}, [], []
    t0 = time.time()
    with rr.MemorySampler() as mem:
        for n, pid in enumerate(papers, 1):
            items = groups[pid]
            try:
                sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, items[0]["pdf_version"])))
            except Exception as e:
                failures.append({"paper_id": pid, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            qv = rp.cached_embed(E5, [it["question"] for it in items], True, f"cret_{pid}")
            per_q = [{"paper_id": pid, "question_id": it["question_id"]} for it in items]
            for st in STRATEGIES:
                units = rp.build_units(sections, st, pid)
                if not units:
                    failures.append({"paper_id": pid, "strategy": st, "error": "no units"})
                    continue
                texts = [u["text"] for u in units]
                te = time.perf_counter()
                um = rp.cached_embed(E5, texts, False, f"cret_{pid}_{st}")
                index_stats[st]["embed_s"] += time.perf_counter() - te
                index_stats[st]["units"] += len(units)
                cand = rp.candidate_units_for_relevance(units, st)
                for rec, it, q in zip(per_q, items, qv):
                    for mode in ("dense", "rrf_prod"):
                        tq = time.perf_counter()
                        ctx = rp.assemble(rp.rank(mode, um @ q, texts, it["question"]), units, st)
                        if mode == "dense":
                            lat.append((time.perf_counter() - tq) * 1000)
                        rec[f"{st}|{mode}"] = rp.question_metrics(ctx, cand, it["retrieval_evidence"])
            rows += [r for r in per_q if all(f"{s}|dense" in r for s in STRATEGIES)]
            if n % 25 == 0:
                print(f"[{n}/{len(papers)}] {time.time() - t0:.0f}s", flush=True)

    arms = [f"{s}|{m}" for s in STRATEGIES for m in ("dense", "rrf_prod")]
    pairs = [("hierarchical|dense", "fixed_size|dense"), ("hierarchical|dense", "section_overlap|dense")]
    primary = rr.family(rows, pairs, "cec_0.5")
    summary = {
        "experiment": "RQ2-v2", "cohort": "C-RET", "role": "SELECTION",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
        "means": rr.arm_means(rows, arms, METRICS),
        "primary_family_cec_0.5": primary,
        "secondary_ndcg10": rr.family(rows, pairs, "ndcg10"),
        "sensitivity_cec_0.3": rr.family(rows, pairs, "cec_0.3"),
        "sensitivity_cec_0.7": rr.family(rows, pairs, "cec_0.7"),
        "decision_rule": "replace hierarchical only if a flat strategy beats it by >= 0.05 CEC@0.5 with CI lower bound > 0",
        "index": {s: {"units": v["units"], "units_per_paper": round(v["units"] / max(1, len(papers)), 1)} for s, v in index_stats.items()},
        "latency_ms_rank_and_assemble_dense": {"p50": round(float(np.percentile(lat, 50)), 3), "p95": round(float(np.percentile(lat, 95)), 3)} if lat else {},
        "memory": mem.report(), "elapsed_s": round(time.time() - t0, 1), "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    flat_win = [r for r in primary if r["diff"] <= -0.05 and r["ci95"][1] < 0]
    summary["decision"] = ("switch to " + flat_win[0]["comparison"].split(" - ")[1].split("|")[0]) if flat_win else "keep hierarchical"
    rr.write_outputs(OUT if not args.limit else OUT / f"smoke_{args.limit}", rows, summary)
    print({k: summary[k] for k in ("papers", "questions", "decision")})


if __name__ == "__main__":
    main()
