# RQ3-v2: Embedding Shortlist on Fresh Papers (original frozen Phase C run)

**Protocol:** `reports/revalidation/protocol/rq1_rq4.json` "RQ3-v2", frozen before Gate B.
**Role:** selection (C-RET-150).
**Script:** `eval/phases/phase_3_embedding/scripts/rq3v2_shortlist.py`, one subprocess per model. Outputs: `summary.json`, `per_query.jsonl`, `model_*.json`.
**Bootstrap:** paper-cluster paired, B = 10,000, seed 42. Holm correction over the 4 challengers vs `intfloat/e5-small-v2`.
**Pipeline (fixed):** `pymupdf_layout` sections → `hierarchical` children (200/40) → dense-only cosine → production context assembly (1,600 estimated tokens, ≤ 5 parents, windowing).

## Counts
- **Cohort:** C-RET-150, 150 papers, 249 questions, 9,783 child units per model.
- **Failures:** none, for any model.
- **PeerQA:** not part of RQ3 (by protocol).
- **Note:** e5 was chosen historically on other papers (RQ3 v1). C-RET-150 papers are fresh (no prior exposure event), so this is a fair re-check of that choice, but it is still selection, not confirmation.

## Primary: budgeted nDCG@10

| Model | nDCG@10 | Δ vs e5 [95% CI] | Holm p | CI half-width |
|---|---|---|---|---|
| intfloat/e5-small-v2 (production) | 0.4537 | — | — | — |
| nomic-ai/modernbert-embed-base | 0.4641 | +0.0104 [−0.0239, +0.0436] | 1.00 | 0.034 |
| Snowflake/snowflake-arctic-embed-s | 0.4401 | −0.0136 [−0.0558, +0.0272] | 1.00 | 0.042 |
| BAAI/bge-small-en-v1.5 | 0.4119 | −0.0418 [−0.0838, −0.0020] | 0.12 | 0.041 |
| sentence-transformers/all-MiniLM-L6-v2 | 0.3834 | −0.0703 [−0.1194, −0.0227] | **0.012** | 0.048 |

- **Decision (rule: P50 latency ≤ 1.5× e5 and Δ ≥ +0.04 with CI lower bound > 0):** **keep `intfloat/e5-small-v2`.** No model beats it; ModernBERT is also ineligible on latency (3.7× e5).
- **Only significant difference after Holm:** MiniLM is worse than e5.
- **Precision vs plan (planned half-width ≈ 0.035):**
  - Observed 0.034–0.048, so up to ~1.4× the plan.
  - **The decision is not affected.** A switch needs a gain ≥ 0.04, and every challenger's upper CI bound except ModernBERT's (+0.044) is below that. ModernBERT is excluded by latency regardless.
  - What the data cannot do: rank e5, arctic and ModernBERT against each other. Differences of about ±0.04 are not ruled out.
  - Per the precision rule, the analysis is **not expanded**. Proposed next step if a ranking among the top three matters: none recommended now. The production choice doesn't depend on it, and RQ6 tests the combined system.

## Secondary: CEC and sensitivity

| Model | CEC@0.3 | CEC@0.5 | CEC@0.7 |
|---|---|---|---|
| e5-small-v2 | 0.940 | 0.739 | 0.639 |
| modernbert-embed-base | 0.932 | 0.743 | 0.643 |
| arctic-embed-s | 0.936 | 0.751 | 0.622 |
| bge-small-en-v1.5 | 0.932 | 0.699 | 0.594 |
| all-MiniLM-L6-v2 | 0.920 | 0.679 | 0.542 |

- CEC@0.5 Holm family vs e5: no comparison significant (MiniLM −0.060 [−0.115, −0.004], Holm p 0.15).
- The CEC ordering of the top three differs from the nDCG ordering, consistent with them being indistinguishable.
- **Cross-check:** e5 here (nDCG 0.4537, CEC 0.739) matches the `pymupdf_layout` downstream arm of RQ1-v2 (0.454, 0.739). Same papers, same pipeline, independent runs.

## Efficiency (this laptop: Ryzen 7 7735HS, CPU-only)

| Model | Indexing chunks/s | Query P50 / P95 (ms, 100 queries) | Python working set, peak (baseline ≈ 486 MB) |
|---|---|---|---|
| e5-small-v2 | 17.3 | 17.3 / 20.3 | 1,310 MB |
| all-MiniLM-L6-v2 | 44.4 | 9.4 / 10.9 | 1,132 MB |
| arctic-embed-s | 16.2 | 17.5 / 20.4 | 1,311 MB |
| bge-small-en-v1.5 | 16.6 | 17.8 / 19.7 | 1,306 MB |
| modernbert-embed-base | 3.0 | 64.5 / 70.4 | 2,176 MB |

- **Memory definition:** peak Windows working set of the model's subprocess, sampled; includes the PDF pipeline and Django imports, so the comparable part is the increase over the ~486 MB baseline.
- **Prefixes used** (logged by the run): e5 `query: ` / `passage: `; arctic and BGE the "Represent this sentence…" query instruction, no passage prefix; ModernBERT `search_query: ` / `search_document: `; MiniLM none. These match the frozen table.

## Does this support the intended claim?
- **Supported:**
  - On fresh papers, e5-small-v2 is at least as good as every small alternative tested, and clearly better than MiniLM.
  - It sits on the quality/cost frontier: ModernBERT's +0.010 (not significant) costs 3.7× query latency, 5.7× slower indexing and ~0.9 GB more memory.
- **Not supported:**
  - "e5 is significantly better than BGE / arctic." BGE's unadjusted CI excludes 0, but not after Holm; arctic is a tie.
  - "ModernBERT is the quality ceiling" (the historical framing). Here it is a statistical tie with e5.

## Deviations
None from the frozen protocol.
