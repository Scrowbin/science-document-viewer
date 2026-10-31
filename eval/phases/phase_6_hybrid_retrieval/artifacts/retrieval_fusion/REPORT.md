# RQ4-v2: Hybrid Fusion vs Dense on Fresh Papers (original frozen Phase C run)

**Protocol:** `reports/revalidation/protocol/rq1_rq4.json` "RQ4-v2", frozen before Gate B.
**Script:** `eval/phases/phase_6_hybrid_retrieval/scripts/rq4v2_fusion.py`. Outputs: `C-RET/`, `PEERQA-PDF/`, `PEERQA-TEXT/` (each `summary.json`, `per_query.jsonl`; `smoke_3/` folders are pre-Gate-B harness checks, not results).
**Pipeline (fixed):** `pymupdf_layout` → `hierarchical` 200/40 → e5-small-v2 → ranking arm → production context assembly (1,600 estimated tokens, ≤ 5 parents, windowing).
**Bootstrap:** paper-cluster paired, B = 10,000, seed 42. Holm m = 3 against dense (`rrf_prod`, `rrf_fix`, `convex_fix`).

**Arms:**
- `dense`: e5 only.
- `bm25_prod` / `rrf_prod` / `convex_prod`: the current app's whitespace BM25 (the known tokenizer defect). `rrf_prod` is what production runs today.
- `bm25_fix` / `rrf_fix` / `convex_fix`: regex tokenizer with 39 stopwords.
- Convex fusion uses α = 0.7; RRF uses k = 60.

## Primary: C-RET (selection; 335 papers, 567 questions, 0 failures)

| Arm | nDCG@10 | CEC@0.5 | Rank latency P50 / P95 (ms) |
|---|---|---|---|
| dense | **0.445** | 0.732 | 0.03 / 0.05 |
| convex_fix | 0.444 | 0.741 | 0.26 / 0.51 |
| convex_prod | 0.442 | 0.735 | 0.34 / 0.64 |
| rrf_prod (current app) | 0.432 | 0.721 | 0.35 / 0.65 |
| rrf_fix | 0.432 | 0.709 | 0.27 / 0.54 |
| bm25_fix | 0.362 | 0.676 | 0.25 / 0.50 |
| bm25_prod | 0.319 | 0.637 | 0.35 / 0.72 |

**Holm family (nDCG@10, against dense):**

| Comparison | Δ [95% CI] | Holm p | Half-width |
|---|---|---|---|
| rrf_prod − dense | −0.013 [−0.042, +0.016] | 0.91 | 0.029 |
| rrf_fix − dense | −0.013 [−0.038, +0.012] | 0.91 | 0.025 |
| convex_fix − dense | −0.002 [−0.022, +0.018] | 0.91 | 0.020 |

- **Decision (rule: dense unless a `*_fix` hybrid is ≥ +0.02 with CI lower bound > 0):** **dense.**
- **CEC@0.5 (secondary):** same picture; no comparison significant (rrf_prod −0.011, rrf_fix −0.023, convex_fix +0.009).
- **The tokenizer fix alone helps BM25** (bm25_fix 0.362 vs bm25_prod 0.319), but BM25 is far below dense (bm25_fix − dense −0.083 [−0.115, −0.052]), and fusing it adds nothing on C-RET.
- **Precision vs plan:**
  - Observed half-widths are 0.020–0.029, against the planned ~0.016. They are wider than planned.
  - **The decision holds anyway.** Every upper bound is below +0.02, so a gain of the SESOI size is excluded for all three hybrids.
  - What the data cannot exclude: a loss of up to ~0.04 for RRF. "RRF is worse than dense" is not established.
  - Not expanded (precision rule).
- **Memory:** Python working set 435 MB baseline, 1,467 MB peak (includes PDF extraction and the e5 model; ranking itself is negligible).

## Descriptive: PeerQA (separate, not pooled with QASPER, cannot change the decision)

| Arm | PEERQA-PDF nDCG@10 / CEC@0.5 (107 papers, 288 q) | PEERQA-TEXT nDCG@10 / CEC@0.5 (73 papers, 148 q) |
|---|---|---|
| dense | 0.340 / 0.816 | 0.476 / 0.845 |
| rrf_prod | 0.354 / 0.813 | 0.494 / 0.851 |
| rrf_fix | **0.380** / 0.844 | 0.512 / 0.885 |
| convex_prod | 0.366 / **0.861** | **0.523** / 0.878 |
| convex_fix | 0.375 / 0.833 | 0.517 / 0.885 |
| bm25_fix | 0.351 / 0.819 | 0.475 / 0.865 |
| bm25_prod | 0.308 / 0.771 | 0.451 / 0.838 |

Differences against dense (nDCG@10, Holm m = 3 within each cohort):

| Comparison | PEERQA-PDF | PEERQA-TEXT |
|---|---|---|
| rrf_prod − dense | +0.014 [−0.013, +0.040], p 0.28 | +0.018 [−0.015, +0.051], p 0.27 |
| rrf_fix − dense | **+0.040 [+0.018, +0.063], p 0.001** | **+0.036 [+0.010, +0.061], p 0.016** |
| convex_fix − dense | **+0.036 [+0.015, +0.059], p 0.001** | **+0.040 [+0.014, +0.067], p 0.007** |

- 0 failures in both cohorts.
- **On PeerQA the fixed-tokenizer hybrids beat dense by about +0.04, in both forms of the data.** On QASPER (C-RET) they don't.
- **Why this can't change the decision:** the protocol fixed PeerQA as descriptive before any results. C-RET is the selection set.
- **What it does mean:** the benefit of hybrid retrieval depends on the question source. A plausible reason, not tested: PeerQA questions are written by reviewers who have read the paper and reuse its terms, while QASPER questions were written from the title and abstract only, so they share fewer words with the evidence. BM25 helps more when questions share terms with the text.

## Does this support the intended claim?
- **Supported:**
  - On fresh QASPER papers, the current production RRF does not improve on dense retrieval, and no hybrid arm gains ≥ 0.02.
  - The whitespace tokenizer defect hurts BM25 by itself (0.319 vs 0.362), but has no measurable effect once fused.
- **Not supported:**
  - "Hybrid retrieval is better" (the historical RQ4 framing).
  - "Hybrid retrieval is worse." The CIs include small losses and small gains, and PeerQA points the other way.
- **Production implication (needs the user's decision at the production-change step):**
  - The registered rule makes **dense** the RQ4 winner.
  - Because PeerQA favours `rrf_fix` / `convex_fix`, a reasonable alternative is to keep a fixed hybrid as a selectable mode. RQ6 already keeps `rrf_legacy` selectable.
  - Adopting a hybrid as the default would go against the registered rule, so it can't be done on this evidence.

## Deviations
None from the frozen protocol. Planned half-width was not reached on C-RET (reported above).
