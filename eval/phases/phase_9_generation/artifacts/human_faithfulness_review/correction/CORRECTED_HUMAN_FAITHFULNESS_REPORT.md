# RQ5 Human Faithfulness Review — Corrected Unblinded Analysis

**Status:** Supersedes the per-model figures in `../UNBLINDED_HUMAN_FAITHFULNESS_REPORT.md` (kept unchanged as a historical record).
**Date:** 2026-10-29 (independent project audit)
**Scope:** 60 adjudicated answers = 20 questions × 3 models (stride-25 sample of the 500-question RQ5 manifest). One reviewer; exploratory; no inter-annotator agreement.

## 1. What was wrong

The reviewer annotated `artifacts/review_and_signed.md`. For many review items that sheet lists the three answers under different blind labels (Alpha/Beta/Gamma) than the blinded package (`HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md`, template CSV) and `restricted_model_label_mapping.json`. Example REV-03: the refusal sentence is `Model_Beta` in the package/mapping but `Model_Gamma` in the signed sheet.

`audit/parse_and_audit.py` kept the signed-sheet blind labels, and `scripts/unblind_and_analyze_faithfulness.py` joined labels to models on `(review_id, blind_label)`. Every label whose answer had moved position was therefore credited to the wrong model, while `token_f1` / containment / latency came from the mapping (the right model for that blind label, but not for that answer).

The adjudication itself is unaffected: each label still belongs to the answer text printed next to it.

## 2. Correction method

`scripts/remap_human_labels_by_answer.py` (new; no original file modified):

1. For each adjudicated row, take the answer text the reviewer saw and compare it with the three inference-checkpoint predictions (`rq5_inference_checkpoint.jsonl`) for the same `question_id`.
2. Only formatting is normalized (blockquote markers, whitespace, surrounding quotes). In practice all 60 answers matched **exactly** without normalization.
3. Question text (signed sheet, template, checkpoint) and context text (adjudicated vs template) are checked for each row: 0 mismatches.
4. A one-to-one assignment per question is required. In 7 questions (REV-01, 04, 06, 09, 12, 16, 20) two models produced byte-identical answers (15 rows, mostly the refusal sentence). Such answers cannot be told apart, but every identical copy received the same label, so the attribution among them cannot change any count. These rows are marked `VALID_IDENTICAL_ANSWERS_SAME_LABEL`.
5. Result: 60/60 accounted for, 45 `VALID` + 15 `VALID_IDENTICAL_ANSWERS_SAME_LABEL`, 0 unresolved. Of the 45 distinguishable answers, **26 had been attributed to the wrong model** and 19 were correct.

Record-level evidence: `remap_validation_report.csv` / `.json`.

**Independent checks**
- A second, separately written parser read the answer blocks directly from `review_and_signed.md` and reproduced the same per-model counts.
- Consistency with the automated refusal detector: on the same 20 items per model, detector refusals = 8 / 10 / 0 (3b / 1b / qwen). Corrected human refusal labels (`REFUSAL_VALID` + `UNJUSTIFIED_REFUSAL`) = 8 / 10 / 0, an exact match. Under the original join, 3b had only 5 refusal labels against 8 detector refusals, which is impossible.

## 3. Corrected label distribution (20 answers per model)

| Primary label | `llama3.2:3b` | `llama3.2:1b` | `qwen2.5:0.5b` | Total |
| :--- | :---: | :---: | :---: | :---: |
| SUPPORTED | 10 | 7 | 10 | 27 |
| REFUSAL_VALID | 5 | 4 | 0 | 9 |
| MISSING_INFO – PARTIAL | 1 | 0 | 3 | 4 |
| MISSING_INFO – UNJUSTIFIED_REFUSAL | 3 | 6 | 0 | 9 |
| UNSUPPORTED | 0 | 2 | 6 | 8 |
| CONTRADICTED | 1 | 1 | 1 | 3 |

Overall totals per label are unchanged by the correction (27 / 9 / 4 / 9 / 8 / 3); only the per-model split changes.

| Derived rate (n = 20 each) | 3b | 1b | qwen | Original (wrong) 3b / 1b / qwen |
| :--- | :---: | :---: | :---: | :---: |
| SUPPORTED | 50% | 35% | 50% | 50 / 45 / 40% |
| Grounded compliance (SUPPORTED + REFUSAL_VALID) | 75% | 55% | 50% | 70 / 55 / 55% |
| Unsupported or contradicted | 5% | 15% | 35% | 15 / 15 / 25% |
| Unjustified refusal | 15% | 30% | 0% | 5 / 25 / 15% |
| Partial | 5% | 0% | 15% | 10 / 5 / 5% |

## 4. Association with automated metrics (N = 60, point-biserial r)

| Pair | r |
| :--- | :---: |
| SUPPORTED vs Token F1 | +0.644 |
| SUPPORTED vs containment proxy | +0.591 |
| Grounded compliance vs Token F1 | +0.366 |
| Grounded compliance vs containment proxy | +0.260 |
| Unsupported/contradicted vs containment proxy | −0.043 |

Mean containment proxy by label: SUPPORTED 68.7%, PARTIAL 75.9%, CONTRADICTED 44.0%, UNSUPPORTED 38.2%, both refusal labels 0.0%.

Interpretation: Token F1 and containment are moderately associated with a human `SUPPORTED` judgment in this sample. The association is mostly driven by refusals, which score near zero on both metrics. Containment does **not** separate unsupported or contradicted answers from the rest (r ≈ 0), so it must not be read as a faithfulness or entailment measure. With N = 60 and one reviewer, these coefficients are descriptive only.

## 5. What the corrected data support

- `llama3.2:3b` produced the fewest unsupported/contradicted answers (1/20) and the highest grounded compliance (15/20). Its main failure mode is over-refusal (3 unjustified + 5 valid refusals).
- `qwen2.5:0.5b` ties 3b on SUPPORTED (10/20) and never refused. It produced the most unsupported or contradicted answers (7/20). This is consistent with its higher Token F1 and lower refusal rate in the 500-question experiment: it answers more often, and more of those answers are ungrounded.
- `llama3.2:1b` had the fewest SUPPORTED answers (7/20) and the most unjustified refusals (6/20).
- With 20 answers per model, differences of a few answers are not statistically meaningful. No significance test is reported, and these percentages are not population estimates.
- The automated 500-question results (Token F1 0.2033 / 0.1346 / 0.2324; refusals 48.6 / 58.8 / 10.0%) are a separate dataset and are unchanged by this correction.

## 6. Files

- `remap_validation_report.csv`, `remap_validation_report.json`: record-level mapping evidence.
- `faithfulness_annotations_unblinded_corrected.csv`, `.jsonl`: corrected unblinded dataset.
- `corrected_human_review_summary.json`: all numbers in this report.
- Superseded (kept unchanged): `../faithfulness_annotations_unblinded.csv`, `../faithfulness_annotations_unblinded.jsonl`, `../UNBLINDED_HUMAN_FAITHFULNESS_REPORT.md`.
