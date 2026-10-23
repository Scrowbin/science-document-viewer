# Practical Dense Embedding Evaluation Plan

**Scope:** Direct Empirical Benchmarking of Open-Source Dense Encoders ($\le 335\text{M}$ Parameters) on the Academic Literature Corpus (`eval/prepared/`).  
**Environment:** AMD Ryzen 5 5600 6-Core CPU, 16 GB Desktop RAM, local single-node deployment alongside Ollama (`llama3.2:3b`).

---

## 1. Objectives & Scope
1. **Target Models:** Candidate pool strictly restricted to open-source (MIT / Apache-2.0) models $\le 335\text{M}$ parameters:
   - `sentence-transformers/all-MiniLM-L6-v2` (Baseline control, 22.7M)
   - `intfloat/e5-small-v2` (Champion, 33.4M)
   - `BAAI/bge-small-en-v1.5` (33.4M)
   - `Snowflake/snowflake-arctic-embed-s` (33.2M)
   - `nomic-ai/modernbert-embed-base` (149M)
2. **Evaluation Dataset:** Complete unified academic corpus (207 papers, 615 queries, 5,194 passage chunks) from QASPER.
3. **Primary Metric:** nDCG@10 (with nDCG@4, Recall@20, MRR@10).
4. **Statistical Testing:** Two-sided paper-cluster bootstrap resampling ($B=2,000$, `seed=42`) with 95% confidence intervals against baseline.
5. **Efficiency Profiling:** Single-query latency (P50/P95 in ms, $B=1$), indexing throughput (chunks/sec, $B=32$), and peak resident RAM on CPU.

---

## 2. Experimental Procedure
1. Extract and chunk full-text arXiv PDFs using sentence-aware boundary packing (`chunking_utils.py`).
2. Generate embeddings with task-prefix integrity (`query: ` and `passage: ` where required).
3. Compute exact cosine similarity between query vectors and document chunk candidate pools.
4. Evaluate ranking metrics against gold verbatim evidence annotations ($\tau^* = 0.55$).
5. Measure CPU latency and RAM footprint under fixed 4-thread allocation (`torch.set_num_threads(4)`).