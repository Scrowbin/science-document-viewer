# ResearchQA Method A — Survey Section Ground-Truth Retrieval Report

> **Generated:** `2026-10-30T04:09:59.306060 UTC`  
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
| `bm25` | 1.0000 | 1.0000 *(±0.000 CI)* | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `dense` | 1.0000 | 1.0000 *(±0.000 CI)* | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| `hybrid_rrf` | 1.0000 | 1.0000 *(±0.000 CI)* | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

### 2.1 Comparison vs QASPER Held-Out Baselines

| Dataset / Method | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 |
| :--- | :---: | :---: | :---: | :---: |
| QASPER BM25 *(reference)* | 0.3812 | 0.4103 | 0.4521 | 0.8930 |
| QASPER Dense E5 *(reference)* | 0.4952 | 0.5213 | 0.5814 | 0.9256 |
| QASPER Hybrid RRF *(reference)* | 0.5121 | 0.5384 | 0.5991 | 0.9560 |
| **ResearchQA Survey `bm25`** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |
| **ResearchQA Survey `dense`** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |
| **ResearchQA Survey `hybrid_rrf`** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

---

## 3. Dev / Held-Out Split Breakdown

### Strategy: `bm25`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| dev | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| held_out | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

### Strategy: `dense`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| dev | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| held_out | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

### Strategy: `hybrid_rrf`

| Split | n | nDCG@4 | nDCG@10 | MRR@5 | Recall@20 | Section Hit@1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| dev | 4 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| held_out | 3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

---

## 4. Per-Query Detail

### `bm25` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_RQA_SURV_001` | `SURVEY_CS_TRANSFORMERS` | 2. IO-Aware Exact Attention & Tilin | 🟢 | 1.0000 | 1.0000 | 2. IO-Aware Exact Attention & Tiling |
| `Q_RQA_SURV_002` | `SURVEY_CS_TRANSFORMERS` | 3. Rotary Position Embeddings (RoPE | 🟢 | 1.0000 | 1.0000 | 3. Rotary Position Embeddings (RoPE) and |
| `Q_RQA_SURV_003` | `SURVEY_CS_TRANSFORMERS` | 4. KV-Cache Compression and Multi-Q | 🟢 | 1.0000 | 1.0000 | 4. KV-Cache Compression and Multi-Query  |
| `Q_RQA_SURV_004` | `SURVEY_BIO_STRUCTURAL` | 2. Evoformer Representations and In | 🟢 | 1.0000 | 1.0000 | 2. Evoformer Representations and Invaria |
| `Q_RQA_SURV_005` | `SURVEY_SYS_CONSENSUS` | 2. Paxos Deconstruction vs. Raft Un | 🟢 | 1.0000 | 1.0000 | 2. Paxos Deconstruction vs. Raft Underst |
| `Q_RQA_SURV_006` | `SURVEY_SYS_CONSENSUS` | 3. Linearizable Read Optimizations  | 🟢 | 1.0000 | 1.0000 | 3. Linearizable Read Optimizations & Lea |
| `Q_RQA_SURV_007` | `SURVEY_AI_AGENTS` | 3. Reasoning and Planning Framework | 🟢 | 1.0000 | 1.0000 | 3. Reasoning and Planning Frameworks |

### `dense` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_RQA_SURV_001` | `SURVEY_CS_TRANSFORMERS` | 2. IO-Aware Exact Attention & Tilin | 🟢 | 1.0000 | 1.0000 | 2. IO-Aware Exact Attention & Tiling |
| `Q_RQA_SURV_002` | `SURVEY_CS_TRANSFORMERS` | 3. Rotary Position Embeddings (RoPE | 🟢 | 1.0000 | 1.0000 | 3. Rotary Position Embeddings (RoPE) and |
| `Q_RQA_SURV_003` | `SURVEY_CS_TRANSFORMERS` | 4. KV-Cache Compression and Multi-Q | 🟢 | 1.0000 | 1.0000 | 4. KV-Cache Compression and Multi-Query  |
| `Q_RQA_SURV_004` | `SURVEY_BIO_STRUCTURAL` | 2. Evoformer Representations and In | 🟢 | 1.0000 | 1.0000 | 2. Evoformer Representations and Invaria |
| `Q_RQA_SURV_005` | `SURVEY_SYS_CONSENSUS` | 2. Paxos Deconstruction vs. Raft Un | 🟢 | 1.0000 | 1.0000 | 2. Paxos Deconstruction vs. Raft Underst |
| `Q_RQA_SURV_006` | `SURVEY_SYS_CONSENSUS` | 3. Linearizable Read Optimizations  | 🟢 | 1.0000 | 1.0000 | 3. Linearizable Read Optimizations & Lea |
| `Q_RQA_SURV_007` | `SURVEY_AI_AGENTS` | 3. Reasoning and Planning Framework | 🟢 | 1.0000 | 1.0000 | 3. Reasoning and Planning Frameworks |

### `hybrid_rrf` — Per-Query Results

| Query ID | Paper | Target Section | Section Hit@1 | nDCG@10 | Recall@20 | Top-1 Section Retrieved |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `Q_RQA_SURV_001` | `SURVEY_CS_TRANSFORMERS` | 2. IO-Aware Exact Attention & Tilin | 🟢 | 1.0000 | 1.0000 | 2. IO-Aware Exact Attention & Tiling |
| `Q_RQA_SURV_002` | `SURVEY_CS_TRANSFORMERS` | 3. Rotary Position Embeddings (RoPE | 🟢 | 1.0000 | 1.0000 | 3. Rotary Position Embeddings (RoPE) and |
| `Q_RQA_SURV_003` | `SURVEY_CS_TRANSFORMERS` | 4. KV-Cache Compression and Multi-Q | 🟢 | 1.0000 | 1.0000 | 4. KV-Cache Compression and Multi-Query  |
| `Q_RQA_SURV_004` | `SURVEY_BIO_STRUCTURAL` | 2. Evoformer Representations and In | 🟢 | 1.0000 | 1.0000 | 2. Evoformer Representations and Invaria |
| `Q_RQA_SURV_005` | `SURVEY_SYS_CONSENSUS` | 2. Paxos Deconstruction vs. Raft Un | 🟢 | 1.0000 | 1.0000 | 2. Paxos Deconstruction vs. Raft Underst |
| `Q_RQA_SURV_006` | `SURVEY_SYS_CONSENSUS` | 3. Linearizable Read Optimizations  | 🟢 | 1.0000 | 1.0000 | 3. Linearizable Read Optimizations & Lea |
| `Q_RQA_SURV_007` | `SURVEY_AI_AGENTS` | 3. Reasoning and Planning Framework | 🟢 | 1.0000 | 1.0000 | 3. Reasoning and Planning Frameworks |

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
