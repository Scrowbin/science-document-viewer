"""
Phase 2: Retrieval Evaluation (Combined Chunking & Dense Embedding Benchmark).

Evaluates the combinatorial matrix of chunking strategies and dense embedding models
across standard Information Retrieval (IR) metrics on QASPER and PeerQA datasets.

Combinations:
  Chunkers:  {hierarchical, section_overlap, fixed_size}
  Embedders: {e5-small-v2, Qwen3-Embedding-0.6B, embeddinggemma-300m, snowflake-arctic-embed-s, modernbert-embed-base}
  Datasets:  QASPER (C-RET / C-RET-150) and PeerQA (PEERQA-PDF / PEERQA-TEXT)

Metrics (Pure Retrieval Quality):
  - MRR:       MRR@5, MRR@10
  - Recall:    Recall@5, Recall@10, Recall@20
  - Precision: Precision@1, Precision@5, Precision@10
  - NDCG:      nDCG@5, nDCG@10
  - MAP:       MAP@10, MAP@20
  - Hit@k:     Hit@1, Hit@5, Hit@10
  - Efficiency: Indexing throughput (chunks/s), query latency (P50/P95 ms), memory usage.

Usage:
  python evaluate_retrieval.py [--dataset {qasper,peerqa,all}] [--cohort COHORT]
                               [--chunkers CHUNKERS] [--models MODELS] [--limit N]
"""

import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402
from eval_common.relevance import count_relevant_chunks, is_chunk_hit  # noqa: E402

rp.setup_django()
from apps.documents.services.chunkers import chunk_fixed_size, chunk_hierarchical  # noqa: E402
from apps.documents.services.chunking_utils import chunk_sections, extract_sections_from_pdf  # noqa: E402
from apps.documents.services.rag_service import get_model_prefix  # noqa: E402

ARTIFACTS_DIR = ROOT / "eval" / "phases" / "phase_2_retrieval" / "artifacts"

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
        "ndcg_5": round(compute_ndcg(relevances, total_relevant, k=5), 4),
        "mrr_10": round(compute_mrr(relevances, k=10), 4),
        "mrr_5": round(compute_mrr(relevances, k=5), 4),
        "map_10": round(compute_average_precision(relevances, total_relevant, k=10), 4),
        "map_20": round(compute_average_precision(relevances, total_relevant, k=20), 4),
        "recall_5": round(compute_recall(relevances, total_relevant, k=5), 4),
        "recall_10": round(compute_recall(relevances, total_relevant, k=10), 4),
        "recall_20": round(compute_recall(relevances, total_relevant, k=20), 4),
        "precision_1": round(compute_precision(relevances, k=1), 4),
        "precision_5": round(compute_precision(relevances, k=5), 4),
        "precision_10": round(compute_precision(relevances, k=10), 4),
        "hit_1": compute_hit_at_k(relevances, k=1),
        "hit_5": compute_hit_at_k(relevances, k=5),
        "hit_10": compute_hit_at_k(relevances, k=10),
    }


# -----------------------------------------------------------------------------
# Section & Document Loading
# -----------------------------------------------------------------------------
_QASPER_CACHE: Dict[str, Dict[str, Any]] = {}


def load_qasper_sections(paper_id: str, split: str = "train") -> List[Dict[str, Any]]:
    # 1. Try local PDF if exists
    pdf_candidates = [
        ROOT / "eval" / "pdfs" / "train_reservoir" / f"{paper_id}.pdf",
        ROOT / "eval" / "pdfs" / "dev" / f"{paper_id}.pdf",
        ROOT / "eval" / "pdfs" / "test" / f"{paper_id}.pdf",
    ]
    for p in pdf_candidates:
        if p.exists() and p.stat().st_size > 1000:
            try:
                sec = extract_sections_from_pdf(str(p))
                if sec:
                    return sec
            except Exception:
                pass

    # 2. Native dataset full_text fallback
    if split not in _QASPER_CACHE:
        path = ROOT / "eval" / "data" / "qasper_official" / f"qasper-{split}-v0.3.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _QASPER_CACHE[split] = json.load(f)
        else:
            _QASPER_CACHE[split] = {}

    pdata = _QASPER_CACHE[split].get(paper_id, {})
    full_text = pdata.get("full_text", [])
    if full_text:
        return [
            {
                "heading": s.get("section_name", "") or "Body",
                "title": s.get("section_name", "") or "Body",
                "text": "\n\n".join(s.get("paragraphs", [])),
            }
            for s in full_text
            if "\n\n".join(s.get("paragraphs", [])).strip()
        ]
    return []


def load_peerqa_sections(paper_id: str) -> List[Dict[str, Any]]:
    # 1. Try PDF if exists
    pdf = ROOT / "eval" / "pdfs" / "peerqa" / (paper_id.replace("/", "__") + ".pdf")
    if pdf.exists() and pdf.stat().st_size > 1000:
        try:
            sec = extract_sections_from_pdf(str(pdf))
            if sec:
                return sec
        except Exception:
            pass

    # 2. Shipped text (papers.jsonl)
    return rr.peerqa_text_sections(paper_id)


def load_sections_for_cohort(cohort: str, paper_id: str) -> List[Dict[str, Any]]:
    if "PEERQA" in cohort:
        return load_peerqa_sections(paper_id)
    split = "dev" if "DEV" in cohort else "train"
    return load_qasper_sections(paper_id, split=split)


# -----------------------------------------------------------------------------
# Unit Building & Ranking Helpers
# -----------------------------------------------------------------------------
def build_units_by_strategy(sections: List[Dict[str, Any]], strategy: str, paper_id: str) -> List[Dict[str, Any]]:
    if strategy == "hierarchical":
        return chunk_hierarchical(sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id)
    if strategy == "section_overlap":
        return chunk_sections(sections, strategy="section_overlap", max_tokens=400, overlap=80)
    if strategy == "fixed_size":
        return chunk_fixed_size(sections, max_tokens=400, paper_id=paper_id)
    raise ValueError(f"Unknown chunking strategy: {strategy}")


def get_candidate_pool(units: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    """Candidate pool over which total relevant chunks R_q is counted."""
    if strategy != "hierarchical":
        return units
    seen, out = set(), []
    for u in units:
        pid = u.get("parent_id")
        if pid and pid not in seen:
            seen.add(pid)
            out.append({"text": u.get("parent_text") or u["text"], "parent_id": pid})
    return out


def rank_units_and_evaluate(
    strategy: str,
    units: List[Dict[str, Any]],
    scores: np.ndarray,
    paper_id: str,
    evidence: List[str],
    cand_pool: List[Dict[str, Any]],
    tau: float = 0.50,
) -> Optional[Dict[str, float]]:
    """Ranks units and calculates IR metrics directly without context truncation.

    Returns None when the question has no relevant chunk in this chunker's
    candidate pool (r_q == 0); the caller counts these as skipped.
    """
    K = 20
    r_q = count_relevant_chunks(cand_pool, paper_id, "", evidence, tau=tau)
    if r_q <= 0:
        return None
    ranked = np.argsort(-scores)
    if strategy == "hierarchical":
        # Small-to-big retrieval: expand child hits to unique parent sections in rank order
        seen, items = set(), []
        for idx in ranked:
            pid = units[idx].get("parent_id")
            if pid and pid not in seen:
                seen.add(pid)
                items.append({"text": units[idx].get("parent_text") or units[idx]["text"], "parent_id": pid})
                if len(items) == K:
                    break
    else:
        # Flat chunk retrieval
        items = [units[i] for i in ranked[:K]]
    relevances = [1 if is_chunk_hit(u, paper_id, "", evidence, tau=tau) else 0 for u in items]
    metrics = compute_all_ir_metrics(relevances, r_q)
    metrics["r_q"] = r_q
    return metrics


# -----------------------------------------------------------------------------
# Main Evaluation Engine
# -----------------------------------------------------------------------------
def run_dataset_retrieval_benchmark(
    cohort_name: str,
    chunkers: List[str],
    models: List[str],
    limit: Optional[int] = None,
    out_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    print(f"\n{'='*70}\nStarting Phase 2 Retrieval Evaluation: Cohort [{cohort_name}]\n{'='*70}", flush=True)

    cohort = rr.load_cohort(cohort_name)
    groups = rr.group_items(cohort)
    papers = sorted(groups)[:limit] if limit else sorted(groups)
    print(f"Loaded cohort {cohort_name}: {len(papers)} papers, "
          f"{sum(len(groups[p]) for p in papers)} questions", flush=True)

    tag = cohort_name.lower().replace("-", "_")
    summary: Dict[str, Any] = {
        "cohort": cohort_name,
        "n_papers": len(papers),
        "n_questions": sum(len(groups[p]) for p in papers),
        "chunkers": chunkers,
        "models": models,
        "combinations": {},
        "failures": [],
    }

    per_query_rows = []
    t_start = time.time()

    # Pre-extract sections for all papers in cohort
    print("Pre-loading sections...", flush=True)
    paper_sections: Dict[str, List[Dict[str, Any]]] = {}
    for pid in papers:
        secs = load_sections_for_cohort(cohort_name, pid)
        if not secs:
            summary["failures"].append({"paper_id": pid, "error": "No sections loaded"})
            continue
        paper_sections[pid] = secs

    valid_papers = [p for p in papers if p in paper_sections]
    print(f"Sections ready for {len(valid_papers)}/{len(papers)} papers.", flush=True)

    # Pre-build units per chunker
    chunker_units: Dict[str, Dict[str, List[Dict[str, Any]]]] = {st: {} for st in chunkers}
    chunker_cands: Dict[str, Dict[str, List[Dict[str, Any]]]] = {st: {} for st in chunkers}
    for st in chunkers:
        for pid in valid_papers:
            u = build_units_by_strategy(paper_sections[pid], st, pid)
            if u:
                chunker_units[st][pid] = u
                chunker_cands[st][pid] = get_candidate_pool(u, st)
            else:
                summary["failures"].append({"paper_id": pid, "strategy": st, "error": "No units built"})

    # Evaluate per model
    for model_name in models:
        m_short = [k for k, v in MODEL_MAP.items() if v == model_name]
        m_label = m_short[0] if m_short else model_name.split("/")[-1]
        print(f"\n--- Model: {model_name} ({m_label}) ---", flush=True)

        try:
            rp.get_model(model_name)
        except Exception as e:
            print(f"Error loading model {model_name}: {e}\nSkipping this model.", flush=True)
            summary["failures"].append({"model": model_name, "error": f"Failed to load: {e}"})
            continue

        # Warm-up first so lazy load / CUDA init doesn't pollute latency numbers
        try:
            rp.embed(model_name, ["warmup text for retriever"], is_query=True, batch_size=1)
        except Exception as e:
            print(f"Warning: model warm-up error: {e}", flush=True)

        # Query latency: real uncached single-query embeds, once per model
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
            indexing_times: List[float] = []
            total_units_indexed = 0
            skipped = 0

            for pid in valid_papers:
                units = chunker_units[st].get(pid)
                cand_pool = chunker_cands[st].get(pid)
                if not units or not cand_pool:
                    continue

                texts = [u["text"] for u in units]
                total_units_indexed += len(texts)

                # Embed chunks (key includes model label + content hash so changing
                # chunk params or switching models never reuses stale embeddings)
                h = hashlib.md5("\x00".join(texts).encode()).hexdigest()[:8]
                t_idx0 = time.perf_counter()
                um = rp.cached_embed(model_name, texts, False, f"{tag}_{pid}_{st}_{m_label}_{h}")
                indexing_times.append(time.perf_counter() - t_idx0)

                items = groups[pid]
                questions = [it["question"] for it in items]

                # Embed questions
                qv = rp.cached_embed(model_name, questions, True, f"{tag}_{pid}_{m_label}")

                # Rank & evaluate
                for it, q in zip(items, qv):
                    scores = um @ q
                    ir_m = rank_units_and_evaluate(
                        strategy=st,
                        units=units,
                        scores=scores,
                        paper_id=pid,
                        evidence=it.get("retrieval_evidence", []),
                        cand_pool=cand_pool,
                    )
                    if ir_m is None:
                        skipped += 1
                        continue

                    for mk, mv in ir_m.items():
                        combo_metrics[mk].append(mv)

                    row = {
                        "cohort": cohort_name,
                        "paper_id": pid,
                        "question_id": it.get("question_id"),
                        "chunker": st,
                        "model": model_name,
                        "model_label": m_label,
                        "combination": combo_key,
                        "metrics": ir_m,
                    }
                    per_query_rows.append(row)

            # Summarize combination performance
            n_eval = len(combo_metrics["ndcg_10"])
            combo_summary = {
                "chunker": st,
                "model": model_name,
                "model_label": m_label,
                "evaluated_questions": n_eval,
                "skipped_no_relevant": skipped,
                "means": {mk: round(float(np.mean(combo_metrics[mk])), 4) if combo_metrics[mk] else 0.0
                          for mk in IR_METRIC_KEYS},
                "total_units": total_units_indexed,
                "indexing_throughput_chunks_per_s": round(total_units_indexed / max(1e-4, sum(indexing_times)), 2),
            }
            summary["combinations"][combo_key] = combo_summary
            print(f"    Done {combo_key}: nDCG@10={combo_summary['means']['ndcg_10']}, "
                  f"MRR@10={combo_summary['means']['mrr_10']}, "
                  f"Recall@10={combo_summary['means']['recall_10']}, "
                  f"P@5={combo_summary['means']['precision_5']}, "
                  f"n={n_eval}, skipped={skipped}", flush=True)

        # Record model latencies
        summary[f"model_latency_{m_label}"] = {
            "p50_ms": round(float(np.percentile(model_latencies, 50)), 2) if model_latencies else 0.0,
            "p95_ms": round(float(np.percentile(model_latencies, 95)), 2) if model_latencies else 0.0,
        }

    summary["elapsed_s"] = round(time.time() - t_start, 1)

    # Write artifacts if out_dir specified
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        with open(out_dir / "per_query.jsonl", "w", encoding="utf-8") as f:
            for r in per_query_rows:
                f.write(json.dumps(r) + "\n")
        generate_markdown_report(summary, out_dir / "REPORT.md")
        print(f"\nArtifacts written to {out_dir}", flush=True)

    return summary


# -----------------------------------------------------------------------------
# Markdown Report Generator
# -----------------------------------------------------------------------------
def generate_markdown_report(summary: Dict[str, Any], report_path: Path):
    combos = summary.get("combinations", {})
    if not combos:
        return

    # Sort combos by nDCG@10 descending
    sorted_combos = sorted(combos.items(), key=lambda x: x[1]["means"]["ndcg_10"], reverse=True)

    lines = [
        f"# Phase 2: Retrieval Evaluation Report — Cohort [{summary.get('cohort')}]",
        "",
        f"- **Cohort:** {summary.get('cohort')}",
        f"- **Evaluated Papers:** {summary.get('n_papers')}",
        f"- **Evaluated Questions:** {summary.get('n_questions')}",
        f"- **Total Combinations Tested:** {len(combos)} (Chunkers × Embedders)",
        f"- **Evaluation Time:** {summary.get('elapsed_s')} s",
        "",
        "## 1. Overall Leaderboard (Ranked by nDCG@10)",
        "",
        "| Rank | Combination | Chunker | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | N | Skipped | Throughput (chunks/s) |",
        "| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for rank_idx, (ck, cdata) in enumerate(sorted_combos, 1):
        m = cdata["means"]
        lines.append(
            f"| {rank_idx} | **{ck}** | `{cdata['chunker']}` | `{cdata['model_label']}` | "
            f"**{m['ndcg_10']:.4f}** | {m['mrr_10']:.4f} | {m['map_10']:.4f} | "
            f"{m['recall_10']:.4f} | {m['recall_5']:.4f} | {m['precision_5']:.4f} | "
            f"{m['hit_1']:.4f} | {cdata.get('evaluated_questions', 0)} | "
            f"{cdata.get('skipped_no_relevant', 0)} | "
            f"{cdata.get('indexing_throughput_chunks_per_s', 0):.1f} |"
        )

    lines.extend([
        "",
        "## 2. Chunking Method Comparison (Averaged across all embedding models)",
        "",
        "| Chunker | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Throughput (chunks/s) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    chunker_groups = defaultdict(list)
    for ck, cdata in combos.items():
        chunker_groups[cdata["chunker"]].append(cdata)

    for st in summary.get("chunkers", []):
        group = chunker_groups.get(st, [])
        if group:
            mean_ndcg = np.mean([g["means"]["ndcg_10"] for g in group])
            mean_mrr = np.mean([g["means"]["mrr_10"] for g in group])
            mean_rec = np.mean([g["means"]["recall_10"] for g in group])
            mean_prec = np.mean([g["means"]["precision_5"] for g in group])
            mean_hit = np.mean([g["means"]["hit_1"] for g in group])
            mean_thr = np.mean([g.get("indexing_throughput_chunks_per_s", 0) for g in group])
            lines.append(
                f"| `{st}` | **{mean_ndcg:.4f}** | {mean_mrr:.4f} | {mean_rec:.4f} | "
                f"{mean_prec:.4f} | {mean_hit:.4f} | {mean_thr:.1f} |"
            )

    lines.extend([
        "",
        "## 3. Embedding Model Comparison (Averaged across all chunking methods)",
        "",
        "| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query Latency P50 (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    model_groups = defaultdict(list)
    for ck, cdata in combos.items():
        model_groups[cdata["model_label"]].append(cdata)

    for ml, group in model_groups.items():
        mean_ndcg = np.mean([g["means"]["ndcg_10"] for g in group])
        mean_mrr = np.mean([g["means"]["mrr_10"] for g in group])
        mean_rec = np.mean([g["means"]["recall_10"] for g in group])
        mean_prec = np.mean([g["means"]["precision_5"] for g in group])
        mean_hit = np.mean([g["means"]["hit_1"] for g in group])
        lat = summary.get(f"model_latency_{ml}", {})
        p50 = lat.get("p50_ms", "—")
        lines.append(
            f"| `{ml}` | **{mean_ndcg:.4f}** | {mean_mrr:.4f} | {mean_rec:.4f} | "
            f"{mean_prec:.4f} | {mean_hit:.4f} | {p50} |"
        )

    lines.extend([
        "",
        "## 4. Key Findings",
        "",
        f"1. **Champion Combination:** `{sorted_combos[0][0]}` achieved highest nDCG@10 of **{sorted_combos[0][1]['means']['ndcg_10']:.4f}** with MRR@10 of **{sorted_combos[0][1]['means']['mrr_10']:.4f}**.",
        "2. **Metric Integrity:** Pure Information Retrieval (IR) metrics evaluated directly on ranked candidate units without context concatenation or token-budget proxies.",
        "3. **Question Set:** Questions with no relevant chunk in a chunker's candidate pool are skipped (see Skipped column); compare chunkers only when N/Skipped are similar.",
        "",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Phase 2 Retrieval Evaluation: Chunking x Embedding")
    ap.add_argument("--dataset", choices=["qasper", "peerqa", "all"], default="all",
                    help="Target dataset: qasper, peerqa, or all (default: all)")
    ap.add_argument("--cohort", default=None,
                    help="Specific cohort name (e.g. C-RET, C-RET-150, PEERQA-PDF, PEERQA-TEXT)")
    ap.add_argument("--chunkers", default=None,
                    help="Comma-separated chunkers (default: hierarchical,section_overlap,fixed_size)")
    ap.add_argument("--models", default=None,
                    help="Comma-separated model names or short keys (default: e5,qwen,gemma,arctic,modernbert)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Number of papers to evaluate (useful for smoke tests)")
    args = ap.parse_args()

    # Parse chunkers
    chunkers = args.chunkers.split(",") if args.chunkers else CHUNKERS

    # Parse models
    if args.models:
        selected_models = []
        for m in args.models.split(","):
            m = m.strip()
            selected_models.append(MODEL_MAP.get(m, m))
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
        sub_dir = ARTIFACTS_DIR / ch_name.lower().replace("-", "_")
        if args.limit:
            sub_dir = sub_dir / f"smoke_{args.limit}"
        res = run_dataset_retrieval_benchmark(
            cohort_name=ch_name,
            chunkers=chunkers,
            models=selected_models,
            limit=args.limit,
            out_dir=sub_dir,
        )
        all_results[ch_name] = res

    # Generate top-level combined summary
    combined_summary_path = ARTIFACTS_DIR / ("summary.json" if not args.limit else f"summary_smoke_{args.limit}.json")
    combined_summary_path.parent.mkdir(parents=True, exist_ok=True)
    combined_summary_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\nAll Phase 2 retrieval benchmarks complete! Overall summary written to {combined_summary_path}")


if __name__ == "__main__":
    main()