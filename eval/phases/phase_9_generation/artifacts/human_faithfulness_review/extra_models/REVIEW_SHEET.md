# Human check: extra generation models (20 questions x 2 answers)

Answers are shown as `Model_Delta` and `Model_Epsilon`; which model is which changes
from question to question. Do not open `restricted_model_label_mapping.json` before
finishing the labels.

## How to label

Judge each answer **only against the context shown** (no outside knowledge). Give one
primary label; if several problems occur, use the first that applies in this order:
CONTRADICTED > UNSUPPORTED > MISSING_INFO - UNJUSTIFIED_REFUSAL > MISSING_INFO - PARTIAL >
REFUSAL_VALID > SUPPORTED. Other problems go in the secondary label / notes.

| Label | Meaning |
| :--- | :--- |
| `SUPPORTED` | Every substantive claim is stated in or follows from the context. |
| `REFUSAL_VALID` | The model refused, and the context really does not contain the answer. |
| `MISSING_INFO - PARTIAL` | Grounded, but leaves out a key part of the answer that the context contains. |
| `MISSING_INFO - UNJUSTIFIED_REFUSAL` | The model refused although the context contains the answer. |
| `UNSUPPORTED` | At least one claim is not in the context (but does not contradict it). |
| `CONTRADICTED` | At least one claim conflicts with the context. |

Fill in `primary_label`, optionally `secondary_label`, a short `supporting_evidence` quote
for supported claims, and `reviewer_notes`, in `annotation_template_40a.csv` (or .jsonl).

## Questions

### REV-01 (manifest item #1, arXiv:1602.00812)
**Paper:** *The Grail theorem prover: Type theory for syntax and semantics*  
**Question:** What formalism does Grail use?

<details><summary>Context given to the model</summary>

```text
This chapter describes the underlying formalism of the theorem provers, as it is visible during an interactive proof trace, and present the general strategy followed by the theorem provers. The presentation in this chapter is somewhat informal, referring the reader elsewhere for full proofs.

The rest of this chapter is structured as follows. Section "Type-logical grammars" presents a general introduction to type-logical grammars and illustrates its basic concepts using the Lambek calculus, ending the section with some problems at the syntax-semantics interface for the Lambek calculus. Section "Modern type-logical grammars" looks at recent developments in type-logical grammars and how they solve some of the problems at the syntax-semantics interface. Section "Theorem proving" looks at two general frameworks for automated theorem proving for type-logical grammars, describing the internal representation of partial proofs and giving a high-level overview of the proof search mechanism.

Type-logical grammars are a family of grammar formalisms built on a foundation of logic and type theory. Type-logical grammars originated when BIBREF4 introduced his Syntactic Calculus (called the Lambek calculus, L, by later authors). Though Lambek built on the work of BIBREF5 , BIBREF6 and others, Lambek's main innovation was to cast the calculus as a logic, giving a sequent calculus and showing decidability by means of cut elimination. This combination of linguistic and computational applications has proved very influential.
```
</details>

**Model_Delta:**

> Type-logical grammars

**Model_Epsilon:**

> The Grail theorem prover uses type-logical grammars.

---

### REV-02 (manifest item #26, arXiv:1610.00879)
**Paper:** *A Computational Approach to Automatic Prediction of Drunk Texting*  
**Question:** Do the authors equate drunk tweeting with drunk texting? 

<details><summary>Context given to the model</summary>

```text
The ubiquity of communication devices has made social media highly accessible. The content on these media reflects a user's day-to-day activities. This includes content created under the influence of alcohol. In popular culture, this has been referred to as `drunk-texting'. In this paper, we introduce automatic `drunk-texting prediction' as a computational task. Given a tweet, the goal is to automatically identify if it was written by a drunk user. We refer to tweets written under the influence of alcohol as `drunk tweets', and the opposite as `sober tweets'.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The authors do not equate drunk tweeting with drunk texting. The context provided does not mention any direct comparison between the two terms.

---

### REV-03 (manifest item #51, arXiv:1704.05572)
**Paper:** *Answering Complex Questions Using Open Information Extraction*  
**Question:** What corpus was the source of the OpenIE extractions?

<details><summary>Context given to the model</summary>

```text
We use the text corpora (S) from BIBREF6 aristo2016:combining to build our tuple KB. For each test set, we use the corresponding training questions $Q_\mathit {tr}$ to retrieve domain-relevant sentences from S. Specifically, for each multiple-choice question $(q,A) \in Q_\mathit {tr}$ and each choice $a \in A$ , we use all non-stopword tokens in $q$ and $a$ as an ElasticSearch query against S. We take the top 200 hits, run Open IE v4, and aggregate the resulting tuples over all $a \in A$ and over all questions in $Q_\mathit {tr}$ to create the tuple KB (T).

We consider two knowledge sources. The Sentence corpus (S) consists of domain-targeted $~$ 80K sentences and 280 GB of plain text extracted from web pages used by BIBREF6 aristo2016:combining. This corpus is used by the IR solver and also used to create the tuple KB T and on-the-fly tuples $T^{\prime }_{qa}$ . Additionally, TableILP uses $\sim $ 70 Curated tables (C) designed for 4th grade NY Regents exams.
```
</details>

**Model_Delta:**

> The source of the OpenIE extractions was the Sentence corpus (S).

**Model_Epsilon:**

> The Sentence corpus (S) was the source of the OpenIE extractions.

---

### REV-04 (manifest item #76, arXiv:1709.00387)
**Paper:** *MIT-QCRI Arabic Dialect Identification System for the 2017 Multi-Genre Broadcast Challenge*  
**Question:** Which are the four Arabic dialects?

<details><summary>Context given to the model</summary>

```text
For the MGB-3 ADI task, the challenge organizers provided 13,825 utterances (53.6 hours) for the training (TRN) set, 1,524 utterances (10 hours) for a development (DEV) set, and 1,492 utterances (10.1 hours) for a test (TST) set. Each dataset consisted of five Arabic dialects: Egyptian (EGY), Levantine (LEV), Gulf (GLF), North African (NOR), and Modern Standard Arabic (MSA). Detailed statistics of the ADI dataset can be found in BIBREF23 . Table TABREF3 shows some facts about the evaluation conditions and data properties. Note that the development set is relatively small compared to the training set. However, it is matched with the test set channel domain. Thus, the development set provides valuable information to adapt or compensate the channel (recording) domain mismatch between the train and test sets.
```
</details>

**Model_Delta:**

> The four Arabic dialects are Egyptian (EGY), Levantine (LEV), Gulf (GLF), and North African (NOR).

**Model_Epsilon:**

> Egyptian (EGY), Levantine (LEV), Gulf (GLF), North African (NOR), and Modern Standard Arabic (MSA).

---

### REV-05 (manifest item #101, arXiv:1711.04457)
**Paper:** *Word, Subword or Character? An Empirical Study of Granularity in Chinese-English NMT*  
**Question:** What dataset did they use?

<details><summary>Context given to the model</summary>

```text
Our training data consists of 2.09M sentence pairs extracted from LDC corpus. Table 1 shows the detailed statistics of our training data. To test different approaches on Chinese-to-English translation task, we use NIST 2003(MT03) dataset as the validation set, and NIST 2004(MT04), NIST 2005(MT05), NIST 2006(MT06) datasets as our test sets. For English-to-Chinese translation task, we also use NIST 2003(MT03) dataset as the validation set, and NIST 2008(MT08) will be used as test set.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> They used the NIST 2003(MT03) dataset for validation and test sets in both Chinese-to-English and English-to-Chinese translation tasks.

---

### REV-06 (manifest item #126, arXiv:1805.12070)
**Paper:** *Code-Switching Language Modeling using Syntax-Aware Multi-Task Learning*  
**Question:** What languages are explored in the work?

<details><summary>Context given to the model</summary>

```text
In this section, we present the experimental setting for this task

Corpus: SEAME (South East Asia Mandarin-English), a conversational Mandarin-English code-switching speech corpus consists of spontaneously spoken interviews and conversations BIBREF8 . Our dataset (LDC2015S04) is the most updated version of the Linguistic Data Consortium (LDC) database. However, the statistics are not identical to BIBREF23 . The corpus consists of two phases. In Phase I, only selected audio segments were transcribed. In Phase II, most of the audio segments were transcribed. According to the authors, it was not possible to restore the original dataset. The authors only used Phase I corpus. Few speaker ids are not in the speaker list provided by the authors BIBREF23 . Therefore as a workaround, we added these ids to the train set. As our future reference, the recording lists are included in the supplementary material.
```
</details>

**Model_Delta:**

> The languages explored in the work are Mandarin and English.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-07 (manifest item #151, arXiv:1808.10113)
**Paper:** *Story Ending Generation with Incremental Encoding and Commonsense Knowledge*  
**Question:** Which baselines are they using?

<details><summary>Context given to the model</summary>

```text
We compared our models with the following state-of-the-art baselines:

Sequence to Sequence (Seq2Seq): A simple encoder-decoder model which concatenates four sentences to a long sentence with an attention mechanism BIBREF31 .

Hierarchical LSTM (HLSTM): The story context is represented by a hierarchical LSTM: a word-level LSTM for each sentence and a sentence-level LSTM connecting the four sentences BIBREF29 . A hierarchical attention mechanism is applied, which attends to the states of the two LSTMs respectively.

HLSTM+Copy: The copy mechanism BIBREF32 is applied to hierarchical states to copy the words in the story context for generation.

HLSTM+Graph Attention(GA): We applied multi-source attention HLSTM where commonsense knowledge is encoded by graph attention.

HLSTM+Contextual Attention(CA): Contextual attention is applied to represent commonsense knowledge.
```
</details>

**Model_Delta:**

> The baselines used are Sequence to Sequence (Seq2Seq), Hierarchical LSTM (HLSTM), HLSTM+Copy, HLSTM+Graph Attention (GA), and HLSTM+Contextual Attention (CA).

**Model_Epsilon:**

> They are using the following baselines:
>
> 1. Sequence to Sequence (Seq2Seq)
> 2. Hierarchical LSTM (HLSTM)
> 3. HLSTM+Copy
> 4. HLSTM+Graph Attention (GA)
> 5. HLSTM+Contextual Attention (CA)

---

### REV-08 (manifest item #176, arXiv:1811.01299)
**Paper:** *SimplerVoice: A Key Message&Visual Description Generator System for Illiteracy*  
**Question:** Does their solution involve connecting images and text?

<details><summary>Context given to the model</summary>

```text
Once the S-V-O is generated, Text2Visual provides users with visual components that convey the S-V-O text meanings.
```
</details>

**Model_Delta:**

> Yes, their solution involves connecting images and text.

**Model_Epsilon:**

> Yes, their solution involves connecting images and text.

---

### REV-09 (manifest item #201, arXiv:1904.03339)
**Paper:** *ThisIsCompetition at SemEval-2019 Task 9: BERT is unstable for out-of-domain samples*  
**Question:** What datasets were used?

<details><summary>Context given to the model</summary>

```text
JESSI is trained using only the datasets given on the shared task, without using any additional external data. Despite this, JESSI performs second on Subtask A with an F1 score of 77.78% among 33 other team submissions. It also performs well on Subtask B with an F1 score of 79.59%.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-10 (manifest item #226, arXiv:1905.10044)
**Paper:** *BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions*  
**Question:** how was the dataset built?

<details><summary>Context given to the model</summary>

```text
Questions are gathered from anonymized, aggregated queries to the Google search engine. Queries that are likely to be yes/no questions are heuristically identified: we found selecting queries where the first word is in a manually constructed set of indicator words and are of sufficient length, to be effective.

Questions are only kept if a Wikipedia page is returned as one of the first five results, in which case the question and Wikipedia page are given to a human annotator for further processing.

Annotators label question/article pairs in a three-step process. First, they decide if the question is good, meaning it is comprehensible, unambiguous, and requesting factual information. This judgment is made before the annotator sees the Wikipedia page. Next, for good questions, annotators find a passage within the document that contains enough information to answer the question. Annotators can mark questions as “not answerable" if the Wikipedia article does not contain the requested information. Finally, annotators mark whether the question's answer is “yes" or “no". Annotating data in this manner is quite expensive since annotators need to search entire Wikipedia documents for relevant evidence and read the text carefully.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The dataset was built by gathering anonymized, aggregated queries from the Google search engine that were likely to be yes/no questions. These were identified heuristically by selecting queries where the first word was in a manually constructed set of indicator words and were of sufficient length. Only questions that returned a Wikipedia page as one of the first five results were kept. These question/article pairs were then given to human annotators for further processing. The annotators labeled the pairs in a three-step process: determining if the question was good (comprehensible, unambiguous, and factual), finding a passage within the Wikipedia article that contained enough information to answer the question, and marking whether the answer was "yes" or "no". The process was expensive as it required annotators to search entire Wikipedia documents for relevant evidence and read the text carefully.

---

### REV-11 (manifest item #251, arXiv:1907.11907)
**Paper:** *Nefnir: A high accuracy lemmatizer for Icelandic*  
**Question:** Which dataset do they use?

<details><summary>Context given to the model</summary>

```text
We have evaluated the output of Nefnir against a reference corpus of 21,093 tokens and their correct lemmas.

Samples for the reference corpus were extracted from two larger corpora, in order to obtain a diverse vocabulary:
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-12 (manifest item #276, arXiv:1908.10383)
**Paper:** *Facet-Aware Evaluation for Extractive Text Summarization*  
**Question:** What is the problem with existing metrics that they are trying to address?

<details><summary>Context given to the model</summary>

```text
Building Extractive CNN/Daily Mail
```
</details>

**Model_Delta:**

> The problem with existing metrics is that they do not consider the context of the text, which is crucial for evaluating the quality of an extractive text summarization.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-13 (manifest item #301, arXiv:1909.03544)
**Paper:** *Czech Text Processing with Contextual Embeddings: POS Tagging, Lemmatization, Parsing and NER*  
**Question:** What data is used to build the embeddings?

<details><summary>Context given to the model</summary>

```text
pretrained word embeddings (WE): For the PDT experiments, we generate the word embeddings with word2vec on a concatenation of large raw Czech corpora available from the LINDAT/CLARIN repository. For UD Czech, we use FastText word embeddings BIBREF27 of dimension 300, which we pretrain on Czech Wikipedia using segmentation and tokenization trained from the UD data.

BERT BIBREF1: Pretrained contextual word embeddings of dimension 768 from the Base model. We average the last four layers of the BERT model to produce the embeddings. Because BERT utilizes word pieces, we decompose UD words into appropriate subwords and then average the generated embeddings over subwords belonging to the same word.

Flair BIBREF2: Pretrained contextual word embeddings of dimension 4096.
```
</details>

**Model_Delta:**

> The embeddings are built using concatenation of large raw Czech corpora available from the LINDAT/CLARIN repository for word2vec, and Czech Wikipedia for FastText embeddings. For BERT, the embeddings are generated from the Base model using word pieces decomposed from UD words. For Flair, the context is not specified.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-14 (manifest item #326, arXiv:1909.08824)
**Paper:** *Modeling Event Background for If-Then Commonsense Reasoning Using Context-aware Variational Autoencoder*  
**Question:** How do they measure the diversity of inferences?

<details><summary>Context given to the model</summary>

```text
We first compare the perplexity of CWVAE with baseline methods. Perplexity measures the probability of model to regenerate the exact targets, which is particular suitable for evaluating the model performance on one-to-many problem BIBREF20. Further, we employ BLEU score to evaluate the accuracy of generations BIBREF21, and the number of distinct n-gram to evaluate the diversity of generations BIBREF6. The distinct is normalized to $[0, 1]$ by dividing the total number of generated tokens.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-15 (manifest item #351, arXiv:1910.06748)
**Paper:** *Language Identification on Massive Datasets of Short Message using an Attention Mechanism CNN*  
**Question:** Which existing language ID systems are tested?

<details><summary>Context given to the model</summary>

```text
For the benchmarks, we selected five systems. We picked first the langid.py library which is frequently used to compare systems in the literature. Since our work is in neural-network LID, we selected two neural network systems from the literature, specifically the encoder-decoder EquiLID system of BIBREF6 and the GRU neural network LanideNN system of BIBREF10. Finally, we included CLD2 and CLD3, two implementations of the Naïve Bayes LID software used by Google in their Chrome web browser BIBREF4, BIBREF0, BIBREF8 and sometimes used as a comparison system in the LID literature BIBREF7, BIBREF6, BIBREF8, BIBREF2, BIBREF10. We obtained publicly-available implementations of each of these algorithms, and test them all against our three datasets. In Table TABREF33, we report each algorithm's accuracy and F1 score, the two metrics usually reported in the LID literature. We also included precision and recall values, which are necessary for computing F1 score. And finally we included the speed in number of messages handled per second. This metric is not often discussed in the LID literature, but is of particular importance when dealing with a massive dataset such as ours or a massive streaming source such as Twitter.
```
</details>

**Model_Delta:**

> The existing language ID systems tested are:
>
> 1. langid.py library
> 2. Encoder-decoder EquiLID system
> 3. GRU neural network LanideNN system
> 4. CLD2 and CLD3, two implementations of the Naïve Bayes LID software
> 5. Google's Naïve Bayes LID software (used in Chrome web browser)

**Model_Epsilon:**

> The existing language ID systems tested are langid.py, the encoder-decoder EquiLID system, the GRU neural network LanideNN system, CLD2, and CLD3.

---

### REV-16 (manifest item #376, arXiv:1911.03310)
**Paper:** *How Language-Neutral is Multilingual BERT?*  
**Question:** What challenges this work presents that must be solved to build better language-neutral representations?

<details><summary>Context given to the model</summary>

```text
Using a set of semantically oriented tasks that require explicit semantic cross-lingual representations, we showed that mBERT contextual embeddings do not represent similar semantic phenomena similarly and therefore they are not directly usable for zero-shot cross-lingual tasks.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---

### REV-17 (manifest item #401, arXiv:1911.13066)
**Paper:** *A Multi-cascaded Deep Model for Bilingual SMS Classification*  
**Question:** What is their baseline model?

<details><summary>Context given to the model</summary>

```text
We re-implement the model proposed in BIBREF3, and use it as a baseline for our problem. The rationale behind choosing this particular model as a baseline is it's proven good predictive performance on multilingual text classification. For McM, the choices of number of convolutional filters, number of hidden units in first dense layer, number of hidden units in second dense layer, and recurrent units for LSTM are made empirically. Rest of the hyperparameters were selected by performing grid search using $20\%$ stratified validation set from training set on McM$_\textsubscript {R}$. Available choices and final selected parameters are mentioned in Table TABREF18. These choices remained same for all experiments and the validation set was merged back into training set.
```
</details>

**Model_Delta:**

> The baseline model is the one proposed in BIBREF3, which is a multi-cascaded deep model for bilingual SMS classification.

**Model_Epsilon:**

> The baseline model used in the study is the one proposed in BIBREF3.

---

### REV-18 (manifest item #426, arXiv:1912.13109)
**Paper:** *"Hinglish"Language -- Modeling a Messy Code-Mixed Language*  
**Question:** What is the previous work's model?

<details><summary>Context given to the model</summary>

```text
Mathur et al. in their paper for detecting offensive tweets proposed a Ternary Trans-CNN model where they train a model architecture comprising of 3 layers of Convolution 1D having filter sizes of 15, 12 and 10 and kernel size of 3 followed by 2 dense fully connected layer of size 64 and 3. The first dense FC layer has ReLU activation while the last Dense layer had Softmax activation. They were able to train this network on a parallel English dataset provided by Davidson et al. The authors were able to achieve Accuracy of 83.9%, Precision of 80.2%, Recall of 69.8%.

The approach looked promising given that the dataset was merely 3189 sentences divided into three categories and thus we replicated the experiment but failed to replicate the results. The results were poor than what the original authors achieved. But, most of the model hyper-parameter choices where inspired from this work.
```
</details>

**Model_Delta:**

> The previous work's model is a Ternary Trans-CNN model proposed by Mathur et al.

**Model_Epsilon:**

> The previous work's model is a Ternary Trans-CNN model proposed by Mathur et al. for detecting offensive tweets. It consists of 3 layers of Convolution 1D with filter sizes of 15, 12, and 10 and a kernel size of 3, followed by 2 dense fully connected layers of size 64 and 3. The first dense FC layer uses ReLU activation, while the last Dense layer uses Softmax activation. This model was trained on a parallel English dataset and achieved an Accuracy of 83.9%, Precision of 80.2%, and Recall of 69.8%.

---

### REV-19 (manifest item #451, arXiv:2002.01861)
**Paper:** *Rapid Adaptation of BERT for Information Extraction on Domain-Specific Business Documents*  
**Question:** What type of documents are supported by the annotation platform?

<details><summary>Context given to the model</summary>

```text
All the capabilities described in this paper come together in an end-to-end cloud-based platform that we have built. The platform has two main features: First, it provides an annotation interface that allows users to define content elements, upload documents, and annotate documents; a screenshot is shown in Figure FIGREF12. We have invested substantial effort in making the interface as easy to use as possible; for example, annotating content elements is as easy as selecting text from the document. Our platform is able to ingest documents in a variety of formats, including PDFs and Microsoft Word, and converts these formats into plain text before presenting them to the annotators.
```
</details>

**Model_Delta:**

> The annotation platform supports a variety of document formats, including PDFs and Microsoft Word documents.

**Model_Epsilon:**

> The annotation platform supports documents in a variety of formats, including PDFs and Microsoft Word.

---

### REV-20 (manifest item #476, arXiv:2003.05377)
**Paper:** *Brazilian Lyrics-Based Music Genre Classification Using a BLSTM Network*  
**Question:** what genres do they songs fall under?

<details><summary>Context given to the model</summary>

```text
From the Vagalume's music web page, we collect the song title and lyrics, and the artist name. The genre was collected from the page of styles, which lists all the musical genres and, for each one, all the artists. We selected only 14 genres that we consider as representative Brazilian music, shown in Table TABREF8. Figure FIGREF6 presents an example of the Vagalume's music Web page with the song “Como é grande o meu amor por você”, of the Brazilian singer Roberto Carlos. Green boxes indicate information about music that can be extracted directly from the web page. From this information, the language in which the lyrics are available can be obtained by looking at the icon indicating the flag of Brazil preceded by the “Original” word.
```
</details>

**Model_Delta:**

> The document does not contain sufficient relevant information to answer this question.

**Model_Epsilon:**

> The document does not contain sufficient relevant information to answer this question.

---
