#!/usr/bin/env python3
"""
EXT-RQ3-SPECTER2: scientific-domain embedding on C-RET-150 (extension; registered in
reports/revalidation/protocol/ext_rq3_specter2.json before running). Separate from the frozen RQ3-v2 family.

Model: allenai/specter2_base (110M, Apache-2.0) with adapters as the model card prescribes for ad-hoc search:
questions -> allenai/specter2_adhoc_query, passages -> allenai/specter2 (proximity). Embedding = [CLS] of the
last hidden state, L2-normalised, max_length 512. Same pipeline and metrics as RQ3-v2 (pymupdf_layout ->
hierarchical children -> dense ranking -> production context assembly).
Compared with e5-small-v2 using the e5 rows produced by RQ3-v2 (identical papers/questions/pipeline).
Decision: the frozen RQ3 rule as a single separate test: diff >= +0.04 nDCG@10, CI lower bound > 0, and
P50 query latency <= 1.5x e5. Efficiency: indexing chunks/s (batch 32), query latency P50/P95
(110 queries, 10 warm-up), peak working set (own subprocess).

Usage: python rq3ext_specter2.py [--limit N]    (run after rq3v2_shortlist.py)
Output: eval/phases/phase_3_embedding/artifacts/rq3_ext_specter2/
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
import numpy as np  # noqa: E402
import torch  # noqa: E402
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402

E5_FILE = ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts" / "rq3v2" / "model_intfloat__e5-small-v2.json"
ARM = "specter2"


class Specter2:
    def __init__(self):
        from adapters import AutoAdapterModel
        from transformers import AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained("allenai/specter2_base")
        self.model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
        self.model.load_adapter("allenai/specter2", source="hf", load_as="proximity")
        self.model.load_adapter("allenai/specter2_adhoc_query", source="hf", load_as="adhoc_query")
        self.model.eval()

    @torch.no_grad()
    def encode(self, texts, is_query, batch_size=32):
        self.model.set_active_adapters("adhoc_query" if is_query else "proximity")
        out = []
        for i in range(0, len(texts), batch_size):
            enc = self.tok(texts[i:i + batch_size], padding=True, truncation=True, max_length=512, return_tensors="pt")
            v = self.model(**enc).last_hidden_state[:, 0, :]
            out.append(torch.nn.functional.normalize(v, dim=-1).numpy().astype(np.float32))
        return np.vstack(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    e5 = json.load(open(E5_FILE, encoding="utf-8")) if not args.limit else None
    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    papers = sorted(groups)[: args.limit] if args.limit else sorted(groups)
    rows, failures, n_units, embed_s = [], [], 0, 0.0
    with rr.MemorySampler() as mem:
        model = Specter2()
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
            um = model.encode(texts, is_query=False)
            embed_s += time.perf_counter() - t
            n_units += len(texts)
            qv = model.encode([it["question"] for it in items], is_query=True)
            cand = rp.candidate_units_for_relevance(units, "hierarchical")
            for it, q in zip(items, qv):
                ctx = rp.assemble(rp.rank("dense", um @ q, texts, it["question"]), units, "hierarchical")
                rows.append({"paper_id": pid, "question_id": it["question_id"],
                             ARM: rp.question_metrics(ctx, cand, it["retrieval_evidence"])})
        qs = [it["question"] for p in sorted(groups) for it in groups[p]][:110]
        lat = []
        for i, q in enumerate(qs):
            t = time.perf_counter()
            model.encode([q], is_query=True, batch_size=1)
            if i >= 10:
                lat.append((time.perf_counter() - t) * 1000)

    eff = {"indexing_chunks_per_s": round(n_units / embed_s, 2) if embed_s else None,
           "query_latency_ms": {"p50": round(float(np.percentile(lat, 50)), 2), "p95": round(float(np.percentile(lat, 95)), 2), "n": len(lat)},
           "memory": mem.report(), "units": n_units}
    summary = {"experiment": "EXT-RQ3-SPECTER2", "cohort": "C-RET-150", "role": "SELECTION EXTENSION",
               "model": "allenai/specter2_base + specter2_adhoc_query (queries) / specter2 proximity (passages)",
               "papers": len({r["paper_id"] for r in rows}), "questions": len(rows), "failures": failures,
               "efficiency": eff, "bootstrap": {"B": rr.B, "seed": rr.SEED}}
    if e5:
        e5_rows = {(r["paper_id"], r["question_id"]): r["m"] for r in e5["rows"]}
        rows = [{**r, "e5": e5_rows[(r["paper_id"], r["question_id"])]} for r in rows if (r["paper_id"], r["question_id"]) in e5_rows]
        cmp_ = rr.compare(rows, "e5", ARM, "ndcg10")
        cmp_["ci95_half_width"] = round((cmp_["ci95"][1] - cmp_["ci95"][0]) / 2, 4)
        lat_ok = eff["query_latency_ms"]["p50"] <= 1.5 * e5["query_latency_ms"]["p50"]
        summary.update({
            "paired_questions": len(rows),
            "means": rr.arm_means(rows, ["e5", ARM], ["ndcg10", "cec_0.5", "cec_0.3", "cec_0.7"]),
            "primary_ndcg10_vs_e5": cmp_, "secondary_cec_0.5_vs_e5": rr.compare(rows, "e5", ARM, "cec_0.5"),
            "e5_query_latency_ms": e5["query_latency_ms"],
            "decision_rule": "switch only if diff >= +0.04, CI lower bound > 0, P50 latency <= 1.5x e5",
            "decision": "specter2" if (cmp_["diff"] >= 0.04 and cmp_["ci95"][0] > 0 and lat_ok) else "keep intfloat/e5-small-v2",
        })
    out = ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts" / "rq3_ext_specter2"
    rr.write_outputs(out if not args.limit else out / f"smoke_{args.limit}", rows, summary)
    print({k: summary.get(k) for k in ("papers", "questions", "decision")})


if __name__ == "__main__":
    main()
