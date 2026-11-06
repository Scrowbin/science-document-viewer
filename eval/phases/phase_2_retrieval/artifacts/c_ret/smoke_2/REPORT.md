# Phase 2: Retrieval Evaluation Report — Cohort [C-RET]

- **Cohort:** C-RET
- **Evaluated Papers:** 2
- **Evaluated Questions:** 3
- **Total Combinations Tested:** 6 (Chunkers × Embedders)
- **Evaluation Time:** 16.2 s

## 1. Overall Leaderboard (Ranked by nDCG@10)

| Rank | Combination | Chunker | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | Throughput (chunks/s) |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **hierarchical|e5** | `hierarchical` | `e5` | **0.8978** | 0.8333 | 0.8611 | 1.0000 | 1.0000 | 0.2667 | 0.6667 | 27.3 |
| 2 | **hierarchical|minilm** | `hierarchical` | `minilm` | **0.7606** | 0.6667 | 0.6667 | 1.0000 | 1.0000 | 0.2667 | 0.3333 | 51.9 |
| 3 | **section_overlap|e5** | `section_overlap` | `e5` | **0.7012** | 0.7500 | 0.5972 | 0.8333 | 0.8333 | 0.3333 | 0.6667 | 16.2 |
| 4 | **fixed_size|e5** | `fixed_size` | `e5` | **0.6996** | 0.7037 | 0.5741 | 1.0000 | 0.5000 | 0.1333 | 0.6667 | 14.8 |
| 5 | **section_overlap|minilm** | `section_overlap` | `minilm` | **0.4974** | 0.4444 | 0.3195 | 0.8333 | 0.5000 | 0.2000 | 0.0000 | 66.7 |
| 6 | **fixed_size|minilm** | `fixed_size` | `minilm` | **0.4875** | 0.5000 | 0.3889 | 0.6667 | 0.5000 | 0.1333 | 0.3333 | 47.3 |

## 2. Chunking Method Comparison (Averaged across all embedding models)

| Chunker | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Throughput (chunks/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `hierarchical` | **0.8292** | 0.7500 | 1.0000 | 0.2667 | 0.5000 | 39.6 |
| `section_overlap` | **0.5993** | 0.5972 | 0.8333 | 0.2666 | 0.3333 | 41.5 |
| `fixed_size` | **0.5936** | 0.6018 | 0.8334 | 0.1333 | 0.5000 | 31.0 |

## 3. Embedding Model Comparison (Averaged across all chunking methods)

| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query Latency P50 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `e5` | **0.7662** | 0.7623 | 0.9444 | 0.2444 | 0.6667 | 0.21 |
| `minilm` | **0.5818** | 0.5370 | 0.8333 | 0.2000 | 0.2222 | 0.21 |

## 4. Key Findings

1. **Champion Combination:** `hierarchical|e5` achieved highest nDCG@10 of **0.8978** with MRR@10 of **0.8333**.
2. **Metric Integrity:** Pure Information Retrieval (IR) metrics evaluated directly on ranked candidate units without context concatenation or token-budget proxies.
