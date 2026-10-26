# RQ5 Qualitative Faithfulness Review: Reviewer Guide & Annotation Instrument

> [!IMPORTANT]
> **Reviewer Confidentiality & Blinding Directive:**
> This document is a **blinded qualitative evaluation instrument**. Each question presents three candidate answers
> labeled anonymously as `Model_Alpha`, `Model_Beta`, and `Model_Gamma`. Candidate identities, parameter counts,
> latency, throughput, and automated Token F1 scores have been strictly removed to eliminate reviewer bias.
> **Do NOT seek or infer model identities during annotation.**

---

## 1. Review Objective & Evaluation Principles

The objective of this qualitative audit is to assess whether generated answers are **semantically faithful and factually grounded**
in the supplied evidence context. This audit directly complements automated Answer Token F1 (which measures lexical precision/recall
against reference answers) by evaluating whether models respect the strict grounding constraint (NFR-03).

### Key Principles for Human Reviewers:
1. **Strict Context Bound:** Judge each answer **exclusively against the provided context**. Do not use external domain knowledge or web searches to verify facts. If a claim is true in real life but absent from the text, it is ungrounded.
2. **Decompose into Atomic Claims:** For complex multi-sentence responses, identify the core verifiable factual propositions.
3. **Distinguish Fabrication vs. Contradiction:**
   - **Unsupported:** Claims asserting details not mentioned in or entailed by the context, but not conflicting with it (extrapolation).
   - **Contradicted:** Claims directly conflicting with or negating explicit statements in the context (inverted numbers, reversed relations).
4. **Fair Evaluation of Refusals (Abstentions):**
   - If the context genuinely lacks the required evidence, the refusal (*'The document does not contain sufficient...'*) is **faithful and correct** (`REFUSAL_VALID`).
   - If the context contains clear evidence to answer the question, but the model refuses, it is an **abstention defect** (`MISSING_INFO - UNJUSTIFIED_REFUSAL`).
5. **Incomplete Answers:** If a model answers but omits crucial qualifiers, condition bounds, or parameters present in the context, classify as `MISSING_INFO - PARTIAL`.

---

## 2. Canonical Annotation Rubric & Precedence Rules

### Protocol Authority:
This rubric and precedence hierarchy are directly codified in Section 6.4 and Section 6.5 of the canonical evaluation protocol ([`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)).

For each answer, assign **one Primary Holistic Label** and note any secondary aspects:

| Primary Label | Operational Definition | Scoring Meaning |
| :--- | :--- | :---: |
| **`SUPPORTED`** | All substantive claims are directly entailed by the supplied context. Free of unsupported extrapolations, contradictions, or core omissions. | Fully Faithful (100% Credit) |
| **`REFUSAL_VALID`** | The model emitted an explicit refusal, and human audit confirms the context genuinely lacked sufficient information to answer. | Valid Abstention (Faithful) |
| **`MISSING_INFO - PARTIAL`** | The answer is partially grounded but omits crucial contextual qualifiers, bounds, or findings necessary to answer accurately. | Incomplete Answer (Partial Defect) |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | The model emitted the refusal message despite the supplied context containing sufficient evidence to answer. | False Abstention (Coverage Defect) |
| **`UNSUPPORTED`** | At least one substantive claim asserts factual details neither stated nor entailed by the context (ungrounded hallucination/extrapolation). | Ungrounded / Hallucinated |
| **`CONTRADICTED`** | At least one substantive claim directly conflicts with or negates explicit statements in the context. | Factually Contradicted |

### Conflict Precedence Rule (Multiple Defects in One Answer):
When an answer exhibits multiple competing issues, assign the primary label by strict failure precedence (as codified in Section 6.5 of `DEC03_FINAL_EVALUATION_PROTOCOL.md`):
$$\mathbf{CONTRADICTED} > \mathbf{UNSUPPORTED} > \mathbf{MISSING\_INFO\ -\ UNJUSTIFIED\_REFUSAL} > \mathbf{MISSING\_INFO\ -\ PARTIAL} > \mathbf{REFUSAL\_VALID} > \mathbf{SUPPORTED}$$

### Mandatory Non-Erasure Directive (Preserving Diagnostic Nuance):
Assigning a primary label based on the precedence hierarchy must **NOT** erase other observed defects or grounded elements. Reviewers must explicitly record:
1. In **Claim-by-Claim Breakdown**: List each extracted atomic proposition and label it individually (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`).
2. In **Supporting Context Quote**: Quote the exact sentence or phrase from the context for any supported or partially supported claim.
3. In **Secondary Label & Reviewer Notes**: Note co-occurring defects (e.g., if an answer contains an unsupported hallucination but also omits crucial context, assign `UNSUPPORTED` as Primary, note `MISSING_INFO - PARTIAL` as Secondary, and explain the omission in notes).

---

## 3. Review Items (20 Sampled Questions $\times$ 3 Blinded Models = 60 Answers)

### REV-01 (Manifest Item #1 | Paper: arXiv:1602.00812)
**Paper Title:** *The Grail theorem prover: Type theory for syntax and semantics*
**Question:** **What formalism does Grail use?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (1531 chars)</b></summary>

```text
This chapter describes the underlying formalism of the theorem provers, as it is visible during an interactive proof trace, and present the general strategy followed by the theorem provers. The presentation in this chapter is somewhat informal, referring the reader elsewhere for full proofs.

The rest of this chapter is structured as follows. Section "Type-logical grammars" presents a general introduction to type-logical grammars and illustrates its basic concepts using the Lambek calculus, ending the section with some problems at the syntax-semantics interface for the Lambek calculus. Section "Modern type-logical grammars" looks at recent developments in type-logical grammars and how they solve some of the problems at the syntax-semantics interface. Section "Theorem proving" looks at two general frameworks for automated theorem proving for type-logical grammars, describing the internal representation of partial proofs and giving a high-level overview of the proof search mechanism.

Type-logical grammars are a family of grammar formalisms built on a foundation of logic and type theory. Type-logical grammars originated when BIBREF4 introduced his Syntactic Calculus (called the Lambek calculus, L, by later authors). Though Lambek built on the work of BIBREF5 , BIBREF6 and others, Lambek's main innovation was to cast the calculus as a logic, giving a sequent calculus and showing decidability by means of cut elimination. This combination of linguistic and computational applications has proved very influential.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-01] Model_Alpha:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-01] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-01] Model_Gamma:
> The Grail theorem provers use a formalism called type-logical grammars.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-02 (Manifest Item #26 | Paper: arXiv:1610.00879)
**Paper Title:** *A Computational Approach to Automatic Prediction of Drunk Texting*
**Question:** **Do the authors equate drunk tweeting with drunk texting? **

<details>
<summary><b>Click to Expand Evidence Context supplied to models (565 chars)</b></summary>

```text
The ubiquity of communication devices has made social media highly accessible. The content on these media reflects a user's day-to-day activities. This includes content created under the influence of alcohol. In popular culture, this has been referred to as `drunk-texting'. In this paper, we introduce automatic `drunk-texting prediction' as a computational task. Given a tweet, the goal is to automatically identify if it was written by a drunk user. We refer to tweets written under the influence of alcohol as `drunk tweets', and the opposite as `sober tweets'.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-02] Model_Alpha:
> The authors do not equate drunk tweeting with drunk texting.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-02] Model_Beta:
> The authors do not equate drunk tweeting with drunk texting. The context does not provide information on whether the authors consider drunk tweeting to be equivalent to drunk texting.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-02] Model_Gamma:
> Yes, the authors equate "drunk tweeting" with "drunk texting".

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-03 (Manifest Item #51 | Paper: arXiv:1704.05572)
**Paper Title:** *Answering Complex Questions Using Open Information Extraction*
**Question:** **What corpus was the source of the OpenIE extractions?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (975 chars)</b></summary>

```text
We use the text corpora (S) from BIBREF6 aristo2016:combining to build our tuple KB. For each test set, we use the corresponding training questions $Q_\mathit {tr}$ to retrieve domain-relevant sentences from S. Specifically, for each multiple-choice question $(q,A) \in Q_\mathit {tr}$ and each choice $a \in A$ , we use all non-stopword tokens in $q$ and $a$ as an ElasticSearch query against S. We take the top 200 hits, run Open IE v4, and aggregate the resulting tuples over all $a \in A$ and over all questions in $Q_\mathit {tr}$ to create the tuple KB (T).

We consider two knowledge sources. The Sentence corpus (S) consists of domain-targeted $~$ 80K sentences and 280 GB of plain text extracted from web pages used by BIBREF6 aristo2016:combining. This corpus is used by the IR solver and also used to create the tuple KB T and on-the-fly tuples $T^{\prime }_{qa}$ . Additionally, TableILP uses $\sim $ 70 Curated tables (C) designed for 4th grade NY Regents exams.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-03] Model_Alpha:
> The corpus used for OpenIE extractions was the Sentence corpus (S) which consists of domain-targeted 80K sentences and 280 GB of plain text extracted from web pages used by BIBREF6 aristo2016:combining.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-03] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-03] Model_Gamma:
> The source of the OpenIE extractions was the Sentence corpus (S).

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-04 (Manifest Item #76 | Paper: arXiv:1709.00387)
**Paper Title:** *MIT-QCRI Arabic Dialect Identification System for the 2017 Multi-Genre Broadcast Challenge*
**Question:** **Which are the four Arabic dialects?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (816 chars)</b></summary>

```text
For the MGB-3 ADI task, the challenge organizers provided 13,825 utterances (53.6 hours) for the training (TRN) set, 1,524 utterances (10 hours) for a development (DEV) set, and 1,492 utterances (10.1 hours) for a test (TST) set. Each dataset consisted of five Arabic dialects: Egyptian (EGY), Levantine (LEV), Gulf (GLF), North African (NOR), and Modern Standard Arabic (MSA). Detailed statistics of the ADI dataset can be found in BIBREF23 . Table TABREF3 shows some facts about the evaluation conditions and data properties. Note that the development set is relatively small compared to the training set. However, it is matched with the test set channel domain. Thus, the development set provides valuable information to adapt or compensate the channel (recording) domain mismatch between the train and test sets.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-04] Model_Alpha:
> The four Arabic dialects mentioned in the context are:
>
> 1. Egyptian (EGY)
> 2. Levantine (LEV)
> 3. Gulf (GLF)
> 4. North African (NOR)

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-04] Model_Beta:
> The four Arabic dialects mentioned in the context are:
>
> 1. Egyptian (EGY)
> 2. Levantine (LEV)
> 3. Gulf (GLF)
> 4. North African (NOR)

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-04] Model_Gamma:
> The four Arabic dialects mentioned in the context are:
>
> 1. Egyptian (EGY)
> 2. Levantine (LEV)
> 3. Gulf (GLF)
> 4. North African (NOR)

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-05 (Manifest Item #101 | Paper: arXiv:1711.04457)
**Paper Title:** *Word, Subword or Character? An Empirical Study of Granularity in Chinese-English NMT*
**Question:** **What dataset did they use?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (487 chars)</b></summary>

```text
Our training data consists of 2.09M sentence pairs extracted from LDC corpus. Table 1 shows the detailed statistics of our training data. To test different approaches on Chinese-to-English translation task, we use NIST 2003(MT03) dataset as the validation set, and NIST 2004(MT04), NIST 2005(MT05), NIST 2006(MT06) datasets as our test sets. For English-to-Chinese translation task, we also use NIST 2003(MT03) dataset as the validation set, and NIST 2008(MT08) will be used as test set.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-05] Model_Alpha:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-05] Model_Beta:
> They used the NIST 2003(MT03) dataset for the Chinese-to-English translation task.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-05] Model_Gamma:
> The NIST 2003(MT03) dataset was used as the validation set for both Chinese-to-English and English-to-Chinese translation tasks.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-06 (Manifest Item #126 | Paper: arXiv:1805.12070)
**Paper Title:** *Code-Switching Language Modeling using Syntax-Aware Multi-Task Learning*
**Question:** **What languages are explored in the work?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (912 chars)</b></summary>

```text
In this section, we present the experimental setting for this task

Corpus: SEAME (South East Asia Mandarin-English), a conversational Mandarin-English code-switching speech corpus consists of spontaneously spoken interviews and conversations BIBREF8 . Our dataset (LDC2015S04) is the most updated version of the Linguistic Data Consortium (LDC) database. However, the statistics are not identical to BIBREF23 . The corpus consists of two phases. In Phase I, only selected audio segments were transcribed. In Phase II, most of the audio segments were transcribed. According to the authors, it was not possible to restore the original dataset. The authors only used Phase I corpus. Few speaker ids are not in the speaker list provided by the authors BIBREF23 . Therefore as a workaround, we added these ids to the train set. As our future reference, the recording lists are included in the supplementary material.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-06] Model_Alpha:
> The languages explored in the work are Mandarin and English.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-06] Model_Beta:
> The work explores Mandarin and English.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-06] Model_Gamma:
> The languages explored in the work are Mandarin and English.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-07 (Manifest Item #151 | Paper: arXiv:1808.10113)
**Paper Title:** *Story Ending Generation with Incremental Encoding and Commonsense Knowledge*
**Question:** **Which baselines are they using?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (877 chars)</b></summary>

```text
We compared our models with the following state-of-the-art baselines:

Sequence to Sequence (Seq2Seq): A simple encoder-decoder model which concatenates four sentences to a long sentence with an attention mechanism BIBREF31 .

Hierarchical LSTM (HLSTM): The story context is represented by a hierarchical LSTM: a word-level LSTM for each sentence and a sentence-level LSTM connecting the four sentences BIBREF29 . A hierarchical attention mechanism is applied, which attends to the states of the two LSTMs respectively.

HLSTM+Copy: The copy mechanism BIBREF32 is applied to hierarchical states to copy the words in the story context for generation.

HLSTM+Graph Attention(GA): We applied multi-source attention HLSTM where commonsense knowledge is encoded by graph attention.

HLSTM+Contextual Attention(CA): Contextual attention is applied to represent commonsense knowledge.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-07] Model_Alpha:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-07] Model_Beta:
> The baselines they are using are:
>
> 1. Sequence to Sequence (Seq2Seq): A simple encoder-decoder model which concatenates four sentences to a long sentence with an attention mechanism.
> 2. Hierarchical LSTM (HLSTM): The story context is represented by a hierarchical LSTM: a word-level LSTM for each sentence and a sentence-level LSTM connecting the four sentences.
> 3. HLSTM+Copy: The copy mechanism BIBREF32 is applied to hierarchical states to copy the words in the story context for generation.
> 4. HLSTM+Graph Attention (GA): We applied multi-source attention HLSTM where commonsense knowledge is encoded by graph attention.
> 5. HLSTM+Contextual Attention (CA): Contextual attention is applied to represent commonsense knowledge.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-07] Model_Gamma:
> The document mentions the following state-of-the-art baselines:
>
> 1. Sequence to Sequence (Seq2Seq)
> 2. Hierarchical LSTM (HLSTM)
> 3. HLSTM+Copy
> 4. HLSTM+Graph Attention (GA)
> 5. HLSTM+Contextual Attention (CA)

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-08 (Manifest Item #176 | Paper: arXiv:1811.01299)
**Paper Title:** *SimplerVoice: A Key Message&Visual Description Generator System for Illiteracy*
**Question:** **Does their solution involve connecting images and text?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (115 chars)</b></summary>

```text
Once the S-V-O is generated, Text2Visual provides users with visual components that convey the S-V-O text meanings.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-08] Model_Alpha:
> Yes, their solution involves providing users with visual components that convey the S-V-O text meanings, which implies connecting images and text.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-08] Model_Beta:
> Yes, their solution involves connecting images and text. The text2visual feature of SimplerVoice generates a visual description of the input text, which can then be used to convey the meaning of the text through images.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-08] Model_Gamma:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-09 (Manifest Item #201 | Paper: arXiv:1904.03339)
**Paper Title:** *ThisIsCompetition at SemEval-2019 Task 9: BERT is unstable for out-of-domain samples*
**Question:** **What datasets were used?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (282 chars)</b></summary>

```text
JESSI is trained using only the datasets given on the shared task, without using any additional external data. Despite this, JESSI performs second on Subtask A with an F1 score of 77.78% among 33 other team submissions. It also performs well on Subtask B with an F1 score of 79.59%.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-09] Model_Alpha:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-09] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-09] Model_Gamma:
> The datasets used in the competition are provided in the context.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-10 (Manifest Item #226 | Paper: arXiv:1905.10044)
**Paper Title:** *BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions*
**Question:** **how was the dataset built?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (1241 chars)</b></summary>

```text
Questions are gathered from anonymized, aggregated queries to the Google search engine. Queries that are likely to be yes/no questions are heuristically identified: we found selecting queries where the first word is in a manually constructed set of indicator words and are of sufficient length, to be effective.

Questions are only kept if a Wikipedia page is returned as one of the first five results, in which case the question and Wikipedia page are given to a human annotator for further processing.

Annotators label question/article pairs in a three-step process. First, they decide if the question is good, meaning it is comprehensible, unambiguous, and requesting factual information. This judgment is made before the annotator sees the Wikipedia page. Next, for good questions, annotators find a passage within the document that contains enough information to answer the question. Annotators can mark questions as “not answerable" if the Wikipedia article does not contain the requested information. Finally, annotators mark whether the question's answer is “yes" or “no". Annotating data in this manner is quite expensive since annotators need to search entire Wikipedia documents for relevant evidence and read the text carefully.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-10] Model_Alpha:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-10] Model_Beta:
> The dataset was built by collecting questions from anonymized, aggregated queries to the Google search engine. These queries were then heuristically identified as likely to be yes/no questions, and the first word of each question was used to construct a set of indicator words. The questions were then kept if a Wikipedia page was returned as one of the first five results, and annotators labeled question/article pairs in a three-step process, including deciding if the question was good, finding a passage within the document that contained enough information to answer the question, and marking the question's answer as "yes" or "no".

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-10] Model_Gamma:
> The dataset was built by aggregating and analyzing a large corpus of text data. This corpus includes a wide range of topics and contexts, from scientific articles to news articles, and from personal experiences to historical events. The goal was to create a comprehensive dataset that could be used for various research and analysis purposes.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-11 (Manifest Item #251 | Paper: arXiv:1907.11907)
**Paper Title:** *Nefnir: A high accuracy lemmatizer for Icelandic*
**Question:** **Which dataset do they use?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (223 chars)</b></summary>

```text
We have evaluated the output of Nefnir against a reference corpus of 21,093 tokens and their correct lemmas.

Samples for the reference corpus were extracted from two larger corpora, in order to obtain a diverse vocabulary:
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-11] Model_Alpha:
> The dataset they use is the reference corpus of 21,093 tokens and their correct lemmas.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-11] Model_Beta:
> The dataset used to evaluate the output of Nefnir is the reference corpus of 21,093 tokens and their correct lemmas.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-11] Model_Gamma:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-12 (Manifest Item #276 | Paper: arXiv:1908.10383)
**Paper Title:** *Facet-Aware Evaluation for Extractive Text Summarization*
**Question:** **What is the problem with existing metrics that they are trying to address?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (34 chars)</b></summary>

```text
Building Extractive CNN/Daily Mail
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-12] Model_Alpha:
> The problem with existing metrics that they are trying to address is that they are not designed to accurately reflect the quality of the extracted text. These metrics are typically based on the precision, recall, and F1 score, which are not specific to the quality of the extracted text. For example, the precision measures the number of true positive results, while the recall measures the number of true positive results divided by the total number of true positives. These metrics do not account for the quality of the extracted text, which can be subjective and can vary from one user to another.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-12] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-12] Model_Gamma:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-13 (Manifest Item #301 | Paper: arXiv:1909.03544)
**Paper Title:** *Czech Text Processing with Contextual Embeddings: POS Tagging, Lemmatization, Parsing and NER*
**Question:** **What data is used to build the embeddings?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (774 chars)</b></summary>

```text
pretrained word embeddings (WE): For the PDT experiments, we generate the word embeddings with word2vec on a concatenation of large raw Czech corpora available from the LINDAT/CLARIN repository. For UD Czech, we use FastText word embeddings BIBREF27 of dimension 300, which we pretrain on Czech Wikipedia using segmentation and tokenization trained from the UD data.

BERT BIBREF1: Pretrained contextual word embeddings of dimension 768 from the Base model. We average the last four layers of the BERT model to produce the embeddings. Because BERT utilizes word pieces, we decompose UD words into appropriate subwords and then average the generated embeddings over subwords belonging to the same word.

Flair BIBREF2: Pretrained contextual word embeddings of dimension 4096.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-13] Model_Alpha:
> The data used to build the embeddings are:
>
> 1. Large raw Czech corpora available from the LINDAT/CLARIN repository.
> 2. Czech Wikipedia.
> 3. UD Czech data (used for FastText word embeddings).
> 4. UD data (used for Flair word embeddings).

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-13] Model_Beta:
> The data used to build the embeddings is the large raw Czech corpora available from the LINDAT/CLARIN repository.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-13] Model_Gamma:
> The data used to build the contextual word embeddings in the provided context is:
>
> 1. Word embeddings generated by word2vec on a concatenation of large raw Czech corpora available from the LINDAT/CLARIN repository.
> 2. Pretrained contextual word embeddings of dimension 768 from the BERT Base model, which are averaged to produce the embeddings.
> 3. Pretrained contextual word embeddings of dimension 4096 from the Flair BIBREF2 model.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-14 (Manifest Item #326 | Paper: arXiv:1909.08824)
**Paper Title:** *Modeling Event Background for If-Then Commonsense Reasoning Using Context-aware Variational Autoencoder*
**Question:** **How do they measure the diversity of inferences?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (493 chars)</b></summary>

```text
We first compare the perplexity of CWVAE with baseline methods. Perplexity measures the probability of model to regenerate the exact targets, which is particular suitable for evaluating the model performance on one-to-many problem BIBREF20. Further, we employ BLEU score to evaluate the accuracy of generations BIBREF21, and the number of distinct n-gram to evaluate the diversity of generations BIBREF6. The distinct is normalized to $[0, 1]$ by dividing the total number of generated tokens.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-14] Model_Alpha:
> The diversity of inferences is measured by the number of distinct n-gram tokens generated by the model.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-14] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-14] Model_Gamma:
> The diversity of generations is measured by the number of distinct n-grams, which is normalized to the range [0, 1] by dividing the total number of generated tokens.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-15 (Manifest Item #351 | Paper: arXiv:1910.06748)
**Paper Title:** *Language Identification on Massive Datasets of Short Message using an Attention Mechanism CNN*
**Question:** **Which existing language ID systems are tested?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (1228 chars)</b></summary>

```text
For the benchmarks, we selected five systems. We picked first the langid.py library which is frequently used to compare systems in the literature. Since our work is in neural-network LID, we selected two neural network systems from the literature, specifically the encoder-decoder EquiLID system of BIBREF6 and the GRU neural network LanideNN system of BIBREF10. Finally, we included CLD2 and CLD3, two implementations of the Naïve Bayes LID software used by Google in their Chrome web browser BIBREF4, BIBREF0, BIBREF8 and sometimes used as a comparison system in the LID literature BIBREF7, BIBREF6, BIBREF8, BIBREF2, BIBREF10. We obtained publicly-available implementations of each of these algorithms, and test them all against our three datasets. In Table TABREF33, we report each algorithm's accuracy and F1 score, the two metrics usually reported in the LID literature. We also included precision and recall values, which are necessary for computing F1 score. And finally we included the speed in number of messages handled per second. This metric is not often discussed in the LID literature, but is of particular importance when dealing with a massive dataset such as ours or a massive streaming source such as Twitter.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-15] Model_Alpha:
> The existing language ID systems tested in the provided context are:
>
> 1. langid.py
> 2. EquiLID (encoder-decoder system of BIBREF6)
> 3. LanideNN (GRU neural network system of BIBREF10)
> 4. CLD2
> 5. CLD3
>
> These systems are used for language identification on massive datasets of short messages.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-15] Model_Beta:
> The existing language ID systems tested in the document are:
>
> 1. langid.py library
> 2. EquiLID system (encoder-decoder neural network)
> 3. LanideNN system (GRU neural network)
> 4. CLD2 (Naïve Bayes LID software)
> 5. CLD3 (Naïve Bayes LID software)

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-15] Model_Gamma:
> The existing language ID systems that are tested are:
>
> 1. langid.py library
> 2. EquiLID system of BIBREF6
> 3. LanideNN system of BIBREF10
> 4. CLD2
> 5. CLD3

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-16 (Manifest Item #376 | Paper: arXiv:1911.03310)
**Paper Title:** *How Language-Neutral is Multilingual BERT?*
**Question:** **What challenges this work presents that must be solved to build better language-neutral representations?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (279 chars)</b></summary>

```text
Using a set of semantically oriented tasks that require explicit semantic cross-lingual representations, we showed that mBERT contextual embeddings do not represent similar semantic phenomena similarly and therefore they are not directly usable for zero-shot cross-lingual tasks.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-16] Model_Alpha:
> This work presents several challenges that must be addressed to build better language-neutral representations. Firstly, the context provided suggests that the current approach of using mBERT contextual embeddings does not directly translate well into zero-shot cross-lingual tasks. This implies that the embeddings may not be as effective in representing similar semantic phenomena across different languages. Secondly, the work highlights the need for a more comprehensive understanding of the semantic phenomena that mBERT contextual embeddings are designed to represent. This requires a deeper analysis of the specific tasks and applications for which these embeddings are being used. Lastly, the challenge of ensuring that the embeddings are not only contextually relevant but also contextually neutral is also addressed. This means that the embeddings should not only capture the semantic relationships between words but also the contextual relationships between words and sentences.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-16] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-16] Model_Gamma:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-17 (Manifest Item #401 | Paper: arXiv:1911.13066)
**Paper Title:** *A Multi-cascaded Deep Model for Bilingual SMS Classification*
**Question:** **What is their baseline model?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (774 chars)</b></summary>

```text
We re-implement the model proposed in BIBREF3, and use it as a baseline for our problem. The rationale behind choosing this particular model as a baseline is it's proven good predictive performance on multilingual text classification. For McM, the choices of number of convolutional filters, number of hidden units in first dense layer, number of hidden units in second dense layer, and recurrent units for LSTM are made empirically. Rest of the hyperparameters were selected by performing grid search using $20\%$ stratified validation set from training set on McM$_\textsubscript {R}$. Available choices and final selected parameters are mentioned in Table TABREF18. These choices remained same for all experiments and the validation set was merged back into training set.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-17] Model_Alpha:
> The baseline model is the model proposed in BIBREF3, which has proven good predictive performance on multilingual text classification.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-17] Model_Beta:
> Their baseline model is the model proposed in BIBREF3.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-17] Model_Gamma:
> The baseline model used in the research is the Multi-cascaded Deep Model proposed in BIBREF3.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-18 (Manifest Item #426 | Paper: arXiv:1912.13109)
**Paper Title:** *"Hinglish"Language -- Modeling a Messy Code-Mixed Language*
**Question:** **What is the previous work's model?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (897 chars)</b></summary>

```text
Mathur et al. in their paper for detecting offensive tweets proposed a Ternary Trans-CNN model where they train a model architecture comprising of 3 layers of Convolution 1D having filter sizes of 15, 12 and 10 and kernel size of 3 followed by 2 dense fully connected layer of size 64 and 3. The first dense FC layer has ReLU activation while the last Dense layer had Softmax activation. They were able to train this network on a parallel English dataset provided by Davidson et al. The authors were able to achieve Accuracy of 83.9%, Precision of 80.2%, Recall of 69.8%.

The approach looked promising given that the dataset was merely 3189 sentences divided into three categories and thus we replicated the experiment but failed to replicate the results. The results were poor than what the original authors achieved. But, most of the model hyper-parameter choices where inspired from this work.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-18] Model_Alpha:
> The previous work's model is the Ternary Trans-CNN model proposed by Mathur et al. in their paper, which is a Ternary Trans-CNN model that consists of 3 layers of Convolution 1D with filter sizes of 15, 12, and 10, kernel sizes of 3, followed by 2 dense fully connected layers of sizes 64 and 3.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-18] Model_Beta:
> The previous work's model is the Ternary Trans-CNN model proposed by Mathur et al., which consists of 3 layers of Convolution 1D with filter sizes of 15, 12, and 10, followed by 2 dense fully connected layers of sizes 64 and 3.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-18] Model_Gamma:
> The previous work's model is the Ternary Trans-CNN model.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-19 (Manifest Item #451 | Paper: arXiv:2002.01861)
**Paper Title:** *Rapid Adaptation of BERT for Information Extraction on Domain-Specific Business Documents*
**Question:** **What type of documents are supported by the annotation platform?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (688 chars)</b></summary>

```text
All the capabilities described in this paper come together in an end-to-end cloud-based platform that we have built. The platform has two main features: First, it provides an annotation interface that allows users to define content elements, upload documents, and annotate documents; a screenshot is shown in Figure FIGREF12. We have invested substantial effort in making the interface as easy to use as possible; for example, annotating content elements is as easy as selecting text from the document. Our platform is able to ingest documents in a variety of formats, including PDFs and Microsoft Word, and converts these formats into plain text before presenting them to the annotators.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-19] Model_Alpha:
> The annotation platform supports documents in a variety of formats, including PDFs and Microsoft Word, and converts these formats into plain text before presenting them to the annotators.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-19] Model_Beta:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-19] Model_Gamma:
> The annotation platform supports a variety of documents, including PDFs and Microsoft Word.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
### REV-20 (Manifest Item #476 | Paper: arXiv:2003.05377)
**Paper Title:** *Brazilian Lyrics-Based Music Genre Classification Using a BLSTM Network*
**Question:** **what genres do they songs fall under?**

<details>
<summary><b>Click to Expand Evidence Context supplied to models (743 chars)</b></summary>

```text
From the Vagalume's music web page, we collect the song title and lyrics, and the artist name. The genre was collected from the page of styles, which lists all the musical genres and, for each one, all the artists. We selected only 14 genres that we consider as representative Brazilian music, shown in Table TABREF8. Figure FIGREF6 presents an example of the Vagalume's music Web page with the song “Como é grande o meu amor por você”, of the Brazilian singer Roberto Carlos. Green boxes indicate information about music that can be extracted directly from the web page. From this information, the language in which the lyrics are available can be obtained by looking at the icon indicating the flag of Brazil preceded by the “Original” word.
```
</details>

#### Candidate Answers for Evaluation:

##### [REV-20] Model_Alpha:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-20] Model_Beta:
> The Brazilian singer Roberto Carlos's songs fall under the following genres:
>
> 1. Pop
> 2. R&B
> 3. Soul
> 4. R&B
> 5. Hip Hop
> 6. R&B
> 7. R&B
> 8. R&B
> 9. R&B
> 10. R&B
> 11. R&B
> 12. R&B
> 13. R&B
> 14. R&B

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

##### [REV-20] Model_Gamma:
> The document does not contain sufficient relevant information to answer this question.

- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`
- **Claim-by-Claim Breakdown:**
  - *Claim 1:*
- **Supporting Context Quote (if supported/partial):**
- **Reviewer Notes & Justification:**

---
