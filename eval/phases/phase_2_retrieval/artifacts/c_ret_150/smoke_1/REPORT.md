# Phase 2: Retrieval Evaluation Report — Cohort [C-RET-150]

- **Cohort:** C-RET-150
- **Evaluated Papers:** 1
- **Evaluated Questions:** 2
- **Total Combinations Tested:** 3 (Chunkers × Embedders)
- **Evaluation Time:** 32.6 s

## 1. Overall Leaderboard (Ranked by nDCG@10)

| Rank | Combination | Chunker | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | N | Skipped | Throughput (chunks/s) |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **hierarchical|gemma** | `hierarchical` | `gemma` | **1.0000** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2000 | 1.0000 | 2 | 0 | 7.1 |
| 2 | **section_overlap|gemma** | `section_overlap` | `gemma` | **0.9251** | 1.0000 | 0.8500 | 1.0000 | 1.0000 | 0.4000 | 1.0000 | 2 | 0 | 3.9 |
| 3 | **fixed_size|gemma** | `fixed_size` | `gemma` | **0.5655** | 0.4166 | 0.4166 | 1.0000 | 1.0000 | 0.2000 | 0.0000 | 2 | 0 | 3.1 |

## 2. Chunking Method Comparison (Averaged across all embedding models)

| Chunker | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Throughput (chunks/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `hierarchical` | **1.0000** | 1.0000 | 1.0000 | 0.2000 | 1.0000 | 7.1 |
| `section_overlap` | **0.9251** | 1.0000 | 1.0000 | 0.4000 | 1.0000 | 3.9 |
| `fixed_size` | **0.5655** | 0.4166 | 1.0000 | 0.2000 | 0.0000 | 3.1 |

## 3. Embedding Model Comparison (Averaged across all chunking methods)

| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query Latency P50 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `gemma` | **0.8302** | 0.8055 | 1.0000 | 0.2667 | 0.6667 | 50.23 |

## 4. Key Findings

1. **Champion Combination:** `hierarchical|gemma` achieved highest nDCG@10 of **1.0000** with MRR@10 of **1.0000**.
2. **Metric Integrity:** Pure Information Retrieval (IR) metrics evaluated directly on ranked candidate units without context concatenation or token-budget proxies.
3. **Question Set:** Questions with no relevant chunk in a chunker's candidate pool are skipped (see Skipped column); compare chunkers only when N/Skipped are similar.
