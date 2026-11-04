#!/usr/bin/env python3
"""
chunking extension (children only): hierarchical children without parent expansion (extension; registered in
protocol ext_rq2_child.json (archived) before running). Separate from the frozen chunking experiment family.

Cohort the QASPER component set (selection). Same children and e5 vectors as chunking experiment `hierarchical` (shared cache key
cret_<pid>_hierarchical). Arms:
  hierarchical   : production assembly (deduplicated parents, windowing, 1,600 tokens, <= 5 units)
  children_only  : the same ranked children assembled as flat units (1,600 tokens, <= 5 units, no expansion)
Primary: CEC@0.5, children_only vs hierarchical, single comparison, paper-cluster bootstrap B=10,000 seed 42.
Descriptive only: never adopted (it would remove parent expansion). nDCG@10 is reported but its relevance
units differ between arms (children vs parents), so it is not comparable across arms.

Usage: python evaluate_chunking_children.py [--limit N]
Output: eval/phases/phase_2_chunking/artifacts/chunking_children/
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
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402

E5 = "intfloat/e5-small-v2"
ARMS = ["hierarchical", "children_only"]
METRICS = ["cec_0.5", "cec_0.3", "cec_0.7", "ndcg10", "context_tokens", "n_units"]
OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "chunking_children"


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
            cand_parent = rp.candidate_units_for_relevance(units, "hierarchical")
            cand_child = rp.candidate_units_for_relevance(units, "flat")
            for it, q in zip(items, qv):
                ranked = rp.rank("dense", um @ q, texts, it["question"])
                ev = it["retrieval_evidence"]
                rows.append({
                    "paper_id": pid, "question_id": it["question_id"],
                    "hierarchical": rp.question_metrics(rp.assemble(ranked, units, "hierarchical"), cand_parent, ev),
                    "children_only": rp.question_metrics(rp.assemble(ranked, units, "flat"), cand_child, ev),
                })
            if n % 25 == 0:
                print(f"[{n}/{len(papers)}] {time.time() - t0:.0f}s", flush=True)

    pair = [("children_only", "hierarchical")]
    primary = rr.family(rows, pair, "cec_0.5")
    for r in primary:
        r["ci95_half_width"] = round((r["ci95"][1] - r["ci95"][0]) / 2, 4)
    summary = {
        "experiment": "EXT-RQ2-CHILD", "cohort": "C-RET", "role": "SELECTION EXTENSION (descriptive)",
        "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
        "means": rr.arm_means(rows, ARMS, METRICS),
        "primary_cec_0.5": primary,
        "sensitivity_cec_0.3": rr.family(rows, pair, "cec_0.3"),
        "sensitivity_cec_0.7": rr.family(rows, pair, "cec_0.7"),
        "note_ndcg10": "relevance units differ (children vs parents); nDCG@10 not comparable across arms",
        "decision_rule": "descriptive only; never adopted",
        "memory": mem.report(), "elapsed_s": round(time.time() - t0, 1), "bootstrap": {"B": rr.B, "seed": rr.SEED},
    }
    rr.write_outputs(OUT if not args.limit else OUT / f"smoke_{args.limit}", rows, summary)
    print({k: summary[k] for k in ("papers", "questions")})


if __name__ == "__main__":
    main()
