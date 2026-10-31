# RQ5-R: Reanalysis of the Stored RQ5 Generations (no inference)

**Protocol:** `reports/revalidation/protocol/rq5_rq6.json` "RQ5-R", frozen before Gate B.
**Script:** `eval/phases/phase_9_generation/scripts/rq5_reanalysis.py`. Output: `summary.json`.
**Inputs (read only):** the stored RQ5 checkpoint (500 questions × 3 models, 250 papers) and the corrected human-review attribution (`human_faithfulness_review/correction/`).
**Bootstrap:** paper-cluster paired, B = 10,000, seed 42, 250 clusters. Wilson 95% intervals for proportions.
**Role:** the RQ5 manifest was already evaluated in RQ5 (selection-stage). Everything here is descriptive reanalysis of existing answers.

## 1. Boolean accuracy (72 Boolean questions)
Rule: first yes/no token of the answer vs the majority yes/no reference. Refusals and answers without a yes/no token count as wrong.

| Model | Correct | Accuracy [Wilson 95%] | Refusals | Unparseable | Old Token F1 on the same items |
|---|---|---|---|---|---|
| llama3.2:3b | 18 | **0.250** [0.164, 0.361] | 53 | 0 | 0.042 |
| llama3.2:1b | 1 | 0.014 [0.002, 0.075] | 65 | 4 | 0.001 |
| qwen2.5:0.5b | 13 | 0.181 [0.109, 0.285] | 30 | 23 | 0.033 |

- **Token F1 badly mis-measures Boolean answers** (0.04 vs 25% accuracy for 3b). That confirms the audit finding: Boolean questions need their own metric.
- **All three models handle yes/no questions poorly under this prompt.** The main cause is refusal: 3b refuses 74% of Boolean questions (53/72), 1b 90%. Qwen refuses less but often answers without a yes/no (23 unparseable).
- **3b vs qwen on Boolean accuracy:** the intervals overlap, so no ranking.

## 2. Refusal rate differences (all 500 questions)

| Pair | Δ refusal rate [95% CI] | p (unadjusted) |
|---|---|---|
| 3b − 1b | −0.102 [−0.154, −0.050] | 0.0004 |
| 3b − qwen | **+0.386** [+0.340, +0.434] | 0.0002 |
| 1b − qwen | +0.488 [+0.440, +0.534] | 0.0002 |

Every question in the manifest is answerable from the supplied gold evidence. So every refusal here is a missed answer, unless a human judged the evidence insufficient (see section 4).

## 3. Token F1 on questions answered by both models (selection-affected, descriptive)

| Pair | Questions / papers | Mean F1 | Δ [95% CI] |
|---|---|---|---|
| 3b − 1b | 148 / 124 | 0.391 vs 0.327 | +0.063 [+0.034, +0.094] |
| 3b − qwen | 244 / 185 | 0.380 vs 0.300 | **+0.080 [+0.048, +0.111]** |
| 1b − qwen | 203 / 152 | 0.307 vs 0.273 | +0.034 [+0.007, +0.061] |

- **When 3b answers, its answers are better than qwen's** (+0.080). That reverses the all-question result (qwen +0.029), which comes from qwen refusing far less.
- **Caveat:** the subset depends on which questions each model chose to answer, so it is not a randomised comparison. It describes answer quality *given an answer*, not overall usefulness.

## 4. Human review (20 answers per model, corrected attribution, single reviewer)

| Model | Supported | Unsupported or contradicted | Unjustified refusal | Grounded compliance* |
|---|---|---|---|---|
| llama3.2:3b | 10 [0.30, 0.70] | **1** [0.01, 0.24] | 3 [0.05, 0.36] | **15** [0.53, 0.89] |
| llama3.2:1b | 7 [0.18, 0.57] | 3 [0.05, 0.36] | 6 [0.15, 0.52] | 11 [0.34, 0.74] |
| qwen2.5:0.5b | 10 [0.30, 0.70] | **7** [0.18, 0.57] | 0 [0, 0.16] | 10 [0.30, 0.70] |

*Grounded compliance = Supported + Partial + valid refusal.

- **All intervals overlap at n = 20.** These are descriptive counts, not a ranking.
- **The direction is consistent with section 3:** qwen answers almost everything, but about a third of its reviewed answers are unsupported or contradicted (7/20). 3b refuses more and makes fewer unsupported claims (1/20).

## Does this support the intended claim?
- **Supported:**
  - "llama3.2:3b is a defensible production default for grounded answering." When it answers, it is more accurate than the alternatives (section 3), and in the review sample it rarely asserts unsupported content.
  - Token F1 is unsuitable for Boolean questions; Boolean accuracy is reported instead.
- **Not supported:**
  - "llama3.2:3b is the best model" on the all-question Token F1 (qwen leads there, +0.029, through answering more).
  - Any ranking from the human review alone (n = 20 per model, one reviewer).
- **Weakness found:** high refusal on answerable questions, especially Boolean ones (3b 49% overall, 74% Boolean). The production prompt's refusal instruction is a likely factor. This is not tested here; the prompt variant was deferred in the candidate audit.

## Deviations
None. No inference was run. The historical files were read only.
