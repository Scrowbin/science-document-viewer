# EXT-RQ3-SPECTER2: Scientific-Domain Embedding (Selection-Stage Extension)

**Protocol:** `reports/revalidation/protocol/ext_rq3_specter2.json`, registered before the run (registry `EXP-REVAL-EXT-RQ3-SPECTER2`, protocol record version 5).
**Script:** `eval/phases/phase_3_embedding/scripts/rq3ext_specter2.py`.
**Outputs:** `summary.json`, `per_query.jsonl` (the smoke test is in `smoke_2/` and is not part of these results).
**Role:** selection-stage extension on C-RET-150. C-INT was not used. This is a single separate test, not part of the frozen RQ3-v2 Holm family.

## Counts
- 150 papers, 249 questions, 0 failures. All 249 are paired with the e5 rows from RQ3-v2 (same papers, questions and pipeline).
- MuPDF printed parser warnings on one PDF. Extraction still succeeded, so nothing was excluded.
- **Model:** `allenai/specter2_base` with the adapters the model card prescribes for ad-hoc search: `specter2_adhoc_query` for questions, `specter2` (proximity) for passages. Embedding = [CLS], L2-normalised, max length 512.

## Primary: budgeted nDCG@10 (paper-cluster bootstrap B = 10,000, seed 42)

| Model | nDCG@10 | Diff vs e5 [95% CI] | p | CI half-width (planned 0.035) |
|---|---|---|---|---|
| e5-small-v2 (RQ3-v2 rows) | 0.454 | — | — | — |
| SPECTER2 | 0.281 | **−0.173** [−0.219, −0.128] | 0.0002 | 0.045 |

## Secondary and efficiency

| Model | CEC@0.3 | CEC@0.5 | CEC@0.7 | Query P50 / P95 (ms) | Indexing (chunks/s) | Peak working set |
|---|---|---|---|---|---|---|
| e5-small-v2 | 0.940 | 0.739 | 0.639 | 17.3 / 20.3 | 17.3 (RQ3-v2) | 1,310 MB (RQ3-v2) |
| SPECTER2 | 0.908 | 0.606 | 0.446 | 48.9 / 53.9 | 4.9 | 1,963 MB |

- **CEC@0.5 difference:** −0.133 [−0.195, −0.070].
- **Where the e5 figures come from:** the e5 latency, throughput and memory were measured in the RQ3-v2 run on the same machine, not in this run.

## Decision (registered rule)
**Keep `intfloat/e5-small-v2`.** SPECTER2 fails every part of the rule:
- it is 0.173 below e5, where the rule needs at least +0.04 above;
- its CI is entirely below 0;
- its P50 latency is 2.8× e5's, where the rule allows at most 1.5×.

## Precision
The CI half-width is 0.045, wider than the planned 0.035. This doesn't affect the decision, because the whole interval lies far below 0. Nothing was expanded.

## Interpretation (descriptive)
The result matches the caveat registered in advance. SPECTER2 was trained for similarity between whole papers (title + abstract), and its ad-hoc query adapter targets paper search, not finding passages inside one paper. Being in the scientific domain did not make up for that mismatch. It was the worst model tested in RQ3-v2 and in this extension, below MiniLM's 0.383.

## Does this support the claim?
- **Supported:** a general-purpose retrieval embedder (e5-small-v2) is the better choice for passage QA within a paper than the scientific-domain SPECTER2. It wins clearly on accuracy, latency and memory.
- **Limitation:** only one scientific-domain model and one adapter configuration were tested. Other domain models (e.g. SciNCL), or domain models fine-tuned for retrieval, were not.

## Deviations
None.
