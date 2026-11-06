# Phase 2: Semantic Chunking Evaluation Report — Cohort [C-RET-150]

> **Role:** Extension / ablation study for semantic chunking. Not part of the primary 3-chunker × 5-model matrix (`evaluate_retrieval.py`).

- **Cohort:** C-RET-150
- **Evaluated Papers:** 1 (of 1 requested)
- **Evaluated Questions:** 2
- **Common Questions (all active variants):** 2
- **Semantic Variants:** semantic_v1 (production branch), semantic_v2 (teammate, buffer_size=1)
- **Total Combinations Tested:** 2 (Variants × Embedders)
- **Evaluation Time:** 14.3 s

## 1. Overall Leaderboard (Ranked by nDCG@10, each variant's own question set)

| Rank | Combination | Variant | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | N | Skipped | Chunk tput (c/s) | Index tput (c/s) |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **semantic_v2|e5** | `semantic_v2` | `e5` | **0.6241** | 0.7500 | 0.4584 | 0.8334 | 0.6666 | 0.2000 | 0.5000 | 2 | 0 | 24.63 | 19.6 |
| 2 | **semantic_v1|e5** | `semantic_v1` | `e5` | **0.5389** | 0.6250 | 0.3334 | 0.8750 | 0.6250 | 0.2000 | 0.5000 | 2 | 0 | 21.93 | 17.9 |

## 2. Semantic Variant Comparison (Common 2 questions only, averaged across all embedding models)

| Variant | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | N | Chunk tput (c/s) | Index tput (c/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `semantic_v1` | **0.5389** | 0.6250 | 0.8750 | 0.2000 | 0.5000 | 2 | 21.93 | 17.9 |
| `semantic_v2` | **0.6241** | 0.7500 | 0.8334 | 0.2000 | 0.5000 | 2 | 24.63 | 19.6 |

## 3. Embedding Model Comparison (Averaged across both semantic variants)

| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query P50 (ms) | Query P95 (ms) | Peak Memory (MB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `e5` | **0.5815** | 0.6875 | 0.8542 | 0.2000 | 0.5000 | 10.59 | 10.95 | 1461.4 |

## 4. Notes

- **semantic_v1** — `apps.documents.services.chunkers.chunk_semantic` on the production branch.
  Uses percentile-based similarity drop threshold (25th pct) and a max_tokens=400 ceiling.
- **semantic_v2** — teammate's implementation (`vendor/teammate_chunkers_49dcac6.py`, commit 49dcac6).
  Adds `buffer_size=1` smoothing (mean of neighbour embeddings before thresholding) and per-section percentile calculation.
- Both variants use the same embedding model for sentence similarity scoring at chunk time,
  so chunking throughput (c/s) includes that embedding cost and is much lower than flat chunkers.
- **Metric Integrity:** Pure IR metrics on flat semantic chunks; strictly unit-L2 normalized.
- **Section sources:** see `section_sources` in `summary.json`.

**Champion combination:** `semantic_v2|e5` — nDCG@10 = **0.6241**, MRR@10 = **0.7500** (on its own question subset).