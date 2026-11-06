# EXT-RQ4-RERANK: Cross-Encoder Reranking (Selection-Stage Extension)

**Protocol:** `reports/revalidation/protocol/ext_rq4_rerank.json`, registered before the run (registry `EXP-REVAL-EXT-RQ4-RERANK`, protocol record version 5).
**Script:** `eval/phases/phase_6_hybrid_retrieval/scripts/rq4ext_rerank.py`.
**Outputs:** `summary.json`, `per_query.jsonl` (the smoke test is in `smoke_2/` and is not part of these results).
**Role:** selection-stage extension on C-RET. C-INT was not used. Separate from the frozen RQ4-v2 arms.

## Counts
- 335 papers, 567 questions (all of C-RET), 0 failures. Two MuPDF parser warnings on two PDFs. Extraction still succeeded, so there were no exclusions.
- Same pipeline as RQ4-v2: `pymupdf_layout` → hierarchical 200/40 → e5-small-v2 (shared vector cache) → ranking → production context assembly (1,600 tokens, ≤ 5 parents).
- Rerankers re-score the dense top 30 children. Model revisions: MiniLM `233902d25c`, BGE `2cfc18c941`.
- Run time 74 min, CPU-only, no other heavy job running.

## Primary: budgeted nDCG@10 vs dense (Holm m = 2, paper-cluster bootstrap B = 10,000, seed 42)

| Arm | nDCG@10 | Diff vs dense [95% CI] | Holm p | CI half-width (planned 0.016) |
|---|---|---|---|---|
| dense (baseline) | 0.445 | — | — | — |
| rerank_minilm (ms-marco-MiniLM-L6-v2) | 0.457 | +0.012 [−0.018, +0.041] | 0.46 | 0.030 |
| rerank_bge (bge-reranker-base) | 0.355 | **−0.090** [−0.122, −0.058] | 0.0004 | 0.032 |

## Secondary (not part of the decision)

| Arm | CEC@0.5 | Diff vs dense [95% CI], Holm p | CEC@0.3 | CEC@0.7 | Context tokens |
|---|---|---|---|---|---|
| dense | 0.732 | — | 0.922 | 0.616 | 1,318 |
| rerank_minilm | 0.773 | +0.041 [+0.003, +0.078], 0.050 | 0.949 | 0.646 | 1,321 |
| rerank_bge | 0.681 | −0.051 [−0.095, −0.007], 0.050 | 0.915 | 0.533 | 1,313 |

**Added latency per query (rerank step only, this CPU):**

| Arm | P50 | P95 | Bound (P95) |
|---|---|---|---|
| rerank_minilm | 1,041 ms | 1,433 ms | 1,000 ms: **fails** |
| rerank_bge | 6,338 ms | 8,574 ms | 1,000 ms: **fails** |

**Memory:** the Python working set peaked at 2,306 MB (baseline 434 MB). That peak covers the e5 encoder and both rerankers loaded together, so it is an upper bound for any single reranker.

## Decision (registered rule)
**Production keeps the RQ4-v2 decision (dense); no reranker is adopted.**
- **MiniLM** fails the quality part of the rule: +0.012 is below +0.02, the CI includes 0, and Holm p is 0.46. It also fails the latency bound (P95 1.43 s).
- **BGE** is significantly worse, and about 6× too slow.

## Precision
The CI half-widths are 0.030 and 0.032, about twice the planned 0.016. As the precision rule requires, the analysis was not expanded.
- **For BGE** the imprecision doesn't matter: the whole CI lies below 0.
- **For MiniLM** the CI's upper bound (+0.041) does not rule out a gain at or above the +0.02 threshold. So "no quality gain" is **inconclusive**, not shown.
- The latency failure holds whatever the quality result: even P50 is above 1 s.
- **Proposed next step (not run; needs approval):** none for the production decision, which latency already settles. If the thesis wants a quality claim about reranking, the honest wording is "inconclusive at this precision".

## Interpretation (descriptive)
- **MiniLM's CEC gain is a lead, not a finding.** MiniLM puts more evidence into the context (CEC@0.5 +0.041, CI just above 0, Holm p 0.050) but barely changes nDCG@10. The gain is secondary and sits at the edge of significance.
- **BGE's drop is large and consistent across metrics.** Likely contributors, none tested:
  - The rerankers score 200-token child chunks, but ranking quality is then judged on the parents built from those children.
  - bge-reranker-base was trained on query–passage data, not on scientific QA.
  - Inputs are cut off at 512 tokens.
  The registered design has no arm that would separate these causes.

## Does this support the claim?
- **Supported:** cross-encoder reranking is not worth adding to this CPU-only production pipeline under the registered rule. The latency cost alone rules it out.
- **Not supported:** "reranking does not improve retrieval quality". For MiniLM the quality result is inconclusive.

## Deviations
None. The smoke test (2 papers) ran before registration, and its output stays in `smoke_2/`.
