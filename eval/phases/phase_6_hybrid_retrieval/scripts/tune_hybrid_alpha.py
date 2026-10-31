#!/usr/bin/env python3
"""
Tune the hybrid fusion weight alpha (score = alpha * minmax(dense) + (1 - alpha) * minmax(BM25, regex tokens)).

Data: the 150-paper QASPER Train subset (cohort_C-RET-150, 249 questions); only Train papers are used, so the
Dev/Test papers of the combination set stay untouched by this choice.
Pipelines: pymupdf_layout x {hierarchical, fixed_size} x {e5-small-v2, modernbert-embed-base}, production context
(1,600 tokens, <= 5 units). Embeddings come from the existing cache (no model is loaded if the cache is complete).
alpha = 1.0 and 0.0 are included as checks: they should match dense and BM25 rankings.
Output: eval/phases/phase_6_hybrid_retrieval/artifacts/hybrid_alpha_sweep/{per_query.jsonl, summary.json}

Usage:  backend/venv/Scripts/python.exe eval/phases/phase_6_hybrid_retrieval/scripts/tune_hybrid_alpha.py [--limit N]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
OUT = ROOT / "eval" / "phases" / "phase_6_hybrid_retrieval" / "artifacts" / "hybrid_alpha_sweep"
ALPHAS = [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
CHUNKERS = ["hierarchical", "fixed_size"]
EMBEDDERS = {"e5": "intfloat/e5-small-v2", "modernbert": "nomic-ai/modernbert-embed-base"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    rp.setup_django()
    import numpy as np
    from apps.documents.services.chunking_utils import extract_sections_from_pdf

    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    papers = sorted(groups)[: a.limit] if a.limit else sorted(groups)
    rows, loaded_models = [], set()
    for n, pid in enumerate(papers, 1):
        items = groups[pid]
        sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, items[0]["pdf_version"])))
        recs = [{"paper_id": pid, "question_id": it["question_id"]} for it in items]
        for ch in CHUNKERS:
            units = rp.build_units(sections, ch, pid) if sections else []
            if not units:
                continue
            texts = [u["text"] for u in units]
            cand = rp.candidate_units_for_relevance(units, ch)
            for short, model in EMBEDDERS.items():
                if model in rp._MODELS:
                    loaded_models.add(model)
                um = rp.cached_embed(model, texts, False, f"cret_{pid}_{ch}")
                qv = rp.cached_embed(model, [it["question"] for it in items], True, f"cret_{pid}")
                for r, it, q in zip(recs, items, qv):
                    dense = um @ q
                    sparse = rp.bm25_scores(texts, it["question"], "regex")
                    for alpha in ALPHAS:
                        ranked = rp.convex(dense, sparse, alpha=alpha)
                        m = rp.question_metrics(rp.assemble(ranked, units, ch), cand, it["retrieval_evidence"])
                        r[f"{ch}|{short}|{alpha}"] = {"ndcg10": round(m["ndcg10"], 5), "cec_0.5": m["cec_0.5"]}
                    for mode in ("dense", "bm25_fix"):  # reference rankings for the endpoint check
                        m = rp.question_metrics(rp.assemble(rp.rank(mode, dense, texts, it["question"]), units, ch),
                                                cand, it["retrieval_evidence"])
                        r[f"{ch}|{short}|{mode}"] = {"ndcg10": round(m["ndcg10"], 5), "cec_0.5": m["cec_0.5"]}
        rows += recs
        if n % 25 == 0:
            print(f"{n}/{len(papers)} papers", flush=True)
    loaded_models |= set(rp._MODELS)

    keys = sorted({k for r in rows for k in r if "|" in k})
    means = {k: {met: round(sum(r[k][met] for r in rows if k in r) / max(1, sum(1 for r in rows if k in r)), 4)
                 for met in ("ndcg10", "cec_0.5")} for k in keys}
    curve = {met: {str(al): round(sum(means[f"{c}|{e}|{al}"][met] for c in CHUNKERS for e in EMBEDDERS) / 4, 4)
                   for al in ALPHAS} for met in ("ndcg10", "cec_0.5")}
    endpoint_check = {f"{c}|{e}": {"alpha1_vs_dense_ndcg10": [means[f"{c}|{e}|1.0"]["ndcg10"], means[f"{c}|{e}|dense"]["ndcg10"]],
                                   "alpha0_vs_bm25_ndcg10": [means[f"{c}|{e}|0.0"]["ndcg10"], means[f"{c}|{e}|bm25_fix"]["ndcg10"]]}
                      for c in CHUNKERS for e in EMBEDDERS}
    summary = {"experiment": "hybrid alpha sweep", "data": "QASPER Train 150-paper subset (cohort_C-RET-150)",
               "papers": len(papers), "questions": len(rows), "alphas": ALPHAS,
               "means_by_pipeline": means, "mean_over_4_pipelines": curve, "endpoint_check": endpoint_check,
               "models_loaded_during_run": sorted(loaded_models)}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "per_query.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps({"mean_over_4_pipelines": curve, "endpoint_check": endpoint_check,
                      "models_loaded": sorted(loaded_models)}, indent=1))


if __name__ == "__main__":
    main()
