# RQ2-v2: Chunking Strategies Under the Production Context Budget (C-RET)

**Protocol:**
- `reports/revalidation/protocol/rq1_rq4.json` "RQ2-v2", frozen before Gate B.
- The CEC fallback was applied as recorded in `rq2_cec_fallback_applied.json` (protocol record version 8) **before this run**.
  - The CEC check reached 20/30 = 0.667 agreement, below the 0.80 required.
  - So **budgeted nDCG@10 is the primary metric** and CEC@0.5 is secondary.
  - Every other element is unchanged: Holm m = 2, SESOI 0.05.

**Script:** `eval/phases/phase_2_chunking/scripts/rq2v2_budgeted_chunking.py`. It ran unchanged; its hash matches the record.

**Outputs:**
- `summary.json` and `per_query.jsonl`.
- `smoke_3/` is the pre-registration smoke test and is not part of these results.

## Counts
- 335 papers, 567 questions, 0 failures.
- **Pipeline:**
  - `pymupdf_layout` sections → chunker → e5-small-v2 dense ranking.
  - Context assembly as in production: 1,600 estimated tokens, at most 5 units, ±200-word windowing for parents over 800 tokens.
- Run time 51 min; Python peak working set 1,361 MB.

**Index size:**

| Strategy | Units | Units per paper |
|---|---|---|
| fixed_size (400) | 7,520 | 22.4 |
| section_overlap (400/80) | 13,490 | 40.3 |
| hierarchical (200/40, production) | 22,211 children | 66.3 |

## Primary (after the fallback): budgeted nDCG@10, dense retrieval (Holm m = 2, B = 10,000, seed 42)

| Strategy | nDCG@10 | Diff hierarchical − strategy [95% CI] | Holm p |
|---|---|---|---|
| hierarchical (incumbent) | 0.445 | — | — |
| fixed_size | 0.386 | +0.059 [+0.026, +0.091] | 0.001 |
| section_overlap | 0.384 | +0.061 [+0.035, +0.088] | 0.0004 |

## Secondary: CEC (dense)

| Strategy | CEC@0.3 | CEC@0.5 | CEC@0.7 | Context tokens | Units in context |
|---|---|---|---|---|---|
| hierarchical | 0.922 | 0.732 | 0.616 | 1,318 | 3.4 |
| fixed_size | 0.961 | 0.758 | 0.575 | 1,579 | 4.0 |
| section_overlap | 0.930 | 0.743 | 0.603 | 1,244 | 4.9 |

**Hierarchical − flat, CEC:**

| τ | vs fixed_size | vs section_overlap |
|---|---|---|
| 0.5 | −0.027 [−0.067, +0.014] | −0.011 [−0.047, +0.027] |
| 0.3 | **−0.039** [−0.062, −0.016] | −0.007 [−0.030, +0.015] |
| 0.7 | +0.041 [−0.002, +0.083] | +0.012 [−0.025, +0.051] |

**Descriptive, production RRF ranking.** RRF helps the flat strategies a little (fixed_size nDCG 0.411, CEC@0.5 0.799) and not hierarchical (0.432 / 0.721).

**Latency.** Ranking plus assembly takes P50 0.26 ms and P95 0.51 ms (dense), so it is negligible.

## Decision (registered rule)
**Keep hierarchical.**
- The rule replaces hierarchical only if a flat strategy beats it by ≥ 0.05 with the CI lower bound > 0.
- **Neither metric shows that:**
  - on nDCG@10, both flat strategies are significantly worse;
  - on CEC@0.5, there is no significant difference.

## Important limitation: nDCG@10 is not a fair comparison across chunkers
- **Why:** relevance is judged per context unit.
  - Hierarchical units are whole or windowed parents, which are larger than flat 400-token chunks.
  - A larger unit is more likely to contain enough evidence to count as relevant.
  - The relevant-unit count R_q also differs between strategies.
- **So the +0.06 nDCG advantage is partly an artefact of unit size.** The EXT-RQ2-CHILD addendum records exactly this reason for not comparing nDCG across arms.
- **CEC compares like with like:** it scores the same assembled text the LLM receives. On CEC, hierarchical shows **no advantage**. fixed_size even covers more evidence at τ 0.3 (−0.039, CI below 0), helped by using ~260 more context tokens.
- **CEC has its own weakness:** its agreement with the check labels was only 0.667, and those labels are not an independent human judgment (see `cec_check_result.json`).
- **Supported wording:** "Under the production budget, no flat strategy beat hierarchical; hierarchical is kept as the incumbent. A real advantage of hierarchical is not shown: it ranks higher on nDCG@10, but that metric favours its larger units, and evidence coverage of the assembled context is similar for all three."
- **Not supported:** "hierarchical chunking is better", and the historical 0.688 nDCG@10 claim. RQ2-diag decomposes the latter.

## Precision
CEC@0.5 CI half-widths are 0.041 and 0.037, against the planned ~0.035, so slightly wider. nDCG half-widths are about 0.03. The decision doesn't depend on this, and nothing was expanded.

## Deviations
- None from the protocol.
- The fallback was applied as pre-registered, and how it was applied was recorded before the run.
