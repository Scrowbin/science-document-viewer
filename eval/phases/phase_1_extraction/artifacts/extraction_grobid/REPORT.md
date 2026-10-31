# RQ1-v2 GROBID Add-on: Report

**Type:** post-Gate-B add-on, approved by the user on 2026-10-30 and registered before the full run (`reports/revalidation/protocol/rq1_grobid_addon.json`). It is a single separate test, **not eligible for adoption in this run**.
**Server:** GROBID 0.8.2 (CRF image `grobid/grobid:0.8.2-crf`) in local Docker/WSL2, one request at a time.
**Data:** `summary.json` and `per_query.jsonl` in this folder. The extraction cache is in `eval/data/revalidation_cache/extract_grobid/`.

## Cohort counts and exclusions
- **Papers per set:**

  | Set | Role | Papers |
  |---|---|---|
  | C-RET | Primary | 335 |
  | All opened reservoir papers except C-INT | Sensitivity | 363 |
  | C-RET-150 (249 questions) | Downstream | 150 |
  | PeerQA-PDF | Descriptive | 107 |

- **Failures:** none. No GROBID extraction failed or returned an empty body.
- **C-INT:** not extracted.

## Primary result: evidence recall (C-RET, one value per paper)

| | pymupdf_layout | grobid |
|---|---|---|
| Mean evidence recall | 0.9848 | 0.9811 |

- **Difference, GROBID − pymupdf_layout:** **−0.0037**, 95% CI [−0.0130, +0.0040], p = 0.39.
- **Precision:** the CI half-width is 0.0085, well inside the planned < 0.03.
- **Rule** (≥ +0.03 with CI lower bound > 0): **not met.** The two extractors find the same share of the evidence text. Any difference larger than about ±0.013 is ruled out.
- **Sensitivity check (363 opened papers):** +0.0068 [−0.0045, +0.0179]. Same conclusion.

## Secondary results (not part of the decision)

| Measure | pymupdf_layout | grobid | Note |
|---|---|---|---|
| Heading F1 vs QASPER section names | 0.466 | 0.576 | Descriptive |
| ms per page, P50 / mean | 12.3 / 29.9 | 185.4 / 215.3 | GROBID figures are HTTP round-trips to a Docker/WSL2 container; pymupdf runs in-process. Not like-for-like |
| Failures | 0 | 0 | |
| Memory | +2.7 MB working-set increase (Python process, about 446 MB peak) | Container 3.1–3.7 GB idle, **4,096 MB peak (= the compose memory cap)**, about 3.3–3.8 GB mean | GROBID memory is `docker stats` cgroup memory (JVM heap), sampled every 1–2 s. Not comparable 1:1 with a Windows working set. Reaching the cap may have slowed GROBID; it caused no failures |
| **Downstream CEC@0.5** (C-RET-150, 249 questions; hierarchical → e5 dense → production context) | 0.739 | 0.823 | **Δ +0.084 [+0.040, +0.130]**, p = 0.0004 (unadjusted) |
| **Downstream budgeted nDCG@10** | 0.454 | 0.513 | **Δ +0.059 [+0.023, +0.094]**, p = 0.0016 (unadjusted) |
| PeerQA-PDF evidence recall (descriptive, separate) | 0.933 | 0.900 | 107 papers |

## Interpretation
- **Text recovery:** the extractors don't differ in how much of the gold evidence text they recover, so the pre-registered RQ1 question gets a clear "no difference".
- **Downstream retrieval is better with GROBID's text.** Same chunker, same embedder, same context budget.
- **Likely cause (found after the results, so a hypothesis to test, not a finding):**
  - **No reference list.** GROBID's body text has none: 0 of 349 papers have a References section, against 304 of 349 for `pymupdf_layout`.
  - **Less text overall:** median 4,108 words per paper vs 6,187.
  - **Smaller largest sections:** median largest section 739 words vs 1,113.

  Less text that doesn't carry evidence means fewer distractor chunks competing for the 1,600-token context.
- **On PeerQA (OpenReview and other formats), GROBID recovers slightly less evidence (0.900 vs 0.933).** That is descriptive only, but it shows the advantage may not carry over to other layouts.

## Protocol status and deviations
- **Decision:** `pymupdf_layout` stays, under the registered rule (GROBID can't be adopted in this run).
- **Downstream result:** a **lead for future work or a separately registered follow-up.** It is not a winner: it is a secondary metric, unadjusted, and the explanation was found after the results.
- **Deviations:**
  - The protocol named GROBID 0.8.0; 0.8.2 was used (recorded in the addendum).
  - The container reached its 4 GB memory cap (recorded here).
  - The 3-paper smoke-test bug was fixed before registration (recorded in the addendum).
- **Next step (needs the user's decision):** a cheap follow-up could test whether removing the References section from `pymupdf_layout` output gives the same downstream gain without GROBID's ~3.5 GB of memory. It would be a new, separately registered extension on C-RET, decided before it runs. It is not run automatically, because it was suggested by these results.
