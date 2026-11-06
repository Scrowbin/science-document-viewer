# COMBO Stage 1: Retrieval Grid Results

**Protocol:** `reports/revalidation/protocol/combo_test.json` (registry version 9).
**Script:** `eval/phases/phase_12_combination/scripts/combo_stage1_grid.py`.
**Data:** C-RET-150, 150 QASPER v0.3 Train papers / 249 questions, a seed-42 subset of C-RET. Selection data only; C-INT was not used.
**Grid:** 2 extractors × 3 chunkers × 5 embedders × 4 retrieval modes = **120 combinations**, no LLM.
**Completed:** 2026-10-31 ~11:30. All 150 papers / 249 questions in every combination, **0 failures**.
**Production:** `pymupdf_layout | hierarchical | e5 | dense`.

## 1. Headline

- **No combination clearly beats production.**
- **Within the hierarchical chunker (nDCG@10 comparable):** the best is ModernBERT + convex fusion, +0.016 [−0.021, +0.052], Holm p = 1.0.
- **On CEC@0.5 (comparable across all 119 challengers):** one combination passes Holm, `pymupdf_layout | fixed_size | modernbert | rrf_fix`, +0.092 [+0.038, +0.149], Holm p = 0.048. Part of that gain is a bigger context (1,583 vs 1,291 tokens).
- **CEC caveat:** CEC has only moderate validation (check agreement 0.667).

## 2. Top combinations (mean budgeted nDCG@10)

| Combination | nDCG@10 | CEC@0.5 | Context tokens |
|---|---|---|---|
| pymupdf_layout · hierarchical · modernbert · convex_fix | 0.470 | 0.755 | 1,276 |
| pymupdf_layout · fixed_size · arctic · convex_fix | 0.465 | 0.803 | 1,578 |
| pymupdf_layout · hierarchical · modernbert · dense | 0.464 | 0.743 | 1,303 |
| pymupdf_layout · fixed_size · modernbert · convex_fix | 0.464 | 0.819 | 1,587 |
| pypdf · fixed_size · e5 · convex_fix | 0.463 | 0.787 | 1,578 |
| pymupdf_layout · hierarchical · arctic · convex_fix | 0.457 | 0.755 | 1,296 |
| **pymupdf_layout · hierarchical · e5 · dense (production)** | **0.454** | **0.739** | **1,291** |

nDCG@10 is **not comparable across chunkers**: relevance is judged per unit, and hierarchical units are parents. The top of the table spans only 0.454–0.470, well inside the per-comparison CI half-width of about ±0.035.

## 3. Main effects (mean over all other factors)

| Factor | nDCG@10 | CEC@0.5 |
|---|---|---|
| Extractor | pymupdf_layout 0.418 · pypdf 0.408 | 0.754 · 0.757 |
| Chunker | fixed_size 0.429 · hierarchical 0.419 · section_overlap 0.391 | 0.793 · 0.712 · 0.762 |
| Embedder | modernbert 0.425 · e5 0.420 · arctic 0.419 · bge 0.409 · minilm 0.394 | 0.769 · 0.761 · 0.757 · 0.752 · 0.739 |
| Retrieval | convex_fix 0.436 · rrf_fix 0.419 · dense 0.403 · rrf_prod 0.396 | 0.776 · 0.759 · 0.733 · 0.754 |

## 4. Interactions (what the grid adds over RQ1–RQ4)

- **Hybrid retrieval helps flat chunkers more than hierarchical ones.** Mean nDCG@10 over embedders (pymupdf_layout):

  | Chunker | dense | rrf_fix | convex_fix |
  |---|---|---|---|
  | hierarchical | 0.431 | 0.432 | 0.448 |
  | section_overlap | 0.381 | 0.406 | 0.429 |
  | fixed_size | 0.406 | 0.439 | 0.449 |

  With e5 on hierarchical, convex is −0.005 against dense, which matches RQ4-v2 ("hybrid adds nothing"). Averaged over the weaker embedders, convex adds +0.02 to +0.05. So RQ4's conclusion holds for the production chunker and embedder, but does not hold in general.
- **The old production fusion (`rrf_prod`, whitespace tokenizer) is the worst mode for every chunker.** This confirms the RQ4 switch away from it.
- **Chunker × embedder:** the ranking of embedders is the same under each chunker; ModernBERT is first or second everywhere. There is no sign that one embedder needs a particular chunker.
- **CEC favours fixed_size,** which fills more of the 1,600-token budget (≈ 1,580 tokens against ≈ 1,290 for hierarchical). Part of its CEC lead is more text, not better ranking.

## 5. Efficiency (one subprocess per embedder; AMD Ryzen 7 7735HS, CPU only)

| Embedder | Query P50 / P95 (ms) | Indexing (chunks/s, uncached batches) | Peak Python working set |
|---|---|---|---|
| minilm | 17.2 / 23.5 | ≈ 23 | 1,533 MB |
| bge | 27.5 / 32.6 | 6.4–11.5 | 2,001 MB |
| arctic | 29.5 / 34.3 | 5.6–9.9 | 1,598 MB |
| e5 | 30.1 / 45.9 | 5.6–5.9 (most batches were cache hits from RQ2/RQ3) | 1,819 MB |
| modernbert | 89.1 / 109.1 | 0.6–2.0 | **13,845 MB** |

**Caveats:**
- **ModernBERT memory, observed but not yet explained.** The 13.8 GB peak is far above RQ3-v2's 2.2 GB for the same model. A likely cause, not yet tested: badly extracted text (e.g. pypdf words run together) makes very long subword sequences, and ModernBERT accepts up to 8,192 tokens where the other models truncate at 512. On a 13.7 GB laptop this means swapping, which also slowed the run (about 8.5 h for ModernBERT). It is a deployment risk for ModernBERT on raw PDFs.
- **ModernBERT latency:** 89 ms here against 64.5 ms in RQ3-v2. My smoke tests and test runs overlapped part of this worker, so treat its timing as an upper bound.

## 6. Registered outputs for stage 2

- **Shortlist** (rule: top 2 per chunker by nDCG@10, ties by CEC@0.5, plus production):
  1. pymupdf_layout · hierarchical · modernbert · convex_fix
  2. pymupdf_layout · hierarchical · modernbert · dense
  3. pymupdf_layout · section_overlap · modernbert · convex_fix
  4. pymupdf_layout · section_overlap · arctic · convex_fix
  5. pymupdf_layout · fixed_size · arctic · convex_fix
  6. pymupdf_layout · fixed_size · modernbert · convex_fix
  7. pymupdf_layout · hierarchical · e5 · dense (production)

  The semantic add-on (`combo_semantic_addon.json`) adds its top 2 combinations before stage 2 starts.
- **Gate thresholds** (rule: e5 keeps 0.80; other embedders get the threshold with production's gate-refusal rate on these questions, **2.4%**): ModernBERT 0.26–0.31, arctic 0.545–0.558, production 0.80.

## 7. Interpretation

- **Production holds up.** Of the 119 alternatives, one beats it significantly, and only on the secondary metric, partly by using more context. Stage 2 decides whether that or anything else on the shortlist gives better *answers*.
- **The grid reveals interactions that one-factor-at-a-time testing missed.** Fusion only pays off with weaker embedders or flat chunkers; it does not with the production pair.
- **ModernBERT is the most accurate retrieval embedder on average,** but at 3× the query latency, a third of the indexing speed and a memory risk.

Outputs: `summary.json`, `per_query.jsonl`, `embedder_<name>.json` (this folder); run log `../stage1_run.log`.
