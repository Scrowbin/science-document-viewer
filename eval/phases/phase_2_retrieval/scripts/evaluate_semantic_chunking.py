"""
Phase 2: Semantic Chunking Evaluation (Retrieval Ablation).

Extension / ablation study for two semantic chunking variants against the same
embedding models and datasets used in evaluate_retrieval.py.  Semantic chunking
is NOT part of the primary 3-chunker × 5-model matrix; this script exists so its
retrieval quality can be reported alongside that matrix.

Variants (both use percentile_threshold=25.0, max_tokens=400):
  semantic_v1  — apps.documents.services.chunkers.chunk_semantic
                 (production branch implementation; identical defaults)
  semantic_v2  — teammate's implementation vendored from origin/main commit 49dcac6
                 (adds buffer_size=1 smoothing and section-level percentile calc)

Datasets / Cohorts: same as evaluate_retrieval.py
  QASPER  → C-RET  / C-RET-150
  PeerQA  → PEERQA-PDF / PEERQA-TEXT

Metrics (Pure Retrieval Quality, identical to evaluate_retrieval.py):
  nDCG@5/10, MRR@5/10, MAP@10/20, Recall@5/10/20, Precision@1/5/10, Hit@1/5/10
  Efficiency: query latency P50/P95 ms, chunking throughput (chunks/s),
              indexing throughput (chunks/s) per (variant, model), peak memory MB.

NOTE: Semantic chunking requires the embedder at chunk-build time (~6 s / paper on
CPU; budget ~10 min for C-RET-150 × 2 variants × 1 model on a CPU-only machine).

Usage:
  python evaluate_semantic_chunking.py [--dataset {qasper,peerqa,all}]
                                       [--cohort COHORT]
                                       [--chunkers CHUNKERS]
                                       [--models MODELS]
                                       [--limit N] [--seed S]
  # Smoke test (1 paper, e5 only):
  python evaluate_semantic_chunking.py --cohort C-RET-150 --limit 1 --models e5
"""

import argparse
import hashlib
import importlib.util
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
        "Expected evaluate_semantic_chunking.py to live at eval/phases/phase_2_retrieval/scripts/."
    )

from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402
from eval_common.relevance import count_relevant_chunks, is_chunk_hit  # noqa: E402

rp.setup_django()
from apps.documents.services.chunkers import chunk_semantic as chunk_semantic_v1  # noqa: E402
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402

# ---------------------------------------------------------------------------
# Load vendored semantic_v2 (teammate's implementation, archived)
# ---------------------------------------------------------------------------
_VENDOR = (
    ROOT / "archive" / "eval" / "phases" / "phase_2_chunking"
    / "scripts" / "vendor" / "teammate_chunkers_49dcac6.py"
)
_VENDOR_SHA256 = "206a7a57499a867db51315893d9d63ab0656531bc98aa82d6e8f489d5585adc6"


def _load_vendor() -> Any:
    """Load vendored semantic_v2 chunker; raises with a clear message if missing."""
    if not _VENDOR.exists():
        raise FileNotFoundError(
            f"Vendored semantic_v2 chunker not found at {_VENDOR}.\n"
            "Expected archive/eval/phases/phase_2_chunking/scripts/vendor/"
            "teammate_chunkers_49dcac6.py"
        )
    actual = hashlib.sha256(_VENDOR.read_bytes()).hexdigest()
    if actual != _VENDOR_SHA256:
        raise RuntimeError(
            f"Vendored chunker SHA-256 mismatch (got {actual[:12]}…). "
            "The file has been modified since archival."
        )
    spec = importlib.util.spec_from_file_location("teammate_chunkers_49dcac6", _VENDOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.chunk_semantic


chunk_semantic_v2 = _load_vendor()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ARTIFACTS_DIR = ROOT / "eval" / "phases" / "phase_2_retrieval" / "artifacts"

CHUNKERS = ["semantic_v1", "semantic_v2"]

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


# ---------------------------------------------------------------------------
# Math & Metric Helpers (Pure IR + Exact Cosine Guarantee)
# ---------------------------------------------------------------------------
def normalize_l2(x: np.ndarray) -> np.ndarray:
    """Guarantee strictly unit L2 norm so dot-product is exact cosine similarity."""
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norms, 1e-12)


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
def bench_index(model_name: str, texts: List[str], n: int = 100) -> float:
    """Measure passage-encoding throughput (chunks/s) for model on up to n texts.

    Runs a small warm-up call first so CUDA kernel launch / JIT cost is excluded
    from the timed window.
    """
    s = texts[:n]
    if not s:
        return 0.0
    try:
        rp.embed(model_name, s[:8], is_query=False, batch_size=8)  # warm passage path
        t0 = time.perf_counter()
        rp.embed(model_name, s, is_query=False, batch_size=32)
        return round(len(s) / max(time.perf_counter() - t0, 1e-4), 1)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# Section / Document Loading (multi-split fallback + source tracking)
# ---------------------------------------------------------------------------
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
    """Return (sections, source_tag)."""
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

    # 2. JSON fallback — try hinted split first, then remaining splits
    for s in [split] + [x for x in _QASPER_ALL_SPLITS if x != split]:
        pdata = _load_qasper_split(s).get(paper_id, {})
        full_text = pdata.get("full_text", [])
        if full_text:
            secs = [
                {
                    "heading": sec.get("section_name", "") or "Body",
                    "title":   sec.get("section_name", "") or "Body",
                    "text": "\n\n".join(sec.get("paragraphs", [])),
                }
                for sec in full_text
                if "\n\n".join(sec.get("paragraphs", [])).strip()
            ]
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
# Common-key intersection (comparable variant averages in Table 2)
# -----------------------------------------------------------------------------
def common_question_keys(
    per_query_rows: List[Dict[str, Any]],
    chunkers: List[str],
) -> frozenset:
    """Return (paper_id, question_id) pairs evaluated by ALL active chunkers."""
    by: Dict[str, set] = defaultdict(set)
    for r in per_query_rows:
        by[r["chunker"]].add((r["paper_id"], r["question_id"]))
    active = [c for c in chunkers if c in by and by[c]]
    if not active:
        return frozenset()
    return frozenset(set.intersection(*(by[c] for c in active)))


# ---------------------------------------------------------------------------
# Semantic Chunk Building
# ---------------------------------------------------------------------------
def build_semantic_units(
    sections: List[Dict[str, Any]],
    variant: str,
    model_name: str,
    paper_id: str,
) -> List[Dict[str, Any]]:
    """Build semantic chunks using the embedder (required by both variants).

    Both variants use max_tokens=400 and percentile_threshold=25.0 (registered
    defaults). semantic_v2 additionally applies buffer_size=1 smoothing.
    """
    embedder = rp.get_model(model_name)
    if variant == "semantic_v1":
        chunks = chunk_semantic_v1(
            sections,
            embedder=embedder,
            max_tokens=400,
            percentile_threshold=25.0,
            paper_id=paper_id,
        )
    elif variant == "semantic_v2":
        chunks = chunk_semantic_v2(
            sections,
            embedder=embedder,
            max_tokens=400,
            percentile_threshold=25.0,
            paper_id=paper_id,
        )
    else:
        raise ValueError(f"Unknown semantic variant: {variant!r}")

    for c in chunks:
        c.setdefault("paper_arxiv_id", paper_id)
    return chunks


def rank_units_and_evaluate(
    units: List[Dict[str, Any]],
    scores: np.ndarray,
    paper_id: str,
    evidence: List[str],
    tau: float = 0.50,
) -> Optional[Dict[str, Any]]:
    """Rank flat semantic chunks and return IR metrics."""
    K = 20
    r_q = count_relevant_chunks(units, paper_id, "", evidence, tau=tau)
    if r_q <= 0:
        return None
    ranked = np.argsort(-scores)
    items = [units[i] for i in ranked[:K]]
    relevances = [1 if is_chunk_hit(u, paper_id, "", evidence, tau=tau) else 0 for u in items]
    rel_sum = sum(relevances)
    metrics = compute_all_ir_metrics(relevances, r_q)
    metrics["r_q"] = int(r_q)
    metrics["rel_gt_rq"] = int(rel_sum > r_q)
    return metrics


# ---------------------------------------------------------------------------
# Main Evaluation Engine
# ---------------------------------------------------------------------------
def run_semantic_retrieval_benchmark(
    cohort_name: str,
    chunkers: List[str],
    models: List[str],
    limit: Optional[int] = None,
    seed: Optional[int] = None,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    print(
        f"\n{'='*70}\n"
        f"Starting Phase 2 Semantic Chunking Evaluation: Cohort [{cohort_name}]\n"
        f"{'='*70}",
        flush=True,
    )

    cohort = rr.load_cohort(cohort_name)
    groups = rr.group_items(cohort)
    all_papers = sorted(groups)

    if limit and seed is not None:
        rng = np.random.RandomState(seed)
        chosen = sorted(rng.choice(len(all_papers), size=min(limit, len(all_papers)), replace=False))
        papers = [all_papers[i] for i in chosen]
    elif limit:
        papers = all_papers[:limit]
    else:
        papers = all_papers

    print(
        f"Loaded cohort {cohort_name}: {len(papers)} papers (limit={limit}, seed={seed}), "
        f"{sum(len(groups[p]) for p in papers)} questions",
        flush=True,
    )

    tag = cohort_name.lower().replace("-", "_")

    per_query_rows: List[Dict[str, Any]] = []
    t_start = time.time()
    section_sources: Dict[str, str] = {}
    failures: List[Dict[str, Any]] = []

    # Pre-extract sections for all papers in cohort
    print("Pre-loading sections...", flush=True)
    paper_sections: Dict[str, List[Dict[str, Any]]] = {}
    for pid in papers:
        secs, src = load_sections_for_cohort(cohort_name, pid)
        if not secs:
            failures.append({"paper_id": pid, "error": "No sections loaded"})
            continue
        paper_sections[pid] = secs
        section_sources[pid] = src

    valid_papers = [p for p in papers if p in paper_sections]
    print(f"Sections ready for {len(valid_papers)}/{len(papers)} papers.", flush=True)

    summary: Dict[str, Any] = {
        "cohort": cohort_name,
        "n_papers": len(valid_papers),
        "n_questions": sum(len(groups[p]) for p in valid_papers),
        "n_papers_requested": len(papers),
        "chunkers": chunkers,
        "models": models,
        "section_sources": section_sources,
        "combinations": {},
        "failures": failures,
    }

    def safe_pid(pid: str) -> str:
        return pid.replace("/", "__").replace("\\", "__")

    # Evaluate per model (semantic chunking is model-dependent: embed at chunk time)
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

            # Build semantic units per variant per paper (CPU-bound; expect ~6 s / paper)
            chunker_units: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
                st: {} for st in chunkers
            }
            chunker_chunk_times: Dict[str, float] = {st: 0.0 for st in chunkers}
            total_units: Dict[str, int] = {st: 0 for st in chunkers}

            for st in chunkers:
                print(f"  Building {st} chunks with {m_label}...", flush=True)
                for pid in valid_papers:
                    try:
                        tc = time.perf_counter()
                        units = build_semantic_units(
                            paper_sections[pid], variant=st,
                            model_name=model_name, paper_id=pid,
                        )
                        chunker_chunk_times[st] += time.perf_counter() - tc
                        if units:
                            chunker_units[st][pid] = units
                            total_units[st] += len(units)
                        else:
                            failures.append(
                                {"paper_id": pid, "strategy": st, "error": "No units built"}
                            )
                    except Exception as e:
                        failures.append(
                            {"paper_id": pid, "strategy": st,
                             "error": f"{type(e).__name__}: {str(e)[:200]}"}
                        )

            # Rank & evaluate per chunker variant
            for st in chunkers:
                combo_key = f"{st}|{m_label}"
                print(f"  > Evaluating combination: [{combo_key}]", flush=True)
                combo_metrics: Dict[str, List[float]] = defaultdict(list)
                skipped = 0

                # Passage-indexing throughput benchmark per (variant, model)
                sample_texts = [
                    u["text"]
                    for p in valid_papers[:5]
                    for u in chunker_units[st].get(p, [])
                ]
                combo_index_tput = bench_index(model_name, sample_texts)

                try:
                    for pid in valid_papers:
                        units = chunker_units[st].get(pid)
                        if not units:
                            continue

                        texts = [u["text"] for u in units]
                        h = hashlib.md5("\x00".join(texts).encode()).hexdigest()[:8]
                        um = rp.cached_embed(
                            model_name, texts, False,
                            f"{tag}_{safe_pid(pid)}_{st}_{m_label}_{h}"
                        )
                        if len(um) != len(units):
                            raise RuntimeError(
                                f"Embedding count mismatch: {len(um)} vs {len(units)}"
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
                            qid = it.get("question_id") or f"{pid}#{i}"
                            scores = um @ q
                            ir_m = rank_units_and_evaluate(
                                units=units,
                                scores=scores,
                                paper_id=pid,
                                evidence=it.get("retrieval_evidence", []),
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
                chunk_tput = (
                    round(total_units[st] / max(chunker_chunk_times[st], 1e-4), 2)
                    if chunker_chunk_times[st] > 0 else 0.0
                )
                combo_summary = {
                    "chunker": st,
                    "model": model_name,
                    "model_label": m_label,
                    "evaluated_questions": n_eval,
                    "skipped_no_relevant": skipped,
                    "rel_gt_rq_count": rel_gt_count,
                    "means": {
                        mk: round(float(np.mean(combo_metrics[mk])), 4)
                        if combo_metrics[mk] else 0.0
                        for mk in IR_METRIC_KEYS
                    },
                    "total_units": total_units[st],
                    "chunking_throughput_chunks_per_s": chunk_tput,
                    "indexing_throughput_chunks_per_s": combo_index_tput,
                }
                summary["combinations"][combo_key] = combo_summary
                print(
                    f"    Done {combo_key}: nDCG@10={combo_summary['means']['ndcg_10']}, "
                    f"MRR@10={combo_summary['means']['mrr_10']}, "
                    f"Recall@10={combo_summary['means']['recall_10']}, "
                    f"P@5={combo_summary['means']['precision_5']}, "
                    f"n={n_eval}, skipped={skipped}",
                    flush=True,
                )

        # Record model efficiency
        mem_info = mem.report()
        summary[f"model_efficiency_{m_label}"] = {
            "p50_ms": round(float(np.percentile(model_latencies, 50)), 2) if model_latencies else 0.0,
            "p95_ms": round(float(np.percentile(model_latencies, 95)), 2) if model_latencies else 0.0,
            "peak_memory_mb": mem_info.get("python_working_set_peak_mb", 0.0),
        }

        # Checkpoint: write summary and per_query.jsonl after each model
        if out_dir:
            out_dir.mkdir(parents=True, exist_ok=True)
            summary["elapsed_s"] = round(time.time() - t_start, 1)
            (out_dir / "summary.json").write_text(
                json.dumps(summary, indent=2, default=str), encoding="utf-8"
            )
            with open(out_dir / "per_query.jsonl", "w", encoding="utf-8") as f:
                for r in per_query_rows:
                    f.write(json.dumps(r, default=str) + "\n")
            print(f"    Checkpoint written to {out_dir}", flush=True)

        # Evict model to prevent memory accumulation across models
        evicted = False
        if hasattr(rp, "_MODELS") and model_name in rp._MODELS:
            del rp._MODELS[model_name]
            evicted = True
        elif hasattr(rp.get_model, "cache_clear"):
            rp.get_model.cache_clear()
            evicted = True

        if not evicted:
            print(f"    Warning: Could not evict model {model_name} from cache; memory may accumulate.", flush=True)

        import gc
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    summary["elapsed_s"] = round(time.time() - t_start, 1)
    summary["failures"] = failures

    # Common-key means across semantic variants
    common_keys = common_question_keys(per_query_rows, chunkers)
    summary["n_common_questions"] = len(common_keys)
    for combo_key, cdata in summary["combinations"].items():
        st = cdata["chunker"]
        ml = cdata["model_label"]
        filtered = [
            r["metrics"] for r in per_query_rows
            if r["chunker"] == st and r["model_label"] == ml
            and (r["paper_id"], r["question_id"]) in common_keys
        ]
        cdata["common_means"] = {
            mk: round(float(np.mean([f[mk] for f in filtered])), 4)
            if filtered else 0.0
            for mk in IR_METRIC_KEYS
        }
        cdata["n_common"] = len(filtered)

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )
        with open(out_dir / "per_query.jsonl", "w", encoding="utf-8") as f:
            for r in per_query_rows:
                f.write(json.dumps(r, default=str) + "\n")
        generate_markdown_report(summary, out_dir / "REPORT.md")
        print(f"\nArtifacts written to {out_dir}", flush=True)

    return summary


# ---------------------------------------------------------------------------
# Markdown Report Generator
# ---------------------------------------------------------------------------
def generate_markdown_report(summary: Dict[str, Any], report_path: Path):
    combos = summary.get("combinations", {})
    if not combos:
        return

    sorted_combos = sorted(combos.items(), key=lambda x: x[1]["means"]["ndcg_10"], reverse=True)
    n_common = summary.get("n_common_questions", 0)

    lines = [
        f"# Phase 2: Semantic Chunking Evaluation Report — Cohort [{summary.get('cohort')}]",
        "",
        "> **Role:** Extension / ablation study for semantic chunking. "
        "Not part of the primary 3-chunker × 5-model matrix (`evaluate_retrieval.py`).",
        "",
        f"- **Cohort:** {summary.get('cohort')}",
        f"- **Evaluated Papers:** {summary.get('n_papers')} "
        f"(of {summary.get('n_papers_requested', summary.get('n_papers'))} requested)",
        f"- **Evaluated Questions:** {summary.get('n_questions')}",
        f"- **Common Questions (all active variants):** {n_common}",
        f"- **Semantic Variants:** semantic_v1 (production branch), semantic_v2 (teammate, buffer_size=1)",
        f"- **Total Combinations Tested:** {len(combos)} (Variants × Embedders)",
        f"- **Evaluation Time:** {summary.get('elapsed_s')} s",
        "",
        "## 1. Overall Leaderboard (Ranked by nDCG@10, each variant's own question set)",
        "",
        "| Rank | Combination | Variant | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | N | Skipped | Chunk tput (c/s) | Index tput (c/s) |",
        "| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for rank_idx, (ck, cdata) in enumerate(sorted_combos, 1):
        m = cdata["means"]
        lines.append(
            f"| {rank_idx} | **{ck}** | `{cdata['chunker']}` | `{cdata['model_label']}` | "
            f"**{m['ndcg_10']:.4f}** | {m['mrr_10']:.4f} | {m['map_10']:.4f} | "
            f"{m['recall_10']:.4f} | {m['recall_5']:.4f} | {m['precision_5']:.4f} | "
            f"{m['hit_1']:.4f} | {cdata.get('evaluated_questions', 0)} | "
            f"{cdata.get('skipped_no_relevant', 0)} | "
            f"{cdata.get('chunking_throughput_chunks_per_s', 0):.2f} | "
            f"{cdata.get('indexing_throughput_chunks_per_s', 0):.1f} |"
        )

    lines.extend([
        "",
        f"## 2. Semantic Variant Comparison (Common {n_common} questions only, averaged across all embedding models)",
        "",
        "| Variant | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | N | Chunk tput (c/s) | Index tput (c/s) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    chunker_groups: Dict[str, list] = defaultdict(list)
    for ck, cdata in combos.items():
        chunker_groups[cdata["chunker"]].append(cdata)

    for st in summary.get("chunkers", []):
        group = chunker_groups.get(st, [])
        if group:
            common_rows = [g for g in group if g.get("n_common", 0) > 0]
            src = common_rows if common_rows else group
            mean_ndcg  = np.mean([g["common_means"]["ndcg_10"] for g in src]) if common_rows else float("nan")
            mean_mrr   = np.mean([g["common_means"]["mrr_10"] for g in src]) if common_rows else float("nan")
            mean_rec   = np.mean([g["common_means"]["recall_10"] for g in src]) if common_rows else float("nan")
            mean_prec  = np.mean([g["common_means"]["precision_5"] for g in src]) if common_rows else float("nan")
            mean_hit   = np.mean([g["common_means"]["hit_1"] for g in src]) if common_rows else float("nan")
            mean_n     = int(np.mean([g.get("n_common", 0) for g in group]))
            mean_ctput = np.mean([g.get("chunking_throughput_chunks_per_s", 0) for g in group])
            mean_itput = np.mean([g.get("indexing_throughput_chunks_per_s", 0) for g in group])
            ndcg_str   = f"**{mean_ndcg:.4f}**" if not np.isnan(mean_ndcg) else "—"
            mrr_str    = f"{mean_mrr:.4f}" if not np.isnan(mean_mrr) else "—"
            rec_str    = f"{mean_rec:.4f}" if not np.isnan(mean_rec) else "—"
            prec_str   = f"{mean_prec:.4f}" if not np.isnan(mean_prec) else "—"
            hit_str    = f"{mean_hit:.4f}" if not np.isnan(mean_hit) else "—"
            lines.append(
                f"| `{st}` | {ndcg_str} | {mrr_str} | {rec_str} | "
                f"{prec_str} | {hit_str} | {mean_n} | {mean_ctput:.2f} | {mean_itput:.1f} |"
            )

    lines.extend([
        "",
        "## 3. Embedding Model Comparison (Averaged across both semantic variants)",
        "",
        "| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query P50 (ms) | Query P95 (ms) | Peak Memory (MB) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    model_groups: Dict[str, list] = defaultdict(list)
    for ck, cdata in combos.items():
        model_groups[cdata["model_label"]].append(cdata)

    for ml, group in model_groups.items():
        mean_ndcg = np.mean([g["means"]["ndcg_10"] for g in group])
        mean_mrr  = np.mean([g["means"]["mrr_10"] for g in group])
        mean_rec  = np.mean([g["means"]["recall_10"] for g in group])
        mean_prec = np.mean([g["means"]["precision_5"] for g in group])
        mean_hit  = np.mean([g["means"]["hit_1"] for g in group])
        eff = summary.get(f"model_efficiency_{ml}") or summary.get(f"model_latency_{ml}", {})
        p50    = eff.get("p50_ms", "—")
        p95    = eff.get("p95_ms", "—")
        mem_mb = eff.get("peak_memory_mb", "—")
        lines.append(
            f"| `{ml}` | **{mean_ndcg:.4f}** | {mean_mrr:.4f} | {mean_rec:.4f} | "
            f"{mean_prec:.4f} | {mean_hit:.4f} | {p50} | {p95} | {mem_mb} |"
        )

    lines.extend([
        "",
        "## 4. Notes",
        "",
        "- **semantic_v1** — `apps.documents.services.chunkers.chunk_semantic` on the production branch.",
        "  Uses percentile-based similarity drop threshold (25th pct) and a max_tokens=400 ceiling.",
        "- **semantic_v2** — teammate's implementation (`vendor/teammate_chunkers_49dcac6.py`, commit 49dcac6).",
        "  Adds `buffer_size=1` smoothing (mean of neighbour embeddings before thresholding) and "
        "per-section percentile calculation.",
        "- Both variants use the same embedding model for sentence similarity scoring at chunk time,",
        "  so chunking throughput (c/s) includes that embedding cost and is much lower than flat chunkers.",
        "- **Metric Integrity:** Pure IR metrics on flat semantic chunks; strictly unit-L2 normalized.",
        "- **Section sources:** see `section_sources` in `summary.json`.",
        "",
    ])

    if sorted_combos:
        best_ck, best_cd = sorted_combos[0]
        lines.append(
            f"**Champion combination:** `{best_ck}` — "
            f"nDCG@10 = **{best_cd['means']['ndcg_10']:.4f}**, "
            f"MRR@10 = **{best_cd['means']['mrr_10']:.4f}** (on its own question subset)."
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Phase 2 Semantic Chunking Evaluation: semantic_v1 vs semantic_v2 × Embedding Models"
    )
    ap.add_argument(
        "--dataset", choices=["qasper", "peerqa", "all"], default="all",
        help="Target dataset: qasper, peerqa, or all (default: all)",
    )
    ap.add_argument(
        "--cohort", default=None,
        help="Specific cohort name (e.g. C-RET, C-RET-150, PEERQA-PDF, PEERQA-TEXT)",
    )
    ap.add_argument(
        "--chunkers", "--variants", dest="chunkers", default=None,
        help="Comma-separated semantic variants (default: semantic_v1,semantic_v2)",
    )
    ap.add_argument(
        "--models", default=None,
        help="Comma-separated model short keys or HF IDs (default: e5,qwen,gemma,arctic,modernbert)",
    )
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Number of papers to evaluate (useful for smoke tests)",
    )
    ap.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for sampling papers when --limit is set (default: None, takes head)",
    )
    args = ap.parse_args()

    # Parse and validate chunkers
    if args.chunkers:
        chunkers = [c.strip() for c in args.chunkers.split(",")]
        bad = [c for c in chunkers if c not in CHUNKERS]
        if bad:
            ap.error(f"Unknown variant(s): {bad}. Valid: {CHUNKERS}")
    else:
        chunkers = CHUNKERS

    # Parse models
    if args.models:
        selected_models = [MODEL_MAP.get(m.strip(), m.strip()) for m in args.models.split(",")]
    else:
        selected_models = DEFAULT_MODELS

    # Determine cohorts to run
    cohort_list = []
    if args.cohort:
        cohort_list.append(args.cohort)
    elif args.dataset == "qasper":
        cohort_list.append("C-RET")
    elif args.dataset == "peerqa":
        cohort_list.append("PEERQA-PDF")
    else:  # all
        cohort_list.extend(["C-RET", "PEERQA-PDF"])

    all_results = {}
    for ch_name in cohort_list:
        sub_dir = ARTIFACTS_DIR / ch_name.lower().replace("-", "_") / "semantic"
        if args.limit:
            sub_dir = sub_dir / f"smoke_{args.limit}"
        res = run_semantic_retrieval_benchmark(
            cohort_name=ch_name,
            chunkers=chunkers,
            models=selected_models,
            limit=args.limit,
            seed=args.seed,
            out_dir=sub_dir,
        )
        all_results[ch_name] = res

    # Merge with any existing combined summary so single-cohort runs don't overwrite prior cohorts
    combined_path = ARTIFACTS_DIR / (
        "summary_semantic.json"
        if not args.limit
        else f"summary_semantic_smoke_{args.limit}.json"
    )
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    if combined_path.exists():
        try:
            prev = json.loads(combined_path.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
        prev.update(all_results)
        all_results = prev
    combined_path.write_text(
        json.dumps(all_results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nAll semantic chunking benchmarks complete! Summary → {combined_path}")


if __name__ == "__main__":
    main()
