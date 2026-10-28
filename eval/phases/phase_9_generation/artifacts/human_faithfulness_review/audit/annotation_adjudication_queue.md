# RQ5 Human Faithfulness Review Adjudication Queue

**Status:** ADJUDICATED_AND_FINALIZED
**Total Records:** 60 (60 answers: 20 questions × 3 blinded models)
**Flagged Items Adjudicated:** 21
**Unflagged Records (Passed Verification):** 39

---

## Section 1: Flagged Items with Final Adjudicated Decisions

The following 21 records have been adjudicated and updated with final decisions.

| # | Review ID | Model | Original Label | Audit Issue | Proposed Label | Conf | Decision | Final Label |
| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :---: | :---: |
| 1 | **REV-01** | Model_Alpha | `REFUSAL_VALID` | BORDERLINE_REVIEW: Context discusses type-log... | `REFUSAL_VALID` | MEDIUM | [X] ACCEPT | `REFUSAL_VALID` |
| 2 | **REV-01** | Model_Beta | `REFUSAL_VALID` | BORDERLINE_REVIEW: Same context and refusal a... | `REFUSAL_VALID` | MEDIUM | [X] ACCEPT | `REFUSAL_VALID` |
| 3 | **REV-01** | Model_Gamma | `CONTRADICTED` | SEMANTIC_INCONSISTENCY: Label CONTRADICTED ap... | `UNSUPPORTED` | MEDIUM | [X] ACCEPT | `UNSUPPORTED` |
| 4 | **REV-02** | Model_Alpha | `CONTRADICTED` | RATIONALE_AMBIGUITY: Rationale opens with 'Su... | `CONTRADICTED` | HIGH | [X] ACCEPT | `CONTRADICTED` |
| 5 | **REV-02** | Model_Beta | `UNSUPPORTED` | SEMANTIC_INCONSISTENCY: Model claims authors ... | `CONTRADICTED` | MEDIUM | [X] ACCEPT | `CONTRADICTED` |
| 6 | **REV-03** | Model_Gamma | `UNSUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | HIGH | [X] ACCEPT | `MISSING_INFO - UNJUSTIFIED_REFUSAL` |
| 7 | **REV-04** | Model_Alpha | `SUPPORTED` | BORDERLINE_REVIEW: Context lists 5 dialects; ... | `SUPPORTED` | HIGH | [X] ACCEPT | `SUPPORTED` |
| 8 | **REV-04** | Model_Beta | `SUPPORTED` | BORDERLINE_REVIEW: Context lists 5 dialects; ... | `SUPPORTED` | HIGH | [X] ACCEPT | `SUPPORTED` |
| 9 | **REV-04** | Model_Gamma | `SUPPORTED` | BORDERLINE_REVIEW: Context lists 5 dialects; ... | `SUPPORTED` | HIGH | [X] ACCEPT | `SUPPORTED` |
| 10 | **REV-08** | Model_Beta | `SUPPORTED` | BORDERLINE_REVIEW: Minor elaboration beyond l... | `SUPPORTED` | HIGH | [X] ACCEPT | `SUPPORTED` |
| 11 | **REV-09** | Model_Alpha | `SUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `REFUSAL_VALID` | HIGH | [X] ACCEPT | `REFUSAL_VALID` |
| 12 | **REV-09** | Model_Gamma | `SUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `REFUSAL_VALID` | HIGH | [X] ACCEPT | `REFUSAL_VALID` |
| 13 | **REV-10** | Model_Beta | `UNSUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | HIGH | [X] ACCEPT | `MISSING_INFO - UNJUSTIFIED_REFUSAL` |
| 14 | **REV-10** | Model_Gamma | `MISSING_INFO - PARTIAL` | SEMANTIC_INCONSISTENCY: Entirely fabricated r... | `UNSUPPORTED` | MEDIUM | [X] ACCEPT | `UNSUPPORTED` |
| 15 | **REV-11** | Model_Alpha | `REFUSAL_VALID` | BORDERLINE_REVIEW: Context mentions 'referenc... | `REFUSAL_VALID` | MEDIUM | [X] ACCEPT | `REFUSAL_VALID` |
| 16 | **REV-12** | Model_Beta | `SUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `REFUSAL_VALID` | HIGH | [X] ACCEPT | `REFUSAL_VALID` |
| 17 | **REV-12** | Model_Gamma | `SUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `REFUSAL_VALID` | HIGH | [X] ACCEPT | `REFUSAL_VALID` |
| 18 | **REV-13** | Model_Alpha | `CONTRADICTED` | BORDERLINE_REVIEW: Model misattributes FastTe... | `CONTRADICTED` | HIGH | [X] ACCEPT | `CONTRADICTED` |
| 19 | **REV-17** | Model_Alpha | `UNSUPPORTED` | BORDERLINE_REVIEW: Model misattributes baseli... | `UNSUPPORTED` | HIGH | [X] ACCEPT | `UNSUPPORTED` |
| 20 | **REV-20** | Model_Beta | `SUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `REFUSAL_VALID` | HIGH | [X] ACCEPT | `REFUSAL_VALID` |
| 21 | **REV-20** | Model_Gamma | `SUPPORTED` | PROTOCOL_VIOLATION: Refusal boilerplate label... | `REFUSAL_VALID` | HIGH | [X] ACCEPT | `REFUSAL_VALID` |

---

## Section 2: Detailed Dossiers for Flagged Records (Adjudicated)

### Item 1: REV-01 — Model_Alpha

- **Original Primary Label:** `REFUSAL_VALID`
- **Original Secondary Label:** `None`
- **Original Rationale:** Provided text did not directly mention formalisms for the grail, it just mentions the type of grammars.
- **Audit Issue:** BORDERLINE_REVIEW: Context discusses type-logical grammars extensively but specific name 'Grail' does not appear in excerpt; refusal accepted as valid
- **Protocol Rule:** Section 6.5: Context sufficiency threshold for specific named entities
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **MEDIUM**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
This chapter describes the underlying formalism of the theorem provers, as it is visible during an interactive proof trace, and present the general strategy followed by the theorem provers. The presentation in this chapter is somewhat informal, referring the reader elsewhere for full proofs.

The rest of this chapter is structured as follows. Section "Type-logical grammars" presents a general introduction to type-logical grammars and illustrates its basic concepts using the Lambek calculus, endi...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`REFUSAL_VALID`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted proposed label; borderline refusal is defensible due to absence of specific named entity.`

---

### Item 2: REV-01 — Model_Beta

- **Original Primary Label:** `REFUSAL_VALID`
- **Original Secondary Label:** `None`
- **Original Rationale:** Provided text did not directly mention formalisms for the grail, it just mentions the type of grammars.
- **Audit Issue:** BORDERLINE_REVIEW: Same context and refusal as REV-01 Alpha
- **Protocol Rule:** Section 6.5: Context sufficiency threshold for specific named entities
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **MEDIUM**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
This chapter describes the underlying formalism of the theorem provers, as it is visible during an interactive proof trace, and present the general strategy followed by the theorem provers. The presentation in this chapter is somewhat informal, referring the reader elsewhere for full proofs.

The rest of this chapter is structured as follows. Section "Type-logical grammars" presents a general introduction to type-logical grammars and illustrates its basic concepts using the Lambek calculus, endi...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`REFUSAL_VALID`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted proposed label consistent with Model Alpha.`

---

### Item 3: REV-01 — Model_Gamma

- **Original Primary Label:** `CONTRADICTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** - *Claim 1:* Given text did not mention that type-logical grammars was used by the Grail | Provided text did not directly mention formalisms for the grail, it just mentions the type of grammars.
- **Audit Issue:** SEMANTIC_INCONSISTENCY: Label CONTRADICTED applied to unmentioned/unsupported claim rather than direct contradiction
- **Protocol Rule:** Precedence Rule 1 (CONTRADICTED requires explicit conflict/negation) vs Rule 2 (UNSUPPORTED = ungrounded/missing claim)
- **Proposed Primary Label:** `UNSUPPORTED`
- **Final Primary Label:** `UNSUPPORTED`
- **Final Secondary Label:** `EXTRAPOLATION`
- **Confidence:** **MEDIUM**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The Grail theorem provers use a formalism called type-logical grammars.
```

**Context Excerpt:**
```text
This chapter describes the underlying formalism of the theorem provers, as it is visible during an interactive proof trace, and present the general strategy followed by the theorem provers. The presentation in this chapter is somewhat informal, referring the reader elsewhere for full proofs.

The rest of this chapter is structured as follows. Section "Type-logical grammars" presents a general introduction to type-logical grammars and illustrates its basic concepts using the Lambek calculus, endi...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`UNSUPPORTED`)
- [ ] RETAIN Original Label (`CONTRADICTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted UNSUPPORTED per Precedence Rule 2; lack of mention does not equal explicit contradiction.`

---

### Item 4: REV-02 — Model_Alpha

- **Original Primary Label:** `CONTRADICTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** - *Claim 1:* The model claimed there was no direct comparison by the author between drunk tweet and drunk text | Supported. The authors treat drunk tweeting as synonymous with drunk texting by using tweets as the primary medium to formulate and evaluate their "drunk-texting prediction" task.
- **Audit Issue:** RATIONALE_AMBIGUITY: Rationale opens with 'Supported' but meant 'Context supports equivalence', which correctly results in CONTRADICTED label for model's negation
- **Protocol Rule:** Precedence Rule 1: CONTRADICTED is correct when answer asserts negation of supported relationship
- **Proposed Primary Label:** `CONTRADICTED`
- **Final Primary Label:** `CONTRADICTED`
- **Final Secondary Label:** `FACTUAL_CONFLICT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The authors do not equate drunk tweeting with drunk texting.
```

**Context Excerpt:**
```text
The ubiquity of communication devices has made social media highly accessible. The content on these media reflects a user's day-to-day activities. This includes content created under the influence of alcohol. In popular culture, this has been referred to as `drunk-texting'. In this paper, we introduce automatic `drunk-texting prediction' as a computational task. Given a tweet, the goal is to automatically identify if it was written by a drunk user. We refer to tweets written under the influence ...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`CONTRADICTED`)
- [ ] RETAIN Original Label (`CONTRADICTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted CONTRADICTED; rationale phrasing clarified for audit trail.`

---

### Item 5: REV-02 — Model_Beta

- **Original Primary Label:** `UNSUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** - *Claim 1:* The model claimed there was no direct comparison by the author between drunk tweet and drunk text | Supported. The authors treat drunk tweeting as synonymous with drunk texting by using tweets as the primary medium to formulate and evaluate their "drunk-texting prediction" task.
- **Audit Issue:** SEMANTIC_INCONSISTENCY: Model claims authors do not equate drunk texting/tweeting; labeled UNSUPPORTED while identical claim in Alpha labeled CONTRADICTED
- **Protocol Rule:** Precedence Rule 1: CONTRADICTED takes precedence over UNSUPPORTED when claims contradict context
- **Proposed Primary Label:** `CONTRADICTED`
- **Final Primary Label:** `CONTRADICTED`
- **Final Secondary Label:** `FACTUAL_CONFLICT`
- **Confidence:** **MEDIUM**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The authors do not equate drunk tweeting with drunk texting. The context does not provide information on whether the authors consider drunk tweeting to be equivalent to drunk texting.
```

**Context Excerpt:**
```text
The ubiquity of communication devices has made social media highly accessible. The content on these media reflects a user's day-to-day activities. This includes content created under the influence of alcohol. In popular culture, this has been referred to as `drunk-texting'. In this paper, we introduce automatic `drunk-texting prediction' as a computational task. Given a tweet, the goal is to automatically identify if it was written by a drunk user. We refer to tweets written under the influence ...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`CONTRADICTED`)
- [ ] RETAIN Original Label (`UNSUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted CONTRADICTED per Precedence Rule 1 to maintain consistency with Model Alpha.`

---

### Item 6: REV-03 — Model_Gamma

- **Original Primary Label:** `UNSUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** - *Claim 1:* It claimed that there was no mentioned of the corpus, in which it did. | ---
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled UNSUPPORTED when context contains answer
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals must be labeled REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL. When context contains answer, label must be MISSING_INFO - UNJUSTIFIED_REFUSAL.
- **Proposed Primary Label:** `MISSING_INFO - UNJUSTIFIED_REFUSAL`
- **Final Primary Label:** `MISSING_INFO - UNJUSTIFIED_REFUSAL`
- **Final Secondary Label:** `REFUSAL`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
We use the text corpora (S) from BIBREF6 aristo2016:combining to build our tuple KB. For each test set, we use the corresponding training questions $Q_\mathit {tr}$ to retrieve domain-relevant sentences from S. Specifically, for each multiple-choice question $(q,A) \in Q_\mathit {tr}$ and each choice $a \in A$ , we use all non-stopword tokens in $q$ and $a$ as an ElasticSearch query against S. We take the top 200 hits, run Open IE v4, and aggregate the resulting tuples over all $a \in A$ and ove...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`MISSING_INFO - UNJUSTIFIED_REFUSAL`)
- [ ] RETAIN Original Label (`UNSUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted MISSING_INFO - UNJUSTIFIED_REFUSAL; context contains relevant corpus information.`

---

### Item 7: REV-04 — Model_Alpha

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** None recorded
- **Audit Issue:** BORDERLINE_REVIEW: Context lists 5 dialects; question asks for 4; model lists 4 (omits MSA)
- **Protocol Rule:** Taxonomy: SUPPORTED vs MISSING_INFO - PARTIAL when question framing constrains answer scope
- **Proposed Primary Label:** `SUPPORTED`
- **Final Primary Label:** `SUPPORTED`
- **Final Secondary Label:** `None`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The four Arabic dialects mentioned in the context are:

1. Egyptian (EGY)
2. Levantine (LEV)
3. Gulf (GLF)
4. North African (NOR)
```

**Context Excerpt:**
```text
For the MGB-3 ADI task, the challenge organizers provided 13,825 utterances (53.6 hours) for the training (TRN) set, 1,524 utterances (10 hours) for a development (DEV) set, and 1,492 utterances (10.1 hours) for a test (TST) set. Each dataset consisted of five Arabic dialects: Egyptian (EGY), Levantine (LEV), Gulf (GLF), North African (NOR), and Modern Standard Arabic (MSA). Detailed statistics of the ADI dataset can be found in BIBREF23 . Table TABREF3 shows some facts about the evaluation cond...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`SUPPORTED`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Retained SUPPORTED; model successfully targeted the requested subset of dialects.`

---

### Item 8: REV-04 — Model_Beta

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** None recorded
- **Audit Issue:** BORDERLINE_REVIEW: Context lists 5 dialects; question asks for 4; model lists 4 (omits MSA)
- **Protocol Rule:** Taxonomy: SUPPORTED vs MISSING_INFO - PARTIAL when question framing constrains answer scope
- **Proposed Primary Label:** `SUPPORTED`
- **Final Primary Label:** `SUPPORTED`
- **Final Secondary Label:** `None`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The four Arabic dialects mentioned in the context are:

1. Egyptian (EGY)
2. Levantine (LEV)
3. Gulf (GLF)
4. North African (NOR)
```

**Context Excerpt:**
```text
For the MGB-3 ADI task, the challenge organizers provided 13,825 utterances (53.6 hours) for the training (TRN) set, 1,524 utterances (10 hours) for a development (DEV) set, and 1,492 utterances (10.1 hours) for a test (TST) set. Each dataset consisted of five Arabic dialects: Egyptian (EGY), Levantine (LEV), Gulf (GLF), North African (NOR), and Modern Standard Arabic (MSA). Detailed statistics of the ADI dataset can be found in BIBREF23 . Table TABREF3 shows some facts about the evaluation cond...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`SUPPORTED`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Retained SUPPORTED consistently.`

---

### Item 9: REV-04 — Model_Gamma

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** ---
- **Audit Issue:** BORDERLINE_REVIEW: Context lists 5 dialects; question asks for 4; model lists 4 (omits MSA)
- **Protocol Rule:** Taxonomy: SUPPORTED vs MISSING_INFO - PARTIAL when question framing constrains answer scope
- **Proposed Primary Label:** `SUPPORTED`
- **Final Primary Label:** `SUPPORTED`
- **Final Secondary Label:** `None`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The four Arabic dialects mentioned in the context are:

1. Egyptian (EGY)
2. Levantine (LEV)
3. Gulf (GLF)
4. North African (NOR)
```

**Context Excerpt:**
```text
For the MGB-3 ADI task, the challenge organizers provided 13,825 utterances (53.6 hours) for the training (TRN) set, 1,524 utterances (10 hours) for a development (DEV) set, and 1,492 utterances (10.1 hours) for a test (TST) set. Each dataset consisted of five Arabic dialects: Egyptian (EGY), Levantine (LEV), Gulf (GLF), North African (NOR), and Modern Standard Arabic (MSA). Detailed statistics of the ADI dataset can be found in BIBREF23 . Table TABREF3 shows some facts about the evaluation cond...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`SUPPORTED`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Retained SUPPORTED consistently.`

---

### Item 10: REV-08 — Model_Beta

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** None recorded
- **Audit Issue:** BORDERLINE_REVIEW: Minor elaboration beyond literal context ('convey meaning through images')
- **Protocol Rule:** Taxonomy: SUPPORTED vs UNSUPPORTED for benign semantic elaboration
- **Proposed Primary Label:** `SUPPORTED`
- **Final Primary Label:** `SUPPORTED`
- **Final Secondary Label:** `None`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
Yes, their solution involves connecting images and text. The text2visual feature of SimplerVoice generates a visual description of the input text, which can then be used to convey the meaning of the text through images.
```

**Context Excerpt:**
```text
Once the S-V-O is generated, Text2Visual provides users with visual components that convey the S-V-O text meanings....
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`SUPPORTED`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted SUPPORTED; minor elaboration is benign and directly grounded.`

---

### Item 11: REV-09 — Model_Alpha

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** None recorded
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. Genuinely absent answer in context must be labeled REFUSAL_VALID.
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
JESSI is trained using only the datasets given on the shared task, without using any additional external data. Despite this, JESSI performs second on Subtask A with an F1 score of 77.78% among 33 other team submissions. It also performs well on Subtask B with an F1 score of 79.59%....
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted REFUSAL_VALID; context lacks specific dataset names requested.`

---

### Item 12: REV-09 — Model_Gamma

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** ---
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. Genuinely absent answer in context must be labeled REFUSAL_VALID.
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
JESSI is trained using only the datasets given on the shared task, without using any additional external data. Despite this, JESSI performs second on Subtask A with an F1 score of 77.78% among 33 other team submissions. It also performs well on Subtask B with an F1 score of 79.59%....
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted REFUSAL_VALID consistently.`

---

### Item 13: REV-10 — Model_Beta

- **Original Primary Label:** `UNSUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** - *Claim 1:* The model claimed there was no information related to how the dataset was built | The entire passage was about how the dataset was built.
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled UNSUPPORTED when context contains answer
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals must be labeled REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL, not UNSUPPORTED. When answer is in context, label must be MISSING_INFO - UNJUSTIFIED_REFUSAL.
- **Proposed Primary Label:** `MISSING_INFO - UNJUSTIFIED_REFUSAL`
- **Final Primary Label:** `MISSING_INFO - UNJUSTIFIED_REFUSAL`
- **Final Secondary Label:** `REFUSAL`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
Questions are gathered from anonymized, aggregated queries to the Google search engine. Queries that are likely to be yes/no questions are heuristically identified: we found selecting queries where the first word is in a manually constructed set of indicator words and are of sufficient length, to be effective.

Questions are only kept if a Wikipedia page is returned as one of the first five results, in which case the question and Wikipedia page are given to a human annotator for further processi...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`MISSING_INFO - UNJUSTIFIED_REFUSAL`)
- [ ] RETAIN Original Label (`UNSUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted MISSING_INFO - UNJUSTIFIED_REFUSAL; context explicitly details dataset collection methods.`

---

### Item 14: REV-10 — Model_Gamma

- **Original Primary Label:** `MISSING_INFO - PARTIAL`
- **Original Secondary Label:** `None`
- **Original Rationale:** The answer didn't include any specific information that the paragraph has provided. (EG: collections are aggregated queries from google search engine,...)
- **Audit Issue:** SEMANTIC_INCONSISTENCY: Entirely fabricated response labeled MISSING_INFO - PARTIAL
- **Protocol Rule:** Precedence Rule 2 (UNSUPPORTED > MISSING_INFO) & Taxonomy: Partial coverage requires some supported facts from context; zero supported facts must be labeled UNSUPPORTED
- **Proposed Primary Label:** `UNSUPPORTED`
- **Final Primary Label:** `UNSUPPORTED`
- **Final Secondary Label:** `HALLUCINATION`
- **Confidence:** **MEDIUM**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The dataset was built by aggregating and analyzing a large corpus of text data. This corpus includes a wide range of topics and contexts, from scientific articles to news articles, and from personal experiences to historical events. The goal was to create a comprehensive dataset that could be used for various research and analysis purposes.
```

**Context Excerpt:**
```text
Questions are gathered from anonymized, aggregated queries to the Google search engine. Queries that are likely to be yes/no questions are heuristically identified: we found selecting queries where the first word is in a manually constructed set of indicator words and are of sufficient length, to be effective.

Questions are only kept if a Wikipedia page is returned as one of the first five results, in which case the question and Wikipedia page are given to a human annotator for further processi...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`UNSUPPORTED`)
- [ ] RETAIN Original Label (`MISSING_INFO - PARTIAL`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted UNSUPPORTED; response is entirely fabricated with zero factual overlap.`

---

### Item 15: REV-11 — Model_Alpha

- **Original Primary Label:** `REFUSAL_VALID`
- **Original Secondary Label:** `None`
- **Original Rationale:** It could've answered like model beta, but then again the paragraph didn't contain sufficient information, so this answer isn't wrong either.
- **Audit Issue:** BORDERLINE_REVIEW: Context mentions 'reference corpus of 21,093 tokens'; model refused; reviewer deemed info insufficient
- **Protocol Rule:** Section 6.5: Context sufficiency threshold for dataset identification
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **MEDIUM**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
We have evaluated the output of Nefnir against a reference corpus of 21,093 tokens and their correct lemmas.

Samples for the reference corpus were extracted from two larger corpora, in order to obtain a diverse vocabulary:...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`REFUSAL_VALID`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Retained REFUSAL_VALID for borderline information sufficiency.`

---

### Item 16: REV-12 — Model_Beta

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** None recorded
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
Building Extractive CNN/Daily Mail...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted REFUSAL_VALID; context lacks metric information entirely.`

---

### Item 17: REV-12 — Model_Gamma

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** ---
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
Building Extractive CNN/Daily Mail...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted REFUSAL_VALID consistently.`

---

### Item 18: REV-13 — Model_Alpha

- **Original Primary Label:** `CONTRADICTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** - *Claim 1:* It claims in point 3 that UD Czech data was used to help build the FastText word embeddings, in reality, the actual data used to pretrain the embeddings is Czech Wikipedia. The UD data was only used to train the segmentation and tokenization tools used during preprocessing, not the embeddings themselves.
+ It claims in point 4 that UD data was being used for FLair word embeddings, in which the text did not mention anything about it. | The model did got Point 1 and 2 correct though, too bad it hallucinated on point 3 and 4.
- **Audit Issue:** BORDERLINE_REVIEW: Model misattributes FastText pretraining to UD Czech rather than Czech Wikipedia; labeled CONTRADICTED
- **Protocol Rule:** Precedence Rule 1 (CONTRADICTED > UNSUPPORTED)
- **Proposed Primary Label:** `CONTRADICTED`
- **Final Primary Label:** `CONTRADICTED`
- **Final Secondary Label:** `FACTUAL_CONFLICT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The data used to build the embeddings are:

1. Large raw Czech corpora available from the LINDAT/CLARIN repository.
2. Czech Wikipedia.
3. UD Czech data (used for FastText word embeddings).
4. UD data (used for Flair word embeddings).
```

**Context Excerpt:**
```text
pretrained word embeddings (WE): For the PDT experiments, we generate the word embeddings with word2vec on a concatenation of large raw Czech corpora available from the LINDAT/CLARIN repository. For UD Czech, we use FastText word embeddings BIBREF27 of dimension 300, which we pretrain on Czech Wikipedia using segmentation and tokenization trained from the UD data.

BERT BIBREF1: Pretrained contextual word embeddings of dimension 768 from the Base model. We average the last four layers of the BER...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`CONTRADICTED`)
- [ ] RETAIN Original Label (`CONTRADICTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Retained CONTRADICTED; model misattributed FastText pretraining source.`

---

### Item 19: REV-17 — Model_Alpha

- **Original Primary Label:** `UNSUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** "Multi-cascaded Deep Model" (McM) is the authors' own proposed model, not the baseline, it's literally in the paper's name.
- **Audit Issue:** BORDERLINE_REVIEW: Model misattributes baseline name; labeled UNSUPPORTED
- **Protocol Rule:** Taxonomy: UNSUPPORTED for ungrounded entity name
- **Proposed Primary Label:** `UNSUPPORTED`
- **Final Primary Label:** `UNSUPPORTED`
- **Final Secondary Label:** `HALLUCINATION`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The baseline model used in the research is the Multi-cascaded Deep Model proposed in BIBREF3.
```

**Context Excerpt:**
```text
We re-implement the model proposed in BIBREF3, and use it as a baseline for our problem. The rationale behind choosing this particular model as a baseline is it's proven good predictive performance on multilingual text classification. For McM, the choices of number of convolutional filters, number of hidden units in first dense layer, number of hidden units in second dense layer, and recurrent units for LSTM are made empirically. Rest of the hyperparameters were selected by performing grid searc...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`UNSUPPORTED`)
- [ ] RETAIN Original Label (`UNSUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Retained UNSUPPORTED for ungrounded entity/baseline naming.`

---

### Item 20: REV-20 — Model_Beta

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** None recorded
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
From the Vagalume's music web page, we collect the song title and lyrics, and the artist name. The genre was collected from the page of styles, which lists all the musical genres and, for each one, all the artists. We selected only 14 genres that we consider as representative Brazilian music, shown in Table TABREF8. Figure FIGREF6 presents an example of the Vagalume's music Web page with the song “Como é grande o meu amor por você”, of the Brazilian singer Roberto Carlos. Green boxes indicate in...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted REFUSAL_VALID; referenced table contents are missing from the excerpt.`

---

### Item 21: REV-20 — Model_Gamma

- **Original Primary Label:** `SUPPORTED`
- **Original Secondary Label:** `None`
- **Original Rationale:** ---
- **Audit Issue:** PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED
- **Protocol Rule:** Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.
- **Proposed Primary Label:** `REFUSAL_VALID`
- **Final Primary Label:** `REFUSAL_VALID`
- **Final Secondary Label:** `ABSENT`
- **Confidence:** **HIGH**

<details>
<summary><b>Click to View Model Answer and Context</b></summary>

**Answer:**
```text
The document does not contain sufficient relevant information to answer this question.
```

**Context Excerpt:**
```text
From the Vagalume's music web page, we collect the song title and lyrics, and the artist name. The genre was collected from the page of styles, which lists all the musical genres and, for each one, all the artists. We selected only 14 genres that we consider as representative Brazilian music, shown in Table TABREF8. Figure FIGREF6 presents an example of the Vagalume's music Web page with the song “Como é grande o meu amor por você”, of the Brazilian singer Roberto Carlos. Green boxes indicate in...
```
</details>

**Adjudication Action Required:**
- [X] ACCEPT Proposed Label (`REFUSAL_VALID`)
- [ ] RETAIN Original Label (`SUPPORTED`)
- [ ] ASSIGN Custom Label: `____________________`
- **Adjudicator Notes:** `Accepted REFUSAL_VALID consistently.`

---

## Section 3: Records Passed with No Inconsistencies (39 Items)

The remaining 39 records demonstrated consistent alignment between model answer, evidence context, reviewer rationale, and protocol precedence rules.

| Review ID | Model | Primary Label | Secondary Label | Status |
| :--- | :--- | :--- | :--- | :---: |
| REV-02 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-03 | Model_Alpha | `SUPPORTED` | `-` | ✅ PASS |
| REV-03 | Model_Beta | `MISSING_INFO - PARTIAL` | `-` | ✅ PASS |
| REV-05 | Model_Alpha | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-05 | Model_Beta | `MISSING_INFO - PARTIAL` | `-` | ✅ PASS |
| REV-05 | Model_Gamma | `MISSING_INFO - PARTIAL` | `-` | ✅ PASS |
| REV-06 | Model_Alpha | `SUPPORTED` | `-` | ✅ PASS |
| REV-06 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-06 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-07 | Model_Alpha | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-07 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-07 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-08 | Model_Alpha | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-08 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-09 | Model_Beta | `UNSUPPORTED` | `-` | ✅ PASS |
| REV-10 | Model_Alpha | `SUPPORTED` | `-` | ✅ PASS |
| REV-11 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-11 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-12 | Model_Alpha | `UNSUPPORTED` | `-` | ✅ PASS |
| REV-13 | Model_Beta | `UNSUPPORTED` | `-` | ✅ PASS |
| REV-13 | Model_Gamma | `MISSING_INFO - PARTIAL` | `-` | ✅ PASS |
| REV-14 | Model_Alpha | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-14 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-14 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-15 | Model_Alpha | `SUPPORTED` | `-` | ✅ PASS |
| REV-15 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-15 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-16 | Model_Alpha | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-16 | Model_Beta | `UNSUPPORTED` | `-` | ✅ PASS |
| REV-16 | Model_Gamma | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-17 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-17 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-18 | Model_Alpha | `SUPPORTED` | `-` | ✅ PASS |
| REV-18 | Model_Beta | `SUPPORTED` | `-` | ✅ PASS |
| REV-18 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-19 | Model_Alpha | `SUPPORTED` | `-` | ✅ PASS |
| REV-19 | Model_Beta | `MISSING_INFO - UNJUSTIFIED_REFUSAL` | `-` | ✅ PASS |
| REV-19 | Model_Gamma | `SUPPORTED` | `-` | ✅ PASS |
| REV-20 | Model_Alpha | `UNSUPPORTED` | `-` | ✅ PASS |
