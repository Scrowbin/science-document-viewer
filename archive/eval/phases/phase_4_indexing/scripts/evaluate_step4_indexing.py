"""
Step 4 Evaluation: Embedded Vector Store & Exact Search Characterization
Evaluates Qdrant embedded mode (local SQLite-backed exact search) against NumPy BLAS
exact brute-force cosine nearest neighbor oracle using champion model intfloat/e5-small-v2 (384-d, FP32).

Methodological Notes & Audit Remediation (Priority 2):
  1. Engine Reality: Qdrant local embedded mode (QdrantClient(path=...)) executes exact
     brute-force vector scanning by design; HNSW graph parameters (M, ef_construct, ef_search)
     and payload indexes are inert in local mode.
  2. Non-Fatal Tokenization Audit (Task 2A): Dynamically reads model.max_seq_length (512),
     audits truncation rate, logs a warning if >= 1.0% without aborting execution, and records
     a `within_budget` boolean in the output artifact.
  3. Latency Methodology (Task 2C): Implements a 10-query warm-up phase per regime, followed by
     5 timed passes over all 114 queries (570 pooled timings per regime). Reports pooled P50, P95,
     P99 latencies alongside per-pass P50 ranges. Results make no unmeasured 'fastest' claims.
  4. Measured Claims Only (Task 2B): Rewords latency and memory descriptions as measured facts
     or explicitly designated unprofiled hypotheses.
  5. Parity Rigor: Verifies chunk ID set equality and float32 score parity (|s_qdrant - s_blas| <= 1e-5)
     across all 114 held-out queries.
  6. Disclosure: The 48 held-out papers (1,119 chunks, 114 queries) are evaluated here for
     vector store infrastructure benchmarking.
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKSPACE_ROOT / "backend" / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from apps.documents.services.chunking_utils import chunk_sections

MODEL_NAME = "intfloat/e5-small-v2"
TOP_K_PRIMARY = 4
TOP_K_SECONDARY = 20
NUM_LATENCY_PASSES = 5
NUM_WARMUP_QUERIES = 10


def load_held_out_data():
    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    held_out_aids = set(split_data["held_out_papers"])

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)
    held_out_corpus = {k: v for k, v in corpus_all.items() if k in held_out_aids}

    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)
    held_out_queries = [
        q for q in qa_all
        if q.get("paper_arxiv_id") in held_out_aids and q.get("question_type") != "unanswerable"
    ]
    return held_out_aids, held_out_corpus, held_out_queries


def build_chunks(corpus, strategy="section_overlap", max_tokens=350, overlap=70):
    chunks = []
    for aid, doc in corpus.items():
        sec_list = doc.get("sections", [])
        base_chunks = chunk_sections(sec_list, strategy=strategy,
                                     max_tokens=max_tokens, overlap=overlap)
        for c_idx, c in enumerate(base_chunks):
            c["chunk_id"] = f"{aid}_c_{c_idx}"
            c["chunk_int_id"] = len(chunks)
            c["paper_arxiv_id"] = aid
            c["document_id"] = aid
            chunks.append(c)
    return chunks


def get_dir_size(path: Path) -> float:
    total = 0
    if path.exists():
        for p in path.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
    return total / (1024 * 1024)  # MB


def main():
    print("=" * 100)
    print("STEP 4: EMBEDDED VECTOR STORE & EXACT SEARCH BENCHMARK (AUDITED)")
    print(f"Embedding Model: {MODEL_NAME} (384-d, FP32, prefixes: 'passage: ' / 'query: ')")
    print("Engine: Qdrant Local Embedded Mode (SQLite-backed Exact Search)")
    print("=" * 100)

    # 1. Load Data
    held_out_aids, held_out_corpus, held_out_queries = load_held_out_data()
    print(f"[DATA] Loaded {len(held_out_aids)} held-out papers, {len(held_out_queries)} queries.")

    chunks = build_chunks(held_out_corpus)
    print(f"[CORPUS] Built {len(chunks)} chunks across {len(held_out_corpus)} held-out papers.")

    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    # 2. Task 2A: Check Chunk Token Lengths Dynamically from model.max_seq_length
    model = SentenceTransformer(MODEL_NAME)
    seq_limit = int(getattr(model, "max_seq_length", 512))
    tokenizer = model.tokenizer

    print(f"\n[CHECK 1] Auditing chunk subword lengths against model.max_seq_length ({seq_limit} tokens)...")
    passages = ["passage: " + c["text"] for c in chunks]
    tokenized_lengths = [len(tokenizer.encode(p, truncation=False)) for p in passages]

    subword_mean = float(np.mean(tokenized_lengths))
    subword_p50 = float(np.percentile(tokenized_lengths, 50))
    subword_p90 = float(np.percentile(tokenized_lengths, 90))
    subword_p95 = float(np.percentile(tokenized_lengths, 95))
    subword_max = int(np.max(tokenized_lengths))
    num_exceeding_limit = sum(1 for l in tokenized_lengths if l > seq_limit)
    pct_exceeding_limit = (num_exceeding_limit / len(tokenized_lengths)) * 100.0
    within_budget = bool(pct_exceeding_limit < 1.0)

    print(f"  Subword Stats: Mean={subword_mean:.1f}, P50={subword_p50:.1f}, P90={subword_p90:.1f}, P95={subword_p95:.1f}, Max={subword_max}")
    print(f"  Chunks > {seq_limit} Tokens: {num_exceeding_limit} / {len(tokenized_lengths)} ({pct_exceeding_limit:.2f}%)")

    # Non-fatal warning instead of hard assert (Task 2A)
    if not within_budget:
        print(f"  [WARNING] Truncation rate ({pct_exceeding_limit:.2f}%) exceeds nominal 1.0% threshold.")
    else:
        print(f"  [PASSED] Truncation rate ({pct_exceeding_limit:.2f}%) is within 1.0% budget.")

    # 3. Embedding Generation with Cache Integrity Validation
    cache_dir = WORKSPACE_ROOT / "eval" / "prepared"
    doc_cache = cache_dir / "step4_e5_doc_embs.npy"
    query_cache = cache_dir / "step4_e5_query_embs.npy"

    doc_embs: np.ndarray
    if doc_cache.exists():
        loaded = np.load(doc_cache)
        if loaded.shape == (len(chunks), 384):
            print(f"[CACHE] Loaded chunk embeddings from {doc_cache.name} (shape: {loaded.shape}).")
            doc_embs = loaded
        else:
            print(f"[CACHE INVALID] Shape mismatch in {doc_cache.name} ({loaded.shape} vs ({len(chunks)}, 384)). Re-encoding...")
            doc_embs = model.encode(passages, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
            np.save(doc_cache, doc_embs)
    else:
        print(f"[EMBED] Encoding {len(chunks)} chunks with prefix 'passage: '...")
        doc_embs = model.encode(passages, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
        np.save(doc_cache, doc_embs)

    queries_text = ["query: " + q["question"] for q in held_out_queries]
    q_embs: np.ndarray
    if query_cache.exists():
        loaded_q = np.load(query_cache)
        if loaded_q.shape == (len(held_out_queries), 384):
            print(f"[CACHE] Loaded query embeddings from {query_cache.name} (shape: {loaded_q.shape}).")
            q_embs = loaded_q
        else:
            print(f"[CACHE INVALID] Shape mismatch in {query_cache.name}. Re-encoding...")
            q_embs = model.encode(queries_text, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
            np.save(query_cache, q_embs)
    else:
        print(f"[EMBED] Encoding {len(held_out_queries)} queries with prefix 'query: '...")
        q_embs = model.encode(queries_text, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
        np.save(query_cache, q_embs)

    # Invariant Check 1: Normalization
    norms = np.linalg.norm(doc_embs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5), f"Embedding vectors are not unit normalized! Min: {min(norms)}, Max: {max(norms)}"
    print(f"[INVARIANT 1 PASSED] All {len(doc_embs)} chunk vectors verified unit normalized (||v||_2 = 1.0 +- 1e-5).")

    # 4. Compute NumPy BLAS Exact Ground Truth Oracle
    print("\n[ORACLE] Computing NumPy BLAS exact cosine nearest neighbors...")
    exact_wp_top4: List[List[int]] = []
    exact_wp_top20: List[List[int]] = []
    exact_wp_scores: List[List[float]] = []

    exact_xp_top4: List[List[int]] = []
    exact_xp_top20: List[List[int]] = []
    exact_xp_scores: List[List[float]] = []

    for q_idx, q in enumerate(held_out_queries):
        aid = q["paper_arxiv_id"]
        q_vec = q_embs[q_idx]

        # Regime A: Within-paper candidate pool
        cand_indices = paper_chunk_indices.get(aid, [])
        if cand_indices:
            cand_matrix = doc_embs[cand_indices]
            sims = np.dot(cand_matrix, q_vec)
            sorted_local = np.argsort(-sims)
            exact_wp_top4.append([cand_indices[i] for i in sorted_local[:TOP_K_PRIMARY]])
            exact_wp_top20.append([cand_indices[i] for i in sorted_local[:TOP_K_SECONDARY]])
            exact_wp_scores.append([float(sims[i]) for i in sorted_local[:TOP_K_SECONDARY]])
        else:
            exact_wp_top4.append([])
            exact_wp_top20.append([])
            exact_wp_scores.append([])

        # Regime B: Global multi-paper corpus
        all_sims = np.dot(doc_embs, q_vec)
        sorted_global = np.argsort(-all_sims)
        exact_xp_top4.append([int(i) for i in sorted_global[:TOP_K_PRIMARY]])
        exact_xp_top20.append([int(i) for i in sorted_global[:TOP_K_SECONDARY]])
        exact_xp_scores.append([float(all_sims[i]) for i in sorted_global[:TOP_K_SECONDARY]])

    print(f"[ORACLE] Generated exact ground truth for all {len(held_out_queries)} queries.")

    # 5. Build Qdrant Embedded Collection & Characterize Footprint
    temp_dir = Path(tempfile.mkdtemp(prefix="qdrant_step4_exact_"))
    try:
        db_path = temp_dir / "qdrant_db"
        coll_name = "step4_heldout_exact"

        print(f"\n[QDRANT BUILD] Initializing Qdrant embedded collection at {db_path}...")
        tracemalloc.start()
        t0_build = time.perf_counter()

        client = QdrantClient(path=str(db_path))
        client.create_collection(
            collection_name=coll_name,
            vectors_config=qmodels.VectorParams(size=384, distance=qmodels.Distance.COSINE),
        )

        points = [
            qmodels.PointStruct(
                id=i,
                vector=doc_embs[i].tolist(),
                payload={
                    "chunk_id": chunks[i]["chunk_id"],
                    "document_id": chunks[i]["document_id"],
                    "paper_arxiv_id": chunks[i]["paper_arxiv_id"],
                    "text": chunks[i]["text"][:100],
                },
            )
            for i in range(len(chunks))
        ]
        client.upsert(coll_name, points)

        build_time_s = time.perf_counter() - t0_build
        peak_py_ram_bytes, _ = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        disk_mb = get_dir_size(db_path)
        peak_ram_mb = peak_py_ram_bytes / (1024 * 1024)

        print(f"[QDRANT BUILD COMPLETED] Indexed {len(points)} chunks in {build_time_s:.2f}s.")
        print(f"  Disk Footprint: {disk_mb:.2f} MB (SQLite database + payloads)")
        print(f"  Traced Python Heap: {peak_ram_mb:.2f} MB")

        # 6. Task 2C: Warm-up Phase
        print(f"\n[WARM-UP] Executing {NUM_WARMUP_QUERIES} untimed warm-up queries per regime to eliminate JIT/cold-start artifacts...")
        for q_idx in range(min(NUM_WARMUP_QUERIES, len(held_out_queries))):
            q_vec = q_embs[q_idx].tolist()
            aid = held_out_queries[q_idx]["paper_arxiv_id"]
            wp_filter = qmodels.Filter(
                must=[qmodels.FieldCondition(key="paper_arxiv_id", match=qmodels.MatchValue(value=aid))]
            )
            _ = client.query_points(collection_name=coll_name, query=q_vec, query_filter=wp_filter, limit=TOP_K_SECONDARY)
            _ = client.query_points(collection_name=coll_name, query=q_vec, limit=TOP_K_SECONDARY)
        print("[WARM-UP COMPLETED] Engine caches primed.")

        # 7. Evaluate Exact Parity and Multi-Pass Latency (Task 2C)
        print("\n" + "=" * 90)
        print(f"[PARITY & LATENCY BENCHMARK] Evaluating {NUM_LATENCY_PASSES} timed passes across {len(held_out_queries)} queries...")
        print("=" * 90)

        wp_id_matches_4 = 0
        wp_id_matches_20 = 0
        wp_score_max_delta = 0.0

        xp_id_matches_4 = 0
        xp_id_matches_20 = 0
        xp_score_max_delta = 0.0

        all_wp_latencies_ms: List[float] = []
        all_xp_latencies_ms: List[float] = []
        wp_pass_p50s: List[float] = []
        xp_pass_p50s: List[float] = []

        for pass_num in range(NUM_LATENCY_PASSES):
            pass_wp_lats: List[float] = []
            pass_xp_lats: List[float] = []

            for q_idx, q in enumerate(held_out_queries):
                q_vec = q_embs[q_idx].tolist()
                aid = q["paper_arxiv_id"]

                # --- Regime A: Within-Paper Filtered Search ---
                wp_filter = qmodels.Filter(
                    must=[qmodels.FieldCondition(key="paper_arxiv_id", match=qmodels.MatchValue(value=aid))]
                )
                t0 = time.perf_counter_ns()
                wp_res = client.query_points(
                    collection_name=coll_name,
                    query=q_vec,
                    query_filter=wp_filter,
                    limit=TOP_K_SECONDARY,
                )
                t1 = time.perf_counter_ns()
                lat_wp = (t1 - t0) / 1_000_000
                pass_wp_lats.append(lat_wp)
                all_wp_latencies_ms.append(lat_wp)

                # Parity checked on pass 0
                if pass_num == 0:
                    retrieved_wp_ids = [p.id for p in wp_res.points]
                    gt_wp_4 = set(exact_wp_top4[q_idx])
                    gt_wp_20 = set(exact_wp_top20[q_idx])

                    if set(retrieved_wp_ids[:TOP_K_PRIMARY]) == gt_wp_4:
                        wp_id_matches_4 += 1
                    if set(retrieved_wp_ids[:TOP_K_SECONDARY]) == gt_wp_20:
                        wp_id_matches_20 += 1

                    for rank, p in enumerate(wp_res.points[:TOP_K_PRIMARY]):
                        expected_score = exact_wp_scores[q_idx][rank]
                        wp_score_max_delta = max(wp_score_max_delta, abs(p.score - expected_score))

                # --- Regime B: Global Corpus Unfiltered Search ---
                t0 = time.perf_counter_ns()
                xp_res = client.query_points(
                    collection_name=coll_name,
                    query=q_vec,
                    limit=TOP_K_SECONDARY,
                )
                t1 = time.perf_counter_ns()
                lat_xp = (t1 - t0) / 1_000_000
                pass_xp_lats.append(lat_xp)
                all_xp_latencies_ms.append(lat_xp)

                if pass_num == 0:
                    retrieved_xp_ids = [p.id for p in xp_res.points]
                    gt_xp_4 = set(exact_xp_top4[q_idx])
                    gt_xp_20 = set(exact_xp_top20[q_idx])

                    if set(retrieved_xp_ids[:TOP_K_PRIMARY]) == gt_xp_4:
                        xp_id_matches_4 += 1
                    if set(retrieved_xp_ids[:TOP_K_SECONDARY]) == gt_xp_20:
                        xp_id_matches_20 += 1

                    for rank, p in enumerate(xp_res.points[:TOP_K_PRIMARY]):
                        expected_score = exact_xp_scores[q_idx][rank]
                        xp_score_max_delta = max(xp_score_max_delta, abs(p.score - expected_score))

            p50_wp = float(np.percentile(pass_wp_lats, 50))
            p50_xp = float(np.percentile(pass_xp_lats, 50))
            wp_pass_p50s.append(p50_wp)
            xp_pass_p50s.append(p50_xp)
            print(f"  Pass {pass_num+1}/{NUM_LATENCY_PASSES}: Regime A P50={p50_wp:.2f} ms | Regime B P50={p50_xp:.2f} ms")

        wp_recall_4_pct = (wp_id_matches_4 / len(held_out_queries)) * 100.0
        wp_recall_20_pct = (wp_id_matches_20 / len(held_out_queries)) * 100.0
        xp_recall_4_pct = (xp_id_matches_4 / len(held_out_queries)) * 100.0
        xp_recall_20_pct = (xp_id_matches_20 / len(held_out_queries)) * 100.0

        # Pooled latency statistics over all 570 samples
        wp_pooled_p50 = float(np.percentile(all_wp_latencies_ms, 50))
        wp_pooled_p95 = float(np.percentile(all_wp_latencies_ms, 95))
        wp_pooled_p99 = float(np.percentile(all_wp_latencies_ms, 99))

        xp_pooled_p50 = float(np.percentile(all_xp_latencies_ms, 50))
        xp_pooled_p95 = float(np.percentile(all_xp_latencies_ms, 95))
        xp_pooled_p99 = float(np.percentile(all_xp_latencies_ms, 99))

        print("\n" + "-" * 90)
        print("POOLED BENCHMARK RESULTS SUMMARY:")
        print("-" * 90)
        print(f"Regime A (Within-Paper Filtered, pool ~25):")
        print(f"  Exact ID Match Top-4 : {wp_id_matches_4}/{len(held_out_queries)} ({wp_recall_4_pct:.1f}%)")
        print(f"  Exact ID Match Top-20: {wp_id_matches_20}/{len(held_out_queries)} ({wp_recall_20_pct:.1f}%)")
        print(f"  Max Score Delta vs BLAS: {wp_score_max_delta:.2e} (float32 parity <= 1e-5)")
        print(f"  Pooled Latency (N={len(all_wp_latencies_ms)}): P50={wp_pooled_p50:.2f} ms, P95={wp_pooled_p95:.2f} ms, P99={wp_pooled_p99:.2f} ms")
        print(f"  Per-Pass P50 Range: [{min(wp_pass_p50s):.2f} ms, {max(wp_pass_p50s):.2f} ms]")

        print(f"\nRegime B (Global Corpus Unfiltered, pool 1,119):")
        print(f"  Exact ID Match Top-4 : {xp_id_matches_4}/{len(held_out_queries)} ({xp_recall_4_pct:.1f}%)")
        print(f"  Exact ID Match Top-20: {xp_id_matches_20}/{len(held_out_queries)} ({xp_recall_20_pct:.1f}%)")
        print(f"  Max Score Delta vs BLAS: {xp_score_max_delta:.2e} (float32 parity <= 1e-5)")
        print(f"  Pooled Latency (N={len(all_xp_latencies_ms)}): P50={xp_pooled_p50:.2f} ms, P95={xp_pooled_p95:.2f} ms, P99={xp_pooled_p99:.2f} ms")
        print(f"  Per-Pass P50 Range: [{min(xp_pass_p50s):.2f} ms, {max(xp_pass_p50s):.2f} ms]")

        assert wp_score_max_delta <= 1e-5, f"Within-paper score delta exceeded 1e-5: {wp_score_max_delta}"
        assert xp_score_max_delta <= 1e-5, f"Global corpus score delta exceeded 1e-5: {xp_score_max_delta}"
        print(f"\n[INVARIANT 2 PASSED] Float32 numerical parity verified across all 114 queries (delta <= 1e-5).")

        # 8. Task 2B & 2D: Serialize Clean Artifact
        out_json = WORKSPACE_ROOT / "eval" / "prepared" / "step4_indexing_pareto_results.json"
        benchmark_payload = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "embedding_model": MODEL_NAME,
            "dimension": 384,
            "engine": "qdrant_embedded_local",
            "storage_backend": "sqlite",
            "search_mode": "exact_brute_force",
            "hnsw_status": "inert_in_local_mode",
            "champion_config": None,  # Explicit: No HNSW config chosen; local mode is exact by design
            "notes": (
                "Audit Remediation: Qdrant local embedded mode uses SQLite exact brute-force search. "
                "HNSW parameters (M, ef_construct, ef_search) have no effect in local mode. "
                "This benchmark characterizes exact retrieval fidelity against NumPy BLAS across all 114 queries."
            ),
            "tokenization_audit": {
                "sequence_limit": seq_limit,
                "mean_subwords": round(subword_mean, 1),
                "p50_subwords": round(subword_p50, 1),
                "p90_subwords": round(subword_p90, 1),
                "p95_subwords": round(subword_p95, 1),
                "max_subwords": subword_max,
                "num_exceeding_limit": num_exceeding_limit,
                "pct_exceeding_limit": round(pct_exceeding_limit, 2),
                "within_budget": within_budget,
            },
            "resource_footprint": {
                "num_chunks": len(chunks),
                "disk_mb": round(disk_mb, 2),
                "peak_traced_ram_mb": round(peak_ram_mb, 2),
                "memory_measurement_qualification": (
                    "tracemalloc tracks Python-allocated heap memory (including NumPy arrays in recent versions); "
                    "it misses SQLite and other native allocations."
                ),
                "build_time_s": round(build_time_s, 2),
            },
            "regime_a_within_paper": {
                "candidate_pool_size": "~25 chunks per paper",
                "exact_id_match_top4_pct": round(wp_recall_4_pct, 2),
                "exact_id_match_top20_pct": round(wp_recall_20_pct, 2),
                "max_score_delta_vs_blas": float(f"{wp_score_max_delta:.2e}"),
                "warmup_queries": NUM_WARMUP_QUERIES,
                "num_timed_passes": NUM_LATENCY_PASSES,
                "pooled_samples": len(all_wp_latencies_ms),
                "p50_latency_ms": round(wp_pooled_p50, 3),
                "p95_latency_ms": round(wp_pooled_p95, 3),
                "p99_latency_ms": round(wp_pooled_p99, 3),
                "p50_pass_range_ms": [round(min(wp_pass_p50s), 3), round(max(wp_pass_p50s), 3)],
                "latency_explanation": "Likely includes Python-side payload filtering overhead; not profiled.",
            },
            "regime_b_global_corpus": {
                "candidate_pool_size": f"{len(chunks)} chunks across all papers",
                "exact_id_match_top4_pct": round(xp_recall_4_pct, 2),
                "exact_id_match_top20_pct": round(xp_recall_20_pct, 2),
                "max_score_delta_vs_blas": float(f"{xp_score_max_delta:.2e}"),
                "warmup_queries": NUM_WARMUP_QUERIES,
                "num_timed_passes": NUM_LATENCY_PASSES,
                "pooled_samples": len(all_xp_latencies_ms),
                "p50_latency_ms": round(xp_pooled_p50, 3),
                "p95_latency_ms": round(xp_pooled_p95, 3),
                "p99_latency_ms": round(xp_pooled_p99, 3),
                "p50_pass_range_ms": [round(min(xp_pass_p50s), 3), round(max(xp_pass_p50s), 3)],
                "latency_explanation": "Likely dominated by in-process Python/NumPy scan; not profiled.",
            },
        }

        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(benchmark_payload, f, indent=2)
        print(f"\n[ARTIFACT] Rigorous benchmark results written to: {out_json.relative_to(WORKSPACE_ROOT)}")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
