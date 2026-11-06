# Phase 2: Retrieval Evaluation Report — Cohort [C-RET-150]

- **Cohort:** C-RET-150
- **Papers (loaded / requested):** 1 / 1
- **Questions in loaded papers:** 2
- **Common scored questions (all active chunkers):** 2
- **Section sources:** {'json:train': 1}
- **Total Combinations Tested:** 3 (Chunkers × Embedders)
- **Metric basis:** common question set (N=2)
- **Evaluation Time:** 11.9 s

## 1. Overall Leaderboard (Ranked by nDCG@10 on common question set (N=2))

| Rank | Combination | Chunker | Granularity | Model | nDCG@10 | MRR@10 | MAP@10 | Recall@10 | Recall@5 | Prec@5 | Hit@1 | N (scored) | N (own) | Skipped (no rel / no units) | Index tput (c/s) |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **hierarchical|e5** | `hierarchical` | parent | `e5` | **1.0000** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.2000 | 1.0000 | 2 | 2 | 0 / 0 | 22.8 |
| 2 | **section_overlap|e5** | `section_overlap` | chunk | `e5` | **0.7821** | 0.7500 | 0.6750 | 1.0000 | 0.7500 | 0.2000 | 0.5000 | 2 | 2 | 0 / 0 | 13.8 |
| 3 | **fixed_size|e5** | `fixed_size` | chunk | `e5` | **0.4890** | 0.3500 | 0.2964 | 1.0000 | 0.7500 | 0.2000 | 0.0000 | 2 | 2 | 0 / 0 | 12.5 |

## 2. Chunking Method Comparison (averaged across embedding models; common question set (N=2))

> `hierarchical` retrieves at parent-section granularity; flat chunkers retrieve at
> 400-token chunk granularity. P@k, MAP and nDCG are therefore not on the same units.

| Chunker | Granularity | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | N (scored) | Index tput (c/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `hierarchical` | parent | **1.0000** | 1.0000 | 1.0000 | 0.2000 | 1.0000 | 2 | 22.8 |
| `section_overlap` | chunk | **0.7821** | 0.7500 | 1.0000 | 0.2000 | 0.5000 | 2 | 13.8 |
| `fixed_size` | chunk | **0.4890** | 0.3500 | 1.0000 | 0.2000 | 0.0000 | 2 | 12.5 |

## 3. Embedding Model Comparison (averaged across chunking methods; common question set (N=2))

| Model | Mean nDCG@10 | Mean MRR@10 | Mean Recall@10 | Mean Prec@5 | Mean Hit@1 | Query P50 (ms) | Query P95 (ms) | Peak Memory (MB) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `e5` | **0.7570** | 0.7000 | 1.0000 | 0.2000 | 0.5000 | 12.36 | 12.63 | 1463.6 |

## 4. Key Findings

1. **Top Combination:** `hierarchical|e5` (parent granularity) achieved the highest nDCG@10 of **1.0000** with MRR@10 of **1.0000** on the common question set (N=2).
2. **Best flat-chunk combination:** `section_overlap|e5` with nDCG@10 **0.7821**, MRR@10 **0.7500**. Hierarchical is scored on larger parent sections, so its lead is not like-for-like.
3. **Metric Integrity:** Pure IR metrics on ranked candidate units; unit-L2 normalized; deterministic tie-breaking.
4. **Section sources:** see `section_sources` in `summary.json` — PDF and JSON text are mixed if not all PDFs are present (counts: {'json:train': 1}); evidence matching at τ=0.5 behaves differently on each.
5. **Relevance consistency:** 0 queries had more hits than R_q (relevance counter vs hit test disagree); this should be 0.
6. **Failures:** 0 recorded in `summary.json`.
