#!/usr/bin/env python3
"""
Pre-Gate-B validation of the revalidation harness (backend/scripts/eval_common/reval_pipeline.py).

A. Fusion fidelity vs E1: harness rank() for dense / rrf_prod / convex_prod, fed through E1's own
   expansion and metric code, reproduces the stored E1 Dev per-query nDCG@10 (4 dp) for 3 papers.
B. Chunking/embedding fidelity vs RQ2: harness build_units() + embed() on the same PDFs, fed to RQ2's own
   evaluate_retrieval_with_matrix, reproduces the stored RQ2 per-query nDCG@10 (4 dp) for 3 papers.
C. Production fidelity: harness rank('rrf_prod') + assemble('hierarchical') returns the same context
   texts as the real DocumentRAG.hybrid_search (in-memory dense path) for every query of 3 papers.

No new cohort is touched. Output: eval/phases/phase_0_baseline/artifacts/revalidation/harness_validation.json
"""

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402

rp.setup_django()
import numpy as np  # noqa: E402

OUT = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "revalidation" / "harness_validation.json"
E5 = "intfloat/e5-small-v2"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_e1(n_papers=3):
    rq4 = load_module(ROOT / "eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py", "rq4")
    queries, chunks, pmap, _ = rq4.load_official_qasper_corpus(splits=["dev"], strategy="hierarchical")
    doc = np.load(rq4.CACHE_DIR / "full_qasper_dev_hierarchical_doc_embs.npy")
    qe = np.load(rq4.CACHE_DIR / "full_qasper_dev_hierarchical_query_embs.npy")
    stored = {}
    for line in open(ROOT / "eval/phases/phase_6_hybrid_retrieval/artifacts/rq4p_production_fusion/dev_per_query.jsonl"):
        r = json.loads(line)
        stored[r["query_id"]] = r
    papers = sorted({q["paper_arxiv_id"] for q in queries})[:n_papers]
    qidx = {q["query_id"]: i for i, q in enumerate(queries)}
    rows, ok = [], True
    for q in queries:
        aid = q["paper_arxiv_id"]
        if aid not in papers:
            continue
        cand = pmap[aid]
        sims = doc[cand] @ qe[qidx[q["query_id"]]]
        texts = [chunks[i]["text"] for i in cand]
        seen, units = set(), []
        for i in cand:
            c = chunks[i]
            if c.get("parent_id") not in seen:
                seen.add(c.get("parent_id"))
                units.append({"paper_arxiv_id": aid, "text": c.get("parent_text") or c["text"]})
        rq = max(1, rq4.count_relevant_chunks(units, aid, q["verbatim_evidence_quote"], q["evidence_list"], tau=0.5))
        for mode in ("dense", "rrf_prod", "convex_prod"):
            ranked = [cand[i] for i in rp.rank(mode, sims, texts, q["question"])][: rq4.TOP_K]
            passages = rq4.expand_to_parents(ranked, chunks, budget_tokens=rq4.CONTEXT_BUDGET_TOKENS, max_parents=rq4.MAX_PARENTS)
            rel = [1 if rq4.is_chunk_hit(p, aid, q["verbatim_evidence_quote"], q["evidence_list"], tau=0.5) else 0 for p in passages]
            rel += [0] * (rq4.TOP_K - len(rel))
            got = round(rq4.compute_ndcg(rel[:10], rq, k=10), 4)
            ref = round(stored[q["query_id"]][mode]["ndcg10"], 4)
            ok &= got == ref
            rows.append({"query_id": q["query_id"], "mode": mode, "harness": got, "stored_E1": ref})
    return {"papers": papers, "comparisons": len(rows), "all_match_4dp": ok,
            "mismatches": [r for r in rows if r["harness"] != r["stored_E1"]]}


def check_rq2(n_papers=3):
    from apps.documents.services.chunking_utils import extract_sections_from_pdf
    rq2 = load_module(ROOT / "backend/scripts/evaluate_rq2_chunking.py", "rq2")
    stored = {}
    for line in open(ROOT / "eval/results/rq2_chunking_queries_20261024_013443.jsonl"):
        r = json.loads(line)
        stored[(r["query_id"], r["strategy"])] = r
    qa = json.load(open(ROOT / "eval/prepared/qasper_sampled.json", encoding="utf-8"))
    papers = sorted({r["paper_arxiv_id"] for r in stored.values()})[:n_papers]
    rows, ok = [], True
    for aid in papers:
        pdf = ROOT / "eval" / "pdfs" / "dev" / f"{aid}.pdf"
        qs = [q for q in qa if q["paper_arxiv_id"] == aid and q.get("question_type") != "unanswerable"]
        sections = extract_sections_from_pdf(str(pdf))
        qm = rp.embed(E5, [q["question"] for q in qs], is_query=True)
        for st in ("fixed_size", "section_overlap", "hierarchical"):
            units = rp.build_units(sections, st, aid)
            um = rp.embed(E5, [u["text"] for u in units], is_query=False)
            res = rq2.evaluate_retrieval_with_matrix(qm @ um.T, units, qs, aid, tau=0.5, context_budget_tokens=1600,
                                                     is_hierarchical_parent=(st == "hierarchical"))
            for q, got in zip(qs, res["ndcg10"]):
                ref = stored[(q["id"], st)]["ndcg10"]
                match = abs(round(got, 4) - ref) < 1e-4
                ok &= match
                rows.append({"query_id": q["id"], "strategy": st, "harness": round(got, 4), "stored_RQ2": ref})
    return {"papers": papers, "comparisons": len(rows), "all_match_4dp": ok,
            "mismatches": [r for r in rows if abs(r["harness"] - r["stored_RQ2"]) >= 1e-4]}


def check_production(n_papers=3):
    from apps.documents.services import rag_service
    from apps.documents.services.chunking_utils import chunk_document, extract_sections_from_pdf

    class _NoQdrant:
        class client:
            @staticmethod
            def collection_exists(name):
                return False

        def search_dense(self, **kw):
            return []

    rag_service.RagService.get_instance = classmethod(lambda cls, **kw: _NoQdrant())
    qa = json.load(open(ROOT / "eval/prepared/qasper_sampled.json", encoding="utf-8"))
    papers = sorted({q["paper_arxiv_id"] for q in qa if (ROOT / "eval" / "pdfs" / "dev" / f"{q['paper_arxiv_id']}.pdf").exists()})[:n_papers]
    compared, ok, mism = 0, True, []
    for aid in papers:
        pdf = str(ROOT / "eval" / "pdfs" / "dev" / f"{aid}.pdf")
        docs = chunk_document(pdf, strategy="hierarchical")
        units = rp.build_units(extract_sections_from_pdf(pdf), "hierarchical", Path(pdf).stem)
        same_units = [d.page_content for d in docs] == [u["text"] for u in units]
        emb = rp.embed(E5, [u["text"] for u in units], is_query=False)
        rag = rag_service.DocumentRAG(0, docs, embeddings=emb, collection_name="validation_unused")
        for q in [q for q in qa if q["paper_arxiv_id"] == aid]:
            prod = [d.page_content for d, _ in rag.hybrid_search(q["question"], top_k=5)]
            qv = rp.embed(E5, [q["question"]], is_query=True)[0]
            mine = [c["text"] for c in rp.assemble(rp.rank("rrf_prod", emb @ qv, [u["text"] for u in units], q["question"]),
                                                   units, "hierarchical")]
            compared += 1
            if prod != mine or not same_units:
                ok = False
                mism.append({"paper": aid, "query_id": q["id"], "same_units": same_units,
                             "n_prod": len(prod), "n_harness": len(mine)})
    return {"papers": papers, "queries_compared": compared, "identical_contexts": ok, "mismatches": mism}


if __name__ == "__main__":
    result = {"A_e1_fusion": check_e1(), "B_rq2_chunk_embed": check_rq2(), "C_production_hybrid_search": check_production()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "mismatches"} | {"n_mismatch": len(v["mismatches"])}
                      for k, v in result.items()}, indent=1))
