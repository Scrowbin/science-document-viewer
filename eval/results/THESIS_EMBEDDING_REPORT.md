# Graduation Thesis Benchmark Report: Open-Source Dense Embedding Evaluation & Pareto Efficiency for Desktop Scientific Document RAG

**Title:** Empirical Evaluation of Open-Source Dense Encoders (<= 335M Parameters) for Grounded Academic Passage Retrieval on Resource-Constrained Hardware  
**Target Architecture:** AMD Ryzen 5 5600 6-Core / 12-Thread Processor, 16 GB Desktop RAM, Local Single-Node CPU Deployment alongside Ollama (`llama3.2:3b`)  
**Evaluation Scope:** Unified 207-Paper / 615-Query / 5,207-Chunk Academic Literature Corpus (`eval/prepared/`)  
**Evaluation Engine:** Exact Brute-Force Cosine Similarity (NumPy BLAS on FP32 Unit-Normalized Vectors) Decoupled from ANN Index Truncation  
**Date:** October 18, 2026  
**Artifact Directory:** [`eval/results/`](file:///c:/DACNTT/eval/results/)  

---

## 1. Executive Summary & Key Thesis Findings

This report delivers the empirical and statistical foundation for the graduation thesis on the **Scientific Document Retrieval-Augmented Generation (RAG)** pipeline. We evaluated **11 open-source, non-gated models (MIT / Apache-2.0, $\le 335\text{M}$ parameters)** on the unified academic development corpus (207 papers, 615 queries, 5,207 passage chunks) using exact cosine similarity and paper-cluster bootstrap inference ($B=2,000$ resamples). Hardware efficiency was profiled under fixed single-node CPU allocation (`torch.set_num_threads(4)`) on an AMD Ryzen 5 5600.

### Core Discoveries:
1. **The ModernBERT Revolution (Highest Absolute Retrieval Quality):**
   - **`nomic-ai/modernbert-embed-base`** (149.0M parameters, 768-dim) achieves the highest accuracy across every metric: **0.5872 nDCG@10**, **0.4937 nDCG@4**, **0.9642 Recall@20**, and **0.5283 MRR@10**.
   - Statistically dominates the production baseline `all-MiniLM-L6-v2` by **$\Delta = +0.0846$ nDCG@10** ($p = 0.0010^*$, 95% Clustered CI $[+0.0627, +0.1075]$).
2. **The Small Champion for Production Deployment (Optimal Desktop Trade-Off):**
   - **`intfloat/e5-small-v2`** (33.4M parameters, 384-dim) achieves **0.5522 nDCG@10** ($\Delta = +0.0497$ over baseline, $p = 0.0010^*$, 95% CI $[+0.0262, +0.0741]$).
   - Delivers **3.4x faster single-query latency** (30.26 ms vs 103.39 ms) and **3.6x higher indexing throughput** (6.5 vs 1.8 chunks/sec) while consuming only **799.3 MB peak RAM** (allowing comfortable co-existence with Ollama on 16 GB RAM).
3. **The Parameter Saturation Paradox (Disproving "Bigger is Better"):**
   - The largest candidate, **`mixedbread-ai/mxbai-embed-large-v1`** (335.1M parameters, 1024-dim), scored **0.5064 nDCG@10** ($\Delta = +0.0039$, $p = 0.7236$ ns), failing to statistically separate from the 22.7M MiniLM baseline despite using **14.8x more parameters**.
   - **`snowflake-arctic-embed-m-v2.0`** (305.0M parameters) degraded performance (**0.4809 nDCG@10**, falling below baseline).
   - **Thesis Insight:** Pre-training architecture and contrastive loss objectives (e.g., ModernBERT's unpadded flash-attention pretraining and E5's weak-supervision contrastive tuning) decisively outperform sheer parameter scaling for domain-specific passage retrieval.
4. **Pareto Optimal Frontier:**
   - Only 4 models define the Pareto frontier across accuracy vs. efficiency:
     $$\text{BM25 (Sparse)} \longrightarrow \text{MiniLM-L6-v2 (22.7M)} \longrightarrow \text{E5-Small-v2 (33.4M)} \longrightarrow \text{ModernBERT-Embed (149M)}$$

---

## 2. Master Benchmark Results Table

All 11 candidate models evaluated under identical conditions on the unified 207-paper / 615-query / 5,207-chunk corpus:

| # | Model Architecture | Parameters | Embedding Dim | License | nDCG@10 (Primary) [95% CI] | nDCG@4 | Recall@20 | MRR@10 | Indexing Throughput ($B=32$) | Query Latency P50 ($B=1$) | Query Latency P95 ($B=1$) | Peak RSS (MB) |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
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
| **`nomic-ai/nomic-embed-text-v1.5`** | +0.0108 | $[-0.0106, +0.0337]$ | $0.3418$ | NO (ns) | Inconclusive; does not justify 6x latency penalty |
| **`mixedbread-ai/mxbai-embed-large-v1`** | +0.0039 | $[-0.0173, +0.0265]$ | $0.7236$ | NO (ns) | Severe failure to separate despite 335M params |
| **`BM25 [WordPiece]`** | -0.0220 | $[-0.0522, +0.0091]$ | $0.1739$ | NO (ns) | Strong sparse baseline; competitive with dense base |
| **`Snowflake/snowflake-arctic-embed-m-v2.0`** | -0.0216 | $[-0.0465, +0.0033]$ | $0.0950$ | NO (ns) | Underperforms baseline despite 305M params |
| **`thenlper/gte-small`** | -0.0367 | $[-0.0599, -0.0135]$ | $0.0010^*$ | **YES (Degraded)** | Statistically significantly worse than MiniLM |

---

## 4. Hardware Efficiency & Pareto Frontier Analysis

The efficiency profiles measured on the host **AMD Ryzen 5 5600 CPU** reveal distinct engineering trade-offs:

### 4.1. Accuracy vs. Single-Query Latency
* **Artifact Generated:** [`eval/results/figures/pareto_ndcg10_vs_latency.png`](file:///c:/DACNTT/eval/results/figures/pareto_ndcg10_vs_latency.png) (Vector PDF: [`pareto_ndcg10_vs_latency.pdf`](file:///c:/DACNTT/eval/results/figures/pareto_ndcg10_vs_latency.pdf))
* **Pareto Frontier Points (Minimize Latency, Maximize Accuracy):**
  1. `BM25`: 0.10 ms latency, 0.4805 nDCG@10 (Ultra-low latency sparse reference)
  2. `all-MiniLM-L6-v2`: 19.30 ms latency, 0.5026 nDCG@10 (Fastest dense encoder)
  3. `e5-small-v2`: 30.26 ms latency, 0.5522 nDCG@10 (Best accuracy per millisecond)
  4. `modernbert-embed-base`: 103.39 ms latency, 0.5872 nDCG@10 (Accuracy ceiling)
* **Dominated Models:** All other models lie strictly beneath the frontier. In particular, `mxbai-embed-large-v1` requires 275.34 ms (nearly 10x slower than E5) while delivering 0.0458 lower nDCG@10.

### 4.2. Accuracy vs. Document Indexing Throughput
* **Artifact Generated:** [`eval/results/figures/pareto_ndcg10_vs_throughput.png`](file:///c:/DACNTT/eval/results/figures/pareto_ndcg10_vs_throughput.png) (Vector PDF: [`pareto_ndcg10_vs_throughput.pdf`](file:///c:/DACNTT/eval/results/figures/pareto_ndcg10_vs_throughput.pdf))
* **Pareto Frontier Points (Maximize Throughput, Maximize Accuracy):**
  1. `modernbert-embed-base`: 1.8 ch/s throughput, 0.5872 nDCG@10
  2. `e5-small-v2`: 6.5 ch/s throughput, 0.5522 nDCG@10
  3. `all-MiniLM-L6-v2`: 19.0 ch/s throughput, 0.5026 nDCG@10
  4. `BM25`: 14,673.3 ch/s throughput, 0.4805 nDCG@10

---

## 5. Out-of-Domain STEM Generalization (SciFact Sanity Check)

To ensure that the embedding representation quality is not an artifact of computer science or arXiv formatting conventions, models were evaluated zero-shot on the **SciFact biomedical claim verification dataset** (5,183 peer-reviewed PubMed abstracts across genetics, pharmacology, and oncology; [`evaluate_scifact_cross_dataset.py`](file:///c:/DACNTT/eval/phases/phase_3_embedding/scripts/evaluate_scifact_cross_dataset.py)):

| Model | Domain Role | SciFact nDCG@10 | SciFact Recall@100 | Zero-Shot Transfer Assessment |
| :--- | :--- | :---: | :---: | :--- |
| **`BAAI/bge-small-en-v1.5`** | Dense Contender | **0.7057** | **94.3%** | Strong general STEM transfer |
| **`intfloat/e5-small-v2`** | Dense Champion | **0.6955** | **93.1%** | Outstanding biomedical zero-shot recall |
| **`BM25 [WordPiece]`** | Sparse Reference | 0.6737 | 91.5% | Strong keyword match on abstract titles |
| **`all-MiniLM-L6-v2`** | Baseline Control | 0.6484 | 88.1% | Lags by $\ge +0.047$ nDCG@10 |

**Empirical Conclusion:** Modern contrastive encoders (`e5-small-v2` and `bge-small-en-v1.5`) beat the baseline by **+0.0471 to +0.0573 nDCG@10** on biomedical abstracts without fine-tuning, ruling out QASPER dataset memorization.


---

## 6. Vector Indexing & Approximate Nearest Neighbor (ANN) Scalability (Phase 4 — HNSW vs. Exact BLAS)

To evaluate the operational scalability and candidate retention of the vector storage layer, we benchmarked **Qdrant's Hierarchical Navigable Small World (HNSW)** graph index against an exact brute-force NumPy BLAS cosine oracle across our top three candidate models on a global multi-paper corpus of **4,108 academic text chunks and 487 queries across 160 papers** ([`hnsw_index_eval.ipynb`](file:///c:/DACNTT/hnsw_index_eval.ipynb)):

### 6.1. Methodology & Experimental Protocol
* **Decoupled Architecture:** Cleanly isolates dense embedding representation quality (measured in Chapter 2 via NumPy BLAS) from approximate nearest-neighbor index graph truncation.
* **Corpus & Search Space:** All 487 queries were searched against the entire unconstrained corpus of 4,108 chunks simultaneously, introducing thousands of realistic cross-paper academic distractors.
* **Evaluation Environment:** Official standalone Qdrant binary (`v1.13.2`) daemon executing under Google Colab CPU environment.
* **Parameter Sweep Grid:** Evaluated bi-directional links per node $M \in \{16, 32, 64\}$, index construction pool $ef_{\text{construct}} \in \{64, 128, 256\}$, and query search pool $ef_{\text{search}} \in \{16, 32, 64, 128, 256\}$.
* **Primary Metric:** **ANN Recall@10** (fraction of the exact top-10 BLAS candidates retained by HNSW graph traversal) alongside end-task global **nDCG@10**, single-query latency (P50/P95 in ms), Queries Per Second (QPS), and graph build time.

### 6.2. Master Cross-Model Summary at Optimal Operating Point
Under the recommended configuration (**$M=16, ef_{\text{construct}}=128, ef_{\text{search}}=64$**):

| Model Architecture | Vector Dim | Parameters | Global nDCG@10 | ANN Recall@10 (%) | Latency P50 (ms) | Latency P95 (ms) | Throughput (QPS) | Index Build Time (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`all-MiniLM-L6-v2`** *(Baseline)* | 384 | 22.7M | 0.1255 | **100.0%** | **4.17 ms** | 7.18 ms | **240.0** | **2.45 s** |
| **`intfloat/e5-small-v2`** *(Champion)* | 384 | 33.4M | 0.1539 | **100.0%** | **5.65 ms** | 10.44 ms | **176.9** | **3.52 s** |
| **`modernbert-embed-base`** *(SOTA)* | **768** | 149.0M | **0.1861** | **99.01%** | **5.87 ms** | 10.81 ms | **170.5** | **4.86 s** |

### 6.3. Complete Empirical HNSW Parameter Sweep Grid

#### Model A: `intfloat/e5-small-v2` (384-dim, Champion Desktop Model)
| $M$ | $ef_{\text{construct}}$ | $ef_{\text{search}}$ | Recall@10 (%) | Global nDCG@10 | Latency P50 (ms) | Latency P95 (ms) | QPS | Index Build Time (s) |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 16 | 64 | 16 | 100.0% | 0.1539 | 5.23 ms | 8.67 ms | 191.4 | 3.58 s |
| 16 | 64 | 32 | 100.0% | 0.1539 | 4.58 ms | 8.11 ms | 218.2 | — |
| **16** | **128** | **64** | **100.0%** | **0.1539** | **5.65 ms** | **10.44 ms** | **176.9** | **3.52 s** |
| 16 | 128 | 128 | 100.0% | 0.1539 | 5.39 ms | 8.62 ms | 185.5 | — |
| 32 | 128 | 64 | 100.0% | 0.1539 | 6.07 ms | 10.57 ms | 164.7 | 3.74 s |
| 32 | 128 | 128 | 100.0% | 0.1539 | 5.36 ms | 9.90 ms | 186.6 | — |
| 32 | 256 | 256 | 100.0% | 0.1539 | 5.36 ms | 10.61 ms | 186.7 | 3.81 s |
| 64 | 256 | 128 | 100.0% | 0.1539 | 5.10 ms | 9.98 ms | 196.0 | 3.63 s |
| 64 | 256 | 256 | 100.0% | 0.1539 | 5.16 ms | 9.34 ms | 193.6 | — |

#### Model B: `nomic-ai/modernbert-embed-base` (768-dim, High-Capacity SOTA Model)
| $M$ | $ef_{\text{construct}}$ | $ef_{\text{search}}$ | Recall@10 (%) | Global nDCG@10 | Latency P50 (ms) | Latency P95 (ms) | QPS | Index Build Time (s) |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 16 | 64 | 16 | 85.59% | 0.1732 | 4.57 ms | 9.11 ms | 218.7 | 4.66 s |
| 16 | 64 | 32 | 93.24% | 0.1803 | 4.87 ms | 9.59 ms | 205.4 | 4.76 s |
| **16** | **128** | **64** | **99.01%** | **0.1861** | **5.87 ms** | **10.81 ms** | **170.5** | **4.86 s** |
| 16 | 128 | 128 | 99.61% | 0.1861 | 7.05 ms | 11.14 ms | 141.9 | 4.85 s |
| 32 | 128 | 64 | 99.24% | 0.1861 | 6.27 ms | 9.65 ms | 159.4 | 4.81 s |
| 32 | 128 | 128 | 99.77% | 0.1861 | 6.20 ms | 9.52 ms | 161.3 | 4.87 s |
| 32 | 256 | 256 | 100.0% | 0.1860 | 6.60 ms | 9.82 ms | 151.4 | 5.12 s |
| 64 | 256 | 128 | 99.98% | 0.1860 | 6.38 ms | 8.96 ms | 156.8 | 5.07 s |
| 64 | 256 | 256 | 99.98% | 0.1860 | 6.26 ms | 9.61 ms | 159.8 | 4.93 s |

#### Model C: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, Baseline Control Model)
| $M$ | $ef_{\text{construct}}$ | $ef_{\text{search}}$ | Recall@10 (%) | Global nDCG@10 | Latency P50 (ms) | Latency P95 (ms) | QPS | Index Build Time (s) |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 16 | 64 | 16 | 100.0% | 0.1255 | 4.54 ms | 6.91 ms | 220.1 | 2.35 s |
| 16 | 64 | 32 | 100.0% | 0.1255 | 3.95 ms | 7.02 ms | 253.0 | 2.35 s |
| **16** | **128** | **64** | **100.0%** | **0.1255** | **4.17 ms** | **7.18 ms** | **240.0** | **2.45 s** |
| 16 | 128 | 128 | 100.0% | 0.1255 | 4.00 ms | 6.96 ms | 249.9 | 2.50 s |
| 32 | 128 | 64 | 100.0% | 0.1255 | 4.92 ms | 7.78 ms | 203.4 | 2.41 s |
| 32 | 128 | 128 | 100.0% | 0.1255 | 4.98 ms | 8.16 ms | 200.9 | 2.40 s |
| 32 | 256 | 256 | 100.0% | 0.1255 | 5.04 ms | 8.74 ms | 198.4 | 2.60 s |
| 64 | 256 | 128 | 100.0% | 0.1255 | 5.06 ms | 7.74 ms | 197.7 | 2.52 s |
| 64 | 256 | 256 | 100.0% | 0.1255 | 4.79 ms | 7.25 ms | 209.0 | 2.57 s |

### 6.4. Core Theoretical & Engineering Insights for Thesis Defense

1. **Invariance of Semantic Quality under Cross-Paper Distractors:**
   When searching across all 4,108 chunks without paper filtering, the models exhibit the exact same accuracy ordering as observed in isolated per-document retrieval:
   $$\text{ModernBERT (0.1861)} > \text{E5-Small-v2 (0.1539)} > \text{MiniLM (0.1255)}$$
   ModernBERT's 768-dimensional representation provides superior cross-document discriminative power (+48.3% over MiniLM), successfully filtering out irrelevant passages across unrelated academic topics.

2. **The Dimensionality Effect on HNSW Graph Traversal:**
   The empirical data provides a textbook demonstration of the relationship between vector dimension and greedy graph navigation:
   * **In 384 dimensions (`e5-small-v2`, `MiniLM`):** Graph connectivity is dense enough that even at minimal search beam width ($ef_{\text{search}}=16$), HNSW achieves **100.0% exact match retention**.
   * **In 768 dimensions (`ModernBERT`):** The curse of dimensionality increases distance concentration, requiring wider search candidate pools: Recall@10 scales from $85.59\%$ ($ef=16$) to $93.24\%$ ($ef=32$), reaching **$99.01\%$ at $ef=64$** and **$100.0\%$ at $ef=256$**.
   * **Defense Takeaway:** Higher dimensional models require setting $ef_{\text{search}} \ge 64$ during query routing to avoid graph truncation.

3. **Zero Downstream Quality Degradation ($\Delta \text{nDCG@10} = 0.0000$):**
   Comparing exact brute-force BLAS against optimal HNSW configurations shows identical end-task ranking ($0.1539$ for E5, $0.1861$ for ModernBERT), proving that approximate nearest-neighbor indexing introduces zero loss into the downstream LLM generation stage.

4. **Unified Operational Standard:**
   Deploying **$M=16, ef_{\text{construct}}=128, ef_{\text{search}}=64$** serves as the universal sweet spot: it delivers $\ge 99.0\%$ candidate recall across all model architectures, maintains sub-6 ms latency (>170 QPS), and indexes 4,000+ chunks in $< 5\text{ seconds}$ without excessive graph edge memory overhead.

---

## 7. Architectural Recommendations for System Deployment

Based on empirical evidence across QASPER (207 papers), SciFact (5,183 abstracts), and HNSW graph scaling (4,108 multi-paper chunks):

### Recommendation A: Production Default Model $\longrightarrow$ `intfloat/e5-small-v2`
* **Why:** At 33.4M parameters, `e5-small-v2` offers the single best engineering compromise for a desktop scientific document manager. Its 30 ms query latency feels instantaneous in the interactive `<AiChatPanel>`, its 799 MB RAM profile leaves ample headroom for Ollama (`llama3.2:3b`), and its **0.5522 nDCG@10** provides a statistically significant +0.0497 gain over the baseline.
* **Production Prefix Integrity:** Must enforce `"query: "` on search questions and `"passage: "` on document chunks, as implemented in `backend/apps/documents/services/rag_service.py`.
* **Vector Index Standard:** Pair with Qdrant HNSW configuration $M=16, ef_{\text{construct}}=128, ef_{\text{search}}=64$ (100.0% recall, 5.65 ms P50 latency, 176.9 QPS).

### Recommendation B: High-Accuracy Tier Model $\longrightarrow$ `nomic-ai/modernbert-embed-base`
* **Why:** If the user has a modern CPU or optional GPU acceleration, ModernBERT provides a substantial **+0.0846 nDCG@10** jump (0.5872) and near-perfect candidate recall (96.4% Recall@20). Its native 8,192 token context window enables long section encoding without chunk boundary fragmentation.
* **Vector Index Standard:** Requires $ef_{\text{search}} \ge 64$ to guarantee $\ge 99.0\%$ candidate retention in its 768-dimensional space.

### Recommendation C: Dual-Mode Search Architecture (Exact BLAS vs. HNSW)
In scientific document management, users alternate between two fundamentally different retrieval workflows. Our empirical findings dictate a **Dual-Mode Search Engine**:

```
                              [User Information Request]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     [Single-Paper Reader Mode]                     [Global Multi-Paper Library Mode]
      • Target: Active PDF in Viewer                 • Target: Entire User Collection
      • Scale: N < 100 chunks                        • Scale: N > 4,000 chunks
      • Engine: Exact BLAS Dot Product               • Engine: Qdrant HNSW Graph Index
      • Implementation: NumPy BLAS in-memory         • Configuration: M=16, ef_search=64
      • Latency: < 0.2 ms                            • Latency: 4.17 - 5.87 ms (P50)
      • Recall Loss: 0.00% (Exact Ceiling)           • Recall Loss: < 0.99% (99.01% - 100%)
```

1. **Single-Document Reader Mode (`DocumentRAG` in-memory):**
   * When chatting with a single active document in `<AiChatPanel>`, chunk count is small ($N \le 100$).
   * Brute-force cosine dot product (`query_emb @ doc_embs.T`) runs in $<0.2$ ms on CPU.
   * **Rule:** Do not construct an HNSW graph for individual documents. Exact in-memory BLAS eliminates graph build overhead (saving ~3.5s per paper) while delivering a mathematically perfect 100% recall.
2. **Global Multi-Paper Library Mode (`RagService` via Qdrant):**
   * When querying across all documents in a collection or research library ($N > 4,000$ chunks), linear scanning incurs unacceptable memory movement.
   * Route queries to **Qdrant HNSW** with pinned production parameters:
     - `m = 16` (Low edge connectivity, minimal RAM overhead)
     - `ef_construct = 128` (High-quality graph construction in $<5$ seconds)
     - `hnsw_ef = 64` (Sub-6 ms P50 latency, $>170$ QPS, $\ge 99.01\%$ candidate retention)

### Recommendation D: Permanent Deprecation of 300M+ Dense Models on Desktop CPU
* **Why:** Models $>300\text{M}$ parameters (`mxbai-embed-large-v1` at 335M, `arctic-embed-m-v2.0` at 305M) failed completely on desktop CPU: throughput plunged to $0.6$ chunks/sec, query latency ballooned to $275$ ms, and accuracy was no better than the 22M baseline. They should be strictly excluded from desktop deployment.

---

## 8. Artifact & Code Traceability

| Artifact Description | File Path |
| :--- | :--- |
| **HNSW Multi-Model Benchmark CSV** | [`eval/phases/phase_4_indexing/artifacts/hnsw_benchmark_results.csv`](file:///c:/DACNTT/eval/phases/phase_4_indexing/artifacts/hnsw_benchmark_results.csv) |
| **Raw Benchmark Metrics JSON (Phase 3)** | [`eval/results/thesis_embedding_benchmark.json`](file:///c:/DACNTT/eval/results/thesis_embedding_benchmark.json) |
| **Pareto Frontier Plot (Accuracy vs Latency)** | [`eval/results/figures/pareto_ndcg10_vs_latency.png`](file:///c:/DACNTT/eval/results/figures/pareto_ndcg10_vs_latency.png) |
| **Pareto Frontier Plot (Accuracy vs Throughput)** | [`eval/results/figures/pareto_ndcg10_vs_throughput.png`](file:///c:/DACNTT/eval/results/figures/pareto_ndcg10_vs_throughput.png) |
| **HNSW Standalone Colab Suite (Phase 4)** | [`hnsw_index_eval.ipynb`](file:///c:/DACNTT/hnsw_index_eval.ipynb) |
| **HNSW Export Utility Script** | [`backend/scripts/export_embeddings_for_hnsw.py`](file:///c:/DACNTT/backend/scripts/export_embeddings_for_hnsw.py) |
| **Exported Artifacts (`e5-small-v2`)** | [`eval/phases/phase_4_indexing/artifacts/colab_exports/intfloat__e5-small-v2/`](file:///c:/DACNTT/eval/phases/phase_4_indexing/artifacts/colab_exports/intfloat__e5-small-v2/) |
| **Exported Artifacts (`modernbert-embed-base`)** | [`eval/phases/phase_4_indexing/artifacts/colab_exports/nomic-ai__modernbert-embed-base/`](file:///c:/DACNTT/eval/phases/phase_4_indexing/artifacts/colab_exports/nomic-ai__modernbert-embed-base/) |
| **Exported Artifacts (`all-MiniLM-L6-v2`)** | [`eval/phases/phase_4_indexing/artifacts/colab_exports/sentence-transformers__all-MiniLM-L6-v2/`](file:///c:/DACNTT/eval/phases/phase_4_indexing/artifacts/colab_exports/sentence-transformers__all-MiniLM-L6-v2/) |
| **Benchmark Runner Script** | [`backend/scripts/run_thesis_embedding_benchmark.py`](file:///c:/DACNTT/backend/scripts/run_thesis_embedding_benchmark.py) |
| **Pareto Plot Generator** | [`backend/scripts/plot_pareto_frontier.py`](file:///c:/DACNTT/backend/scripts/plot_pareto_frontier.py) |
| **Shared Canonical Evaluation Utils** | [`backend/scripts/eval_common.py`](file:///c:/DACNTT/backend/scripts/eval_common.py) |
| **SciFact Cross-Domain Benchmark Script** | [`eval/phases/phase_3_embedding/scripts/evaluate_scifact_cross_dataset.py`](file:///c:/DACNTT/eval/phases/phase_3_embedding/scripts/evaluate_scifact_cross_dataset.py) |

