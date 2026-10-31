"""
Phase 3 Embedding Benchmark: Expanded High-Power Cohort (160 Papers, 487 Queries)
Includes:
- Official allenai/specter2_adhoc_query adapter for SPECTER2
- Live process Peak RAM RSS sampling via psutil
- Paired paper-level cluster bootstrap (B=2,000) with Holm-Bonferroni FWER control
- Direct Head-to-Head pairwise bootstrap between E5 and BGE on full expanded sample
- Strict containment ground truth calibration (tau* = 0.55)
"""

import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import torch

WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

from apps.documents.services.chunking_utils import chunk_sections
from eval_common import (
    STOPWORDS,
    clean_evidence,
    compute_dcg,
    compute_ndcg,
    count_relevant_chunks,
    is_chunk_hit,
    paired_cluster_bootstrap,
    tokenize_regex,
)
from sentence_transformers import SentenceTransformer

TOP_K = 20
PHASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PHASE_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def get_process_rss_mb() -> float:
    """Returns current process Resident Set Size (RSS) in megabytes."""
    return psutil.Process().memory_info().rss / (1024.0 * 1024.0)


# ─── Simple Inverted-Index BM25 ──────────────────────────────────────────────
class SimpleBM25:
    def __init__(self, corpus_chunks: List[Dict[str, Any]], tokenizer_fn):
        self.chunks = corpus_chunks
        self.tokenizer_fn = tokenizer_fn
        self.doc_len = [len(tokenizer_fn(c["text"])) for c in corpus_chunks]
        self.avg_dl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.df: Dict[str, int] = {}
        self.postings: Dict[str, List[Tuple[int, int]]] = {}

        for doc_id, c in enumerate(corpus_chunks):
            tokens = tokenizer_fn(c["text"])
            counts: Dict[str, int] = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            for t, cnt in counts.items():
                self.df[t] = self.df.get(t, 0) + 1
                self.postings.setdefault(t, []).append((doc_id, cnt))

    def retrieve(self, query: str, cand_indices: Optional[List[int]] = None,
                 top_k: int = TOP_K, k1: float = 1.5, b: float = 0.75) -> List[int]:
        q_tokens = self.tokenizer_fn(query)
        scores = {}
        valid_set = set(cand_indices) if cand_indices is not None else None
        N = len(self.chunks)

        for t in q_tokens:
            if t not in self.df:
                continue
            df_t = self.df[t]
            idf = np.log((N - df_t + 0.5) / (df_t + 0.5) + 1.0)
            for doc_id, tf in self.postings[t]:
                if valid_set is not None and doc_id not in valid_set:
                    continue
                dl = self.doc_len[doc_id]
                denom = tf + k1 * (1.0 - b + b * (dl / self.avg_dl))
                num = tf * (k1 + 1.0)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (num / denom)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [doc_id for doc_id, _ in ranked]


# ─── Data Loading ────────────────────────────────────────────────────────────
def load_expanded_data():
    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_held_out_split.json"
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_corpus.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_qasper_sampled.json"

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
            c["paper_arxiv_id"] = aid
            chunks.append(c)
    return chunks


def precompute_rq(queries, chunks, paper_chunk_map, tau=0.55):
    rq_map = {}
    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        cand_indices = paper_chunk_map.get(aid, [])
        paper_chunks = [chunks[i] for i in cand_indices]
        rq_map[q_idx] = count_relevant_chunks(paper_chunks, aid, quote, ev_list, tau=tau)
    return rq_map


def compute_query_metrics(retrieved_chunks, query, rq, top_k=TOP_K, tau=0.55):
    aid = query.get("paper_arxiv_id", "")
    quote = query.get("verbatim_evidence_quote", "")
    ev_list = query.get("evidence_list", [])
    ranked_hits = [int(is_chunk_hit(c, aid, quote, ev_list, tau=tau)) for c in retrieved_chunks[:top_k]]
    while len(ranked_hits) < top_k:
        ranked_hits.append(0)

    ndcg4 = compute_ndcg(ranked_hits, rq, k=4)
    ndcg10 = compute_ndcg(ranked_hits, rq, k=10)

    mrr5 = 0.0
    for r, h in enumerate(ranked_hits[:5]):
        if h == 1:
            mrr5 = 1.0 / (r + 1)
            break

    hit1 = int(any(ranked_hits[:1]))
    hit3 = int(any(ranked_hits[:3]))
    hit5 = int(any(ranked_hits[:5]))
    recall4 = sum(ranked_hits[:4]) / max(1, rq)
    recall20 = sum(ranked_hits[:20]) / max(1, rq)

    return {
        "ndcg4": ndcg4, "ndcg10": ndcg10, "mrr5": mrr5,
        "hit1": hit1, "hit3": hit3, "hit5": hit5,
        "recall4": recall4, "recall20": recall20,
    }


def _aggregate_metrics(metrics_list, scores_by_paper):
    n = len(metrics_list)
    return {
        "ndcg4": float(np.mean([m["ndcg4"] for m in metrics_list])),
        "ndcg10": float(np.mean([m["ndcg10"] for m in metrics_list])),
        "mrr5": float(np.mean([m["mrr5"] for m in metrics_list])),
        "hit1": float(np.mean([m["hit1"] for m in metrics_list]) * 100),
        "hit3": float(np.mean([m["hit3"] for m in metrics_list]) * 100),
        "hit5": float(np.mean([m["hit5"] for m in metrics_list]) * 100),
        "recall4": float(np.mean([m["recall4"] for m in metrics_list])),
        "recall20": float(np.mean([m["recall20"] for m in metrics_list])),
        "n_queries": n,
        "scores_by_paper": scores_by_paper,
    }


# ─── Evaluators ─────────────────────────────────────────────────────────────
def evaluate_bm25(chunks, queries, rq_map, tokenizer_fn, name, tau=0.55):
    print(f"\n[BM25 EVAL] Indexing {len(chunks)} chunks with {name}...")
    rss_start = get_process_rss_mb()
    t0 = time.time()
    bm25 = SimpleBM25(chunks, tokenizer_fn)
    idx_time = time.time() - t0
    rss_peak = get_process_rss_mb()

    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    wp_metrics, xp_metrics = [], []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    xp_scores_by_paper: Dict[str, List[float]] = {}
    wp_lat = 0.0

    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        q_text = q["question"]
        rq = rq_map[q_idx]
        cand_idx = paper_chunk_indices.get(aid, [])

        t0 = time.time()
        ranked_wp_idx = bm25.retrieve(q_text, cand_indices=cand_idx, top_k=TOP_K)
        wp_lat += time.time() - t0
        ranked_wp = [chunks[i] for i in ranked_wp_idx]
        m_wp = compute_query_metrics(ranked_wp, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

    n = len(queries)
    return {
        "model_name": name,
        "embedding_dim": "Lexical",
        "indexing_time_s": round(idx_time, 2),
        "wp_latency_ms": round(wp_lat / n * 1000, 2),
        "peak_rss_mb": round(rss_peak, 1),
        "within_paper": _aggregate_metrics(wp_metrics, wp_scores_by_paper),
    }


def evaluate_dense_model(model_name, chunks, queries, rq_map,
                         query_prefix="", passage_prefix="", tau=0.55, save_prefix=None):
    print(f"\n[DENSE EVAL] Loading: {model_name}...")
    gc.collect()
    rss_before = get_process_rss_mb()
    t_load_0 = time.time()
    model = SentenceTransformer(model_name)
    load_time = time.time() - t_load_0
    rss_loaded = get_process_rss_mb()

    print(f"  Encoding {len(chunks)} chunks (passage prefix: '{passage_prefix}')...")
    t_enc_0 = time.time()
    doc_texts = [passage_prefix + c["text"] for c in chunks]
    doc_embs = model.encode(doc_texts, batch_size=32, show_progress_bar=False,
                            normalize_embeddings=True)
    enc_time = time.time() - t_enc_0
    rss_peak = max(rss_loaded, get_process_rss_mb())

    if save_prefix:
        np.save(ARTIFACTS_DIR / f"{save_prefix}_doc_embs.npy", doc_embs)
        print(f"  Saved {save_prefix}_doc_embs.npy ({doc_embs.shape})")

    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    print(f"  Encoding {len(queries)} queries (query prefix: '{query_prefix}')...")
    q_texts = [query_prefix + q["question"] for q in queries]
    q_embs = model.encode(q_texts, batch_size=32, show_progress_bar=False,
                          normalize_embeddings=True)

    if save_prefix:
        np.save(ARTIFACTS_DIR / f"{save_prefix}_query_embs.npy", q_embs)
        print(f"  Saved {save_prefix}_query_embs.npy ({q_embs.shape})")

    wp_metrics = []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    wp_lat = 0.0

    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        q_emb = q_embs[q_idx]
        rq = rq_map[q_idx]

        cand_idx = paper_chunk_indices.get(aid, [])
        if cand_idx:
            cand_embs = doc_embs[cand_idx]
            t0 = time.time()
            scores = np.dot(cand_embs, q_emb)
            top_local = np.argsort(scores)[::-1][:TOP_K]
            wp_lat += time.time() - t0
            ranked_wp = [chunks[cand_idx[i]] for i in top_local]
        else:
            ranked_wp = []

        m_wp = compute_query_metrics(ranked_wp, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

    n = len(queries)
    dim = doc_embs.shape[1]

    # Free memory
    del model, doc_embs, q_embs
    gc.collect()

    return {
        "model_name": model_name,
        "embedding_dim": dim,
        "load_time_s": round(load_time, 2),
        "chunk_encode_time_s": round(enc_time, 2),
        "wp_latency_ms": round(wp_lat / n * 1000, 2),
        "peak_rss_mb": round(rss_peak, 1),
        "within_paper": _aggregate_metrics(wp_metrics, wp_scores_by_paper),
    }


def evaluate_specter2_with_adapter(chunks, queries, rq_map, tau=0.55):
    """
    Evaluates SPECTER2 utilizing the official allenai/specter2_adhoc_query adapter.
    Chunks: encoded via allenai/specter2_base [CLS] representations.
    Queries: encoded with the active 'adhoc_query' adapter head!
    """
    model_name = "allenai/specter2_base (with adhoc_query adapter)"
    print(f"\n[SPECTER2 EVAL] Loading: allenai/specter2_base + specter2_adhoc_query adapter...")
    gc.collect()
    rss_before = get_process_rss_mb()
    t_load_0 = time.time()

    from adapters import AutoAdapterModel
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained("allenai/specter2_base")
    model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
    model.eval()

    adapter_path = WORKSPACE_ROOT / "backend" / "eval" / "models" / "specter2_adhoc_query"
    if not adapter_path.exists():
        from huggingface_hub import snapshot_download
        adapter_path = Path(snapshot_download("allenai/specter2_adhoc_query",
                                              local_dir=str(adapter_path)))

    adapter_name = model.load_adapter(str(adapter_path))
    load_time = time.time() - t_load_0
    rss_loaded = get_process_rss_mb()

    # 1. Encode chunks without adapter (or base representation)
    print(f"  Encoding {len(chunks)} chunks with SPECTER2 base representation...")
    t_enc_0 = time.time()
    chunk_embs_list = []
    batch_size = 16

    for i in range(0, len(chunks), batch_size):
        batch_texts = [c["text"] for c in chunks[i:i+batch_size]]
        inputs = tok(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            # CLS token
            cls_reps = outputs.last_hidden_state[:, 0, :]
            cls_reps = torch.nn.functional.normalize(cls_reps, p=2, dim=1)
            chunk_embs_list.append(cls_reps.cpu().numpy())

    doc_embs = np.vstack(chunk_embs_list)
    enc_time = time.time() - t_enc_0

    # 2. Encode queries WITH adhoc_query adapter active
    print(f"  Encoding {len(queries)} queries with ACTIVE adhoc_query adapter...")
    model.set_active_adapters(adapter_name)
    rss_peak = max(rss_loaded, get_process_rss_mb())

    q_embs_list = []
    for i in range(0, len(queries), batch_size):
        batch_texts = [q["question"] for q in queries[i:i+batch_size]]
        inputs = tok(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            cls_reps = outputs.last_hidden_state[:, 0, :]
            cls_reps = torch.nn.functional.normalize(cls_reps, p=2, dim=1)
            q_embs_list.append(cls_reps.cpu().numpy())

    q_embs = np.vstack(q_embs_list)

    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_indices.setdefault(c["paper_arxiv_id"], []).append(idx)

    wp_metrics = []
    wp_scores_by_paper: Dict[str, List[float]] = {}
    wp_lat = 0.0

    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        q_emb = q_embs[q_idx]
        rq = rq_map[q_idx]

        cand_idx = paper_chunk_indices.get(aid, [])
        if cand_idx:
            cand_embs = doc_embs[cand_idx]
            t0 = time.time()
            scores = np.dot(cand_embs, q_emb)
            top_local = np.argsort(scores)[::-1][:TOP_K]
            wp_lat += time.time() - t0
            ranked_wp = [chunks[cand_idx[i]] for i in top_local]
        else:
            ranked_wp = []

        m_wp = compute_query_metrics(ranked_wp, q, rq, tau=tau)
        wp_metrics.append(m_wp)
        wp_scores_by_paper.setdefault(aid, []).append(m_wp["ndcg4"])

    n = len(queries)
    dim = doc_embs.shape[1]

    del model, tok, doc_embs, q_embs
    gc.collect()

    return {
        "model_name": model_name,
        "embedding_dim": dim,
        "load_time_s": round(load_time, 2),
        "chunk_encode_time_s": round(enc_time, 2),
        "wp_latency_ms": round(wp_lat / n * 1000, 2),
        "peak_rss_mb": round(rss_peak, 1),
        "within_paper": _aggregate_metrics(wp_metrics, wp_scores_by_paper),
    }


def _print_master_table(base_res, stat_results, specter_res, bm25_res):
    print(f"\n{'Model':<38} | {'Dim':<5} | {'Peak RSS':<9} | {'Latency':<8} | {'nDCG@4':<7} | {'MRR@5':<7} | {'Hit@5':<6} | {'Rec@20':<7} | {'Delta':<7} | {'95% CI':<19} | {'p-val':<7} | {'Sig*'}")
    print("-" * 155)

    # Base
    b_wp = base_res["within_paper"]
    print(f"{base_res['model_name']:<38} | {base_res['embedding_dim']:<5} | {base_res['peak_rss_mb']:>6.1f} MB | {base_res['wp_latency_ms']:>5.2f} ms | {b_wp['ndcg4']:>7.4f} | {b_wp['mrr5']:>7.4f} | {b_wp['hit5']:>5.1f}% | {b_wp['recall20']:>7.3f} | {'Base':<7} | {'Reference':<19} | {'-':<7} | {'-'}")

    for item in stat_results:
        res = item["res"]
        wp = res["within_paper"]
        sig_str = "YES*" if item["is_sig"] else "No"
        ci_str = f"[{item['ci_lower']:+.4f}, {item['ci_upper']:+.4f}]"
        print(f"{item['model_name']:<38} | {res['embedding_dim']:<5} | {res['peak_rss_mb']:>6.1f} MB | {res['wp_latency_ms']:>5.2f} ms | {wp['ndcg4']:>7.4f} | {wp['mrr5']:>7.4f} | {wp['hit5']:>5.1f}% | {wp['recall20']:>7.3f} | {item['diff']:>+7.4f} | {ci_str:<19} | {item['p_val']:>7.4f} | {sig_str}")

    # SPECTER2
    s_wp = specter_res["within_paper"]
    print(f"{specter_res['model_name']:<38} | {specter_res['embedding_dim']:<5} | {specter_res['peak_rss_mb']:>6.1f} MB | {specter_res['wp_latency_ms']:>5.2f} ms | {s_wp['ndcg4']:>7.4f} | {s_wp['mrr5']:>7.4f} | {s_wp['hit5']:>5.1f}% | {s_wp['recall20']:>7.3f} | {'Explor':<7} | {'Task-Adapted':<19} | {'-':<7} | {'-'}")

    # BM25
    bm_wp = bm25_res["within_paper"]
    print(f"{bm25_res['model_name']:<38} | {bm25_res['embedding_dim']:<5} | {bm25_res['peak_rss_mb']:>6.1f} MB | {bm25_res['wp_latency_ms']:>5.2f} ms | {bm_wp['ndcg4']:>7.4f} | {bm_wp['mrr5']:>7.4f} | {bm_wp['hit5']:>5.1f}% | {bm_wp['recall20']:>7.3f} | {'Lexical':<7} | {'Subword Postings':<19} | {'-':<7} | {'-'}")


# ─── Main Execution ───────────────────────────────────────────────────────────
def main():
    print("=" * 110)
    print("PHASE 3: HIGH-POWER EXPANDED HELD-OUT BENCHMARK (160 PAPERS, 487 QUERIES)")
    print("Protocol: Strict Containment tau*=0.55 | Paper Cluster Bootstrap B=2,000 | psutil Peak RSS")
    print("=" * 110)

    held_out_aids, corpus, queries = load_expanded_data()
    print(f"\nLoaded {len(held_out_aids)} papers, {len(queries)} answerable queries.")

    chunks = build_chunks(corpus, strategy="section_overlap", max_tokens=350, overlap=70)
    print(f"Generated {len(chunks)} chunks across {len(held_out_aids)} papers.")
    with open(ARTIFACTS_DIR / "expanded_160_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f)

    paper_chunk_map: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        paper_chunk_map.setdefault(c["paper_arxiv_id"], []).append(idx)

    print("\nPre-computing relevant chunk count R_q for all 487 queries (strict containment tau*=0.55)...")
    rq_map = precompute_rq(queries, chunks, paper_chunk_map, tau=0.55)
    rq_vals = list(rq_map.values())
    print(f"  R_q Summary: mean={np.mean(rq_vals):.2f}, median={np.median(rq_vals):.1f}, non-zero={sum(1 for r in rq_vals if r > 0)}/487 ({sum(1 for r in rq_vals if r > 0)/487*100:.1f}%)")

    # 1. Lexical Baseline
    from transformers import AutoTokenizer
    bge_tok = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
    wp_tokenizer = lambda text: [t for t in bge_tok.tokenize(text.lower()) if len(t) > 1]
    bm25_res = evaluate_bm25(chunks, queries, rq_map, wp_tokenizer, "BM25 [WordPiece Subwords]", tau=0.55)

    # 2. Registered Baseline: MiniLM
    base_res = evaluate_dense_model(
        "sentence-transformers/all-MiniLM-L6-v2", chunks, queries, rq_map,
        query_prefix="", passage_prefix="", tau=0.55
    )

    # 3. Dense Candidate: BGE Small
    bge_res = evaluate_dense_model(
        "BAAI/bge-small-en-v1.5", chunks, queries, rq_map,
        query_prefix="Represent this sentence for searching relevant passages: ",
        passage_prefix="", tau=0.55
    )

    # 4. Dense Candidate: E5 Small v2 (Champion)
    e5_res = evaluate_dense_model(
        "intfloat/e5-small-v2", chunks, queries, rq_map,
        query_prefix="query: ", passage_prefix="passage: ", tau=0.55,
        save_prefix="expanded_160_e5"
    )

    # 5. Dense Candidate: MPNet Base
    mpnet_res = evaluate_dense_model(
        "sentence-transformers/all-mpnet-base-v2", chunks, queries, rq_map,
        query_prefix="", passage_prefix="", tau=0.55
    )

    # 6. Dense Candidate: SPECTER2 with adhoc_query adapter
    specter_res = evaluate_specter2_with_adapter(chunks, queries, rq_map, tau=0.55)

    # 7. Hypothesis Testing vs Base (Holm-Bonferroni M=3)
    candidates = [
        ("intfloat/e5-small-v2", e5_res),
        ("BAAI/bge-small-en-v1.5", bge_res),
        ("sentence-transformers/all-mpnet-base-v2", mpnet_res),
    ]

    stat_results: List[Dict[str, Any]] = []
    for name, c_res in candidates:
        diff, ci, p_val = paired_cluster_bootstrap(
            base_res["within_paper"]["scores_by_paper"],
            c_res["within_paper"]["scores_by_paper"],
            n_bootstraps=2000,
        )
        stat_results.append({
            "model_name": name, "res": c_res,
            "diff": diff, "ci_lower": ci[0], "ci_upper": ci[1], "p_val": p_val,
        })

    stat_results.sort(key=lambda x: float(x["p_val"]))
    M = len(stat_results)
    for rank_idx, item in enumerate(stat_results):
        alpha_k = 0.05 / (M - rank_idx)
        item["holm_alpha"] = alpha_k
        item["is_sig"] = item["p_val"] <= alpha_k
        item["meets_sesoi"] = item["diff"] >= 0.030

    # Direct Head-to-Head Pairwise Bootstrap: E5 vs BGE on N=487
    diff_e5_bge, ci_e5_bge, p_val_e5_bge = paired_cluster_bootstrap(
        bge_res["within_paper"]["scores_by_paper"],
        e5_res["within_paper"]["scores_by_paper"],
        n_bootstraps=2000,
    )

    # Print Master Table
    print("\n" + "=" * 155)
    print("EXPANDED HELD-OUT BENCHMARK RESULTS (K=160 Papers, N=487 Queries, tau*=0.55)")
    print("=" * 155)
    _print_master_table(base_res, stat_results, specter_res, bm25_res)

    print("\n[DIRECT HIGH-POWER HEAD-TO-HEAD] intfloat/e5-small-v2 vs BAAI/bge-small-en-v1.5 (K=160, N=487):")
    print(f"  Delta nDCG@4: {diff_e5_bge:+.4f} [95% CI: {ci_e5_bge[0]:+.4f}, {ci_e5_bge[1]:+.4f}]")
    print(f"  p-value:      {p_val_e5_bge:.4f}")
    print(f"  Significant (alpha=0.05): {'YES*' if p_val_e5_bge <= 0.05 else 'No'}")

    # Serialize Artifact
    out_payload = {
        "benchmark": "Phase 3 High-Power Expanded Held-Out Benchmark",
        "dataset": "QASPER Expanded Split (160 Papers, 487 Queries)",
        "containment_tau": 0.55,
        "n_bootstraps": 2000,
        "cluster_level": "paper",
        "statistical_power_level": "78.3%-85.5% for observed delta (+0.0493/+0.0555); 38.6% for prespecified SESOI=0.030 (see audit_and_correct_statistics.py)",
        "models": {
            "all-MiniLM-L6-v2": base_res,
            "bge-small-en-v1.5": bge_res,
            "e5-small-v2": e5_res,
            "all-mpnet-base-v2": mpnet_res,
            "specter2_base_with_adhoc_query": specter_res,
            "bm25_wordpiece": bm25_res,
        },
        "hypothesis_tests_vs_baseline": [
            {
                "model_name": item["model_name"],
                "delta_ndcg4": item["diff"],
                "ci_95": [item["ci_lower"], item["ci_upper"]],
                "p_value": item["p_val"],
                "holm_alpha": item["holm_alpha"],
                "is_significant": item["is_sig"],
                "meets_sesoi": item["meets_sesoi"],
            }
            for item in stat_results
        ],
        "direct_head_to_head_e5_vs_bge": {
            "delta_ndcg4": diff_e5_bge,
            "ci_95": [ci_e5_bge[0], ci_e5_bge[1]],
            "p_value": p_val_e5_bge,
            "is_significant": p_val_e5_bge <= 0.05,
        },
    }

    out_file = ARTIFACTS_DIR / "expanded_160_papers_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nSaved definitive high-power benchmark artifact to: {out_file}")


if __name__ == "__main__":
    main()
