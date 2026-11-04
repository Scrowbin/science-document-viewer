"""
Regression Evaluation & Verification Script: Hierarchical Production Parity.
Compares production hierarchical (Small-to-Big) retrieval against section_overlap
across the RQ2 benchmark setup (47 Dev papers, 127 questions, tau=0.50, budget=1600 tokens).
Measures accuracy (nDCG@10, nDCG@4, Recall@20, MRR@10), query latency (P50/P95), and index footprint.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

import django
django.setup()

from apps.documents.services.chunkers import chunk_document_unified, estimate_tokens
from apps.documents.services.chunking_utils import extract_sections_from_pdf
from apps.documents.services.rag_service import RagService
from eval_common.relevance import count_relevant_chunks, is_chunk_hit
from eval_common.stats import compute_mrr, compute_ndcg, compute_recall


def run_production_parity_eval(limit: Optional[int] = None) -> Dict[str, Any]:
    torch.set_num_threads(4)
    print("=" * 80)
    print("PRODUCTION RETRIEVAL PARITY EVALUATION: HIERARCHICAL vs SECTION_OVERLAP")
    print("Scope: 47 Dev Papers, 127 Questions, Context Budget: 1,600 Tokens, tau=0.50")
    print("Vector Store: Local Qdrant (in-memory) | Embedding: intfloat/e5-small-v2")
    print("=" * 80)

    # 1. Load ground truth
    dev_split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(dev_split_path, "r", encoding="utf-8") as f:
        dev_papers = json.load(f)["dev_papers"]
    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)

    pdf_dirs = [
        WORKSPACE_ROOT / "eval" / "pdfs" / "dev",
        WORKSPACE_ROOT / "eval" / "data" / "pdfs",
        WORKSPACE_ROOT / "sample_papers",
    ]
    available_pdfs: Dict[str, Path] = {}
    for aid in dev_papers:
        for d in pdf_dirs:
            cand = d / f"{aid}.pdf"
            if cand.exists() and cand.stat().st_size > 10000:
                available_pdfs[aid] = cand
                break

    paper_ids = [aid for aid in dev_papers if aid in available_pdfs]
    if limit:
        paper_ids = paper_ids[:limit]

    paper_queries: Dict[str, List[Dict[str, Any]]] = {}
    for q in qa_all:
        aid = q.get("paper_arxiv_id")
        if aid in paper_ids and q.get("question_type") != "unanswerable":
            paper_queries.setdefault(aid, []).append(q)

    total_queries = sum(len(qs) for qs in paper_queries.values())
    print(f"Evaluated Papers: {len(paper_ids)} | Evaluated Questions: {total_queries}")

    rag = RagService(in_memory=True)

    # Containers for metrics
    strategies = ["section_overlap", "hierarchical"]
    results: Dict[str, Dict[str, Any]] = {
        st: {
            "ndcg10": [],
            "ndcg4": [],
            "recall20": [],
            "mrr10": [],
            "budget_coverage": [],
            "latencies_ms": [],
            "total_chunks": 0,
            "total_parents": 0,
        }
        for st in strategies
    }

    t0_all = time.perf_counter()

    for p_idx, aid in enumerate(paper_ids, start=1):
        pdf_path = available_pdfs[aid]
        queries = paper_queries.get(aid, [])
        if not queries:
            continue

        sections = extract_sections_from_pdf(str(pdf_path))

        # Test both strategies on this paper
        for st in strategies:
            coll_name = f"test_{st}_{aid.replace('.', '_')}"

            # 1. Chunk document
            chunks = chunk_document_unified(
                sections=sections,
                strategy=st,
                max_tokens=400,
                overlap=80,
                paper_id=aid,
            )
            for c in chunks:
                c["paper_arxiv_id"] = aid
                c["document_id"] = aid

            # 2. Index into Qdrant
            rag.index_chunks(collection_name=coll_name, chunks=chunks, recreate=True)
            results[st]["total_chunks"] += len(chunks)

            parents_col = f"{coll_name}_parents"
            if rag.client.collection_exists(parents_col):
                p_count = rag.client.count(collection_name=parents_col).count
                results[st]["total_parents"] += p_count

            # 3. For relevance evaluation, get unique evaluation units
            if st == "hierarchical":
                unique_parents: Dict[str, Dict[str, Any]] = {}
                for c in chunks:
                    pid = c.get("parent_id")
                    if pid and pid not in unique_parents:
                        unique_parents[pid] = {
                            "chunk_id": pid,
                            "paper_arxiv_id": aid,
                            "section": c.get("section", ""),
                            "page": c.get("page", 1),
                            "text": c.get("parent_text", ""),
                            "token_count": c.get("parent_tokens", estimate_tokens(c.get("parent_text", ""))),
                        }
                eval_units = list(unique_parents.values())
            else:
                eval_units = chunks

            # 4. Run queries through production retrieval path
            for q in queries:
                q_text = q["question"]
                quote = q.get("verbatim_evidence_quote", "")
                ev_list = q.get("evidence_list", [])

                R_q = count_relevant_chunks(eval_units, aid, quote, ev_list, tau=0.50)

                t_start = time.perf_counter()
                if st == "hierarchical":
                    retrieved = rag.search_hierarchical(
                        collection_name=coll_name,
                        query=q_text,
                        token_budget=1600,
                        candidate_pool=20,
                        max_parent_tokens=800,
                        filter_arxiv_id=aid,
                    )
                else:
                    retrieved = rag.search_dense_with_token_budget(
                        collection_name=coll_name,
                        query=q_text,
                        token_budget=1600,
                        candidate_pool=25,
                        filter_arxiv_id=aid,
                        strategy="section_overlap",
                    )
                t_lat = (time.perf_counter() - t_start) * 1000.0
                results[st]["latencies_ms"].append(t_lat)

                # Extract ranked units for nDCG / Recall
                ranked_items = [item for score, item in retrieved]
                ranked_rels = [
                    1 if is_chunk_hit(item, aid, quote, ev_list, tau=0.50) else 0
                    for item in ranked_items
                ]

                ndcg4 = compute_ndcg(ranked_rels, R_q, k=4)
                ndcg10 = compute_ndcg(ranked_rels, R_q, k=10)
                rec20 = compute_recall(ranked_rels, R_q, k=20)
                mrr10 = compute_mrr(ranked_rels, k=10)
                has_ev = 1 if any(ranked_rels) else 0

                results[st]["ndcg4"].append(ndcg4)
                results[st]["ndcg10"].append(ndcg10)
                results[st]["recall20"].append(rec20)
                results[st]["mrr10"].append(mrr10)
                results[st]["budget_coverage"].append(has_ev)

        if p_idx % 10 == 0 or p_idx == len(paper_ids):
            print(f"[{p_idx}/{len(paper_ids)}] Processed arXiv:{aid}...")

    total_time = time.perf_counter() - t0_all
    print(f"\nEvaluation completed in {total_time:.2f} seconds.")

    # Summarize metrics
    summary = {}
    for st in strategies:
        lats = results[st]["latencies_ms"]
        p50 = np.percentile(lats, 50) if lats else 0.0
        p95 = np.percentile(lats, 95) if lats else 0.0
        summary[st] = {
            "total_chunks": results[st]["total_chunks"],
            "total_parents": results[st]["total_parents"],
            "ndcg10": round(float(np.mean(results[st]["ndcg10"])), 4),
            "ndcg4": round(float(np.mean(results[st]["ndcg4"])), 4),
            "recall20": round(float(np.mean(results[st]["recall20"])), 4),
            "mrr10": round(float(np.mean(results[st]["mrr10"])), 4),
            "budget_coverage_pct": round(float(np.mean(results[st]["budget_coverage"])) * 100.0, 2),
            "latency_p50_ms": round(p50, 2),
            "latency_p95_ms": round(p95, 2),
        }

    print("\n" + "=" * 80)
    print("RETRIEVAL PARITY & BENCHMARK COMPARISON RESULTS")
    print("=" * 80)
    print(f"{'Strategy':<20} | {'nDCG@10':<8} | {'nDCG@4':<8} | {'Recall@20':<10} | {'MRR@10':<8} | {'P50 (ms)':<9} | {'P95 (ms)':<9} | {'Chunks':<8} | {'Parents':<8}")
    print("-" * 105)
    for st in strategies:
        d = summary[st]
        print(f"{st:<20} | {d['ndcg10']:<8.4f} | {d['ndcg4']:<8.4f} | {d['recall20']:<10.4f} | {d['mrr10']:<8.4f} | {d['latency_p50_ms']:<9.2f} | {d['latency_p95_ms']:<9.2f} | {d['total_chunks']:<8} | {d['total_parents']:<8}")
    print("=" * 105)

    # Save artifact
    out_dir = WORKSPACE_ROOT / "eval" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "hierarchical_production_parity.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Artifact saved to: {out_path}")

    return summary


if __name__ == "__main__":
    run_production_parity_eval()
