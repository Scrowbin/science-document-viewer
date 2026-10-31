#!/usr/bin/env python3
"""
RQ2-diag: stepwise decomposition of the hierarchical score gap (RQ2 0.6880 vs production parity 0.5049) on the
47 RQ2 Dev papers / 127 questions. Diagnostic only (exploratory, descriptive; no inference).
Pre-registered steps: reports/revalidation/protocol/rq1_rq4.json "RQ2-diag".

Same sections (pymupdf_layout), same e5 vectors, same dense ranking in every step; only the context
construction and the scoring convention change:
  S0  RQ2 protocol: rank ALL unique parents (no budget, no cap), nDCG@10 with RQ2's R_q (no floor)
  S1  budget 1,600 + 5-unit cap, parents over 800 tokens cut to the first 400 words (RQ4 benchmark rule)
  S2  budget + cap + production windowing (+-200 words around the matched child)       [= harness assemble]
  S3  RagService.search_hierarchical on an in-memory Qdrant (the parity script's production call)
Metrics at each step: nDCG@10 (budgeted convention, R_q floored at 1) and CEC@0.5; S0 also in RQ2's convention.
Output: eval/phases/phase_2_chunking/artifacts/rq2diag/
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
import numpy as np  # noqa: E402
from apps.documents.services.chunkers import estimate_tokens  # noqa: E402
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402
from apps.documents.services.rag_service import RagService  # noqa: E402
from eval_common.relevance import count_relevant_chunks, is_chunk_hit  # noqa: E402
from eval_common.revalidation import context_evidence_coverage, qasper_text_evidence  # noqa: E402
from eval_common.stats import compute_ndcg  # noqa: E402

E5 = "intfloat/e5-small-v2"
OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "rq2diag"


def parents_in_rank_order(ranked, units):
    seen, out = set(), []
    for i in ranked:
        u = units[i]
        if u["parent_id"] not in seen:
            seen.add(u["parent_id"])
            out.append(u)
    return out


def score(ctx_texts, cand, ev, floor=True):
    rel = [1 if is_chunk_hit({"text": t}, "", "", ev, tau=0.5) else 0 for t in ctx_texts]
    rq = count_relevant_chunks(cand, "", "", ev, tau=0.5)
    return {"ndcg10": compute_ndcg((rel + [0] * 10)[:10] if len(rel) < 10 else rel, max(1, rq) if floor else rq, k=10),
            "cec_0.5": context_evidence_coverage("\n\n".join(ctx_texts[:5]) if floor else "\n\n".join(ctx_texts), ev)}


def main():
    dev = json.load(open(ROOT / "eval/data/qasper_official/qasper-dev-v0.3.json", encoding="utf-8"))
    inhouse = {q["id"]: q["original_id"] for q in json.load(open(ROOT / "eval/prepared/qasper_sampled.json", encoding="utf-8"))}
    by_paper = {}
    for line in open(ROOT / "eval/results/rq2_chunking_queries_20261024_013443.jsonl"):
        r = json.loads(line)
        by_paper.setdefault(r["paper_arxiv_id"], set()).add(r["query_id"])

    svc = RagService(in_memory=True)
    rows = []
    for pid in sorted(by_paper):
        qas = {qa["question_id"]: qa for qa in dev[pid]["qas"]}
        qs = [qas[inhouse[i]] for i in sorted(by_paper[pid])]
        pdf = str(rr.pdf_path("DEV47", pid))
        sections = extract_sections_from_pdf(pdf)
        units = rp.build_units(sections, "hierarchical", pid)
        texts = [u["text"] for u in units]
        um = rp.cached_embed(E5, texts, False, f"dev47_{pid}_hierarchical")
        qv = rp.cached_embed(E5, [qa["question"] for qa in qs], True, f"dev47_{pid}")
        cand = rp.candidate_units_for_relevance(units, "hierarchical")
        coll = f"rq2diag_{pid.replace('.', '_')}"
        chunks = [dict(u, document_id=pid, paper_arxiv_id=pid) for u in units]
        svc.index_chunks(collection_name=coll, chunks=chunks, recreate=True, chunking_strategy="hierarchical")
        for qa, q in zip(qs, qv):
            ev = qasper_text_evidence(qa)
            if not ev:
                continue
            ranked = rp.rank("dense", um @ q, texts, qa["question"])
            parents = parents_in_rank_order(ranked, units)
            rec = {"paper_id": pid, "question_id": qa["question_id"]}
            s0_texts = [p["parent_text"] for p in parents]
            rec["S0"] = score(s0_texts, cand, ev, floor=False)
            rec["S0_budgeted_convention"] = score(s0_texts[:5], cand, ev)
            s1, used = [], 0
            for p in parents:
                t = p["parent_text"]
                if (p.get("parent_tokens") or estimate_tokens(t)) > 800:
                    t = " ".join(t.split()[:400])
                tok = estimate_tokens(t)
                if used + tok > 1600 and s1:
                    break
                s1.append(t)
                used += tok
                if len(s1) >= 5:
                    break
            rec["S1"] = score(s1, cand, ev)
            rec["S2"] = score([c["text"] for c in rp.assemble(ranked, units, "hierarchical")], cand, ev)
            hits = svc.search_hierarchical(collection_name=coll, query=qa["question"], token_budget=1600,
                                           candidate_pool=20, max_parent_tokens=800, filter_arxiv_id=pid)
            rec["S3"] = score([item.get("text", "") for _, item in hits], cand, ev)
            rows.append(rec)
        print(pid, len(qs), flush=True)

    steps = ["S0", "S0_budgeted_convention", "S1", "S2", "S3"]
    summary = {"experiment": "RQ2-diag", "cohort": "Dev 47 (diagnostic)", "papers": len(by_paper), "questions": len(rows),
               "means": {s: {m: round(float(np.mean([r[s][m] for r in rows])), 4) for m in ("ndcg10", "cec_0.5")} for s in steps},
               "reference": {"RQ2_hierarchical_ndcg10": 0.6880, "parity_hierarchical_ndcg10": 0.5049},
               "notes": "S0 should reproduce 0.6880 and S3 should be close to 0.5049; the step differences attribute the gap."}
    rr.write_outputs(OUT, rows, summary)
    print(json.dumps(summary["means"], indent=1))


if __name__ == "__main__":
    main()
