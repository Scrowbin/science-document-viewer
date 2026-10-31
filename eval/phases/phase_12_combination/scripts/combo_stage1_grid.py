#!/usr/bin/env python3
"""
COMBO stage 1: full retrieval grid on the 150-paper QASPER subset (registered: protocol combo_test.json (archived)).

Grid: extractor {pymupdf_layout, pypdf} x chunker {hierarchical, section_overlap, fixed_size}
      x embedder {MiniLM, e5-small-v2, arctic-embed-s, bge-small, modernbert-embed} x retrieval {dense, rrf_fix,
      convex_fix, rrf_prod(= production rrf_legacy)} = 120 combinations. No LLM.
Pipeline per combination (same harness as the component experiments): sections -> chunker -> embedder (model prefixes) -> ranking ->
production context assembly (1,600 est. tokens, <= 5 units, +-200-word windowing for parents > 800 tokens).
  pymupdf_layout sections: extract_sections_from_pdf (production, as in the component experiments)
  pypdf sections: the extraction experiment extraction cache (headings or page fallback, as extraction experiment downstream)
Per question and combination: budgeted nDCG@10, CEC@0.3/0.5/0.7, context tokens, units, and the gate score
(production rule: max dense cosine of the matched children whose units entered the context; children outside the
dense top-50 count as 0 in rrf modes, as in DocumentRAG.hybrid_search).
Efficiency per (extractor, chunker, embedder): indexing chunks/s (uncached batches only), units; per embedder:
query latency P50/P95 (110 queries, 10 warm-up), peak working set (one subprocess per embedder).

Usage: python combo_stage1_grid.py [--limit N]
Output: eval/phases/phase_12_combination/artifacts/stage1/[smoke_N/]
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_1_extraction" / "scripts"))
OUT = ROOT / "eval" / "phases" / "phase_12_combination" / "artifacts" / "stage1"
EXTRACTORS = ["pymupdf_layout", "pypdf"]
CHUNKERS = ["hierarchical", "section_overlap", "fixed_size"]
EMBEDDERS = {"e5": "intfloat/e5-small-v2", "minilm": "sentence-transformers/all-MiniLM-L6-v2",
             "arctic": "Snowflake/snowflake-arctic-embed-s", "bge": "BAAI/bge-small-en-v1.5",
             "modernbert": "nomic-ai/modernbert-embed-base"}
MODES = ["dense", "rrf_fix", "convex_fix", "rrf_prod"]
PRODUCTION = "pymupdf_layout|hierarchical|e5|dense"


def arm(ex, ch, em, mode):
    return f"{ex}|{ch}|{em}|{mode}"


def context_indices(ranked, units, strategy, n_ctx):
    """Indices of the units that entered the context, in assembly order (mirrors reval_pipeline.assemble)."""
    out, seen = [], set()
    for idx in ranked:
        if len(out) >= n_ctx:
            break
        if strategy == "hierarchical":
            pid = units[idx].get("parent_id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
        out.append(idx)
    return out


def worker(short, limit, out_dir):
    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    rp.setup_django()
    import numpy as np
    import evaluate_extraction as rq1  # frozen script; only its cache helpers are used
    from apps.documents.services.chunking_utils import extract_sections_from_pdf

    model = EMBEDDERS[short]
    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    papers = sorted(groups)[:limit] if limit else sorted(groups)
    cache = rq1.load_cache("reservoir")
    rows, failures, eff = [], [], {}
    with rr.MemorySampler() as mem:
        rp.get_model(model)
        for pid in papers:
            items = groups[pid]
            version = items[0]["pdf_version"]
            qv = rp.cached_embed(model, [it["question"] for it in items], True, f"cret_{pid}")
            recs = [{"paper_id": pid, "question_id": it["question_id"]} for it in items]
            for ex in EXTRACTORS:
                try:
                    if ex == "pymupdf_layout":
                        sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, version)))
                    else:
                        c = cache.get((pid, version, ex))
                        assert c and c.get("ok"), "no cached extraction"
                        sections = rq1.sections_of(c)
                except Exception as e:
                    failures.append({"paper_id": pid, "extractor": ex, "error": f"{type(e).__name__}: {e}"[:200]})
                    sections = []
                for ch in CHUNKERS:
                    units = rp.build_units(sections, ch, pid) if sections else []
                    key = f"{ex}|{ch}"
                    e = eff.setdefault(key, {"units": 0, "embed_s": 0.0, "embedded_uncached": 0})
                    if not units:
                        failures.append({"paper_id": pid, "extractor": ex, "chunker": ch, "error": "no units"})
                        for r in recs:
                            for mode in MODES:
                                r[arm(ex, ch, short, mode)] = {"ndcg10": 0.0, "cec_0.5": 0, "cec_0.3": 0, "cec_0.7": 0,
                                                               "context_tokens": 0, "n_units": 0, "gate_score": 0.0}
                        continue
                    texts = [u["text"] for u in units]
                    tag = (f"cret_{pid}_{ch}" if ex == "pymupdf_layout"
                           else (f"rq1v2_{pid}_{ex}" if ch == "hierarchical" else f"grid_{pid}_{ex}_{ch}"))
                    t = time.perf_counter()
                    path_before = len(list((rp.EMB_CACHE / model.replace("/", "__") / "p").glob(f"{tag}_*.npy"))) \
                        if (rp.EMB_CACHE / model.replace("/", "__") / "p").exists() else 0
                    um = rp.cached_embed(model, texts, False, tag)
                    dt = time.perf_counter() - t
                    path_after = len(list((rp.EMB_CACHE / model.replace("/", "__") / "p").glob(f"{tag}_*.npy")))
                    e["units"] += len(texts)
                    if path_after > path_before:  # newly embedded (not a cache hit): counts for throughput
                        e["embed_s"] += dt
                        e["embedded_uncached"] += len(texts)
                    cand = rp.candidate_units_for_relevance(units, ch)
                    for r, it, q in zip(recs, items, qv):
                        dense = um @ q
                        dense_top50 = set(int(i) for i in np.argsort(dense)[::-1][:rp.RETRIEVE_K])
                        for mode in MODES:
                            ranked = rp.rank(mode, dense, texts, it["question"])
                            ctx = rp.assemble(ranked, units, ch)
                            m = rp.question_metrics(ctx, cand, it["retrieval_evidence"])
                            idx = context_indices(ranked, units, ch, len(ctx))
                            if mode in ("rrf_prod", "rrf_fix"):
                                gs = max((float(dense[i]) if i in dense_top50 else 0.0 for i in idx), default=0.0)
                            else:
                                gs = max((float(dense[i]) for i in idx), default=0.0)
                            m["gate_score"] = round(gs, 5)
                            r[arm(ex, ch, short, mode)] = m
            rows += recs
            print(f"{short} {pid} done", flush=True)
        qs = [it["question"] for p in sorted(groups) for it in groups[p]][:110]
        lat = []
        for i, q in enumerate(qs):
            t = time.perf_counter()
            rp.embed(model, [q], is_query=True, batch_size=1)
            if i >= 10:
                lat.append((time.perf_counter() - t) * 1000)
    res = {"embedder": short, "model": model, "rows": rows, "failures": failures,
           "efficiency": {k: {**v, "chunks_per_s": round(v["embedded_uncached"] / v["embed_s"], 2) if v["embed_s"] else None}
                          for k, v in eff.items()},
           "query_latency_ms": {"p50": round(float(np.percentile(lat, 50)), 2), "p95": round(float(np.percentile(lat, 95)), 2), "n": len(lat)},
           "memory": mem.report()}
    (out_dir / f"embedder_{short}.json").write_text(json.dumps(res), encoding="utf-8")


def analyse(out_dir):
    import numpy as np
    from eval_common import reval_runner as rr
    res = {s: json.load(open(out_dir / f"embedder_{s}.json", encoding="utf-8")) for s in EMBEDDERS}
    key = lambda r: (r["paper_id"], r["question_id"])
    common = sorted(set.intersection(*[{key(r) for r in v["rows"]} for v in res.values()]))
    rows = []
    for k in common:
        rec = {"paper_id": k[0], "question_id": k[1]}
        for v in res.values():
            r = next(x for x in v["rows"] if key(x) == k)
            rec.update({a: m for a, m in r.items() if "|" in a})
        rows.append(rec)
    arms = [arm(ex, ch, em, mode) for ex in EXTRACTORS for ch in CHUNKERS for em in EMBEDDERS for mode in MODES]
    metrics = ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7", "context_tokens", "n_units", "gate_score"]
    means = rr.arm_means(rows, arms, metrics)

    # Comparisons with production. nDCG@10 only within the hierarchical chunker (units differ across chunkers);
    # CEC@0.5 for every combination. Holm over all comparisons in each family.
    hier = [a for a in arms if a.split("|")[1] == "hierarchical" and a != PRODUCTION]
    fam_ndcg = rr.family(rows, [(a, PRODUCTION) for a in hier], "ndcg10")
    fam_cec = rr.family(rows, [(a, PRODUCTION) for a in arms if a != PRODUCTION], "cec_0.5")

    # Shortlist (registered rule): top 2 per chunker by nDCG@10 (ties: CEC@0.5), plus production if absent
    shortlist = []
    for ch in CHUNKERS:
        cand = sorted([a for a in arms if a.split("|")[1] == ch],
                      key=lambda a: (means[a]["ndcg10"], means[a]["cec_0.5"]), reverse=True)
        shortlist += cand[:2]
    if PRODUCTION not in shortlist:
        shortlist.append(PRODUCTION)

    # Gate calibration (design rule 6): e5 keeps 0.80; other embedders get the threshold that gives each
    # combination the same gate-refusal rate as production (e5 hierarchical dense at 0.80) on these questions
    prod_scores = np.array([r[PRODUCTION]["gate_score"] for r in rows])
    prod_rate = float(np.mean(prod_scores < 0.80))
    gates = {}
    for a in shortlist:
        if a.split("|")[2] == "e5":
            gates[a] = 0.80
        else:
            s = np.array([r[a]["gate_score"] for r in rows])
            gates[a] = round(float(np.quantile(s, prod_rate)), 5) if prod_rate > 0 else 0.0

    # Main effects and two-way interactions (descriptive): mean over all other factors
    def level_means(pos, metric):
        out = {}
        for lv in sorted({a.split("|")[pos] for a in arms}):
            out[lv] = round(float(np.mean([means[a][metric] for a in arms if a.split("|")[pos] == lv])), 4)
        return out

    def two_way(p1, p2, metric):
        out = {}
        for a in arms:
            k = f"{a.split('|')[p1]} x {a.split('|')[p2]}"
            out.setdefault(k, []).append(means[a][metric])
        return {k: round(float(np.mean(v)), 4) for k, v in sorted(out.items())}

    names = ["extractor", "chunker", "embedder", "retrieval"]
    effects = {m: {names[i]: level_means(i, m) for i in range(4)} for m in ["ndcg10", "cec_0.5"]}
    inter = {"cec_0.5": {f"{names[i]} x {names[j]}": two_way(i, j, "cec_0.5") for i in range(4) for j in range(i + 1, 4)},
             "ndcg10_hierarchical_only": None}
    summary = {
        "experiment": "COMBO-STAGE1", "cohort": "C-RET-150", "papers": len({r["paper_id"] for r in rows}),
        "questions": len(rows), "combinations": len(arms), "production": PRODUCTION,
        "failures": {s: v["failures"] for s, v in res.items()},
        "means": means, "main_effects": effects, "two_way_cec_0.5": inter["cec_0.5"],
        "vs_production_ndcg10_hierarchical_only": fam_ndcg, "vs_production_cec_0.5": fam_cec,
        "shortlist": shortlist, "gate_thresholds": gates, "production_gate_refusal_rate": round(prod_rate, 4),
        "efficiency": {s: {"index": v["efficiency"], "query_latency_ms": v["query_latency_ms"], "memory": v["memory"]}
                       for s, v in res.items()},
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper"},
    }
    rr.write_outputs(out_dir, rows, summary)
    print(json.dumps({"questions": len(rows), "shortlist": shortlist, "gates": gates}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--worker")
    a = ap.parse_args()
    out = OUT / (f"smoke_{a.limit}" if a.limit else "")
    out.mkdir(parents=True, exist_ok=True)
    if a.worker:
        worker(a.worker, a.limit, out)
        return
    for s in EMBEDDERS:
        if not (out / f"embedder_{s}.json").exists():
            print(f"running {s}", flush=True)
            cmd = [sys.executable, __file__, "--worker", s] + (["--limit", str(a.limit)] if a.limit else [])
            subprocess.run(cmd, check=True)
    analyse(out)


if __name__ == "__main__":
    main()
