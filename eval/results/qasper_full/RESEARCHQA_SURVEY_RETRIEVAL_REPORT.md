# ResearchQA Method A — Survey Section Ground-Truth Retrieval Report

> **Generated:** `2026-10-30T04:13:42.750939 UTC`  
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
| `bm25` | 0.2684 | 0.3562 *(±-0.022 CI)* | 0.3451 | 0.5560 | 0.7402 | 0.1960 |
| `dense` | 0.2732 | 0.3623 *(±-0.022 CI)* | 0.3451 | 0.5600 | 0.7456 | 0.2160 |
| `hybrid_rrf` | 0.2720 | 0.3588 *(±-0.022 CI)* | 0.3480 | 0.5640 | 0.7395 | 0.2080 |

### 2.1 Comparison vs QASPER Held-Out Baselines

| Dataset / Method | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 |
| :--- | :---: | :---: | :---: | :---: |
| QASPER BM25 *(reference)* | 0.3812 | 0.4103 | 0.4521 | 0.8930 |
| QASPER Dense E5 *(reference)* | 0.4952 | 0.5213 | 0.5814 | 0.9256 |
| QASPER Hybrid RRF *(reference)* | 0.5121 | 0.5384 | 0.5991 | 0.9560 |
| **ResearchQA Survey `bm25`** | **0.2684** | **0.3562** | **0.3451** | **0.7402** |
| **ResearchQA Survey `dense`** | **0.2732** | **0.3623** | **0.3451** | **0.7456** |
| **ResearchQA Survey `hybrid_rrf`** | **0.2720** | **0.3588** | **0.3480** | **0.7395** |

---

## 3. Dev / Held-Out Split Breakdown

### Strategy: `bm25`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| dev | 132 | 0.2676 | 0.3607 | 0.3444 | 0.7558 | 0.2121 |
| held_out | 118 | 0.2693 | 0.3511 | 0.3459 | 0.7227 | 0.1780 |

### Strategy: `dense`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| dev | 132 | 0.2624 | 0.3627 | 0.3316 | 0.7568 | 0.2273 |
| held_out | 118 | 0.2853 | 0.3618 | 0.3602 | 0.7331 | 0.2034 |

### Strategy: `hybrid_rrf`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| dev | 132 | 0.2684 | 0.3611 | 0.3504 | 0.7510 | 0.2197 |
| held_out | 118 | 0.2760 | 0.3561 | 0.3453 | 0.7267 | 0.1949 |

---

## 4. Per-Query Detail

### `bm25` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_QASP_001` | `1912.01214` | Experiments ::: Main Results | 🟢 | 0.8175 | 1.0000 | Experiments ::: Main Results |
| `Q_QASP_002` | `1912.01214` | Experiments ::: Main Results | 🔴 | 0.2468 | 0.3333 | Experiments ::: Setup |
| `Q_QASP_004` | `1912.01214` | Experiments ::: Setup ::: Datasets. | 🔴 | 0.0000 | 0.3333 | Approach |
| `Q_QASP_005` | `1810.08699` | Experiments | 🟢 | 0.5873 | 1.0000 | Experiments |
| `Q_QASP_006` | `1810.08699` | Test dataset | 🟢 | 0.6131 | 1.0000 | Test dataset |
| `Q_QASP_007` | `1810.08699` | Test dataset | 🔴 | 0.1413 | 0.6667 | Dataset extraction |
| `Q_QASP_008` | `1609.00425` | Dogmatism data | 🟢 | 0.7977 | 1.0000 | Dogmatism data |
| `Q_QASP_009` | `1609.00425` | Predicting dogmatism | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_010` | `1801.05147` | Data Sets | 🟢 | 0.0000 | 0.0000 | Data Sets |
| `Q_QASP_011` | `1811.00383` | Network | 🔴 | 0.6509 | 1.0000 | Introduction |
| `Q_QASP_012` | `1811.00383` | Languages | 🔴 | 0.5677 | 0.7143 | Abstract |
| `Q_QASP_013` | `1811.00383` | Introduction | 🔴 | 0.0000 | 0.5000 | Addressing Lexical Divergence |
| `Q_QASP_014` | `1909.09067` | Introduction | 🔴 | 0.1564 | 1.0000 | Building a Corpus for Automatic Readabil |
| `Q_QASP_015` | `1909.09067` | Introduction | 🔴 | 0.4855 | 0.8333 | Building a Corpus for Automatic Readabil |
| `Q_QASP_018` | `1704.06194` | Introduction | 🔴 | 0.3869 | 1.0000 | KBQA End-Task Results |
| `Q_QASP_019` | `1704.06194` | Introduction | 🔴 | 0.6364 | 1.0000 | Abstract |
| `Q_QASP_020` | `1909.00512` | Approach ::: Measures of Contextual | 🔴 | 0.1699 | 0.5000 | Abstract |
| `Q_QASP_021` | `1909.00512` | Introduction | 🔴 | 0.0000 | 0.0000 | Approach ::: Measures of Contextuality : |
| `Q_QASP_022` | `2003.03106` | Results ::: Experiment A: NUBes-PHI | 🔴 | 0.0000 | 0.6667 | Materials and Methods ::: Systems ::: BE |
| `Q_QASP_023` | `2003.03106` | Materials and Methods ::: Systems : | 🔴 | 0.1510 | 0.2500 | Materials and Methods |
| `Q_QASP_025` | `2003.03106` | Materials and Methods ::: Data | 🟢 | 0.5842 | 0.8333 | Materials and Methods ::: Data |
| `Q_QASP_026` | `1708.01464` | High Resource Results | 🔴 | 0.6309 | 1.0000 | Low Resource g2p |
| `Q_QASP_027` | `1708.01464` | Baseline | 🔴 | 0.5000 | 1.0000 | Adapted Results |
| `Q_QASP_028` | `1708.01464` | Introduction | 🔴 | 1.0000 | 1.0000 | Evaluation |
| `Q_QASP_029` | `1708.01464` | Data | 🔴 | 0.1128 | 0.7500 | High Resource Results |
| `Q_QASP_030` | `2002.03407` | Introduction | 🔴 | 0.0000 | 0.0000 | Results |
| `Q_QASP_031` | `2002.03407` | Results | 🟢 | 0.7654 | 0.6667 | Results |
| `Q_QASP_032` | `2002.03407` | Experiments | 🟢 | 0.0000 | 0.4286 | Experiments |
| `Q_QASP_033` | `2002.03407` | Introduction | 🔴 | 0.1952 | 1.0000 | Abstract |
| `Q_QASP_034` | `2002.03407` | Explored Approaches for Limited Res | 🔴 | 0.2044 | 0.5000 | Abstract |
| `Q_QASP_035` | `1909.11687` | Introduction | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_036` | `1909.11687` | Experiments ::: Models and Baseline | 🔴 | 0.1934 | 0.5000 | Abstract |
| `Q_QASP_037` | `1605.06083` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_038` | `1605.06083` | Introduction | 🟢 | 0.8066 | 1.0000 | Introduction |
| `Q_QASP_039` | `1605.06083` | Other methods | 🔴 | 0.1301 | 0.5000 | Abstract |
| `Q_QASP_040` | `1605.06083` | Introduction | 🔴 | 0.1131 | 0.6000 | Abstract |
| `Q_QASP_041` | `1804.05918` | Experimental Results | 🔴 | 0.3392 | 0.8000 | Dataset and Preprocessing |
| `Q_QASP_042` | `1804.05918` | Experimental Results | 🔴 | 0.1413 | 1.0000 | Abstract |
| `Q_QASP_043` | `1809.04267` | Introduction | 🔴 | 0.0000 | 0.5000 | Hierarchical seq2seq Generation Model |
| `Q_QASP_044` | `1901.05287` | Results | 🔴 | 0.4312 | 1.0000 | Introduction |
| `Q_QASP_045` | `1612.06685` | Psycholinguistic and Semantic Maps | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_046` | `1612.06685` | Data Collection | 🔴 | 0.4976 | 1.0000 | Abstract |
| `Q_QASP_048` | `1912.04961` | Experiments ::: Model variations | 🟢 | 1.0000 | 1.0000 | Experiments ::: Model variations |
| `Q_QASP_049` | `1912.04961` | Data | 🔴 | 0.6309 | 1.0000 | Acknowledgements |
| `Q_QASP_050` | `1912.04961` | Experiments ::: Model variations | 🔴 | 0.2641 | 1.0000 | Results and Discussion ::: Training Data |
| `Q_QASP_051` | `1910.10781` | Introduction | 🔴 | 0.4297 | 0.6667 | Related work |
| `Q_QASP_052` | `1910.10781` | Introduction | 🟢 | 0.3120 | 1.0000 | Introduction |
| `Q_QASP_053` | `1603.09631` | Dataset Collection Process | 🔴 | 0.3956 | 1.0000 | Dialog Simulation |
| `Q_QASP_054` | `1603.09631` | Dataset Properties | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_055` | `1911.06964` | Experiments | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_056` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.0000 | 1.0000 | Approach |
| `Q_QASP_057` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_058` | `1911.06964` | Experiments ::: Efficiency-accuracy | 🔴 | 0.6309 | 1.0000 | Approach ::: Modeling with autoencoders. |
| `Q_QASP_059` | `2001.02284` | Model ::: Dialogue Modules | 🔴 | 0.0000 | 0.2500 | Related Work |
| `Q_QASP_060` | `2001.02284` | Re-implementation of units with BER | 🔴 | 0.0980 | 0.2000 | Introduction ::: Outline and Contributio |
| `Q_QASP_061` | `2001.02284` | Target Domain & Task Definition | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_062` | `2002.01664` | INTRODUCTION | 🔴 | 0.7877 | 1.0000 | DATASET |
| `Q_QASP_063` | `2002.01664` | POOLING STRATEGIES ::: GhostVLAD po | 🔴 | 0.3183 | 1.0000 | RESULTS ::: Comparison with different po |
| `Q_QASP_064` | `2002.01664` | Introduction | 🟢 | 0.3869 | 0.5000 | INTRODUCTION |
| `Q_QASP_065` | `1808.09111` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_066` | `1808.09111` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_067` | `1808.09111` | Learning & Inference | 🟢 | 0.6131 | 0.5000 | Learning & Inference |
| `Q_QASP_068` | `1906.08593` | Qualitative Comparison | 🟢 | 0.8268 | 0.5556 | Qualitative Comparison |
| `Q_QASP_069` | `1906.08593` | The model | 🔴 | 0.0000 | 1.0000 | Relation to Multi-Head attention |
| `Q_QASP_070` | `1906.08593` | Introduction | 🔴 | 0.2692 | 0.7500 | Abstract |
| `Q_QASP_071` | `1809.00540` | Related Work | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_072` | `1809.00540` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_073` | `2004.03354` | Experiment 1: Biomedical NER ::: Do | 🔴 | 0.2346 | 0.3333 | Abstract |
| `Q_QASP_074` | `1611.04798` | Introduction | 🔴 | 0.0000 | 0.0000 | Neural Machine Translation: Background |
| `Q_QASP_075` | `1611.04798` | Introduction | 🟢 | 0.3333 | 1.0000 | Introduction |
| `Q_QASP_076` | `1611.04798` | Under-resourced Translation | 🟢 | 0.8772 | 1.0000 | Under-resourced Translation |
| `Q_QASP_077` | `1912.13337` | Introduction | 🔴 | 0.0734 | 0.2500 | Abstract |
| `Q_QASP_078` | `1912.13337` | Introduction | 🔴 | 0.2641 | 0.5000 | Related Work |
| `Q_QASP_079` | `1912.13337` | Introduction | 🔴 | 0.0000 | 1.0000 | Results and Findings ::: How well do pre |
| `Q_QASP_080` | `1912.13337` | Introduction | 🔴 | 0.0000 | 0.1111 | Abstract |
| `Q_QASP_081` | `1912.13337` | Introduction | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_082` | `1809.01541` | Our system | 🟢 | 0.7598 | 1.0000 | Our system |
| `Q_QASP_083` | `1809.01541` | Baseline | 🟢 | 0.1772 | 1.0000 | Baseline |
| `Q_QASP_084` | `1809.01541` | Baseline | 🔴 | 0.0000 | 1.0000 | System Description |
| `Q_QASP_085` | `1809.01541` | Baseline | 🔴 | 0.0000 | 1.0000 | System Description |
| `Q_QASP_086` | `1809.01541` | Introduction | 🔴 | 0.0000 | 1.0000 | MSD prediction |
| `Q_QASP_087` | `1809.01541` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
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
| `Q_QASP_101` | `1809.00530` | Introduction | 🔴 | 0.7328 | 1.0000 | Datasets and Experimental Settings |
| `Q_QASP_102` | `1809.00530` | Notations and Model Overview | 🔴 | 0.2372 | 0.5000 | Models for Comparison |
| `Q_QASP_103` | `1809.00530` | Introduction | 🔴 | 0.1815 | 0.3333 | Numerical Results of Figure |
| `Q_QASP_104` | `1809.00530` | Introduction | 🟢 | 0.3127 | 0.7500 | Introduction |
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
| `Q_QASP_116` | `2002.11910` | Introduction | 🔴 | 0.4509 | 1.0000 | Abstract |
| `Q_QASP_117` | `2002.11910` | Model ::: Boundary Assembling Metho | 🔴 | 0.4575 | 1.0000 | Experiments ::: Results and Discussion |
| `Q_QASP_118` | `2002.11910` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_119` | `1909.09587` | Zero-shot Transfer with Multi-BERT  | 🔴 | 0.1021 | 0.6000 | Abstract |
| `Q_QASP_120` | `1909.09587` | Introduction | 🟢 | 0.0000 | 0.4000 | Introduction |
| `Q_QASP_121` | `1909.09587` | Zero-shot Transfer with Multi-BERT | 🔴 | 0.2482 | 0.8000 | What Does Zero-shot Transfer Model Learn |
| `Q_QASP_122` | `1909.09587` | Zero-shot Transfer with Multi-BERT  | 🔴 | 0.0000 | 0.5000 | What Does Zero-shot Transfer Model Learn |
| `Q_QASP_123` | `1802.07862` | Results: SnapCaptions Dataset | 🟢 | 0.2921 | 0.6667 | Results: SnapCaptions Dataset |
| `Q_QASP_124` | `1802.07862` | Baselines | 🔴 | 0.4329 | 0.8333 | Introduction |
| `Q_QASP_125` | `1802.07862` | SnapCaptions Dataset | 🟢 | 0.6509 | 1.0000 | Results: SnapCaptions Dataset |
| `Q_QASP_126` | `1802.07862` | Baselines | 🔴 | 0.0000 | 0.0000 | Results: SnapCaptions Dataset |
| `Q_QASP_127` | `1802.07862` | SnapCaptions Dataset | 🔴 | 0.5013 | 1.0000 | Introduction |
| `Q_QASP_128` | `2004.01853` | Introduction | 🔴 | 0.4307 | 1.0000 | Experimental Setup ::: Datasets ::: GIGA |
| `Q_QASP_129` | `2004.01853` | Results ::: Automatic Evaluation | 🟢 | 0.9197 | 1.0000 | Results ::: Automatic Evaluation |
| `Q_QASP_130` | `1710.03348` | Introduction | 🔴 | 0.2443 | 0.8000 | Abstract |
| `Q_QASP_131` | `1710.03348` | Impact of Attention Mechanism | 🔴 | 0.2372 | 0.5000 | Attention Models |
| `Q_QASP_132` | `1710.03348` | Alignment Quality Impact on Transla | 🔴 | 0.2184 | 0.5000 | Abstract |
| `Q_QASP_133` | `1612.03226` | Expected Gradient Length | 🔴 | 0.6437 | 1.0000 | Variance in the Asymptote |
| `Q_QASP_134` | `1612.03226` | Experiments | 🔴 | 0.0000 | 0.7500 | Introduction |
| `Q_QASP_135` | `1612.03226` | Experiments | 🔴 | 0.4118 | 1.0000 | Similarity between Query Methods |
| `Q_QASP_136` | `1612.03226` | Experiments | 🟢 | 0.0000 | 1.0000 | Experiments |
| `Q_QASP_137` | `1809.02286` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_138` | `1809.01202` | Experiment | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_139` | `1809.01202` | Dataset | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_140` | `1909.02027` | Dataset ::: In-Scope Data Collectio | 🔴 | 0.0000 | 1.0000 | Dataset |
| `Q_QASP_141` | `1909.02027` | Introduction | 🔴 | 0.4693 | 1.0000 | Benchmark Evaluation |
| `Q_QASP_142` | `1909.02027` | Introduction | 🔴 | 0.3869 | 1.0000 | Results ::: Results with oos-train |
| `Q_QASP_143` | `1909.02027` | Dataset | 🔴 | 0.2977 | 0.6667 | Benchmark Evaluation ::: Out-of-Scope Pr |
| `Q_QASP_144` | `1911.02855` | Experiments ::: Paraphrase Identifi | 🔴 | 0.8711 | 1.0000 | Experiments ::: Paraphrase Identificatio |
| `Q_QASP_145` | `1911.02855` | Experiments ::: Named Entity Recogn | 🔴 | 0.9197 | 1.0000 | Experiments ::: Named Entity Recognition |
| `Q_QASP_146` | `1911.02855` | Experiments ::: Part-of-Speech Tagg | 🔴 | 0.3869 | 1.0000 | Experiments ::: Named Entity Recognition |
| `Q_QASP_147` | `1911.02855` | Losses ::: Self-adusting Dice Loss | 🔴 | 0.1461 | 0.4000 | Related Work ::: Data Resample |
| `Q_QASP_148` | `1906.01081` | Introduction | 🔴 | 0.1672 | 1.0000 | Hyperparameters |
| `Q_QASP_149` | `1906.01081` | Human Evaluation | 🔴 | 0.2044 | 0.5000 | Abstract |
| `Q_QASP_150` | `1906.01081` | Correlation Comparison | 🔴 | 0.2372 | 1.0000 | Introduction |
| `Q_QASP_151` | `1611.01576` | Character-level Neural Machine Tran | 🟢 | 1.0000 | 1.0000 | Character-level Neural Machine Translati |
| `Q_QASP_152` | `1611.01576` | Sentiment Classification | 🟢 | 1.0000 | 1.0000 | Sentiment Classification |
| `Q_QASP_153` | `1611.01576` | Model | 🔴 | 0.2641 | 1.0000 | Variants |
| `Q_QASP_154` | `1904.09535` | Experiments | 🔴 | 0.8772 | 1.0000 | Sequence Labeling |
| `Q_QASP_155` | `1904.09535` | Block Zoo | 🟢 | 0.7031 | 0.7500 | Block Zoo |
| `Q_QASP_156` | `1904.09535` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_157` | `1911.03059` | Question Collection and Categories | 🔴 | 0.0000 | 0.0000 | Related Works ::: Research Works Related |
| `Q_QASP_159` | `1706.08198` | Conclusion | 🔴 | 0.6609 | 1.0000 | Introduction |
| `Q_QASP_160` | `1706.08198` | Datasets | 🟢 | 1.0000 | 1.0000 | Datasets |
| `Q_QASP_161` | `1909.08089` | Results and Analysis | 🔴 | 0.1846 | 1.0000 | Introduction |
| `Q_QASP_162` | `1909.08089` | Introduction | 🔴 | 0.2044 | 1.0000 | Extractive summarization |
| `Q_QASP_164` | `1910.09982` | Data | 🔴 | 0.0000 | 0.5000 | Participants and Approaches ::: Teams Pa |
| `Q_QASP_165` | `1910.09982` | Baselines | 🟢 | 1.0000 | 1.0000 | Baselines |
| `Q_QASP_166` | `1609.00559` | Introduction | 🔴 | 0.6309 | 1.0000 | Method |
| `Q_QASP_167` | `1609.00559` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_168` | `1609.00559` | Comparison with Previous Work | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 1.0000 | Decoding the KB Query |
| `Q_QASP_170` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_171` | `1612.02482` | Introduction | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_173` | `1608.01084` | Data Set and Toolkits | 🟢 | 0.0000 | 0.0000 | Data Set and Toolkits |
| `Q_QASP_174` | `1904.10503` | Introduction | 🔴 | 1.0000 | 1.0000 | Conclusion and Future Work |
| `Q_QASP_175` | `1904.10503` | Results | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_176` | `1904.10503` | Entity Linking using Wikidata | 🔴 | 0.2140 | 0.8000 | Abstract |
| `Q_QASP_177` | `1912.01772` | Introduction | 🔴 | 0.4776 | 0.7778 | Abstract |
| `Q_QASP_178` | `1912.01772` | The Resource ::: Additional Annotat | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_179` | `1603.01987` | The medical domain model | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_180` | `1908.06941` | PMI & Matrix Factorization | 🔴 | 0.2339 | 1.0000 | Abstract |
| `Q_QASP_181` | `1908.06941` | Materials | 🔴 | 0.4790 | 1.0000 | Abstract |
| `Q_QASP_182` | `1908.06941` | Results | 🔴 | 0.1772 | 1.0000 | Related Work |
| `Q_QASP_183` | `1908.06941` | Introduction | 🔴 | 0.6934 | 1.0000 | Abstract |
| `Q_QASP_184` | `1702.03856` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_185` | `1702.03856` | Introduction | 🔴 | 0.6332 | 1.0000 | Analysis of challenges from UTD |
| `Q_QASP_186` | `1702.03856` | Dataset | 🔴 | 0.3869 | 1.0000 | Introduction |
| `Q_QASP_187` | `1904.01548` | Related Work | 🔴 | 0.0843 | 0.8750 | Abstract |
| `Q_QASP_188` | `1904.01548` | Related Work | 🔴 | 0.6188 | 0.7500 | Discussion |
| `Q_QASP_189` | `1606.03676` | Corpora | 🔴 | 0.0000 | 0.0000 | Baseline models |
| `Q_QASP_190` | `1606.03676` | Corpora | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_191` | `1802.00396` | Introduction | 🔴 | 0.0000 | 0.0000 | Network Analysis |
| `Q_QASP_192` | `1802.00396` | UN votes and speeches | 🟢 | 0.6131 | 1.0000 | UN votes and speeches |
| `Q_QASP_193` | `1911.03343` | Introduction | 🔴 | 0.3978 | 1.0000 | Abstract |
| `Q_QASP_194` | `1712.00991` | Evaluation of auto-generated summar | 🟢 | 1.0000 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_195` | `1712.00991` | Evaluation of auto-generated summar | 🟢 | 0.9197 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_196` | `1712.00991` | Discovering Clusters within Sentenc | 🔴 | 0.3380 | 0.6667 | Introduction |
| `Q_QASP_197` | `1712.00991` | PA along Attributes | 🔴 | 0.1480 | 1.0000 | Introduction |
| `Q_QASP_198` | `1712.00991` | Sentence Classification | 🔴 | 0.4441 | 1.0000 | Conclusions and Further Work |
| `Q_QASP_199` | `1712.00991` | Dataset | 🔴 | 0.6309 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_200` | `1712.00991` | Dataset | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_201` | `1805.08241` | Experiments | 🔴 | 0.2641 | 1.0000 | Fertility Bounds |
| `Q_QASP_202` | `1907.04433` | Performance | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_204` | `2003.04642` | Framework for MRC Gold Standard Ana | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_205` | `2003.04642` | Application of the Framework ::: Ca | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_206` | `2003.04642` | Introduction | 🔴 | 0.6131 | 1.0000 | Framework for MRC Gold Standard Analysis |
| `Q_QASP_208` | `2001.09215` | Proposed Methodology | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_209` | `1909.07575` | Experiments ::: Baseline Models and | 🔴 | 0.5508 | 1.0000 | Abstract |
| `Q_QASP_210` | `1909.07575` | Our method ::: Training Procedure : | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_211` | `1701.04056` | Interactive Dialog Context LM | 🔴 | 0.2961 | 0.6667 | Results and Analysis |
| `Q_QASP_212` | `1904.07904` | Spoken Question Answering | 🟢 | 1.0000 | 1.0000 | Spoken Question Answering |
| `Q_QASP_213` | `1904.07904` | Results | 🔴 | 0.6509 | 1.0000 | Conclusion |
| `Q_QASP_214` | `1904.07904` | Results | 🔴 | 0.4367 | 0.6667 | Conclusion |
| `Q_QASP_215` | `1904.07904` | Corpus | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_216` | `2003.11645` | Introduction | 🔴 | 1.0000 | 1.0000 | Methodology |
| `Q_QASP_217` | `2003.11645` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_218` | `2003.11645` | Introduction | 🟢 | 0.7904 | 1.0000 | Introduction |
| `Q_QASP_219` | `2003.11645` | Introduction | 🔴 | 0.0000 | 1.0000 | Literature Review |
| `Q_QASP_220` | `1909.02304` | Experiments ::: Results ::: Automat | 🔴 | 0.0000 | 0.4000 | Introduction |
| `Q_QASP_221` | `1909.02304` | Experiments ::: Results ::: Automat | 🔴 | 0.0000 | 0.2857 | Abstract |
| `Q_QASP_222` | `1604.03114` | Modeling Idea Flow | 🔴 | 0.2692 | 0.7500 | Abstract |
| `Q_QASP_223` | `1604.03114` | Debate Dataset: Intelligence Square | 🟢 | 1.0000 | 1.0000 | Debate Dataset: Intelligence Squared |
| `Q_QASP_225` | `2001.03131` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments and Discussions ::: Results  |
| `Q_QASP_226` | `2001.03131` | Proposed Approach | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_227` | `1606.02891` | Baseline System | 🔴 | 0.6053 | 1.0000 | Abstract |
| `Q_QASP_228` | `1803.09123` | Empirical Study | 🔴 | 0.3904 | 0.7500 | Introduction |
| `Q_QASP_229` | `1803.09123` | Discovering Semantically Similar Eq | 🔴 | 0.5205 | 1.0000 | Equation Unit Embeddings |
| `Q_QASP_230` | `1910.01863` | Text Generation ::: Baseline Experi | 🔴 | 0.5337 | 0.7273 | Text Generation |
| `Q_QASP_231` | `1701.08229` | METHODS | 🔴 | 0.4228 | 1.0000 | Feature Elimination |
| `Q_QASP_232` | `1701.08229` | Feature Elimination | 🟢 | 0.8175 | 1.0000 | Feature Elimination |
| `Q_QASP_233` | `1701.08229` | METHODS | 🟢 | 0.9197 | 1.0000 | METHODS |
| `Q_QASP_234` | `1701.08229` | METHODS | 🟢 | 0.6131 | 1.0000 | METHODS |
| `Q_QASP_235` | `1912.06262` | Experiments ::: Results | 🔴 | 0.0000 | 1.0000 | Experiments ::: Hyperparameter Tuning |
| `Q_QASP_236` | `1912.06262` | Experiments ::: Data | 🔴 | 0.2372 | 0.5000 | Abstract |
| `Q_QASP_237` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.7542 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_238` | `1709.07814` | Attention-based Encoder Decoder for | 🔴 | 0.3651 | 1.0000 | Speech Data |
| `Q_QASP_239` | `1709.07814` | Speech Data | 🔴 | 0.1510 | 0.2500 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_240` | `1806.00738` | Model | 🔴 | 0.5317 | 1.0000 | Previous work |
| `Q_QASP_241` | `1806.00738` | Decoder | 🔴 | 0.3127 | 1.0000 | Methodology |
| `Q_QASP_242` | `1806.00738` | Encoder | 🔴 | 0.6053 | 1.0000 | Decoder |
| `Q_QASP_243` | `1806.00738` | Decoder | 🟢 | 0.8316 | 1.0000 | Decoder |
| `Q_QASP_244` | `1811.00147` | Dolores: Learner | 🟢 | 0.6131 | 0.5000 | Dolores: Learner |
| `Q_QASP_245` | `1811.00147` | Dolores: Learner | 🔴 | 0.0000 | 0.2500 | Problem Formulation |
| `Q_QASP_246` | `1610.09225` | Introduction | 🟢 | 0.2382 | 0.8000 | Introduction |
| `Q_QASP_247` | `1610.09225` | Feature Extraction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_248` | `1610.09225` | Data Collection | 🔴 | 0.0000 | 0.5000 | Sentiment Analyzer Results |
| `Q_QASP_249` | `2003.08380` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_250` | `1811.05711` | Multiscale graph partitioning for t | 🔴 | 0.1866 | 0.6667 | Abstract |
| `Q_QASP_251` | `1805.04508` | Gender Bias Results | 🔴 | 0.1357 | 1.0000 | Abstract |
| `Q_QASP_252` | `1805.04508` | The Equity Evaluation Corpus | 🔴 | 0.3191 | 0.7500 | Introduction |
| `Q_QASP_253` | `1904.03288` | Conversational Speech | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_254` | `1904.03288` | Read Speech | 🔴 | 0.5714 | 1.0000 | Introduction |
| `Q_QASP_256` | `1909.13714` | Methodology | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_257` | `1910.05603` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_258` | `1910.05603` | System Description ::: Language Mod | 🟢 | 0.7670 | 1.0000 | System Description ::: Language Model |
| `Q_QASP_259` | `1910.05603` | Experiments ::: System combination | 🔴 | 0.5000 | 1.0000 | Conclusion |
| `Q_QASP_260` | `1910.05603` | System Description ::: Acoustic Mod | 🔴 | 0.3562 | 1.0000 | Experiments ::: Single system evaluation |
| `Q_QASP_261` | `1909.03405` | Results of NLI Tasks ::: GLUE | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_262` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.5000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_263` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |

### `dense` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_QASP_001` | `1912.01214` | Experiments ::: Main Results | 🟢 | 0.8316 | 1.0000 | Experiments ::: Main Results |
| `Q_QASP_002` | `1912.01214` | Experiments ::: Main Results | 🟢 | 0.2918 | 0.3333 | Experiments ::: Main Results ::: Results |
| `Q_QASP_004` | `1912.01214` | Experiments ::: Setup ::: Datasets. | 🔴 | 0.0000 | 0.3333 | Approach |
| `Q_QASP_005` | `1810.08699` | Experiments | 🟢 | 0.5873 | 1.0000 | Experiments |
| `Q_QASP_006` | `1810.08699` | Test dataset | 🟢 | 0.6131 | 1.0000 | Test dataset |
| `Q_QASP_007` | `1810.08699` | Test dataset | 🔴 | 0.1480 | 0.6667 | Dataset extraction |
| `Q_QASP_008` | `1609.00425` | Dogmatism data | 🟢 | 0.8503 | 1.0000 | Dogmatism data |
| `Q_QASP_009` | `1609.00425` | Predicting dogmatism | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_010` | `1801.05147` | Data Sets | 🟢 | 0.0000 | 0.0000 | Data Sets |
| `Q_QASP_011` | `1811.00383` | Network | 🔴 | 0.5250 | 1.0000 | Introduction |
| `Q_QASP_012` | `1811.00383` | Languages | 🔴 | 0.5626 | 0.7143 | Abstract |
| `Q_QASP_013` | `1811.00383` | Introduction | 🔴 | 0.0000 | 0.5000 | Addressing Lexical Divergence |
| `Q_QASP_014` | `1909.09067` | Introduction | 🔴 | 0.1564 | 0.6667 | Building a Corpus for Automatic Readabil |
| `Q_QASP_015` | `1909.09067` | Introduction | 🔴 | 0.2987 | 0.8333 | Abstract |
| `Q_QASP_018` | `1704.06194` | Introduction | 🔴 | 0.3562 | 1.0000 | KBQA End-Task Results |
| `Q_QASP_019` | `1704.06194` | Introduction | 🔴 | 0.6364 | 1.0000 | Abstract |
| `Q_QASP_020` | `1909.00512` | Approach ::: Measures of Contextual | 🔴 | 0.1740 | 0.6250 | Abstract |
| `Q_QASP_021` | `1909.00512` | Introduction | 🔴 | 0.0000 | 0.0000 | Approach ::: Measures of Contextuality : |
| `Q_QASP_022` | `2003.03106` | Results ::: Experiment A: NUBes-PHI | 🔴 | 0.0000 | 1.0000 | Materials and Methods ::: Systems |
| `Q_QASP_023` | `2003.03106` | Materials and Methods ::: Systems : | 🔴 | 0.1681 | 0.2500 | Materials and Methods |
| `Q_QASP_025` | `2003.03106` | Materials and Methods ::: Data | 🟢 | 0.5842 | 0.6667 | Materials and Methods ::: Data |
| `Q_QASP_026` | `1708.01464` | High Resource Results | 🔴 | 0.6309 | 1.0000 | Low Resource g2p |
| `Q_QASP_027` | `1708.01464` | Baseline | 🔴 | 0.4307 | 1.0000 | Adapted Results |
| `Q_QASP_028` | `1708.01464` | Introduction | 🔴 | 1.0000 | 1.0000 | Evaluation |
| `Q_QASP_029` | `1708.01464` | Data | 🔴 | 0.1232 | 0.7500 | Baseline |
| `Q_QASP_030` | `2002.03407` | Introduction | 🔴 | 0.0000 | 0.0000 | Results |
| `Q_QASP_031` | `2002.03407` | Results | 🟢 | 0.7654 | 0.6667 | Results |
| `Q_QASP_032` | `2002.03407` | Experiments | 🔴 | 0.0000 | 0.2857 | Proposed Template-Based Synthesis Model |
| `Q_QASP_033` | `2002.03407` | Introduction | 🔴 | 0.1391 | 1.0000 | Abstract |
| `Q_QASP_034` | `2002.03407` | Explored Approaches for Limited Res | 🔴 | 0.2184 | 0.5000 | Introduction |
| `Q_QASP_035` | `1909.11687` | Introduction | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_036` | `1909.11687` | Experiments ::: Models and Baseline | 🔴 | 0.1772 | 0.5000 | Abstract |
| `Q_QASP_037` | `1605.06083` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_038` | `1605.06083` | Introduction | 🟢 | 0.8066 | 1.0000 | Introduction |
| `Q_QASP_039` | `1605.06083` | Other methods | 🔴 | 0.1175 | 0.5000 | Abstract |
| `Q_QASP_040` | `1605.06083` | Introduction | 🔴 | 0.1131 | 0.6000 | Abstract |
| `Q_QASP_041` | `1804.05918` | Experimental Results | 🔴 | 0.2140 | 0.4000 | Introduction |
| `Q_QASP_042` | `1804.05918` | Experimental Results | 🔴 | 0.1357 | 1.0000 | Abstract |
| `Q_QASP_043` | `1809.04267` | Introduction | 🔴 | 0.3072 | 0.7500 | The Question Generation Model |
| `Q_QASP_044` | `1901.05287` | Results | 🔴 | 0.4256 | 1.0000 | Introduction |
| `Q_QASP_045` | `1612.06685` | Psycholinguistic and Semantic Maps | 🔴 | 0.3155 | 1.0000 | Maps from Blogs |
| `Q_QASP_046` | `1612.06685` | Data Collection | 🔴 | 0.4865 | 1.0000 | Abstract |
| `Q_QASP_048` | `1912.04961` | Experiments ::: Model variations | 🟢 | 1.0000 | 1.0000 | Experiments ::: Model variations |
| `Q_QASP_049` | `1912.04961` | Data | 🟢 | 1.0000 | 1.0000 | Data |
| `Q_QASP_050` | `1912.04961` | Experiments ::: Model variations | 🔴 | 0.2641 | 1.0000 | Data |
| `Q_QASP_051` | `1910.10781` | Introduction | 🔴 | 0.3991 | 0.6667 | Related work |
| `Q_QASP_052` | `1910.10781` | Introduction | 🟢 | 0.3120 | 1.0000 | Introduction |
| `Q_QASP_053` | `1603.09631` | Dataset Collection Process | 🔴 | 0.2641 | 1.0000 | Introduction |
| `Q_QASP_054` | `1603.09631` | Dataset Properties | 🔴 | 0.0000 | 0.0000 | Dialog policies |
| `Q_QASP_055` | `1911.06964` | Experiments | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_056` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.0000 | 1.0000 | Approach |
| `Q_QASP_057` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_058` | `1911.06964` | Experiments ::: Efficiency-accuracy | 🔴 | 0.6309 | 1.0000 | Approach ::: Modeling with autoencoders. |
| `Q_QASP_059` | `2001.02284` | Model ::: Dialogue Modules | 🔴 | 0.0000 | 0.2500 | Related Work |
| `Q_QASP_060` | `2001.02284` | Re-implementation of units with BER | 🔴 | 0.0000 | 0.2000 | Introduction ::: Outline and Contributio |
| `Q_QASP_061` | `2001.02284` | Target Domain & Task Definition | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_062` | `2002.01664` | INTRODUCTION | 🔴 | 0.7757 | 1.0000 | DATASET |
| `Q_QASP_063` | `2002.01664` | POOLING STRATEGIES ::: GhostVLAD po | 🔴 | 0.3253 | 1.0000 | Conclusion |
| `Q_QASP_064` | `2002.01664` | Introduction | 🟢 | 0.3066 | 0.5000 | INTRODUCTION |
| `Q_QASP_065` | `1808.09111` | Data | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_066` | `1808.09111` | Data | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_067` | `1808.09111` | Learning & Inference | 🟢 | 0.6131 | 0.5000 | Learning & Inference |
| `Q_QASP_068` | `1906.08593` | Qualitative Comparison | 🟢 | 0.9052 | 0.6111 | Qualitative Comparison |
| `Q_QASP_069` | `1906.08593` | The model | 🔴 | 0.0000 | 0.0000 | Relation to Multi-Head attention |
| `Q_QASP_070` | `1906.08593` | Introduction | 🔴 | 0.2304 | 0.7500 | Abstract |
| `Q_QASP_071` | `1809.00540` | Related Work | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_072` | `1809.00540` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_073` | `2004.03354` | Experiment 1: Biomedical NER ::: Do | 🔴 | 0.2346 | 0.3333 | Abstract |
| `Q_QASP_074` | `1611.04798` | Introduction | 🔴 | 0.0000 | 0.0000 | Neural Machine Translation: Background |
| `Q_QASP_075` | `1611.04798` | Introduction | 🟢 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_076` | `1611.04798` | Under-resourced Translation | 🟢 | 0.9197 | 1.0000 | Under-resourced Translation |
| `Q_QASP_077` | `1912.13337` | Introduction | 🔴 | 0.0734 | 0.2000 | Abstract |
| `Q_QASP_078` | `1912.13337` | Introduction | 🔴 | 0.2372 | 0.5000 | Related Work |
| `Q_QASP_079` | `1912.13337` | Introduction | 🔴 | 0.0000 | 1.0000 | Results and Findings ::: How well do pre |
| `Q_QASP_080` | `1912.13337` | Introduction | 🔴 | 0.0000 | 0.1111 | Related Work |
| `Q_QASP_081` | `1912.13337` | Introduction | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_082` | `1809.01541` | Our system | 🟢 | 0.7157 | 1.0000 | Our system |
| `Q_QASP_083` | `1809.01541` | Baseline | 🟢 | 0.1772 | 1.0000 | Baseline |
| `Q_QASP_084` | `1809.01541` | Baseline | 🔴 | 0.0000 | 1.0000 | System Description |
| `Q_QASP_085` | `1809.01541` | Baseline | 🔴 | 0.0000 | 1.0000 | System Description |
| `Q_QASP_086` | `1809.01541` | Introduction | 🔴 | 0.0000 | 1.0000 | MSD prediction |
| `Q_QASP_087` | `1809.01541` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
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
| `Q_QASP_101` | `1809.00530` | Introduction | 🔴 | 0.7123 | 1.0000 | Datasets and Experimental Settings |
| `Q_QASP_102` | `1809.00530` | Notations and Model Overview | 🔴 | 0.3066 | 0.5000 | Models for Comparison |
| `Q_QASP_103` | `1809.00530` | Introduction | 🔴 | 0.1815 | 0.3333 | Numerical Results of Figure |
| `Q_QASP_104` | `1809.00530` | Introduction | 🟢 | 0.2692 | 1.0000 | Introduction |
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
| `Q_QASP_116` | `2002.11910` | Introduction | 🔴 | 0.3045 | 1.0000 | Abstract |
| `Q_QASP_117` | `2002.11910` | Model ::: Boundary Assembling Metho | 🔴 | 0.4911 | 1.0000 | Experiments ::: Results and Discussion |
| `Q_QASP_118` | `2002.11910` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_119` | `1909.09587` | Zero-shot Transfer with Multi-BERT  | 🔴 | 0.0980 | 0.8000 | Abstract |
| `Q_QASP_120` | `1909.09587` | Introduction | 🟢 | 0.0000 | 0.6000 | Introduction |
| `Q_QASP_121` | `1909.09587` | Zero-shot Transfer with Multi-BERT | 🔴 | 0.2292 | 0.8000 | What Does Zero-shot Transfer Model Learn |
| `Q_QASP_122` | `1909.09587` | Zero-shot Transfer with Multi-BERT  | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_123` | `1802.07862` | Results: SnapCaptions Dataset | 🟢 | 0.3501 | 0.6667 | Results: SnapCaptions Dataset |
| `Q_QASP_124` | `1802.07862` | Baselines | 🔴 | 0.2684 | 0.8333 | Introduction |
| `Q_QASP_125` | `1802.07862` | SnapCaptions Dataset | 🟢 | 0.4685 | 1.0000 | Results: SnapCaptions Dataset |
| `Q_QASP_126` | `1802.07862` | Baselines | 🔴 | 0.0000 | 0.0000 | SnapCaptions Dataset |
| `Q_QASP_127` | `1802.07862` | SnapCaptions Dataset | 🟢 | 0.5250 | 1.0000 | Results: SnapCaptions Dataset |
| `Q_QASP_128` | `2004.01853` | Introduction | 🔴 | 0.5000 | 1.0000 | Experimental Setup ::: Datasets ::: GIGA |
| `Q_QASP_129` | `2004.01853` | Results ::: Automatic Evaluation | 🟢 | 0.9197 | 1.0000 | Results ::: Automatic Evaluation |
| `Q_QASP_130` | `1710.03348` | Introduction | 🔴 | 0.2339 | 0.8000 | Abstract |
| `Q_QASP_131` | `1710.03348` | Impact of Attention Mechanism | 🔴 | 0.3869 | 0.5000 | Attention Concentration |
| `Q_QASP_132` | `1710.03348` | Alignment Quality Impact on Transla | 🔴 | 0.2184 | 1.0000 | Abstract |
| `Q_QASP_133` | `1612.03226` | Expected Gradient Length | 🔴 | 0.5085 | 1.0000 | Experiments |
| `Q_QASP_134` | `1612.03226` | Experiments | 🔴 | 0.0000 | 0.7500 | Introduction |
| `Q_QASP_135` | `1612.03226` | Experiments | 🔴 | 0.3978 | 1.0000 | Similarity between Query Methods |
| `Q_QASP_136` | `1612.03226` | Experiments | 🟢 | 0.0000 | 1.0000 | Experiments |
| `Q_QASP_137` | `1809.02286` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_138` | `1809.01202` | Experiment | 🔴 | 0.0000 | 0.0000 | Exploration |
| `Q_QASP_139` | `1809.01202` | Dataset | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_140` | `1909.02027` | Dataset ::: In-Scope Data Collectio | 🔴 | 0.0000 | 1.0000 | Dataset |
| `Q_QASP_141` | `1909.02027` | Introduction | 🔴 | 0.4693 | 1.0000 | Benchmark Evaluation |
| `Q_QASP_142` | `1909.02027` | Introduction | 🔴 | 0.6131 | 1.0000 | Dataset |
| `Q_QASP_143` | `1909.02027` | Dataset | 🔴 | 0.3296 | 0.6667 | Benchmark Evaluation ::: Out-of-Scope Pr |
| `Q_QASP_144` | `1911.02855` | Experiments ::: Paraphrase Identifi | 🔴 | 0.8603 | 1.0000 | Experiments ::: Paraphrase Identificatio |
| `Q_QASP_145` | `1911.02855` | Experiments ::: Named Entity Recogn | 🔴 | 1.0000 | 1.0000 | Experiments ::: Named Entity Recognition |
| `Q_QASP_146` | `1911.02855` | Experiments ::: Part-of-Speech Tagg | 🔴 | 0.3869 | 1.0000 | Experiments ::: Named Entity Recognition |
| `Q_QASP_147` | `1911.02855` | Losses ::: Self-adusting Dice Loss | 🔴 | 0.1461 | 0.4000 | Related Work ::: Data Resample |
| `Q_QASP_148` | `1906.01081` | Introduction | 🔴 | 0.3759 | 1.0000 | Hyperparameters |
| `Q_QASP_149` | `1906.01081` | Human Evaluation | 🔴 | 0.2184 | 1.0000 | Data & Models |
| `Q_QASP_150` | `1906.01081` | Correlation Comparison | 🔴 | 0.2372 | 1.0000 | Introduction |
| `Q_QASP_151` | `1611.01576` | Character-level Neural Machine Tran | 🟢 | 1.0000 | 1.0000 | Character-level Neural Machine Translati |
| `Q_QASP_152` | `1611.01576` | Sentiment Classification | 🟢 | 1.0000 | 1.0000 | Sentiment Classification |
| `Q_QASP_153` | `1611.01576` | Model | 🔴 | 0.3066 | 1.0000 | Variants |
| `Q_QASP_154` | `1904.09535` | Experiments | 🔴 | 0.9197 | 1.0000 | Sequence Labeling |
| `Q_QASP_155` | `1904.09535` | Block Zoo | 🟢 | 0.7031 | 0.7500 | Block Zoo |
| `Q_QASP_156` | `1904.09535` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_157` | `1911.03059` | Question Collection and Categories | 🔴 | 0.0000 | 0.0000 | Related Works ::: Research Works Related |
| `Q_QASP_159` | `1706.08198` | Conclusion | 🔴 | 0.8332 | 1.0000 | Introduction |
| `Q_QASP_160` | `1706.08198` | Datasets | 🟢 | 1.0000 | 1.0000 | Datasets |
| `Q_QASP_161` | `1909.08089` | Results and Analysis | 🔴 | 0.5641 | 1.0000 | Introduction |
| `Q_QASP_162` | `1909.08089` | Introduction | 🔴 | 0.1934 | 1.0000 | Decoder |
| `Q_QASP_164` | `1910.09982` | Data | 🔴 | 0.0000 | 0.5000 | Participants and Approaches ::: Teams Pa |
| `Q_QASP_165` | `1910.09982` | Baselines | 🟢 | 1.0000 | 1.0000 | Baselines |
| `Q_QASP_166` | `1609.00559` | Introduction | 🔴 | 0.6309 | 1.0000 | Method |
| `Q_QASP_167` | `1609.00559` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_168` | `1609.00559` | Comparison with Previous Work | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 1.0000 | Decoding the KB Query |
| `Q_QASP_170` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 0.0000 | Attention Mechanisms |
| `Q_QASP_171` | `1612.02482` | Introduction | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_173` | `1608.01084` | Data Set and Toolkits | 🔴 | 0.0000 | 0.0000 | Our Approach |
| `Q_QASP_174` | `1904.10503` | Introduction | 🔴 | 1.0000 | 1.0000 | Conclusion and Future Work |
| `Q_QASP_175` | `1904.10503` | Results | 🟢 | 0.9197 | 1.0000 | Results |
| `Q_QASP_176` | `1904.10503` | Entity Linking using Wikidata | 🔴 | 0.2140 | 0.8000 | Abstract |
| `Q_QASP_177` | `1912.01772` | Introduction | 🔴 | 0.5492 | 0.7778 | Abstract |
| `Q_QASP_178` | `1912.01772` | The Resource ::: Additional Annotat | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_179` | `1603.01987` | The medical domain model | 🔴 | 0.0000 | 1.0000 | Classification results |
| `Q_QASP_180` | `1908.06941` | PMI & Matrix Factorization | 🔴 | 0.2189 | 1.0000 | Abstract |
| `Q_QASP_181` | `1908.06941` | Materials | 🔴 | 0.4585 | 1.0000 | Abstract |
| `Q_QASP_182` | `1908.06941` | Results | 🔴 | 0.1772 | 1.0000 | Introduction |
| `Q_QASP_183` | `1908.06941` | Introduction | 🔴 | 0.6934 | 1.0000 | Abstract |
| `Q_QASP_184` | `1702.03856` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_185` | `1702.03856` | Introduction | 🔴 | 0.6332 | 1.0000 | Analysis of challenges from UTD |
| `Q_QASP_186` | `1702.03856` | Dataset | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_187` | `1904.01548` | Related Work | 🔴 | 0.0843 | 0.8750 | Abstract |
| `Q_QASP_188` | `1904.01548` | Related Work | 🔴 | 0.6188 | 0.7500 | Discussion |
| `Q_QASP_189` | `1606.03676` | Corpora | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_190` | `1606.03676` | Corpora | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_191` | `1802.00396` | Introduction | 🔴 | 0.0000 | 0.0000 | Network Analysis |
| `Q_QASP_192` | `1802.00396` | UN votes and speeches | 🟢 | 0.4838 | 1.0000 | UN votes and speeches |
| `Q_QASP_193` | `1911.03343` | Introduction | 🔴 | 0.4685 | 1.0000 | Abstract |
| `Q_QASP_194` | `1712.00991` | Evaluation of auto-generated summar | 🟢 | 1.0000 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_195` | `1712.00991` | Evaluation of auto-generated summar | 🟢 | 1.0000 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_196` | `1712.00991` | Discovering Clusters within Sentenc | 🔴 | 0.3759 | 0.6667 | Evaluation of auto-generated summaries |
| `Q_QASP_197` | `1712.00991` | PA along Attributes | 🔴 | 0.1480 | 1.0000 | Introduction |
| `Q_QASP_198` | `1712.00991` | Sentence Classification | 🔴 | 0.4632 | 1.0000 | Conclusions and Further Work |
| `Q_QASP_199` | `1712.00991` | Dataset | 🟢 | 1.0000 | 1.0000 | Dataset |
| `Q_QASP_200` | `1712.00991` | Dataset | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_201` | `1805.08241` | Experiments | 🔴 | 0.2641 | 1.0000 | Fertility Bounds |
| `Q_QASP_202` | `1907.04433` | Performance | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_204` | `2003.04642` | Framework for MRC Gold Standard Ana | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_205` | `2003.04642` | Application of the Framework ::: Ca | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_206` | `2003.04642` | Introduction | 🔴 | 0.6131 | 1.0000 | Framework for MRC Gold Standard Analysis |
| `Q_QASP_208` | `2001.09215` | Proposed Methodology | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_209` | `1909.07575` | Experiments ::: Baseline Models and | 🔴 | 0.5508 | 1.0000 | Abstract |
| `Q_QASP_210` | `1909.07575` | Our method ::: Training Procedure : | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_211` | `1701.04056` | Interactive Dialog Context LM | 🔴 | 0.2961 | 0.6667 | Results and Analysis |
| `Q_QASP_212` | `1904.07904` | Spoken Question Answering | 🟢 | 1.0000 | 1.0000 | Spoken Question Answering |
| `Q_QASP_213` | `1904.07904` | Results | 🔴 | 0.6509 | 1.0000 | Conclusion |
| `Q_QASP_214` | `1904.07904` | Results | 🔴 | 0.4367 | 1.0000 | Conclusion |
| `Q_QASP_215` | `1904.07904` | Corpus | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_216` | `2003.11645` | Introduction | 🔴 | 1.0000 | 1.0000 | Methodology |
| `Q_QASP_217` | `2003.11645` | Introduction | 🔴 | 0.6053 | 1.0000 | Abstract |
| `Q_QASP_218` | `2003.11645` | Introduction | 🟢 | 0.8175 | 1.0000 | Introduction |
| `Q_QASP_219` | `2003.11645` | Introduction | 🔴 | 0.0000 | 1.0000 | Literature Review |
| `Q_QASP_220` | `1909.02304` | Experiments ::: Results ::: Automat | 🔴 | 0.0980 | 0.6000 | Conclusion |
| `Q_QASP_221` | `1909.02304` | Experiments ::: Results ::: Automat | 🔴 | 0.1744 | 0.2857 | Abstract |
| `Q_QASP_222` | `1604.03114` | Modeling Idea Flow | 🔴 | 0.2901 | 0.7500 | Abstract |
| `Q_QASP_223` | `1604.03114` | Debate Dataset: Intelligence Square | 🟢 | 1.0000 | 1.0000 | Debate Dataset: Intelligence Squared |
| `Q_QASP_225` | `2001.03131` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments and Discussions ::: Results  |
| `Q_QASP_226` | `2001.03131` | Proposed Approach | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_227` | `1606.02891` | Baseline System | 🔴 | 0.4685 | 1.0000 | Abstract |
| `Q_QASP_228` | `1803.09123` | Empirical Study | 🔴 | 0.1232 | 0.7500 | Equation Embeddings Models |
| `Q_QASP_229` | `1803.09123` | Discovering Semantically Similar Eq | 🟢 | 0.7598 | 1.0000 | Discovering Semantically Similar Equatio |
| `Q_QASP_230` | `1910.01863` | Text Generation ::: Baseline Experi | 🔴 | 0.5501 | 0.7273 | Text Generation |
| `Q_QASP_231` | `1701.08229` | METHODS | 🔴 | 0.4228 | 1.0000 | Feature Elimination |
| `Q_QASP_232` | `1701.08229` | Feature Elimination | 🔴 | 0.5714 | 1.0000 | Discussion |
| `Q_QASP_233` | `1701.08229` | METHODS | 🟢 | 0.9197 | 1.0000 | METHODS |
| `Q_QASP_234` | `1701.08229` | METHODS | 🔴 | 0.3869 | 1.0000 | Discussion |
| `Q_QASP_235` | `1912.06262` | Experiments ::: Results | 🔴 | 0.0000 | 1.0000 | Experiments ::: Hyperparameter Tuning |
| `Q_QASP_236` | `1912.06262` | Experiments ::: Data | 🔴 | 0.2184 | 1.0000 | Abstract |
| `Q_QASP_237` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.6367 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_238` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.6548 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_239` | `1709.07814` | Speech Data | 🔴 | 0.1391 | 0.2500 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_240` | `1806.00738` | Model | 🟢 | 0.7865 | 1.0000 | Model |
| `Q_QASP_241` | `1806.00738` | Decoder | 🔴 | 0.2856 | 1.0000 | Methodology |
| `Q_QASP_242` | `1806.00738` | Encoder | 🔴 | 0.6053 | 1.0000 | Decoder |
| `Q_QASP_243` | `1806.00738` | Decoder | 🟢 | 0.8772 | 1.0000 | Decoder |
| `Q_QASP_244` | `1811.00147` | Dolores: Learner | 🟢 | 0.6131 | 0.5000 | Dolores: Learner |
| `Q_QASP_245` | `1811.00147` | Dolores: Learner | 🔴 | 0.1128 | 0.2500 | Problem Formulation |
| `Q_QASP_246` | `1610.09225` | Introduction | 🟢 | 0.1208 | 0.8000 | Introduction |
| `Q_QASP_247` | `1610.09225` | Feature Extraction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_248` | `1610.09225` | Data Collection | 🔴 | 0.0000 | 0.5000 | Sentiment Analyzer Results |
| `Q_QASP_249` | `2003.08380` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_250` | `1811.05711` | Multiscale graph partitioning for t | 🔴 | 0.2874 | 0.6667 | Abstract |
| `Q_QASP_251` | `1805.04508` | Gender Bias Results | 🔴 | 0.3378 | 1.0000 | Abstract |
| `Q_QASP_252` | `1805.04508` | The Equity Evaluation Corpus | 🔴 | 0.4132 | 0.7500 | Introduction |
| `Q_QASP_253` | `1904.03288` | Conversational Speech | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_254` | `1904.03288` | Read Speech | 🔴 | 0.5714 | 1.0000 | Introduction |
| `Q_QASP_256` | `1909.13714` | Methodology | 🔴 | 0.3869 | 1.0000 | Introduction |
| `Q_QASP_257` | `1910.05603` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_258` | `1910.05603` | System Description ::: Language Mod | 🟢 | 0.7929 | 1.0000 | System Description ::: Language Model |
| `Q_QASP_259` | `1910.05603` | Experiments ::: System combination | 🔴 | 0.4307 | 1.0000 | Conclusion |
| `Q_QASP_260` | `1910.05603` | System Description ::: Acoustic Mod | 🔴 | 0.3562 | 1.0000 | Experiments ::: Single system evaluation |
| `Q_QASP_261` | `1909.03405` | Results of NLI Tasks ::: GLUE | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_262` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Results of NLI Tasks ::: GLUE |
| `Q_QASP_263` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |

### `hybrid_rrf` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_QASP_001` | `1912.01214` | Experiments ::: Main Results | 🟢 | 0.8175 | 1.0000 | Experiments ::: Main Results |
| `Q_QASP_002` | `1912.01214` | Experiments ::: Main Results | 🟢 | 0.2468 | 0.3333 | Experiments ::: Main Results ::: Results |
| `Q_QASP_004` | `1912.01214` | Experiments ::: Setup ::: Datasets. | 🔴 | 0.0000 | 0.3333 | Approach |
| `Q_QASP_005` | `1810.08699` | Experiments | 🟢 | 0.5873 | 1.0000 | Experiments |
| `Q_QASP_006` | `1810.08699` | Test dataset | 🟢 | 0.6131 | 1.0000 | Test dataset |
| `Q_QASP_007` | `1810.08699` | Test dataset | 🔴 | 0.1413 | 0.6667 | Dataset extraction |
| `Q_QASP_008` | `1609.00425` | Dogmatism data | 🟢 | 0.8175 | 1.0000 | Dogmatism data |
| `Q_QASP_009` | `1609.00425` | Predicting dogmatism | 🔴 | 0.0000 | 0.0000 | Conclusion |
| `Q_QASP_010` | `1801.05147` | Data Sets | 🟢 | 0.0000 | 0.0000 | Data Sets |
| `Q_QASP_011` | `1811.00383` | Network | 🔴 | 0.6509 | 1.0000 | Introduction |
| `Q_QASP_012` | `1811.00383` | Languages | 🔴 | 0.5677 | 0.7143 | Abstract |
| `Q_QASP_013` | `1811.00383` | Introduction | 🔴 | 0.0000 | 0.5000 | Addressing Lexical Divergence |
| `Q_QASP_014` | `1909.09067` | Introduction | 🔴 | 0.1564 | 0.6667 | Building a Corpus for Automatic Readabil |
| `Q_QASP_015` | `1909.09067` | Introduction | 🔴 | 0.4035 | 0.8333 | Building a Corpus for Automatic Readabil |
| `Q_QASP_018` | `1704.06194` | Introduction | 🔴 | 0.3869 | 1.0000 | KBQA End-Task Results |
| `Q_QASP_019` | `1704.06194` | Introduction | 🔴 | 0.6364 | 1.0000 | Abstract |
| `Q_QASP_020` | `1909.00512` | Approach ::: Measures of Contextual | 🔴 | 0.1699 | 0.5000 | Abstract |
| `Q_QASP_021` | `1909.00512` | Introduction | 🔴 | 0.0000 | 0.0000 | Approach ::: Measures of Contextuality : |
| `Q_QASP_022` | `2003.03106` | Results ::: Experiment A: NUBes-PHI | 🔴 | 0.0000 | 1.0000 | Materials and Methods ::: Systems ::: BE |
| `Q_QASP_023` | `2003.03106` | Materials and Methods ::: Systems : | 🔴 | 0.1510 | 0.2500 | Materials and Methods |
| `Q_QASP_025` | `2003.03106` | Materials and Methods ::: Data | 🟢 | 0.5842 | 0.6667 | Materials and Methods ::: Data |
| `Q_QASP_026` | `1708.01464` | High Resource Results | 🔴 | 0.6309 | 1.0000 | Low Resource g2p |
| `Q_QASP_027` | `1708.01464` | Baseline | 🔴 | 0.5000 | 1.0000 | Adapted Results |
| `Q_QASP_028` | `1708.01464` | Introduction | 🔴 | 1.0000 | 1.0000 | Evaluation |
| `Q_QASP_029` | `1708.01464` | Data | 🔴 | 0.1175 | 0.7500 | High Resource Results |
| `Q_QASP_030` | `2002.03407` | Introduction | 🔴 | 0.0000 | 0.0000 | Results |
| `Q_QASP_031` | `2002.03407` | Results | 🟢 | 0.7654 | 0.6667 | Results |
| `Q_QASP_032` | `2002.03407` | Experiments | 🟢 | 0.0000 | 0.4286 | Experiments |
| `Q_QASP_033` | `2002.03407` | Introduction | 🔴 | 0.1952 | 1.0000 | Abstract |
| `Q_QASP_034` | `2002.03407` | Explored Approaches for Limited Res | 🔴 | 0.2184 | 0.5000 | Abstract |
| `Q_QASP_035` | `1909.11687` | Introduction | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_036` | `1909.11687` | Experiments ::: Models and Baseline | 🔴 | 0.1846 | 0.5000 | Abstract |
| `Q_QASP_037` | `1605.06083` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_038` | `1605.06083` | Introduction | 🟢 | 0.8066 | 1.0000 | Introduction |
| `Q_QASP_039` | `1605.06083` | Other methods | 🔴 | 0.1301 | 0.5000 | Abstract |
| `Q_QASP_040` | `1605.06083` | Introduction | 🔴 | 0.1131 | 0.6000 | Abstract |
| `Q_QASP_041` | `1804.05918` | Experimental Results | 🔴 | 0.3392 | 0.6000 | Dataset and Preprocessing |
| `Q_QASP_042` | `1804.05918` | Experimental Results | 🔴 | 0.1357 | 0.6667 | Abstract |
| `Q_QASP_043` | `1809.04267` | Introduction | 🔴 | 0.1175 | 0.7500 | The Question Generation Model |
| `Q_QASP_044` | `1901.05287` | Results | 🔴 | 0.4256 | 1.0000 | Introduction |
| `Q_QASP_045` | `1612.06685` | Psycholinguistic and Semantic Maps | 🔴 | 0.3333 | 1.0000 | Abstract |
| `Q_QASP_046` | `1612.06685` | Data Collection | 🔴 | 0.4976 | 1.0000 | Abstract |
| `Q_QASP_048` | `1912.04961` | Experiments ::: Model variations | 🟢 | 1.0000 | 1.0000 | Experiments ::: Model variations |
| `Q_QASP_049` | `1912.04961` | Data | 🔴 | 0.6309 | 1.0000 | Acknowledgements |
| `Q_QASP_050` | `1912.04961` | Experiments ::: Model variations | 🔴 | 0.2641 | 1.0000 | Results and Discussion ::: Training Data |
| `Q_QASP_051` | `1910.10781` | Introduction | 🔴 | 0.4297 | 0.6667 | Related work |
| `Q_QASP_052` | `1910.10781` | Introduction | 🟢 | 0.3120 | 1.0000 | Introduction |
| `Q_QASP_053` | `1603.09631` | Dataset Collection Process | 🔴 | 0.2372 | 1.0000 | Dialog Simulation |
| `Q_QASP_054` | `1603.09631` | Dataset Properties | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_055` | `1911.06964` | Experiments | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_056` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.0000 | 1.0000 | Approach |
| `Q_QASP_057` | `1911.06964` | Experiments ::: User study. | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_058` | `1911.06964` | Experiments ::: Efficiency-accuracy | 🔴 | 0.6309 | 1.0000 | Approach ::: Modeling with autoencoders. |
| `Q_QASP_059` | `2001.02284` | Model ::: Dialogue Modules | 🔴 | 0.0000 | 0.2500 | Related Work |
| `Q_QASP_060` | `2001.02284` | Re-implementation of units with BER | 🔴 | 0.0000 | 0.2000 | Introduction ::: Outline and Contributio |
| `Q_QASP_061` | `2001.02284` | Target Domain & Task Definition | 🔴 | 0.1772 | 1.0000 | Abstract |
| `Q_QASP_062` | `2002.01664` | INTRODUCTION | 🔴 | 0.7877 | 1.0000 | DATASET |
| `Q_QASP_063` | `2002.01664` | POOLING STRATEGIES ::: GhostVLAD po | 🔴 | 0.3183 | 1.0000 | RESULTS ::: Comparison with different po |
| `Q_QASP_064` | `2002.01664` | Introduction | 🟢 | 0.3869 | 0.5000 | INTRODUCTION |
| `Q_QASP_065` | `1808.09111` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_066` | `1808.09111` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_067` | `1808.09111` | Learning & Inference | 🟢 | 0.6131 | 0.5000 | Learning & Inference |
| `Q_QASP_068` | `1906.08593` | Qualitative Comparison | 🟢 | 0.8237 | 0.6111 | Qualitative Comparison |
| `Q_QASP_069` | `1906.08593` | The model | 🔴 | 0.0000 | 0.0000 | Relation to Multi-Head attention |
| `Q_QASP_070` | `1906.08593` | Introduction | 🔴 | 0.2622 | 0.7500 | Abstract |
| `Q_QASP_071` | `1809.00540` | Related Work | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_072` | `1809.00540` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments |
| `Q_QASP_073` | `2004.03354` | Experiment 1: Biomedical NER ::: Do | 🔴 | 0.2346 | 0.3333 | Abstract |
| `Q_QASP_074` | `1611.04798` | Introduction | 🔴 | 0.0000 | 0.0000 | Neural Machine Translation: Background |
| `Q_QASP_075` | `1611.04798` | Introduction | 🟢 | 0.3010 | 1.0000 | Introduction |
| `Q_QASP_076` | `1611.04798` | Under-resourced Translation | 🟢 | 0.8772 | 1.0000 | Under-resourced Translation |
| `Q_QASP_077` | `1912.13337` | Introduction | 🔴 | 0.0734 | 0.2000 | Abstract |
| `Q_QASP_078` | `1912.13337` | Introduction | 🔴 | 0.2641 | 0.5000 | Related Work |
| `Q_QASP_079` | `1912.13337` | Introduction | 🔴 | 0.0000 | 1.0000 | Results and Findings ::: How well do pre |
| `Q_QASP_080` | `1912.13337` | Introduction | 🔴 | 0.0000 | 0.1111 | Abstract |
| `Q_QASP_081` | `1912.13337` | Introduction | 🔴 | 0.4307 | 1.0000 | Abstract |
| `Q_QASP_082` | `1809.01541` | Our system | 🟢 | 0.7598 | 1.0000 | Our system |
| `Q_QASP_083` | `1809.01541` | Baseline | 🟢 | 0.1772 | 1.0000 | Baseline |
| `Q_QASP_084` | `1809.01541` | Baseline | 🔴 | 0.0000 | 1.0000 | System Description |
| `Q_QASP_085` | `1809.01541` | Baseline | 🔴 | 0.0000 | 1.0000 | System Description |
| `Q_QASP_086` | `1809.01541` | Introduction | 🔴 | 0.0000 | 1.0000 | MSD prediction |
| `Q_QASP_087` | `1809.01541` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
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
| `Q_QASP_101` | `1809.00530` | Introduction | 🔴 | 0.7328 | 1.0000 | Datasets and Experimental Settings |
| `Q_QASP_102` | `1809.00530` | Notations and Model Overview | 🔴 | 0.2641 | 0.5000 | Models for Comparison |
| `Q_QASP_103` | `1809.00530` | Introduction | 🔴 | 0.1815 | 0.3333 | Numerical Results of Figure |
| `Q_QASP_104` | `1809.00530` | Introduction | 🟢 | 0.3127 | 1.0000 | Introduction |
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
| `Q_QASP_116` | `2002.11910` | Introduction | 🔴 | 0.4401 | 1.0000 | Abstract |
| `Q_QASP_117` | `2002.11910` | Model ::: Boundary Assembling Metho | 🔴 | 0.4575 | 1.0000 | Experiments ::: Results and Discussion |
| `Q_QASP_118` | `2002.11910` | Introduction | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_119` | `1909.09587` | Zero-shot Transfer with Multi-BERT  | 🔴 | 0.1021 | 0.8000 | Abstract |
| `Q_QASP_120` | `1909.09587` | Introduction | 🟢 | 0.0000 | 0.4000 | Introduction |
| `Q_QASP_121` | `1909.09587` | Zero-shot Transfer with Multi-BERT | 🔴 | 0.2441 | 0.8000 | What Does Zero-shot Transfer Model Learn |
| `Q_QASP_122` | `1909.09587` | Zero-shot Transfer with Multi-BERT  | 🔴 | 0.0000 | 0.5000 | What Does Zero-shot Transfer Model Learn |
| `Q_QASP_123` | `1802.07862` | Results: SnapCaptions Dataset | 🟢 | 0.3152 | 0.6667 | Results: SnapCaptions Dataset |
| `Q_QASP_124` | `1802.07862` | Baselines | 🔴 | 0.4329 | 0.8333 | Introduction |
| `Q_QASP_125` | `1802.07862` | SnapCaptions Dataset | 🟢 | 0.5438 | 1.0000 | Results: SnapCaptions Dataset |
| `Q_QASP_126` | `1802.07862` | Baselines | 🔴 | 0.0000 | 0.0000 | Results: SnapCaptions Dataset |
| `Q_QASP_127` | `1802.07862` | SnapCaptions Dataset | 🔴 | 0.5013 | 1.0000 | Introduction |
| `Q_QASP_128` | `2004.01853` | Introduction | 🔴 | 0.4307 | 1.0000 | Experimental Setup ::: Datasets ::: GIGA |
| `Q_QASP_129` | `2004.01853` | Results ::: Automatic Evaluation | 🟢 | 0.9197 | 1.0000 | Results ::: Automatic Evaluation |
| `Q_QASP_130` | `1710.03348` | Introduction | 🔴 | 0.2339 | 0.8000 | Abstract |
| `Q_QASP_131` | `1710.03348` | Impact of Attention Mechanism | 🔴 | 0.2641 | 0.5000 | Attention Concentration |
| `Q_QASP_132` | `1710.03348` | Alignment Quality Impact on Transla | 🔴 | 0.2184 | 0.5000 | Abstract |
| `Q_QASP_133` | `1612.03226` | Expected Gradient Length | 🔴 | 0.6437 | 1.0000 | Variance in the Asymptote |
| `Q_QASP_134` | `1612.03226` | Experiments | 🔴 | 0.0000 | 0.7500 | Introduction |
| `Q_QASP_135` | `1612.03226` | Experiments | 🔴 | 0.3978 | 1.0000 | Similarity between Query Methods |
| `Q_QASP_136` | `1612.03226` | Experiments | 🟢 | 0.0000 | 1.0000 | Experiments |
| `Q_QASP_137` | `1809.02286` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_138` | `1809.01202` | Experiment | 🔴 | 0.0000 | 0.0000 | Exploration |
| `Q_QASP_139` | `1809.01202` | Dataset | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_140` | `1909.02027` | Dataset ::: In-Scope Data Collectio | 🔴 | 0.0000 | 1.0000 | Dataset |
| `Q_QASP_141` | `1909.02027` | Introduction | 🔴 | 0.4693 | 1.0000 | Benchmark Evaluation |
| `Q_QASP_142` | `1909.02027` | Introduction | 🔴 | 0.3869 | 1.0000 | Results ::: Results with oos-train |
| `Q_QASP_143` | `1909.02027` | Dataset | 🔴 | 0.3084 | 0.6667 | Benchmark Evaluation ::: Out-of-Scope Pr |
| `Q_QASP_144` | `1911.02855` | Experiments ::: Paraphrase Identifi | 🔴 | 0.8711 | 1.0000 | Experiments ::: Paraphrase Identificatio |
| `Q_QASP_145` | `1911.02855` | Experiments ::: Named Entity Recogn | 🔴 | 0.9197 | 1.0000 | Experiments ::: Named Entity Recognition |
| `Q_QASP_146` | `1911.02855` | Experiments ::: Part-of-Speech Tagg | 🔴 | 0.3869 | 1.0000 | Experiments ::: Named Entity Recognition |
| `Q_QASP_147` | `1911.02855` | Losses ::: Self-adusting Dice Loss | 🔴 | 0.1461 | 0.4000 | Related Work ::: Data Resample |
| `Q_QASP_148` | `1906.01081` | Introduction | 🔴 | 0.3045 | 1.0000 | Hyperparameters |
| `Q_QASP_149` | `1906.01081` | Human Evaluation | 🔴 | 0.2044 | 1.0000 | Data & Models |
| `Q_QASP_150` | `1906.01081` | Correlation Comparison | 🔴 | 0.2641 | 1.0000 | Introduction |
| `Q_QASP_151` | `1611.01576` | Character-level Neural Machine Tran | 🟢 | 1.0000 | 1.0000 | Character-level Neural Machine Translati |
| `Q_QASP_152` | `1611.01576` | Sentiment Classification | 🟢 | 1.0000 | 1.0000 | Sentiment Classification |
| `Q_QASP_153` | `1611.01576` | Model | 🔴 | 0.2641 | 1.0000 | Variants |
| `Q_QASP_154` | `1904.09535` | Experiments | 🔴 | 0.8772 | 1.0000 | Sequence Labeling |
| `Q_QASP_155` | `1904.09535` | Block Zoo | 🟢 | 0.7157 | 0.7500 | Block Zoo |
| `Q_QASP_156` | `1904.09535` | Introduction | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_157` | `1911.03059` | Question Collection and Categories | 🔴 | 0.0000 | 0.0000 | Related Works ::: Research Works Related |
| `Q_QASP_159` | `1706.08198` | Conclusion | 🔴 | 0.7726 | 1.0000 | Introduction |
| `Q_QASP_160` | `1706.08198` | Datasets | 🟢 | 1.0000 | 1.0000 | Datasets |
| `Q_QASP_161` | `1909.08089` | Results and Analysis | 🔴 | 0.2184 | 1.0000 | Introduction |
| `Q_QASP_162` | `1909.08089` | Introduction | 🔴 | 0.1934 | 1.0000 | Decoder |
| `Q_QASP_164` | `1910.09982` | Data | 🔴 | 0.0000 | 0.5000 | Participants and Approaches ::: Teams Pa |
| `Q_QASP_165` | `1910.09982` | Baselines | 🟢 | 1.0000 | 1.0000 | Baselines |
| `Q_QASP_166` | `1609.00559` | Introduction | 🔴 | 0.6309 | 1.0000 | Method |
| `Q_QASP_167` | `1609.00559` | Data | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_168` | `1609.00559` | Comparison with Previous Work | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_169` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 1.0000 | Decoding the KB Query |
| `Q_QASP_170` | `1604.00727` | Dataset and Experimental Settings | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_171` | `1612.02482` | Introduction | 🔴 | 0.0000 | 0.0000 | Related Work |
| `Q_QASP_173` | `1608.01084` | Data Set and Toolkits | 🟢 | 0.0000 | 0.0000 | Data Set and Toolkits |
| `Q_QASP_174` | `1904.10503` | Introduction | 🔴 | 1.0000 | 1.0000 | Conclusion and Future Work |
| `Q_QASP_175` | `1904.10503` | Results | 🔴 | 0.6509 | 1.0000 | Introduction |
| `Q_QASP_176` | `1904.10503` | Entity Linking using Wikidata | 🔴 | 0.2140 | 0.8000 | Abstract |
| `Q_QASP_177` | `1912.01772` | Introduction | 🔴 | 0.5464 | 0.7778 | Abstract |
| `Q_QASP_178` | `1912.01772` | The Resource ::: Additional Annotat | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_179` | `1603.01987` | The medical domain model | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_180` | `1908.06941` | PMI & Matrix Factorization | 🔴 | 0.2382 | 1.0000 | Abstract |
| `Q_QASP_181` | `1908.06941` | Materials | 🔴 | 0.4585 | 1.0000 | Abstract |
| `Q_QASP_182` | `1908.06941` | Results | 🔴 | 0.1846 | 1.0000 | Related Work |
| `Q_QASP_183` | `1908.06941` | Introduction | 🔴 | 0.6934 | 1.0000 | Abstract |
| `Q_QASP_184` | `1702.03856` | Introduction | 🟢 | 1.0000 | 1.0000 | Introduction |
| `Q_QASP_185` | `1702.03856` | Introduction | 🔴 | 0.6332 | 1.0000 | Analysis of challenges from UTD |
| `Q_QASP_186` | `1702.03856` | Dataset | 🔴 | 0.3562 | 1.0000 | Introduction |
| `Q_QASP_187` | `1904.01548` | Related Work | 🔴 | 0.0843 | 0.8750 | Abstract |
| `Q_QASP_188` | `1904.01548` | Related Work | 🔴 | 0.6188 | 0.7500 | Discussion |
| `Q_QASP_189` | `1606.03676` | Corpora | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_190` | `1606.03676` | Corpora | 🔴 | 0.6241 | 1.0000 | Introduction |
| `Q_QASP_191` | `1802.00396` | Introduction | 🔴 | 0.0000 | 0.0000 | Network Analysis |
| `Q_QASP_192` | `1802.00396` | UN votes and speeches | 🟢 | 0.6131 | 1.0000 | UN votes and speeches |
| `Q_QASP_193` | `1911.03343` | Introduction | 🔴 | 0.4306 | 1.0000 | Abstract |
| `Q_QASP_194` | `1712.00991` | Evaluation of auto-generated summar | 🟢 | 1.0000 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_195` | `1712.00991` | Evaluation of auto-generated summar | 🟢 | 0.9197 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_196` | `1712.00991` | Discovering Clusters within Sentenc | 🔴 | 0.3380 | 0.6667 | Evaluation of auto-generated summaries |
| `Q_QASP_197` | `1712.00991` | PA along Attributes | 🔴 | 0.1480 | 1.0000 | Introduction |
| `Q_QASP_198` | `1712.00991` | Sentence Classification | 🔴 | 0.4441 | 1.0000 | Conclusions and Further Work |
| `Q_QASP_199` | `1712.00991` | Dataset | 🔴 | 0.6309 | 1.0000 | Evaluation of auto-generated summaries |
| `Q_QASP_200` | `1712.00991` | Dataset | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_201` | `1805.08241` | Experiments | 🔴 | 0.2641 | 1.0000 | Fertility Bounds |
| `Q_QASP_202` | `1907.04433` | Performance | 🔴 | 0.0000 | 1.0000 | Abstract |
| `Q_QASP_204` | `2003.04642` | Framework for MRC Gold Standard Ana | 🔴 | 0.4911 | 1.0000 | Abstract |
| `Q_QASP_205` | `2003.04642` | Application of the Framework ::: Ca | 🔴 | 0.0000 | 0.5000 | Abstract |
| `Q_QASP_206` | `2003.04642` | Introduction | 🔴 | 0.6131 | 1.0000 | Framework for MRC Gold Standard Analysis |
| `Q_QASP_208` | `2001.09215` | Proposed Methodology | 🔴 | 0.3562 | 1.0000 | Abstract |
| `Q_QASP_209` | `1909.07575` | Experiments ::: Baseline Models and | 🔴 | 0.5508 | 1.0000 | Abstract |
| `Q_QASP_210` | `1909.07575` | Our method ::: Training Procedure : | 🔴 | 0.0000 | 0.0000 | Introduction |
| `Q_QASP_211` | `1701.04056` | Interactive Dialog Context LM | 🔴 | 0.2961 | 0.6667 | Results and Analysis |
| `Q_QASP_212` | `1904.07904` | Spoken Question Answering | 🟢 | 1.0000 | 1.0000 | Spoken Question Answering |
| `Q_QASP_213` | `1904.07904` | Results | 🔴 | 0.6509 | 1.0000 | Conclusion |
| `Q_QASP_214` | `1904.07904` | Results | 🔴 | 0.4367 | 1.0000 | Conclusion |
| `Q_QASP_215` | `1904.07904` | Corpus | 🔴 | 0.0000 | 1.0000 | Introduction |
| `Q_QASP_216` | `2003.11645` | Introduction | 🔴 | 1.0000 | 1.0000 | Methodology |
| `Q_QASP_217` | `2003.11645` | Introduction | 🔴 | 0.5110 | 1.0000 | Abstract |
| `Q_QASP_218` | `2003.11645` | Introduction | 🟢 | 0.7977 | 1.0000 | Introduction |
| `Q_QASP_219` | `2003.11645` | Introduction | 🔴 | 0.0000 | 1.0000 | Literature Review |
| `Q_QASP_220` | `1909.02304` | Experiments ::: Results ::: Automat | 🔴 | 0.0000 | 0.4000 | Introduction |
| `Q_QASP_221` | `1909.02304` | Experiments ::: Results ::: Automat | 🔴 | 0.0867 | 0.2857 | Abstract |
| `Q_QASP_222` | `1604.03114` | Modeling Idea Flow | 🔴 | 0.2811 | 0.7500 | Abstract |
| `Q_QASP_223` | `1604.03114` | Debate Dataset: Intelligence Square | 🟢 | 1.0000 | 1.0000 | Debate Dataset: Intelligence Squared |
| `Q_QASP_225` | `2001.03131` | Introduction | 🔴 | 0.0000 | 0.0000 | Experiments and Discussions ::: Results  |
| `Q_QASP_226` | `2001.03131` | Proposed Approach | 🔴 | 0.5000 | 1.0000 | Abstract |
| `Q_QASP_227` | `1606.02891` | Baseline System | 🔴 | 0.5250 | 1.0000 | Abstract |
| `Q_QASP_228` | `1803.09123` | Empirical Study | 🔴 | 0.1952 | 0.7500 | Equation Embeddings Models |
| `Q_QASP_229` | `1803.09123` | Discovering Semantically Similar Eq | 🟢 | 0.7087 | 1.0000 | Discovering Semantically Similar Equatio |
| `Q_QASP_230` | `1910.01863` | Text Generation ::: Baseline Experi | 🔴 | 0.5337 | 0.7273 | Text Generation |
| `Q_QASP_231` | `1701.08229` | METHODS | 🔴 | 0.4228 | 1.0000 | Feature Elimination |
| `Q_QASP_232` | `1701.08229` | Feature Elimination | 🟢 | 0.7977 | 1.0000 | Feature Elimination |
| `Q_QASP_233` | `1701.08229` | METHODS | 🟢 | 0.9197 | 1.0000 | METHODS |
| `Q_QASP_234` | `1701.08229` | METHODS | 🟢 | 0.6131 | 1.0000 | METHODS |
| `Q_QASP_235` | `1912.06262` | Experiments ::: Results | 🔴 | 0.0000 | 1.0000 | Experiments ::: Hyperparameter Tuning |
| `Q_QASP_236` | `1912.06262` | Experiments ::: Data | 🔴 | 0.2372 | 0.5000 | Abstract |
| `Q_QASP_237` | `1709.07814` | Attention-based Encoder Decoder for | 🟢 | 0.7495 | 1.0000 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_238` | `1709.07814` | Attention-based Encoder Decoder for | 🔴 | 0.4660 | 1.0000 | Speech Data |
| `Q_QASP_239` | `1709.07814` | Speech Data | 🔴 | 0.1510 | 0.2500 | Attention-based Encoder Decoder for Raw  |
| `Q_QASP_240` | `1806.00738` | Model | 🔴 | 0.5574 | 1.0000 | Introduction |
| `Q_QASP_241` | `1806.00738` | Decoder | 🔴 | 0.2856 | 1.0000 | Methodology |
| `Q_QASP_242` | `1806.00738` | Encoder | 🔴 | 0.6053 | 1.0000 | Decoder |
| `Q_QASP_243` | `1806.00738` | Decoder | 🟢 | 0.8316 | 1.0000 | Decoder |
| `Q_QASP_244` | `1811.00147` | Dolores: Learner | 🟢 | 0.6131 | 0.5000 | Dolores: Learner |
| `Q_QASP_245` | `1811.00147` | Dolores: Learner | 🔴 | 0.0000 | 0.2500 | Problem Formulation |
| `Q_QASP_246` | `1610.09225` | Introduction | 🟢 | 0.2333 | 0.8000 | Introduction |
| `Q_QASP_247` | `1610.09225` | Feature Extraction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_248` | `1610.09225` | Data Collection | 🔴 | 0.0000 | 0.5000 | Sentiment Analyzer Results |
| `Q_QASP_249` | `2003.08380` | Results | 🔴 | 0.6309 | 1.0000 | Abstract |
| `Q_QASP_250` | `1811.05711` | Multiscale graph partitioning for t | 🔴 | 0.2794 | 0.6667 | Abstract |
| `Q_QASP_251` | `1805.04508` | Gender Bias Results | 🔴 | 0.2769 | 1.0000 | Abstract |
| `Q_QASP_252` | `1805.04508` | The Equity Evaluation Corpus | 🔴 | 0.4247 | 0.7500 | Introduction |
| `Q_QASP_253` | `1904.03288` | Conversational Speech | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_254` | `1904.03288` | Read Speech | 🔴 | 0.5714 | 1.0000 | Introduction |
| `Q_QASP_256` | `1909.13714` | Methodology | 🔴 | 0.3869 | 1.0000 | Abstract |
| `Q_QASP_257` | `1910.05603` | Introduction | 🔴 | 0.0000 | 0.0000 | Abstract |
| `Q_QASP_258` | `1910.05603` | System Description ::: Language Mod | 🟢 | 0.7845 | 1.0000 | System Description ::: Language Model |
| `Q_QASP_259` | `1910.05603` | Experiments ::: System combination | 🔴 | 0.5000 | 1.0000 | Conclusion |
| `Q_QASP_260` | `1910.05603` | System Description ::: Acoustic Mod | 🔴 | 0.3562 | 1.0000 | Experiments ::: Single system evaluation |
| `Q_QASP_261` | `1909.03405` | Results of NLI Tasks ::: GLUE | 🔴 | 0.3155 | 1.0000 | Abstract |
| `Q_QASP_262` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |
| `Q_QASP_263` | `1909.03405` | Experiment Settings | 🔴 | 0.0000 | 0.0000 | Related Work ::: Pair-wise semantic reas |

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
