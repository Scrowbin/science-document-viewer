"""
Phase 3 Embedding Benchmark: SciFact Out-of-Domain Sanity Check
Zero-shot scientific passage retrieval across biomedical & multi-disciplinary research.
Compares:
- sentence-transformers/all-MiniLM-L6-v2 (Baseline)
- BAAI/bge-small-en-v1.5
- intfloat/e5-small-v2 (Champion)
- allenai/specter2_base (with specter2_adhoc_query adapter)
- BM25 (Lexical Reference)
Metrics: nDCG@10, Recall@10, Recall@100, MRR@10, MAP@10, Latency, Peak RSS.
"""

import gc
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

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

from sentence_transformers import SentenceTransformer

PHASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PHASE_DIR / "artifacts"
SCIFACT_DIR = ARTIFACTS_DIR / "scifact" / "data"


def get_process_rss_mb() -> float:
    return psutil.Process().memory_info().rss / (1024.0 * 1024.0)


# ─── Load SciFact Data ───────────────────────────────────────────────────────
def load_scifact():
    claims_file = SCIFACT_DIR / "claims_dev.jsonl"
    corpus_file = SCIFACT_DIR / "corpus.jsonl"

    corpus = []
    doc_id_to_idx = {}
    with open(corpus_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)
            doc_id = item["doc_id"]
            title = item.get("title", "")
            abstract = " ".join(item.get("abstract", []))
            full_text = f"{title}. {abstract}".strip()
            corpus.append({"doc_id": doc_id, "text": full_text})
            doc_id_to_idx[doc_id] = idx

    claims = []
    with open(claims_file, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            cited_ids = set(item.get("cited_doc_ids", []))
            if cited_ids:  # only evaluate claims that have ground-truth evidence docs
                claims.append({
                    "id": item["id"],
                    "claim": item["claim"],
                    "gold_doc_ids": cited_ids,
                })

    return corpus, doc_id_to_idx, claims


# ─── IR Metrics ─────────────────────────────────────────────────────────────
def compute_ir_metrics(retrieved_doc_ids: List[int], gold_doc_ids: Set[int], k: int = 10):
    hits = [1 if d_id in gold_doc_ids else 0 for d_id in retrieved_doc_ids]
    n_rel = len(gold_doc_ids)

    # Recall@k, Recall@100
    rec_k = sum(hits[:k]) / max(1, n_rel)
    rec_100 = sum(hits[:100]) / max(1, n_rel)

    # MRR@k
    mrr = 0.0
    for r, h in enumerate(hits[:k]):
        if h == 1:
            mrr = 1.0 / (r + 1)
            break

    # DCG / IDCG @ k
    dcg = sum(h / np.log2(r + 2) for r, h in enumerate(hits[:k]))
    idcg = sum(1.0 / np.log2(r + 2) for r in range(min(k, n_rel)))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    # AP@k
    num_hits = 0
    prec_sum = 0.0
    for r, h in enumerate(hits[:k]):
        if h == 1:
            num_hits += 1
            prec_sum += num_hits / (r + 1)
    ap = prec_sum / min(k, n_rel) if n_rel > 0 else 0.0

    return {
        "ndcg10": ndcg,
        "recall10": rec_k,
        "recall100": rec_100,
        "mrr10": mrr,
        "map10": ap,
        "hit1": hits[0] if hits else 0,
    }


# ─── BM25 Baseline ──────────────────────────────────────────────────────────
class SimpleBM25:
    def __init__(self, corpus, tokenizer_fn):
        self.corpus = corpus
        self.tokenizer_fn = tokenizer_fn
        self.doc_len = [len(tokenizer_fn(c["text"])) for c in corpus]
        self.avg_dl = sum(self.doc_len) / max(1, len(self.doc_len))
        self.df = {}
        self.postings = {}

        for doc_id, c in enumerate(corpus):
            tokens = tokenizer_fn(c["text"])
            counts = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            for t, cnt in counts.items():
                self.df[t] = self.df.get(t, 0) + 1
                self.postings.setdefault(t, []).append((doc_id, cnt))

    def retrieve(self, query: str, top_k: int = 100, k1: float = 1.5, b: float = 0.75):
        q_tokens = self.tokenizer_fn(query)
        scores = {}
        N = len(self.corpus)

        for t in q_tokens:
            if t not in self.df:
                continue
            df_t = self.df[t]
            idf = np.log((N - df_t + 0.5) / (df_t + 0.5) + 1.0)
            for doc_id, tf in self.postings[t]:
                dl = self.doc_len[doc_id]
                denom = tf + k1 * (1.0 - b + b * (dl / self.avg_dl))
                num = tf * (k1 + 1.0)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * (num / denom)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [doc_id for doc_id, _ in ranked]


def evaluate_bm25_scifact(corpus, claims):
    print("\n[SCIFACT EVAL] Running BM25 baseline...")
    from transformers import AutoTokenizer
    bge_tok = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5")
    wp_tokenizer = lambda text: [t for t in bge_tok.tokenize(text.lower()) if len(t) > 1]

    t0 = time.time()
    bm25 = SimpleBM25(corpus, wp_tokenizer)
    rss_peak = get_process_rss_mb()

    metrics = []
    lat = 0.0
    for c in claims:
        t_q = time.time()
        top_idx = bm25.retrieve(c["claim"], top_k=100)
        lat += time.time() - t_q
        ret_doc_ids = [corpus[i]["doc_id"] for i in top_idx]
        m = compute_ir_metrics(ret_doc_ids, c["gold_doc_ids"])
        metrics.append(m)

    n = len(claims)
    return {
        "model_name": "BM25 (WordPiece)",
        "embedding_dim": "Lexical",
        "latency_ms": round(lat / n * 1000, 2),
        "peak_rss_mb": round(rss_peak, 1),
        "ndcg10": float(np.mean([m["ndcg10"] for m in metrics])),
        "recall10": float(np.mean([m["recall10"] for m in metrics])),
        "recall100": float(np.mean([m["recall100"] for m in metrics])),
        "mrr10": float(np.mean([m["mrr10"] for m in metrics])),
        "map10": float(np.mean([m["map10"] for m in metrics])),
    }


def evaluate_dense_scifact(model_name, corpus, claims, query_prefix="", passage_prefix=""):
    print(f"\n[SCIFACT EVAL] Running dense model: {model_name}...")
    gc.collect()
    rss_before = get_process_rss_mb()
    t_load_0 = time.time()
    model = SentenceTransformer(model_name)
    load_time = time.time() - t_load_0

    doc_texts = [passage_prefix + c["text"] for c in corpus]
    doc_embs = model.encode(doc_texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
    rss_peak = max(rss_before, get_process_rss_mb())

    claim_texts = [query_prefix + c["claim"] for c in claims]
    claim_embs = model.encode(claim_texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)

    metrics = []
    lat = 0.0
    for q_idx, c in enumerate(claims):
        q_emb = claim_embs[q_idx]
        t_q = time.time()
        scores = np.dot(doc_embs, q_emb)
        top_100_idx = np.argsort(scores)[::-1][:100]
        lat += time.time() - t_q

        ret_doc_ids = [corpus[i]["doc_id"] for i in top_100_idx]
        m = compute_ir_metrics(ret_doc_ids, c["gold_doc_ids"])
        metrics.append(m)

    n = len(claims)
    dim = doc_embs.shape[1]
    del model, doc_embs, claim_embs
    gc.collect()

    return {
        "model_name": model_name,
        "embedding_dim": dim,
        "latency_ms": round(lat / n * 1000, 2),
        "peak_rss_mb": round(rss_peak, 1),
        "ndcg10": float(np.mean([m["ndcg10"] for m in metrics])),
        "recall10": float(np.mean([m["recall10"] for m in metrics])),
        "recall100": float(np.mean([m["recall100"] for m in metrics])),
        "mrr10": float(np.mean([m["mrr10"] for m in metrics])),
        "map10": float(np.mean([m["map10"] for m in metrics])),
    }


def evaluate_specter2_scifact(corpus, claims):
    model_name = "allenai/specter2_base (with adhoc_query adapter)"
    print(f"\n[SCIFACT EVAL] Running: {model_name}...")
    gc.collect()
    rss_before = get_process_rss_mb()

    from adapters import AutoAdapterModel
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained("allenai/specter2_base")
    model = AutoAdapterModel.from_pretrained("allenai/specter2_base")
    model.eval()

    adapter_path = WORKSPACE_ROOT / "backend" / "eval" / "models" / "specter2_adhoc_query"
    adapter_name = model.load_adapter(str(adapter_path))

    # Encode corpus docs with base model
    chunk_embs_list = []
    batch_size = 32
    for i in range(0, len(corpus), batch_size):
        batch_texts = [c["text"] for c in corpus[i:i+batch_size]]
        inputs = tok(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            cls_reps = outputs.last_hidden_state[:, 0, :]
            cls_reps = torch.nn.functional.normalize(cls_reps, p=2, dim=1)
            chunk_embs_list.append(cls_reps.cpu().numpy())
    doc_embs = np.vstack(chunk_embs_list)

    # Encode claims with active adapter
    model.set_active_adapters(adapter_name)
    rss_peak = max(rss_before, get_process_rss_mb())

    q_embs_list = []
    for i in range(0, len(claims), batch_size):
        batch_texts = [c["claim"] for c in claims[i:i+batch_size]]
        inputs = tok(batch_texts, padding=True, truncation=True, max_length=512, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            cls_reps = outputs.last_hidden_state[:, 0, :]
            cls_reps = torch.nn.functional.normalize(cls_reps, p=2, dim=1)
            q_embs_list.append(cls_reps.cpu().numpy())
    claim_embs = np.vstack(q_embs_list)

    metrics = []
    lat = 0.0
    for q_idx, c in enumerate(claims):
        q_emb = claim_embs[q_idx]
        t_q = time.time()
        scores = np.dot(doc_embs, q_emb)
        top_100_idx = np.argsort(scores)[::-1][:100]
        lat += time.time() - t_q

        ret_doc_ids = [corpus[i]["doc_id"] for i in top_100_idx]
        m = compute_ir_metrics(ret_doc_ids, c["gold_doc_ids"])
        metrics.append(m)

    n = len(claims)
    dim = doc_embs.shape[1]
    del model, tok, doc_embs, claim_embs
    gc.collect()

    return {
        "model_name": model_name,
        "embedding_dim": dim,
        "latency_ms": round(lat / n * 1000, 2),
        "peak_rss_mb": round(rss_peak, 1),
        "ndcg10": float(np.mean([m["ndcg10"] for m in metrics])),
        "recall10": float(np.mean([m["recall10"] for m in metrics])),
        "recall100": float(np.mean([m["recall100"] for m in metrics])),
        "mrr10": float(np.mean([m["mrr10"] for m in metrics])),
        "map10": float(np.mean([m["map10"] for m in metrics])),
    }


def main():
    print("=" * 110)
    print("PHASE 3: SCIFACT OUT-OF-DOMAIN SANITY CHECK (ZERO-SHOT RETRIEVAL)")
    print("Corpus: 5,183 Scientific Abstracts | Claims: 211 Answerable Claims")
    print("=" * 110)

    corpus, doc_id_to_idx, claims = load_scifact()
    print(f"Loaded {len(corpus)} abstracts, {len(claims)} evaluation claims.")

    # 1. BM25
    bm25_res = evaluate_bm25_scifact(corpus, claims)

    # 2. MiniLM
    minilm_res = evaluate_dense_scifact(
        "sentence-transformers/all-MiniLM-L6-v2", corpus, claims, query_prefix="", passage_prefix=""
    )

    # 3. BGE Small
    bge_res = evaluate_dense_scifact(
        "BAAI/bge-small-en-v1.5", corpus, claims,
        query_prefix="Represent this sentence for searching relevant passages: ", passage_prefix=""
    )

    # 4. E5 Small v2 (Champion)
    e5_res = evaluate_dense_scifact(
        "intfloat/e5-small-v2", corpus, claims,
        query_prefix="query: ", passage_prefix="passage: "
    )

    # 5. SPECTER2 + adhoc_query adapter
    specter_res = evaluate_specter2_scifact(corpus, claims)

    results = [minilm_res, bge_res, e5_res, specter_res, bm25_res]

    print("\n" + "=" * 110)
    print("SCIFACT CROSS-DATASET ZERO-SHOT BENCHMARK RESULTS")
    print("=" * 110)
    print(f"{'Model':<42} | {'Dim':<5} | {'Peak RSS':<9} | {'Lat':<7} | {'nDCG@10':<8} | {'Rec@10':<7} | {'Rec@100':<8} | {'MRR@10':<7}")
    print("-" * 110)
    for r in results:
        print(f"{r['model_name']:<42} | {str(r['embedding_dim']):<5} | {r['peak_rss_mb']:>6.1f} MB | {r['latency_ms']:>5.2f}ms | {r['ndcg10']:>8.4f} | {r['recall10']:>7.4f} | {r['recall100']:>8.4f} | {r['mrr10']:>7.4f}")

    out_file = ARTIFACTS_DIR / "scifact_cross_dataset_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved SciFact benchmark artifact to: {out_file}")


if __name__ == "__main__":
    main()
