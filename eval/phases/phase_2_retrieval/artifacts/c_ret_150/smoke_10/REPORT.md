# Phase 2: Retrieval Evaluation Report — Cohort [C-RET-150]

- **Cohort:** C-RET-150
- **Evaluated Papers:** 10
- **Evaluated Questions:** 24
- **Total Combinations Tested:** 15 (Chunkers × Embedders)
- **Evaluation Time:** 377.0 s

## 1. Overall Leaderboard (Ranked by nDCG@10)

| Rank | Combination | Chunker | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | Throughput (chunks/s) |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **hierarchical|arctic** | `hierarchical` | `arctic` | **0.8256** | 0.8185 | 0.7690 | 0.9444 | 0.8542 | 0.2500 | 0.7500 | 29.8 |
| 2 | **hierarchical|e5** | `hierarchical` | `e5` | **0.8241** | 0.7792 | 0.7726 | 0.9444 | 0.8958 | 0.2583 | 0.6250 | 31.5 |
| 3 | **hierarchical|modernbert** | `hierarchical` | `modernbert` | **0.7934** | 0.7444 | 0.7332 | 0.9352 | 0.8958 | 0.2583 | 0.5833 | 6.4 |
| 4 | **hierarchical|minilm** | `hierarchical` | `minilm` | **0.7411** | 0.6948 | 0.6662 | 0.9190 | 0.7940 | 0.2083 | 0.5417 | 60.0 |
| 5 | **hierarchical|bge** | `hierarchical` | `bge` | **0.7371** | 0.6691 | 0.6573 | 0.9398 | 0.8449 | 0.2333 | 0.5000 | 29.8 |
| 6 | **section_overlap|modernbert** | `section_overlap` | `modernbert` | **0.6533** | 0.6223 | 0.5614 | 0.8625 | 0.7479 | 0.1917 | 0.4583 | 3.8 |
| 7 | **section_overlap|e5** | `section_overlap` | `e5` | **0.6481** | 0.5830 | 0.5572 | 0.8688 | 0.7917 | 0.1833 | 0.4167 | 19.3 |
| 8 | **fixed_size|arctic** | `fixed_size` | `arctic` | **0.6250** | 0.5321 | 0.5178 | 0.9222 | 0.7028 | 0.1750 | 0.3333 | 15.2 |
| 9 | **fixed_size|modernbert** | `fixed_size` | `modernbert` | **0.6084** | 0.5115 | 0.4934 | 0.9306 | 0.8153 | 0.2083 | 0.3333 | 3.0 |
| 10 | **section_overlap|arctic** | `section_overlap` | `arctic` | **0.5964** | 0.5459 | 0.5001 | 0.8312 | 0.7812 | 0.1917 | 0.3333 | 19.9 |
| 11 | **section_overlap|bge** | `section_overlap` | `bge` | **0.5804** | 0.5453 | 0.5027 | 0.7687 | 0.6750 | 0.1583 | 0.4167 | 19.7 |
| 12 | **fixed_size|e5** | `fixed_size` | `e5` | **0.5789** | 0.5050 | 0.4642 | 0.8722 | 0.7736 | 0.2000 | 0.2917 | 14.9 |
| 13 | **fixed_size|minilm** | `fixed_size` | `minilm` | **0.5545** | 0.4814 | 0.4392 | 0.8653 | 0.6667 | 0.1500 | 0.3333 | 65.0 |
| 14 | **fixed_size|bge** | `fixed_size` | `bge` | **0.4894** | 0.3907 | 0.3599 | 0.8528 | 0.6569 | 0.1750 | 0.2083 | 15.2 |
| 15 | **section_overlap|minilm** | `section_overlap` | `minilm` | **0.4744** | 0.4425 | 0.3977 | 0.6562 | 0.5208 | 0.1250 | 0.2917 | 65.3 |

## 2. Chunking Method Comparison (Averaged across all embedding models)

| Chunker | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Throughput (chunks/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `hierarchical` | **0.7843** | 0.7412 | 0.9366 | 0.2416 | 0.6000 | 31.5 |
| `section_overlap` | **0.5905** | 0.5478 | 0.7975 | 0.1700 | 0.3833 | 25.6 |
| `fixed_size` | **0.5712** | 0.4841 | 0.8886 | 0.1817 | 0.3000 | 22.7 |

## 3. Embedding Model Comparison (Averaged across all chunking methods)

| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query Latency P50 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `e5` | **0.6837** | 0.6224 | 0.8951 | 0.2139 | 0.4445 | 0.12 |
| `minilm` | **0.5900** | 0.5396 | 0.8135 | 0.1611 | 0.3889 | 0.12 |
| `bge` | **0.6023** | 0.5350 | 0.8538 | 0.1889 | 0.3750 | 0.12 |
| `arctic` | **0.6823** | 0.6322 | 0.8993 | 0.2056 | 0.4722 | 0.13 |
| `modernbert` | **0.6850** | 0.6261 | 0.9094 | 0.2194 | 0.4583 | 0.15 |

## 4. Key Findings

1. **Champion Combination:** `hierarchical|arctic` achieved highest nDCG@10 of **0.8256** with MRR@10 of **0.8185**.
2. **Metric Integrity:** Pure Information Retrieval (IR) metrics evaluated directly on ranked candidate units without context concatenation or token-budget proxies.
