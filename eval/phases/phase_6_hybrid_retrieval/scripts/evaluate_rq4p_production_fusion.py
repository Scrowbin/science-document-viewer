#!/usr/bin/env python3
"""
E1 / RQ4-P: RRF vs Convex fusion under production-style BM25 (post-audit, 2026-10-29).

Why: the original RQ4 benchmark (evaluate_full_qasper_rq4_hybrid.py) scores BM25 with WordPiece
tokens, a stopword list and IDF over the whole split. Production (`DocumentRAG.hybrid_search`)
uses `rank_bm25.BM25Okapi` over `text.lower().split()` of one document's child chunks, with no
stopwords, then RRF (k=60) over the top-50 dense and top-50 BM25 candidates. This script keeps
everything else identical to RQ4 (corpus, hierarchical chunks, cached e5 embeddings, relevance
labels tau=0.50, parent expansion with <=5 parents / 1,600 tokens, metrics) and changes only the
BM25 implementation feeding the fusions.

Arms
  dense            Dense only (e5-small-v2, exact cosine)                       [RQ4 arm]
  bm25_bench       WordPiece BM25, split-wide IDF                                [RQ4 arm]
  rrf_bench        RRF k=60 over dense + bm25_bench                               [RQ4 arm, reproduction gate]
  convex_bench     alpha=0.7 min-max convex over dense + bm25_bench               [RQ4 arm, reproduction gate]
  bm25_prod        BM25Okapi, whitespace tokens, per-document IDF (diagnostic)
  rrf_prod         RRF k=60 over top-50 dense + top-50 bm25_prod (production logic)
  convex_prod      alpha=0.7 min-max convex over dense + bm25_prod
  convex_prod_a{a} alpha sweep {0.5,...,0.9}  (Dev only, descriptive)

Pre-declared inference (Test only): Holm m=3 over
  rrf_prod vs dense, convex_prod vs dense, convex_prod vs rrf_prod
Primary metric: nDCG@10 over the budgeted parent list (RQ4 definition).
Dev results and the alpha sweep are descriptive. Test was already used by RQ4, so Test results are
a post-selection diagnostic, not an independent confirmation.

Run from the repository root:
  backend/venv/Scripts/python eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_rq4p_production_fusion.py --split dev
  backend/venv/Scripts/python eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_rq4p_production_fusion.py --split test
"""

import argparse
import importlib.util
import json
import platform
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rq4", HERE / "evaluate_full_qasper_rq4_hybrid.py")
rq4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rq4)

OUT_DIR = rq4.ARTIFACTS_DIR / "rq4p_production_fusion"
OUT_DIR.mkdir(parents=True, exist_ok=True)
ALPHAS = [0.5, 0.6, 0.7, 0.8, 0.9]
RETRIEVE_K = 50  # production: retrieve_k = min(50, num_docs)
RQ4_REFERENCE = {  # nDCG@10 from the original RQ4 artifacts (reproduction gate)
    "dev": {"dense": 0.5610, "rrf_bench": 0.5573, "convex_bench": 0.5650},
    "test": {"dense": 0.5655, "rrf_bench": 0.5662, "convex_bench": 0.5806},
}


def rrf_prod(dense_sims, bm25_scores, cand):
    """Mirror of DocumentRAG.hybrid_search fusion (indices are local to the paper)."""
    k = min(RETRIEVE_K, len(cand))
    dense_top = list(np.argsort(dense_sims)[::-1][:k])
    bm25_top = list(np.argsort(bm25_scores)[::-1][:k])
    s = {}
    for rank, i in enumerate(dense_top):
        s[int(i)] = s.get(int(i), 0.0) + 1.0 / (60 + rank + 1)
    for rank, i in enumerate(bm25_top):
        s[int(i)] = s.get(int(i), 0.0) + 1.0 / (60 + rank + 1)
    order = sorted(s, key=lambda i: s[i], reverse=True)
    return [cand[i] for i in order]


def metrics_for(child_ranks, chunks, aid, quote, ev_list, total_relevant, tau):
    passages = rq4.expand_to_parents(child_ranks, chunks, budget_tokens=rq4.CONTEXT_BUDGET_TOKENS,
                                     max_parents=rq4.MAX_PARENTS)
    rel = [1 if rq4.is_chunk_hit(p, aid, quote, ev_list, tau=tau) else 0 for p in passages]
    rel += [0] * (rq4.TOP_K - len(rel))
    mrr = next((1.0 / (i + 1) for i, r in enumerate(rel[:10]) if r), 0.0)
    return {
        "ndcg10": rq4.compute_ndcg(rel[:10], total_relevant, k=10),
        "ndcg4": rq4.compute_ndcg(rel[:4], total_relevant, k=4),
        "mrr10": mrr,
        "recall20": min(1.0, sum(rel[:20]) / total_relevant),
        "hit5": 1.0 if any(rel[:5]) else 0.0,
        "n_parents": len(passages),
    }


def run(split, tau=0.50, n_boot=2000):
    t0 = time.time()
    queries, chunks, paper_chunks_map, _ = rq4.load_official_qasper_corpus(splits=[split], strategy="hierarchical")
    pref = f"full_qasper_{split}_hierarchical"
    doc_embs = np.load(rq4.CACHE_DIR / f"{pref}_doc_embs.npy")
    q_embs = np.load(rq4.CACHE_DIR / f"{pref}_query_embs.npy")
    if len(doc_embs) != len(chunks) or len(q_embs) != len(queries):
        sys.exit(f"Cached embedding size mismatch ({len(doc_embs)}/{len(chunks)}, {len(q_embs)}/{len(queries)})")

    tok = rq4.AutoTokenizer.from_pretrained("intfloat/e5-small-v2")
    bm25_bench = rq4.WordPieceBM25(chunks, tok)
    prod_index = {aid: BM25Okapi([chunks[i]["text"].lower().split() for i in idxs])
                  for aid, idxs in paper_chunks_map.items() if idxs}

    # Relevance counts, identical to RQ4 (unique parent sections, floored at 1)
    rq_map = {}
    for q in queries:
        aid = q["paper_arxiv_id"]
        seen, units = set(), []
        for i in paper_chunks_map.get(aid, []):
            c = chunks[i]
            if c.get("parent_id") not in seen:
                seen.add(c.get("parent_id"))
                units.append({"paper_arxiv_id": aid, "text": c.get("parent_text") or c.get("text", ""),
                              "section": c.get("section", "")})
        rq_map[q["query_id"]] = max(1, rq4.count_relevant_chunks(units, aid, q["verbatim_evidence_quote"],
                                                                q["evidence_list"], tau=tau))

    arms = ["dense", "bm25_bench", "rrf_bench", "convex_bench", "bm25_prod", "rrf_prod", "convex_prod"]
    if split == "dev":
        arms += [f"convex_prod_a{a}" for a in ALPHAS if a != 0.7]
    by_paper = {a: defaultdict(list) for a in arms}
    per_query = []
    lat = defaultdict(list)
    q_idx = {q["query_id"]: i for i, q in enumerate(queries)}
    zero_bm25_prod = 0

    for q in queries:
        aid, qid = q["paper_arxiv_id"], q["query_id"]
        cand = paper_chunks_map[aid]
        sims = doc_embs[cand] @ q_embs[q_idx[qid]]
        dense_ranked = [cand[i] for i in np.argsort(sims)[::-1]]
        dense_scores = {cand[i]: float(sims[i]) for i in range(len(cand))}

        bb = bm25_bench.score_query(q["question"], cand)
        bm25b_ranked = sorted(cand, key=lambda i: bb.get(i, 0.0), reverse=True)

        t = time.perf_counter()
        bp = prod_index[aid].get_scores(q["question"].lower().split())
        lat["bm25_prod_scoring"].append((time.perf_counter() - t) * 1000)
        if not np.any(bp > 0):
            zero_bm25_prod += 1
        bm25p_ranked = [cand[i] for i in np.argsort(bp)[::-1]]
        bp_scores = {cand[i]: float(bp[i]) for i in range(len(cand))}

        rankings = {"dense": dense_ranked[:rq4.TOP_K], "bm25_bench": bm25b_ranked[:rq4.TOP_K],
                    "bm25_prod": bm25p_ranked[:rq4.TOP_K]}
        t = time.perf_counter()
        rankings["rrf_bench"] = rq4.rrf_fuse(dense_ranked, bm25b_ranked, k_rrf=60, top_k=rq4.TOP_K)
        lat["rrf_fusion"].append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        rankings["convex_bench"] = rq4.convex_fuse(dense_scores, bb, alpha=0.7, top_k=rq4.TOP_K)
        lat["convex_fusion"].append((time.perf_counter() - t) * 1000)
        rankings["rrf_prod"] = rrf_prod(sims, bp, cand)[:rq4.TOP_K]
        rankings["convex_prod"] = rq4.convex_fuse(dense_scores, bp_scores, alpha=0.7, top_k=rq4.TOP_K)
        if split == "dev":
            for a in ALPHAS:
                if a != 0.7:
                    rankings[f"convex_prod_a{a}"] = rq4.convex_fuse(dense_scores, bp_scores, alpha=a, top_k=rq4.TOP_K)

        rec = {"query_id": qid, "paper_arxiv_id": aid, "n_children": len(cand),
               "bm25_prod_all_zero": bool(not np.any(bp > 0))}
        for a in arms:
            m = metrics_for(rankings[a], chunks, aid, q["verbatim_evidence_quote"], q["evidence_list"], rq_map[qid], tau)
            rec[a] = m
            by_paper[a][aid].append(m["ndcg10"])
        per_query.append(rec)

    mean = lambda a, k: float(np.mean([r[a][k] for r in per_query]))
    summary = {a: {k: round(mean(a, k), 4) for k in ("ndcg10", "ndcg4", "mrr10", "recall20", "hit5", "n_parents")}
               for a in arms}

    gate = {a: {"reproduced": summary[a]["ndcg10"], "reference": ref,
                "match_4dp": round(summary[a]["ndcg10"], 4) == ref}
            for a, ref in RQ4_REFERENCE[split].items()}

    comparisons = [("rrf_prod", "dense"), ("convex_prod", "dense"), ("convex_prod", "rrf_prod"),
                   ("rrf_bench", "dense"), ("convex_bench", "dense"), ("convex_bench", "rrf_bench"),
                   ("bm25_prod", "bm25_bench")]
    if split == "dev":
        comparisons += [(f"convex_prod_a{a}", "rrf_prod") for a in ALPHAS if a != 0.7] + [("convex_prod", "rrf_prod")]
    stats = {}
    for cand_arm, base_arm in dict.fromkeys(comparisons):
        d, ci, p = rq4.paired_cluster_bootstrap(by_paper[base_arm], by_paper[cand_arm], n_bootstraps=n_boot, seed=42)
        stats[f"{cand_arm} - {base_arm}"] = {"diff": round(d, 4), "ci95": [round(ci[0], 4), round(ci[1], 4)],
                                             "p_raw": round(p, 4)}
    family = ["rrf_prod - dense", "convex_prod - dense", "convex_prod - rrf_prod"]
    holm = rq4.holm_bonferroni_correction([stats[k]["p_raw"] for k in family], alpha=0.05)
    for k, h in zip(family, holm):
        stats[k]["p_holm_m3"] = round(h["adj_p"], 4)
        stats[k]["family"] = "pre-declared (inferential on Test, descriptive on Dev)"

    meta = {
        "experiment_id": "EXP-RQ4P-PRODUCTION-FUSION",
        "split": split, "papers": len(by_paper["dense"]), "queries": len(per_query), "child_chunks": len(chunks),
        "tau": tau, "top_k": rq4.TOP_K, "context_budget_tokens": rq4.CONTEXT_BUDGET_TOKENS, "max_parents": rq4.MAX_PARENTS,
        "parent_trimming": "RQ4 benchmark rule (first 400 words if parent > 800 tokens); production instead windows +-200 words around the matched child",
        "bootstrap": {"B": n_boot, "seed": 42, "unit": "paper cluster", "estimand": "query-weighted mean nDCG@10 difference"},
        "queries_with_all_zero_bm25_prod": zero_bm25_prod,
        "latency_ms_p50": {k: round(float(np.percentile(v, 50)), 4) for k, v in lat.items()},
        "latency_ms_p95": {k: round(float(np.percentile(v, 95)), 4) for k, v in lat.items()},
        "latency_note": "Measured per query with time.perf_counter on one CPU core; fusion/scoring step only (embedding and expansion excluded).",
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "elapsed_s": round(time.time() - t0, 1),
    }
    out = {"metadata": meta, "reproduction_gate": gate, "summary": summary, "stats": stats}
    (OUT_DIR / f"{split}_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    with open(OUT_DIR / f"{split}_per_query.jsonl", "w", encoding="utf-8") as f:
        for r in per_query:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"gate": gate, "summary": {a: summary[a]["ndcg10"] for a in arms},
                      "family": {k: stats[k] for k in family}, "meta": meta}, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--bootstraps", type=int, default=2000)
    args = ap.parse_args()
    run(args.split, n_boot=args.bootstraps)
