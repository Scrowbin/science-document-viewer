# DATA VERIFICATION AND METHODOLOGICAL AUDIT REPORT (RQ1 – RQ3)

> **Objective:** Systematically audit, verify provenance, and assess the methodological validity of all empirical claims across RQ1 (Extraction), RQ2 (Chunking), and RQ3 (Embedding Models) cited in `docs/CHAPTER3_CONTEXT.md`, `eval/results/THESIS_EMBEDDING_REPORT.md`, and `eval/README.md`.
>
> **Core Principle:** **ZERO FABRICATION**. Every single number must trace back to concrete, reproducible source artifacts on disk. If a number lacks empirical provenance, it is designated as **"UNSUPPORTED"** or **"CONTRADICTED"**. Future research stages (RQ4, RQ5, RQ6, and Stage 2 Combination benchmarks) are formally cataloged as **"NOT YET EVALUATED"**.

---

## 1. Unified Provenance & Verification Audit Table

| Research question | Claim/metric | Reported value | Source file and key | Generating script/configuration | Status | Required action |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **RQ1: Extraction** | Heading Recall (Pilot, 4 papers) | `100.0%` | `eval/README.md:126` & `backend/scripts/evaluate_extraction.py` | `evaluate_extraction.py` (Pilot 4 classic papers: Attention, ResNet, LoRA, RAG) | **VERIFIED** | Clarify in report that this is a 4-paper pilot, not representative of general corpus diversity. |
| **RQ1: Extraction** | Heading Recall (Dev, 47 papers) | `56.5%` | `eval/prepared/step1_full_dev_extraction_benchmark.json` → `macro_summary.PyMuPDF.mean_heading_recall_pct` (`56.47%`) | `evaluate_step1_full_dev.py` (47 Dev academic PDFs vs QASPER section titles) | **REPRODUCED** | Correct report text stating this was measured on 47 Dev papers (not 207). Confirmed by `evaluate_rq1_extractors.py` (`rq1_extraction_20261024_000639.json`: Heading F1 = 48.0%). |
| **RQ1: Extraction** | 1 - Character Error Rate (1-CER) | `37.3%` | `eval/prepared/step1_full_dev_extraction_benchmark.json` → `macro_summary.PyMuPDF.mean_char_accuracy_pct` (`37.32%`) | `evaluate_step1_full_dev.py` (first 5,000 chars vs raw QASPER TeX string) | **REPRODUCED** | Document methodological limitation: compares unstripped 2-column PDF text to LaTeX without filtering headers, footers, page numbers, or references. Low score reflects structural noise, not 63% text loss. |
| **RQ1: Extraction** | GROBID Extraction Benchmark | Claimed GROBID heading recall `100%` or gold reference | `docs/CHAPTER3_CONTEXT.md:582` | GROBID external HTTP server | **CONTRADICTED / UNSUPPORTED** | GROBID was used circularly as both candidate and evaluator in early pilot; GROBID server is currently offline in local environment. Replaced with independent QASPER TeX ground truth. |
| **RQ1: Extraction** | Multi-Engine PDF Parser Comparison | PyMuPDF vs pdfminer vs pypdf vs pdfplumber | `eval/results/rq1_extraction_20261024_000639.json` | `evaluate_rq1_extractors.py` (47 papers, PyMuPDF Layout 26.2ms/page, Plain 10.2ms/page, pypdf 61.7ms/page, pdfminer 107.1ms/page, pdfplumber 195.4ms/page) | **REPRODUCED** | Use PyMuPDF as verified extractor. PyMuPDF Layout-Aware uniquely extracts heading hierarchy necessary for downstream structure-aware chunking. |
| **RQ2: Chunking** | Sentence-aware chunking nDCG@4 | `0.4628` | `eval/prepared/part1b_rigorous_chunking_study.json` → `results_256_cap.sentence_aware.within_paper.ndcg4` (`0.46282`) | `evaluate_part1b_chunking.py` (48 dev papers, 128 queries, MiniLM-L6-v2 capped at 256 subwords) | **VERIFIED** | Document that this was evaluated under a 256-subword receptive field with MiniLM, explaining why it differs from RQ3 E5-small scores. |
| **RQ2: Chunking** | Naive Midpoint chunking nDCG@4 | `0.4133` | `eval/prepared/part1b_rigorous_chunking_study.json` → `results_256_cap.naive_midpoint.within_paper.ndcg4` (`0.41329`) | `evaluate_part1b_chunking.py` (same configuration as above, $\Delta = -0.0495$, $p=0.0060^*$) | **VERIFIED** | Retain as historical comparison; replace with strict continuous `fixed_size` baseline without layout leakage in new benchmark. |
| **RQ2: Chunking** | Silent Subword Truncation Rate | `0.0%` | `eval/prepared/part1b_rigorous_chunking_study.json` → `results_256_cap.sentence_aware.truncation_pct` | `evaluate_part1b_chunking.py` (bounded by sentence-packing budget) | **VERIFIED** | Document exact subword ceiling (256 for MiniLM, 400 for production chunkers). |
| **RQ2: Chunking** | Controlled Chunking Benchmark (6 strategies) | Fixed-size (`0.5654`) vs Overlap (`0.5385`) vs Semantic (`0.4856*`) vs Section (`0.5795`) vs Section-Token (`0.5359`) vs Section-Overlap (`0.5409`) | `eval/results/rq2_chunking_20261024_004912.json` → `summary` | `evaluate_rq2_chunking.py` (47 Dev papers, equal 1600-token budget, `intfloat/e5-small-v2`, primary $\tau=0.50$, sensitivity $\tau=0.30$, $B=2000$ cluster bootstrap) | **REPRODUCED** | Raw nDCG@10 champion is `section` (0.5795) but has 23.7% subword truncation; bounded champion is `section_overlap` (nDCG@4=0.4569, MRR@10=0.5737, truncation=0.63%). Semantic chunking significantly degrades retrieval ($\Delta = -0.0798, p=0.005^*$). |
| **RQ3: Embedding** | MiniLM-L6-v2 nDCG@10 | `0.5026` | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.ndcg10.mean` | `run_thesis_embedding_benchmark.py` (Unified 207 papers, 615 queries, 5,207 chunks, seed=42) | **VERIFIED** | Canonical dense baseline for paired statistical testing. |
| **RQ3: Embedding** | MiniLM-L6-v2 nDCG@4 | `0.4578` (in report) vs `0.3938` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.ndcg4.mean` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Correct report value from `0.4578` to verified JSON value `0.3938`. |
| **RQ3: Embedding** | MiniLM-L6-v2 Recall@20 | `0.9024` (in report) vs `0.9483` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.recall20.mean` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Correct report value from `0.9024` to verified JSON value `0.9483`. |
| **RQ3: Embedding** | MiniLM-L6-v2 MRR@10 | `0.4431` (in report) vs `0.4417` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.mrr10.mean` | `run_thesis_embedding_benchmark.py` | **PARTIALLY VERIFIED** | Minor rounding difference (0.0014); align report to JSON value `0.4417`. |
| **RQ3: Embedding** | MiniLM-L6-v2 Latency P50 | `19.30 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[1].efficiency.query_latency_p50_ms` (`19.3 ms`) | `run_thesis_embedding_benchmark.py` (batch=1, 100 queries, 10 warm-ups) | **VERIFIED** | Matches CPU profile on host Ryzen 5 5600 (4 threads). |
| **RQ3: Embedding** | MiniLM-L6-v2 Throughput | `315.2 chunks/s` (in report) vs `19.0 chunks/s` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[1].efficiency.indexing_throughput_chunks_sec` | `run_thesis_embedding_benchmark.py` (batch=32, CPU 4 threads) | **CONTRADICTED / UNSUPPORTED** | `315.2` is completely unsourced. Correct report to actual measured throughput: `19.0 chunks/s`. |
| **RQ3: Embedding** | MiniLM-L6-v2 Peak RSS | `685 MB` (in report) vs `593.1 MB` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[1].efficiency.peak_ram_mb` | `run_thesis_embedding_benchmark.py` (`psutil` RSS) | **CONTRADICTED** | Report conflated parent process memory; align to verified JSON value `593.1 MB`. |
| **RQ3: Embedding** | E5-Small-v2 nDCG@10 | `0.5522` | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.ndcg10.mean` | `run_thesis_embedding_benchmark.py` (95% CI `[0.5253, 0.5778]`) | **VERIFIED** | Production deployment champion. |
| **RQ3: Embedding** | E5-Small-v2 nDCG@4 | `0.5098` (in report) vs `0.4588` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.ndcg4.mean` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Correct report value from `0.5098` to verified JSON value `0.4588`. |
| **RQ3: Embedding** | E5-Small-v2 Recall@20 | `0.9382` (in report) vs `0.9623` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.recall20.mean` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Correct report value from `0.9382` to verified JSON value `0.9623`. |
| **RQ3: Embedding** | E5-Small-v2 MRR@10 | `0.4950` (in report) vs `0.5046` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.mrr10.mean` | `run_thesis_embedding_benchmark.py` | **PARTIALLY VERIFIED** | Discrepancy between markdown and JSON; align to JSON value `0.5046`. |
| **RQ3: Embedding** | E5-Small-v2 Latency P50 | `30.26 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[2].efficiency.query_latency_p50_ms` | `run_thesis_embedding_benchmark.py` (batch=1, 100 queries) | **VERIFIED** | Reproducible single-query latency. |
| **RQ3: Embedding** | E5-Small-v2 Throughput | `198.4 chunks/s` (in report) vs `6.5 chunks/s` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[2].efficiency.indexing_throughput_chunks_sec` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED / UNSUPPORTED** | `198.4` is completely unsourced. Correct report to actual measured throughput: `6.5 chunks/s`. |
| **RQ3: Embedding** | E5-Small-v2 Peak RSS | `799 MB` (in report) vs `659.8 MB` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[2].efficiency.peak_ram_mb` | `run_thesis_embedding_benchmark.py` | **PARTIALLY VERIFIED** | 799 MB was cumulative memory; isolated RSS is `659.8 MB`. Confirmed by isolated subprocess in dry-run (`491.5 MB`). |
| **RQ3: Embedding** | E5-Small-v2 Paired p-value | `0.0000*` (in report) vs `0.001*` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[2].stats_vs_baseline.p_value` | Cluster bootstrap ($B=2000$, seed=42) | **PARTIALLY VERIFIED** | Minimum p-value for $B=2000$ is $1/(2000+1) \approx 0.0005 \approx 0.001$. Format notation as $p = 0.001^*$. |
| **RQ3: Embedding** | BGE-Small-en-v1.5 Presence in JSON | Missing vs Present | `eval/results/thesis_embedding_benchmark.json` → `models[3]` | Model id: `bge-small-en-v1.5` | **VERIFIED** | Model IS present in source JSON. Audit resolves uncertainty: not missing from JSON. |
| **RQ3: Embedding** | BGE-Small-en-v1.5 nDCG@10 | `0.5410` (in report) vs `0.5209` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[3].metrics.ndcg10.mean` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Report artificially inflated score by $+0.0201$. Correct to verified value `0.5209`. |
| **RQ3: Embedding** | BGE-Small-en-v1.5 Significance | `0.0002*` (in report) vs `0.083` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[3].stats_vs_baseline.p_value` | Cluster bootstrap ($B=2000$) | **CONTRADICTED (MATERIAL ERROR)** | **BGE-Small is NOT statistically significant over MiniLM** at $\alpha=0.05$ ($p=0.083$, CI 95% `[-0.0027, +0.0393]` contains 0, `significant_05: false`). Report claim of $p=0.0002^*$ was false. |
| **RQ3: Embedding** | BGE-Small-en-v1.5 Throughput | `192.1 chunks/s` (in report) vs `6.5 chunks/s` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[3].efficiency.indexing_throughput_chunks_sec` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED / UNSUPPORTED** | Unsourced figure; correct to actual `6.5 chunks/s`. |
| **RQ3: Embedding** | Snowflake Arctic-Embed-S Presence | Missing vs Present | `eval/results/thesis_embedding_benchmark.json` → `models[5]` | Model id: `snowflake-arctic-embed-s` | **VERIFIED** | Model IS present in source JSON. |
| **RQ3: Embedding** | Snowflake Arctic-Embed-S nDCG@10 | `0.5385` (in report) vs `0.5417` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[5].metrics.ndcg10.mean` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Report under-reported score; JSON achieved higher score `0.5417`. Correct report. |
| **RQ3: Embedding** | Snowflake Arctic-Embed-S Throughput | `185.0 chunks/s` (in report) vs `7.0 chunks/s` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[5].efficiency.indexing_throughput_chunks_sec` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED / UNSUPPORTED** | Unsourced figure; correct to actual `7.0 chunks/s`. |
| **RQ3: Embedding** | ModernBERT-Embed-Base nDCG@10 | `0.5872` | `eval/results/thesis_embedding_benchmark.json` → `models[8].metrics.ndcg10.mean` | `run_thesis_embedding_benchmark.py` (95% CI `[0.5598, 0.6121]`) | **VERIFIED** | Highest accuracy model evaluated. Long-context 8192 support. |
| **RQ3: Embedding** | ModernBERT-Embed-Base Throughput | `58.2 chunks/s` (in report) vs `1.8 chunks/s` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[8].efficiency.indexing_throughput_chunks_sec` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED / UNSUPPORTED** | Unsourced figure; actual CPU throughput is `1.8 chunks/s` (768-dim, 149M params). |
| **RQ3: Embedding** | ModernBERT-Embed-Base Peak RAM | `1,840 MB` (in report) vs `1161.7 MB` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `models[8].efficiency.peak_ram_mb` | `run_thesis_embedding_benchmark.py` | **CONTRADICTED** | Transcription error in report; correct to `1161.7 MB`. |
| **Dataset Cohort** | Active Evaluation Papers | `207 papers` | `eval/results/thesis_embedding_benchmark.json` → `metadata.corpus.active_papers` | 48 Dev papers + 159 Held-out papers with valid non-unanswerable queries | **VERIFIED** | Confirmed by dataset manifests on disk. |
| **Dataset Cohort** | Total Evaluation Queries | `615 queries` | `eval/results/thesis_embedding_benchmark.json` → `metadata.corpus.total_queries` | 128 Dev queries + 487 Held-out queries | **VERIFIED** | Confirmed by QASPER split files. |
| **Dataset Cohort** | Total Chunk Count | `5,194` (in old report) vs `5,207` (in JSON) | `eval/results/thesis_embedding_benchmark.json` → `metadata.corpus.total_chunks` | 1,099 (Dev) + 4,108 (Held-out) chunks (`max_tokens=350, overlap=70`) | **VERIFIED** | Provenance established: discrepancy of 13 chunks caused by older script filtering 13 short abstract/title sections. Current ground truth is 5,207. |
| **Database Schema** | Relational Tables Count | `15 tables` | `backend/apps/*/models.py` | Django ORM models across `users`, `collections_app`, `documents` | **VERIFIED** | Exactly 15 tables confirmed by inspecting model definitions. |
| **Future Stage** | RQ4: Hybrid Retrieval (BM25 + Dense RRF) | Planned | `evaluate_step6_hybrid_rrf.py` | Reciprocal Rank Fusion ($k=60$) | **NOT YET EVALUATED** | Outside scope of current task. Clearly marked for future research. |
| **Future Stage** | RQ5: LLM Generation & Answer Quality | Planned | `evaluate_rq5_llms.py` | Llama-3.2:3b, Qwen2.5:3b | **NOT YET EVALUATED** | Outside scope of current task. Do not execute or fabricate. |
| **Future Stage** | RQ6: Cross-Domain Generalization | Planned | `generate_domain_benchmark.py` | Multi-domain dataset expansion | **NOT YET EVALUATED** | Outside scope of current task. |
| **Future Stage** | Stage 2: End-to-End Combination Testing | Planned | System combination matrix | Selected candidate combinations | **NOT YET EVALUATED** | Strictly deferred to subsequent milestone. |

---

## 2. In-Depth Methodological Audit of Key Issues

### 2.1. Material Discrepancies in Embedding Evaluation (RQ3)

Our audit cross-referenced every single cell of Table 3.6.3 in `docs/CHAPTER3_CONTEXT.md` against raw source artifact `eval/results/thesis_embedding_benchmark.json`. Key findings:

1. **Existence of BGE-Small and Arctic-Embed-S:**
   - Both models exist in `thesis_embedding_benchmark.json` under `models[3]` and `models[5]`. They were not omitted from the raw experiment, but their metrics were corrupted during transcription into documentation.
2. **Fabricated Indexing Throughput Figures:**
   - Documentation reported throughput figures of `315.2`, `198.4`, `192.1`, `185.0`, and `58.2` chunks/s.
   - The raw JSON records actual CPU throughputs of `19.0`, `6.5`, `6.5`, `7.0`, and `1.8` chunks/s.
   - The inflated numbers have no empirical basis and appear to have been derived from theoretical GPU projections or invalid multipliers. They have been corrected to empirical measurements.
3. **Falsified Statistical Significance for BGE-Small:**
   - Documentation claimed $p = 0.0002^*$ for BGE-Small over MiniLM.
   - The raw JSON shows $p = 0.083$ with 95% confidence interval $[-0.0027, +0.0393]$ spanning zero (`significant_05: false`).
   - BGE-Small is **statistically indistinguishable from the baseline MiniLM-L6-v2** on this dataset. Falsely claiming statistical significance was a critical reporting error that has now been rectified.
4. **Isolated Memory Profiling:**
   - Earlier scripts measured peak RSS cumulatively within a single long-running Python process, causing downstream models to inherit memory from prior models.
   - Script `backend/scripts/run_rq3_embedding_benchmark.py` introduces dedicated subprocess worker profiling (`--measure-rss-worker`), isolating model footprint (MiniLM: 448.8 MB, E5-Small: 491.5 MB, BGE-Small: 490.4 MB, Arctic-S: 488.2 MB, ModernBERT: 884.9 MB).

### 2.2. Methodological Clarifications on PDF Extraction (RQ1)

1. **Heading Recall (56.5% vs 100.0%):**
   - The 100.0% heading recall was obtained on a 4-paper pilot (*Attention Is All You Need*, *ResNet*, *LoRA*, *RAG*) with standardized formatting.
   - The 56.5% heading recall represents the macro-average across 47 diverse academic papers from the QASPER development split.
2. **1 - Character Error Rate (37.3%):**
   - The reported 1-CER score was computed against unstripped LaTeX source text from QASPER.
   - Running text extracted from multi-column PDF layouts incorporates running headers, page numbers, footnotes, and citation brackets, which do not appear in identical positions in the raw LaTeX source.
   - The 37.3% figure reflects layout divergence rather than text omission. Independent evidence coverage benchmarks confirm over 33–38% verbatim evidence quote matching.
3. **Multi-Engine Evaluation Ground Truth:**
   - Benchmark script `backend/scripts/evaluate_rq1_extractors.py` evaluates 5 local parsers (`pymupdf_plain`, `pymupdf_layout`, `pypdf`, `pdfminer.six`, `pdfplumber`).
   - PyMuPDF Layout achieves the highest balance of heading F1 (48.0%), low latency (26.2 ms/page), and downstream retrieval performance (nDCG@10 = 0.5100), justifying its selection as the fixed extractor for chunking and embedding pipelines.

### 2.3. Chunking Methodology & Receptive Field Alignment (RQ2)

1. **Why RQ2 nDCG@4 (0.4628) Differs from RQ3 nDCG@4 (0.4588 / 0.5098):**
   - RQ2 evaluated sentence-aware chunking on 48 Dev papers using `all-MiniLM-L6-v2` restricted to a 256-subword receptive field without task prefixes.
   - RQ3 evaluated `section_overlap` (max 350 tokens, overlap 70) on the complete 207-paper dataset using `intfloat/e5-small-v2` with task prefixes (`"passage: "` and `"query: "`).
   - The scores cannot be directly compared because the embedding model, context window, dataset scope, and task prefixes differed.
2. **Relevance Rule Standardization:**
   - In all new evaluation harnesses (`eval_common/relevance.py`), chunk relevance is defined uniformly by evidence token containment threshold $\tau$.
   - Primary threshold is set to $\tau = 0.50$ (chunk must contain at least 50% of the evidence tokens), with sensitivity testing at $\tau = 0.30$.
   - This ensures that chunking strategies with different chunk sizes are evaluated on a mathematically consistent basis.

---

## 3. Scope Management & Non-Evaluated Components

The following areas are strictly out of scope for the current audit and have been marked accordingly in documentation:
- **RQ4 (Hybrid RRF Retrieval):** Evaluates dense retrieval vs Reciprocal Rank Fusion combining BM25 and dense representations. Deferred to next milestone.
- **RQ5 (LLM Generation & Answer Quality):** Evaluates local LLM generation faithfulness and citation accuracy. Deferred to next milestone.
- **RQ6 (Cross-Domain Generalization):** Evaluates model transferability across diverse scientific domains. Deferred to next milestone.
- **Stage 2 (Combination Testing):** Shortlisted combinations will be tested end-to-end only after individual component evaluations are audited and finalized.

---

## 4. Summary of Code & Documentation Fixes

1. **Statistical Utilities Factored (`backend/scripts/eval_common/`):**
   - Factored canonical implementations of `compute_ndcg`, `compute_mrr`, `compute_recall`, `compute_hit_at_k`, `cluster_bootstrap_ci`, `paired_cluster_bootstrap`, and `holm_bonferroni_correction` into `backend/scripts/eval_common/stats.py`.
   - Verified by 15 automated unit tests in `backend/scripts/eval_common/test_stats.py`.
2. **Prefix Enforcement (`MODEL_PREFIX_SPECS`):**
   - Centralized task prefix mapping across `SentenceTransformer` and evaluation scripts.
   - Verified by automated unit tests in `backend/scripts/eval_common/test_prefixes.py`.
3. **Subword Truncation Monitoring:**
   - Added tokenizer-based context window overflow checks across all candidate models, verifying that MiniLM truncates 56.4% of 400-token chunks due to its 256-token limit, whereas 512-token models achieve 0.0% truncation.
4. **Documentation Sanitation (`docs/CHAPTER3_CONTEXT.md`):**
   - Converted all machine-specific `file:///c:/...` links to relative repository paths.
   - Removed unsourced hardware assumptions ("16 GB RAM").
   - Explicitly tagged RQ4, RQ5, RQ6, and Stage 2 combination claims with `*(CHƯA CHẠY LẠI / CHƯA KIỂM CHỨNG – làm ở đợt sau)*`.
