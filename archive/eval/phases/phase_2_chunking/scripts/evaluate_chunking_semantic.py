#!/usr/bin/env python3
"""
chunking extension (semantic): semantic chunking under the chunking experiment protocol (extension; registered in
protocol ext_rq2_semantic.json (archived) before running). Separate from the frozen chunking experiment family.

Cohort the QASPER component set (selection). pymupdf_layout sections -> chunker -> e5-small-v2 dense ranking -> production
context assembly (1,600 est. tokens, <= 5 units). Arms:
  hierarchical : production (same children and cached e5 vectors as chunking experiment)
  semantic_v1  : apps.documents.services.chunkers.chunk_semantic on this branch (the historical implementation)
  semantic_v2  : the teammate's chunk_semantic from origin/main commit 49dcac6, vendored unchanged in
                 vendor/teammate_chunkers_49dcac6.py (production code is not changed)
Both semantic arms use each implementation's defaults (max_tokens 400, 25th-percentile threshold; v2 also
min_tokens 60, buffer 1) and the e5 model for sentence similarity, and are assembled as flat units.
Primary (as chunking experiment after the CEC fallback): budgeted nDCG@10, semantic_vX vs hierarchical, Holm m=2,
paper-cluster bootstrap B=10,000 seed 42. Secondary: CEC@0.5 (caveat: check agreement 0.667).

Usage: python evaluate_chunking_semantic.py [--limit N]
Output: eval/phases/phase_2_chunking/artifacts/chunking_semantic/
"""

import argparse
import hashlib
import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
from apps.documents.services.chunkers import chunk_semantic as chunk_semantic_v1  # noqa: E402
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402

VENDOR = Path(__file__).resolve().parent / "vendor" / "teammate_chunkers_49dcac6.py"
VENDOR_SHA256 = "206a7a57499a867db51315893d9d63ab0656531bc98aa82d6e8f489d5585adc6"
_spec = importlib.util.spec_from_file_location("teammate_chunkers_49dcac6", VENDOR)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
chunk_semantic_v2 = _mod.chunk_semantic

E5 = "intfloat/e5-small-v2"
ARMS = ["hierarchical", "semantic_v1", "semantic_v2"]
METRICS = ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7", "context_tokens", "n_units"]
OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "chunking_semantic"


def build(arm, sections, pid):
    if arm == "hierarchical":
        return rp.build_units(sections, "hierarchical", pid)
    fn = chunk_semantic_v1 if arm == "semantic_v1" else chunk_semantic_v2
    return fn(sections, rp.get_model(E5), paper_id=pid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    assert hashlib.sha256(VENDOR.read_bytes()).hexdigest() == VENDOR_SHA256, "vendored chunker changed"
    groups = rr.group_items(rr.load_cohort("C-RET"))
    papers = sorted(groups)[: args.limit] if args.limit else sorted(groups)
    rows, failures = [], []
    stats = {a: {"units": 0, "chunk_s": 0.0} for a in ARMS}
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
            for arm in ARMS:
                try:
                    tc = time.perf_counter()
                    units = build(arm, sections, pid)
                    stats[arm]["chunk_s"] += time.perf_counter() - tc
                    assert units, "no units"
                except Exception as e:
                    failures.append({"paper_id": pid, "arm": arm, "error": f"{type(e).__name__}: {e}"[:200]})
                    continue
                stats[arm]["units"] += len(units)
                strategy = "hierarchical" if arm == "hierarchical" else "flat"
                texts = [u["text"] for u in units]
                tag = f"cret_{pid}_hierarchical" if arm == "hierarchical" else f"cret_{pid}_{arm}"
                um = rp.cached_embed(E5, texts, False, tag)
                cand = rp.candidate_units_for_relevance(units, strategy)
                for rec, it, q in zip(per_q, items, qv):
                    ctx = rp.assemble(rp.rank("dense", um @ q, texts, it["question"]), units, strategy)
                    rec[arm] = rp.question_metrics(ctx, cand, it["retrieval_evidence"])
            rows += [r for r in per_q if all(a in r for a in ARMS)]
            if n % 25 == 0:
                print(f"[{n}/{len(papers)}] {time.time() - t0:.0f}s", flush=True)

    pairs = [("semantic_v1", "hierarchical"), ("semantic_v2", "hierarchical")]
    primary = rr.family(rows, pairs, "ndcg10")
    win = [r for r in primary if r["diff"] >= 0.05 and r["ci95"][0] > 0 and r["p_holm"] < 0.05]
    summary = {
        "experiment": "EXT-RQ2-SEMANTIC", "cohort": "C-RET", "role": "SELECTION EXTENSION",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
        "vendored_chunker": {"file": str(VENDOR.relative_to(ROOT)), "sha256": VENDOR_SHA256,
                             "source": "origin/main commit 49dcac6673e72ac16ac10243eae383c3fc670f10"},
        "means": rr.arm_means(rows, ARMS, METRICS),
        "primary_ndcg10": primary,
        "secondary_cec_0.5": rr.family(rows, pairs, "cec_0.5"),
        "sensitivity_cec_0.3": rr.family(rows, pairs, "cec_0.3"),
        "sensitivity_cec_0.7": rr.family(rows, pairs, "cec_0.7"),
        "descriptive_v2_vs_v1_ndcg10": rr.compare(rows, "semantic_v1", "semantic_v2", "ndcg10"),
        "decision_rule": "a semantic arm enters combination stage 2 (as pymupdf_layout|semantic_vX|e5|dense) only if it "
                         "beats hierarchical by >= 0.05 budgeted nDCG@10 with CI lower bound > 0 (Holm-adjusted p < 0.05); "
                         "production keeps hierarchical unless stage 2 selects it",
        "decision": ("enter stage 2: " + ", ".join(r["comparison"].split(" - ")[0] for r in win)) if win else "keep hierarchical; no semantic arm enters stage 2",
        "index": {a: {"units": v["units"], "units_per_paper": round(v["units"] / max(1, len(papers)), 1),
                      "chunking_s_per_paper": round(v["chunk_s"] / max(1, len(papers)), 2)} for a, v in stats.items()},
        "memory": mem.report(), "elapsed_s": round(time.time() - t0, 1), "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    rr.write_outputs(OUT if not args.limit else OUT / f"smoke_{args.limit}", rows, summary)
    print({k: summary[k] for k in ("papers", "questions", "decision")})


if __name__ == "__main__":
    main()
