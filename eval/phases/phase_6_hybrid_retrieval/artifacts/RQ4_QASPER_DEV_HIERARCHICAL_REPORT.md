# RQ4 Hybrid Retrieval Benchmark Report

- **Benchmark Scope:** Official QASPER v0.3 `DEV` Split (276 papers, 892 queries)
- **Chunking Architecture:** `hierarchical` (Small-to-Big Parent Expansion under 1,600-token context budget, 5-parent cap)
- **Evidence Containment Threshold:** $\tau = 0.5$
- **Bootstrap Samples:** $B = 2000$ (Paper-cluster level, seed=42)
- **Multiple Comparisons:** Holm-Bonferroni correction applied across the 3 planned comparisons against Dense Only

| Strategy / Retrieval Arm | nDCG@10 (Primary) | nDCG@4 | Recall@20 | MRR@10 | Hit@5 (%) | $\Delta$ vs Dense [95% CI] | $p$-raw | $p$-adj (Holm) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Dense Only (e5-small-v2)` | **0.5610** | 0.5649 | 0.6499 | 0.6093 | 80.5% | +0.0000 — | — | — |
| `BM25 Only (WordPiece)` | **0.4860** | 0.4895 | 0.5818 | 0.5254 | 73.8% | -0.0750 [-0.0978; -0.0517] | 0.0010 | 0.0030 |
| `Hybrid RRF (k=60) [Prod]` | **0.5573** | 0.5613 | 0.6448 | 0.6061 | 80.4% | -0.0037 [-0.0195; +0.0116] | 0.6337 | 1.0000 |
| `Hybrid Convex (alpha=0.7)` | **0.5650** | 0.5704 | 0.6422 | 0.6172 | 80.0% | +0.0040 [-0.0098; +0.0169] | 0.5407 | 1.0000 |

*Note: Metrics are calculated end-to-end after Small-to-Big parent expansion, the 5-parent cap, and the 1,600-token context budget. They evaluate assembled prompt context quality rather than unrestricted candidate retrieval.*
