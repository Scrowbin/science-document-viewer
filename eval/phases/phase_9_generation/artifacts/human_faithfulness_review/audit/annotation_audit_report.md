# RQ5 Human Faithfulness Annotation Audit Report

**Audit Date:** 2026-10-28
**Auditor:** AI-Assisted Systematic Audit (pending human adjudication)
**Status:** FINAL_ADJUDICATED — All 21 flagged items adjudicated and finalized with human reviewer decisions

---

## 1. Scope and Source Artifacts

| Artifact | Path | SHA-256 |
| :--- | :--- | :--- |
| **Completed Signed Review** | `eval/phases/phase_9_generation/artifacts/review_and_signed.md` | `A8EC115428EAB2A682D236571D23DB48F431AFDEECDBFED3851D72419C711340` |
| **Reviewer Guide & Template** | `eval/.../human_faithfulness_review/HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md` | `19DACE386B93C9ACC751A682E1A06BA629CB97352DA9B7C72BE8361277EE3CC8` |
| **CSV Template** | `eval/.../faithfulness_annotation_template_60a.csv` | `92A66CFB420CCF599A94F0A8CCB49ADC25BED0649235C80CCEE39688983DAD69` |
| **JSONL Template** | `eval/.../faithfulness_annotation_template_60a.jsonl` | `20F675DF1C5DD0E9D6104275666AEADD6FBF42B7591568070A31732B523BB369` |
| **Sampling Manifest** | `eval/.../sampling_and_integrity_manifest.json` | `55A4DB0CC652424A680E6365512A53976E66A5C96CFCB041CB7DDD94F19CF42C` |
| **Restricted Mapping** | `eval/.../restricted_model_label_mapping.json` | `86209129EE85C81ECF1B5AF32E1685CB4F19B397E88278B54120F210D2137F49` |

**None of the above source artifacts were modified during this audit.** All audit outputs are placed in the separate `audit/` subdirectory.

---

## 2. Structural Validation Results

### 2.1 Record Count and Completeness

| Check | Result |
| :--- | :---: |
| Total annotation records parsed | **60** ✅ |
| Unique review IDs (REV-01 to REV-20) | **20** ✅ |
| Records per review ID | **3 each** ✅ |
| Model_Alpha records | **20** ✅ |
| Model_Beta records | **20** ✅ |
| Model_Gamma records | **20** ✅ |
| All primary labels in valid taxonomy | **60/60** ✅ |
| Structural errors | **0** |

### 2.2 Manifest Consistency

The sampling manifest specifies 20 questions (stride-25 from 500-question manifest) × 3 blinded models = 60 answers. The parsed records match manifest item indices 1, 26, 51, 76, 101, 126, 151, 176, 201, 226, 251, 276, 301, 326, 351, 376, 401, 426, 451, 476. **No duplicates, missing records, or misassigned answers detected.**

### 2.3 Blinding Integrity

No model identity, parameter count, Token F1 score, or gold reference answer was found in any reviewer-facing field. Blinding appears intact.

---

## 3. Overall Label Distribution (As-Annotated, Pre-Audit)

| Primary Label | Count | % |
| :--- | :---: | :---: |
| SUPPORTED | 33 | 55.0% |
| UNSUPPORTED | 9 | 15.0% |
| MISSING_INFO - UNJUSTIFIED_REFUSAL | 7 | 11.7% |
| MISSING_INFO - PARTIAL | 5 | 8.3% |
| REFUSAL_VALID | 3 | 5.0% |
| CONTRADICTED | 3 | 5.0% |
| **Total** | **60** | **100%** |

### Label Distribution by Blind Model (Pre-Audit)

| Label | Alpha | Beta | Gamma |
| :--- | :---: | :---: | :---: |
| SUPPORTED | 8 | 11 | 14 |
| UNSUPPORTED | 3 | 5 | 1 |
| MISSING_INFO - UNJUST_REFUSAL | 5 | 1 | 1 |
| MISSING_INFO - PARTIAL | 0 | 2 | 3 |
| REFUSAL_VALID | 2 | 1 | 0 |
| CONTRADICTED | 2 | 0 | 1 |

---

## 4. Completeness Assessment

Of 60 records, **47 have at least one incomplete annotation field**:
- **Claims breakdown missing/blank:** 40 records have only the empty template `*Claim 1:*` with no actual claim text.
- **Supporting context quote missing:** 42 records have no supporting evidence quote.
- **Reviewer notes missing:** 25 records have no justification text.

The review guide instructs reviewers to record claim-by-claim breakdowns, supporting quotes, and notes. Many records were annotated with only the primary label checked and no elaboration. While the guide recommends these fields, the reviewer treated many straightforward cases (especially unanimous SUPPORTED across all 3 models) as self-evident. **This is a completeness concern but does not by itself invalidate the primary labels.**

---

## 5. Detailed Audit of All 60 Annotations

### Legend

- ✅ **PASS** — Label is consistent with answer, context, rationale, and protocol
- ⚠️ **FLAG** — Potential issue requiring human review
- ❌ **INCONSISTENT** — Clear protocol violation or label/rationale contradiction

---

### REV-01: "What formalism does Grail use?" (arXiv:1602.00812)

**Context summary:** The text discusses "the underlying formalism of the theorem provers" and describes type-logical grammars as "a family of grammar formalisms built on a foundation of logic and type theory." It states the chapter covers "automated theorem proving for type-logical grammars."

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | REFUSAL_VALID | ⚠️ |
| Beta | Refusal boilerplate | REFUSAL_VALID | ⚠️ |
| Gamma | "type-logical grammars" | CONTRADICTED | ❌ |

**REV-01 Alpha/Beta (REFUSAL_VALID):** The context says "This chapter describes the underlying formalism of the theorem provers" and discusses type-logical grammars extensively. The text strongly implies (though does not explicitly state with the phrase "Grail uses") that the formalism is type-logical grammars. A reasonable reviewer could judge either way: the context is about a chapter in a book about the Grail prover, describing its formalism as type-logical grammars — or alternatively, the word "Grail" does not appear in this specific excerpt. The reviewer's note says "did not directly mention formalisms for the grail." This is a borderline judgment — the title of the chapter is about the Grail prover's formalism and the text introduces type-logical grammars in that context. **Classification: Semantic judgment requiring review.** Could be REFUSAL_VALID (if the reviewer considers the missing explicit link to "Grail" in the excerpt sufficient) or MISSING_INFO - UNJUSTIFIED_REFUSAL (if the context is deemed sufficient). **Retain pending adjudication.**

**REV-01 Gamma (CONTRADICTED):** ❌ The answer "The Grail theorem provers use a formalism called type-logical grammars" is either SUPPORTED (if the context's discussion of the prover's formalism is taken as implying this) or UNSUPPORTED (if the explicit link is considered missing). The reviewer's note says "Given text did not mention that type-logical grammars was used by the Grail." This rationale describes an *unsupported* claim, not a *contradicted* one. Nothing in the context contradicts this claim. **Proposed correction: UNSUPPORTED** (the reviewer's own reasoning is that the claim is not supported, not that it conflicts with the text).

---

### REV-02: "Do the authors equate drunk tweeting with drunk texting?" (arXiv:1610.00879)

**Context summary:** The paper introduces "drunk-texting prediction" as a task, then says "Given a tweet, the goal is to automatically identify if it was written by a drunk user. We refer to tweets written under the influence of alcohol as 'drunk tweets'." The authors treat drunk-texting prediction using tweets — effectively equating the concepts.

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | "do not equate" | CONTRADICTED | ⚠️ |
| Beta | "do not equate..." | UNSUPPORTED | ❌ |
| Gamma | "Yes, equate" | SUPPORTED | ✅ |

**REV-02 Alpha (CONTRADICTED):** The reviewer's own rationale says: "Supported. The authors treat drunk tweeting as synonymous with drunk texting..." This is a direct contradiction between the rationale and the label — *at first glance*. However, the rationale's opening word "Supported" appears to refer to the *reviewer's own assessment* that the authors equate the concepts — which indeed means Alpha's answer contradicts the context. The label CONTRADICTED is actually correct. The rationale is confusingly worded but the logic is: "The context supports that the authors equate them → Alpha's claim that they don't equate them contradicts the context." **Retain CONTRADICTED, but flag the confusing rationale language.**

**REV-02 Beta (UNSUPPORTED):** ❌ Same answer content as Alpha. Beta says "do not equate" and adds "The context does not provide information on whether the authors consider drunk tweeting to be equivalent to drunk texting." The reviewer's rationale again says "Supported" referring to the context supporting the equivalence. The model's first claim ("do not equate") is actually CONTRADICTED by the context per the reviewer's own analysis. The second claim ("context does not provide information") is also CONTRADICTED — the context clearly does show the equivalence. Per precedence, CONTRADICTED > UNSUPPORTED. **Proposed correction: CONTRADICTED** (consistent with Alpha's treatment of the same claim).

---

### REV-03: "What corpus was the source of the OpenIE extractions?" (arXiv:1704.05572)

**Context summary:** Clearly states "We use the text corpora (S)... We take the top 200 hits, run Open IE v4." Also: "The Sentence corpus (S) consists of domain-targeted ~80K sentences and 280 GB of plain text."

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Correct: Sentence corpus (S) | SUPPORTED | ✅ |
| Beta | Correct: Sentence corpus (S) | MISSING_INFO - PARTIAL | ⚠️ |
| Gamma | Refusal boilerplate | UNSUPPORTED | ❌ |

**REV-03 Beta (MISSING_INFO - PARTIAL):** Beta says "The source of the OpenIE extractions was the Sentence corpus (S)" — this is the correct core answer. The reviewer may have expected more detail. Reasonable judgment. **Retain.**

**REV-03 Gamma (UNSUPPORTED):** ❌ Gamma gives the standard refusal boilerplate. Per protocol, refusals should be labeled REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL, not UNSUPPORTED. The context clearly contains the answer, so the refusal is unjustified. The reviewer's note says "It claimed that there was no mentioned of the corpus, in which it did." **Proposed correction: MISSING_INFO - UNJUSTIFIED_REFUSAL.**

---

### REV-04: "Which are the four Arabic dialects?" (arXiv:1709.00387)

**Context:** Lists *five* dialects: Egyptian, Levantine, Gulf, North African, and MSA. All three models list only four (excluding MSA).

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | 4 dialects (no MSA) | SUPPORTED | ⚠️ |
| Beta | 4 dialects (no MSA) | SUPPORTED | ⚠️ |
| Gamma | 4 dialects (no MSA) | SUPPORTED | ⚠️ |

The question itself asks for "four" and the models provided four that are indeed mentioned in the context. However, the context says there are *five*. MSA is excluded by all models. The question frames the answer scope. **Retain SUPPORTED but note the MSA omission as a borderline case.**

---

### REV-05: "What dataset did they use?" (arXiv:1711.04457)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | MISSING_INFO - UNJUST_REFUSAL | ✅ |
| Beta | Validation set only | MISSING_INFO - PARTIAL | ✅ |
| Gamma | One direction only | MISSING_INFO - PARTIAL | ✅ |

**All labels are defensible. Retain all.**

---

### REV-06: "What languages are explored?" (arXiv:1805.12070)

All three: "Mandarin and English" → SUPPORTED. ✅ **Retain all.**

---

### REV-07: "Which baselines are they using?" (arXiv:1808.10113)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | MISSING_INFO - UNJUST_REFUSAL | ✅ |
| Beta | All 5 baselines | SUPPORTED | ✅ |
| Gamma | All 5 baselines | SUPPORTED | ✅ |

**All correct. Retain all.**

---

### REV-08: "Does their solution involve connecting images and text?" (arXiv:1811.01299)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | MISSING_INFO - UNJUST_REFUSAL | ✅ |
| Beta | Yes, with elaboration | SUPPORTED | ⚠️ |
| Gamma | Yes, with close paraphrase | SUPPORTED | ✅ |

**REV-08 Beta (SUPPORTED):** Beta adds "generates a visual description of the input text, which can then be used to convey the meaning of the text through images." Minor extrapolation risk but core claim is supported. **Retain.**

---

### REV-09: "What datasets were used?" (arXiv:1904.03339)

**Context:** "JESSI is trained using only the datasets given on the shared task" — no specific dataset names mentioned.

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | **SUPPORTED** | ❌ |
| Beta | "datasets are provided in the context" | UNSUPPORTED | ⚠️ |
| Gamma | Refusal boilerplate | **SUPPORTED** | ❌ |

**REV-09 Alpha & Gamma (SUPPORTED):** ❌ Both give refusal boilerplate. A refusal cannot be SUPPORTED. The context references datasets but doesn't name them. The refusal is arguably justified. **Proposed correction: REFUSAL_VALID.**

**REV-09 Beta (UNSUPPORTED):** Beta claims datasets are "provided in the context" — they are referenced but not named. UNSUPPORTED is defensible. **Retain.**

---

### REV-10: "How was the dataset built?" (arXiv:1905.10044)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Detailed correct description | SUPPORTED | ✅ |
| Beta | Refusal boilerplate | UNSUPPORTED | ❌ |
| Gamma | Entirely fabricated description | MISSING_INFO - PARTIAL | ❌ |

**REV-10 Beta (UNSUPPORTED):** ❌ Refusal boilerplate labeled UNSUPPORTED. Context clearly describes dataset construction. **Proposed correction: MISSING_INFO - UNJUSTIFIED_REFUSAL.**

**REV-10 Gamma (MISSING_INFO - PARTIAL):** ❌ The answer fabricates completely: "aggregating and analyzing a large corpus of text data... scientific articles to news articles... personal experiences to historical events." None of this is in the context. This is not partial coverage — it's wholly fabricated. **Proposed correction: UNSUPPORTED.**

---

### REV-11: "Which dataset do they use?" (arXiv:1907.11907)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | REFUSAL_VALID | ⚠️ |
| Beta | "reference corpus of 21,093 tokens" | SUPPORTED | ✅ |
| Gamma | "reference corpus of 21,093 tokens" | SUPPORTED | ✅ |

**REV-11 Alpha:** Borderline. Context does mention the corpus. Reviewer considered information insufficient. **Retain pending adjudication.**

---

### REV-12: "What is the problem with existing metrics?" (arXiv:1908.10383)

**Context:** Only "Building Extractive CNN/Daily Mail" (34 chars — a table header, not evidence).

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Fabricated answer | UNSUPPORTED | ✅ |
| Beta | Refusal boilerplate | **SUPPORTED** | ❌ |
| Gamma | Refusal boilerplate | **SUPPORTED** | ❌ |

**REV-12 Beta & Gamma (SUPPORTED):** ❌ Refusals labeled SUPPORTED. Context is genuinely insufficient. **Proposed correction: REFUSAL_VALID.**

---

### REV-13: "What data is used to build the embeddings?" (arXiv:1909.03544)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | 4 points (2 correct, 2 wrong) | CONTRADICTED | ⚠️ |
| Beta | Lists models, not data | UNSUPPORTED | ⚠️ |
| Gamma | Only LINDAT/CLARIN | MISSING_INFO - PARTIAL | ✅ |

**REV-13 Alpha (CONTRADICTED):** Point 3 misattributes FastText training data (says UD Czech; context says Czech Wikipedia). This is arguable as either contradiction (wrong source stated) or unsupported (source not mentioned). CONTRADICTED is defensible. **Retain.**

**REV-13 Beta (UNSUPPORTED):** Lists model architectures instead of training data. Defensible. **Retain.**

---

### REV-14: "How do they measure diversity?" (arXiv:1909.08824)

All labels defensible. ✅ **Retain all.**

---

### REV-15: "Which language ID systems are tested?" (arXiv:1910.06748)

All three list all 5 systems correctly → SUPPORTED. ✅ **Retain all.**

---

### REV-16: "What challenges does this work present?" (arXiv:1911.03310)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Refusal boilerplate | MISSING_INFO - UNJUST_REFUSAL | ✅ |
| Beta | First point correct, rest fabricated | UNSUPPORTED | ✅ |
| Gamma | Refusal boilerplate | MISSING_INFO - UNJUST_REFUSAL | ✅ |

**All correct. Retain all.**

---

### REV-17: "What is their baseline model?" (arXiv:1911.13066)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Misattributes model name | UNSUPPORTED | ✅ |
| Beta | "model proposed in BIBREF3" | SUPPORTED | ✅ |
| Gamma | "model proposed in BIBREF3" | SUPPORTED | ✅ |

**All correct. Retain all.**

---

### REV-18: "What is the previous work's model?" (arXiv:1912.13109)

All three: Ternary Trans-CNN → SUPPORTED. ✅ **Retain all.**

---

### REV-19: "What type of documents are supported?" (arXiv:2002.01861)

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | PDFs and Microsoft Word | SUPPORTED | ✅ |
| Beta | Refusal boilerplate | MISSING_INFO - UNJUST_REFUSAL | ✅ |
| Gamma | PDFs and Microsoft Word, converts | SUPPORTED | ✅ |

**All correct. Retain all.**

---

### REV-20: "What genres do the songs fall under?" (arXiv:2003.05377)

**Context:** References 14 genres "shown in Table TABREF8" but does NOT list them.

| Model | Answer | Label | Audit |
| :--- | :--- | :--- | :---: |
| Alpha | Fabricated genres | UNSUPPORTED | ✅ |
| Beta | Refusal boilerplate | **SUPPORTED** | ❌ |
| Gamma | Refusal boilerplate | **SUPPORTED** | ❌ |

**REV-20 Beta & Gamma (SUPPORTED):** ❌ Refusals labeled SUPPORTED. Genres are not in the supplied context. Refusal is justified. **Proposed correction: REFUSAL_VALID.**

---

## 6. Issue Summary by Category

### 6.1 Clear Protocol Inconsistencies (Proposed Corrections)

| # | Record | Original Label | Issue | Proposed Label | Confidence |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | REV-09/Alpha | SUPPORTED | Refusal labeled SUPPORTED | REFUSAL_VALID | HIGH |
| 2 | REV-09/Gamma | SUPPORTED | Refusal labeled SUPPORTED | REFUSAL_VALID | HIGH |
| 3 | REV-12/Beta | SUPPORTED | Refusal labeled SUPPORTED | REFUSAL_VALID | HIGH |
| 4 | REV-12/Gamma | SUPPORTED | Refusal labeled SUPPORTED | REFUSAL_VALID | HIGH |
| 5 | REV-20/Beta | SUPPORTED | Refusal labeled SUPPORTED | REFUSAL_VALID | HIGH |
| 6 | REV-20/Gamma | SUPPORTED | Refusal labeled SUPPORTED | REFUSAL_VALID | HIGH |
| 7 | REV-03/Gamma | UNSUPPORTED | Refusal labeled UNSUPPORTED | MISSING_INFO - UNJUST_REFUSAL | HIGH |
| 8 | REV-10/Beta | UNSUPPORTED | Refusal labeled UNSUPPORTED | MISSING_INFO - UNJUST_REFUSAL | HIGH |

### 6.2 Semantic Inconsistencies (Proposed Corrections Requiring Judgment)

| # | Record | Original Label | Issue | Proposed Label | Confidence |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 9 | REV-01/Gamma | CONTRADICTED | Claim unsupported, not contradicted | UNSUPPORTED | MEDIUM |
| 10 | REV-02/Beta | UNSUPPORTED | Same claim as Alpha; Alpha is CONTRADICTED | CONTRADICTED | MEDIUM |
| 11 | REV-10/Gamma | MISSING_INFO - PARTIAL | All claims fabricated; none from context | UNSUPPORTED | MEDIUM |

### 6.3 Rationale Wording Issues (No Label Change Needed)

| # | Record | Issue |
| :---: | :--- | :--- |
| 12 | REV-02/Alpha | Rationale says "Supported" but means "context supports equivalence" — CONTRADICTED label is correct |
| 13 | REV-02/Beta | Same confusing wording |

### 6.4 Borderline Cases Flagged for Review (No Change Proposed)

| # | Record | Current Label | Issue |
| :---: | :--- | :--- | :--- |
| 14 | REV-01/Alpha | REFUSAL_VALID | Context arguably sufficient; could be UNJUST_REFUSAL |
| 15 | REV-01/Beta | REFUSAL_VALID | Same as Alpha |
| 16 | REV-04/All | SUPPORTED | Context says 5 dialects; models list 4 |
| 17 | REV-08/Beta | SUPPORTED | Minor extrapolation in elaboration |
| 18 | REV-11/Alpha | REFUSAL_VALID | Context does contain dataset info |

---

## 7. Reconciled Adjudication Impact Analysis

### 7.1 Final Label Distribution (Post-Adjudication vs Original)

| Primary Label | Original Signed Count | Final Adjudicated Count | Δ | % of Final (N=60) |
| :--- | :---: | :---: | :---: | :---: |
| **SUPPORTED** | 33 | **27** | -6 | 45.0% |
| **REFUSAL_VALID** | 3 | **9** | +6 | 15.0% |
| **UNSUPPORTED** | 9 | **8** | -1 | 13.3% |
| **MISSING_INFO - UNJUSTIFIED_REFUSAL** | 7 | **9** | +2 | 15.0% |
| **MISSING_INFO - PARTIAL** | 5 | **4** | -1 | 6.7% |
| **CONTRADICTED** | 3 | **3** | +0 | 5.0% |
| **Total** | **60** | **60** | **0** | **100.0%** |

### 7.2 Final Adjudicated Distribution by Blind Model

| Primary Label | Model_Alpha | Model_Beta | Model_Gamma | Total |
| :--- | :---: | :---: | :---: | :---: |
| **SUPPORTED** | 7 | 9 | 11 | 27 |
| **REFUSAL_VALID** | 3 | 3 | 3 | 9 |
| **UNSUPPORTED** | 3 | 3 | 2 | 8 |
| **MISSING_INFO - UNJUSTIFIED_REFUSAL** | 5 | 2 | 2 | 9 |
| **MISSING_INFO - PARTIAL** | 0 | 2 | 2 | 4 |
| **CONTRADICTED** | 2 | 1 | 0 | 3 |
| **Total** | **20** | **20** | **20** | **60** |

### 7.3 Complete Transition Breakdown (Original → Adjudicated)

All 11 actual label transitions applied during adjudication:
- **`SUPPORTED` → `REFUSAL_VALID` (6 transitions):**
  - REV-09 Alpha, REV-09 Gamma
  - REV-12 Beta, REV-12 Gamma
  - REV-20 Beta, REV-20 Gamma
- **`UNSUPPORTED` → `MISSING_INFO - UNJUSTIFIED_REFUSAL` (2 transitions):**
  - REV-03 Gamma
  - REV-10 Beta
- **`CONTRADICTED` → `UNSUPPORTED` (1 transition):**
  - REV-01 Gamma (lack of mention is ungrounded claim, not explicit contradiction)
- **`UNSUPPORTED` → `CONTRADICTED` (1 transition):**
  - REV-02 Beta (asserted negation contradictory to context, aligned with Alpha)
- **`MISSING_INFO - PARTIAL` → `UNSUPPORTED` (1 transition):**
  - REV-10 Gamma (fully fabricated explanation with zero grounding from text)

All other 49 records (including 10 verified/retained flagged records and 39 unflagged records) maintained their original primary label.

---

## 8. Audit Status

| Category | Count |
| :--- | :---: |
| Records audited | 60/60 |
| Clear protocol inconsistencies (high confidence) | 8 |
| Semantic inconsistencies (medium confidence) | 3 |
| Rationale wording issues (no label change) | 2 |
| Borderline cases flagged for review | 5 |
| Records with no issues | 42 |
| **Total issues flagged** | **18** |

### Original Artifacts Status

All source artifacts remain unmodified. SHA-256 hashes are recorded in Section 1.

---

## 9. Limitations

1. **Single-reviewer context:** The original annotations were produced by a single reviewer. This audit provides a second perspective but does not constitute independent inter-rater reliability.
2. **Context excerpts are limited:** Some questions might be more or less answerable given the full paper context vs. the retrieved excerpt.
3. **Completeness gaps:** 47/60 records lack claim-level detail or supporting quotes.
4. **Borderline cases:** At least 5 records involve genuinely arguable label assignments.
5. **No unblinding performed:** This audit was conducted without consulting the model identity mapping.
