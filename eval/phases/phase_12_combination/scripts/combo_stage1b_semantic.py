#!/usr/bin/env python3
"""
COMBO stage-1 add-on: semantic chunking in the retrieval grid (registered:
reports/revalidation/protocol/combo_semantic_addon.json; amends combo_test.json).

Grid: pymupdf_layout x {semantic_v1, semantic_v2} x 5 embedders x 4 retrieval modes = 40 cells on C-RET-150,
same questions, harness, metrics and gate score as combo_stage1_grid.py (imported, not copied).
Split points use e5-small-v2 in every cell, so the units are chunked once per paper and version (step 1, cached
in units/) and shared by all 5 embedder workers (step 2, one subprocess per embedder). Step 3 combines with the
stage-1 production arm and applies the registered shortlist and gate rules.

Usage: python combo_stage1b_semantic.py [--limit N]
Output: eval/phases/phase_12_combination/artifacts/stage1b_semantic/[smoke_N/]
"""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(HERE))
import combo_stage1_grid as s1  # noqa: E402

OUT = ROOT / "eval" / "phases" / "phase_12_combination" / "artifacts" / "stage1b_semantic"
STAGE1 = s1.OUT
VENDOR = ROOT / "eval" / "phases" / "phase_2_chunking" / "scripts" / "vendor" / "teammate_chunkers_49dcac6.py"
VENDOR_SHA256 = "206a7a57499a867db51315893d9d63ab0656531bc98aa82d6e8f489d5585adc6"
EXTRACTOR = "pymupdf_layout"
CHUNKERS = ["semantic_v1", "semantic_v2"]
SPLIT_MODEL = "intfloat/e5-small-v2"


def arms():
    return [s1.arm(EXTRACTOR, ch, em, mode) for ch in CHUNKERS for em in s1.EMBEDDERS for mode in s1.MODES]


def chunk_all(limit, out_dir):
    """Step 1: semantic units per paper and version, chunked once with e5 split points."""
    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    rp.setup_django()
    from apps.documents.services.chunkers import chunk_semantic as v1
    from apps.documents.services.chunking_utils import extract_sections_from_pdf
    assert hashlib.sha256(VENDOR.read_bytes()).hexdigest() == VENDOR_SHA256, "vendored chunker changed"
    spec = importlib.util.spec_from_file_location("teammate_chunkers_49dcac6", VENDOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fns = {"semantic_v1": v1, "semantic_v2": mod.chunk_semantic}
    udir = out_dir / "units"
    udir.mkdir(parents=True, exist_ok=True)
    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    papers = sorted(groups)[:limit] if limit else sorted(groups)
    model = rp.get_model(SPLIT_MODEL)
    for pid in papers:
        f = udir / f"{pid}.json"
        if f.exists():
            continue
        rec = {"paper_id": pid, "units": {}, "chunk_s": {}, "error": None}
        try:
            sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, groups[pid][0]["pdf_version"])))
            for ch, fn in fns.items():
                t = time.perf_counter()
                us = fn(sections, model, paper_id=pid)
                rec["chunk_s"][ch] = round(time.perf_counter() - t, 3)
                rec["units"][ch] = [{"chunk_id": u["chunk_id"], "text": u["text"], "page": u.get("page", 1),
                                       "section": u.get("section", "Main")} for u in us]
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"[:200]
        f.write_text(json.dumps(rec), encoding="utf-8")
        print(f"chunked {pid}", flush=True)


def worker(short, limit, out_dir):
    """Step 2: one embedder over both semantic versions and the 4 retrieval modes (mirrors s1.worker)."""
    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    rp.setup_django()
    import numpy as np
    model = s1.EMBEDDERS[short]
    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    papers = sorted(groups)[:limit] if limit else sorted(groups)
    rows, failures, eff = [], [], {}
    with rr.MemorySampler() as mem:
        rp.get_model(model)
        for pid in papers:
            items = groups[pid]
            cached = json.loads((out_dir / "units" / f"{pid}.json").read_text(encoding="utf-8"))
            qv = rp.cached_embed(model, [it["question"] for it in items], True, f"cret_{pid}")
            recs = [{"paper_id": pid, "question_id": it["question_id"]} for it in items]
            for ch in CHUNKERS:
                units = cached["units"].get(ch) or []
                e = eff.setdefault(f"{EXTRACTOR}|{ch}", {"units": 0, "embed_s": 0.0, "embedded_uncached": 0})
                if not units:
                    failures.append({"paper_id": pid, "chunker": ch, "error": cached.get("error") or "no units"})
                    for r in recs:
                        for mode in s1.MODES:
                            r[s1.arm(EXTRACTOR, ch, short, mode)] = {"ndcg10": 0.0, "cec_0.5": 0, "cec_0.3": 0, "cec_0.7": 0,
                                                                     "context_tokens": 0, "n_units": 0, "gate_score": 0.0}
                    continue
                texts = [u["text"] for u in units]
                tag = f"grid_{pid}_{EXTRACTOR}_{ch}"
                pdir = rp.EMB_CACHE / model.replace("/", "__") / "p"
                before = len(list(pdir.glob(f"{tag}_*.npy"))) if pdir.exists() else 0
                t = time.perf_counter()
                um = rp.cached_embed(model, texts, False, tag)
                dt = time.perf_counter() - t
                e["units"] += len(texts)
                if len(list(pdir.glob(f"{tag}_*.npy"))) > before:
                    e["embed_s"] += dt
                    e["embedded_uncached"] += len(texts)
                cand = rp.candidate_units_for_relevance(units, ch)
                for r, it, q in zip(recs, items, qv):
                    dense = um @ q
                    dense_top50 = set(int(i) for i in np.argsort(dense)[::-1][:rp.RETRIEVE_K])
                    for mode in s1.MODES:
                        ranked = rp.rank(mode, dense, texts, it["question"])
                        ctx = rp.assemble(ranked, units, ch)
                        m = rp.question_metrics(ctx, cand, it["retrieval_evidence"])
                        idx = s1.context_indices(ranked, units, ch, len(ctx))
                        if mode in ("rrf_prod", "rrf_fix"):
                            gs = max((float(dense[i]) if i in dense_top50 else 0.0 for i in idx), default=0.0)
                        else:
                            gs = max((float(dense[i]) for i in idx), default=0.0)
                        m["gate_score"] = round(gs, 5)
                        r[s1.arm(EXTRACTOR, ch, short, mode)] = m
            rows += recs
            print(f"{short} {pid} done", flush=True)
    res = {"embedder": short, "model": model, "rows": rows, "failures": failures,
           "efficiency": {k: {**v, "chunks_per_s": round(v["embedded_uncached"] / v["embed_s"], 2) if v["embed_s"] else None}
                          for k, v in eff.items()},
           "memory": mem.report()}
    (out_dir / f"embedder_{short}.json").write_text(json.dumps(res), encoding="utf-8")


def analyse(out_dir, stage1_dir):
    """Step 3: registered shortlist (top 2 semantic cells) and gates; CEC vs production, Holm m=40."""
    import numpy as np
    from eval_common import reval_runner as rr
    res = {s: json.load(open(out_dir / f"embedder_{s}.json", encoding="utf-8")) for s in s1.EMBEDDERS}
    prod = {}
    for line in open(stage1_dir / "per_query.jsonl", encoding="utf-8"):
        r = json.loads(line)
        prod[(r["paper_id"], r["question_id"])] = r[s1.PRODUCTION]
    key = lambda r: (r["paper_id"], r["question_id"])
    common = sorted(set.intersection(set(prod), *[{key(r) for r in v["rows"]} for v in res.values()]))
    by = {s: {key(r): r for r in v["rows"]} for s, v in res.items()}
    rows = []
    for k in common:
        rec = {"paper_id": k[0], "question_id": k[1], s1.PRODUCTION: prod[k]}
        for s in res:
            rec.update({a: m for a, m in by[s][k].items() if "|" in a})
        rows.append(rec)
    A = arms()
    metrics = ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7", "context_tokens", "n_units", "gate_score"]
    means = rr.arm_means(rows, A + [s1.PRODUCTION], metrics)
    fam_cec = rr.family(rows, [(a, s1.PRODUCTION) for a in A], "cec_0.5")
    top2 = sorted(A, key=lambda a: (means[a]["ndcg10"], means[a]["cec_0.5"]), reverse=True)[:2]
    prod_rate = float(np.mean(np.array([r[s1.PRODUCTION]["gate_score"] for r in rows]) < 0.80))
    gates = {}
    for a in top2:
        if a.split("|")[2] == "e5":
            gates[a] = 0.80
        else:
            s = np.array([r[a]["gate_score"] for r in rows])
            gates[a] = round(float(np.quantile(s, prod_rate)), 5) if prod_rate > 0 else 0.0
    s1sum = json.load(open(stage1_dir / "summary.json", encoding="utf-8"))
    combined = list(s1sum["shortlist"]) + [a for a in top2 if a not in s1sum["shortlist"]]
    level = lambda pos, m: {lv: round(float(np.mean([means[a][m] for a in A if a.split("|")[pos] == lv])), 4)
                            for lv in sorted({a.split("|")[pos] for a in A})}
    chunk_s = {ch: [] for ch in CHUNKERS}
    for f in sorted((out_dir / "units").glob("*.json")):
        u = json.loads(f.read_text(encoding="utf-8"))
        for ch in CHUNKERS:
            if ch in u["chunk_s"]:
                chunk_s[ch].append(u["chunk_s"][ch])
    summary = {
        "experiment": "COMBO-STAGE1-SEMANTIC-ADDON", "cohort": "C-RET-150", "papers": len({r["paper_id"] for r in rows}),
        "questions": len(rows), "combinations": len(A), "production": s1.PRODUCTION,
        "vendored_chunker_sha256": VENDOR_SHA256, "split_model": SPLIT_MODEL,
        "failures": {s: v["failures"] for s, v in res.items()},
        "means": means,
        "main_effects": {m: {"chunker": level(1, m), "embedder": level(2, m), "retrieval": level(3, m)} for m in ["ndcg10", "cec_0.5"]},
        "vs_production_cec_0.5": fam_cec,
        "semantic_top2": top2, "gate_thresholds": gates, "production_gate_refusal_rate": round(prod_rate, 4),
        "stage1_shortlist": s1sum["shortlist"], "combined_shortlist": combined,
        "combined_gate_thresholds": {**s1sum["gate_thresholds"], **gates},
        "chunking_s_per_paper_split_with_e5": {ch: {"p50": round(float(np.percentile(v, 50)), 2), "mean": round(float(np.mean(v)), 2)}
                                               for ch, v in chunk_s.items() if v},
        "efficiency": {s: {"index": v["efficiency"], "memory": v["memory"]} for s, v in res.items()},
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper"},
    }
    rr.write_outputs(out_dir, rows, summary)
    print(json.dumps({"questions": len(rows), "semantic_top2": top2, "combined_shortlist": combined, "gates": gates}, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--worker")
    ap.add_argument("--chunk", action="store_true")
    a = ap.parse_args()
    out = OUT / (f"smoke_{a.limit}" if a.limit else "")
    out.mkdir(parents=True, exist_ok=True)
    extra = ["--limit", str(a.limit)] if a.limit else []
    if a.chunk:
        chunk_all(a.limit, out)
        return
    if a.worker:
        worker(a.worker, a.limit, out)
        return
    subprocess.run([sys.executable, __file__, "--chunk"] + extra, check=True)
    for s in s1.EMBEDDERS:
        if not (out / f"embedder_{s}.json").exists():
            print(f"running {s}", flush=True)
            subprocess.run([sys.executable, __file__, "--worker", s] + extra, check=True)
    analyse(out, STAGE1 / (f"smoke_{a.limit}" if a.limit else ""))


if __name__ == "__main__":
    main()
