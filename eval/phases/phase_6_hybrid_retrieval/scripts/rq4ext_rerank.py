#!/usr/bin/env python3
"""
EXT-RQ4-RERANK: second-stage cross-encoder reranking (extension; registered in
reports/revalidation/protocol/ext_rq4_rerank.json before running). Separate from the frozen RQ4-v2 arms.

Cohort C-RET (selection). Same pipeline as RQ4-v2: pymupdf_layout -> hierarchical (200/40) -> e5-small-v2
vectors (shared cache) -> ranking -> production context assembly (1,600 tokens, <= 5 parents, windowing).
Arms:
  dense             : the RQ4-v2 baseline arm (current production dense branch)
  rerank_minilm     : dense top-30 children re-scored by cross-encoder/ms-marco-MiniLM-L6-v2 (22.7M, Apache-2.0)
  rerank_bge        : dense top-30 children re-scored by BAAI/bge-reranker-base (278M, MIT)
Children beyond the top 30 keep their dense order after the reranked block. Cross-encoder input: (question,
child text exactly as embedded), max_length 512.
Primary: budgeted nDCG@10, each reranker vs dense, paper-cluster bootstrap B=10,000 seed 42, Holm m=2.
Decision: adopt only if diff >= +0.02, CI lower bound > 0, Holm p < 0.05 AND P95 added rerank latency
<= 1,000 ms per query on this CPU; if both pass, the one with lower P95 latency.
Also: CEC at tau 0.3/0.5/0.7, P50/P95 rerank latency, peak working set.

Usage: python rq4ext_rerank.py [--limit N]
Output: eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_ext_rerank/
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
TOP_K = 30
RERANKERS = {"rerank_minilm": "cross-encoder/ms-marco-MiniLM-L6-v2", "rerank_bge": "BAAI/bge-reranker-base"}
REVISIONS = {"cross-encoder/ms-marco-MiniLM-L6-v2": "233902d25c", "BAAI/bge-reranker-base": "2cfc18c941"}
# Local copies (snapshot_download local_dir): the Windows HF cache cannot create symlinks without Developer Mode.
MODEL_DIR = ROOT / "eval" / "data" / "revalidation_cache" / "models"
ARMS = ["dense"] + list(RERANKERS)
METRICS = ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7", "context_tokens"]
LATENCY_LIMIT_MS = 1000.0


def rerank(model, question, dense, texts):
    order = [int(i) for i in np.argsort(dense)[::-1]]
    head, tail = order[:TOP_K], order[TOP_K:]
    t = time.perf_counter()
    scores = model.predict([(question, texts[i]) for i in head], batch_size=32, show_progress_bar=False)
    ms = (time.perf_counter() - t) * 1000
    head = [i for _, i in sorted(zip(scores, head), key=lambda x: -x[0])]
    return head + tail, ms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    from sentence_transformers import CrossEncoder

    groups = rr.group_items(rr.load_cohort("C-RET"))
    papers = sorted(groups)[: args.limit] if args.limit else sorted(groups)
    rows, failures, lat = [], [], {a: [] for a in RERANKERS}
    t0 = time.time()
    with rr.MemorySampler() as mem:
        models = {a: CrossEncoder(str(MODEL_DIR / name.replace("/", "__")), device="cpu", max_length=512)
                  for a, name in RERANKERS.items()}
        for a, m in models.items():  # warm-up so the first timed query does not include lazy initialisation
            m.predict([("warm up", "warm up")] * 4, show_progress_bar=False)
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
                rec = {"paper_id": pid, "question_id": it["question_id"]}
                rec["dense"] = rp.question_metrics(rp.assemble(rp.rank("dense", dense, texts, it["question"]), units, "hierarchical"),
                                                   cand, it["retrieval_evidence"])
                for a, m in models.items():
                    ranked, ms = rerank(m, it["question"], dense, texts)
                    lat[a].append(ms)
                    rec[a] = rp.question_metrics(rp.assemble(ranked, units, "hierarchical"), cand, it["retrieval_evidence"])
                rows.append(rec)
            if n % 25 == 0:
                print(f"[{n}/{len(papers)}] {time.time() - t0:.0f}s", flush=True)

    pairs = [(a, "dense") for a in RERANKERS]
    primary = rr.family(rows, pairs, "ndcg10")
    latency = {a: {"p50": round(float(np.percentile(v, 50)), 1), "p95": round(float(np.percentile(v, 95)), 1), "n": len(v)}
               for a, v in lat.items() if v}
    for r in primary:
        arm = r["comparison"].split(" - ")[0]
        r["ci95_half_width"] = round((r["ci95"][1] - r["ci95"][0]) / 2, 4)
        r["passes_quality"] = bool(r["diff"] >= 0.02 and r["ci95"][0] > 0 and r["p_holm"] < 0.05)
        r["passes_latency"] = bool(latency.get(arm, {}).get("p95", 1e9) <= LATENCY_LIMIT_MS)
    passing = [r["comparison"].split(" - ")[0] for r in primary if r["passes_quality"] and r["passes_latency"]]
    winner = min(passing, key=lambda a: latency[a]["p95"]) if passing else "dense (no reranker adopted)"
    summary = {
        "experiment": "EXT-RQ4-RERANK", "cohort": "C-RET", "role": "SELECTION EXTENSION",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
        "rerankers": RERANKERS, "revisions": REVISIONS, "top_k": TOP_K,
        "means": rr.arm_means(rows, ARMS, METRICS),
        "primary_family_ndcg10": primary,
        "secondary_cec_0.5": rr.family(rows, pairs, "cec_0.5"),
        "rerank_latency_ms_added_per_query": latency,
        "decision_rule": "adopt if diff >= +0.02, CI lower bound > 0, Holm p < 0.05 and P95 added latency <= 1000 ms; if both, lower P95",
        "decision": winner, "memory": mem.report(), "elapsed_s": round(time.time() - t0, 1),
        "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    out = ROOT / "eval" / "phases" / "phase_6_hybrid_retrieval" / "artifacts" / "rq4_ext_rerank"
    rr.write_outputs(out if not args.limit else out / f"smoke_{args.limit}", rows, summary)
    print({k: summary[k] for k in ("papers", "questions", "decision")})


if __name__ == "__main__":
    main()
