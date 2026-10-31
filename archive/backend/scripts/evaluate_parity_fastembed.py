"""
FastEmbed INT8 vs. FP32 PyTorch Parity Check (200-Chunk Dev Slice)
Measures the cosine similarity fidelity between FastEmbed ONNX/INT8 and
SentenceTransformers FP32 PyTorch on real scientific text passages.
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastembed import TextEmbedding
from sentence_transformers import SentenceTransformer


def load_dev_chunks(num_chunks: int = 200) -> list:
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"

    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    dev_aids = set(split_data["dev_papers"])

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    chunks = []
    for aid in dev_aids:
        doc = corpus.get(aid, {})
        for sec in doc.get("sections", []):
            paragraphs = sec.get("paragraphs", [])
            for p in paragraphs:
                p_clean = p.strip()
                if len(p_clean.split()) >= 30:  # meaningful academic paragraph
                    chunks.append(p_clean)
                    if len(chunks) >= num_chunks:
                        return chunks
    return chunks


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
    norm1 = np.linalg.norm(v1, axis=1, keepdims=True)
    norm2 = np.linalg.norm(v2, axis=1, keepdims=True)
    v1_norm = v1 / np.maximum(norm1, 1e-12)
    v2_norm = v2 / np.maximum(norm2, 1e-12)
    return np.sum(v1_norm * v2_norm, axis=1)


def main():
    print("[PARITY-CHECK] Loading 200 Dev chunks from QASPER...")
    chunks = load_dev_chunks(num_chunks=200)
    print(f"  Loaded {len(chunks)} paragraphs (mean length: {np.mean([len(c.split()) for c in chunks]):.1f} words)")

    results = {}

    # Test 1: all-MiniLM-L6-v2 (FastEmbed FP32 ONNX vs PyTorch FP32)
    print("\n[PARITY-CHECK] 1. all-MiniLM-L6-v2 (FastEmbed ONNX vs PyTorch FP32)...")
    fe_minilm = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    t0 = time.time()
    fe_minilm_embs = np.array(list(fe_minilm.embed(chunks, batch_size=16)))
    dur_fe_minilm = round((time.time() - t0) * 1000.0, 1)

    pt_minilm = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    t0 = time.time()
    pt_minilm_embs = pt_minilm.encode(chunks, batch_size=16, show_progress_bar=False, normalize_embeddings=True)
    dur_pt_minilm = round((time.time() - t0) * 1000.0, 1)

    cos_minilm = cosine_similarity(fe_minilm_embs, pt_minilm_embs)
    results["all-MiniLM-L6-v2"] = {
        "fe_runtime": "ONNX FP32",
        "pt_runtime": "PyTorch FP32",
        "mean_cosine": float(np.mean(cos_minilm)),
        "min_cosine": float(np.min(cos_minilm)),
        "max_cosine": float(np.max(cos_minilm)),
        "p5_cosine": float(np.percentile(cos_minilm, 5)),
        "p50_cosine": float(np.percentile(cos_minilm, 50)),
        "p95_cosine": float(np.percentile(cos_minilm, 95)),
        "fe_latency_ms": dur_fe_minilm,
        "pt_latency_ms": dur_pt_minilm,
    }
    print(f"  MiniLM Cosine Similarity: Mean = {np.mean(cos_minilm):.5f}, Min = {np.min(cos_minilm):.5f}, P5 = {np.percentile(cos_minilm, 5):.5f}")
    print(f"  FastEmbed ONNX time: {dur_fe_minilm} ms | PyTorch time: {dur_pt_minilm} ms")

    # Test 2: BAAI/bge-small-en-v1.5 (FastEmbed INT8 vs PyTorch FP32)
    print("\n[PARITY-CHECK] 2. BAAI/bge-small-en-v1.5 (FastEmbed INT8 vs PyTorch FP32)...")
    fe_bge = TextEmbedding("BAAI/bge-small-en-v1.5")
    t0 = time.time()
    fe_bge_embs = np.array(list(fe_bge.embed(chunks, batch_size=16)))
    dur_fe_bge = round((time.time() - t0) * 1000.0, 1)

    pt_bge = SentenceTransformer("BAAI/bge-small-en-v1.5")
    t0 = time.time()
    pt_bge_embs = pt_bge.encode(chunks, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
    dur_pt_bge = round((time.time() - t0) * 1000.0, 1)

    cos_bge = cosine_similarity(fe_bge_embs, pt_bge_embs)
    results["bge-small-en-v1.5"] = {
        "fe_runtime": "FastEmbed INT8 ONNX",
        "pt_runtime": "PyTorch FP32",
        "mean_cosine": float(np.mean(cos_bge)),
        "min_cosine": float(np.min(cos_bge)),
        "max_cosine": float(np.max(cos_bge)),
        "p5_cosine": float(np.percentile(cos_bge, 5)),
        "p50_cosine": float(np.percentile(cos_bge, 50)),
        "p95_cosine": float(np.percentile(cos_bge, 95)),
        "fe_latency_ms": dur_fe_bge,
        "pt_latency_ms": dur_pt_bge,
    }
    print(f"  BGE Cosine Similarity: Mean = {np.mean(cos_bge):.5f}, Min = {np.min(cos_bge):.5f}, P5 = {np.percentile(cos_bge, 5):.5f}")
    print(f"  FastEmbed INT8 time: {dur_fe_bge} ms | PyTorch FP32 time: {dur_pt_bge} ms")

    print("\n" + "=" * 80)
    print("PARITY EVALUATION SUMMARY (200 Chunks)")
    print("=" * 80)
    for model_name, data in results.items():
        print(f"Model: {model_name}")
        print(f"  Comparison: {data['fe_runtime']} vs {data['pt_runtime']}")
        print(f"  Mean Cosine Similarity: {data['mean_cosine']:.5f} (Min: {data['min_cosine']:.5f})")
        print(f"  Parity Status: {'[PASS] HIGH FIDELITY (>= 0.995)' if data['mean_cosine'] >= 0.995 else '[WARN] MODEST DRIFT (< 0.995)'}")
        print(f"  Speedup: FastEmbed {data['fe_latency_ms']} ms vs PyTorch {data['pt_latency_ms']} ms ({data['pt_latency_ms']/data['fe_latency_ms']:.2f}x)")

    out_file = WORKSPACE_ROOT / "eval" / "prepared" / "fastembed_parity_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[PARITY-CHECK] Results saved to: {out_file.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()
