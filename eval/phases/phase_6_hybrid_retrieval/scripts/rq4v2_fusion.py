#!/usr/bin/env python3
"""
RQ4-v2: retrieval/fusion modes with app-identical implementations (pre-registered:
reports/revalidation/protocol/rq1_rq4.json "RQ4-v2").

Cohort C-RET (selection; primary), PEERQA-PDF or PEERQA-TEXT (descriptive; TEXT uses the shipped text). pymupdf_layout -> hierarchical -> e5-small-v2
vectors (shared cache with RQ2-v2) -> 7 ranking arms -> production context assembly.
Primary: budgeted nDCG@10; family vs dense: rrf_prod, rrf_fix, convex_fix (Holm m=3), SESOI 0.02.
Decision: default = dense unless a *_fix hybrid beats dense by >= 0.02 with CI lower bound > 0;
tie order bm25_fix < rrf_fix < convex_fix; *_prod arms never adopted.

Usage: python rq4v2_fusion.py --cohort C-RET|PEERQA-PDF|PEERQA-TEXT [--limit N]
Output: eval/phases/phase_6_hybrid_retrieval/artifacts/rq4v2/<cohort>/
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
ARMS = ["dense", "bm25_prod", "rrf_prod", "bm25_fix", "rrf_fix", "convex_prod", "convex_fix"]
TIE_ORDER = ["bm25_fix", "rrf_fix", "convex_fix"]
METRICS = ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7", "context_tokens"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", default="C-RET", choices=["C-RET", "PEERQA-PDF", "PEERQA-TEXT"])
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    cohort = rr.load_cohort(args.cohort)
    groups = rr.group_items(cohort)
    papers = sorted(groups)[: args.limit] if args.limit else sorted(groups)
    rows, failures, lat = [], [], {a: [] for a in ARMS}
    t0 = time.time()
    tag = {"C-RET": "cret", "PEERQA-PDF": "peerqa", "PEERQA-TEXT": "peerqatext"}[args.cohort]
    with rr.MemorySampler() as mem:
        for n, pid in enumerate(papers, 1):
            items = groups[pid]
            try:
                if args.cohort == "PEERQA-TEXT":
                    sections = rr.peerqa_text_sections(pid)
                else:
                    sections = extract_sections_from_pdf(str(rr.pdf_path(args.cohort, pid, items[0].get("pdf_version", "latest"))))
                units = rp.build_units(sections, "hierarchical", pid)
                assert units, "no units"
            except Exception as e:
                failures.append({"paper_id": pid, "error": f"{type(e).__name__}: {e}"[:200]})
                continue
            texts = [u["text"] for u in units]
            um = rp.cached_embed(E5, texts, False, f"{tag}_{pid}_hierarchical")
            qv = rp.cached_embed(E5, [it["question"] for it in items], True, f"{tag}_{pid}")
            cand = rp.candidate_units_for_relevance(units, "hierarchical")
            for tok in ("whitespace", "regex"):  # build BM25 indexes outside the timed per-query step
                rp.bm25_scores(texts, "", tok)
            for it, q in zip(items, qv):
                rec = {"paper_id": pid, "question_id": it["question_id"]}
                dense = um @ q
                for arm in ARMS:
                    tq = time.perf_counter()
                    ranked = rp.rank(arm, dense, texts, it["question"])
                    lat[arm].append((time.perf_counter() - tq) * 1000)
                    rec[arm] = rp.question_metrics(rp.assemble(ranked, units, "hierarchical"), cand, it["retrieval_evidence"])
                rows.append(rec)
            if n % 25 == 0:
                print(f"[{n}/{len(papers)}] {time.time() - t0:.0f}s", flush=True)

    pairs = [("rrf_prod", "dense"), ("rrf_fix", "dense"), ("convex_fix", "dense")]
    primary = rr.family(rows, pairs, "ndcg10")
    passing = {r["comparison"].split(" - ")[0] for r in primary if r["diff"] >= 0.02 and r["ci95"][0] > 0}
    bm25_fix = rr.compare(rows, "dense", "bm25_fix", "ndcg10")
    if bm25_fix["diff"] >= 0.02 and bm25_fix["ci95"][0] > 0:
        passing.add("bm25_fix")
    winner = next((a for a in TIE_ORDER if a in passing), "dense")
    summary = {
        "experiment": "RQ4-v2", "cohort": args.cohort,
        "role": "SELECTION" if args.cohort == "C-RET" else "DESCRIPTIVE",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
        "means": rr.arm_means(rows, ARMS, METRICS),
        "primary_family_ndcg10": primary,
        "bm25_fix_vs_dense_ndcg10_descriptive": bm25_fix,
        "secondary_cec_0.5": rr.family(rows, pairs, "cec_0.5"),
        "descriptive": [rr.compare(rows, "rrf_prod", "rrf_fix", "ndcg10"), rr.compare(rows, "dense", "convex_prod", "ndcg10")],
        "decision_rule": "dense unless a *_fix hybrid >= +0.02 nDCG@10 with CI lower bound > 0; tie order bm25_fix < rrf_fix < convex_fix",
        "decision": winner if args.cohort == "C-RET" else "n/a (descriptive cohort)",
        "rank_latency_ms": {a: {"p50": round(float(np.percentile(v, 50)), 3), "p95": round(float(np.percentile(v, 95)), 3)} for a, v in lat.items() if v},
        "memory": mem.report(), "elapsed_s": round(time.time() - t0, 1), "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    out = ROOT / "eval" / "phases" / "phase_6_hybrid_retrieval" / "artifacts" / "rq4v2" / args.cohort
    rr.write_outputs(out if not args.limit else out / f"smoke_{args.limit}", rows, summary)
    print({k: summary[k] for k in ("papers", "questions", "decision")})


if __name__ == "__main__":
    main()
