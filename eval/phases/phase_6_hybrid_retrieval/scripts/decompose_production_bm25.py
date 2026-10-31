#!/usr/bin/env python3
"""
E1 follow-up (post-hoc, exploratory, Dev only): why is production BM25 weaker than benchmark BM25?

Not pre-declared. Added after E1 showed bm25_prod << bm25_bench. Separates two factors on the the retrieval experiment
Dev split (cached embeddings, same downstream processing as the retrieval experiment):
  tokens:  whitespace `lower().split()` (production)  vs  WordPiece + stopwords (benchmark)
  IDF:     per-document BM25Okapi (production)          vs  split-wide (benchmark)
For each BM25 variant it reports BM25-only and RRF (k=60, production fusion) nDCG@10.
Test is deliberately not used.

  backend/venv/Scripts/python eval/phases/phase_6_hybrid_retrieval/scripts/decompose_production_bm25.py
"""

import importlib.util
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("e1", HERE / "check_production_fusion.py")
e1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e1)
rq4 = e1.rq4


def main(tau=0.50):
    queries, chunks, pcm, _ = rq4.load_official_qasper_corpus(splits=["dev"], strategy="hierarchical")
    doc_embs = np.load(rq4.CACHE_DIR / "full_qasper_dev_hierarchical_doc_embs.npy")
    q_embs = np.load(rq4.CACHE_DIR / "full_qasper_dev_hierarchical_query_embs.npy")
    tok = rq4.AutoTokenizer.from_pretrained("intfloat/e5-small-v2")
    stop = rq4.STOPWORDS
    wp = lambda t: [x.lower() for x in tok.tokenize(t) if x.lower() not in stop]
    ws = lambda t: t.lower().split()
    ws_stop = lambda t: [x for x in t.lower().split() if x not in stop]
    bench = rq4.WordPieceBM25(chunks, tok)  # WordPiece + stopwords + split-wide IDF
    local = {name: {aid: BM25Okapi([fn(chunks[i]["text"]) for i in idx]) for aid, idx in pcm.items() if idx}
             for name, fn in (("ws_local", ws), ("ws_stop_local", ws_stop), ("wp_local", wp))}
    qfn = {"ws_local": ws, "ws_stop_local": ws_stop, "wp_local": wp}

    rq_map = {}
    for q in queries:
        aid = q["paper_arxiv_id"]
        seen, units = set(), []
        for i in pcm[aid]:
            c = chunks[i]
            if c.get("parent_id") not in seen:
                seen.add(c.get("parent_id"))
                units.append({"paper_arxiv_id": aid, "text": c.get("parent_text") or c.get("text", ""), "section": c.get("section", "")})
        rq_map[q["query_id"]] = max(1, rq4.count_relevant_chunks(units, aid, q["verbatim_evidence_quote"], q["evidence_list"], tau=tau))

    variants = ["wp_split_wide", "wp_local", "ws_stop_local", "ws_local"]
    res = {f"{k}_{v}": defaultdict(list) for v in variants for k in ("bm25", "rrf")}
    for qi, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        cand = pcm[aid]
        sims = doc_embs[cand] @ q_embs[qi]
        for v in variants:
            if v == "wp_split_wide":
                d = bench.score_query(q["question"], cand)
                sc = np.array([d.get(i, 0.0) for i in cand])
            else:
                sc = local[v][aid].get_scores(qfn[v](q["question"]))
            bm_rank = [cand[i] for i in np.argsort(sc)[::-1]][:rq4.TOP_K]
            rrf_rank = e1.rrf_prod(sims, sc, cand)[:rq4.TOP_K]
            for k, r in (("bm25", bm_rank), ("rrf", rrf_rank)):
                m = e1.metrics_for(r, chunks, aid, q["verbatim_evidence_quote"], q["evidence_list"], rq_map[q["query_id"]], tau)
                res[f"{k}_{v}"][aid].append(m["ndcg10"])
    out = {k: round(float(np.mean([x for l in v.values() for x in l])), 4) for k, v in res.items()}
    out["_note"] = "Post-hoc exploratory decomposition on RQ4 Dev (276 papers, 892 queries); nDCG@10 under RQ4 downstream rules. Dense-only reference: 0.5610."
    (e1.OUT_DIR / "dev_bm25_decomposition.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
