#!/usr/bin/env python3
"""
Phase 3: lexical (BM25), hybrid fusion and cross-encoder reranking on top of the Phase 2 dense retrievers.

Same data, chunking, relevance rule and metrics as Phase 2 (eval/phases/phase_2_retrieval/scripts/
evaluate_retrieval.py), whose functions are imported, not copied:
  chunking   : hierarchical only (children 200 tokens / overlap 40, ranked children expanded to parent sections)
  cohorts    : C-RET (QASPER, 335 papers / 567 questions) and PEERQA-PDF (107 papers / 288 questions)
  relevance  : eval_common.relevance.is_chunk_hit, tau = 0.50, R_q over the parent pool
  metrics    : the 15 Phase 2 IR metrics (nDCG@5/10, MRR@5/10, MAP@10/20, Recall@5/10/20, P@1/5/10, Hit@1/5/10)

Arms (per embedder e5, qwen, gemma, modernbert):
  dense                     cosine over children (reproduces the Phase 2 hierarchical row)
  rrf                       Reciprocal Rank Fusion of dense and BM25 (top-50 of each list, k=60; as the app's rrf mode)
  convex                    0.7 * minmax(dense) + 0.3 * minmax(BM25), min-max per query over all children
  dense+<reranker>          cross-encoder rescoring of the top-30 children of `dense`; the rest keep their order
  convex+<reranker>         the same on top of `convex`
and one embedder-independent arm:
  bm25                      BM25Okapi over children, regex tokenizer with stopwords (eval_common.relevance.tokenize_regex)

Rerankers: cross-encoder/ms-marco-MiniLM-L6-v2 ("minilm") and BAAI/bge-reranker-v2-m3 ("bgem3"),
input = (question, child text), max_length 512. Reranker scores are cached per (reranker, question, child),
so a child reranked for several embedders is scored once; latency is recorded for the calls actually made.

Outputs (eval/phases/phase_3_hybrid_reranking/artifacts/<cohort>/):
  per_query.jsonl   one row per (arm, question): metrics + top-10 ranked parent ids + latency
  summary.json      per-arm means on the common question set (questions every arm evaluated), latency, device
  REPORT.md         leaderboard and gains over dense per embedder
The run resumes: (arm, question) pairs already in per_query.jsonl are skipped. Descriptive only (no tests).

Usage (Kaggle notebook or backend/venv):
  python eval/phases/phase_3_hybrid_reranking/scripts/evaluate_hybrid_reranking.py                # both cohorts
  python .../evaluate_hybrid_reranking.py --cohort C-RET --embedders e5 --rerankers minilm --limit 2  # smoke test
"""

import argparse
import gc
import importlib.util
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
P2_PATH = ROOT / "eval" / "phases" / "phase_2_retrieval" / "scripts" / "evaluate_retrieval.py"
_spec = importlib.util.spec_from_file_location("phase2_retrieval", P2_PATH)
p2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p2)  # sets up Django and sys.path exactly as Phase 2 does

rp, rr = p2.rp, p2.rr
from eval_common.relevance import count_relevant_chunks  # noqa: E402

ARTIFACTS_DIR = ROOT / "eval" / "phases" / "phase_3_hybrid_reranking" / "artifacts"
STRATEGY = "hierarchical"
COHORTS = ["C-RET", "PEERQA-PDF"]
EMBEDDERS = ["e5", "qwen", "gemma", "modernbert"]
RERANKERS = {
    "minilm": "cross-encoder/ms-marco-MiniLM-L6-v2",
    "bgem3": "BAAI/bge-reranker-v2-m3",
}
RERANK_TOP_K = 30
RERANK_MAX_LEN = 512
TOP_IDS = 10


# ----------------------------------------------------------------------------- helpers
def order_to_scores(order: List[int], n: int) -> np.ndarray:
    """Turn a ranked list of child indices into scores for p2.rank_units_and_evaluate.
    Children missing from the list (RRF keeps only the union of two top-50 lists) rank after it."""
    s = np.full(n, -1.0)
    for rank, i in enumerate(order):
        s[i] = float(n - rank)
    return s


def top_parent_ids(order: List[int], units: List[Dict[str, Any]], k: int = TOP_IDS) -> List[str]:
    seen, out = set(), []
    for i in order:
        pid = units[i].get("parent_id")
        if pid and pid not in seen:
            seen.add(pid)
            out.append(pid)
            if len(out) == k:
                break
    return out


def device_name() -> str:
    try:
        import torch
        if torch.cuda.is_available():
            return f"cuda:{torch.cuda.get_device_name(0)}"
    except Exception:
        pass
    return "cpu"


class Reranker:
    def __init__(self, label: str, name: str):
        from sentence_transformers import CrossEncoder
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        self.label, self.name = label, name
        self.model = CrossEncoder(name, max_length=RERANK_MAX_LEN, device=dev)
        self.model.predict([("warm up", "warm up passage")] * 4, show_progress_bar=False)
        self.cache: Dict[Tuple[str, int], float] = {}

    def rerank(self, qkey: str, question: str, order: List[int], texts: List[str]) -> Tuple[List[int], Optional[float]]:
        """Rescore the top-K of `order`. Returns (new order, latency ms). The latency is reported only when
        every top-K pair was scored in this call (no cache hits), so it is the real per-question cost."""
        head, tail = order[:RERANK_TOP_K], order[RERANK_TOP_K:]
        todo = [i for i in head if (qkey, i) not in self.cache]
        ms: Optional[float] = None
        if todo:
            t0 = time.perf_counter()
            scores = self.model.predict([(question, texts[i]) for i in todo], batch_size=32,
                                        show_progress_bar=False)
            ms = (time.perf_counter() - t0) * 1000 if len(todo) == len(head) else None
            for i, s in zip(todo, scores):
                self.cache[(qkey, i)] = float(s)
        # stable: equal scores keep the base order
        head = sorted(head, key=lambda i: -self.cache[(qkey, i)])
        return head + tail, ms


def load_done(path: Path) -> Tuple[List[Dict[str, Any]], set]:
    rows, done = [], set()
    if path.exists():
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                rows.append(r)
                done.add((r["arm"], r["paper_id"], r["question_id"]))
    return rows, done


def pct(xs: List[float], q: float) -> Optional[float]:
    return round(float(np.percentile(xs, q)), 2) if xs else None


# ----------------------------------------------------------------------------- summary / report
def summarise(cohort: str, rows: List[Dict[str, Any]], meta: Dict[str, Any]) -> Dict[str, Any]:
    by_arm: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_arm[r["arm"]].append(r)
    keysets = [{(r["paper_id"], r["question_id"]) for r in rs} for rs in by_arm.values()]
    common = set.intersection(*keysets) if keysets else set()
    arms = {}
    for arm, rs in sorted(by_arm.items()):
        rc = [r for r in rs if (r["paper_id"], r["question_id"]) in common]
        lat_rank = [r["rank_ms"] for r in rs if r.get("rank_ms") is not None]
        lat_rr = [r["rerank_ms"] for r in rs if r.get("rerank_ms") is not None]
        arms[arm] = {
            "embedder": rs[0]["embedder"], "base": rs[0]["base"], "reranker": rs[0]["reranker"],
            "n_evaluated": len(rs), "n_common": len(rc),
            "means": {k: round(float(np.mean([r["metrics"][k] for r in rs])), 4) for k in p2.IR_METRIC_KEYS},
            "common_means": {k: round(float(np.mean([r["metrics"][k] for r in rc])), 4) if rc else None
                             for k in p2.IR_METRIC_KEYS},
            "rank_ms_p50": pct(lat_rank, 50), "rank_ms_p95": pct(lat_rank, 95),
            "rerank_ms_p50": pct(lat_rr, 50), "rerank_ms_p95": pct(lat_rr, 95),
            "rerank_latency_samples": len(lat_rr),
        }
    return {**meta, "cohort": cohort, "n_common_questions": len(common), "arms": arms}


def write_report(summary: Dict[str, Any], path: Path) -> None:
    arms = summary["arms"]
    use = "common_means" if summary["n_common_questions"] else "means"
    ordered = sorted(arms.items(), key=lambda kv: -(kv[1][use]["ndcg_10"] or 0))
    L = [f"# Phase 3: hybrid retrieval and reranking ({summary['cohort']})", "",
         f"Hierarchical chunking. {summary['n_common_questions']} questions evaluated by every arm (common set). "
         f"Device: {summary.get('device')}. Reranking rescoring the top {RERANK_TOP_K} children. "
         "Reranker latency is a property of the reranker, measured only on calls that scored all top-K "
         "pairs fresh; arms whose pairs were already scored for another arm show –.", "",
         "| Arm | nDCG@10 | MRR@10 | Recall@10 | P@5 | Hit@5 | n | rank p50 ms | rerank p50 / p95 ms |",
         "|---|---|---|---|---|---|---|---|---|"]
    for arm, a in ordered:
        m = a[use]
        rr_lat = f"{a['rerank_ms_p50']} / {a['rerank_ms_p95']}" if a["rerank_ms_p50"] is not None else "–"
        L.append(f"| `{arm}` | **{m['ndcg_10']:.4f}** | {m['mrr_10']:.4f} | {m['recall_10']:.4f} | "
                 f"{m['precision_5']:.4f} | {m['hit_5']:.4f} | {a['n_common'] if use == 'common_means' else a['n_evaluated']} | "
                 f"{a['rank_ms_p50']} | {rr_lat} |")
    L += ["", "## Change in nDCG@10 relative to dense, per embedder", "",
          "| Embedder | dense | " + " | ".join(["rrf", "convex"] + [f"{b}+{r}" for b in ("dense", "convex")
                                                                for r in summary["rerankers"]]) + " |",
          "|---|---|" + "---|" * (2 + 2 * len(summary["rerankers"]))]
    for emb in summary["embedders"]:
        base = arms.get(f"{emb}:dense")
        if not base:
            continue
        b = base[use]["ndcg_10"]
        cells = []
        for suffix in ["rrf", "convex"] + [f"{x}+{r}" for x in ("dense", "convex") for r in summary["rerankers"]]:
            a = arms.get(f"{emb}:{suffix}")
            cells.append(f"{a[use]['ndcg_10'] - b:+.4f}" if a else "–")
        L.append(f"| {emb} | {b:.4f} | " + " | ".join(cells) + " |")
    if "bm25" in arms:
        L += ["", f"BM25 alone (regex tokenizer): nDCG@10 {arms['bm25'][use]['ndcg_10']:.4f}."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------- main loop
def run_cohort(cohort: str, embedders: List[str], rerankers: List[str], limit: Optional[int],
               seed: Optional[int]) -> Dict[str, Any]:
    print(f"\n{'=' * 70}\nPhase 3 hybrid + reranking: cohort [{cohort}]\n{'=' * 70}", flush=True)
    groups = rr.group_items(rr.load_cohort(cohort))
    papers = sorted(groups)
    if limit:
        if seed is not None:
            rng = np.random.RandomState(seed)
            papers = [papers[i] for i in sorted(rng.choice(len(papers), size=min(limit, len(papers)), replace=False))]
        else:
            papers = papers[:limit]
    if cohort == "PEERQA-PDF":
        p2.report_peerqa_pdf_coverage(papers)

    out_dir = ARTIFACTS_DIR / (cohort.lower().replace("-", "_") + (f"_smoke_{limit}" if limit else ""))
    out_dir.mkdir(parents=True, exist_ok=True)
    pq_path = out_dir / "per_query.jsonl"
    rows, done = load_done(pq_path)
    print(f"{len(papers)} papers, {sum(len(groups[p]) for p in papers)} questions; "
          f"{len(done)} (arm, question) rows already done", flush=True)

    # sections, units and R_q, as in Phase 2
    units: Dict[str, List[Dict[str, Any]]] = {}
    pools: Dict[str, List[Dict[str, Any]]] = {}
    sources: Dict[str, int] = defaultdict(int)
    for pid in papers:
        try:
            secs, src = p2.load_sections_for_cohort(cohort, pid)
            u = p2.build_units_by_strategy(secs, STRATEGY, pid) if secs else []
        except Exception as e:  # noqa: BLE001
            print(f"  skip {pid}: {type(e).__name__}: {e}", flush=True)
            continue
        cp = p2.get_candidate_pool(u, STRATEGY) if u else []
        if u and cp:
            units[pid], pools[pid] = u, cp
            sources[src] += 1
    papers = [p for p in papers if p in units]
    print(f"Units ready for {len(papers)} papers. Section sources: {dict(sources)}", flush=True)
    rq: Dict[Tuple[str, str], int] = {}
    for pid in papers:
        for i, it in enumerate(groups[pid]):
            rq[(pid, p2.make_qid(pid, i, it))] = int(count_relevant_chunks(
                pools[pid], pid, "", it.get("retrieval_evidence", []), tau=p2.TAU))

    tag = cohort.lower().replace("-", "_")
    rer = {lab: Reranker(lab, RERANKERS[lab]) for lab in rerankers}
    fout = open(pq_path, "a", encoding="utf-8")

    def emit(arm: str, emb: str, base: str, reranker: Optional[str], pid: str, qid: str,
             order: List[int], rank_ms: Optional[float], rerank_ms: Optional[float]) -> None:
        if (arm, pid, qid) in done:
            return
        m = p2.rank_units_and_evaluate(STRATEGY, units[pid], order_to_scores(order, len(units[pid])),
                                       pid, evidence_of[(pid, qid)], rq[(pid, qid)])
        if m is None:
            return
        row = {"cohort": cohort, "paper_id": pid, "question_id": qid, "arm": arm, "embedder": emb,
               "base": base, "reranker": reranker, "metrics": m,
               "top_parent_ids": top_parent_ids(order, units[pid]),
               "rank_ms": None if rank_ms is None else round(rank_ms, 3),
               "rerank_ms": None if rerank_ms is None else round(rerank_ms, 2)}
        rows.append(row)
        done.add((arm, pid, qid))
        fout.write(json.dumps(row) + "\n")

    evidence_of = {(pid, p2.make_qid(pid, i, it)): it.get("retrieval_evidence", [])
                   for pid in papers for i, it in enumerate(groups[pid])}

    # embedder-independent BM25 arm
    for pid in papers:
        texts = [u["text"] for u in units[pid]]
        for i, it in enumerate(groups[pid]):
            qid = p2.make_qid(pid, i, it)
            t0 = time.perf_counter()
            sp = rp.bm25_scores(texts, it["question"], "regex")
            order = [int(x) for x in np.argsort(-sp, kind="stable")]
            emit("bm25", "-", "bm25", None, pid, qid, order, (time.perf_counter() - t0) * 1000, None)
    fout.flush()

    for emb in embedders:
        model_name = p2.MODEL_MAP[emb]
        arm_names = [f"{emb}:dense", f"{emb}:rrf", f"{emb}:convex"] + \
                    [f"{emb}:{b}+{r}" for b in ("dense", "convex") for r in rerankers]
        if all((a, pid, p2.make_qid(pid, i, it)) in done for a in arm_names
               for pid in papers for i, it in enumerate(groups[pid])):
            print(f"--- {emb}: already complete, skipped", flush=True)
            continue
        print(f"--- Embedder {emb} ({model_name}) ---", flush=True)
        t_emb = time.time()
        for pid in papers:
            us = units[pid]
            texts = [u["text"] for u in us]
            h = p2.hashlib.md5("\x00".join(texts).encode()).hexdigest()[:8]
            um = p2.normalize_l2(rp.cached_embed(model_name, texts, False,
                                                 f"{tag}_{p2.safe_pid(pid)}_{STRATEGY}_{emb}_{h}"))
            items = groups[pid]
            questions = [it["question"] for it in items]
            qh = p2.hashlib.md5("\x00".join(questions).encode()).hexdigest()[:8]
            qv = p2.normalize_l2(rp.cached_embed(model_name, questions, True, f"{tag}_{p2.safe_pid(pid)}_{emb}_q{qh}"))
            for i, (it, q) in enumerate(zip(items, qv)):
                qid = p2.make_qid(pid, i, it)
                if rq[(pid, qid)] <= 0:
                    continue
                t0 = time.perf_counter()
                dense = um @ q
                d_order = [int(x) for x in np.argsort(-dense, kind="stable")]
                t_dense = (time.perf_counter() - t0) * 1000
                t0 = time.perf_counter()
                sp = rp.bm25_scores(texts, it["question"], "regex")
                t_bm25 = (time.perf_counter() - t0) * 1000
                t0 = time.perf_counter()
                r_order = rp.rrf(dense, sp)
                t_rrf = (time.perf_counter() - t0) * 1000
                t0 = time.perf_counter()
                c_order = rp.convex(dense, sp)
                t_cvx = (time.perf_counter() - t0) * 1000
                emit(f"{emb}:dense", emb, "dense", None, pid, qid, d_order, t_dense, None)
                emit(f"{emb}:rrf", emb, "rrf", None, pid, qid, r_order, t_dense + t_bm25 + t_rrf, None)
                emit(f"{emb}:convex", emb, "convex", None, pid, qid, c_order, t_dense + t_bm25 + t_cvx, None)
                qkey = f"{pid}|{qid}"
                for lab, model in rer.items():
                    for base, order, t_base in (("dense", d_order, t_dense),
                                                ("convex", c_order, t_dense + t_bm25 + t_cvx)):
                        arm = f"{emb}:{base}+{lab}"
                        if (arm, pid, qid) in done:
                            continue
                        new_order, ms = model.rerank(qkey, it["question"], order, texts)
                        emit(arm, emb, base, lab, pid, qid, new_order, t_base, ms)
            fout.flush()
        print(f"    {emb} done in {time.time() - t_emb:.0f} s", flush=True)
        rp._MODELS.pop(model_name, None)
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        meta = {"phase": "phase_3_hybrid_reranking", "strategy": STRATEGY, "embedders": embedders,
                "rerankers": rerankers, "reranker_models": {r: RERANKERS[r] for r in rerankers},
                "rerank_top_k": RERANK_TOP_K, "convex_alpha": rp.CONVEX_ALPHA, "rrf_k": rp.RRF_K,
                "bm25_tokenizer": "regex", "tau": p2.TAU, "device": device_name(),
                "n_papers": len(papers), "section_sources": dict(sources)}
        summary = summarise(cohort, rows, meta)
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        write_report(summary, out_dir / "REPORT.md")
    fout.close()
    meta = {"phase": "phase_3_hybrid_reranking", "strategy": STRATEGY, "embedders": embedders,
            "rerankers": rerankers, "reranker_models": {r: RERANKERS[r] for r in rerankers},
            "rerank_top_k": RERANK_TOP_K, "convex_alpha": rp.CONVEX_ALPHA, "rrf_k": rp.RRF_K,
            "bm25_tokenizer": "regex", "tau": p2.TAU, "device": device_name(),
            "n_papers": len(papers), "section_sources": dict(sources)}
    summary = summarise(cohort, rows, meta)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_report(summary, out_dir / "REPORT.md")
    best = max(summary["arms"].items(), key=lambda kv: kv[1]["common_means"]["ndcg_10"] or 0)
    print(f"Done {cohort}: {len(summary['arms'])} arms, {summary['n_common_questions']} common questions; "
          f"best nDCG@10 {best[0]} = {best[1]['common_means']['ndcg_10']}", flush=True)
    del rer
    gc.collect()
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--cohort", choices=COHORTS + ["all"], default="all")
    ap.add_argument("--embedders", default=",".join(EMBEDDERS))
    ap.add_argument("--rerankers", default=",".join(RERANKERS))
    ap.add_argument("--skip-rerank", action="store_true")
    ap.add_argument("--limit", type=int, help="papers per cohort (smoke test)")
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    embedders = [e.strip() for e in a.embedders.split(",") if e.strip()]
    for e in embedders:
        if e not in p2.MODEL_MAP:
            ap.error(f"unknown embedder {e!r}; choose from {sorted(p2.MODEL_MAP)}")
    rerankers = [] if a.skip_rerank else [r.strip() for r in a.rerankers.split(",") if r.strip()]
    for r in rerankers:
        if r not in RERANKERS:
            ap.error(f"unknown reranker {r!r}; choose from {sorted(RERANKERS)}")
    cohorts = COHORTS if a.cohort == "all" else [a.cohort]
    combined = {c: run_cohort(c, embedders, rerankers, a.limit, a.seed) for c in cohorts}
    name = "summary.json" if not a.limit else f"summary_smoke_{a.limit}.json"
    (ARTIFACTS_DIR / name).write_text(json.dumps(combined, indent=2), encoding="utf-8")
    print(f"\nPhase 3 complete -> {ARTIFACTS_DIR / name}")


if __name__ == "__main__":
    main()
