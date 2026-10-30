# ResearchQA Method A — Survey Section Ground-Truth Retrieval Report

> **Generated:** `2026-10-30T04:14:03.806942 UTC`  
> **Strategies evaluated:** `bm25`, `dense`, `hybrid_rrf`  
> **Benchmark:** `eval/prepared/researchqa_survey_sampled.json`

---

## 1. Overview

Method A treats each ResearchQA survey-paper section as a ground-truth evidence source,
constructing QASPER-schema-identical queries with `verbatim_evidence_quote` + `evidence_list`.
The same `is_chunk_hit` containment check (τ=0.55) and nDCG/MRR/Recall metrics used in the
existing QASPER harness are applied here, making results directly comparable.

---

## 2. Main Results — All Strategies

| Strategy | nDCG@4 | nDCG@10 | MRR@5 | Hit@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `bm25` | 0.2479 | 0.3391 *(±-0.015 CI)* | 0.3026 | 0.5216 | 0.7410 | 0.1951 |
| `dense` | 0.2578 | 0.3414 *(±-0.015 CI)* | 0.3088 | 0.5236 | 0.7435 | 0.2012 |
| `hybrid_rrf` | 0.2536 | 0.3422 *(±-0.015 CI)* | 0.3049 | 0.5175 | 0.7392 | 0.2033 |

### 2.1 Comparison vs QASPER Held-Out Baselines

| Dataset / Method | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 |
| :--- | :---: | :---: | :---: | :---: |
| QASPER BM25 *(reference)* | 0.3812 | 0.4103 | 0.4521 | 0.8930 |
| QASPER Dense E5 *(reference)* | 0.4952 | 0.5213 | 0.5814 | 0.9256 |
| QASPER Hybrid RRF *(reference)* | 0.5121 | 0.5384 | 0.5991 | 0.9560 |
| **ResearchQA Survey `bm25`** | **0.2479** | **0.3391** | **0.3026** | **0.7410** |
| **ResearchQA Survey `dense`** | **0.2578** | **0.3414** | **0.3088** | **0.7435** |
| **ResearchQA Survey `hybrid_rrf`** | **0.2536** | **0.3422** | **0.3049** | **0.7392** |

---

## 3. Dev / Held-Out Split Breakdown

### Strategy: `bm25`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| all | 487 | 0.2479 | 0.3391 | 0.3026 | 0.7410 | 0.1951 |

### Strategy: `dense`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| all | 487 | 0.2578 | 0.3414 | 0.3088 | 0.7435 | 0.2012 |

### Strategy: `hybrid_rrf`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| all | 487 | 0.2536 | 0.3422 | 0.3049 | 0.7392 | 0.2033 |

---

## 4. Per-Query Detail

### `bm25` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_QASP_010` | `1801.05147` | Data Sets | 🟢 | 0.0000 | 0.0000 | Data Sets |
| `Q_QASP_020` | `1909.00512` | Approach ::: Measures of Contextual | 🔴 | 0.1699 | 0.5000 | Abstract |
| `Q_QASP_021` | `1909.00512` | Introduction | 🔴 | 0.0000 | 0.0000 | Approach ::: Measures of Contextuality : |
| `Q_QASP_022` | `2003.03106` | Results ::: Experiment A: NUBes-PHI | 🔴 | 0.0000 | 0.6667 | Materials and Methods ::: Systems ::: BE |
| `Q_QASP_023` | `2003.03106` | Materials and Methods ::: Systems : | 🔴 | 0.1510 | 0.2500 | Materials and Methods |
| `Q_QASP_025` | `2003.03106` | Materials and Methods ::: Data | 🟢 | 0.5842 | 0.8333 | Materials and Methods ::: Data |
| `Q_QASP_038` | `1605.06083` | Introduction | 🟢 | 0.8066 | 1.0000 | Introduction |
| `Q_QASP_039` | `1605.06083` | Other methods | 🔴 | 0.1301 | 0.5000 | Abstract |
| `Q_QASP_040` | `1605.06083` | Introduction | 🔴 | 0.1131 | 0.6000 | Abstract |
| `Q_QASP_041` | `1804.05918` | Experimental Results | 🔴 | 0.3392 | 0.8000 | Dataset and Preprocessing |
| `Q_QASP_042` | `1804.05918` | Experimental Results | 🔴 | 0.1413 | 1.0000 | Abstract |
| `Q_QASP_044` | `1901.05287` | Results | 🔴 | 0.4312 | 1.0000 | Introduction |
| `Q_QASP_045` | `1612.06685` | Psycholinguistic and Semantic Maps | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_046` | `1612.06685` | Data Collection | 🔴 | 0.4976 | 1.0000 | Abstract |
| `Q_QASP_051` | `1910.10781` | Introduction | 🔴 | 0.4297 | 0.6667 | Related work |
| `Q_QASP_052` | `1910.10781` | Introduction | 🟢 | 0.3120 | 1.0000 | Introduction |
| `Q_QASP_055` | `1911.06964` | Experiments | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_056` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.0000 | 1.0000 | Approach |
| `Q_QASP_057` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_058` | `1911.06964` | Experiments ::: Efficiency-accuracy | 🔴 | 0.6309 | 1.0000 | Approach ::: Modeling with autoencoders. |
| `Q_QASP_059` | `2001.02284` | Model ::: Dialogue Modules | 🔴 | 0.0000 | 0.2500 | Related Work |
| `Q_QASP_060` | `2001.02284` | Re-implementation of units with BER | 🔴 | 0.0980 | 0.2000 | Introduction ::: Outline and Contributio |
| `Q_QASP_061` | `2001.02284` | Target Domain & Task Definition | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_071` | `1809.00540` | Related Work | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_072` | `1809.00540` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_073` | `2004.03354` | Experiment 1: Biomedical NER ::: Do | 🔴 | 0.2346 | 0.3333 | Abstract |
| `Q_QASP_075` | `1611.04798` | Introduction | 🟢 | 0.3333 | 1.0000 | Introduction |
| `Q_QASP_076` | `1611.04798` | Under-resourced Translation | 🟢 | 0.8772 | 1.0000 | Under-resourced Translation |
| `Q_QASP_088` | `1809.09194` | Model | 🟢 | 0.8503 | 1.0000 | Model |
| `Q_QASP_089` | `1809.09194` | Results | 🔴 | 0.0000 | 1.0000 | Background |
| `Q_QASP_090` | `1809.09194` | Model | 🟢 | 0.6131 | 1.0000 | Model |
| `Q_QASP_091` | `1604.05372` | Learning to Translate: Ukrainian-to | 🔴 | 0.0000 | 0.5000 | Academic texts as Comparable Corpora |
| `Q_QASP_092` | `2002.08795` | Introduction | 🔴 | 0.5641 | 1.0000 | Abstract |
| `Q_QASP_093` | `2002.08795` | Introduction and Background | 🔴 | 0.8208 | 1.0000 | Abstract |
| `Q_QASP_094` | `2002.08795` | Introduction and Background | 🔴 | 0.3874 | 0.8571 | Abstract |
| `Q_QASP_096` | `1802.06024` | Experiments | 🔴 | 0.4483 | 0.5714 | Results and Analysis |
| `Q_QASP_097` | `1802.06024` | Experiments | 🟢 | 0.2769 | 0.6667 | Experiments |
| `Q_QASP_098` | `1802.06024` | Introduction | 🔴 | 0.5641 | 1.0000 | Abstract |
| `Q_QASP_099` | `1802.06024` | Experiments | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_100` | `1802.06024` | Introduction | 🔴 | 0.2730 | 0.7500 | Abstract |
| `Q_QASP_105` | `1710.07960` | Discussion | 🔴 | 0.1772 | 0.5000 | Introduction |
| `Q_QASP_106` | `1710.07960` | Introduction | 🔴 | 0.5307 | 0.8571 | Conclusions |
| `Q_QASP_107` | `1912.03804` | Related Work | 🟢 | 0.7039 | 1.0000 | Related Work |
| `Q_QASP_108` | `1912.03804` | Conclusion and Future Work | 🔴 | 0.3409 | 0.6000 | Abstract |
| `Q_QASP_109` | `1912.03804` | Method ::: Emotion detection | 🔴 | 0.6053 | 1.0000 | Related Work |
| `Q_QASP_110` | `1912.03804` | Introduction | 🔴 | 0.8365 | 0.5000 | Abstract |
| `Q_QASP_111` | `1912.03804` | Method ::: Content Analysis | 🔴 | 0.2520 | 1.0000 | Abstract |
| `Q_QASP_112` | `1912.08960` | Introduction | 🔴 | 0.1681 | 1.0000 | Experimental Setup ::: Datasets |
| `Q_QASP_113` | `1912.08960` | Experimental Setup ::: Datasets | 🔴 | 0.1357 | 0.6667 | Related work ::: Synthetic datasets |
| `Q_QASP_114` | `1912.08960` | Experimental Setup ::: Models | 🔴 | 0.0000 | 1.0000 | Experimental Setup ::: Datasets |
| `Q_QASP_115` | `1912.08960` | GTD Evaluation Framework ::: Divers | 🔴 | 0.5803 | 1.0000 | Experimental Setup ::: Datasets |
| `Q_QASP_128` | `2004.01853` | Introduction | 🔴 | 0.4307 | 1.0000 | Experimental Setup ::: Datasets ::: GIGA |
| `Q_QASP_129` | `2004.01853` | Results ::: Automatic Evaluation | 🟢 | 0.9197 | 1.0000 | Results ::: Automatic Evaluation |
| `Q_QASP_130` | `1710.03348` | Introduction | 🔴 | 0.2443 | 0.8000 | Abstract |
| `Q_QASP_131` | `1710.03348` | Impact of Attention Mechanism | 🔴 | 0.2372 | 0.5000 | Attention Models |
| `Q_QASP_132` | `1710.03348` | Alignment Quality Impact on Transla | 🔴 | 0.2184 | 0.5000 | Abstract |
| `Q_QASP_138` | `1809.01202` | Experiment | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_139` | `1809.01202` | Dataset | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_140` | `1909.02027` | Dataset ::: In-Scope Data Collectio | 🔴 | 0.0000 | 1.0000 | Dataset |
| `Q_QASP_141` | `1909.02027` | Introduction | 🔴 | 0.4693 | 1.0000 | Benchmark Evaluation |
| `Q_QASP_142` | `1909.02027` | Introduction | 🔴 | 0.3869 | 1.0000 | Results ::: Results with oos-train |
| `Q_QASP_143` | `1909.02027` | Dataset | 🔴 | 0.2977 | 0.6667 | Benchmark Evaluation ::: Out-of-Scope Pr |
| `Q_QASP_151` | `1611.01576` | Character-level Neural Machine Tran | 🟢 | 1.0000 | 1.0000 | Character-level Neural Machine Translati |
| `Q_QASP_152` | `1611.01576` | Sentiment Classification | 🟢 | 1.0000 | 1.0000 | Sentiment Classification |
| `Q_QASP_153` | `1611.01576` | Model | 🔴 | 0.2641 | 1.0000 | Variants |
| `Q_QASP_161` | `1909.08089` | Results and Analysis | 🔴 | 0.1846 | 1.0000 | Introduction |
| `Q_QASP_162` | `1909.08089` | Introduction | 🔴 | 0.2044 | 1.0000 | Extractive summarization |
| `Q_QASP_164` | `1910.09982` | Data | 🔴 | 0.0000 | 0.5000 | Participants and Approaches ::: Teams Pa |
| `Q_QASP_165` | `1910.09982` | Baselines | 🟢 | 1.0000 | 1.0000 | Baselines |
| `Q_QASP_166` | `1609.00559` | Introduction | 🔴 | 0.6309 | 1.0000 | Method |
| `Q_QASP_167` | `1609.00559` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_168` | `1609.00559` | Comparison with Previous Work | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 1.0000 | Decoding the KB Query |
| `Q_QASP_170` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_173` | `1608.01084` | Data Set and Toolkits | 🟢 | 0.0000 | 0.0000 | Data Set and Toolkits |
| `Q_QASP_174` | `1904.10503` | Introduction | 🔴 | 1.0000 | 1.0000 | Conclusion and Future Work |
| `Q_QASP_175` | `1904.10503` | Results | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_176` | `1904.10503` | Entity Linking using Wikidata | 🔴 | 0.2140 | 0.8000 | Abstract |
| `Q_QASP_177` | `1912.01772` | Introduction | 🔴 | 0.4776 | 0.7778 | Abstract |
| `Q_QASP_178` | `1912.01772` | The Resource ::: Additional Annotat | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_179` | `1603.01987` | The medical domain model | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_184` | `1702.03856` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_185` | `1702.03856` | Introduction | 🔴 | 0.6332 | 1.0000 | Analysis of challenges from UTD |
| `Q_QASP_186` | `1702.03856` | Dataset | 🔴 | 0.3869 | 1.0000 | Introduction |
| `Q_QASP_189` | `1606.03676` | Corpora | 🔴 | 0.0000 | 0.0000 | Baseline models |
| `Q_QASP_190` | `1606.03676` | Corpora | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_193` | `1911.03343` | Introduction | 🔴 | 0.3978 | 1.0000 | Abstract |
| `Q_QASP_209` | `1909.07575` | Experiments ::: Baseline Models and | 🔴 | 0.5508 | 1.0000 | Abstract |
| `Q_QASP_210` | `1909.07575` | Our method ::: Training Procedure : | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_212` | `1904.07904` | Spoken Question Answering | 🟢 | 1.0000 | 1.0000 | Spoken Question Answering |
| `Q_QASP_213` | `1904.07904` | Results | 🔴 | 0.6509 | 1.0000 | Conclusion |
| `Q_QASP_214` | `1904.07904` | Results | 🔴 | 0.4367 | 0.6667 | Conclusion |
| `Q_QASP_215` | `1904.07904` | Corpus | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_216` | `2003.11645` | Introduction | 🔴 | 1.0000 | 1.0000 | Methodology |
| `Q_QASP_217` | `2003.11645` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_218` | `2003.11645` | Introduction | 🟢 | 0.7904 | 1.0000 | Introduction |
| `Q_QASP_219` | `2003.11645` | Introduction | 🔴 | 0.0000 | 1.0000 | Literature Review |
| `Q_QASP_222` | `1604.03114` | Modeling Idea Flow | 🔴 | 0.2692 | 0.7500 | Abstract |
| `Q_QASP_223` | `1604.03114` | Debate Dataset: Intelligence Square | 🟢 | 1.0000 | 1.0000 | Debate Dataset: Intelligence Squared |
| `Q_QASP_227` | `1606.02891` | Baseline System | 🔴 | 0.6053 | 1.0000 | Abstract |
| `Q_QASP_228` | `1803.09123` | Empirical Study | 🔴 | 0.3904 | 0.7500 | Introduction |
| `Q_QASP_229` | `1803.09123` | Discovering Semantically Similar Eq | 🔴 | 0.5205 | 1.0000 | Equation Unit Embeddings |
| `Q_QASP_237` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.7542 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_238` | `1709.07814` | Attention-based Encoder Decoder for | 🔴 | 0.3651 | 1.0000 | Speech Data |
| `Q_QASP_239` | `1709.07814` | Speech Data | 🔴 | 0.1510 | 0.2500 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_249` | `2003.08380` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_251` | `1805.04508` | Gender Bias Results | 🔴 | 0.1357 | 1.0000 | Abstract |
| `Q_QASP_252` | `1805.04508` | The Equity Evaluation Corpus | 🔴 | 0.3191 | 0.7500 | Introduction |
| `Q_QASP_258` | `1910.05603` | System Description ::: Language Mod | 🟢 | 0.7670 | 1.0000 | System Description ::: Language Model |
| `Q_QASP_259` | `1910.05603` | Experiments ::: System combination | 🔴 | 0.5000 | 1.0000 | Conclusion |
| `Q_QASP_260` | `1910.05603` | System Description ::: Acoustic Mod | 🔴 | 0.3562 | 1.0000 | Experiments ::: Single system evaluation |
| `Q_QASP_261` | `1909.03405` | Results of NLI Tasks ::: GLUE | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_262` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.5000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_263` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_134` | `1909.08859` | Procedural Reasoning Networks | 🔴 | 0.2346 | 1.0000 | Abstract |
| `Q_QASP_135` | `1909.08859` | Experiments ::: Baselines | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_136` | `1909.08859` | Experiments ::: Results | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_541` | `1905.06566` | Introduction | 🔴 | 0.8539 | 0.8000 | Results |
| `Q_QASP_116` | `1708.05873` | Introduction | 🔴 | 0.6189 | 1.0000 | Abstract |
| `Q_QASP_117` | `1708.05873` | Introduction | 🔴 | 0.2891 | 1.0000 | Conclusion |
| `Q_QASP_118` | `1708.05873` | Estimation of topic models | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_303` | `1807.00868` | Using different features | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_304` | `1807.00868` | Basic setup | 🔴 | 0.3869 | 1.0000 | Related work |
| `Q_QASP_305` | `1807.00868` | Training the best model | 🟢 | 1.0000 | 1.0000 | Training the best model |
| `Q_QASP_505` | `2003.03612` | Introduction | 🔴 | 0.4939 | 0.7500 | Discussion |
| `Q_QASP_506` | `2003.03612` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_507` | `2003.03612` | Introduction | 🔴 | 0.0000 | 0.0000 | Multinomials |
| `Q_QASP_508` | `2003.03612` | Introduction | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_509` | `2003.03612` | Models And Predictions ::: Predicti | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_510` | `2003.03612` | Models And Predictions ::: Predicti | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_511` | `2003.03612` | Introduction | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_163` | `1810.06743` | Results | 🟢 | 0.4693 | 0.3333 | Results |
| `Q_QASP_164` | `1810.06743` | Conclusion and Future Work | 🔴 | 0.0000 | 0.0000 | Similarities in the annotation |
| `Q_QASP_165` | `1810.06743` | Introduction | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_166` | `1810.06743` | Introduction | 🔴 | 0.3661 | 0.6000 | Abstract |
| `Q_QASP_284` | `1603.07044` | Introduction | 🔴 | 0.4367 | 1.0000 | Multitask Learning |
| `Q_QASP_286` | `1603.07044` | Conclusion | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_476` | `1810.00663` | Introduction | 🔴 | 0.4693 | 0.6667 | Dataset |
| `Q_QASP_477` | `1810.00663` | Quantitative Evaluation | 🔴 | 0.2961 | 1.0000 | Models Used in the Evaluation |
| `Q_QASP_478` | `1810.00663` | Models Used in the Evaluation | 🔴 | 0.5000 | 1.0000 | Evaluation Metrics |
| `Q_QASP_479` | `1810.00663` | Evaluation Metrics | 🟢 | 0.8520 | 1.0000 | Evaluation Metrics |
| `Q_QASP_480` | `1810.00663` | Introduction | 🔴 | 0.0000 | 1.0000 | Acknowledgments |
| `Q_QASP_481` | `1810.00663` | Introduction | 🔴 | 0.8319 | 0.7500 | Dataset |
| `Q_QASP_482` | `1810.00663` | Dataset | 🔴 | 0.2372 | 1.0000 | Quantitative Evaluation |
| `Q_QASP_193` | `2004.03685` | Towards Better Faithfulness Criteri | 🟢 | 0.6131 | 0.5000 | Towards Better Faithfulness Criteria |
| `Q_QASP_194` | `2004.03685` | Towards Better Faithfulness Criteri | 🔴 | 0.3869 | 1.0000 | Faithfulness vs. Plausibility |
| `Q_QASP_195` | `2004.03685` | Introduction | 🔴 | 0.0909 | 1.0000 | Defining Faithfulness |
| `Q_QASP_196` | `2004.03685` | Introduction | 🔴 | 0.8007 | 0.9000 | Guidelines for Evaluating Faithfulness : |
| `Q_QASP_658` | `1805.00760` | Model Description | 🔴 | 0.0000 | 1.0000 | Attention Visualization and Case Study |
| `Q_QASP_659` | `1805.00760` | Introduction | 🟢 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_660` | `1805.00760` | Datasets | 🔴 | 0.0000 | 1.0000 | Settings |
| `Q_QASP_661` | `1805.00760` | Main Results | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_587` | `1911.03243` | Dataset Quality Analysis ::: Agreem | 🔴 | 0.2044 | 1.0000 | Conclusion |
| `Q_QASP_588` | `1911.03243` | Background — QA-SRL ::: Corpora | 🔴 | 0.3155 | 1.0000 | Dataset Quality Analysis ::: Agreement w |
| `Q_QASP_589` | `1911.03243` | Introduction | 🔴 | 0.9833 | 1.0000 | Dataset Quality Analysis ::: Agreement w |
| `Q_QASP_590` | `1911.03243` | Introduction | 🔴 | 0.3978 | 1.0000 | Background — QA-SRL ::: Corpora |
| `Q_QASP_591` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_592` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_593` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.0000 | 0.0000 | Dataset Quality Analysis ::: Dataset Ass |
| `Q_QASP_594` | `1911.03243` | Dataset Quality Analysis ::: Agreem | 🔴 | 0.3869 | 1.0000 | Dataset Quality Analysis ::: Dataset Ass |
| `Q_QASP_669` | `2004.03744` | SNLI-VE-2.0 ::: Re-annotation detai | 🔴 | 0.0000 | 0.0000 | Visual-Textual Entailment with Natural L |
| `Q_QASP_670` | `2004.03744` | Appendix ::: Details of the Mechani | 🔴 | 0.0000 | 0.0000 | Visual-Textual Entailment with Natural L |
| `Q_QASP_671` | `2004.03744` | Appendix ::: Statistics of e-SNLI-V | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_672` | `2004.03744` | SNLI-VE-2.0 ::: Re-evaluation of Vi | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_673` | `2004.03744` | Introduction | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_342` | `1911.11750` | Background ::: Document Representat | 🔴 | 0.3333 | 1.0000 | Background ::: Measures of Similarity |
| `Q_QASP_343` | `1911.11750` | Experiments | 🔴 | 0.6309 | 1.0000 | The Spearman's Rank Correlation Coeffici |
| `Q_QASP_344` | `1911.11750` | The Spearman's Rank Correlation Coe | 🔴 | 0.0000 | 0.5000 | Introduction |
| `Q_QASP_783` | `1710.07395` | Experimental Results | 🔴 | 0.0000 | 1.0000 | Annotation Procedure |
| `Q_QASP_784` | `1710.07395` | Logistic Regression Models | 🔴 | 0.4556 | 1.0000 | Abstract |
| `Q_QASP_785` | `1710.07395` | Logistic Regression Models | 🔴 | 0.3010 | 1.0000 | Annotation Procedure |
| `Q_QASP_786` | `1710.07395` | Annotation Guidelines | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_787` | `1710.07395` | Neural Network Models | 🟢 | 1.0000 | 1.0000 | Neural Network Models |
| `Q_QASP_253` | `1912.05066` | Introduction | 🔴 | 0.0000 | 0.5000 | Methodology ::: Machine Learning Models |
| `Q_QASP_255` | `1912.05066` | Introduction | 🔴 | 0.4423 | 1.0000 | Data Analysis |
| `Q_QASP_256` | `1912.05066` | Introduction | 🔴 | 0.1772 | 0.5000 | Data Analysis |
| `Q_QASP_257` | `1912.05066` | Methodology ::: Procedure | 🔴 | 0.3041 | 0.6667 | Data Analysis |
| `Q_QASP_059` | `2003.12218` | Results ::: NER Annotation Results | 🔴 | 0.0000 | 1.0000 | Conclusion |
| `Q_QASP_060` | `2003.12218` | Introduction | 🔴 | 0.3501 | 1.0000 | Conclusion |
| `Q_QASP_316` | `1908.10449` | Introduction | 🔴 | 0.2891 | 1.0000 | Abstract |
| `Q_QASP_317` | `1908.10449` | iMRC: Making MRC Interactive | 🔴 | 0.0000 | 0.8000 | Introduction |
| `Q_QASP_318` | `1908.10449` | Introduction | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_319` | `1908.10449` | iMRC: Making MRC Interactive ::: Ac | 🔴 | 0.0000 | 0.6667 | Abstract |
| `Q_QASP_031` | `1811.00942` | Experimental Setup | 🔴 | 0.0000 | 1.0000 | Conclusion |
| `Q_QASP_032` | `1811.00942` | Introduction | 🔴 | 0.2372 | 1.0000 | Abstract |
| `Q_QASP_033` | `1811.00942` | Introduction | 🔴 | 0.3333 | 1.0000 | Infrastructure |
| `Q_QASP_767` | `1606.05286` | Experimental results | 🔴 | 0.6509 | 1.0000 | Abstract |
| `Q_QASP_637` | `1808.00265` | Results | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_638` | `1808.00265` | Results | 🔴 | 0.2891 | 1.0000 | Conclusions |
| `Q_QASP_639` | `1808.00265` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_083` | `1910.03042` | Analysis | 🟢 | 0.1391 | 0.7500 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_084` | `1910.03042` | Analysis ::: Response Depth: Mean W | 🟢 | 1.0000 | 1.0000 | Analysis ::: Response Depth: Mean Word C |
| `Q_QASP_085` | `1910.03042` | System Architecture | 🔴 | 0.3066 | 1.0000 | Abstract |
| `Q_QASP_086` | `1910.03042` | System Architecture | 🔴 | 0.0000 | 0.5000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_087` | `1910.03042` | Analysis | 🟢 | 0.3869 | 0.5000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_088` | `1910.03042` | Analysis ::: Response Depth: Mean W | 🔴 | 0.1413 | 1.0000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_469` | `1911.00069` | Experiments ::: Source (English) RE | 🔴 | 0.6131 | 1.0000 | Experiments ::: Cross-Lingual RE Perform |
| `Q_QASP_470` | `1911.00069` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_471` | `1911.00069` | Experiments ::: Datasets | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_472` | `1911.00069` | Experiments ::: Datasets | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_772` | `1906.10519` | Setting for Experiment 1: Sentence- | 🟢 | 0.0000 | 0.0000 | Setting for Experiment 1: Sentence-level |
| `Q_QASP_649` | `1906.07668` | Visualization | 🔴 | 0.2044 | 0.5000 | Conclusions |
| `Q_QASP_704` | `1607.06275` | WebQA Dataset | 🔴 | 0.0000 | 0.0000 | Baselines |
| `Q_QASP_705` | `1607.06275` | Introduction | 🔴 | 0.8072 | 1.0000 | Baselines |
| `Q_QASP_706` | `1607.06275` | WebQA Dataset | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_152` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_153` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_154` | `1910.07181` | Evaluation ::: Downstream Task Data | 🟢 | 0.4838 | 1.0000 | Evaluation ::: Downstream Task Datasets |
| `Q_QASP_155` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_444` | `1812.07023` | Experiments | 🔴 | 0.3066 | 1.0000 | Abstract |
| `Q_QASP_010` | `2003.07723` | Introduction | 🟢 | 0.4685 | 1.0000 | Introduction |
| `Q_QASP_011` | `2003.07723` | Expert Annotation ::: Agreement | 🔴 | 0.0000 | 0.0000 | Crowdsourcing Annotation |
| `Q_QASP_012` | `2003.07723` | Introduction | 🔴 | 0.3869 | 1.0000 | ::: ::: |
| `Q_QASP_407` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_408` | `1902.06843` | Multi-modal Prediction Framework | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_409` | `1902.06843` | Demographic Prediction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_410` | `1902.06843` | Data Modality Analysis | 🟢 | 0.2895 | 0.3636 | Data Modality Analysis |
| `Q_QASP_411` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.5000 | Untitled Section |
| `Q_QASP_412` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.4000 | Untitled Section |
| `Q_QASP_413` | `1902.06843` | Introduction | 🔴 | 0.3155 | 1.0000 | Untitled Section |
| `Q_QASP_414` | `1902.06843` | Introduction | 🔴 | 0.3869 | 1.0000 | Demographic Prediction |
| `Q_QASP_415` | `1902.06843` | Introduction | 🔴 | 0.0000 | 0.0000 | Demographic Prediction |
| `Q_QASP_585` | `1606.02006` | Settings | 🔴 | 0.0000 | 0.0000 | Hybrid Lexicons |
| `Q_QASP_586` | `1606.02006` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_779` | `2003.05995` | Introduction | 🔴 | 0.0000 | 0.2500 | Abstract |
| `Q_QASP_780` | `2003.05995` | Related Work | 🟢 | 0.4935 | 0.8333 | Related Work |
| `Q_QASP_781` | `2003.05995` | Data Analysis | 🔴 | 0.2337 | 0.3077 | Introduction |
| `Q_QASP_782` | `2003.05995` | System Overview | 🔴 | 0.3591 | 1.0000 | Abstract |
| `Q_QASP_013` | `1705.09665` | Applying the typology to Reddit | 🔴 | 0.2641 | 0.5000 | Community-type and user tenure |
| `Q_QASP_014` | `1705.09665` | Community-type and monthly retentio | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_015` | `1705.09665` | Introduction | 🟢 | 0.0000 | 0.6667 | Introduction |
| `Q_QASP_016` | `1705.09665` | Applying the typology to Reddit | 🔴 | 0.1772 | 1.0000 | Introduction |
| `Q_QASP_017` | `1705.09665` | Community-level measures | 🔴 | 0.0000 | 0.5000 | Acknowledgements |
| `Q_QASP_018` | `1705.09665` | Community-level measures | 🔴 | 0.3155 | 1.0000 | Acknowledgements |
| `Q_QASP_063` | `2003.06651` | Related Work | 🟢 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_064` | `2003.06651` | Evaluation ::: Word Sense Disambigu | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_065` | `2003.06651` | Evaluation | 🔴 | 0.0000 | 1.0000 | Conclusions and Future Work |
| `Q_QASP_422` | `1910.02789` | Semantic State Representations in t | 🔴 | 0.4685 | 1.0000 | Abstract |
| `Q_QASP_425` | `1910.02789` | Semantic State Representations in t | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_426` | `1910.02789` | Introduction | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_160` | `1909.00542` | Classification vs. Regression Exper | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_161` | `1909.00542` | Classification vs. Regression Exper | 🔴 | 0.0000 | 1.0000 | Conclusions |
| `Q_QASP_162` | `1909.00542` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_748` | `1909.01013` | Approach ::: Regularizers for Dual  | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_749` | `1909.01013` | Experiments ::: Comparison with the | 🔴 | 0.3155 | 1.0000 | Introduction |
| `Q_QASP_750` | `1909.01013` | Introduction | 🟢 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_752` | `1909.01013` | Experiments ::: The Effectiveness o | 🔴 | 0.2372 | 1.0000 | Experiments ::: Comparison with the Stat |
| `Q_QASP_753` | `1909.01013` | Experiments ::: Comparison with the | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_613` | `1803.03664` | Experiments and Results | 🔴 | 0.0000 | 1.0000 | Question Generation |
| `Q_QASP_467` | `1708.09157` | Character-Level Neural Transfer | 🔴 | 0.2372 | 1.0000 | Abstract |
| `Q_QASP_468` | `1708.09157` | Datasets | 🔴 | 0.0000 | 0.0000 | Experimental Languages |
| `Q_QASP_244` | `1907.02030` | Choosing an embedding | 🟢 | 0.0000 | 0.0000 | Choosing an embedding |
| `Q_QASP_245` | `1907.02030` | Related Work | 🔴 | 0.1772 | 0.5000 | Abstract |
| `Q_QASP_246` | `1907.02030` | Choosing an embedding | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_170` | `1905.11901` | Data and Preprocessing | 🔴 | 0.1301 | 0.7500 | Hyperparameters |
| `Q_QASP_171` | `1905.11901` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_172` | `1905.11901` | Results | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_173` | `1905.11901` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_512` | `1904.08386` | Embedding city descriptions | 🟢 | 0.8772 | 1.0000 | Embedding city descriptions |
| `Q_QASP_513` | `1904.08386` | Introduction | 🔴 | 0.3562 | 1.0000 | Conclusion |
| `Q_QASP_514` | `1904.08386` | Clustering city representations | 🟢 | 0.8772 | 1.0000 | Clustering city representations |
| `Q_QASP_383` | `1911.01799` | Introduction | 🔴 | 0.1934 | 1.0000 | Experiments on speaker recognition ::: S |
| `Q_QASP_492` | `1910.05456` | Experimental Design ::: Target Lang | 🔴 | 0.1021 | 0.6000 | Experimental Design ::: Source Languages |
| `Q_QASP_493` | `1910.05456` | Experimental Design ::: Target Lang | 🔴 | 0.0000 | 0.0000 | Qualitative Results ::: Miscellaneous Er |
| `Q_QASP_494` | `1910.05456` | Introduction | 🔴 | 0.1301 | 0.5000 | Quantitative Results |
| `Q_QASP_495` | `1910.05456` | Introduction | 🔴 | 0.2372 | 1.0000 | Related Work ::: Acquisition of morpholo |
| `Q_QASP_049` | `1810.04528` | Portuguese Embedding | 🟢 | 0.6589 | 1.0000 | Portuguese Embedding |
| `Q_QASP_050` | `1810.04528` | Portuguese Embedding | 🟢 | 0.8503 | 1.0000 | Portuguese Embedding |
| `Q_QASP_644` | `1910.05608` | Introduction | 🔴 | 0.1815 | 0.6667 | System description ::: Data pre-processi |
| `Q_QASP_645` | `1910.05608` | System description ::: System overv | 🟢 | 0.5681 | 1.0000 | System description ::: System overview |
| `Q_QASP_646` | `1910.05608` | Experiment | 🔴 | 0.3066 | 0.5000 | Abstract |
| `Q_QASP_647` | `1910.05608` | Experiment | 🔴 | 0.3066 | 0.5000 | Abstract |
| `Q_QASP_648` | `1910.05608` | System description ::: System overv | 🔴 | 0.3045 | 1.0000 | System description ::: Data pre-processi |
| `Q_QASP_045` | `1912.02481` | Semantic Representations ::: Experi | 🔴 | 0.1815 | 0.3333 | Abstract |
| `Q_QASP_047` | `1912.02481` | Semantic Representations ::: Experi | 🔴 | 0.0000 | 0.0000 | Semantic Representations ::: Word Embedd |
| `Q_QASP_055` | `2003.07433` | Experimental Evaluation ::: Results | 🔴 | 0.2392 | 0.6667 | Introduction |
| `Q_QASP_056` | `2003.07433` | Twitter-based PTSD Detection ::: PT | 🔴 | 0.3695 | 0.7500 | LAXARY: Explainable PTSD Detection Model |
| `Q_QASP_057` | `2003.07433` | Twitter-based PTSD Detection ::: Pr | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_058` | `2003.07433` | Twitter-based PTSD Detection ::: Da | 🔴 | 0.3950 | 0.6250 | Abstract |
| `Q_QASP_141` | `1703.05260` | Introduction | 🔴 | 0.5438 | 1.0000 | Development of the Schema |
| `Q_QASP_142` | `1703.05260` | First Annotation Phase | 🟢 | 1.0000 | 1.0000 | First Annotation Phase |
| `Q_QASP_522` | `1906.04571` | Introduction | 🟢 | 0.7977 | 1.0000 | Introduction |
| `Q_QASP_523` | `1906.04571` | Extrinsic Evaluation | 🟢 | 0.0000 | 0.0000 | Extrinsic Evaluation |
| `Q_QASP_524` | `1906.04571` | Conclusion | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_529` | `1809.07629` | Setup | 🟢 | 1.0000 | 1.0000 | Setup |
| `Q_QASP_530` | `1809.07629` | Setup | 🔴 | 0.0000 | 0.0000 | Attentional Hierarchical Decoder |
| `Q_QASP_320` | `1910.03814` | Methodology ::: Multimodal Architec | 🔴 | 0.3010 | 1.0000 | Abstract |
| `Q_QASP_322` | `1910.03814` | The MMHS150K dataset | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_323` | `1910.03814` | Results | 🟢 | 0.2891 | 1.0000 | Results |
| `Q_QASP_324` | `1910.03814` | Results | 🔴 | 0.3422 | 0.5000 | Abstract |
| `Q_QASP_325` | `1910.03814` | Results | 🟢 | 1.0000 | 1.0000 | Results |
| `Q_QASP_326` | `1910.03814` | The MMHS150K dataset ::: Tweets Gat | 🟢 | 1.0000 | 1.0000 | The MMHS150K dataset ::: Tweets Gatherin |
| `Q_QASP_327` | `1910.03814` | The MMHS150K dataset | 🔴 | 0.3333 | 1.0000 | Related Work ::: Hate Speech Detection |
| `Q_QASP_328` | `1910.03814` | Methodology ::: Unimodal Treatment  | 🔴 | 0.3780 | 1.0000 | Abstract |
| `Q_QASP_329` | `1910.03814` | Methodology ::: Multimodal Architec | 🔴 | 0.0000 | 1.0000 | Results |
| `Q_QASP_330` | `1910.03814` | The MMHS150K dataset ::: Annotation | 🔴 | 0.0000 | 0.0000 | Related Work ::: Hate Speech Detection |
| `Q_QASP_436` | `1909.00279` | Experiment ::: Interpoetry: Generat | 🔴 | 0.1175 | 0.7500 | Abstract |
| `Q_QASP_437` | `1909.00279` | Experiment ::: Reborn Poems: Genera | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_438` | `1909.00279` | Experiment ::: Datasets | 🔴 | 0.4307 | 1.0000 | Model ::: Addressing Under-Translation a |
| `Q_QASP_665` | `2003.06279` | Conclusion | 🔴 | 0.4575 | 1.0000 | Abstract |
| `Q_QASP_666` | `2003.06279` | Introduction | 🔴 | 0.2346 | 1.0000 | Abstract |
| `Q_QASP_667` | `2003.06279` | Introduction | 🔴 | 0.0000 | 1.0000 | Related works |
| `Q_QASP_668` | `2003.06279` | Introduction | 🔴 | 0.1934 | 0.5000 | Results and Discussion ::: Effects of co |
| `Q_QASP_297` | `1702.06378` | Multitask Learning Results | 🔴 | 0.6241 | 1.0000 | Abstract |
| `Q_QASP_777` | `1806.04535` | Puns | 🟢 | 1.0000 | 1.0000 | Puns |
| `Q_QASP_778` | `1806.04535` | Introduction | 🔴 | 0.4900 | 1.0000 | Dataset |
| `Q_QASP_298` | `1903.03467` | Conclusions | 🟢 | 0.8772 | 1.0000 | Conclusions |
| `Q_QASP_299` | `1903.03467` | Introduction | 🔴 | 0.2021 | 0.3333 | Abstract |
| `Q_QASP_300` | `1903.03467` | Quantitative Results | 🔴 | 0.1681 | 0.7500 | Qualitative Results |
| `Q_QASP_301` | `1903.03467` | Experiments & Results | 🔴 | 0.4413 | 1.0000 | Abstract |
| `Q_QASP_302` | `1903.03467` | Black-Box Knowledge Injection | 🟢 | 0.4693 | 0.6667 | Black-Box Knowledge Injection |
| `Q_QASP_381` | `1909.00088` | Introduction | 🔴 | 0.6309 | 1.0000 | Evaluation ::: Semantic Text Exchange Sc |
| `Q_QASP_382` | `1909.00088` | Introduction | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_066` | `1910.04269` | Related Work | 🔴 | 0.0000 | 0.0000 | Proposed Method ::: Model Details: 1D Co |
| `Q_QASP_067` | `1910.04269` | Related Work | 🟢 | 0.3155 | 1.0000 | Related Work |
| `Q_QASP_226` | `1911.09886` | Experiments ::: Datasets | 🟢 | 0.8066 | 1.0000 | Experiments ::: Datasets |
| `Q_QASP_227` | `1911.09886` | Experiments ::: Experimental Result | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_228` | `1911.09886` | Experiments ::: Baselines and Evalu | 🔴 | 0.1012 | 0.5556 | Abstract |
| `Q_QASP_229` | `1911.09886` | Experiments ::: Experimental Result | 🟢 | 1.0000 | 1.0000 | Experiments ::: Experimental Results |
| `Q_QASP_735` | `1908.10275` | Experiments | 🔴 | 0.0000 | 0.0000 | Motivation, Background and Related Work |
| `Q_QASP_736` | `1908.10275` | Data Description | 🔴 | 0.0000 | 0.0000 | Brief introduction to popular music |
| `Q_QASP_737` | `1908.10275` | Data Description | 🔴 | 0.5000 | 1.0000 | Brief introduction to popular music |
| `Q_QASP_533` | `2002.11402` | Data Preparation | 🟢 | 0.7777 | 1.0000 | Data Preparation |
| `Q_QASP_230` | `1611.01400` | Baseline Systems | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_231` | `1611.01400` | Learning to Rank | 🔴 | 0.0000 | 0.5000 | Introduction |
| `Q_QASP_232` | `1611.01400` | Benchmark Datasets | 🔴 | 0.0000 | 0.0000 | Features |
| `Q_QASP_233` | `1611.01400` | Benchmark Datasets | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_001` | `1608.06757` | Evaluation Set Up | 🟢 | 0.8503 | 1.0000 | Evaluation Set Up |
| `Q_QASP_698` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.3890 | 1.0000 | Introduction |
| `Q_QASP_699` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.1815 | 0.3333 | Results |
| `Q_QASP_700` | `1604.05781` | Dataset, filtering, and corpus sele | 🟢 | 0.4575 | 1.0000 | Dataset, filtering, and corpus selection |
| `Q_QASP_701` | `1604.05781` | Introduction | 🔴 | 0.3869 | 1.0000 | Results |
| `Q_QASP_702` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.0000 | 0.3333 | Abstract |
| `Q_QASP_703` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.1564 | 0.3333 | Results |
| `Q_QASP_428` | `2001.07209` | Emerging NLP research on morality | 🔴 | 0.3562 | 1.0000 | Applications to diachronic morality :::  |
| `Q_QASP_429` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.0000 | 0.5000 | Applications to diachronic morality :::  |
| `Q_QASP_430` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.2346 | 0.6667 | Abstract |
| `Q_QASP_431` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.0000 | 0.5000 | Applications to diachronic morality :::  |
| `Q_QASP_432` | `2001.07209` | A three-tier modelling framework | 🟢 | 0.2641 | 1.0000 | A three-tier modelling framework ::: Mod |
| `Q_QASP_773` | `1905.13413` | Iterative Learning | 🔴 | 0.4632 | 1.0000 | Problem Formulation |
| `Q_QASP_774` | `1905.13413` | Model Architecture and Decoding | 🔴 | 0.6309 | 1.0000 | Evaluation Results |
| `Q_QASP_137` | `1908.08419` | Information Entropy Based Scoring M | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_138` | `1908.08419` | Active Learning for Chinese Word Se | 🔴 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_139` | `1908.08419` | Information Entropy Based Scoring M | 🟢 | 0.8066 | 1.0000 | Information Entropy Based Scoring Model |
| `Q_QASP_387` | `1905.08949` | Wider Input Modalities | 🔴 | 0.2021 | 0.3333 | Generation of Deep Questions |
| `Q_QASP_388` | `1905.08949` | Learning Paradigm | 🔴 | 0.0000 | 0.6667 | Abstract |
| `Q_QASP_389` | `1905.08949` | Input Modality | 🟢 | 0.8175 | 1.0000 | Input Modality |
| `Q_QASP_515` | `1909.00754` | Experimental Setting | 🟢 | 0.6131 | 0.5000 | Experimental Setting |
| `Q_QASP_516` | `1909.00754` | Experimental Setting | 🔴 | 0.0000 | 0.0000 | Implementation Details |
| `Q_QASP_462` | `1710.06536` | Introduction | 🔴 | 0.2641 | 1.0000 | Aspect-Based Sentiment Analysis |
| `Q_QASP_384` | `1812.06705` | Datasets | 🟢 | 0.8503 | 1.0000 | Datasets |
| `Q_QASP_385` | `1812.06705` | Text classification | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_386` | `1812.06705` | Text classification | 🔴 | 0.4307 | 1.0000 | Connection to Style Transfer |
| `Q_QASP_650` | `1605.04655` | Sentence Embeddings | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_651` | `1605.04655` | Evaluation | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_653` | `1605.04655` | Introduction | 🔴 | 0.3273 | 0.4118 | Conclusion |
| `Q_QASP_683` | `1904.07342` | Data | 🟢 | 1.0000 | 1.0000 | Data |
| `Q_QASP_684` | `1904.07342` | Results & Discussion | 🔴 | 0.0000 | 0.0000 | Data |
| `Q_QASP_685` | `1904.07342` | Labeling Methodology | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_686` | `1904.07342` | Data | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_687` | `1904.07342` | Data | 🟢 | 0.3066 | 1.0000 | Data |
| `Q_QASP_792` | `1907.02636` | Results | 🟢 | 1.0000 | 1.0000 | Results |
| `Q_QASP_793` | `1907.02636` | Contextual Features | 🔴 | 0.3155 | 1.0000 | Datasets |
| `Q_QASP_794` | `1907.02636` | Datasets | 🟢 | 1.0000 | 1.0000 | Datasets |
| `Q_QASP_122` | `1909.09491` | Plackett-Luce Model in Statistical  | 🔴 | 0.4162 | 0.6667 | Abstract |
| `Q_QASP_124` | `1909.09491` | Introduction | 🔴 | 0.2752 | 1.0000 | Abstract |
| `Q_QASP_618` | `1902.09087` | Introduction | 🟢 | 0.5617 | 0.3636 | Introduction |
| `Q_QASP_619` | `1902.09087` | Evaluation Metrics | 🟢 | 1.0000 | 1.0000 | Evaluation Metrics |
| `Q_QASP_620` | `1902.09087` | Introduction | 🔴 | 0.4852 | 0.4000 | Results |
| `Q_QASP_623` | `1907.01413` | Future Work | 🔴 | 0.2372 | 1.0000 | Results and Discussion |
| `Q_QASP_624` | `1907.01413` | Ultrasound Data | 🟢 | 0.6131 | 1.0000 | Ultrasound Data |
| `Q_QASP_625` | `1907.01413` | Preprocessing and Model Architectur | 🔴 | 0.2372 | 0.5000 | Abstract |
| `Q_QASP_626` | `1907.01413` | Data Selection | 🔴 | 0.0000 | 1.0000 | Ultrasound Data |
| `Q_QASP_627` | `1907.01413` | Preprocessing and Model Architectur | 🟢 | 0.8316 | 1.0000 | Preprocessing and Model Architectures |
| `Q_QASP_628` | `1907.01413` | Ultrasound Data | 🟢 | 0.6131 | 0.5000 | Ultrasound Data |
| `Q_QASP_312` | `1909.00430` | Expectation Regularization (XR) | 🔴 | 0.6053 | 1.0000 | Introduction |
| `Q_QASP_174` | `1912.01252` | Introduction ::: Objective | 🔴 | 0.2184 | 0.5000 | Conclusion |
| `Q_QASP_177` | `1912.01252` | Mining opinions and beliefs from te | 🟢 | 0.3869 | 1.0000 | Mining opinions and beliefs from texts : |
| `Q_QASP_573` | `1606.05320` | Methods | 🔴 | 0.3985 | 1.0000 | Experiments |
| `Q_QASP_574` | `1606.05320` | Experiments | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_575` | `1606.05320` | Introduction | 🔴 | 0.1175 | 1.0000 | Abstract |
| `Q_QASP_459` | `1907.00758` | Data | 🔴 | 0.6309 | 1.0000 | Dividing samples for training, validatio |
| `Q_QASP_460` | `1907.00758` | Model | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_461` | `1907.00758` | Model | 🔴 | 0.6053 | 1.0000 | Introduction |
| `Q_QASP_292` | `1910.11769` | Introduction | 🔴 | 0.0000 | 1.0000 | Benchmarks ::: Fine-tuned BERT |
| `Q_QASP_293` | `1910.11769` | Dataset ::: Plutchik’s Wheel of Emo | 🔴 | 0.4306 | 1.0000 | Dataset ::: Mechanical Turk (MTurk) |
| `Q_QASP_294` | `1910.11769` | Benchmarks ::: Bag-of-Words-based B | 🔴 | 1.0000 | 1.0000 | Abstract |
| `Q_QASP_295` | `1910.11769` | Dataset ::: Dataset Statistics | 🟢 | 1.0000 | 1.0000 | Dataset ::: Dataset Statistics |
| `Q_QASP_296` | `1910.11769` | Dataset ::: Mechanical Turk (MTurk) | 🟢 | 1.0000 | 1.0000 | Dataset ::: Mechanical Turk (MTurk) |
| `Q_QASP_599` | `1911.11744` | Results | 🔴 | 0.5110 | 1.0000 | Abstract |
| `Q_QASP_600` | `1911.11744` | Results | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_601` | `1911.11744` | Results | 🔴 | 0.0000 | 0.3333 | Background |
| `Q_QASP_545` | `2004.03034` | Results and Analysis | 🟢 | 0.5706 | 1.0000 | Results and Analysis |
| `Q_QASP_546` | `2004.03034` | Methodology ::: Baseline Models ::: | 🔴 | 0.4825 | 1.0000 | Abstract |
| `Q_QASP_547` | `2004.03034` | Dataset | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_548` | `2004.03034` | Dataset | 🔴 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_307` | `1909.13375` | Related Work | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_308` | `1909.13375` | Model ::: Multi-Span Head | 🟢 | 0.6131 | 1.0000 | Model ::: Multi-Span Head |
| `Q_QASP_309` | `1909.13375` | Results and Discussion ::: Performa | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_310` | `1909.13375` | Related Work | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_074` | `1712.09127` | weGAN: Training cross-corpus word e | 🟢 | 0.0000 | 0.5000 | weGAN: Training cross-corpus word embedd |
| `Q_QASP_075` | `1712.09127` | The CNN data set | 🔴 | 0.0000 | 0.0000 | deGAN: Generating document embeddings fo |
| `Q_QASP_076` | `1712.09127` | Experiments | 🟢 | 1.0000 | 1.0000 | Experiments |
| `Q_QASP_483` | `1809.05752` | Future Work and Conclusion | 🟢 | 1.0000 | 1.0000 | Future Work and Conclusion |
| `Q_QASP_484` | `1809.05752` | Data | 🔴 | 0.3836 | 0.6667 | Related Work |
| `Q_QASP_730` | `1602.08741` | Acquiring data | 🔴 | 0.2154 | 0.4118 | Determining optimal corpus size |
| `Q_QASP_760` | `1910.10408` | Introduction | 🔴 | 0.2044 | 0.5000 | Results ::: Human Evaluation and Analysi |
| `Q_QASP_761` | `1910.10408` | Experiments ::: Data and Settings | 🔴 | 0.6934 | 1.0000 | Results |
| `Q_QASP_762` | `1910.10408` | Introduction | 🔴 | 0.5357 | 0.6000 | Background ::: Transformer |
| `Q_QASP_763` | `1910.10408` | Introduction | 🔴 | 0.1518 | 0.2308 | Abstract |
| `Q_QASP_764` | `1910.10408` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_765` | `1910.10408` | Experiments ::: Data and Settings | 🔴 | 0.4228 | 1.0000 | Related works |
| `Q_QASP_766` | `1910.10408` | Introduction | 🔴 | 0.8253 | 0.8889 | Methods ::: Combining the two methods |
| `Q_QASP_427` | `1902.00672` | Detection of hypergraph transversal | 🔴 | 0.0000 | 0.0000 | Comparison with DUC systems |
| `Q_QASP_248` | `1910.04601` | Baseline RC-QED@!START@$^{\rm E}$@! | 🔴 | 0.4228 | 1.0000 | Introduction |
| `Q_QASP_249` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_250` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.3333 | 1.0000 | Data collection for RC-QED@!START@$^{\rm |
| `Q_QASP_251` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.0000 | 0.0000 | Related work ::: RC datasets with explan |
| `Q_QASP_395` | `1603.01417` | Input Module for Text QA | 🔴 | 0.3010 | 1.0000 | Conclusion |
| `Q_QASP_396` | `1603.01417` | Introduction | 🔴 | 0.0000 | 1.0000 | Comparison to state of the art using bAb |
| `Q_QASP_397` | `1603.01417` | Input Module for Text QA | 🔴 | 0.0000 | 0.5000 | Related Work |
| `Q_QASP_398` | `1603.01417` | Introduction | 🔴 | 0.0000 | 1.0000 | Improved Dynamic Memory Networks: DMN+ |
| `Q_QASP_399` | `1603.01417` | Conclusion | 🔴 | 0.3010 | 1.0000 | Introduction |
| `Q_QASP_400` | `1603.01417` | Conclusion | 🔴 | 0.0000 | 1.0000 | Comparison to state of the art using VQA |
| `Q_QASP_800` | `1908.11425` | Methods ::: Speech-to-text translat | 🔴 | 0.6131 | 1.0000 | Experimental Setup ::: Fine-grained topi |
| `Q_QASP_801` | `1908.11425` | Experimental Setup ::: Data. | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_167` | `1909.02764` | Results ::: Facial Expressions and  | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_168` | `1909.02764` | Methods ::: Emotion Recognition fro | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1909.02764` | Methods ::: Emotion Recognition fro | 🔴 | 0.1413 | 0.6667 | Abstract |
| `Q_QASP_463` | `1701.02877` | Datasets | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_496` | `1910.05154` | Experiments | 🟢 | 0.6131 | 1.0000 | Experiments |
| `Q_QASP_497` | `1910.05154` | Experiments | 🟢 | 0.9197 | 1.0000 | Experiments |
| `Q_QASP_498` | `1910.05154` | Experiments | 🟢 | 0.5856 | 1.0000 | Experiments |
| `Q_QASP_499` | `1910.05154` | Methodology ::: Bilingual Unsupervi | 🔴 | 0.5875 | 1.0000 | Conclusion |
| `Q_QASP_500` | `1910.05154` | Conclusion | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_201` | `1703.04617` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_202` | `1703.04617` | Results | 🔴 | 0.2184 | 1.0000 | Conclusions |
| `Q_QASP_203` | `1703.04617` | The Baseline Model | 🟢 | 0.5000 | 1.0000 | The Baseline Model |
| `Q_QASP_204` | `1703.04617` | Results | 🔴 | 0.5000 | 1.0000 | Set-Up |
| `Q_QASP_549` | `1910.12618` | Presentation of the data ::: Text | 🔴 | 0.0000 | 0.0000 | Modeling and forecasting framework ::: H |
| `Q_QASP_550` | `1910.12618` | Experiments ::: Interpretability of | 🟢 | 0.1772 | 0.5000 | Experiments ::: Interpretability of the  |
| `Q_QASP_551` | `1910.12618` | Experiments ::: Interpretability of | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_552` | `1910.12618` | Introduction | 🔴 | 0.1564 | 0.3333 | Modeling and forecasting framework ::: N |
| `Q_QASP_390` | `1909.00170` | Introduction | 🔴 | 0.0000 | 1.0000 | Model |
| `Q_QASP_391` | `1909.00170` | Off-the-shelf NE Recognition System | 🟢 | 0.6131 | 0.5000 | Off-the-shelf NE Recognition Systems |
| `Q_QASP_474` | `1910.04887` | Methods ::: Data and Training Detai | 🔴 | 0.6934 | 1.0000 | Abstract |
| `Q_QASP_475` | `1910.04887` | Methods ::: Modifying FactorCell LS | 🔴 | 0.3010 | 1.0000 | Abstract |
| `Q_QASP_606` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.6309 | 1.0000 | Dataset |
| `Q_QASP_607` | `1911.00523` | Predicting Pointers ::: Experiment  | 🔴 | 0.2961 | 0.3333 | Predicting Pointers ::: Prediction Perfo |
| `Q_QASP_608` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.1786 | 0.5000 | Predicting Pointers |
| `Q_QASP_609` | `1911.00523` | Predicting Pointers ::: Experiment  | 🔴 | 0.8316 | 1.0000 | Predicting Pointers ::: Prediction Perfo |
| `Q_QASP_610` | `1911.00523` | Predicting Pointers ::: Experiment  | 🟢 | 1.0000 | 1.0000 | Predicting Pointers ::: Experiment setup |
| `Q_QASP_611` | `1911.00523` | Concluding Discussions | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_612` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.1786 | 0.5000 | Predicting Pointers |
| `Q_QASP_535` | `2002.00652` | Experiment & Analysis ::: Experimen | 🔴 | 0.2372 | 0.5000 | Abstract |
| `Q_QASP_536` | `2002.00652` | Introduction | 🔴 | 0.7328 | 1.0000 | Experiment & Analysis ::: Experimental S |
| `Q_QASP_537` | `2002.00652` | Experiment & Analysis ::: Model Com | 🔴 | 0.4575 | 1.0000 | Abstract |
| `Q_QASP_538` | `2002.00652` | Introduction | 🔴 | 0.9060 | 1.0000 | Abstract |
| `Q_QASP_371` | `1706.08032` | Experimental results | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_372` | `1706.08032` | Data Preparation | 🔴 | 0.0000 | 0.0000 | Preprocessing |
| `Q_QASP_373` | `1706.08032` | Data Preparation | 🔴 | 0.6508 | 0.6667 | Experimental results |
| `Q_QASP_374` | `1706.08032` | Data Preparation | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_375` | `1706.08032` | Semantic Rules (SR) | 🟢 | 0.9134 | 1.0000 | Semantic Rules (SR) |
| `Q_QASP_602` | `1910.03467` | Experiments ::: Results ::: Japanes | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_603` | `1910.03467` | Experiments ::: Results ::: Japanes | 🔴 | 0.0000 | 1.0000 | Rare Word translation ::: Reducing Unkno |
| `Q_QASP_569` | `1901.04899` | Methodology | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_570` | `1901.04899` | Methodology | 🟢 | 0.4307 | 1.0000 | Methodology |
| `Q_QASP_571` | `1901.04899` | Experimental Results | 🔴 | 0.3010 | 1.0000 | Methodology |
| `Q_QASP_572` | `1901.04899` | Methodology | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_125` | `2001.05284` | Baseline, Oracle and Direct Models  | 🔴 | 0.4144 | 1.0000 | Introduction |
| `Q_QASP_126` | `2001.05284` | Baseline, Oracle and Direct Models  | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_127` | `2001.05284` | Experiment ::: Dataset | 🔴 | 0.0000 | 1.0000 | Baseline, Oracle and Direct Models ::: B |
| `Q_QASP_519` | `1906.00180` | Unseen lengths | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_690` | `1911.00547` | Data Collection and Annotation | 🔴 | 0.5000 | 1.0000 | Experiments and Results ::: Experimental |
| `Q_QASP_691` | `1911.00547` | Introduction | 🔴 | 0.3869 | 0.5000 | Experiments and Results ::: Experimental |
| `Q_QASP_692` | `1911.00547` | Patterns of Sexual Harassment | 🔴 | 0.1021 | 1.0000 | Conclusions |
| `Q_QASP_313` | `1910.11493` | Baselines ::: Task 2 Baselines :::  | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_722` | `1908.04917` | Compared Methods and Evaluation Pro | 🔴 | 0.0000 | 0.5000 | Attention Visualisation |
| `Q_QASP_723` | `1908.04917` | Introduction | 🔴 | 0.2641 | 0.5000 | Abstract |
| `Q_QASP_724` | `1908.04917` | Tone Prediction Sub-network | 🔴 | 0.1920 | 0.5000 | Abstract |
| `Q_QASP_238` | `1807.03367` | Data Collection | 🔴 | 0.1564 | 0.3333 | The Tourist |
| `Q_QASP_239` | `1807.03367` | Data Collection | 🔴 | 0.3155 | 1.0000 | Dataset Statistics |
| `Q_QASP_240` | `1807.03367` | Introduction | 🔴 | 0.4288 | 0.1739 | Experiments |
| `Q_QASP_241` | `1807.03367` | Results and Discussion | 🔴 | 0.0000 | 0.0000 | Evaluation on Full Setup |
| `Q_QASP_242` | `1807.03367` | Introduction | 🔴 | 0.0000 | 0.0000 | Data Collection |
| `Q_QASP_486` | `2001.01589` | Approach ::: Morphologically Motiva | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_487` | `2001.01589` | Approach | 🔴 | 0.0000 | 0.5000 | Related Work |

### `dense` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_QASP_010` | `1801.05147` | Data Sets | 🟢 | 0.0000 | 0.0000 | Data Sets |
| `Q_QASP_020` | `1909.00512` | Approach ::: Measures of Contextual | 🔴 | 0.1740 | 0.6250 | Abstract |
| `Q_QASP_021` | `1909.00512` | Introduction | 🔴 | 0.0000 | 0.0000 | Approach ::: Measures of Contextuality : |
| `Q_QASP_022` | `2003.03106` | Results ::: Experiment A: NUBes-PHI | 🔴 | 0.0000 | 1.0000 | Materials and Methods ::: Systems |
| `Q_QASP_023` | `2003.03106` | Materials and Methods ::: Systems : | 🔴 | 0.1681 | 0.2500 | Materials and Methods |
| `Q_QASP_025` | `2003.03106` | Materials and Methods ::: Data | 🟢 | 0.5842 | 0.6667 | Materials and Methods ::: Data |
| `Q_QASP_038` | `1605.06083` | Introduction | 🟢 | 0.8066 | 1.0000 | Introduction |
| `Q_QASP_039` | `1605.06083` | Other methods | 🔴 | 0.1175 | 0.5000 | Abstract |
| `Q_QASP_040` | `1605.06083` | Introduction | 🔴 | 0.1131 | 0.6000 | Abstract |
| `Q_QASP_041` | `1804.05918` | Experimental Results | 🔴 | 0.2140 | 0.4000 | Introduction |
| `Q_QASP_042` | `1804.05918` | Experimental Results | 🔴 | 0.1357 | 1.0000 | Abstract |
| `Q_QASP_044` | `1901.05287` | Results | 🔴 | 0.4256 | 1.0000 | Introduction |
| `Q_QASP_045` | `1612.06685` | Psycholinguistic and Semantic Maps | 🔴 | 0.3155 | 1.0000 | Maps from Blogs |
| `Q_QASP_046` | `1612.06685` | Data Collection | 🔴 | 0.4865 | 1.0000 | Abstract |
| `Q_QASP_051` | `1910.10781` | Introduction | 🔴 | 0.3991 | 0.6667 | Related work |
| `Q_QASP_052` | `1910.10781` | Introduction | 🟢 | 0.3120 | 1.0000 | Introduction |
| `Q_QASP_055` | `1911.06964` | Experiments | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_056` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.0000 | 1.0000 | Approach |
| `Q_QASP_057` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_058` | `1911.06964` | Experiments ::: Efficiency-accuracy | 🔴 | 0.6309 | 1.0000 | Approach ::: Modeling with autoencoders. |
| `Q_QASP_059` | `2001.02284` | Model ::: Dialogue Modules | 🔴 | 0.0000 | 0.2500 | Related Work |
| `Q_QASP_060` | `2001.02284` | Re-implementation of units with BER | 🔴 | 0.0000 | 0.2000 | Introduction ::: Outline and Contributio |
| `Q_QASP_061` | `2001.02284` | Target Domain & Task Definition | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_071` | `1809.00540` | Related Work | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_072` | `1809.00540` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_073` | `2004.03354` | Experiment 1: Biomedical NER ::: Do | 🔴 | 0.2346 | 0.3333 | Abstract |
| `Q_QASP_075` | `1611.04798` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_076` | `1611.04798` | Under-resourced Translation | 🟢 | 0.9197 | 1.0000 | Under-resourced Translation |
| `Q_QASP_088` | `1809.09194` | Model | 🟢 | 0.8503 | 1.0000 | Model |
| `Q_QASP_089` | `1809.09194` | Results | 🔴 | 0.0000 | 1.0000 | Background |
| `Q_QASP_090` | `1809.09194` | Model | 🟢 | 0.6131 | 1.0000 | Model |
| `Q_QASP_091` | `1604.05372` | Learning to Translate: Ukrainian-to | 🟢 | 0.0000 | 0.5000 | Learning to Translate: Ukrainian-to-Russ |
| `Q_QASP_092` | `2002.08795` | Introduction | 🔴 | 0.3956 | 1.0000 | Abstract |
| `Q_QASP_093` | `2002.08795` | Introduction and Background | 🔴 | 0.8208 | 1.0000 | Abstract |
| `Q_QASP_094` | `2002.08795` | Introduction and Background | 🔴 | 0.4181 | 0.8571 | Abstract |
| `Q_QASP_096` | `1802.06024` | Experiments | 🔴 | 0.4483 | 0.5714 | Results and Analysis |
| `Q_QASP_097` | `1802.06024` | Experiments | 🟢 | 0.2769 | 0.6667 | Experiments |
| `Q_QASP_098` | `1802.06024` | Introduction | 🔴 | 0.6053 | 1.0000 | Abstract |
| `Q_QASP_099` | `1802.06024` | Experiments | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_100` | `1802.06024` | Introduction | 🔴 | 0.1596 | 0.7500 | Abstract |
| `Q_QASP_105` | `1710.07960` | Discussion | 🔴 | 0.0000 | 0.5000 | Related work |
| `Q_QASP_106` | `1710.07960` | Introduction | 🔴 | 0.4292 | 0.8571 | Discussion |
| `Q_QASP_107` | `1912.03804` | Related Work | 🔴 | 0.4982 | 1.0000 | Results |
| `Q_QASP_108` | `1912.03804` | Conclusion and Future Work | 🔴 | 0.2001 | 0.6000 | Abstract |
| `Q_QASP_109` | `1912.03804` | Method ::: Emotion detection | 🟢 | 0.8175 | 1.0000 | Method ::: Emotion detection |
| `Q_QASP_110` | `1912.03804` | Introduction | 🔴 | 0.8268 | 0.5000 | Abstract |
| `Q_QASP_111` | `1912.03804` | Method ::: Content Analysis | 🔴 | 0.2591 | 1.0000 | Abstract |
| `Q_QASP_112` | `1912.08960` | Introduction | 🔴 | 0.1681 | 1.0000 | GTD Evaluation Framework |
| `Q_QASP_113` | `1912.08960` | Experimental Setup ::: Datasets | 🔴 | 0.1672 | 0.6667 | Results |
| `Q_QASP_114` | `1912.08960` | Experimental Setup ::: Models | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_115` | `1912.08960` | GTD Evaluation Framework ::: Divers | 🔴 | 0.6053 | 1.0000 | Experimental Setup ::: Datasets |
| `Q_QASP_128` | `2004.01853` | Introduction | 🔴 | 0.5000 | 1.0000 | Experimental Setup ::: Datasets ::: GIGA |
| `Q_QASP_129` | `2004.01853` | Results ::: Automatic Evaluation | 🟢 | 0.9197 | 1.0000 | Results ::: Automatic Evaluation |
| `Q_QASP_130` | `1710.03348` | Introduction | 🔴 | 0.2339 | 0.8000 | Abstract |
| `Q_QASP_131` | `1710.03348` | Impact of Attention Mechanism | 🔴 | 0.3869 | 0.5000 | Attention Concentration |
| `Q_QASP_132` | `1710.03348` | Alignment Quality Impact on Transla | 🔴 | 0.2184 | 1.0000 | Abstract |
| `Q_QASP_138` | `1809.01202` | Experiment | 🔴 | 0.0000 | 0.0000 | Exploration |
| `Q_QASP_139` | `1809.01202` | Dataset | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_140` | `1909.02027` | Dataset ::: In-Scope Data Collectio | 🔴 | 0.0000 | 1.0000 | Dataset |
| `Q_QASP_141` | `1909.02027` | Introduction | 🔴 | 0.4693 | 1.0000 | Benchmark Evaluation |
| `Q_QASP_142` | `1909.02027` | Introduction | 🔴 | 0.6131 | 1.0000 | Dataset |
| `Q_QASP_143` | `1909.02027` | Dataset | 🔴 | 0.3296 | 0.6667 | Benchmark Evaluation ::: Out-of-Scope Pr |
| `Q_QASP_151` | `1611.01576` | Character-level Neural Machine Tran | 🟢 | 1.0000 | 1.0000 | Character-level Neural Machine Translati |
| `Q_QASP_152` | `1611.01576` | Sentiment Classification | 🟢 | 1.0000 | 1.0000 | Sentiment Classification |
| `Q_QASP_153` | `1611.01576` | Model | 🔴 | 0.3066 | 1.0000 | Variants |
| `Q_QASP_161` | `1909.08089` | Results and Analysis | 🔴 | 0.5641 | 1.0000 | Introduction |
| `Q_QASP_162` | `1909.08089` | Introduction | 🔴 | 0.1934 | 1.0000 | Decoder |
| `Q_QASP_164` | `1910.09982` | Data | 🔴 | 0.0000 | 0.5000 | Participants and Approaches ::: Teams Pa |
| `Q_QASP_165` | `1910.09982` | Baselines | 🟢 | 1.0000 | 1.0000 | Baselines |
| `Q_QASP_166` | `1609.00559` | Introduction | 🔴 | 0.6309 | 1.0000 | Method |
| `Q_QASP_167` | `1609.00559` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_168` | `1609.00559` | Comparison with Previous Work | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 1.0000 | Decoding the KB Query |
| `Q_QASP_170` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 0.0000 | Attention Mechanisms |
| `Q_QASP_173` | `1608.01084` | Data Set and Toolkits | 🔴 | 0.0000 | 0.0000 | Our Approach |
| `Q_QASP_174` | `1904.10503` | Introduction | 🔴 | 1.0000 | 1.0000 | Conclusion and Future Work |
| `Q_QASP_175` | `1904.10503` | Results | 🟢 | 0.9197 | 1.0000 | Results |
| `Q_QASP_176` | `1904.10503` | Entity Linking using Wikidata | 🔴 | 0.2140 | 0.8000 | Abstract |
| `Q_QASP_177` | `1912.01772` | Introduction | 🔴 | 0.5492 | 0.7778 | Abstract |
| `Q_QASP_178` | `1912.01772` | The Resource ::: Additional Annotat | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_179` | `1603.01987` | The medical domain model | 🔴 | 0.0000 | 1.0000 | Classification results |
| `Q_QASP_184` | `1702.03856` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_185` | `1702.03856` | Introduction | 🔴 | 0.6332 | 1.0000 | Analysis of challenges from UTD |
| `Q_QASP_186` | `1702.03856` | Dataset | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_189` | `1606.03676` | Corpora | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_190` | `1606.03676` | Corpora | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_193` | `1911.03343` | Introduction | 🔴 | 0.4685 | 1.0000 | Abstract |
| `Q_QASP_209` | `1909.07575` | Experiments ::: Baseline Models and | 🔴 | 0.5508 | 1.0000 | Abstract |
| `Q_QASP_210` | `1909.07575` | Our method ::: Training Procedure : | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_212` | `1904.07904` | Spoken Question Answering | 🟢 | 1.0000 | 1.0000 | Spoken Question Answering |
| `Q_QASP_213` | `1904.07904` | Results | 🔴 | 0.6509 | 1.0000 | Conclusion |
| `Q_QASP_214` | `1904.07904` | Results | 🔴 | 0.4367 | 1.0000 | Conclusion |
| `Q_QASP_215` | `1904.07904` | Corpus | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_216` | `2003.11645` | Introduction | 🔴 | 1.0000 | 1.0000 | Methodology |
| `Q_QASP_217` | `2003.11645` | Introduction | 🔴 | 0.6053 | 1.0000 | Abstract |
| `Q_QASP_218` | `2003.11645` | Introduction | 🟢 | 0.8175 | 1.0000 | Introduction |
| `Q_QASP_219` | `2003.11645` | Introduction | 🔴 | 0.0000 | 1.0000 | Literature Review |
| `Q_QASP_222` | `1604.03114` | Modeling Idea Flow | 🔴 | 0.2901 | 0.7500 | Abstract |
| `Q_QASP_223` | `1604.03114` | Debate Dataset: Intelligence Square | 🟢 | 1.0000 | 1.0000 | Debate Dataset: Intelligence Squared |
| `Q_QASP_227` | `1606.02891` | Baseline System | 🔴 | 0.4685 | 1.0000 | Abstract |
| `Q_QASP_228` | `1803.09123` | Empirical Study | 🔴 | 0.1232 | 0.7500 | Equation Embeddings Models |
| `Q_QASP_229` | `1803.09123` | Discovering Semantically Similar Eq | 🟢 | 0.7598 | 1.0000 | Discovering Semantically Similar Equatio |
| `Q_QASP_237` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.6367 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_238` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.6548 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_239` | `1709.07814` | Speech Data | 🔴 | 0.1391 | 0.2500 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_249` | `2003.08380` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_251` | `1805.04508` | Gender Bias Results | 🔴 | 0.3378 | 1.0000 | Abstract |
| `Q_QASP_252` | `1805.04508` | The Equity Evaluation Corpus | 🔴 | 0.4132 | 0.7500 | Introduction |
| `Q_QASP_258` | `1910.05603` | System Description ::: Language Mod | 🟢 | 0.7929 | 1.0000 | System Description ::: Language Model |
| `Q_QASP_259` | `1910.05603` | Experiments ::: System combination | 🔴 | 0.4307 | 1.0000 | Conclusion |
| `Q_QASP_260` | `1910.05603` | System Description ::: Acoustic Mod | 🔴 | 0.3562 | 1.0000 | Experiments ::: Single system evaluation |
| `Q_QASP_261` | `1909.03405` | Results of NLI Tasks ::: GLUE | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_262` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Results of NLI Tasks ::: GLUE |
| `Q_QASP_263` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_134` | `1909.08859` | Procedural Reasoning Networks | 🔴 | 0.2346 | 1.0000 | Abstract |
| `Q_QASP_135` | `1909.08859` | Experiments ::: Baselines | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_136` | `1909.08859` | Experiments ::: Results | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_541` | `1905.06566` | Introduction | 🔴 | 0.8539 | 0.8000 | Results |
| `Q_QASP_116` | `1708.05873` | Introduction | 🔴 | 0.4776 | 1.0000 | Abstract |
| `Q_QASP_117` | `1708.05873` | Introduction | 🔴 | 0.2891 | 1.0000 | Conclusion |
| `Q_QASP_118` | `1708.05873` | Estimation of topic models | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_303` | `1807.00868` | Using different features | 🟢 | 1.0000 | 1.0000 | Using different features |
| `Q_QASP_304` | `1807.00868` | Basic setup | 🔴 | 0.5000 | 1.0000 | Related work |
| `Q_QASP_305` | `1807.00868` | Training the best model | 🟢 | 1.0000 | 1.0000 | Training the best model |
| `Q_QASP_505` | `2003.03612` | Introduction | 🔴 | 0.3973 | 1.0000 | Discussion |
| `Q_QASP_506` | `2003.03612` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_507` | `2003.03612` | Introduction | 🔴 | 0.0000 | 0.0000 | Multinomials |
| `Q_QASP_508` | `2003.03612` | Introduction | 🔴 | 0.2372 | 1.0000 | Abstract |
| `Q_QASP_509` | `2003.03612` | Models And Predictions ::: Predicti | 🔴 | 0.4307 | 1.0000 | Introduction ::: Related Work |
| `Q_QASP_510` | `2003.03612` | Models And Predictions ::: Predicti | 🔴 | 0.5000 | 1.0000 | Introduction ::: Related Work |
| `Q_QASP_511` | `2003.03612` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_163` | `1810.06743` | Results | 🟢 | 0.4693 | 0.3333 | Results |
| `Q_QASP_164` | `1810.06743` | Conclusion and Future Work | 🔴 | 0.0000 | 0.0000 | Similarities in the annotation |
| `Q_QASP_165` | `1810.06743` | Introduction | 🔴 | 0.0000 | 0.0000 | UD treebanks and UniMorph tables |
| `Q_QASP_166` | `1810.06743` | Introduction | 🔴 | 0.3464 | 0.6000 | Abstract |
| `Q_QASP_284` | `1603.07044` | Introduction | 🔴 | 0.4367 | 1.0000 | Multitask Learning |
| `Q_QASP_286` | `1603.07044` | Conclusion | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_476` | `1810.00663` | Introduction | 🔴 | 0.4693 | 0.6667 | Dataset |
| `Q_QASP_477` | `1810.00663` | Quantitative Evaluation | 🔴 | 0.2961 | 1.0000 | Models Used in the Evaluation |
| `Q_QASP_478` | `1810.00663` | Models Used in the Evaluation | 🔴 | 0.5000 | 1.0000 | Quantitative Evaluation |
| `Q_QASP_479` | `1810.00663` | Evaluation Metrics | 🟢 | 0.8127 | 1.0000 | Evaluation Metrics |
| `Q_QASP_480` | `1810.00663` | Introduction | 🔴 | 0.0000 | 1.0000 | Acknowledgments |
| `Q_QASP_481` | `1810.00663` | Introduction | 🔴 | 0.8319 | 0.7500 | Dataset |
| `Q_QASP_482` | `1810.00663` | Dataset | 🔴 | 0.1846 | 1.0000 | Related work |
| `Q_QASP_193` | `2004.03685` | Towards Better Faithfulness Criteri | 🟢 | 0.6131 | 0.5000 | Towards Better Faithfulness Criteria |
| `Q_QASP_194` | `2004.03685` | Towards Better Faithfulness Criteri | 🔴 | 0.2641 | 1.0000 | Faithfulness vs. Plausibility |
| `Q_QASP_195` | `2004.03685` | Introduction | 🔴 | 0.1589 | 0.7778 | Abstract |
| `Q_QASP_196` | `2004.03685` | Introduction | 🔴 | 0.7910 | 0.9000 | Guidelines for Evaluating Faithfulness |
| `Q_QASP_658` | `1805.00760` | Model Description | 🔴 | 0.3816 | 1.0000 | Attention Visualization and Case Study |
| `Q_QASP_659` | `1805.00760` | Introduction | 🟢 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_660` | `1805.00760` | Datasets | 🔴 | 0.0000 | 1.0000 | Settings |
| `Q_QASP_661` | `1805.00760` | Main Results | 🔴 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_587` | `1911.03243` | Dataset Quality Analysis ::: Agreem | 🔴 | 0.2044 | 1.0000 | Abstract |
| `Q_QASP_588` | `1911.03243` | Background — QA-SRL ::: Corpora | 🔴 | 0.3010 | 1.0000 | Dataset Quality Analysis ::: Agreement w |
| `Q_QASP_589` | `1911.03243` | Introduction | 🔴 | 0.9671 | 1.0000 | Dataset Quality Analysis ::: Agreement w |
| `Q_QASP_590` | `1911.03243` | Introduction | 🔴 | 0.3978 | 1.0000 | Background — QA-SRL ::: Corpora |
| `Q_QASP_591` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_592` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_593` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.0000 | 0.0000 | Dataset Quality Analysis ::: Dataset Ass |
| `Q_QASP_594` | `1911.03243` | Dataset Quality Analysis ::: Agreem | 🔴 | 0.3869 | 1.0000 | Dataset Quality Analysis ::: Dataset Ass |
| `Q_QASP_669` | `2004.03744` | SNLI-VE-2.0 ::: Re-annotation detai | 🔴 | 0.0000 | 0.0000 | Visual-Textual Entailment with Natural L |
| `Q_QASP_670` | `2004.03744` | Appendix ::: Details of the Mechani | 🔴 | 0.0000 | 0.0000 | Visual-Textual Entailment with Natural L |
| `Q_QASP_671` | `2004.03744` | Appendix ::: Statistics of e-SNLI-V | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_672` | `2004.03744` | SNLI-VE-2.0 ::: Re-evaluation of Vi | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_673` | `2004.03744` | Introduction | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_342` | `1911.11750` | Background ::: Document Representat | 🔴 | 0.3010 | 1.0000 | The Spearman's Rank Correlation Coeffici |
| `Q_QASP_343` | `1911.11750` | Experiments | 🔴 | 0.6309 | 1.0000 | The Spearman's Rank Correlation Coeffici |
| `Q_QASP_344` | `1911.11750` | The Spearman's Rank Correlation Coe | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_783` | `1710.07395` | Experimental Results | 🔴 | 0.0000 | 1.0000 | Annotation Procedure |
| `Q_QASP_784` | `1710.07395` | Logistic Regression Models | 🔴 | 0.4416 | 1.0000 | Abstract |
| `Q_QASP_785` | `1710.07395` | Logistic Regression Models | 🔴 | 0.0000 | 1.0000 | Annotation Procedure |
| `Q_QASP_786` | `1710.07395` | Annotation Guidelines | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_787` | `1710.07395` | Neural Network Models | 🔴 | 0.6309 | 1.0000 | Experimental Results |
| `Q_QASP_253` | `1912.05066` | Introduction | 🔴 | 0.2184 | 0.5000 | Methodology ::: Machine Learning Models |
| `Q_QASP_255` | `1912.05066` | Introduction | 🔴 | 0.4763 | 1.0000 | Data Analysis |
| `Q_QASP_256` | `1912.05066` | Introduction | 🔴 | 0.0000 | 0.5000 | Conclusions |
| `Q_QASP_257` | `1912.05066` | Methodology ::: Procedure | 🔴 | 0.3036 | 0.6667 | Data Analysis |
| `Q_QASP_059` | `2003.12218` | Results ::: NER Annotation Results | 🔴 | 0.0000 | 1.0000 | Conclusion |
| `Q_QASP_060` | `2003.12218` | Introduction | 🔴 | 0.3434 | 1.0000 | Conclusion |
| `Q_QASP_316` | `1908.10449` | Introduction | 🔴 | 0.3010 | 1.0000 | Experimental Results ::: Mastering Train |
| `Q_QASP_317` | `1908.10449` | iMRC: Making MRC Interactive | 🔴 | 0.0000 | 0.8000 | Introduction |
| `Q_QASP_318` | `1908.10449` | Introduction | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_319` | `1908.10449` | iMRC: Making MRC Interactive ::: Ac | 🔴 | 0.0000 | 0.6667 | Abstract |
| `Q_QASP_031` | `1811.00942` | Experimental Setup | 🔴 | 0.0000 | 1.0000 | Conclusion |
| `Q_QASP_032` | `1811.00942` | Introduction | 🔴 | 0.2184 | 1.0000 | Abstract |
| `Q_QASP_033` | `1811.00942` | Introduction | 🔴 | 0.6309 | 1.0000 | Infrastructure |
| `Q_QASP_767` | `1606.05286` | Experimental results | 🔴 | 0.6509 | 1.0000 | Abstract |
| `Q_QASP_637` | `1808.00265` | Results | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_638` | `1808.00265` | Results | 🔴 | 0.0000 | 1.0000 | Conclusions |
| `Q_QASP_639` | `1808.00265` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_083` | `1910.03042` | Analysis | 🟢 | 0.1232 | 0.7500 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_084` | `1910.03042` | Analysis ::: Response Depth: Mean W | 🟢 | 1.0000 | 1.0000 | Analysis ::: Response Depth: Mean Word C |
| `Q_QASP_085` | `1910.03042` | System Architecture | 🔴 | 0.3066 | 0.5000 | Abstract |
| `Q_QASP_086` | `1910.03042` | System Architecture | 🔴 | 0.0000 | 0.5000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_087` | `1910.03042` | Analysis | 🟢 | 0.3066 | 0.5000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_088` | `1910.03042` | Analysis ::: Response Depth: Mean W | 🔴 | 0.1413 | 1.0000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_469` | `1911.00069` | Experiments ::: Source (English) RE | 🔴 | 0.3869 | 1.0000 | Experiments ::: Cross-Lingual RE Perform |
| `Q_QASP_470` | `1911.00069` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_471` | `1911.00069` | Experiments ::: Datasets | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_472` | `1911.00069` | Experiments ::: Datasets | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_772` | `1906.10519` | Setting for Experiment 1: Sentence- | 🟢 | 0.0000 | 0.0000 | Setting for Experiment 1: Sentence-level |
| `Q_QASP_649` | `1906.07668` | Visualization | 🔴 | 0.2044 | 0.5000 | Conclusions |
| `Q_QASP_704` | `1607.06275` | WebQA Dataset | 🔴 | 0.0000 | 0.0000 | Baselines |
| `Q_QASP_705` | `1607.06275` | Introduction | 🔴 | 0.8072 | 1.0000 | Baselines |
| `Q_QASP_706` | `1607.06275` | WebQA Dataset | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_152` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_153` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_154` | `1910.07181` | Evaluation ::: Downstream Task Data | 🟢 | 0.7904 | 1.0000 | Evaluation ::: Downstream Task Datasets |
| `Q_QASP_155` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_444` | `1812.07023` | Experiments | 🔴 | 0.2372 | 1.0000 | Abstract |
| `Q_QASP_010` | `2003.07723` | Introduction | 🟢 | 0.5000 | 1.0000 | Introduction |
| `Q_QASP_011` | `2003.07723` | Expert Annotation ::: Agreement | 🔴 | 0.0000 | 0.0000 | Crowdsourcing Annotation |
| `Q_QASP_012` | `2003.07723` | Introduction | 🔴 | 0.3066 | 1.0000 | ::: ::: |
| `Q_QASP_407` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_408` | `1902.06843` | Multi-modal Prediction Framework | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_409` | `1902.06843` | Demographic Prediction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_410` | `1902.06843` | Data Modality Analysis | 🔴 | 0.2489 | 0.2727 | Related Work |
| `Q_QASP_411` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.5000 | Untitled Section |
| `Q_QASP_412` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.4000 | Untitled Section |
| `Q_QASP_413` | `1902.06843` | Introduction | 🔴 | 0.2891 | 1.0000 | Untitled Section |
| `Q_QASP_414` | `1902.06843` | Introduction | 🔴 | 0.3562 | 1.0000 | Demographic Prediction |
| `Q_QASP_415` | `1902.06843` | Introduction | 🔴 | 0.0000 | 0.0000 | Demographic Prediction |
| `Q_QASP_585` | `1606.02006` | Settings | 🔴 | 0.0000 | 0.0000 | Neural Machine Translation |
| `Q_QASP_586` | `1606.02006` | Introduction | 🔴 | 0.0000 | 1.0000 | Experiment & Result |
| `Q_QASP_779` | `2003.05995` | Introduction | 🔴 | 0.0000 | 0.2500 | Abstract |
| `Q_QASP_780` | `2003.05995` | Related Work | 🟢 | 0.7149 | 1.0000 | Related Work |
| `Q_QASP_781` | `2003.05995` | Data Analysis | 🔴 | 0.2462 | 0.3077 | Introduction |
| `Q_QASP_782` | `2003.05995` | System Overview | 🔴 | 0.3591 | 1.0000 | Abstract |
| `Q_QASP_013` | `1705.09665` | Applying the typology to Reddit | 🔴 | 0.2641 | 0.5000 | Community-type and user tenure |
| `Q_QASP_014` | `1705.09665` | Community-type and monthly retentio | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_015` | `1705.09665` | Introduction | 🟢 | 0.0000 | 0.6667 | Introduction |
| `Q_QASP_016` | `1705.09665` | Applying the typology to Reddit | 🔴 | 0.1846 | 1.0000 | Introduction |
| `Q_QASP_017` | `1705.09665` | Community-level measures | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_018` | `1705.09665` | Community-level measures | 🔴 | 0.6309 | 1.0000 | Community identity and acculturation |
| `Q_QASP_063` | `2003.06651` | Related Work | 🟢 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_064` | `2003.06651` | Evaluation ::: Word Sense Disambigu | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_065` | `2003.06651` | Evaluation | 🔴 | 0.2891 | 1.0000 | Conclusions and Future Work |
| `Q_QASP_422` | `1910.02789` | Semantic State Representations in t | 🔴 | 0.3066 | 1.0000 | Abstract |
| `Q_QASP_425` | `1910.02789` | Semantic State Representations in t | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_426` | `1910.02789` | Introduction | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_160` | `1909.00542` | Classification vs. Regression Exper | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_161` | `1909.00542` | Classification vs. Regression Exper | 🔴 | 0.0000 | 1.0000 | Conclusions |
| `Q_QASP_162` | `1909.00542` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_748` | `1909.01013` | Approach ::: Regularizers for Dual  | 🔴 | 0.3333 | 1.0000 | Experiments ::: The Effectiveness of Dua |
| `Q_QASP_749` | `1909.01013` | Experiments ::: Comparison with the | 🔴 | 0.3155 | 1.0000 | Introduction |
| `Q_QASP_750` | `1909.01013` | Introduction | 🟢 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_752` | `1909.01013` | Experiments ::: The Effectiveness o | 🔴 | 0.2372 | 1.0000 | Experiments ::: Comparison with the Stat |
| `Q_QASP_753` | `1909.01013` | Experiments ::: Comparison with the | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_613` | `1803.03664` | Experiments and Results | 🔴 | 0.2891 | 1.0000 | Question Generation |
| `Q_QASP_467` | `1708.09157` | Character-Level Neural Transfer | 🔴 | 0.2044 | 1.0000 | Abstract |
| `Q_QASP_468` | `1708.09157` | Datasets | 🔴 | 0.0000 | 0.0000 | Experimental Languages |
| `Q_QASP_244` | `1907.02030` | Choosing an embedding | 🟢 | 0.0000 | 0.0000 | Choosing an embedding |
| `Q_QASP_245` | `1907.02030` | Related Work | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_246` | `1907.02030` | Choosing an embedding | 🟢 | 0.0000 | 0.0000 | Choosing an embedding |
| `Q_QASP_170` | `1905.11901` | Data and Preprocessing | 🔴 | 0.1232 | 0.7500 | NMT Systems |
| `Q_QASP_171` | `1905.11901` | Results | 🟢 | 1.0000 | 1.0000 | Results |
| `Q_QASP_172` | `1905.11901` | Results | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_173` | `1905.11901` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_512` | `1904.08386` | Embedding city descriptions | 🟢 | 0.9197 | 1.0000 | Embedding city descriptions |
| `Q_QASP_513` | `1904.08386` | Introduction | 🔴 | 0.3562 | 1.0000 | Conclusion |
| `Q_QASP_514` | `1904.08386` | Clustering city representations | 🟢 | 0.8772 | 1.0000 | Clustering city representations |
| `Q_QASP_383` | `1911.01799` | Introduction | 🔴 | 0.2044 | 1.0000 | The CN-Celeb dataset ::: Challenges with |
| `Q_QASP_492` | `1910.05456` | Experimental Design ::: Target Lang | 🔴 | 0.1312 | 0.6000 | Conclusion and Future Work |
| `Q_QASP_493` | `1910.05456` | Experimental Design ::: Target Lang | 🔴 | 0.0000 | 0.0000 | Qualitative Results ::: Stem Errors |
| `Q_QASP_494` | `1910.05456` | Introduction | 🔴 | 0.2463 | 0.5000 | Quantitative Results |
| `Q_QASP_495` | `1910.05456` | Introduction | 🔴 | 0.3066 | 1.0000 | Related Work ::: Acquisition of morpholo |
| `Q_QASP_049` | `1810.04528` | Portuguese Embedding | 🟢 | 0.6423 | 1.0000 | Portuguese Embedding |
| `Q_QASP_050` | `1810.04528` | Portuguese Embedding | 🔴 | 0.6053 | 1.0000 | Related Work |
| `Q_QASP_644` | `1910.05608` | Introduction | 🔴 | 0.2346 | 0.6667 | System description ::: Data pre-processi |
| `Q_QASP_645` | `1910.05608` | System description ::: System overv | 🟢 | 0.5801 | 1.0000 | System description ::: System overview |
| `Q_QASP_646` | `1910.05608` | Experiment | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_647` | `1910.05608` | Experiment | 🔴 | 0.3066 | 0.5000 | Abstract |
| `Q_QASP_648` | `1910.05608` | System description ::: System overv | 🔴 | 0.2921 | 1.0000 | Experiment |
| `Q_QASP_045` | `1912.02481` | Semantic Representations ::: Experi | 🔴 | 0.2021 | 0.3333 | Abstract |
| `Q_QASP_047` | `1912.02481` | Semantic Representations ::: Experi | 🔴 | 0.0000 | 0.0000 | Semantic Representations |
| `Q_QASP_055` | `2003.07433` | Experimental Evaluation ::: Results | 🔴 | 0.3072 | 0.6667 | Introduction |
| `Q_QASP_056` | `2003.07433` | Twitter-based PTSD Detection ::: PT | 🔴 | 0.3638 | 0.7500 | Related Works |
| `Q_QASP_057` | `2003.07433` | Twitter-based PTSD Detection ::: Pr | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_058` | `2003.07433` | Twitter-based PTSD Detection ::: Da | 🔴 | 0.3086 | 0.5000 | Abstract |
| `Q_QASP_141` | `1703.05260` | Introduction | 🔴 | 0.5706 | 1.0000 | Development of the Schema |
| `Q_QASP_142` | `1703.05260` | First Annotation Phase | 🟢 | 1.0000 | 1.0000 | First Annotation Phase |
| `Q_QASP_522` | `1906.04571` | Introduction | 🟢 | 0.7904 | 1.0000 | Introduction |
| `Q_QASP_523` | `1906.04571` | Extrinsic Evaluation | 🟢 | 0.0000 | 0.0000 | Extrinsic Evaluation |
| `Q_QASP_524` | `1906.04571` | Conclusion | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_529` | `1809.07629` | Setup | 🟢 | 0.9197 | 1.0000 | Setup |
| `Q_QASP_530` | `1809.07629` | Setup | 🔴 | 0.0000 | 0.0000 | Attentional Hierarchical Decoder |
| `Q_QASP_320` | `1910.03814` | Methodology ::: Multimodal Architec | 🔴 | 0.3010 | 1.0000 | Results |
| `Q_QASP_322` | `1910.03814` | The MMHS150K dataset | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_323` | `1910.03814` | Results | 🟢 | 0.0000 | 1.0000 | Results |
| `Q_QASP_324` | `1910.03814` | Results | 🔴 | 0.3212 | 0.6667 | Abstract |
| `Q_QASP_325` | `1910.03814` | Results | 🟢 | 0.6309 | 1.0000 | Results |
| `Q_QASP_326` | `1910.03814` | The MMHS150K dataset ::: Tweets Gat | 🟢 | 1.0000 | 1.0000 | The MMHS150K dataset ::: Tweets Gatherin |
| `Q_QASP_327` | `1910.03814` | The MMHS150K dataset | 🔴 | 0.4307 | 1.0000 | Related Work ::: Hate Speech Detection |
| `Q_QASP_328` | `1910.03814` | Methodology ::: Unimodal Treatment  | 🔴 | 0.2044 | 1.0000 | Abstract |
| `Q_QASP_329` | `1910.03814` | Methodology ::: Multimodal Architec | 🔴 | 0.3155 | 1.0000 | Results |
| `Q_QASP_330` | `1910.03814` | The MMHS150K dataset ::: Annotation | 🔴 | 0.0000 | 0.0000 | Related Work ::: Hate Speech Detection |
| `Q_QASP_436` | `1909.00279` | Experiment ::: Interpoetry: Generat | 🔴 | 0.1128 | 0.7500 | Abstract |
| `Q_QASP_437` | `1909.00279` | Experiment ::: Reborn Poems: Genera | 🔴 | 0.3869 | 1.0000 | Experiment ::: Evaluation Metrics |
| `Q_QASP_438` | `1909.00279` | Experiment ::: Datasets | 🔴 | 0.3869 | 1.0000 | Experiment |
| `Q_QASP_665` | `2003.06279` | Conclusion | 🔴 | 0.5706 | 1.0000 | Abstract |
| `Q_QASP_666` | `2003.06279` | Introduction | 🔴 | 0.2021 | 1.0000 | Abstract |
| `Q_QASP_667` | `2003.06279` | Introduction | 🔴 | 0.0000 | 1.0000 | Related works |
| `Q_QASP_668` | `2003.06279` | Introduction | 🔴 | 0.0000 | 0.5000 | Results and Discussion ::: Effects of co |
| `Q_QASP_297` | `1702.06378` | Multitask Learning Results | 🔴 | 0.5110 | 1.0000 | Abstract |
| `Q_QASP_777` | `1806.04535` | Puns | 🟢 | 1.0000 | 1.0000 | Puns |
| `Q_QASP_778` | `1806.04535` | Introduction | 🔴 | 0.4585 | 1.0000 | Dataset |
| `Q_QASP_298` | `1903.03467` | Conclusions | 🟢 | 0.9197 | 1.0000 | Conclusions |
| `Q_QASP_299` | `1903.03467` | Introduction | 🔴 | 0.2021 | 0.3333 | Abstract |
| `Q_QASP_300` | `1903.03467` | Quantitative Results | 🔴 | 0.1681 | 1.0000 | Abstract |
| `Q_QASP_301` | `1903.03467` | Experiments & Results | 🔴 | 0.3890 | 1.0000 | Abstract |
| `Q_QASP_302` | `1903.03467` | Black-Box Knowledge Injection | 🟢 | 0.4693 | 0.6667 | Black-Box Knowledge Injection |
| `Q_QASP_381` | `1909.00088` | Introduction | 🔴 | 0.5000 | 1.0000 | Evaluation ::: Semantic Text Exchange Sc |
| `Q_QASP_382` | `1909.00088` | Introduction | 🔴 | 0.2891 | 1.0000 | Abstract |
| `Q_QASP_066` | `1910.04269` | Related Work | 🔴 | 0.0000 | 0.0000 | Proposed Method ::: Motivations |
| `Q_QASP_067` | `1910.04269` | Related Work | 🔴 | 0.3333 | 1.0000 | Results and Discussion |
| `Q_QASP_226` | `1911.09886` | Experiments ::: Datasets | 🟢 | 0.6131 | 1.0000 | Experiments ::: Datasets |
| `Q_QASP_227` | `1911.09886` | Experiments ::: Experimental Result | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_228` | `1911.09886` | Experiments ::: Baselines and Evalu | 🔴 | 0.1012 | 0.5556 | Abstract |
| `Q_QASP_229` | `1911.09886` | Experiments ::: Experimental Result | 🟢 | 1.0000 | 1.0000 | Experiments ::: Experimental Results |
| `Q_QASP_735` | `1908.10275` | Experiments | 🔴 | 0.0000 | 0.0000 | Motivation, Background and Related Work |
| `Q_QASP_736` | `1908.10275` | Data Description | 🔴 | 0.0000 | 0.0000 | Brief introduction to popular music |
| `Q_QASP_737` | `1908.10275` | Data Description | 🔴 | 0.6309 | 1.0000 | Brief introduction to popular music |
| `Q_QASP_533` | `2002.11402` | Data Preparation | 🟢 | 0.6257 | 1.0000 | Data Preparation |
| `Q_QASP_230` | `1611.01400` | Baseline Systems | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_231` | `1611.01400` | Learning to Rank | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_232` | `1611.01400` | Benchmark Datasets | 🔴 | 0.0000 | 0.0000 | Features |
| `Q_QASP_233` | `1611.01400` | Benchmark Datasets | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_001` | `1608.06757` | Evaluation Set Up | 🟢 | 0.8772 | 1.0000 | Evaluation Set Up |
| `Q_QASP_698` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.3707 | 1.0000 | Introduction |
| `Q_QASP_699` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.2346 | 0.3333 | Results |
| `Q_QASP_700` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.1934 | 1.0000 | Discussion |
| `Q_QASP_701` | `1604.05781` | Introduction | 🔴 | 0.5000 | 1.0000 | Results |
| `Q_QASP_702` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.0000 | 0.0000 | Tagging and corpus comparison |
| `Q_QASP_703` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.1815 | 0.3333 | Tagging and corpus comparison |
| `Q_QASP_428` | `2001.07209` | Emerging NLP research on morality | 🔴 | 0.0000 | 1.0000 | Applications to diachronic morality :::  |
| `Q_QASP_429` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.0000 | 0.5000 | Applications to diachronic morality :::  |
| `Q_QASP_430` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.3501 | 0.6667 | Abstract |
| `Q_QASP_431` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.1846 | 0.5000 | Applications to diachronic morality :::  |
| `Q_QASP_432` | `2001.07209` | A three-tier modelling framework | 🟢 | 0.1772 | 1.0000 | A three-tier modelling framework ::: Mod |
| `Q_QASP_773` | `1905.13413` | Iterative Learning | 🔴 | 0.6364 | 1.0000 | Experimental Settings |
| `Q_QASP_774` | `1905.13413` | Model Architecture and Decoding | 🔴 | 0.6309 | 1.0000 | Evaluation Results |
| `Q_QASP_137` | `1908.08419` | Information Entropy Based Scoring M | 🟢 | 0.8175 | 1.0000 | Information Entropy Based Scoring Model |
| `Q_QASP_138` | `1908.08419` | Active Learning for Chinese Word Se | 🔴 | 0.4307 | 1.0000 | Chinese Word Segmentation |
| `Q_QASP_139` | `1908.08419` | Information Entropy Based Scoring M | 🟢 | 0.8316 | 1.0000 | Information Entropy Based Scoring Model |
| `Q_QASP_387` | `1905.08949` | Wider Input Modalities | 🔴 | 0.1413 | 0.3333 | Input Modality |
| `Q_QASP_388` | `1905.08949` | Learning Paradigm | 🔴 | 0.1672 | 0.6667 | Abstract |
| `Q_QASP_389` | `1905.08949` | Input Modality | 🟢 | 0.9197 | 1.0000 | Input Modality |
| `Q_QASP_515` | `1909.00754` | Experimental Setting | 🔴 | 0.2641 | 0.5000 | Related Work |
| `Q_QASP_516` | `1909.00754` | Experimental Setting | 🔴 | 0.0000 | 0.0000 | Implementation Details |
| `Q_QASP_462` | `1710.06536` | Introduction | 🟢 | 0.2044 | 0.5000 | Introduction |
| `Q_QASP_384` | `1812.06705` | Datasets | 🟢 | 0.6131 | 1.0000 | Datasets |
| `Q_QASP_385` | `1812.06705` | Text classification | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_386` | `1812.06705` | Text classification | 🟢 | 0.3869 | 1.0000 | Text classification |
| `Q_QASP_650` | `1605.04655` | Sentence Embeddings | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_651` | `1605.04655` | Evaluation | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_653` | `1605.04655` | Introduction | 🔴 | 0.2583 | 0.4118 | Sentence Embeddings |
| `Q_QASP_683` | `1904.07342` | Data | 🟢 | 1.0000 | 1.0000 | Data |
| `Q_QASP_684` | `1904.07342` | Results & Discussion | 🔴 | 0.0000 | 0.0000 | Data |
| `Q_QASP_685` | `1904.07342` | Labeling Methodology | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_686` | `1904.07342` | Data | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_687` | `1904.07342` | Data | 🟢 | 0.2372 | 1.0000 | Data |
| `Q_QASP_792` | `1907.02636` | Results | 🟢 | 1.0000 | 1.0000 | Results |
| `Q_QASP_793` | `1907.02636` | Contextual Features | 🟢 | 0.2891 | 1.0000 | Analysis of Contextual Features |
| `Q_QASP_794` | `1907.02636` | Datasets | 🟢 | 1.0000 | 1.0000 | Datasets |
| `Q_QASP_122` | `1909.09491` | Plackett-Luce Model in Statistical  | 🔴 | 0.4776 | 0.6667 | Abstract |
| `Q_QASP_124` | `1909.09491` | Introduction | 🔴 | 0.2694 | 1.0000 | Abstract |
| `Q_QASP_618` | `1902.09087` | Introduction | 🟢 | 0.4925 | 0.3939 | Introduction |
| `Q_QASP_619` | `1902.09087` | Evaluation Metrics | 🟢 | 1.0000 | 1.0000 | Evaluation Metrics |
| `Q_QASP_620` | `1902.09087` | Introduction | 🟢 | 0.3270 | 0.4000 | Introduction |
| `Q_QASP_623` | `1907.01413` | Future Work | 🟢 | 0.6131 | 1.0000 | Future Work |
| `Q_QASP_624` | `1907.01413` | Ultrasound Data | 🟢 | 0.6131 | 1.0000 | Ultrasound Data |
| `Q_QASP_625` | `1907.01413` | Preprocessing and Model Architectur | 🔴 | 0.2184 | 0.5000 | Conclusion |
| `Q_QASP_626` | `1907.01413` | Data Selection | 🔴 | 0.0000 | 1.0000 | Ultrasound Data |
| `Q_QASP_627` | `1907.01413` | Preprocessing and Model Architectur | 🟢 | 0.8066 | 1.0000 | Preprocessing and Model Architectures |
| `Q_QASP_628` | `1907.01413` | Ultrasound Data | 🟢 | 0.6131 | 0.5000 | Ultrasound Data |
| `Q_QASP_312` | `1909.00430` | Expectation Regularization (XR) | 🔴 | 0.4228 | 1.0000 | Introduction |
| `Q_QASP_174` | `1912.01252` | Introduction ::: Objective | 🔴 | 0.3869 | 0.5000 | Conclusion |
| `Q_QASP_177` | `1912.01252` | Mining opinions and beliefs from te | 🟢 | 0.3869 | 1.0000 | Mining opinions and beliefs from texts : |
| `Q_QASP_573` | `1606.05320` | Methods | 🔴 | 0.2983 | 1.0000 | Abstract |
| `Q_QASP_574` | `1606.05320` | Experiments | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_575` | `1606.05320` | Introduction | 🔴 | 0.1175 | 1.0000 | Abstract |
| `Q_QASP_459` | `1907.00758` | Data | 🟢 | 1.0000 | 1.0000 | Data |
| `Q_QASP_460` | `1907.00758` | Model | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_461` | `1907.00758` | Model | 🔴 | 0.6053 | 1.0000 | Introduction |
| `Q_QASP_292` | `1910.11769` | Introduction | 🔴 | 0.0000 | 1.0000 | Benchmarks ::: Fine-tuned BERT |
| `Q_QASP_293` | `1910.11769` | Dataset ::: Plutchik’s Wheel of Emo | 🔴 | 0.4575 | 1.0000 | Dataset ::: Mechanical Turk (MTurk) |
| `Q_QASP_294` | `1910.11769` | Benchmarks ::: Bag-of-Words-based B | 🔴 | 1.0000 | 1.0000 | Abstract |
| `Q_QASP_295` | `1910.11769` | Dataset ::: Dataset Statistics | 🟢 | 1.0000 | 1.0000 | Dataset ::: Dataset Statistics |
| `Q_QASP_296` | `1910.11769` | Dataset ::: Mechanical Turk (MTurk) | 🟢 | 1.0000 | 1.0000 | Dataset ::: Mechanical Turk (MTurk) |
| `Q_QASP_599` | `1911.11744` | Results | 🔴 | 0.4911 | 1.0000 | Abstract |
| `Q_QASP_600` | `1911.11744` | Results | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_601` | `1911.11744` | Results | 🔴 | 0.0000 | 0.3333 | Abstract |
| `Q_QASP_545` | `2004.03034` | Results and Analysis | 🔴 | 0.5438 | 1.0000 | Methodology ::: Baseline Models ::: Majo |
| `Q_QASP_546` | `2004.03034` | Methodology ::: Baseline Models ::: | 🔴 | 0.4416 | 1.0000 | Abstract |
| `Q_QASP_547` | `2004.03034` | Dataset | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_548` | `2004.03034` | Dataset | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_307` | `1909.13375` | Related Work | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_308` | `1909.13375` | Model ::: Multi-Span Head | 🔴 | 0.3869 | 0.5000 | Model ::: Tag Sequence Prediction with t |
| `Q_QASP_309` | `1909.13375` | Results and Discussion ::: Performa | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_310` | `1909.13375` | Related Work | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_074` | `1712.09127` | weGAN: Training cross-corpus word e | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_075` | `1712.09127` | The CNN data set | 🔴 | 0.0000 | 0.0000 | deGAN: Generating document embeddings fo |
| `Q_QASP_076` | `1712.09127` | Experiments | 🔴 | 0.6309 | 1.0000 | Models and Algorithms |
| `Q_QASP_483` | `1809.05752` | Future Work and Conclusion | 🟢 | 1.0000 | 1.0000 | Future Work and Conclusion |
| `Q_QASP_484` | `1809.05752` | Data | 🔴 | 0.4441 | 0.6667 | Related Work |
| `Q_QASP_730` | `1602.08741` | Acquiring data | 🔴 | 0.1420 | 0.4706 | Conclusion |
| `Q_QASP_760` | `1910.10408` | Introduction | 🔴 | 0.2184 | 0.5000 | Results ::: Human Evaluation and Analysi |
| `Q_QASP_761` | `1910.10408` | Experiments ::: Data and Settings | 🔴 | 0.6509 | 1.0000 | Results |
| `Q_QASP_762` | `1910.10408` | Introduction | 🔴 | 0.6399 | 0.6000 | Background ::: Transformer |
| `Q_QASP_763` | `1910.10408` | Introduction | 🔴 | 0.2083 | 0.3077 | Abstract |
| `Q_QASP_764` | `1910.10408` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_765` | `1910.10408` | Experiments ::: Data and Settings | 🔴 | 0.4416 | 1.0000 | Related works |
| `Q_QASP_766` | `1910.10408` | Introduction | 🔴 | 0.7538 | 0.8889 | Methods ::: Combining the two methods |
| `Q_QASP_427` | `1902.00672` | Detection of hypergraph transversal | 🔴 | 0.0000 | 0.2500 | Comparison with DUC systems |
| `Q_QASP_248` | `1910.04601` | Baseline RC-QED@!START@$^{\rm E}$@! | 🔴 | 0.4228 | 1.0000 | Introduction |
| `Q_QASP_249` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.3333 | 1.0000 | Introduction |
| `Q_QASP_250` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.3333 | 1.0000 | Data collection for RC-QED@!START@$^{\rm |
| `Q_QASP_251` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.0000 | 0.0000 | Related work ::: RC datasets with explan |
| `Q_QASP_395` | `1603.01417` | Input Module for Text QA | 🔴 | 0.3010 | 1.0000 | Abstract |
| `Q_QASP_396` | `1603.01417` | Introduction | 🔴 | 0.0000 | 1.0000 | Comparison to state of the art using bAb |
| `Q_QASP_397` | `1603.01417` | Input Module for Text QA | 🔴 | 0.1846 | 0.5000 | Datasets |
| `Q_QASP_398` | `1603.01417` | Introduction | 🔴 | 0.2372 | 1.0000 | Improved Dynamic Memory Networks: DMN+ |
| `Q_QASP_399` | `1603.01417` | Conclusion | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_400` | `1603.01417` | Conclusion | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_800` | `1908.11425` | Methods ::: Speech-to-text translat | 🔴 | 0.6131 | 1.0000 | Experimental Setup ::: Fine-grained topi |
| `Q_QASP_801` | `1908.11425` | Experimental Setup ::: Data. | 🔴 | 0.0000 | 1.0000 | Results ::: Spanish-English ST. |
| `Q_QASP_167` | `1909.02764` | Results ::: Facial Expressions and  | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_168` | `1909.02764` | Methods ::: Emotion Recognition fro | 🔴 | 0.0000 | 0.0000 | Results ::: Text from Transcribed Uttera |
| `Q_QASP_169` | `1909.02764` | Methods ::: Emotion Recognition fro | 🔴 | 0.1815 | 0.6667 | Abstract |
| `Q_QASP_463` | `1701.02877` | Datasets | 🔴 | 0.3333 | 1.0000 | RQ2: NER performance in Different Genres |
| `Q_QASP_496` | `1910.05154` | Experiments | 🟢 | 0.6131 | 1.0000 | Experiments |
| `Q_QASP_497` | `1910.05154` | Experiments | 🟢 | 1.0000 | 1.0000 | Experiments |
| `Q_QASP_498` | `1910.05154` | Experiments | 🟢 | 0.5856 | 1.0000 | Experiments |
| `Q_QASP_499` | `1910.05154` | Methodology ::: Bilingual Unsupervi | 🔴 | 0.6166 | 1.0000 | Conclusion |
| `Q_QASP_500` | `1910.05154` | Conclusion | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_201` | `1703.04617` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_202` | `1703.04617` | Results | 🔴 | 0.2184 | 1.0000 | Conclusions |
| `Q_QASP_203` | `1703.04617` | The Baseline Model | 🟢 | 0.5000 | 1.0000 | The Baseline Model |
| `Q_QASP_204` | `1703.04617` | Results | 🟢 | 0.5000 | 1.0000 | Results |
| `Q_QASP_549` | `1910.12618` | Presentation of the data ::: Text | 🔴 | 0.0000 | 0.0000 | Modeling and forecasting framework ::: H |
| `Q_QASP_550` | `1910.12618` | Experiments ::: Interpretability of | 🔴 | 0.1934 | 1.0000 | Abstract |
| `Q_QASP_551` | `1910.12618` | Experiments ::: Interpretability of | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_552` | `1910.12618` | Introduction | 🔴 | 0.1357 | 0.3333 | Modeling and forecasting framework ::: N |
| `Q_QASP_390` | `1909.00170` | Introduction | 🔴 | 0.0000 | 1.0000 | Model |
| `Q_QASP_391` | `1909.00170` | Off-the-shelf NE Recognition System | 🔴 | 0.3869 | 0.5000 | Experiment |
| `Q_QASP_474` | `1910.04887` | Methods ::: Data and Training Detai | 🔴 | 0.6934 | 1.0000 | Abstract |
| `Q_QASP_475` | `1910.04887` | Methods ::: Modifying FactorCell LS | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_606` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.6309 | 1.0000 | Dataset |
| `Q_QASP_607` | `1911.00523` | Predicting Pointers ::: Experiment  | 🔴 | 0.2961 | 0.3333 | Predicting Pointers ::: Prediction Perfo |
| `Q_QASP_608` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.1786 | 0.5000 | Predicting Pointers ::: The Effect on Ge |
| `Q_QASP_609` | `1911.00523` | Predicting Pointers ::: Experiment  | 🔴 | 0.8066 | 1.0000 | Predicting Pointers ::: Prediction Perfo |
| `Q_QASP_610` | `1911.00523` | Predicting Pointers ::: Experiment  | 🟢 | 1.0000 | 1.0000 | Predicting Pointers ::: Experiment setup |
| `Q_QASP_611` | `1911.00523` | Concluding Discussions | 🔴 | 0.2891 | 1.0000 | Abstract |
| `Q_QASP_612` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.1786 | 0.5000 | Predicting Pointers ::: The Effect on Ge |
| `Q_QASP_535` | `2002.00652` | Experiment & Analysis ::: Experimen | 🔴 | 0.6131 | 0.5000 | Experiment & Analysis ::: Model Comparis |
| `Q_QASP_536` | `2002.00652` | Introduction | 🔴 | 0.7328 | 1.0000 | Experiment & Analysis ::: Experimental S |
| `Q_QASP_537` | `2002.00652` | Experiment & Analysis ::: Model Com | 🔴 | 0.4416 | 1.0000 | Abstract |
| `Q_QASP_538` | `2002.00652` | Introduction | 🔴 | 0.9675 | 1.0000 | Abstract |
| `Q_QASP_371` | `1706.08032` | Experimental results | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_372` | `1706.08032` | Data Preparation | 🔴 | 0.0000 | 0.0000 | Preprocessing |
| `Q_QASP_373` | `1706.08032` | Data Preparation | 🔴 | 0.6364 | 0.6667 | Experimental results |
| `Q_QASP_374` | `1706.08032` | Data Preparation | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_375` | `1706.08032` | Semantic Rules (SR) | 🟢 | 0.9134 | 1.0000 | Semantic Rules (SR) |
| `Q_QASP_602` | `1910.03467` | Experiments ::: Results ::: Japanes | 🔴 | 0.1772 | 1.0000 | Introduction |
| `Q_QASP_603` | `1910.03467` | Experiments ::: Results ::: Japanes | 🔴 | 0.0000 | 1.0000 | Rare Word translation ::: Reducing Unkno |
| `Q_QASP_569` | `1901.04899` | Methodology | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_570` | `1901.04899` | Methodology | 🟢 | 0.4307 | 1.0000 | Methodology |
| `Q_QASP_571` | `1901.04899` | Experimental Results | 🔴 | 0.3010 | 1.0000 | Methodology |
| `Q_QASP_572` | `1901.04899` | Methodology | 🔴 | 0.3010 | 1.0000 | Abstract |
| `Q_QASP_125` | `2001.05284` | Baseline, Oracle and Direct Models  | 🔴 | 0.3978 | 1.0000 | Conclusions and Future Work |
| `Q_QASP_126` | `2001.05284` | Baseline, Oracle and Direct Models  | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_127` | `2001.05284` | Experiment ::: Dataset | 🔴 | 0.0000 | 1.0000 | Baseline, Oracle and Direct Models ::: B |
| `Q_QASP_519` | `1906.00180` | Unseen lengths | 🔴 | 0.0000 | 0.0000 | Task definition & data generation |
| `Q_QASP_690` | `1911.00547` | Data Collection and Annotation | 🔴 | 0.5000 | 1.0000 | Experiments and Results ::: Experimental |
| `Q_QASP_691` | `1911.00547` | Introduction | 🔴 | 0.2184 | 0.5000 | Experiments and Results ::: Results and  |
| `Q_QASP_692` | `1911.00547` | Patterns of Sexual Harassment | 🔴 | 0.0000 | 1.0000 | Conclusions |
| `Q_QASP_313` | `1910.11493` | Baselines ::: Task 2 Baselines :::  | 🟢 | 1.0000 | 1.0000 | Baselines ::: Task 2 Baselines ::: Non-n |
| `Q_QASP_722` | `1908.04917` | Compared Methods and Evaluation Pro | 🔴 | 0.1846 | 0.5000 | The Proposed Method |
| `Q_QASP_723` | `1908.04917` | Introduction | 🔴 | 0.2184 | 0.5000 | Abstract |
| `Q_QASP_724` | `1908.04917` | Tone Prediction Sub-network | 🔴 | 0.0955 | 0.5000 | Abstract |
| `Q_QASP_238` | `1807.03367` | Data Collection | 🔴 | 0.1413 | 0.3333 | The Tourist |
| `Q_QASP_239` | `1807.03367` | Data Collection | 🔴 | 0.0000 | 1.0000 | Dataset Statistics |
| `Q_QASP_240` | `1807.03367` | Introduction | 🔴 | 0.5541 | 0.1739 | Abstract |
| `Q_QASP_241` | `1807.03367` | Results and Discussion | 🔴 | 0.0000 | 0.0000 | Evaluation on Full Setup |
| `Q_QASP_242` | `1807.03367` | Introduction | 🔴 | 0.0000 | 0.0000 | Data Collection |
| `Q_QASP_486` | `2001.01589` | Approach ::: Morphologically Motiva | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_487` | `2001.01589` | Approach | 🔴 | 0.2184 | 0.5000 | Related Work |

### `hybrid_rrf` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_QASP_010` | `1801.05147` | Data Sets | 🟢 | 0.0000 | 0.0000 | Data Sets |
| `Q_QASP_020` | `1909.00512` | Approach ::: Measures of Contextual | 🔴 | 0.1699 | 0.5000 | Abstract |
| `Q_QASP_021` | `1909.00512` | Introduction | 🔴 | 0.0000 | 0.0000 | Approach ::: Measures of Contextuality : |
| `Q_QASP_022` | `2003.03106` | Results ::: Experiment A: NUBes-PHI | 🔴 | 0.0000 | 1.0000 | Materials and Methods ::: Systems ::: BE |
| `Q_QASP_023` | `2003.03106` | Materials and Methods ::: Systems : | 🔴 | 0.1510 | 0.2500 | Materials and Methods |
| `Q_QASP_025` | `2003.03106` | Materials and Methods ::: Data | 🟢 | 0.5842 | 0.6667 | Materials and Methods ::: Data |
| `Q_QASP_038` | `1605.06083` | Introduction | 🟢 | 0.8066 | 1.0000 | Introduction |
| `Q_QASP_039` | `1605.06083` | Other methods | 🔴 | 0.1301 | 0.5000 | Abstract |
| `Q_QASP_040` | `1605.06083` | Introduction | 🔴 | 0.1131 | 0.6000 | Abstract |
| `Q_QASP_041` | `1804.05918` | Experimental Results | 🔴 | 0.3392 | 0.6000 | Dataset and Preprocessing |
| `Q_QASP_042` | `1804.05918` | Experimental Results | 🔴 | 0.1357 | 0.6667 | Abstract |
| `Q_QASP_044` | `1901.05287` | Results | 🔴 | 0.4256 | 1.0000 | Introduction |
| `Q_QASP_045` | `1612.06685` | Psycholinguistic and Semantic Maps | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_046` | `1612.06685` | Data Collection | 🔴 | 0.4976 | 1.0000 | Abstract |
| `Q_QASP_051` | `1910.10781` | Introduction | 🔴 | 0.4297 | 0.6667 | Related work |
| `Q_QASP_052` | `1910.10781` | Introduction | 🟢 | 0.3120 | 1.0000 | Introduction |
| `Q_QASP_055` | `1911.06964` | Experiments | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_056` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.0000 | 1.0000 | Approach |
| `Q_QASP_057` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_058` | `1911.06964` | Experiments ::: Efficiency-accuracy | 🔴 | 0.6309 | 1.0000 | Approach ::: Modeling with autoencoders. |
| `Q_QASP_059` | `2001.02284` | Model ::: Dialogue Modules | 🔴 | 0.0000 | 0.2500 | Related Work |
| `Q_QASP_060` | `2001.02284` | Re-implementation of units with BER | 🔴 | 0.0000 | 0.2000 | Introduction ::: Outline and Contributio |
| `Q_QASP_061` | `2001.02284` | Target Domain & Task Definition | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_071` | `1809.00540` | Related Work | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_072` | `1809.00540` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_073` | `2004.03354` | Experiment 1: Biomedical NER ::: Do | 🔴 | 0.2346 | 0.3333 | Abstract |
| `Q_QASP_075` | `1611.04798` | Introduction | 🟢 | 0.3010 | 1.0000 | Introduction |
| `Q_QASP_076` | `1611.04798` | Under-resourced Translation | 🟢 | 0.8772 | 1.0000 | Under-resourced Translation |
| `Q_QASP_088` | `1809.09194` | Model | 🟢 | 0.8316 | 1.0000 | Model |
| `Q_QASP_089` | `1809.09194` | Results | 🔴 | 0.0000 | 1.0000 | Background |
| `Q_QASP_090` | `1809.09194` | Model | 🟢 | 0.6131 | 1.0000 | Model |
| `Q_QASP_091` | `1604.05372` | Learning to Translate: Ukrainian-to | 🟢 | 0.0000 | 0.5000 | Learning to Translate: Ukrainian-to-Russ |
| `Q_QASP_092` | `2002.08795` | Introduction | 🔴 | 0.4838 | 1.0000 | Abstract |
| `Q_QASP_093` | `2002.08795` | Introduction and Background | 🔴 | 0.8208 | 1.0000 | Abstract |
| `Q_QASP_094` | `2002.08795` | Introduction and Background | 🔴 | 0.3946 | 0.8571 | Abstract |
| `Q_QASP_096` | `1802.06024` | Experiments | 🔴 | 0.4483 | 0.5714 | Results and Analysis |
| `Q_QASP_097` | `1802.06024` | Experiments | 🟢 | 0.2837 | 0.6667 | Experiments |
| `Q_QASP_098` | `1802.06024` | Introduction | 🔴 | 0.5912 | 1.0000 | Abstract |
| `Q_QASP_099` | `1802.06024` | Experiments | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_100` | `1802.06024` | Introduction | 🔴 | 0.2063 | 0.7500 | Abstract |
| `Q_QASP_105` | `1710.07960` | Discussion | 🔴 | 0.0000 | 0.5000 | Introduction |
| `Q_QASP_106` | `1710.07960` | Introduction | 🔴 | 0.5307 | 0.8571 | Conclusions |
| `Q_QASP_107` | `1912.03804` | Related Work | 🟢 | 0.7039 | 1.0000 | Related Work |
| `Q_QASP_108` | `1912.03804` | Conclusion and Future Work | 🔴 | 0.3181 | 0.6000 | Abstract |
| `Q_QASP_109` | `1912.03804` | Method ::: Emotion detection | 🔴 | 0.6053 | 1.0000 | Related Work |
| `Q_QASP_110` | `1912.03804` | Introduction | 🔴 | 0.8365 | 0.5000 | Abstract |
| `Q_QASP_111` | `1912.03804` | Method ::: Content Analysis | 🔴 | 0.2443 | 1.0000 | Abstract |
| `Q_QASP_112` | `1912.08960` | Introduction | 🔴 | 0.1681 | 1.0000 | GTD Evaluation Framework |
| `Q_QASP_113` | `1912.08960` | Experimental Setup ::: Datasets | 🔴 | 0.1480 | 0.6667 | Related work ::: Synthetic datasets |
| `Q_QASP_114` | `1912.08960` | Experimental Setup ::: Models | 🔴 | 0.3010 | 1.0000 | Introduction |
| `Q_QASP_115` | `1912.08960` | GTD Evaluation Framework ::: Divers | 🔴 | 0.5912 | 1.0000 | Experimental Setup ::: Datasets |
| `Q_QASP_128` | `2004.01853` | Introduction | 🔴 | 0.4307 | 1.0000 | Experimental Setup ::: Datasets ::: GIGA |
| `Q_QASP_129` | `2004.01853` | Results ::: Automatic Evaluation | 🟢 | 0.9197 | 1.0000 | Results ::: Automatic Evaluation |
| `Q_QASP_130` | `1710.03348` | Introduction | 🔴 | 0.2339 | 0.8000 | Abstract |
| `Q_QASP_131` | `1710.03348` | Impact of Attention Mechanism | 🔴 | 0.2641 | 0.5000 | Attention Concentration |
| `Q_QASP_132` | `1710.03348` | Alignment Quality Impact on Transla | 🔴 | 0.2184 | 0.5000 | Abstract |
| `Q_QASP_138` | `1809.01202` | Experiment | 🔴 | 0.0000 | 0.0000 | Exploration |
| `Q_QASP_139` | `1809.01202` | Dataset | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_140` | `1909.02027` | Dataset ::: In-Scope Data Collectio | 🔴 | 0.0000 | 1.0000 | Dataset |
| `Q_QASP_141` | `1909.02027` | Introduction | 🔴 | 0.4693 | 1.0000 | Benchmark Evaluation |
| `Q_QASP_142` | `1909.02027` | Introduction | 🔴 | 0.3869 | 1.0000 | Results ::: Results with oos-train |
| `Q_QASP_143` | `1909.02027` | Dataset | 🔴 | 0.3084 | 0.6667 | Benchmark Evaluation ::: Out-of-Scope Pr |
| `Q_QASP_151` | `1611.01576` | Character-level Neural Machine Tran | 🟢 | 1.0000 | 1.0000 | Character-level Neural Machine Translati |
| `Q_QASP_152` | `1611.01576` | Sentiment Classification | 🟢 | 1.0000 | 1.0000 | Sentiment Classification |
| `Q_QASP_153` | `1611.01576` | Model | 🔴 | 0.2641 | 1.0000 | Variants |
| `Q_QASP_161` | `1909.08089` | Results and Analysis | 🔴 | 0.2184 | 1.0000 | Introduction |
| `Q_QASP_162` | `1909.08089` | Introduction | 🔴 | 0.1934 | 1.0000 | Decoder |
| `Q_QASP_164` | `1910.09982` | Data | 🔴 | 0.0000 | 0.5000 | Participants and Approaches ::: Teams Pa |
| `Q_QASP_165` | `1910.09982` | Baselines | 🟢 | 1.0000 | 1.0000 | Baselines |
| `Q_QASP_166` | `1609.00559` | Introduction | 🔴 | 0.6309 | 1.0000 | Method |
| `Q_QASP_167` | `1609.00559` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_168` | `1609.00559` | Comparison with Previous Work | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 1.0000 | Decoding the KB Query |
| `Q_QASP_170` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_173` | `1608.01084` | Data Set and Toolkits | 🟢 | 0.0000 | 0.0000 | Data Set and Toolkits |
| `Q_QASP_174` | `1904.10503` | Introduction | 🔴 | 1.0000 | 1.0000 | Conclusion and Future Work |
| `Q_QASP_175` | `1904.10503` | Results | 🔴 | 0.6509 | 1.0000 | Introduction |
| `Q_QASP_176` | `1904.10503` | Entity Linking using Wikidata | 🔴 | 0.2140 | 0.8000 | Abstract |
| `Q_QASP_177` | `1912.01772` | Introduction | 🔴 | 0.5464 | 0.7778 | Abstract |
| `Q_QASP_178` | `1912.01772` | The Resource ::: Additional Annotat | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_179` | `1603.01987` | The medical domain model | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_184` | `1702.03856` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_185` | `1702.03856` | Introduction | 🔴 | 0.6332 | 1.0000 | Analysis of challenges from UTD |
| `Q_QASP_186` | `1702.03856` | Dataset | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_189` | `1606.03676` | Corpora | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_190` | `1606.03676` | Corpora | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_193` | `1911.03343` | Introduction | 🔴 | 0.4306 | 1.0000 | Abstract |
| `Q_QASP_209` | `1909.07575` | Experiments ::: Baseline Models and | 🔴 | 0.5508 | 1.0000 | Abstract |
| `Q_QASP_210` | `1909.07575` | Our method ::: Training Procedure : | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_212` | `1904.07904` | Spoken Question Answering | 🟢 | 1.0000 | 1.0000 | Spoken Question Answering |
| `Q_QASP_213` | `1904.07904` | Results | 🔴 | 0.6509 | 1.0000 | Conclusion |
| `Q_QASP_214` | `1904.07904` | Results | 🔴 | 0.4367 | 1.0000 | Conclusion |
| `Q_QASP_215` | `1904.07904` | Corpus | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_216` | `2003.11645` | Introduction | 🔴 | 1.0000 | 1.0000 | Methodology |
| `Q_QASP_217` | `2003.11645` | Introduction | 🔴 | 0.5110 | 1.0000 | Abstract |
| `Q_QASP_218` | `2003.11645` | Introduction | 🟢 | 0.7977 | 1.0000 | Introduction |
| `Q_QASP_219` | `2003.11645` | Introduction | 🔴 | 0.0000 | 1.0000 | Literature Review |
| `Q_QASP_222` | `1604.03114` | Modeling Idea Flow | 🔴 | 0.2811 | 0.7500 | Abstract |
| `Q_QASP_223` | `1604.03114` | Debate Dataset: Intelligence Square | 🟢 | 1.0000 | 1.0000 | Debate Dataset: Intelligence Squared |
| `Q_QASP_227` | `1606.02891` | Baseline System | 🔴 | 0.5250 | 1.0000 | Abstract |
| `Q_QASP_228` | `1803.09123` | Empirical Study | 🔴 | 0.1952 | 0.7500 | Equation Embeddings Models |
| `Q_QASP_229` | `1803.09123` | Discovering Semantically Similar Eq | 🟢 | 0.7087 | 1.0000 | Discovering Semantically Similar Equatio |
| `Q_QASP_237` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.7495 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_238` | `1709.07814` | Attention-based Encoder Decoder for | 🔴 | 0.4660 | 1.0000 | Speech Data |
| `Q_QASP_239` | `1709.07814` | Speech Data | 🔴 | 0.1510 | 0.2500 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_249` | `2003.08380` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_251` | `1805.04508` | Gender Bias Results | 🔴 | 0.2769 | 1.0000 | Abstract |
| `Q_QASP_252` | `1805.04508` | The Equity Evaluation Corpus | 🔴 | 0.4247 | 0.7500 | Introduction |
| `Q_QASP_258` | `1910.05603` | System Description ::: Language Mod | 🟢 | 0.7845 | 1.0000 | System Description ::: Language Model |
| `Q_QASP_259` | `1910.05603` | Experiments ::: System combination | 🔴 | 0.5000 | 1.0000 | Conclusion |
| `Q_QASP_260` | `1910.05603` | System Description ::: Acoustic Mod | 🔴 | 0.3562 | 1.0000 | Experiments ::: Single system evaluation |
| `Q_QASP_261` | `1909.03405` | Results of NLI Tasks ::: GLUE | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_262` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_263` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_134` | `1909.08859` | Procedural Reasoning Networks | 🔴 | 0.2346 | 1.0000 | Abstract |
| `Q_QASP_135` | `1909.08859` | Experiments ::: Baselines | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_136` | `1909.08859` | Experiments ::: Results | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_541` | `1905.06566` | Introduction | 🔴 | 0.8539 | 0.8000 | Results |
| `Q_QASP_116` | `1708.05873` | Introduction | 🔴 | 0.6133 | 1.0000 | Abstract |
| `Q_QASP_117` | `1708.05873` | Introduction | 🔴 | 0.2891 | 1.0000 | Conclusion |
| `Q_QASP_118` | `1708.05873` | Estimation of topic models | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_303` | `1807.00868` | Using different features | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_304` | `1807.00868` | Basic setup | 🔴 | 0.4307 | 1.0000 | Related work |
| `Q_QASP_305` | `1807.00868` | Training the best model | 🟢 | 1.0000 | 1.0000 | Training the best model |
| `Q_QASP_505` | `2003.03612` | Introduction | 🔴 | 0.5029 | 1.0000 | Discussion |
| `Q_QASP_506` | `2003.03612` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_507` | `2003.03612` | Introduction | 🔴 | 0.0000 | 0.0000 | Multinomials |
| `Q_QASP_508` | `2003.03612` | Introduction | 🔴 | 0.1846 | 1.0000 | Abstract |
| `Q_QASP_509` | `2003.03612` | Models And Predictions ::: Predicti | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_510` | `2003.03612` | Models And Predictions ::: Predicti | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_511` | `2003.03612` | Introduction | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_163` | `1810.06743` | Results | 🟢 | 0.4693 | 0.3333 | Results |
| `Q_QASP_164` | `1810.06743` | Conclusion and Future Work | 🔴 | 0.0000 | 0.0000 | Similarities in the annotation |
| `Q_QASP_165` | `1810.06743` | Introduction | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_166` | `1810.06743` | Introduction | 🔴 | 0.3661 | 0.6000 | Abstract |
| `Q_QASP_284` | `1603.07044` | Introduction | 🔴 | 0.4367 | 1.0000 | Multitask Learning |
| `Q_QASP_286` | `1603.07044` | Conclusion | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_476` | `1810.00663` | Introduction | 🔴 | 0.4693 | 0.6667 | Dataset |
| `Q_QASP_477` | `1810.00663` | Quantitative Evaluation | 🔴 | 0.2961 | 1.0000 | Models Used in the Evaluation |
| `Q_QASP_478` | `1810.00663` | Models Used in the Evaluation | 🔴 | 0.5000 | 1.0000 | Evaluation Metrics |
| `Q_QASP_479` | `1810.00663` | Evaluation Metrics | 🟢 | 0.8452 | 1.0000 | Evaluation Metrics |
| `Q_QASP_480` | `1810.00663` | Introduction | 🔴 | 0.0000 | 1.0000 | Acknowledgments |
| `Q_QASP_481` | `1810.00663` | Introduction | 🔴 | 0.8319 | 0.7500 | Dataset |
| `Q_QASP_482` | `1810.00663` | Dataset | 🔴 | 0.2372 | 1.0000 | Quantitative Evaluation |
| `Q_QASP_193` | `2004.03685` | Towards Better Faithfulness Criteri | 🟢 | 0.6131 | 0.5000 | Towards Better Faithfulness Criteria |
| `Q_QASP_194` | `2004.03685` | Towards Better Faithfulness Criteri | 🔴 | 0.3869 | 1.0000 | Faithfulness vs. Plausibility |
| `Q_QASP_195` | `2004.03685` | Introduction | 🔴 | 0.1517 | 0.8889 | Defining Faithfulness |
| `Q_QASP_196` | `2004.03685` | Introduction | 🔴 | 0.7968 | 0.9000 | Guidelines for Evaluating Faithfulness : |
| `Q_QASP_658` | `1805.00760` | Model Description | 🔴 | 0.0000 | 1.0000 | Attention Visualization and Case Study |
| `Q_QASP_659` | `1805.00760` | Introduction | 🟢 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_660` | `1805.00760` | Datasets | 🔴 | 0.0000 | 1.0000 | Settings |
| `Q_QASP_661` | `1805.00760` | Main Results | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_587` | `1911.03243` | Dataset Quality Analysis ::: Agreem | 🔴 | 0.2044 | 1.0000 | Conclusion |
| `Q_QASP_588` | `1911.03243` | Background — QA-SRL ::: Corpora | 🔴 | 0.3010 | 1.0000 | Dataset Quality Analysis ::: Agreement w |
| `Q_QASP_589` | `1911.03243` | Introduction | 🔴 | 0.9715 | 1.0000 | Dataset Quality Analysis ::: Agreement w |
| `Q_QASP_590` | `1911.03243` | Introduction | 🔴 | 0.3978 | 1.0000 | Background — QA-SRL ::: Corpora |
| `Q_QASP_591` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_592` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_593` | `1911.03243` | Annotation and Evaluation Methods : | 🔴 | 0.0000 | 0.0000 | Dataset Quality Analysis ::: Dataset Ass |
| `Q_QASP_594` | `1911.03243` | Dataset Quality Analysis ::: Agreem | 🔴 | 0.3869 | 1.0000 | Dataset Quality Analysis ::: Dataset Ass |
| `Q_QASP_669` | `2004.03744` | SNLI-VE-2.0 ::: Re-annotation detai | 🔴 | 0.0000 | 0.0000 | Visual-Textual Entailment with Natural L |
| `Q_QASP_670` | `2004.03744` | Appendix ::: Details of the Mechani | 🔴 | 0.0000 | 0.0000 | Visual-Textual Entailment with Natural L |
| `Q_QASP_671` | `2004.03744` | Appendix ::: Statistics of e-SNLI-V | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_672` | `2004.03744` | SNLI-VE-2.0 ::: Re-evaluation of Vi | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_673` | `2004.03744` | Introduction | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_342` | `1911.11750` | Background ::: Document Representat | 🔴 | 0.3155 | 1.0000 | Background ::: Measures of Similarity |
| `Q_QASP_343` | `1911.11750` | Experiments | 🔴 | 0.6309 | 1.0000 | The Spearman's Rank Correlation Coeffici |
| `Q_QASP_344` | `1911.11750` | The Spearman's Rank Correlation Coe | 🔴 | 0.0000 | 0.5000 | Introduction |
| `Q_QASP_783` | `1710.07395` | Experimental Results | 🔴 | 0.0000 | 1.0000 | Annotation Procedure |
| `Q_QASP_784` | `1710.07395` | Logistic Regression Models | 🔴 | 0.4416 | 1.0000 | Abstract |
| `Q_QASP_785` | `1710.07395` | Logistic Regression Models | 🔴 | 0.2891 | 1.0000 | Annotation Procedure |
| `Q_QASP_786` | `1710.07395` | Annotation Guidelines | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_787` | `1710.07395` | Neural Network Models | 🟢 | 1.0000 | 1.0000 | Neural Network Models |
| `Q_QASP_253` | `1912.05066` | Introduction | 🔴 | 0.1846 | 0.5000 | Methodology ::: Machine Learning Models |
| `Q_QASP_255` | `1912.05066` | Introduction | 🔴 | 0.4423 | 1.0000 | Data Analysis |
| `Q_QASP_256` | `1912.05066` | Introduction | 🔴 | 0.1846 | 0.5000 | Conclusions |
| `Q_QASP_257` | `1912.05066` | Methodology ::: Procedure | 🔴 | 0.2997 | 0.6667 | Data Analysis |
| `Q_QASP_059` | `2003.12218` | Results ::: NER Annotation Results | 🔴 | 0.0000 | 1.0000 | Conclusion |
| `Q_QASP_060` | `2003.12218` | Introduction | 🔴 | 0.3434 | 1.0000 | Conclusion |
| `Q_QASP_316` | `1908.10449` | Introduction | 🔴 | 0.2891 | 1.0000 | Abstract |
| `Q_QASP_317` | `1908.10449` | iMRC: Making MRC Interactive | 🔴 | 0.0000 | 0.8000 | Introduction |
| `Q_QASP_318` | `1908.10449` | Introduction | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_319` | `1908.10449` | iMRC: Making MRC Interactive ::: Ac | 🔴 | 0.0000 | 0.6667 | Abstract |
| `Q_QASP_031` | `1811.00942` | Experimental Setup | 🔴 | 0.0000 | 1.0000 | Conclusion |
| `Q_QASP_032` | `1811.00942` | Introduction | 🔴 | 0.2372 | 1.0000 | Abstract |
| `Q_QASP_033` | `1811.00942` | Introduction | 🔴 | 0.4307 | 1.0000 | Infrastructure |
| `Q_QASP_767` | `1606.05286` | Experimental results | 🔴 | 0.6509 | 1.0000 | Abstract |
| `Q_QASP_637` | `1808.00265` | Results | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_638` | `1808.00265` | Results | 🔴 | 0.2891 | 1.0000 | Conclusions |
| `Q_QASP_639` | `1808.00265` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_083` | `1910.03042` | Analysis | 🟢 | 0.1301 | 0.7500 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_084` | `1910.03042` | Analysis ::: Response Depth: Mean W | 🟢 | 1.0000 | 1.0000 | Analysis ::: Response Depth: Mean Word C |
| `Q_QASP_085` | `1910.03042` | System Architecture | 🔴 | 0.3066 | 1.0000 | Abstract |
| `Q_QASP_086` | `1910.03042` | System Architecture | 🔴 | 0.0000 | 0.5000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_087` | `1910.03042` | Analysis | 🟢 | 0.3869 | 0.5000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_088` | `1910.03042` | Analysis ::: Response Depth: Mean W | 🔴 | 0.1357 | 1.0000 | Analysis ::: Interleaving Personal and F |
| `Q_QASP_469` | `1911.00069` | Experiments ::: Source (English) RE | 🔴 | 0.6131 | 1.0000 | Experiments ::: Cross-Lingual RE Perform |
| `Q_QASP_470` | `1911.00069` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_471` | `1911.00069` | Experiments ::: Datasets | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_472` | `1911.00069` | Experiments ::: Datasets | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_772` | `1906.10519` | Setting for Experiment 1: Sentence- | 🟢 | 0.0000 | 0.0000 | Setting for Experiment 1: Sentence-level |
| `Q_QASP_649` | `1906.07668` | Visualization | 🔴 | 0.2044 | 0.5000 | Conclusions |
| `Q_QASP_704` | `1607.06275` | WebQA Dataset | 🔴 | 0.0000 | 0.0000 | Baselines |
| `Q_QASP_705` | `1607.06275` | Introduction | 🔴 | 0.8072 | 1.0000 | Baselines |
| `Q_QASP_706` | `1607.06275` | WebQA Dataset | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_152` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_153` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_154` | `1910.07181` | Evaluation ::: Downstream Task Data | 🟢 | 0.5641 | 1.0000 | Evaluation ::: Downstream Task Datasets |
| `Q_QASP_155` | `1910.07181` | Evaluation ::: WNLaMPro | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_444` | `1812.07023` | Experiments | 🔴 | 0.3066 | 1.0000 | Abstract |
| `Q_QASP_010` | `2003.07723` | Introduction | 🟢 | 0.4685 | 1.0000 | Introduction |
| `Q_QASP_011` | `2003.07723` | Expert Annotation ::: Agreement | 🔴 | 0.0000 | 0.0000 | Crowdsourcing Annotation |
| `Q_QASP_012` | `2003.07723` | Introduction | 🔴 | 0.3066 | 1.0000 | ::: ::: |
| `Q_QASP_407` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_408` | `1902.06843` | Multi-modal Prediction Framework | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_409` | `1902.06843` | Demographic Prediction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_410` | `1902.06843` | Data Modality Analysis | 🟢 | 0.3301 | 0.2727 | Data Modality Analysis |
| `Q_QASP_411` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.5000 | Untitled Section |
| `Q_QASP_412` | `1902.06843` | Dataset | 🔴 | 0.0000 | 0.2000 | Untitled Section |
| `Q_QASP_413` | `1902.06843` | Introduction | 🔴 | 0.3155 | 1.0000 | Untitled Section |
| `Q_QASP_414` | `1902.06843` | Introduction | 🔴 | 0.3869 | 1.0000 | Demographic Prediction |
| `Q_QASP_415` | `1902.06843` | Introduction | 🔴 | 0.0000 | 0.0000 | Demographic Prediction |
| `Q_QASP_585` | `1606.02006` | Settings | 🔴 | 0.0000 | 0.0000 | Hybrid Lexicons |
| `Q_QASP_586` | `1606.02006` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_779` | `2003.05995` | Introduction | 🔴 | 0.0000 | 0.2500 | Abstract |
| `Q_QASP_780` | `2003.05995` | Related Work | 🟢 | 0.6819 | 0.6667 | Related Work |
| `Q_QASP_781` | `2003.05995` | Data Analysis | 🔴 | 0.2588 | 0.3077 | Introduction |
| `Q_QASP_782` | `2003.05995` | System Overview | 🔴 | 0.3591 | 1.0000 | Abstract |
| `Q_QASP_013` | `1705.09665` | Applying the typology to Reddit | 🔴 | 0.2641 | 0.5000 | Community-type and user tenure |
| `Q_QASP_014` | `1705.09665` | Community-type and monthly retentio | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_015` | `1705.09665` | Introduction | 🟢 | 0.0000 | 0.6667 | Introduction |
| `Q_QASP_016` | `1705.09665` | Applying the typology to Reddit | 🔴 | 0.1772 | 1.0000 | Introduction |
| `Q_QASP_017` | `1705.09665` | Community-level measures | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_018` | `1705.09665` | Community-level measures | 🔴 | 0.4307 | 1.0000 | Community identity and acculturation |
| `Q_QASP_063` | `2003.06651` | Related Work | 🟢 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_064` | `2003.06651` | Evaluation ::: Word Sense Disambigu | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_065` | `2003.06651` | Evaluation | 🔴 | 0.0000 | 1.0000 | Conclusions and Future Work |
| `Q_QASP_422` | `1910.02789` | Semantic State Representations in t | 🔴 | 0.4413 | 1.0000 | Abstract |
| `Q_QASP_425` | `1910.02789` | Semantic State Representations in t | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_426` | `1910.02789` | Introduction | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_160` | `1909.00542` | Classification vs. Regression Exper | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_161` | `1909.00542` | Classification vs. Regression Exper | 🔴 | 0.0000 | 1.0000 | Conclusions |
| `Q_QASP_162` | `1909.00542` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_748` | `1909.01013` | Approach ::: Regularizers for Dual  | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_749` | `1909.01013` | Experiments ::: Comparison with the | 🔴 | 0.3155 | 1.0000 | Introduction |
| `Q_QASP_750` | `1909.01013` | Introduction | 🟢 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_752` | `1909.01013` | Experiments ::: The Effectiveness o | 🔴 | 0.2372 | 1.0000 | Experiments ::: Comparison with the Stat |
| `Q_QASP_753` | `1909.01013` | Experiments ::: Comparison with the | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_613` | `1803.03664` | Experiments and Results | 🔴 | 0.0000 | 1.0000 | Question Generation |
| `Q_QASP_467` | `1708.09157` | Character-Level Neural Transfer | 🔴 | 0.2184 | 1.0000 | Abstract |
| `Q_QASP_468` | `1708.09157` | Datasets | 🔴 | 0.0000 | 0.0000 | Experimental Languages |
| `Q_QASP_244` | `1907.02030` | Choosing an embedding | 🟢 | 0.0000 | 0.0000 | Choosing an embedding |
| `Q_QASP_245` | `1907.02030` | Related Work | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_246` | `1907.02030` | Choosing an embedding | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_170` | `1905.11901` | Data and Preprocessing | 🔴 | 0.1301 | 0.7500 | Hyperparameters |
| `Q_QASP_171` | `1905.11901` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_172` | `1905.11901` | Results | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_173` | `1905.11901` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_512` | `1904.08386` | Embedding city descriptions | 🟢 | 0.8772 | 1.0000 | Embedding city descriptions |
| `Q_QASP_513` | `1904.08386` | Introduction | 🔴 | 0.3333 | 1.0000 | Conclusion |
| `Q_QASP_514` | `1904.08386` | Clustering city representations | 🟢 | 0.8772 | 1.0000 | Clustering city representations |
| `Q_QASP_383` | `1911.01799` | Introduction | 🔴 | 0.1934 | 1.0000 | Experiments on speaker recognition ::: S |
| `Q_QASP_492` | `1910.05456` | Experimental Design ::: Target Lang | 🔴 | 0.1131 | 0.4000 | Experimental Design ::: Source Languages |
| `Q_QASP_493` | `1910.05456` | Experimental Design ::: Target Lang | 🔴 | 0.0000 | 0.0000 | Qualitative Results ::: Miscellaneous Er |
| `Q_QASP_494` | `1910.05456` | Introduction | 🔴 | 0.1952 | 0.5000 | Quantitative Results |
| `Q_QASP_495` | `1910.05456` | Introduction | 🔴 | 0.2372 | 1.0000 | Related Work ::: Acquisition of morpholo |
| `Q_QASP_049` | `1810.04528` | Portuguese Embedding | 🟢 | 0.6589 | 1.0000 | Portuguese Embedding |
| `Q_QASP_050` | `1810.04528` | Portuguese Embedding | 🟢 | 0.8503 | 1.0000 | Portuguese Embedding |
| `Q_QASP_644` | `1910.05608` | Introduction | 🔴 | 0.1815 | 0.6667 | System description ::: Data pre-processi |
| `Q_QASP_645` | `1910.05608` | System description ::: System overv | 🟢 | 0.5791 | 1.0000 | System description ::: System overview |
| `Q_QASP_646` | `1910.05608` | Experiment | 🔴 | 0.3066 | 0.5000 | Abstract |
| `Q_QASP_647` | `1910.05608` | Experiment | 🔴 | 0.3066 | 0.5000 | Abstract |
| `Q_QASP_648` | `1910.05608` | System description ::: System overv | 🔴 | 0.3045 | 1.0000 | System description ::: Data pre-processi |
| `Q_QASP_045` | `1912.02481` | Semantic Representations ::: Experi | 🔴 | 0.1815 | 0.3333 | Abstract |
| `Q_QASP_047` | `1912.02481` | Semantic Representations ::: Experi | 🔴 | 0.0000 | 0.0000 | Semantic Representations |
| `Q_QASP_055` | `2003.07433` | Experimental Evaluation ::: Results | 🔴 | 0.2658 | 0.6667 | Introduction |
| `Q_QASP_056` | `2003.07433` | Twitter-based PTSD Detection ::: PT | 🔴 | 0.3072 | 0.7500 | LAXARY: Explainable PTSD Detection Model |
| `Q_QASP_057` | `2003.07433` | Twitter-based PTSD Detection ::: Pr | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_058` | `2003.07433` | Twitter-based PTSD Detection ::: Da | 🔴 | 0.3762 | 0.6250 | Abstract |
| `Q_QASP_141` | `1703.05260` | Introduction | 🔴 | 0.5438 | 1.0000 | Development of the Schema |
| `Q_QASP_142` | `1703.05260` | First Annotation Phase | 🟢 | 1.0000 | 1.0000 | First Annotation Phase |
| `Q_QASP_522` | `1906.04571` | Introduction | 🟢 | 0.7977 | 1.0000 | Introduction |
| `Q_QASP_523` | `1906.04571` | Extrinsic Evaluation | 🟢 | 0.0000 | 0.0000 | Extrinsic Evaluation |
| `Q_QASP_524` | `1906.04571` | Conclusion | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_529` | `1809.07629` | Setup | 🟢 | 1.0000 | 1.0000 | Setup |
| `Q_QASP_530` | `1809.07629` | Setup | 🔴 | 0.0000 | 0.0000 | Attentional Hierarchical Decoder |
| `Q_QASP_320` | `1910.03814` | Methodology ::: Multimodal Architec | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_322` | `1910.03814` | The MMHS150K dataset | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_323` | `1910.03814` | Results | 🟢 | 0.0000 | 1.0000 | Results |
| `Q_QASP_324` | `1910.03814` | Results | 🔴 | 0.3422 | 0.5000 | Abstract |
| `Q_QASP_325` | `1910.03814` | Results | 🟢 | 1.0000 | 1.0000 | Results |
| `Q_QASP_326` | `1910.03814` | The MMHS150K dataset ::: Tweets Gat | 🟢 | 1.0000 | 1.0000 | The MMHS150K dataset ::: Tweets Gatherin |
| `Q_QASP_327` | `1910.03814` | The MMHS150K dataset | 🔴 | 0.4307 | 1.0000 | Related Work ::: Hate Speech Detection |
| `Q_QASP_328` | `1910.03814` | Methodology ::: Unimodal Treatment  | 🔴 | 0.3707 | 1.0000 | Abstract |
| `Q_QASP_329` | `1910.03814` | Methodology ::: Multimodal Architec | 🔴 | 0.2891 | 1.0000 | Results |
| `Q_QASP_330` | `1910.03814` | The MMHS150K dataset ::: Annotation | 🔴 | 0.0000 | 0.0000 | Related Work ::: Hate Speech Detection |
| `Q_QASP_436` | `1909.00279` | Experiment ::: Interpoetry: Generat | 🔴 | 0.1175 | 0.7500 | Abstract |
| `Q_QASP_437` | `1909.00279` | Experiment ::: Reborn Poems: Genera | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_438` | `1909.00279` | Experiment ::: Datasets | 🔴 | 0.4307 | 1.0000 | Experiment |
| `Q_QASP_665` | `2003.06279` | Conclusion | 🔴 | 0.5438 | 1.0000 | Abstract |
| `Q_QASP_666` | `2003.06279` | Introduction | 🔴 | 0.2021 | 1.0000 | Abstract |
| `Q_QASP_667` | `2003.06279` | Introduction | 🔴 | 0.0000 | 1.0000 | Related works |
| `Q_QASP_668` | `2003.06279` | Introduction | 🔴 | 0.0000 | 0.5000 | Results and Discussion ::: Effects of co |
| `Q_QASP_297` | `1702.06378` | Multitask Learning Results | 🔴 | 0.6241 | 1.0000 | Abstract |
| `Q_QASP_777` | `1806.04535` | Puns | 🟢 | 1.0000 | 1.0000 | Puns |
| `Q_QASP_778` | `1806.04535` | Introduction | 🔴 | 0.4708 | 1.0000 | Dataset |
| `Q_QASP_298` | `1903.03467` | Conclusions | 🟢 | 0.8772 | 1.0000 | Conclusions |
| `Q_QASP_299` | `1903.03467` | Introduction | 🔴 | 0.2021 | 0.3333 | Abstract |
| `Q_QASP_300` | `1903.03467` | Quantitative Results | 🔴 | 0.1510 | 0.7500 | Abstract |
| `Q_QASP_301` | `1903.03467` | Experiments & Results | 🔴 | 0.4030 | 1.0000 | Abstract |
| `Q_QASP_302` | `1903.03467` | Black-Box Knowledge Injection | 🟢 | 0.4693 | 0.6667 | Black-Box Knowledge Injection |
| `Q_QASP_381` | `1909.00088` | Introduction | 🔴 | 0.6309 | 1.0000 | Evaluation ::: Semantic Text Exchange Sc |
| `Q_QASP_382` | `1909.00088` | Introduction | 🔴 | 0.3010 | 1.0000 | Abstract |
| `Q_QASP_066` | `1910.04269` | Related Work | 🔴 | 0.0000 | 0.0000 | Proposed Method ::: Model Details: 1D Co |
| `Q_QASP_067` | `1910.04269` | Related Work | 🟢 | 0.3155 | 1.0000 | Related Work |
| `Q_QASP_226` | `1911.09886` | Experiments ::: Datasets | 🟢 | 0.6131 | 1.0000 | Experiments ::: Datasets |
| `Q_QASP_227` | `1911.09886` | Experiments ::: Experimental Result | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_228` | `1911.09886` | Experiments ::: Baselines and Evalu | 🔴 | 0.1012 | 0.5556 | Abstract |
| `Q_QASP_229` | `1911.09886` | Experiments ::: Experimental Result | 🟢 | 1.0000 | 1.0000 | Experiments ::: Experimental Results |
| `Q_QASP_735` | `1908.10275` | Experiments | 🔴 | 0.0000 | 0.0000 | Motivation, Background and Related Work |
| `Q_QASP_736` | `1908.10275` | Data Description | 🔴 | 0.0000 | 0.0000 | Brief introduction to popular music |
| `Q_QASP_737` | `1908.10275` | Data Description | 🔴 | 0.5000 | 1.0000 | Brief introduction to popular music |
| `Q_QASP_533` | `2002.11402` | Data Preparation | 🟢 | 0.7670 | 1.0000 | Data Preparation |
| `Q_QASP_230` | `1611.01400` | Baseline Systems | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_231` | `1611.01400` | Learning to Rank | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_232` | `1611.01400` | Benchmark Datasets | 🔴 | 0.0000 | 0.0000 | Features |
| `Q_QASP_233` | `1611.01400` | Benchmark Datasets | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_001` | `1608.06757` | Evaluation Set Up | 🟢 | 0.8503 | 1.0000 | Evaluation Set Up |
| `Q_QASP_698` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.3816 | 1.0000 | Introduction |
| `Q_QASP_699` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.2346 | 0.3333 | Results |
| `Q_QASP_700` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.2184 | 1.0000 | Discussion |
| `Q_QASP_701` | `1604.05781` | Introduction | 🔴 | 0.3869 | 1.0000 | Results |
| `Q_QASP_702` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_703` | `1604.05781` | Dataset, filtering, and corpus sele | 🔴 | 0.1815 | 0.3333 | Tagging and corpus comparison |
| `Q_QASP_428` | `2001.07209` | Emerging NLP research on morality | 🔴 | 0.3155 | 1.0000 | Applications to diachronic morality :::  |
| `Q_QASP_429` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.0000 | 0.5000 | Applications to diachronic morality :::  |
| `Q_QASP_430` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.2346 | 0.6667 | Abstract |
| `Q_QASP_431` | `2001.07209` | A three-tier modelling framework :: | 🔴 | 0.0000 | 0.5000 | Applications to diachronic morality :::  |
| `Q_QASP_432` | `2001.07209` | A three-tier modelling framework | 🟢 | 0.2184 | 1.0000 | A three-tier modelling framework ::: Mod |
| `Q_QASP_773` | `1905.13413` | Iterative Learning | 🔴 | 0.4632 | 1.0000 | Problem Formulation |
| `Q_QASP_774` | `1905.13413` | Model Architecture and Decoding | 🔴 | 0.6309 | 1.0000 | Evaluation Results |
| `Q_QASP_137` | `1908.08419` | Information Entropy Based Scoring M | 🟢 | 0.8066 | 1.0000 | Information Entropy Based Scoring Model |
| `Q_QASP_138` | `1908.08419` | Active Learning for Chinese Word Se | 🔴 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_139` | `1908.08419` | Information Entropy Based Scoring M | 🟢 | 0.8316 | 1.0000 | Information Entropy Based Scoring Model |
| `Q_QASP_387` | `1905.08949` | Wider Input Modalities | 🔴 | 0.1564 | 0.3333 | Generation of Deep Questions |
| `Q_QASP_388` | `1905.08949` | Learning Paradigm | 🔴 | 0.1413 | 0.6667 | Abstract |
| `Q_QASP_389` | `1905.08949` | Input Modality | 🟢 | 0.8503 | 1.0000 | Input Modality |
| `Q_QASP_515` | `1909.00754` | Experimental Setting | 🟢 | 0.6131 | 0.5000 | Experimental Setting |
| `Q_QASP_516` | `1909.00754` | Experimental Setting | 🔴 | 0.0000 | 0.0000 | Implementation Details |
| `Q_QASP_462` | `1710.06536` | Introduction | 🔴 | 0.2372 | 0.5000 | Aspect-Based Sentiment Analysis |
| `Q_QASP_384` | `1812.06705` | Datasets | 🟢 | 0.7977 | 1.0000 | Datasets |
| `Q_QASP_385` | `1812.06705` | Text classification | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_386` | `1812.06705` | Text classification | 🟢 | 0.4307 | 1.0000 | Text classification |
| `Q_QASP_650` | `1605.04655` | Sentence Embeddings | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_651` | `1605.04655` | Evaluation | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_653` | `1605.04655` | Introduction | 🔴 | 0.2736 | 0.4118 | Conclusion |
| `Q_QASP_683` | `1904.07342` | Data | 🟢 | 1.0000 | 1.0000 | Data |
| `Q_QASP_684` | `1904.07342` | Results & Discussion | 🔴 | 0.0000 | 0.0000 | Data |
| `Q_QASP_685` | `1904.07342` | Labeling Methodology | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_686` | `1904.07342` | Data | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_687` | `1904.07342` | Data | 🟢 | 0.3066 | 1.0000 | Data |
| `Q_QASP_792` | `1907.02636` | Results | 🟢 | 1.0000 | 1.0000 | Results |
| `Q_QASP_793` | `1907.02636` | Contextual Features | 🟢 | 0.2891 | 1.0000 | Analysis of Contextual Features |
| `Q_QASP_794` | `1907.02636` | Datasets | 🟢 | 1.0000 | 1.0000 | Datasets |
| `Q_QASP_122` | `1909.09491` | Plackett-Luce Model in Statistical  | 🔴 | 0.4162 | 0.6667 | Abstract |
| `Q_QASP_124` | `1909.09491` | Introduction | 🔴 | 0.2694 | 1.0000 | Abstract |
| `Q_QASP_618` | `1902.09087` | Introduction | 🟢 | 0.5587 | 0.3636 | Introduction |
| `Q_QASP_619` | `1902.09087` | Evaluation Metrics | 🟢 | 1.0000 | 1.0000 | Evaluation Metrics |
| `Q_QASP_620` | `1902.09087` | Introduction | 🔴 | 0.4704 | 0.4000 | Results |
| `Q_QASP_623` | `1907.01413` | Future Work | 🔴 | 0.3869 | 1.0000 | Results and Discussion |
| `Q_QASP_624` | `1907.01413` | Ultrasound Data | 🟢 | 0.6131 | 1.0000 | Ultrasound Data |
| `Q_QASP_625` | `1907.01413` | Preprocessing and Model Architectur | 🔴 | 0.2184 | 0.5000 | Conclusion |
| `Q_QASP_626` | `1907.01413` | Data Selection | 🔴 | 0.0000 | 1.0000 | Ultrasound Data |
| `Q_QASP_627` | `1907.01413` | Preprocessing and Model Architectur | 🟢 | 0.8175 | 1.0000 | Preprocessing and Model Architectures |
| `Q_QASP_628` | `1907.01413` | Ultrasound Data | 🟢 | 0.6131 | 0.5000 | Ultrasound Data |
| `Q_QASP_312` | `1909.00430` | Expectation Regularization (XR) | 🔴 | 0.5110 | 1.0000 | Introduction |
| `Q_QASP_174` | `1912.01252` | Introduction ::: Objective | 🔴 | 0.3066 | 0.5000 | Conclusion |
| `Q_QASP_177` | `1912.01252` | Mining opinions and beliefs from te | 🟢 | 0.3869 | 1.0000 | Mining opinions and beliefs from texts : |
| `Q_QASP_573` | `1606.05320` | Methods | 🔴 | 0.2901 | 1.0000 | Introduction |
| `Q_QASP_574` | `1606.05320` | Experiments | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_575` | `1606.05320` | Introduction | 🔴 | 0.1175 | 1.0000 | Abstract |
| `Q_QASP_459` | `1907.00758` | Data | 🔴 | 0.6309 | 1.0000 | Dividing samples for training, validatio |
| `Q_QASP_460` | `1907.00758` | Model | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_461` | `1907.00758` | Model | 🔴 | 0.5912 | 1.0000 | Introduction |
| `Q_QASP_292` | `1910.11769` | Introduction | 🔴 | 0.0000 | 1.0000 | Benchmarks ::: Fine-tuned BERT |
| `Q_QASP_293` | `1910.11769` | Dataset ::: Plutchik’s Wheel of Emo | 🔴 | 0.4306 | 1.0000 | Dataset ::: Mechanical Turk (MTurk) |
| `Q_QASP_294` | `1910.11769` | Benchmarks ::: Bag-of-Words-based B | 🔴 | 1.0000 | 1.0000 | Abstract |
| `Q_QASP_295` | `1910.11769` | Dataset ::: Dataset Statistics | 🟢 | 1.0000 | 1.0000 | Dataset ::: Dataset Statistics |
| `Q_QASP_296` | `1910.11769` | Dataset ::: Mechanical Turk (MTurk) | 🟢 | 1.0000 | 1.0000 | Dataset ::: Mechanical Turk (MTurk) |
| `Q_QASP_599` | `1911.11744` | Results | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_600` | `1911.11744` | Results | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_601` | `1911.11744` | Results | 🔴 | 0.0000 | 0.3333 | Abstract |
| `Q_QASP_545` | `2004.03034` | Results and Analysis | 🟢 | 0.5438 | 1.0000 | Results and Analysis |
| `Q_QASP_546` | `2004.03034` | Methodology ::: Baseline Models ::: | 🔴 | 0.4685 | 1.0000 | Abstract |
| `Q_QASP_547` | `2004.03034` | Dataset | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_548` | `2004.03034` | Dataset | 🔴 | 0.4307 | 1.0000 | Introduction |
| `Q_QASP_307` | `1909.13375` | Related Work | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_308` | `1909.13375` | Model ::: Multi-Span Head | 🟢 | 0.6131 | 0.5000 | Model ::: Multi-Span Head |
| `Q_QASP_309` | `1909.13375` | Results and Discussion ::: Performa | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_310` | `1909.13375` | Related Work | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_074` | `1712.09127` | weGAN: Training cross-corpus word e | 🟢 | 0.0000 | 1.0000 | weGAN: Training cross-corpus word embedd |
| `Q_QASP_075` | `1712.09127` | The CNN data set | 🔴 | 0.0000 | 0.0000 | deGAN: Generating document embeddings fo |
| `Q_QASP_076` | `1712.09127` | Experiments | 🟢 | 1.0000 | 1.0000 | Experiments |
| `Q_QASP_483` | `1809.05752` | Future Work and Conclusion | 🟢 | 1.0000 | 1.0000 | Future Work and Conclusion |
| `Q_QASP_484` | `1809.05752` | Data | 🔴 | 0.3911 | 0.6667 | Related Work |
| `Q_QASP_730` | `1602.08741` | Acquiring data | 🔴 | 0.1396 | 0.4118 | Determining optimal corpus size |
| `Q_QASP_760` | `1910.10408` | Introduction | 🔴 | 0.2044 | 0.5000 | Results ::: Human Evaluation and Analysi |
| `Q_QASP_761` | `1910.10408` | Experiments ::: Data and Settings | 🔴 | 0.6934 | 1.0000 | Results |
| `Q_QASP_762` | `1910.10408` | Introduction | 🔴 | 0.5599 | 0.6000 | Background ::: Transformer |
| `Q_QASP_763` | `1910.10408` | Introduction | 🔴 | 0.1795 | 0.2308 | Abstract |
| `Q_QASP_764` | `1910.10408` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_765` | `1910.10408` | Experiments ::: Data and Settings | 🔴 | 0.4228 | 1.0000 | Related works |
| `Q_QASP_766` | `1910.10408` | Introduction | 🔴 | 0.7484 | 0.8889 | Methods ::: Combining the two methods |
| `Q_QASP_427` | `1902.00672` | Detection of hypergraph transversal | 🔴 | 0.0000 | 0.0000 | Comparison with DUC systems |
| `Q_QASP_248` | `1910.04601` | Baseline RC-QED@!START@$^{\rm E}$@! | 🔴 | 0.4228 | 1.0000 | Introduction |
| `Q_QASP_249` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_250` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.3333 | 1.0000 | Data collection for RC-QED@!START@$^{\rm |
| `Q_QASP_251` | `1910.04601` | Data collection for RC-QED@!START@$ | 🔴 | 0.0000 | 0.0000 | Related work ::: RC datasets with explan |
| `Q_QASP_395` | `1603.01417` | Input Module for Text QA | 🔴 | 0.3010 | 1.0000 | Conclusion |
| `Q_QASP_396` | `1603.01417` | Introduction | 🔴 | 0.0000 | 1.0000 | Comparison to state of the art using bAb |
| `Q_QASP_397` | `1603.01417` | Input Module for Text QA | 🔴 | 0.0000 | 0.5000 | Datasets |
| `Q_QASP_398` | `1603.01417` | Introduction | 🔴 | 0.2184 | 1.0000 | Improved Dynamic Memory Networks: DMN+ |
| `Q_QASP_399` | `1603.01417` | Conclusion | 🔴 | 0.2891 | 1.0000 | Introduction |
| `Q_QASP_400` | `1603.01417` | Conclusion | 🔴 | 0.0000 | 1.0000 | Comparison to state of the art using VQA |
| `Q_QASP_800` | `1908.11425` | Methods ::: Speech-to-text translat | 🔴 | 0.6131 | 1.0000 | Experimental Setup ::: Fine-grained topi |
| `Q_QASP_801` | `1908.11425` | Experimental Setup ::: Data. | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_167` | `1909.02764` | Results ::: Facial Expressions and  | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_168` | `1909.02764` | Methods ::: Emotion Recognition fro | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1909.02764` | Methods ::: Emotion Recognition fro | 🔴 | 0.1564 | 0.6667 | Abstract |
| `Q_QASP_463` | `1701.02877` | Datasets | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_496` | `1910.05154` | Experiments | 🟢 | 0.6131 | 1.0000 | Experiments |
| `Q_QASP_497` | `1910.05154` | Experiments | 🟢 | 0.9197 | 1.0000 | Experiments |
| `Q_QASP_498` | `1910.05154` | Experiments | 🟢 | 0.5856 | 1.0000 | Experiments |
| `Q_QASP_499` | `1910.05154` | Methodology ::: Bilingual Unsupervi | 🔴 | 0.5995 | 1.0000 | Conclusion |
| `Q_QASP_500` | `1910.05154` | Conclusion | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_201` | `1703.04617` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_202` | `1703.04617` | Results | 🔴 | 0.2184 | 1.0000 | Conclusions |
| `Q_QASP_203` | `1703.04617` | The Baseline Model | 🟢 | 0.5000 | 1.0000 | The Baseline Model |
| `Q_QASP_204` | `1703.04617` | Results | 🔴 | 0.5000 | 1.0000 | Set-Up |
| `Q_QASP_549` | `1910.12618` | Presentation of the data ::: Text | 🔴 | 0.0000 | 0.0000 | Modeling and forecasting framework ::: H |
| `Q_QASP_550` | `1910.12618` | Experiments ::: Interpretability of | 🟢 | 0.1846 | 0.5000 | Experiments ::: Interpretability of the  |
| `Q_QASP_551` | `1910.12618` | Experiments ::: Interpretability of | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_552` | `1910.12618` | Introduction | 🔴 | 0.1480 | 0.3333 | Modeling and forecasting framework ::: N |
| `Q_QASP_390` | `1909.00170` | Introduction | 🔴 | 0.0000 | 1.0000 | Model |
| `Q_QASP_391` | `1909.00170` | Off-the-shelf NE Recognition System | 🟢 | 0.6131 | 0.5000 | Off-the-shelf NE Recognition Systems |
| `Q_QASP_474` | `1910.04887` | Methods ::: Data and Training Detai | 🔴 | 0.6934 | 1.0000 | Abstract |
| `Q_QASP_475` | `1910.04887` | Methods ::: Modifying FactorCell LS | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_606` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.6309 | 1.0000 | Dataset |
| `Q_QASP_607` | `1911.00523` | Predicting Pointers ::: Experiment  | 🔴 | 0.2961 | 0.3333 | Predicting Pointers ::: Prediction Perfo |
| `Q_QASP_608` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.1786 | 0.5000 | Predicting Pointers |
| `Q_QASP_609` | `1911.00523` | Predicting Pointers ::: Experiment  | 🔴 | 0.8175 | 1.0000 | Predicting Pointers ::: Prediction Perfo |
| `Q_QASP_610` | `1911.00523` | Predicting Pointers ::: Experiment  | 🟢 | 1.0000 | 1.0000 | Predicting Pointers ::: Experiment setup |
| `Q_QASP_611` | `1911.00523` | Concluding Discussions | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_612` | `1911.00523` | Understanding the Pointers in Expla | 🔴 | 0.1786 | 0.5000 | Predicting Pointers |
| `Q_QASP_535` | `2002.00652` | Experiment & Analysis ::: Experimen | 🔴 | 0.3869 | 0.5000 | Abstract |
| `Q_QASP_536` | `2002.00652` | Introduction | 🔴 | 0.7328 | 1.0000 | Experiment & Analysis ::: Experimental S |
| `Q_QASP_537` | `2002.00652` | Experiment & Analysis ::: Model Com | 🔴 | 0.4306 | 1.0000 | Abstract |
| `Q_QASP_538` | `2002.00652` | Introduction | 🔴 | 0.9060 | 1.0000 | Abstract |
| `Q_QASP_371` | `1706.08032` | Experimental results | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_372` | `1706.08032` | Data Preparation | 🔴 | 0.0000 | 0.0000 | Preprocessing |
| `Q_QASP_373` | `1706.08032` | Data Preparation | 🔴 | 0.6508 | 0.6667 | Experimental results |
| `Q_QASP_374` | `1706.08032` | Data Preparation | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_375` | `1706.08032` | Semantic Rules (SR) | 🟢 | 0.9134 | 1.0000 | Semantic Rules (SR) |
| `Q_QASP_602` | `1910.03467` | Experiments ::: Results ::: Japanes | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_603` | `1910.03467` | Experiments ::: Results ::: Japanes | 🔴 | 0.0000 | 1.0000 | Rare Word translation ::: Reducing Unkno |
| `Q_QASP_569` | `1901.04899` | Methodology | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_570` | `1901.04899` | Methodology | 🟢 | 0.4307 | 1.0000 | Methodology |
| `Q_QASP_571` | `1901.04899` | Experimental Results | 🔴 | 0.3010 | 1.0000 | Methodology |
| `Q_QASP_572` | `1901.04899` | Methodology | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_125` | `2001.05284` | Baseline, Oracle and Direct Models  | 🔴 | 0.4118 | 1.0000 | Introduction |
| `Q_QASP_126` | `2001.05284` | Baseline, Oracle and Direct Models  | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_127` | `2001.05284` | Experiment ::: Dataset | 🔴 | 0.0000 | 1.0000 | Baseline, Oracle and Direct Models ::: B |
| `Q_QASP_519` | `1906.00180` | Unseen lengths | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_690` | `1911.00547` | Data Collection and Annotation | 🔴 | 0.5000 | 1.0000 | Experiments and Results ::: Experimental |
| `Q_QASP_691` | `1911.00547` | Introduction | 🔴 | 0.2372 | 0.5000 | Experiments and Results ::: Experimental |
| `Q_QASP_692` | `1911.00547` | Patterns of Sexual Harassment | 🔴 | 0.0000 | 1.0000 | Conclusions |
| `Q_QASP_313` | `1910.11493` | Baselines ::: Task 2 Baselines :::  | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_722` | `1908.04917` | Compared Methods and Evaluation Pro | 🔴 | 0.1772 | 0.5000 | Attention Visualisation |
| `Q_QASP_723` | `1908.04917` | Introduction | 🔴 | 0.2641 | 0.5000 | Abstract |
| `Q_QASP_724` | `1908.04917` | Tone Prediction Sub-network | 🔴 | 0.1866 | 0.5000 | Abstract |
| `Q_QASP_238` | `1807.03367` | Data Collection | 🔴 | 0.1480 | 0.3333 | The Tourist |
| `Q_QASP_239` | `1807.03367` | Data Collection | 🔴 | 0.2891 | 1.0000 | Dataset Statistics |
| `Q_QASP_240` | `1807.03367` | Introduction | 🔴 | 0.5101 | 0.1739 | Abstract |
| `Q_QASP_241` | `1807.03367` | Results and Discussion | 🔴 | 0.0000 | 0.0000 | Evaluation on Full Setup |
| `Q_QASP_242` | `1807.03367` | Introduction | 🔴 | 0.0000 | 0.0000 | Data Collection |
| `Q_QASP_486` | `2001.01589` | Approach ::: Morphologically Motiva | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_487` | `2001.01589` | Approach | 🔴 | 0.1772 | 0.5000 | Related Work |

---

## 5. Methodology Notes

- **Chunking:** Sliding window (120 words, 25-word overlap) per section.
- **Relevance:** `is_chunk_hit(chunk, paper_arxiv_id, verbatim_evidence_quote,
  evidence_list, τ=0.55)` — containment-based, identical to QASPER harness.
- **Section Hit@1:** Top-1 chunk's `section` heading matches `target_section` from the
  ground-truth annotation (case-insensitive substring match). This is a Method A-specific
  metric that measures coarse-grained retrieval precision at the section level.
- **BM25:** Pure-Python Okapi BM25 (k₁=1.5, b=0.75) with regex tokenisation; no tokenizer
  dependency required.
- **Dense:** SentenceTransformer cosine similarity; falls back to TF-IDF cosine if
  `sentence_transformers` is unavailable.
- **Hybrid RRF:** Reciprocal Rank Fusion of BM25 + Dense ranked lists (k=60).
- **Bootstrap CI:** Paper-level cluster bootstrap (1000 iterations, 95% CI) on nDCG@10.
