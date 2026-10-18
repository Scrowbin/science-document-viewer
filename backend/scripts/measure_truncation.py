import json
import os
import sys
import numpy as np
from fastembed import TextEmbedding

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from apps.documents.services.chunking_utils import chunk_sections

bge = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
tokenizer = bge.model.tokenizer
# Disable default 512 truncation to measure the TRUE raw subword distribution of chunks
tokenizer.no_truncation()

corpus_path = os.path.join(ROOT_DIR, "eval", "prepared", "qasper_corpus.json")
with open(corpus_path, "r", encoding="utf-8") as f:
    corpus_dict = json.load(f)

# Baseline chunker: section_overlap (max_tokens=350, overlap=70)
chunks = []
for aid, p_data in corpus_dict.items():
    secs = p_data.get("sections", [])
    c_list = chunk_sections(secs, strategy="section_overlap", max_tokens=350, overlap=70)
    for c in c_list:
        chunks.append(c.get("text", ""))

subword_counts = []
for text in chunks:
    enc = tokenizer.encode(text)
    subword_counts.append(len(enc.ids))

arr = np.array(subword_counts)
total_tokens = int(arr.sum())
n_chunks = len(arr)


def compute_truncation_stats(limit: int):
    over = arr > limit
    n_over = int(np.sum(over))
    pct_over = round((n_over / n_chunks) * 100, 2)
    truncated_tokens = int(np.sum(arr[over] - limit))
    pct_tokens_lost = round((truncated_tokens / total_tokens) * 100, 2)
    mean_lost_on_trunc = round(float(np.mean(arr[over] - limit)), 1) if n_over > 0 else 0.0
    return {
        "limit": limit,
        "chunks_over": n_over,
        "pct_chunks_over": pct_over,
        "tokens_lost": truncated_tokens,
        "pct_tokens_lost": pct_tokens_lost,
        "mean_lost_on_truncated": mean_lost_on_trunc,
    }


stats_256 = compute_truncation_stats(256)
stats_512 = compute_truncation_stats(512)

print("=== PART 1a: MEASURED TOKENIZER & TRUNCATION DISTRIBUTION (UNCONSTRAINED) ===")
print(f"Total chunks evaluated: {n_chunks}")
print(f"Total subword tokens in corpus: {total_tokens:,}")
print("True Subword Token Distribution:")
print(f"  - Mean: {round(float(np.mean(arr)), 1)}")
print(f"  - Min:  {int(np.min(arr))}")
print(f"  - P50 (Median): {int(np.percentile(arr, 50))}")
print(f"  - P90: {int(np.percentile(arr, 90))}")
print(f"  - P95: {int(np.percentile(arr, 95))}")
print(f"  - Max:  {int(np.max(arr))}")

print(f"\nTruncation at Limit 256 (e.g. FastEmbed MiniLM-L6-v2):")
print(f"  - Chunks exceeding 256: {stats_256['chunks_over']} / {n_chunks} ({stats_256['pct_chunks_over']}%)")
print(f"  - Total subwords discarded: {stats_256['tokens_lost']:,} ({stats_256['pct_tokens_lost']}% of total corpus subwords)")
print(f"  - Mean tokens lost per truncated chunk: {stats_256['mean_lost_on_truncated']} subwords")

print(f"\nTruncation at Limit 512 (e.g. BGE-small-en-v1.5 / BERT / SciBERT):")
print(f"  - Chunks exceeding 512: {stats_512['chunks_over']} / {n_chunks} ({stats_512['pct_chunks_over']}%)")
print(f"  - Total subwords discarded: {stats_512['tokens_lost']:,} ({stats_512['pct_tokens_lost']}% of total corpus subwords)")
print(f"  - Mean tokens lost per truncated chunk: {stats_512['mean_lost_on_truncated']} subwords")
