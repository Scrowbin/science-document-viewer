#!/usr/bin/env python3
"""
embedding experiment: embedding shortlist on fresh papers (pre-registered: protocol rq1_rq4.json (archived) "embedding experiment").

Cohort the 150-paper QASPER subset (selection). pymupdf_layout -> hierarchical children -> each model (own subprocess, so
memory and latency are attributable) -> dense ranking -> production context assembly.
Primary: budgeted nDCG@10; family: each challenger vs e5-small-v2 (Holm m=4), SESOI 0.04.
Decision: switch only if a model with P50 query latency <= 1.5x e5 beats e5 by >= 0.04 with CI lower bound > 0.
Efficiency per model: indexing chunks/s (batch 32, uncached, timed), query latency P50/P95 (batch 1,
100 queries after 10 warm-up), peak working set of the model subprocess.

Usage: python evaluate_embedding.py [--limit N]
Output: eval/phases/phase_3_embedding/artifacts/embedding/
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
OUT = ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts" / "embedding"
MODELS = ["intfloat/e5-small-v2", "sentence-transformers/all-MiniLM-L6-v2", "Snowflake/snowflake-arctic-embed-s",
          "BAAI/bge-small-en-v1.5", "nomic-ai/modernbert-embed-base"]
INCUMBENT = "intfloat/e5-small-v2"


def worker(model: str, limit, out_dir: Path):
    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    rp.setup_django()
    import numpy as np
    from apps.documents.services.chunking_utils import extract_sections_from_pdf
    from apps.documents.services.rag_service import get_model_prefix

    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    papers = sorted(groups)[:limit] if limit else sorted(groups)
    rows, failures, n_units, embed_s = [], [], 0, 0.0
    with rr.MemorySampler() as mem:
        rp.get_model(model)
        for pid in papers:
            items = groups[pid]
            try:
                sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, items[0]["pdf_version"])))
                units = rp.build_units(sections, "hierarchical", pid)
                assert units, "no units"
            except Exception as e:
                failures.append({"paper_id": pid, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            texts = [u["text"] for u in units]
            t = time.perf_counter()
            um = rp.embed(model, texts, is_query=False, batch_size=32)  # uncached: indexing throughput
            embed_s += time.perf_counter() - t
            n_units += len(texts)
            qv = rp.embed(model, [it["question"] for it in items], is_query=True)
            cand = rp.candidate_units_for_relevance(units, "hierarchical")
            for it, q in zip(items, qv):
                ctx = rp.assemble(rp.rank("dense", um @ q, texts, it["question"]), units, "hierarchical")
                rows.append({"paper_id": pid, "question_id": it["question_id"],
                             "m": rp.question_metrics(ctx, cand, it["retrieval_evidence"])})
        qs = [it["question"] for p in sorted(groups) for it in groups[p]][:110]  # 10 warm-up + 100 timed, all of C-RET-150
        lat = []
        for i, q in enumerate(qs):
            t = time.perf_counter()
            rp.embed(model, [q], is_query=True, batch_size=1)
            if i >= 10:
                lat.append((time.perf_counter() - t) * 1000)
    res = {"model": model, "prefix_query": get_model_prefix(model, True), "prefix_passage": get_model_prefix(model, False),
           "rows": rows, "failures": failures, "units": n_units,
           "indexing_chunks_per_s": round(n_units / embed_s, 2) if embed_s else None,
           "query_latency_ms": {"p50": round(float(np.percentile(lat, 50)), 2), "p95": round(float(np.percentile(lat, 95)), 2), "n": len(lat)},
           "memory": mem.report()}
    (out_dir / f"model_{model.replace('/', '__')}.json").write_text(json.dumps(res), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--worker")
    args = ap.parse_args()
    out = OUT if not args.limit else OUT / f"smoke_{args.limit}"
    out.mkdir(parents=True, exist_ok=True)
    if args.worker:
        worker(args.worker, args.limit, out)
        return
    for m in MODELS:
        if not (out / f"model_{m.replace('/', '__')}.json").exists():
            print(f"running {m}", flush=True)
            cmd = [sys.executable, __file__, "--worker", m] + (["--limit", str(args.limit)] if args.limit else [])
            subprocess.run(cmd, check=True)

    from eval_common import reval_runner as rr
    res = {m: json.load(open(out / f"model_{m.replace('/', '__')}.json", encoding="utf-8")) for m in MODELS}
    key = lambda r: (r["paper_id"], r["question_id"])
    common = set.intersection(*[{key(r) for r in v["rows"]} for v in res.values()])
    rows = []
    for k in sorted(common):
        rec = {"paper_id": k[0], "question_id": k[1]}
        for m, v in res.items():
            rec[m] = next(r["m"] for r in v["rows"] if key(r) == k)
        rows.append(rec)
    pairs = [(m, INCUMBENT) for m in MODELS if m != INCUMBENT]
    primary = rr.family(rows, pairs, "ndcg10")
    lat_e5 = res[INCUMBENT]["query_latency_ms"]["p50"]
    eligible = [r for r in primary if r["diff"] >= 0.04 and r["ci95"][0] > 0
                and res[r["comparison"].split(" - ")[0]]["query_latency_ms"]["p50"] <= 1.5 * lat_e5]
    summary = {
        "experiment": "RQ3-v2", "cohort": "C-RET-150", "role": "SELECTION",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows),
        "means": rr.arm_means(rows, MODELS, ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7"]),
        "primary_family_ndcg10": primary,
        "secondary_cec_0.5": rr.family(rows, pairs, "cec_0.5"),
        "efficiency": {m: {k: v[k] for k in ("indexing_chunks_per_s", "query_latency_ms", "memory", "units", "prefix_query", "prefix_passage")} for m, v in res.items()},
        "failures": {m: v["failures"] for m, v in res.items()},
        "decision_rule": "switch only if P50 latency <= 1.5x e5 and diff >= 0.04 with CI lower bound > 0",
        "decision": (max(eligible, key=lambda r: r["diff"])["comparison"].split(" - ")[0] if eligible else "keep intfloat/e5-small-v2"),
        "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    rr.write_outputs(out, rows, summary)
    print({k: summary[k] for k in ("papers", "questions", "decision")})


if __name__ == "__main__":
    main()
