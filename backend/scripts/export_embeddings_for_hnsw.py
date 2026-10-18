"""
export_embeddings_for_hnsw.py
=============================
Standalone Embedding Export Utility for Google Colab HNSW Index Benchmarking.

Purpose:
  Decouples dense embedding inference (executed locally on Ryzen 5 5600) from 
  HNSW index graph construction and approximate nearest-neighbor benchmarking 
  (executed remotely on Google Colab).

Outputs per model:
  1. doc_embeddings.npy      - (N_docs, D) float32 L2-normalized document vectors
  2. query_embeddings.npy    - (N_queries, D) float32 L2-normalized query vectors
  3. doc_ids.json            - Ordered list of chunk identifiers matching matrix rows
  4. query_ids.json          - Ordered list of query identifiers matching matrix rows
  5. qrels.json              - Binary relevance dictionary {query_id: [relevant_doc_id, ...]}
  6. corpus_metadata.jsonl   - Chunk metadata stream (paper_id, section, page spans)
  7. manifest.json           - Comprehensive run manifest with SHA-256 checksums,
                               model metadata, dimensions, and prefix specifications.

Author: Academic Research Team
License: Apache 2.0 (Strictly Code-Only, Unexecuted during Plan Turn)
"""

import argparse
import hashlib
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

# Fix Windows SIGALRM missing attribute for transformers dynamic module resolution
if not hasattr(signal, "SIGALRM"):
    setattr(signal, "SIGALRM", getattr(signal, "SIGABRT", 6))

torch.set_num_threads(4)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# Ensure backend and backend/scripts are resolvable
WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

from eval_common import (
    clean_evidence,
    is_chunk_hit,
    tokenize_regex,
)


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 cryptographic hash of a file for manifest integrity."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_model_specs(model_name: str) -> Dict[str, Any]:
    """
    Returns pre-registered prefix and normalization specifications for candidate models.
    Prevents silent representation space corruption across evaluation stages.
    """
    specs = {
        "intfloat/e5-small-v2": {
            "query_prefix": "query: ",
            "passage_prefix": "passage: ",
            "dim": 384,
            "normalize": True,
            "trust_remote_code": False,
        },
        "BAAI/bge-small-en-v1.5": {
            "query_prefix": "Represent this sentence for searching relevant passages: ",
            "passage_prefix": "",
            "dim": 384,
            "normalize": True,
            "trust_remote_code": False,
        },
        "sentence-transformers/all-MiniLM-L6-v2": {
            "query_prefix": "",
            "passage_prefix": "",
            "dim": 384,
            "normalize": True,
            "trust_remote_code": False,
        },
        "Snowflake/snowflake-arctic-embed-m-v1.5": {
            "query_prefix": "Represent this sentence for searching relevant passages: ",
            "passage_prefix": "",
            "dim": 768,
            "normalize": True,
            "trust_remote_code": False,
        },
        "Snowflake/snowflake-arctic-embed-s": {
            "query_prefix": "Represent this sentence for searching relevant passages: ",
            "passage_prefix": "",
            "dim": 384,
            "normalize": True,
            "trust_remote_code": False,
        },
        "nomic-ai/nomic-embed-text-v1.5": {
            "query_prefix": "search_query: ",
            "passage_prefix": "search_document: ",
            "dim": 768,
            "normalize": True,
            "trust_remote_code": True,
        },
        "nomic-ai/modernbert-embed-base": {
            "query_prefix": "search_query: ",
            "passage_prefix": "search_document: ",
            "dim": 768,
            "normalize": True,
            "trust_remote_code": True,
        },
    }
    
    if model_name in specs:
        return specs[model_name]
    
    # Heuristic fallback with warning
    print(f"[WARN] Model '{model_name}' not in pre-registered registry. Applying raw fallback.")
    return {
        "query_prefix": "",
        "passage_prefix": "",
        "dim": 384,
        "normalize": True,
        "trust_remote_code": False,
    }


def load_corpus_and_queries(
    split_path: Path, corpus_path: Path, qa_path: Path
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Loads held-out split corpus chunks and answerable queries."""
    from apps.documents.services.chunking_utils import chunk_sections

    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    held_out_aids = set(split_data.get("held_out_papers", []))

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)
    held_out_corpus = {k: v for k, v in corpus_all.items() if k in held_out_aids}

    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)
    held_out_queries = [
        q for q in qa_all
        if q.get("paper_arxiv_id") in held_out_aids and q.get("question_type") != "unanswerable"
    ]

    # Build chunk candidate pool
    chunks: List[Dict[str, Any]] = []
    for aid, doc in held_out_corpus.items():
        sec_list = doc.get("sections", [])
        base_chunks = chunk_sections(
            sec_list, strategy="section_overlap", max_tokens=350, overlap=70
        )
        for c_idx, c in enumerate(base_chunks):
            chunk_dict = {
                "chunk_id": f"{aid}_c_{c_idx}",
                "paper_arxiv_id": aid,
                "section": c.get("section", "Main"),
                "page_start": c.get("page_start", 1),
                "page_end": c.get("page_end", 1),
                "text": c.get("text", ""),
            }
            chunks.append(chunk_dict)

    return chunks, held_out_queries


def generate_qrels(
    queries: List[Dict[str, Any]], chunks: List[Dict[str, Any]], tau: float = 0.55
) -> Dict[str, List[str]]:
    """
    Constructs binary relevance map (qrels) across all queries and chunks using
    the pre-registered token containment rule (tau* = 0.55).
    """
    qrels: Dict[str, List[str]] = {}
    paper_chunk_map: Dict[str, List[Dict[str, Any]]] = {}
    for c in chunks:
        paper_chunk_map.setdefault(c["paper_arxiv_id"], []).append(c)

    for q_idx, q in enumerate(queries):
        qid = q.get("question_id", f"q_{q_idx}")
        aid = q.get("paper_arxiv_id", "")
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])

        relevant_chunks: List[str] = []
        for c in paper_chunk_map.get(aid, []):
            if is_chunk_hit(c, aid, quote, ev_list, tau=tau):
                relevant_chunks.append(c["chunk_id"])

        qrels[qid] = relevant_chunks

    return qrels


def export_model_vectors(
    model_name: str,
    chunks: List[Dict[str, Any]],
    queries: List[Dict[str, Any]],
    qrels: Dict[str, List[str]],
    output_base_dir: Path,
    batch_size: int = 32,
    tau: float = 0.55,
) -> Path:
    """
    Encodes and exports document and query vectors with cryptographic checksums.
    """
    from sentence_transformers import SentenceTransformer

    safe_name = model_name.replace("/", "__").replace(":", "_")
    target_dir = output_base_dir / safe_name
    target_dir.mkdir(parents=True, exist_ok=True)

    specs = get_model_specs(model_name)
    print(f"\n========================================================")
    print(f"[EXPORT] Initializing model: {model_name}")
    print(f"[EXPORT] Output Directory: {target_dir}")
    print(f"[EXPORT] Specs: {specs}")
    print(f"========================================================")

    doc_emb_path = target_dir / "doc_embeddings.npy"
    query_emb_path = target_dir / "query_embeddings.npy"
    doc_embs: Optional[np.ndarray] = None
    query_embs: Optional[np.ndarray] = None
    doc_enc_time = 0.0
    query_enc_time = 0.0

    # Check for existing cached vectors to save computation
    if doc_emb_path.exists() and query_emb_path.exists():
        try:
            cached_d = np.load(doc_emb_path)
            cached_q = np.load(query_emb_path)
            if cached_d.shape == (len(chunks), specs["dim"]) and cached_q.shape == (len(queries), specs["dim"]):
                print(f"  [FAST PATH] Found existing valid embeddings in {target_dir.name}. Reusing without re-encoding.")
                doc_embs = cached_d.astype(np.float32)
                query_embs = cached_q.astype(np.float32)
        except Exception as e:
            print(f"  [WARN] Failed to load target cache: {e}. Re-encoding.")

    if doc_embs is None and "e5-small-v2" in model_name:
        e5_d_path = WORKSPACE_ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts" / "expanded_160_e5_doc_embs.npy"
        e5_q_path = WORKSPACE_ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts" / "expanded_160_e5_query_embs.npy"
        if e5_d_path.exists() and e5_q_path.exists():
            try:
                cached_d = np.load(e5_d_path)
                cached_q = np.load(e5_q_path)
                if cached_d.shape == (len(chunks), specs["dim"]) and cached_q.shape == (len(queries), specs["dim"]):
                    print(f"  [FAST PATH] Loaded pre-computed embeddings from {e5_d_path.name}")
                    doc_embs = cached_d.astype(np.float32)
                    query_embs = cached_q.astype(np.float32)
            except Exception as e:
                print(f"  [WARN] Failed to load e5 artifacts: {e}. Re-encoding.")

    if doc_embs is None or query_embs is None:
        model = SentenceTransformer(
            model_name,
            trust_remote_code=specs.get("trust_remote_code", False),
        )

        # 1. Encode Documents
        doc_texts = [specs["passage_prefix"] + c["text"] for c in chunks]
        print(f"  Encoding {len(doc_texts)} document chunks (batch_size={batch_size})...")
        t0 = time.time()
        doc_embs = model.encode(
            doc_texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=specs["normalize"],
        ).astype(np.float32)
        doc_enc_time = time.time() - t0

        # 2. Encode Queries
        q_texts = [specs["query_prefix"] + q["question"] for q in queries]
        print(f"  Encoding {len(q_texts)} queries (batch_size={batch_size})...")
        t0 = time.time()
        query_embs = model.encode(
            q_texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=specs["normalize"],
        ).astype(np.float32)
        query_enc_time = time.time() - t0

    # 3. Save Binary Matrices
    np.save(doc_emb_path, doc_embs)
    np.save(query_emb_path, query_embs)

    # 4. Save Ordered IDs & Query-Paper Mapping
    doc_ids = [c["chunk_id"] for c in chunks]
    query_ids = [q.get("question_id", f"q_{i}") for i, q in enumerate(queries)]
    query_paper_map = {q.get("question_id", f"q_{i}"): q.get("paper_arxiv_id", "") for i, q in enumerate(queries)}
    
    doc_ids_path = target_dir / "doc_ids.json"
    query_ids_path = target_dir / "query_ids.json"
    query_paper_map_path = target_dir / "query_paper_map.json"
    with open(doc_ids_path, "w", encoding="utf-8") as f:
        json.dump(doc_ids, f, indent=2)
    with open(query_ids_path, "w", encoding="utf-8") as f:
        json.dump(query_ids, f, indent=2)
    with open(query_paper_map_path, "w", encoding="utf-8") as f:
        json.dump(query_paper_map, f, indent=2)

    # 5. Save Relevance Labels (Qrels)
    qrels_path = target_dir / "qrels.json"
    with open(qrels_path, "w", encoding="utf-8") as f:
        json.dump(qrels, f, indent=2)

    # 6. Save Chunk Metadata Stream
    corpus_meta_path = target_dir / "corpus_metadata.jsonl"
    with open(corpus_meta_path, "w", encoding="utf-8") as f:
        for c in chunks:
            meta = {
                "chunk_id": c["chunk_id"],
                "paper_arxiv_id": c["paper_arxiv_id"],
                "section": c["section"],
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "token_estimate": len(tokenize_regex(c["text"])),
            }
            f.write(json.dumps(meta) + "\n")

    # 7. Compute Checksums & Compile Manifest
    files_to_hash = [
        "doc_embeddings.npy",
        "query_embeddings.npy",
        "doc_ids.json",
        "query_ids.json",
        "query_paper_map.json",
        "qrels.json",
        "corpus_metadata.jsonl",
    ]
    checksums = {fname: compute_sha256(target_dir / fname) for fname in files_to_hash}

    manifest = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "model_name": model_name,
        "safe_name": safe_name,
        "embedding_dim": int(doc_embs.shape[1]),
        "num_documents": int(doc_embs.shape[0]),
        "num_queries": int(query_embs.shape[0]),
        "specs": specs,
        "relevance_tau": tau,
        "doc_encode_time_seconds": round(doc_enc_time, 2),
        "query_encode_time_seconds": round(query_enc_time, 2),
        "sha256_checksums": checksums,
        "hardware_environment": "AMD Ryzen 5 5600 6-Core / 12-Thread CPU, 16 GB RAM",
    }

    manifest_path = target_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[SUCCESS] Export completed for {model_name}.")
    print(f"          Manifest: {manifest_path}")
    print(f"          Files: {list(checksums.keys())}\n")
    return target_dir


def main():
    parser = argparse.ArgumentParser(
        description="Export pre-embedded dense representations and qrels for Colab HNSW indexing."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=[
            "intfloat/e5-small-v2",
            "nomic-ai/modernbert-embed-base",
            "sentence-transformers/all-MiniLM-L6-v2",
        ],
        help="List of model names to export.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(WORKSPACE_ROOT / "eval" / "phases" / "phase_4_indexing" / "artifacts" / "colab_exports"),
        help="Directory to save exported artifacts.",
    )
    parser.add_argument(
        "--tau",
        type=float,
        default=0.55,
        help="Evidence containment threshold (default: 0.55).",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help="Batch size for local CPU embedding inference.",
    )
    args = parser.parse_args()

    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_held_out_split.json"
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_corpus.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_qasper_sampled.json"

    print(f"[INFO] Loading data from {WORKSPACE_ROOT}...")
    chunks, queries = load_corpus_and_queries(split_path, corpus_path, qa_path)
    print(f"[INFO] Loaded {len(chunks)} chunks and {len(queries)} queries.")

    print(f"[INFO] Generating ground-truth relevance labels (tau={args.tau})...")
    qrels = generate_qrels(queries, chunks, tau=args.tau)
    num_hits = sum(len(v) for v in qrels.values())
    print(f"[INFO] Generated qrels: {len(qrels)} queries, {num_hits} total relevance hits.")

    out_base = Path(args.output_dir)
    out_base.mkdir(parents=True, exist_ok=True)

    for m in args.models:
        export_model_vectors(
            model_name=m,
            chunks=chunks,
            queries=queries,
            qrels=qrels,
            output_base_dir=out_base,
            batch_size=args.batch_size,
            tau=args.tau,
        )

    print("[COMPLETED] All candidate models exported successfully.")


if __name__ == "__main__":
    main()
