# Phase 2: Retrieval Evaluation Report — Cohort [PEERQA-PDF]

- **Cohort:** PEERQA-PDF
- **Evaluated Papers:** 2
- **Evaluated Questions:** 4
- **Total Combinations Tested:** 6 (Chunkers × Embedders)
- **Evaluation Time:** 20.8 s

## 1. Overall Leaderboard (Ranked by nDCG@10)

| Rank | Combination | Chunker | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | Throughput (chunks/s) |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **hierarchical|minilm** | `hierarchical` | `minilm` | **0.8711** | 0.8750 | 0.7708 | 0.9285 | 0.6643 | 0.6500 | 0.7500 | 57.7 |
| 2 | **hierarchical|e5** | `hierarchical` | `e5` | **0.7808** | 0.8750 | 0.6498 | 0.8072 | 0.5810 | 0.6000 | 0.7500 | 32.0 |
| 3 | **fixed_size|e5** | `fixed_size` | `e5` | **0.5371** | 0.7500 | 0.3585 | 0.5523 | 0.3886 | 0.5000 | 0.5000 | 15.5 |
| 4 | **section_overlap|e5** | `section_overlap` | `e5` | **0.4806** | 0.5938 | 0.3691 | 0.5312 | 0.4444 | 0.4000 | 0.5000 | 22.3 |
| 5 | **fixed_size|minilm** | `fixed_size` | `minilm` | **0.4586** | 0.5208 | 0.2985 | 0.4795 | 0.3432 | 0.4000 | 0.2500 | 61.8 |
| 6 | **section_overlap|minilm** | `section_overlap` | `minilm` | **0.3849** | 0.7500 | 0.2697 | 0.3646 | 0.2257 | 0.2000 | 0.7500 | 57.0 |

## 2. Chunking Method Comparison (Averaged across all embedding models)

| Chunker | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Throughput (chunks/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `hierarchical` | **0.8259** | 0.8750 | 0.8679 | 0.6250 | 0.7500 | 44.8 |
| `section_overlap` | **0.4328** | 0.6719 | 0.4479 | 0.3000 | 0.6250 | 39.7 |
| `fixed_size` | **0.4979** | 0.6354 | 0.5159 | 0.4500 | 0.3750 | 38.7 |

## 3. Embedding Model Comparison (Averaged across all chunking methods)

| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query Latency P50 (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `e5` | **0.5995** | 0.7396 | 0.6302 | 0.5000 | 0.5833 | 0.14 |
| `minilm` | **0.5715** | 0.7153 | 0.5909 | 0.4167 | 0.5833 | 0.14 |

## 4. Key Findings

1. **Champion Combination:** `hierarchical|minilm` achieved highest nDCG@10 of **0.8711** with MRR@10 of **0.8750**.
2. **Metric Integrity:** Pure Information Retrieval (IR) metrics evaluated directly on ranked candidate units without context concatenation or token-budget proxies.
