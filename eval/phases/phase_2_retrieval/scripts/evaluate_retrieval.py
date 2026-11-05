"""
Phase 2: Retrieval Evaluation (Combined Chunking & Dense Embedding Benchmark).

Evaluates the combinatorial matrix of chunking strategies and dense embedding models
across standard Information Retrieval (IR) metrics on QASPER and PeerQA datasets.

Combinations:
  Chunkers:  {hierarchical, section_overlap, fixed_size}
  Embedders: {e5-small-v2, Qwen3-Embedding-0.6B, embeddinggemma-300m, snowflake-arctic-embed-s, modernbert-embed-base}
  Datasets:  QASPER (C-RET / C-RET-150) and PeerQA (PEERQA-PDF / PEERQA-TEXT)
             `--dataset all` runs C-RET and PEERQA-PDF only; use --cohort for the others.

Metrics (Pure Retrieval Quality):
  - MRR:       MRR@5, MRR@10
  - Recall:    Recall@5, Recall@10, Recall@20
  - Precision: Precision@1, Precision@5, Precision@10
  - NDCG:      nDCG@5, nDCG@10
  - MAP:       MAP@10, MAP@20
  - Hit@k:     Hit@1, Hit@5, Hit@10
  - Efficiency: Indexing throughput (chunks/s) per (chunker, model), query latency (P50/P95 ms), memory usage.

Usage:
  python evaluate_retrieval.py [--dataset {qasper,peerqa,all}] [--cohort COHORT]
                               [--chunkers CHUNKERS] [--models MODELS]
                               [--limit N] [--seed S]

Notes:
  - Indexing throughput is measured per (chunker, model) with a warm passage-path call
    before the timed window, so cold CUDA/kernel-launch overhead is excluded. A failed
    benchmark is reported as "—" (None), never as 0.
  - Leaderboard, chunker table and model table are all computed on the intersection of
    (paper_id, question_id) pairs scored by ALL active chunkers ("common set"), so every
    row reflects the same questions. Raw per-combination means are kept as `means`.
  - hierarchical retrieves at parent-section granularity while flat chunkers retrieve at
    chunk granularity; P@k, MAP and nDCG are therefore on different units. The report
    labels granularity and also names the best flat-chunk combination.
  - The combined summary.json is merged with any previous run so a single-cohort
    invocation does not erase results from other cohorts.
"""

import argparse
import gc
import hashlib
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

# Sanity-check path resolution at import time (never stripped under python -O)
if not (BACKEND / "apps").exists():
    raise RuntimeError(
        f"BACKEND path looks wrong: {BACKEND}. "
        "Expected evaluate_retrieval.py to live at eval/phases/phase_2_retrieval/scripts/."
    )

from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402
from eval_common.relevance import count_relevant_chunks, is_chunk_hit  # noqa: E402

rp.setup_django()
from apps.documents.services.chunkers import chunk_fixed_size, chunk_hierarchical  # noqa: E402
from apps.documents.services.chunking_utils import chunk_sections, extract_sections_from_pdf  # noqa: E402

ARTIFACTS_DIR = ROOT / "eval" / "phases" / "phase_2_retrieval" / "artifacts"

TAU = 0.50
CHUNKERS = ["hierarchical", "section_overlap", "fixed_size"]
MODEL_MAP = {
    "e5": "intfloat/e5-small-v2",
    # "minilm": "sentence-transformers/all-MiniLM-L6-v2",
    # "bge": "BAAI/bge-small-en-v1.5",
    "qwen": "Qwen/Qwen3-Embedding-0.6B",
    "gemma": "google/embeddinggemma-300m",
    "arctic": "Snowflake/snowflake-arctic-embed-s",
    "modernbert": "nomic-ai/modernbert-embed-base",
}
DEFAULT_MODELS = list(MODEL_MAP.values())

IR_METRIC_KEYS = [
    "ndcg_10", "ndcg_5",
    "mrr_10", "mrr_5",
    "map_10", "map_20",
    "recall_5", "recall_10", "recall_20",
    "precision_1", "precision_5", "precision_10",
    "hit_1", "hit_5", "hit_10",
]

_QASPER_ALL_SPLITS = ["train", "dev", "test"]


# -----------------------------------------------------------------------------
# Small helpers
# -----------------------------------------------------------------------------
def normalize_l2(x: np.ndarray) -> np.ndarray:
    """Guarantee strictly unit L2 norm so dot-product is exact cosine similarity."""
    x = np.asarray(x, dtype=np.float32)
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norms, 1e-12)


def make_qid(pid: str, idx: int, item: Dict[str, Any]) -> str:
    """Unique, stable question key: survives None ids and duplicate ids within a paper."""
    base = item.get("question_id")
    return f"{base if base is not None else pid}|{idx}"


def safe_pid(pid: str) -> str:
    return pid.replace("/", "__").replace("\\", "__")


def write_checkpoint(summary: Dict[str, Any], rows: List[Dict[str, Any]], out_dir: Optional[Path]) -> None:
    if not out_dir:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    with open(out_dir / "per_query.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")


# -----------------------------------------------------------------------------
# Metric Calculations (Pure IR)
# -----------------------------------------------------------------------------
def compute_dcg(relevances: Sequence[int], k: int = 10) -> float:
    return sum(float(rel) / np.log2(idx + 2) for idx, rel in enumerate(relevances[:k]) if rel > 0)


def compute_ndcg(relevances: Sequence[int], total_relevant: int, k: int = 10) -> float:
    if total_relevant <= 0:
        return 0.0
    dcg = compute_dcg(relevances, k=k)
    ideal_k = min(total_relevant, k)
    idcg = sum(1.0 / np.log2(idx + 2) for idx in range(ideal_k))
    return float(dcg / idcg) if idcg > 0.0 else 0.0


def compute_mrr(relevances: Sequence[int], k: int = 10) -> float:
    for idx, rel in enumerate(relevances[:k]):
        if rel > 0:
            return 1.0 / (idx + 1)
    return 0.0


def compute_recall(relevances: Sequence[int], total_relevant: int, k: int = 10) -> float:
    if total_relevant <= 0:
        return 0.0
    return float(sum(1 for r in relevances[:k] if r > 0) / total_relevant)


def compute_precision(relevances: Sequence[int], k: int = 10) -> float:
    if k <= 0:
        return 0.0
    return float(sum(1 for r in relevances[:k] if r > 0) / k)


def compute_average_precision(relevances: Sequence[int], total_relevant: int, k: int = 10) -> float:
    if total_relevant <= 0:
        return 0.0
    hits = 0
    prec_sum = 0.0
    for idx, rel in enumerate(relevances[:k]):
        if rel > 0:
            hits += 1
            prec_sum += hits / (idx + 1)
    denom = min(total_relevant, k)
    return float(prec_sum / denom) if denom > 0 else 0.0


def compute_hit_at_k(relevances: Sequence[int], k: int = 5) -> int:
    return 1 if any(r > 0 for r in relevances[:k]) else 0


def compute_all_ir_metrics(relevances: Sequence[int], total_relevant: int) -> Dict[str, float]:
    return {
        "ndcg_10": round(compute_ndcg(relevances, total_relevant, k=10), 4),
        "ndcg_5":  round(compute_ndcg(relevances, total_relevant, k=5), 4),
        "mrr_10":  round(compute_mrr(relevances, k=10), 4),
        "mrr_5":   round(compute_mrr(relevances, k=5), 4),
        "map_10":  round(compute_average_precision(relevances, total_relevant, k=10), 4),
        "map_20":  round(compute_average_precision(relevances, total_relevant, k=20), 4),
        "recall_5":    round(compute_recall(relevances, total_relevant, k=5), 4),
        "recall_10":   round(compute_recall(relevances, total_relevant, k=10), 4),
        "recall_20":   round(compute_recall(relevances, total_relevant, k=20), 4),
        "precision_1":  round(compute_precision(relevances, k=1), 4),
        "precision_5":  round(compute_precision(relevances, k=5), 4),
        "precision_10": round(compute_precision(relevances, k=10), 4),
        "hit_1":  compute_hit_at_k(relevances, k=1),
        "hit_5":  compute_hit_at_k(relevances, k=5),
        "hit_10": compute_hit_at_k(relevances, k=10),
    }


# -----------------------------------------------------------------------------
# Efficiency helpers
# -----------------------------------------------------------------------------
def bench_index(model_name: str, texts: List[str], n: int = 100) -> Optional[float]:
    """Passage-encoding throughput (chunks/s) on up to n texts, after a warm passage-path call.

    Returns None (not 0.0) when there is nothing to time or the benchmark fails,
    so a failure can never masquerade as a measured number.
    """
    s = texts[:n]
    if not s:
        return None
    try:
        rp.embed(model_name, s[:8], is_query=False, batch_size=8)   # warm passage path
        t0 = time.perf_counter()
        rp.embed(model_name, s, is_query=False, batch_size=32)
        return round(len(s) / max(time.perf_counter() - t0, 1e-4), 1)
    except Exception as e:
        print(f"    Warning: index throughput benchmark failed for {model_name}: {type(e).__name__}: {e}",
              flush=True)
        return None


# -----------------------------------------------------------------------------
# Section & Document Loading
# -----------------------------------------------------------------------------
_QASPER_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_qasper_split(split: str) -> Dict[str, Any]:
    if split not in _QASPER_CACHE:
        path = ROOT / "eval" / "data" / "qasper_official" / f"qasper-{split}-v0.3.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _QASPER_CACHE[split] = json.load(f)
        else:
            _QASPER_CACHE[split] = {}
    return _QASPER_CACHE[split]


def load_qasper_sections(paper_id: str, split: str = "train") -> tuple:
    """Return (sections, source_tag) where source_tag is 'pdf' or 'json:<split>'."""
    # 1. Try local PDF (all dirs)
    for pdf_dir in ("train_reservoir", "dev", "test"):
        p = ROOT / "eval" / "pdfs" / pdf_dir / f"{paper_id}.pdf"
        if p.exists() and p.stat().st_size > 1000:
            try:
                sec = extract_sections_from_pdf(str(p))
                if sec:
                    return sec, "pdf"
            except Exception:
                pass

    # 2. JSON fallback: hinted split first, then the remaining two
    for s in [split] + [x for x in _QASPER_ALL_SPLITS if x != split]:
        pdata = _load_qasper_split(s).get(paper_id, {})
        full_text = pdata.get("full_text", [])
        if full_text:
            secs = []
            for sec in full_text:
                text = "\n\n".join(sec.get("paragraphs", []))
                if not text.strip():
                    continue
                name = sec.get("section_name", "") or "Body"
                secs.append({"heading": name, "title": name, "text": text})
            if secs:
                return secs, f"json:{s}"

    return [], "not_found"


def load_peerqa_sections(paper_id: str) -> tuple:
    """Return (sections, source_tag)."""
    pdf = ROOT / "eval" / "pdfs" / "peerqa" / (paper_id.replace("/", "__") + ".pdf")
    if pdf.exists() and pdf.stat().st_size > 1000:
        try:
            sec = extract_sections_from_pdf(str(pdf))
            if sec:
                return sec, "pdf"
        except Exception:
            pass
    return rr.peerqa_text_sections(paper_id), "papers_jsonl"


def load_sections_for_cohort(cohort: str, paper_id: str) -> tuple:
    """Return (sections, source_tag)."""
    if "PEERQA" in cohort:
        return load_peerqa_sections(paper_id)
    split = "dev" if "DEV" in cohort else "train"
    return load_qasper_sections(paper_id, split=split)


# -----------------------------------------------------------------------------
# Common-key intersection (comparable averages)
# -----------------------------------------------------------------------------
def common_question_keys(per_query_rows: List[Dict[str, Any]], chunkers: List[str]) -> frozenset:
    """(paper_id, question_id) pairs evaluated by ALL active chunkers.

    Intersects only over chunkers that actually produced rows, so one failed
    chunker does not blank the comparison tables.
    """
    by: Dict[str, set] = defaultdict(set)
    for r in per_query_rows:
        by[r["chunker"]].add((r["paper_id"], r["question_id"]))
    active = [c for c in chunkers if by.get(c)]
    if not active:
        return frozenset()
    return frozenset(set.intersection(*(by[c] for c in active)))


# -----------------------------------------------------------------------------
# Unit Building & Ranking Helpers
# -----------------------------------------------------------------------------
def build_units_by_strategy(
    sections: List[Dict[str, Any]], strategy: str, paper_id: str
) -> List[Dict[str, Any]]:
    if strategy == "hierarchical":
        return chunk_hierarchical(sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id)
    if strategy == "section_overlap":
        chunks = chunk_sections(sections, strategy="section_overlap", max_tokens=400, overlap=80)
        for idx, c in enumerate(chunks):
            c.setdefault("paper_arxiv_id", paper_id)
            c.setdefault("chunk_id", f"{paper_id}_section_overlap_{idx:03d}")
        return chunks
    if strategy == "fixed_size":
        return chunk_fixed_size(sections, max_tokens=400, paper_id=paper_id)
    raise ValueError(f"Unknown chunking strategy: {strategy!r}")


def get_candidate_pool(units: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    """Candidate pool over which total relevant chunks R_q is counted."""
    if strategy != "hierarchical":
        return units
    seen, out = set(), []
    for u in units:
        pid = u.get("parent_id")
        if pid and pid not in seen:
            seen.add(pid)
            out.append({
                "text": u.get("parent_text") or u["text"],
                "parent_id": pid,
                "paper_arxiv_id": u.get("paper_arxiv_id", ""),
            })
    return out


def rank_units_and_evaluate(
    strategy: str,
    units: List[Dict[str, Any]],
    scores: np.ndarray,
    paper_id: str,
    evidence: List[str],
    r_q: int,
    tau: float = TAU,
) -> Optional[Dict[str, Any]]:
    """Rank units and return IR metrics using the pre-computed r_q (None if r_q <= 0)."""
    if r_q <= 0:
        return None
    K = 20
    # stable sort: ties (overlap regions, boilerplate) resolve in unit order, reproducibly
    ranked = np.argsort(-scores, kind="stable")
    if strategy == "hierarchical":
        # Small-to-big retrieval: expand child hits to unique parent sections in rank order
        seen, items = set(), []
        for idx in ranked:
            pid = units[idx].get("parent_id")
            if pid and pid not in seen:
                seen.add(pid)
                items.append({
                    "text": units[idx].get("parent_text") or units[idx]["text"],
                    "parent_id": pid,
                    "paper_arxiv_id": units[idx].get("paper_arxiv_id", ""),
                })
                if len(items) == K:
                    break
    else:
        items = [units[i] for i in ranked[:K]]
    relevances = [1 if is_chunk_hit(u, paper_id, "", evidence, tau=tau) else 0 for u in items]
    metrics = compute_all_ir_metrics(relevances, r_q)
    metrics["r_q"] = int(r_q)
    metrics["rel_gt_rq"] = int(sum(relevances) > r_q)
    return metrics


# -----------------------------------------------------------------------------
# Main Evaluation Engine
# -----------------------------------------------------------------------------
def run_dataset_retrieval_benchmark(
    cohort_name: str,
    chunkers: List[str],
    models: List[str],
    limit: Optional[int] = None,
    seed: Optional[int] = None,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    print(f"\n{'='*70}\nStarting Phase 2 Retrieval Evaluation: Cohort [{cohort_name}]\n{'='*70}", flush=True)

    cohort = rr.load_cohort(cohort_name)
    groups = rr.group_items(cohort)
    all_papers = sorted(groups)

    # Paper sampling: seeded random sample if --seed given, else head (alphabetical)
    if limit and seed is not None:
        rng = np.random.RandomState(seed)
        chosen = sorted(rng.choice(len(all_papers), size=min(limit, len(all_papers)), replace=False))
        papers = [all_papers[i] for i in chosen]
    elif limit:
        papers = all_papers[:limit]
    else:
        papers = all_papers

    print(f"Loaded cohort {cohort_name}: {len(papers)} papers (limit={limit}, seed={seed}), "
          f"{sum(len(groups[p]) for p in papers)} questions", flush=True)

    tag = cohort_name.lower().replace("-", "_")

    per_query_rows: List[Dict[str, Any]] = []
    t_start = time.time()
    section_sources: Dict[str, str] = {}
    failures: List[Dict[str, Any]] = []

    # Pre-extract sections for all papers in cohort
    print("Pre-loading sections...", flush=True)
    paper_sections: Dict[str, List[Dict[str, Any]]] = {}
    for pid in papers:
        try:
            secs, src = load_sections_for_cohort(cohort_name, pid)
        except Exception as e:
            failures.append({"paper_id": pid, "error": f"Section load error: {type(e).__name__}: {str(e)[:200]}"})
            continue
        if not secs:
            failures.append({"paper_id": pid, "error": "No sections loaded"})
            continue
        paper_sections[pid] = secs
        section_sources[pid] = src

    valid_papers = [p for p in papers if p in paper_sections]
    src_counts: Dict[str, int] = defaultdict(int)
    for s in section_sources.values():
        src_counts[s] += 1
    print(f"Sections ready for {len(valid_papers)}/{len(papers)} papers. Sources: {dict(src_counts)}", flush=True)
    if len(src_counts) > 1:
        print("Warning: mixed section sources in one run; evidence matching may differ per paper.", flush=True)

    summary: Dict[str, Any] = {
        "cohort": cohort_name,
        "n_papers": len(valid_papers),
        "n_questions": sum(len(groups[p]) for p in valid_papers),
        "n_papers_requested": len(papers),
        "chunkers": chunkers,
        "models": models,
        "section_sources": section_sources,
        "section_source_counts": dict(src_counts),
        "combinations": {},
        "failures": failures,
    }

    if not valid_papers:
        summary["elapsed_s"] = round(time.time() - t_start, 1)
        write_checkpoint(summary, per_query_rows, out_dir)
        return summary

    # Pre-build units per chunker
    chunker_units: Dict[str, Dict[str, List[Dict[str, Any]]]] = {st: {} for st in chunkers}
    chunker_cands: Dict[str, Dict[str, List[Dict[str, Any]]]] = {st: {} for st in chunkers}
    for st in chunkers:
        for pid in valid_papers:
            try:
                u = build_units_by_strategy(paper_sections[pid], st, pid)
            except Exception as e:
                failures.append({"paper_id": pid, "strategy": st,
                                 "error": f"{type(e).__name__}: {str(e)[:200]}"})
                continue
            if u:
                cp = get_candidate_pool(u, st)
                if cp:
                    chunker_units[st][pid] = u
                    chunker_cands[st][pid] = cp
                else:
                    failures.append({"paper_id": pid, "strategy": st,
                                     "error": "Candidate pool empty (hierarchical units missing parent_id?)"})
            else:
                failures.append({"paper_id": pid, "strategy": st, "error": "No units built"})

    # Pre-compute r_q per (chunker, paper, question), once, shared across models.
    # A bad evidence entry degrades to r_q=0 (skipped) + a failure record instead of killing the run.
    precomp_rq: Dict[tuple, int] = {}
    for st in chunkers:
        for pid in valid_papers:
            cand_pool = chunker_cands[st].get(pid, [])
            for i, it in enumerate(groups[pid]):
                qid = make_qid(pid, i, it)
                try:
                    precomp_rq[(st, pid, qid)] = int(count_relevant_chunks(
                        cand_pool, pid, "", it.get("retrieval_evidence", []), tau=TAU
                    ))
                except Exception as e:
                    precomp_rq[(st, pid, qid)] = 0
                    failures.append({"paper_id": pid, "strategy": st, "question_id": qid,
                                     "error": f"r_q computation failed: {type(e).__name__}: {str(e)[:150]}"})

    # Evaluate per model
    for model_name in models:
        m_short = [k for k, v in MODEL_MAP.items() if v == model_name]
        m_label = m_short[0] if m_short else model_name.split("/")[-1]
        print(f"\n--- Model: {model_name} ({m_label}) ---", flush=True)

        try:
            rp.get_model(model_name)
        except Exception as e:
            print(f"Error loading model {model_name}: {e}\nSkipping this model.", flush=True)
            failures.append({"model": model_name, "error": f"Failed to load: {e}"})
            continue

        with rr.MemorySampler() as mem:
            # Warm-up: exclude CUDA init from latency numbers
            try:
                rp.embed(model_name, ["warmup text for retriever"], is_query=True, batch_size=1)
            except Exception as e:
                print(f"Warning: model warm-up error: {e}", flush=True)

            # Query latency: uncached single-query embeds
            qs = [it["question"] for p in valid_papers for it in groups[p]][:200]
            model_latencies: List[float] = []
            for q in qs:
                try:
                    t0 = time.perf_counter()
                    rp.embed(model_name, [q], is_query=True, batch_size=1)
                    model_latencies.append((time.perf_counter() - t0) * 1000)
                except Exception:
                    pass

            for st in chunkers:
                combo_key = f"{st}|{m_label}"
                print(f"  > Evaluating combination: [{combo_key}]", flush=True)
                combo_metrics: Dict[str, List[float]] = defaultdict(list)
                skipped = 0            # no relevant unit in pool (r_q == 0)
                skipped_no_units = 0   # paper had no usable units for this chunker

                # Per-chunker indexing throughput
                sample_texts = [
                    u["text"]
                    for p in valid_papers[:5]
                    for u in chunker_units[st].get(p, [])
                ]
                combo_index_tput = bench_index(model_name, sample_texts)
                if combo_index_tput is None:
                    failures.append({"combo": combo_key, "error": "index throughput benchmark unavailable"})

                try:
                    for pid in valid_papers:
                        units = chunker_units[st].get(pid)
                        cand_pool = chunker_cands[st].get(pid)
                        if not units or not cand_pool:
                            skipped_no_units += len(groups[pid])
                            continue

                        texts = [u["text"] for u in units]
                        h = hashlib.md5("\x00".join(texts).encode()).hexdigest()[:8]
                        um = rp.cached_embed(
                            model_name, texts, False,
                            f"{tag}_{safe_pid(pid)}_{st}_{m_label}_{h}"
                        )
                        if len(um) != len(units):
                            raise RuntimeError(
                                f"Embedding count mismatch: {len(um)} vs {len(units)} units"
                            )
                        um = normalize_l2(um)

                        items = groups[pid]
                        questions = [it["question"] for it in items]

                        qh = hashlib.md5("\x00".join(questions).encode()).hexdigest()[:8]
                        qv = rp.cached_embed(
                            model_name, questions, True,
                            f"{tag}_{safe_pid(pid)}_{m_label}_q{qh}"
                        )
                        if len(qv) != len(questions):
                            raise RuntimeError(
                                f"Question embedding count mismatch: {len(qv)} vs {len(questions)}"
                            )
                        qv = normalize_l2(qv)

                        for i, (it, q) in enumerate(zip(items, qv)):
                            qid = make_qid(pid, i, it)
                            r_q = precomp_rq.get((st, pid, qid), 0)
                            ir_m = rank_units_and_evaluate(
                                strategy=st,
                                units=units,
                                scores=um @ q,
                                paper_id=pid,
                                evidence=it.get("retrieval_evidence", []),
                                r_q=r_q,
                            )
                            if ir_m is None:
                                skipped += 1
                                continue

                            for mk, mv in ir_m.items():
                                combo_metrics[mk].append(mv)

                            per_query_rows.append({
                                "cohort": cohort_name,
                                "paper_id": pid,
                                "question_id": qid,
                                "chunker": st,
                                "model": model_name,
                                "model_label": m_label,
                                "combination": combo_key,
                                "metrics": ir_m,
                            })

                except Exception as e:
                    # Drop partial rows so a broken combo never lands truncated in the summary
                    per_query_rows[:] = [r for r in per_query_rows if r["combination"] != combo_key]
                    failures.append({
                        "combo": combo_key,
                        "error": f"{type(e).__name__}: {str(e)[:300]}",
                    })
                    print(f"    ERROR in {combo_key}: {e} (combo dropped)", flush=True)
                    continue

                rel_gt_count = sum(int(v) for v in combo_metrics.get("rel_gt_rq", []))
                if rel_gt_count > 0:
                    print(f"    WARNING: {rel_gt_count} queries had relevances > r_q in {combo_key}", flush=True)

                n_eval = len(combo_metrics["ndcg_10"])
                combo_summary = {
                    "chunker": st,
                    "model": model_name,
                    "model_label": m_label,
                    "granularity": "parent" if st == "hierarchical" else "chunk",
                    "evaluated_questions": n_eval,
                    "skipped_no_relevant": skipped,
                    "skipped_no_units": skipped_no_units,
                    "rel_gt_rq_count": rel_gt_count,
                    "means": {
                        mk: round(float(np.mean(combo_metrics[mk])), 4)
                        if combo_metrics[mk] else 0.0
                        for mk in IR_METRIC_KEYS
                    },
                    "total_units": sum(len(chunker_units[st].get(p, [])) for p in valid_papers),
                    "indexing_throughput_chunks_per_s": combo_index_tput,
                }
                summary["combinations"][combo_key] = combo_summary
                print(f"    Done {combo_key}: nDCG@10={combo_summary['means']['ndcg_10']}, "
                      f"MRR@10={combo_summary['means']['mrr_10']}, "
                      f"Recall@10={combo_summary['means']['recall_10']}, "
                      f"P@5={combo_summary['means']['precision_5']}, "
                      f"n={n_eval}, skipped={skipped}, no_units={skipped_no_units}", flush=True)

        # Record model efficiency
        mem_info = mem.report()
        summary[f"model_efficiency_{m_label}"] = {
            "p50_ms": round(float(np.percentile(model_latencies, 50)), 2) if model_latencies else 0.0,
            "p95_ms": round(float(np.percentile(model_latencies, 95)), 2) if model_latencies else 0.0,
            "peak_memory_mb": mem_info.get("python_working_set_peak_mb", 0.0),
        }

        # Checkpoint after each model (summary.json + per_query.jsonl)
        summary["elapsed_s"] = round(time.time() - t_start, 1)
        write_checkpoint(summary, per_query_rows, out_dir)
        if out_dir:
            print(f"    Checkpoint written to {out_dir}", flush=True)

        # Evict model from cache to avoid RSS/VRAM accumulation across models
        evicted = False
        if hasattr(rp, "_MODELS") and model_name in rp._MODELS:
            del rp._MODELS[model_name]
            evicted = True
        elif hasattr(rp.get_model, "cache_clear"):
            rp.get_model.cache_clear()
            evicted = True
        if not evicted:
            print(f"    Warning: could not evict model {model_name} from cache; memory may accumulate.", flush=True)

        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    summary["elapsed_s"] = round(time.time() - t_start, 1)
    summary["failures"] = failures

    # Common-set means (the basis for every comparison table in the report)
    common_keys = common_question_keys(per_query_rows, chunkers)
    summary["n_common_questions"] = len(common_keys)
    rows_by_combo: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in per_query_rows:
        if (r["paper_id"], r["question_id"]) in common_keys:
            rows_by_combo[r["combination"]].append(r["metrics"])
    for combo_key, cdata in summary["combinations"].items():
        filtered = rows_by_combo.get(combo_key, [])
        cdata["common_means"] = {
            mk: round(float(np.mean([f[mk] for f in filtered])), 4) if filtered else 0.0
            for mk in IR_METRIC_KEYS
        }
        cdata["n_common"] = len(filtered)

    if out_dir:
        write_checkpoint(summary, per_query_rows, out_dir)
        generate_markdown_report(summary, out_dir / "REPORT.md")
        print(f"\nArtifacts written to {out_dir}", flush=True)

    return summary


# -----------------------------------------------------------------------------
# Markdown Report Generator
# -----------------------------------------------------------------------------
def _metrics(cdata: Dict[str, Any], use_common: bool) -> Dict[str, float]:
    if use_common and "common_means" in cdata:
        return cdata["common_means"]
    return cdata["means"]


def _fmt_thr(t: Any) -> str:
    return f"{t:.1f}" if isinstance(t, (int, float)) else "—"


def generate_markdown_report(summary: Dict[str, Any], report_path: Path):
    combos = summary.get("combinations", {})
    if not combos:
        return

    n_common = summary.get("n_common_questions", 0)
    use_common = n_common > 0
    basis = (f"common question set (N={n_common})" if use_common
             else "each combination's own question set (NOT directly comparable)")

    sorted_combos = sorted(combos.items(), key=lambda x: _metrics(x[1], use_common)["ndcg_10"], reverse=True)

    lines = [
        f"# Phase 2: Retrieval Evaluation Report — Cohort [{summary.get('cohort')}]",
        "",
        f"- **Cohort:** {summary.get('cohort')}",
        f"- **Papers (loaded / requested):** {summary.get('n_papers')} / "
        f"{summary.get('n_papers_requested', summary.get('n_papers'))}",
        f"- **Questions in loaded papers:** {summary.get('n_questions')}",
        f"- **Common scored questions (all active chunkers):** {n_common}",
        f"- **Section sources:** {summary.get('section_source_counts')}",
        f"- **Total Combinations Tested:** {len(combos)} (Chunkers × Embedders)",
        f"- **Metric basis:** {basis}",
        f"- **Evaluation Time:** {summary.get('elapsed_s')} s",
        "",
        f"## 1. Overall Leaderboard (Ranked by nDCG@10 on {basis})",
        "",
        "| Rank | Combination | Chunker | Granularity | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | N (scored) | N (own) | Skipped (no rel / no units) | Index tput (c/s) |",
        "| :---: | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for rank_idx, (ck, cdata) in enumerate(sorted_combos, 1):
        m = _metrics(cdata, use_common)
        n_scored = cdata.get("n_common", 0) if use_common else cdata.get("evaluated_questions", 0)
        lines.append(
            f"| {rank_idx} | **{ck}** | `{cdata['chunker']}` | {cdata.get('granularity', '')} | "
            f"`{cdata['model_label']}` | **{m['ndcg_10']:.4f}** | {m['mrr_10']:.4f} | {m['map_10']:.4f} | "
            f"{m['recall_10']:.4f} | {m['recall_5']:.4f} | {m['precision_5']:.4f} | "
            f"{m['hit_1']:.4f} | {n_scored} | {cdata.get('evaluated_questions', 0)} | "
            f"{cdata.get('skipped_no_relevant', 0)} / {cdata.get('skipped_no_units', 0)} | "
            f"{_fmt_thr(cdata.get('indexing_throughput_chunks_per_s'))} |"
        )

    lines.extend([
        "",
        f"## 2. Chunking Method Comparison (averaged across embedding models; {basis})",
        "",
        "> `hierarchical` retrieves at parent-section granularity; flat chunkers retrieve at",
        "> 400-token chunk granularity. P@k, MAP and nDCG are therefore not on the same units.",
        "",
        "| Chunker | Granularity | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | N (scored) | Index tput (c/s) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    chunker_groups: Dict[str, list] = defaultdict(list)
    for ck, cdata in combos.items():
        chunker_groups[cdata["chunker"]].append(cdata)

    for st in summary.get("chunkers", []):
        group = chunker_groups.get(st, [])
        if not group:
            continue
        ms = [_metrics(g, use_common) for g in group]
        n_scored = int(np.mean([g.get("n_common", 0) if use_common else g.get("evaluated_questions", 0)
                                for g in group]))
        thr_vals = [g.get("indexing_throughput_chunks_per_s") for g in group
                    if isinstance(g.get("indexing_throughput_chunks_per_s"), (int, float))]
        thr = _fmt_thr(float(np.mean(thr_vals))) if thr_vals else "—"
        lines.append(
            f"| `{st}` | {group[0].get('granularity', '')} | "
            f"**{np.mean([m['ndcg_10'] for m in ms]):.4f}** | "
            f"{np.mean([m['mrr_10'] for m in ms]):.4f} | "
            f"{np.mean([m['recall_10'] for m in ms]):.4f} | "
            f"{np.mean([m['precision_5'] for m in ms]):.4f} | "
            f"{np.mean([m['hit_1'] for m in ms]):.4f} | {n_scored} | {thr} |"
        )

    lines.extend([
        "",
        f"## 3. Embedding Model Comparison (averaged across chunking methods; {basis})",
        "",
        "| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query P50 (ms) | Query P95 (ms) | Peak Memory (MB) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    model_groups: Dict[str, list] = defaultdict(list)
    for ck, cdata in combos.items():
        model_groups[cdata["model_label"]].append(cdata)

    for ml, group in model_groups.items():
        ms = [_metrics(g, use_common) for g in group]
        eff = summary.get(f"model_efficiency_{ml}") or summary.get(f"model_latency_{ml}", {})
        lines.append(
            f"| `{ml}` | **{np.mean([m['ndcg_10'] for m in ms]):.4f}** | "
            f"{np.mean([m['mrr_10'] for m in ms]):.4f} | "
            f"{np.mean([m['recall_10'] for m in ms]):.4f} | "
            f"{np.mean([m['precision_5'] for m in ms]):.4f} | "
            f"{np.mean([m['hit_1'] for m in ms]):.4f} | "
            f"{eff.get('p50_ms', '—')} | {eff.get('p95_ms', '—')} | {eff.get('peak_memory_mb', '—')} |"
        )
    n_chunkers_per_model = {ml: len(g) for ml, g in model_groups.items()}
    if len(set(n_chunkers_per_model.values())) > 1:
        lines.extend(["", f"> Note: models averaged over different numbers of chunkers "
                          f"(some combos failed): {n_chunkers_per_model}"])

    best_ck, best = sorted_combos[0]
    bm = _metrics(best, use_common)
    n_inconsistent = sum(c.get("rel_gt_rq_count", 0) for c in combos.values())
    findings = [
        f"1. **Top Combination:** `{best_ck}` ({best.get('granularity')} granularity) achieved the highest "
        f"nDCG@10 of **{bm['ndcg_10']:.4f}** with MRR@10 of **{bm['mrr_10']:.4f}** on the {basis}.",
    ]
    if best.get("chunker") == "hierarchical":
        flat = [(k, c) for k, c in sorted_combos if c["chunker"] != "hierarchical"]
        if flat:
            fk, fc = flat[0]
            fm = _metrics(fc, use_common)
            findings.append(
                f"2. **Best flat-chunk combination:** `{fk}` with nDCG@10 **{fm['ndcg_10']:.4f}**, "
                "MRR@10 "
                f"**{fm['mrr_10']:.4f}**. Hierarchical is scored on larger parent sections, so its lead "
                "is not like-for-like."
            )
    findings.extend([
        "3. **Metric Integrity:** Pure IR metrics on ranked candidate units; unit-L2 normalized; "
        "deterministic tie-breaking.",
        "4. **Section sources:** see `section_sources` in `summary.json` — PDF and JSON text "
        f"are mixed if not all PDFs are present (counts: {summary.get('section_source_counts')}); "
        "evidence matching at τ=0.5 behaves differently on each.",
        f"5. **Relevance consistency:** {n_inconsistent} queries had more hits than R_q "
        "(relevance counter vs hit test disagree); this should be 0.",
        f"6. **Failures:** {len(summary.get('failures', []))} recorded in `summary.json`.",
    ])
    lines.extend(["", "## 4. Key Findings", ""] + findings + [""])

    report_path.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Phase 2 Retrieval Evaluation: Chunking x Embedding")
    ap.add_argument("--dataset", choices=["qasper", "peerqa", "all"], default="all",
                    help="Target dataset: qasper (C-RET), peerqa (PEERQA-PDF), or all (default: all)")
    ap.add_argument("--cohort", default=None,
                    help="Specific cohort name (e.g. C-RET, C-RET-150, PEERQA-PDF, PEERQA-TEXT)")
    ap.add_argument("--chunkers", default=None,
                    help="Comma-separated chunkers (default: hierarchical,section_overlap,fixed_size)")
    ap.add_argument("--models", default=None,
                    help="Comma-separated model names or short keys (default: e5,qwen,gemma,arctic,modernbert)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Number of papers to evaluate (smoke tests); 0 or omitted = all")
    ap.add_argument("--seed", type=int, default=None,
                    help="Seed for random paper sampling; requires --limit > 0 (default: take first N alphabetically)")
    args = ap.parse_args()

    if args.limit is not None and args.limit < 0:
        ap.error("--limit must be >= 0")
    if args.seed is not None and not args.limit:
        ap.error("--seed requires --limit > 0")

    # Parse chunkers — strip whitespace, validate
    if args.chunkers:
        chunkers = [c.strip() for c in args.chunkers.split(",") if c.strip()]
        bad = [c for c in chunkers if c not in CHUNKERS]
        if bad:
            ap.error(f"Unknown chunker(s): {bad}. Valid: {CHUNKERS}")
        if not chunkers:
            ap.error("--chunkers is empty")
    else:
        chunkers = list(CHUNKERS)

    # Parse models
    if args.models:
        selected_models = [MODEL_MAP.get(m.strip(), m.strip()) for m in args.models.split(",") if m.strip()]
    else:
        selected_models = DEFAULT_MODELS

    # Determine cohorts
    cohort_list: List[str] = []
    if args.cohort:
        cohort_list.append(args.cohort)
    elif args.dataset == "qasper":
        cohort_list.append("C-RET")
    elif args.dataset == "peerqa":
        cohort_list.append("PEERQA-PDF")
    else:  # all
        cohort_list.extend(["C-RET", "PEERQA-PDF"])

    all_results: Dict[str, Any] = {}
    for ch_name in cohort_list:
        sub_dir = ARTIFACTS_DIR / ch_name.lower().replace("-", "_")
        if args.limit:
            sub_dir = sub_dir / f"smoke_{args.limit}"
        res = run_dataset_retrieval_benchmark(
            cohort_name=ch_name,
            chunkers=chunkers,
            models=selected_models,
            limit=args.limit,
            seed=args.seed,
            out_dir=sub_dir,
        )
        all_results[ch_name] = res

    # Merge with any previous combined summary
    combined_summary_path = ARTIFACTS_DIR / (
        "summary.json" if not args.limit else f"summary_smoke_{args.limit}.json"
    )
    combined_summary_path.parent.mkdir(parents=True, exist_ok=True)
    if combined_summary_path.exists():
        try:
            prev = json.loads(combined_summary_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        prev.update(all_results)
        all_results = prev
    combined_summary_path.write_text(
        json.dumps(all_results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nAll Phase 2 retrieval benchmarks complete! Overall summary → {combined_summary_path}")


if __name__ == "__main__":
    main()