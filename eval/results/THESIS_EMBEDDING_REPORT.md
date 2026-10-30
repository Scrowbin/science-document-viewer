# Graduation Thesis Benchmark Report: Open-Source Dense Embedding Evaluation for Desktop Scientific Document RAG

**Title:** Empirical Evaluation of Open-Source Dense Encoders (<= 335M Parameters) for Grounded Academic Passage Retrieval on Resource-Constrained Hardware  
**Target Architecture:** AMD Ryzen 5 5600 6-Core / 12-Thread Processor, 16 GB Desktop RAM, Local Single-Node CPU Deployment alongside Ollama (`llama3.2:3b`)  
**Evaluation Scope:** Unified 207-Paper / 615-Query / 5,207-Chunk Academic Literature Corpus (`eval/prepared/`)  
**Evaluation Engine:** Exact Cosine Similarity (NumPy BLAS on FP32 Unit-Normalized Vectors) Decoupled from ANN Index Truncation  
**Date:** October 18, 2026  
**Artifact Directory:** [`eval/results/`](file:///c:/DACNTT/eval/results/)  

---

## 1. Executive Summary & Key Thesis Findings

This report delivers the empirical and statistical foundation for the graduation thesis on the **Scientific Document Retrieval-Augmented Generation (RAG)** pipeline. We evaluated **11 open-source, non-gated models (MIT / Apache-2.0, $\le 335\text{M}$ parameters)** on the unified academic development corpus (207 papers, 615 queries, 5,207 passage chunks) using exact cosine similarity and paper-cluster bootstrap inference ($B=2,000$ resamples). Hardware efficiency was profiled under fixed single-node CPU allocation (`torch.set_num_threads(4)`) on an AMD Ryzen 5 5600.

### Core Discoveries:
1. **High Retrieval Quality:**
   - **`nomic-ai/modernbert-embed-base`** (149.0M parameters, 768-dim) achieves the highest accuracy across metrics: **0.5872 nDCG@10**, **0.4937 nDCG@4**, **0.9642 Recall@20**, and **0.5283 MRR@10**.
   - Statistically outperforms the baseline `all-MiniLM-L6-v2` by **$\Delta = +0.0846$ nDCG@10** ($p = 0.0010^*$, 95% Clustered CI $[+0.0627, +0.1075]$).
2. **The Practical Champion for Local Production Deployment:**
   - **`intfloat/e5-small-v2`** (33.4M parameters, 384-dim) achieves **0.5522 nDCG@10** ($\Delta = +0.0497$ over baseline, $p = 0.0010^*$, 95% CI $[+0.0262, +0.0741]$).
   - Delivers **3.4x faster single-query latency** (30.26 ms vs 103.39 ms) and **3.6x higher indexing throughput** (6.5 vs 1.8 chunks/sec) while consuming only **799.3 MB peak RAM**, fitting comfortably alongside Ollama on 16 GB RAM.
3. **Parameter Scaling Limits:**
   - The largest candidate, **`mixedbread-ai/mxbai-embed-large-v1`** (335.1M parameters, 1024-dim), scored **0.5064 nDCG@10** ($\Delta = +0.0039$, $p = 0.7236$ ns), failing to statistically separate from the 22.7M MiniLM baseline despite using **14.8x more parameters**.
   - **`snowflake-arctic-embed-m-v2.0`** (305.0M parameters) degraded performance (**0.4809 nDCG@10**, falling below baseline).
   - **Insight:** Specialized contrastive objectives and modern pretraining decisively outperform raw parameter scaling for passage retrieval on CPU.

---

## 2. Master Benchmark Results Table

All 11 candidate models evaluated under identical conditions on the unified 207-paper / 615-query / 5,207-chunk corpus:

| # | Model Architecture | Parameters | Embedding Dim | License | nDCG@10 (Primary) [95% CI] | nDCG@4 | Recall@20 | MRR@10 | Indexing Throughput ($B=32$) | Query Latency P50 ($B=1$) | Query Latency P95 ($B=1$) | Peak RSS (MB) |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **`BM25 [WordPiece Subwords]`** | — | — | MIT | 0.4805 [0.4480, 0.5130] | 0.3779 | 0.9363 | 0.4197 | **14,673.3 ch/s** | **0.10 ms** | **0.21 ms** | **477.9 MB** |
| 2 | **`all-MiniLM-L6-v2`** *(Baseline)* | 22.7M | 384 | Apache-2.0 | 0.5026 [0.4746, 0.5315] | 0.3938 | 0.9483 | 0.4417 | **19.0 ch/s** | **19.30 ms** | 30.01 ms | **619.0 MB** |
| 3 | **`intfloat/e5-small-v2`** *(Champion)* | 33.4M | 384 | MIT | **0.5522** [0.5253, 0.5778] | **0.4588** | 0.9623 | **0.4907** | **6.5 ch/s** | **30.26 ms** | 39.63 ms | **799.3 MB** |
| 4 | **`BAAI/bge-small-en-v1.5`** | 33.4M | 384 | MIT | 0.5209 [0.4901, 0.5520] | 0.4214 | 0.9542 | 0.4571 | 6.5 ch/s | 34.14 ms | 44.13 ms | 772.7 MB |
| 5 | **`thenlper/gte-small`** | 33.4M | 384 | Apache-2.0 | 0.4659 [0.4358, 0.4957] | 0.3585 | 0.9329 | 0.4079 | 6.3 ch/s | 29.42 ms | 42.14 ms | 773.0 MB |
| 6 | **`Snowflake/snowflake-arctic-embed-s`** | 33.2M | 384 | Apache-2.0 | 0.5417 [0.5115, 0.5714] | 0.4453 | 0.9523 | 0.4788 | 7.0 ch/s | 30.45 ms | 42.17 ms | 767.9 MB |
| 7 | **`Snowflake/snowflake-arctic-embed-m-v1.5`** | 108.9M | 768 | Apache-2.0 | 0.5472 [0.5186, 0.5756] | 0.4531 | 0.9433 | 0.4851 | 2.4 ch/s | 74.44 ms | 98.54 ms | 1,207.2 MB |
| 8 | **`nomic-ai/nomic-embed-text-v1.5`** | 137.0M | 768 | Apache-2.0 | 0.5133 [0.4843, 0.5422] | 0.4219 | 0.9553 | 0.4503 | 1.6 ch/s | 110.19 ms | 143.15 ms | 1,327.9 MB |
| 9 | **`nomic-ai/modernbert-embed-base`** | 149.0M | 768 | Apache-2.0 | **0.5872** [0.5586, 0.6166] | **0.4937** | **0.9642** | **0.5283** | 1.8 ch/s | 103.39 ms | 137.49 ms | 1,390.8 MB |
| 10 | **`Snowflake/snowflake-arctic-embed-m-v2.0`** | 305.0M | 768 | Apache-2.0 | 0.4809 [0.4512, 0.5090] | 0.3742 | 0.9481 | 0.4137 | 2.2 ch/s | 114.49 ms | 148.65 ms | 2,012.8 MB |
| 11 | **`mixedbread-ai/mxbai-embed-large-v1`** | 335.1M | 1024 | Apache-2.0 | 0.5064 [0.4776, 0.5344] | 0.4177 | 0.9469 | 0.4497 | 0.6 ch/s | 275.34 ms | 337.81 ms | 2,116.3 MB |

---

## 3. Paired Statistical Significance Analysis vs. Baseline (`all-MiniLM-L6-v2`)

Statistical significance evaluated via **two-sided paper-cluster bootstrap resampling** ($B=2,000$, `seed=42`) on the primary metric **nDCG@10**:

| Candidate Model | $\Delta \text{nDCG@10}$ vs MiniLM | 95% Bootstrap Confidence Interval | Bootstrap $p$-value | Statistically Significant at $\alpha=0.05$? | Scientific Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`nomic-ai/modernbert-embed-base`** | **+0.0846** | **$[+0.0627, +0.1075]$** | **$0.0010^*$** | **YES (Dominant)** | Decisive superiority; lower CI bound $> +0.062$ |
| **`intfloat/e5-small-v2`** | **+0.0497** | **$[+0.0262, +0.0741]$** | **$0.0010^*$** | **YES (Significant)** | Substantial gain; CI excludes zero comfortably |
| **`Snowflake/snowflake-arctic-embed-m-v1.5`** | **+0.0447** | **$[+0.0219, +0.0670]$** | **$0.0010^*$** | **YES (Significant)** | Moderate gain, but 2.5x slower than E5-small |
| **`Snowflake/snowflake-arctic-embed-s`** | **+0.0392** | **$[+0.0171, +0.0625]$** | **$0.0020^*$** | **YES (Significant)** | Strong small-model contender |
| **`BAAI/bge-small-en-v1.5`** | +0.0183 | $[-0.0027, +0.0393]$ | $0.0830$ | NO (ns) | 95% CI spans zero; fails to separate from MiniLM |
| **`nomic-ai/nomic-embed-text-v1.5`** | +0.0108 | $[-0.0106, +0.0337]$ | $0.3418$ | NO (ns) | Inconclusive; does not justify latency penalty |
| **`mixedbread-ai/mxbai-embed-large-v1`** | +0.0039 | $[-0.0173, +0.0265]$ | $0.7236$ | NO (ns) | Severe failure to separate despite 335M params |
| **`BM25 [WordPiece]`** | -0.0220 | $[-0.0522, +0.0091]$ | $0.1739$ | NO (ns) | Strong sparse baseline; competitive with dense base |
| **`Snowflake/snowflake-arctic-embed-m-v2.0`** | -0.0216 | $[-0.0465, +0.0033]$ | $0.0950$ | NO (ns) | Underperforms baseline despite 305M params |
| **`thenlper/gte-small`** | -0.0367 | $[-0.0599, -0.0135]$ | $0.0010^*$ | **YES (Degraded)** | Statistically significantly worse than MiniLM |

---

## 4. Hardware Efficiency & Latency Profiling

The efficiency profiles measured on the host **AMD Ryzen 5 5600 CPU** (`torch.set_num_threads(4)`) highlight practical considerations for desktop deployment:

* **Latency Trade-offs:** Small models (`all-MiniLM-L6-v2` at 19.3 ms, `e5-small-v2` at 30.3 ms) deliver immediate response times in interactive chat. In contrast, models $>100\text{M}$ parameters require 75–110 ms, and $>300\text{M}$ models exceed 275 ms per query.
* **Indexing Throughput:** `all-MiniLM-L6-v2` achieves 19.0 chunks/sec, and `e5-small-v2` achieves 6.5 chunks/sec, enabling full-paper indexing in under 10 seconds. Larger models drop below 2 chunks/sec.
* **Memory Footprint:** `e5-small-v2` consumes under 800 MB peak RSS, leaving ample memory for running Ollama (`llama3.2:3b`) locally on a 16 GB machine.

---
---

## 5. Vector Storage & Practical Deployment Architecture

Based on the empirical findings, the system employs a dual-tier search approach tailored to scientific document workflows:

1. **Single-Document Reader Mode (`DocumentRAG` in-memory):**
   * When interacting with a single active document in the viewer, the candidate pool is compact ($N \le 100$ chunks).
   * Exact cosine similarity (`query_emb @ doc_embs.T`) executes in $<0.2$ ms on CPU, delivering exact candidate ranking with zero index construction overhead.
2. **Library-Wide Search Mode (`RagService` via Qdrant):**
   * For cross-document search across collections, vectors are indexed in Qdrant with standard parameters ($M=16, ef_{\text{construct}}=128, ef_{\text{search}}=64$).
   * This provides sub-6 ms search latency and high candidate recall without memory bloat.

### Recommended Production Deployment: `intfloat/e5-small-v2`
* **Rationale:** At 33.4M parameters, `e5-small-v2` offers the best balance for desktop hardware. Its 30 ms query latency ensures fluid chat interactions, its 799 MB RAM usage leaves plenty of headroom for Ollama (`llama3.2:3b`), and its **0.5522 nDCG@10** provides a statistically significant improvement over the baseline.
* **Prefix Requirement:** Enforces `"query: "` on search questions and `"passage: "` on chunks.

---

## 6. Artifact & Code Traceability

| Artifact Description | File Path |
| :--- | :--- |
| **Raw Benchmark Metrics JSON** | [`eval/results/thesis_embedding_benchmark.json`](file:///c:/DACNTT/eval/results/thesis_embedding_benchmark.json) |
| **Benchmark Runner Script** | [`backend/scripts/evaluation/run_thesis_embedding_benchmark.py`](file:///c:/DACNTT/backend/scripts/evaluation/run_thesis_embedding_benchmark.py) |
| **Shared Canonical Evaluation Utils** | [`backend/scripts/eval_common.py`](file:///c:/DACNTT/backend/scripts/eval_common.py) |
| **RAG Service Implementation** | [`backend/apps/documents/services/rag_service.py`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py) |

