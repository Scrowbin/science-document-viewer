# Phase 9: Small Language Model Generation Benchmark (RQ5)
**Definitive Operational Specification, Benchmark Governance, Metric Risk Protocols, and Approval-Gated Execution Blueprint**

*Document Status:* **Active Persistent Context & Experimental Specification (Stage A Complete)**
*Canonical Location:* [`eval/phases/phase_9_generation/README.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/README.md)
*Workspace Root:* `c:\DACNTT`
*Hardware Environment:* AMD Ryzen 5 5600 6-Core / 12-Thread Local CPU (Base 3.5 GHz, Boost 4.4 GHz), 16 GB DDR4 RAM, Windows 11 Host, Zero Discrete GPU (Zero-VRAM CPU Execution)
*Inference Engine:* Local Ollama REST Daemon (`http://localhost:11434/api/generate`)

---

## 1. Executive Objective & Research Question

The objective of RQ5 is to evaluate candidate open-source Small Language Models (SLMs) running locally under strict desktop CPU and memory constraints (16 GB RAM shared across the operating system, PostgreSQL, Django backend, Qdrant vector store, and PDF viewer) to identify a suitable generator for the scientific document manager assistant.

### 1.1. Formal Research Question
> **RQ5:** *Among the candidate small language models that can run under the project's hardware constraints (`qwen2.5:0.5b`, `llama3.2:1b`, `llama3.2:3b`), which provides the best balance of scientific answer quality, evidence faithfulness, inference latency, and memory consumption when used as the generator in the academic RAG system?*

### 1.2. Critical Scope Boundary: Controlled Generation vs. End-to-End RAG
To maintain scientific validity and avoid conflating pipeline failures, two distinct experiments are delineated:
1. **RQ5 (Controlled Generation Evaluation):** All candidate models receive **identical questions, identical prompt formatting, and identical verified evidence passages (gold context)**. This isolates generator reasoning, mathematical fidelity, and context adherence conditional on receiving relevant evidence.
2. **End-to-End RAG Evaluation (Final Combination / RQ6 / Chapter 6):** The frozen candidate generator receives context retrieved by the frozen multi-stage retrieval pipeline. This evaluates the cumulative effects of PDF extraction, hierarchical chunking, retrieval ranking errors, and distractor noise.
*Direct Rule:* Results from gold-evidence generation (RQ5) must never be conflated with or reported as end-to-end RAG accuracy.

---

## 2. Confirmed Candidate Models and Hardware Configuration

All candidate models were verified present and operational in the local Ollama instance on the host machine.

### 2.1. Candidate Model Specifications

| Model Identifier | Base Architecture | Parameter Count | Quantization | Context Window | Disk Footprint | Preliminary Measured Peak RAM | License |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`qwen2.5:0.5b`** | `qwen2` | 494.03M (~0.49B) | `Q4_K_M` | 32,768 tokens | 397 MB | ~620 MB *(preliminary estimate)* | Apache 2.0 |
| **`llama3.2:1b`** | `llama` | 1.23B (~1.2B) | `Q8_0` | 131,072 tokens | 1.3 GB | ~1,680 MB *(preliminary estimate)* | Llama 3.2 Community |
| **`llama3.2:3b`** | `llama` | 3.21B (~3.2B) | `Q4_K_M` | 131,072 tokens | 2.0 GB | ~2,540 MB *(preliminary estimate)* | Llama 3.2 Community |

*Status Note on RAM Values:* The preliminary RAM values above represent initial diagnostic observations of host memory allocation. They are **not yet validated as process-isolated model footprint benchmarks** (see Section 6 for the required memory measurement protocol).

### 2.2. Controlled Inference Controls
- **API Endpoint:** `POST http://localhost:11434/api/generate`.
- **Decoding Temperature:** `temperature = 0.0` (fully deterministic greedy decoding; eliminates sampling variance across comparative runs).
- **Generation Budget:** `num_predict = 256` tokens (sufficient for concise scientific answers; enforces strict upper-bound on generation latency).
- **Prompt Structure:** Identical production academic assistant template aligned with NFR-03 (`DU_AN_CNTT_TOAN_VAN.md` Table 4.2) and `RagService.query_document`:
  ```text
  You are a precise academic research assistant reading "{doc_title}".
  Use ONLY the provided context below to answer the user's question clearly and accurately.
  If the answer is not contained in the context, state clearly: 'The document does not contain sufficient relevant information to answer this question.'
  Do NOT extrapolate, speculate, or fabricate details beyond the provided context.

  Context:
  {context}

  Question: {question}

  Answer:
  ```
- **Pre-Inference Protocol Refinement Note:** The preliminary pilot instruction (*"If the answer is not contained in the context, synthesize the most relevant details available"*) was identified as methodologically contradictory before live inference. It actively commanded models to extrapolate, confounding faithfulness measurement. It was replaced with the explicit refusal directive matching production.
- **Evidence Sufficiency Boundary:** Atomic eligibility (Rule 3) guarantees that an annotator provided $\ge 1$ text evidence paragraph for their answer, but does not guarantee the paragraph contains exhaustive background context. The stricter prompt may prompt conservative models to refuse when evidence is partial; refusal behavior is tracked explicitly (`is_refusal`, `refusal_rate_pct`) and evaluated empirically.
- **Operational Metric Distinctions:**
  1. `Answer Token F1`: Lexical overlap with ground-truth reference answers (evaluates strictly to 0.0 on model refusals).
  2. `is_refusal` & `refusal_rate_pct`: Frequency of explicit NFR-03 refusal responses. Emitting a refusal is not inherently faithful; its validity is judged against whether the context actually lacked sufficient facts.
  3. `automated_containment_proxy`: Automated token overlap heuristic against prompt context (0.0% on refusal). This does **not** establish semantic faithfulness or entailment.
  4. `Human Claim-Level Audit`: 60-answer blinded qualitative review distinguishing `SUPPORTED`, `UNSUPPORTED` (unverifiable claims), `MISSING_INFO - PARTIAL` (incomplete answer), and `MISSING_INFO - UNJUSTIFIED_REFUSAL` (refusal despite sufficient evidence).
- **Observed Single-Query Generation Latency (Preliminary Estimates on 16 Diagnostic Questions):**
  - `qwen2.5:0.5b`: ~3.35s P50 (Throughput: ~46.5 tokens/sec).
  - `llama3.2:1b`: ~5.33s P50 (Throughput: ~17.3 tokens/sec).
  - `llama3.2:3b`: ~7.95s P50 (Throughput: ~10.5 tokens/sec).

---

## 3. Benchmark Dataset Options, Availability & Methodological Limitations

### 3.1. Option A: Curated Diagnostic Benchmark (`eval_benchmark_seed.json`)
- **Location:** [`backend/data/eval_benchmark_seed.json`](file:///c:/DACNTT/backend/data/eval_benchmark_seed.json) (13,299 bytes).
- **Composition:** 16 canonical questions across 4 seminal deep learning papers (exactly 4 questions per paper):
  1. *Attention Is All You Need* (arXiv:1706.03762): 4 questions.
  2. *Deep Residual Learning for Image Recognition* (arXiv:1512.03385): 4 questions.
  3. *LoRA: Low-Rank Adaptation of Large Language Models* (arXiv:2106.09685): 4 questions.
  4. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (arXiv:2005.11401): 4 questions.
- **Question Categorization:** Quantitative (4), Architecture (4), Methodology (4), Factoid (3), Comparative (1).
- **Evidence Verification:** Each question contains an expert expected answer and a verified verbatim text passage from the source paper (mean length: 145.8 characters).
- **Methodological Role & Severe Limitation:**
  - *Utility:* Ideal for technical smoke testing, prompt debugging, output parsing validation, and qualitative diagnostic error analysis.
  - *Limitation:* $N=16$ questions across only 4 paper clusters is **statistically insufficient** for confident generalizability or robust paper-cluster statistical inference. The 4 seminal papers are heavily represented in LLM pre-training corpora.
  - *Rule:* Results on this diagnostic set must be reported separately and **never pooled** with QASPER scores without an explicit protocol.

### 3.2. Option B: QASPER Development Split (`qasper-dev-v0.3.json`)
- **Location:** [`eval/data/qasper_official/qasper-dev-v0.3.json`](file:///c:/DACNTT/eval/data/qasper_official/qasper-dev-v0.3.json) (10.87 MB).
- **Verified Corpus Counts:**
  - Total papers: 281.
  - Papers with text-extractive evidence: 279.
  - Total queries: 1,005.
  - Answerable queries: 945.
  - Queries with valid text-extractive evidence ($R_q \neq \emptyset$): **927 queries**.
- **Role in RQ5:** Leading candidate for broad-scale comparative model evaluation. It provides broad coverage across 279 paper clusters without exhausting the final test split.
- **Audit Prerequisite:** Must verify whether any specific papers or queries in Dev directly influenced upstream component choices in ways that would confound generator evaluation.

### 3.3. Option C: QASPER Test Split (`qasper-test-v0.3.json`)
- **Location:** [`eval/data/qasper_official/qasper-test-v0.3.json`](file:///c:/DACNTT/eval/data/qasper_official/qasper-test-v0.3.json) (17.24 MB).
- **Verified Corpus Counts:** Total 416 papers, 1,451 queries (408 papers with text evidence, 1,310 queries).
- **Prior RQ4 Evaluation:** **408 papers / 1,310 queries** were evaluated in Phase 6.
- **Mandatory Integrity Warning (DEC-03 Audit):**
  - **QASPER Test is NOT an unexposed test set for the overall RAG pipeline.** It was evaluated during Stage 4 retrieval benchmarking (Dense, BM25, RRF, Convex).
  - Any subsequent end-to-end evaluation on QASPER Test must be explicitly reported as *post-retrieval-selection confirmatory testing*. It cannot be presented as independent blind generalization.

### 3.4. Option D: Unexposed QASPER Train Reservoir (Recommended Holdout)
- **Location:** [`eval/data/qasper_official/qasper-train-v0.3.json`](file:///c:/DACNTT/eval/data/qasper_official/qasper-train-v0.3.json) (30.49 MB).
- **Verified Unexposed Reservoir Counts:**
  - Official Train Total: 888 papers (2,593 queries).
  - Train papers used in RQ3: 111 papers.
  - **Experiment-Unexposed Train papers: 777 papers** (2,154 total queries).
  - Unexposed papers with $\ge 1$ text-evidenced question: **713 papers (1,729 text-evidenced eligible queries)**.
  - Papers with $\ge 2$ eligible questions: **487 papers**.
  - Papers with exactly 1 eligible question: **226 papers**.
- **Role in Final Evaluation:** Serves as the primary source for drawing a stratified confirmatory holdout ($N=100$ queries) with zero prior exposure in the project's development history.
- **Scientific Limitation:** Shares QASPER's domain distribution, LaTeX extraction format, and crowdworker collection methodology. It is an *experiment-unexposed paper-level holdout within the project*, not an external pristine distribution.

### 3.5. Other Evaluated / Proposed External Datasets
- **SciFact:** Scientific claim verification dataset (5,183 abstracts, 1,409 claims; SUPPORT / CONTRADICT / NOINFO). Useful as an out-of-domain sanity check for embedding zero-shot transfer, but task mismatch prevents using it for open-ended generative document QA.
- **FiQA / FinQA:** Financial domain question answering. Non-scientific domain; not an appropriate benchmark for academic literature QA.

---

## 4. Faithfulness Metric Risk & Proposed Claim-Level Human Rubric

### 4.1. Current Lexical Containment Proxy and Its Deficiencies
The evaluator implements:
```python
def compute_context_containment_proxy(prediction: str, context: str) -> float:
    # Percentage of non-stopword tokens (len > 2) in prediction that appear in context (0.0 on refusal)
```
- **Methodological Flaw:** This is strictly an **evidence-token containment proxy (lexical overlap)**, not a verified measure of semantic or factual faithfulness. Legacy aliases (`compute_faithfulness`, `faithfulness`, `faithfulness_mean`) have been permanently removed to eliminate any conflation with semantic truth.
- **Specific Risks of Conflating Containment with Faithfulness:**
  1. *Penalizes valid abstraction:* A model that accurately synthesizes an answer using synonyms or rephrased prose receives a low containment score.
  2. *Rewards deceptive hallucination:* A model that stitches together real keywords from the context into a scientifically false claim receives a deceptively high containment score.
- **Governance Directives:**
  - Historical containment scores (34.4%–36.5%) are preserved for traceability under the explicit label **Automated Context Containment Proxy** and **must never be labeled as semantic faithfulness**.
  - Any textual claim in drafts asserting *"faithfulness > 90%"* based on this metric is documented as a template defect and retracted.

### 4.2. Proposed Two-Tier Evaluation Architecture
To provide scientifically defensible generation metrics:
1. **Tier 1 (Automated Lexical Overlap):**
   - SQuAD/QASPER Token-Level Precision, Recall, and F1 (normalized text against expert ground truth).
   - Non-stopword evidence token containment (reported strictly as *Lexical Evidence Grounding Proxy*).
2. **Tier 2 (Human Claim-Level Verification on Stratified Sub-Sample):**
   - Evaluate a stratified sample of answers (e.g. across the 16 diagnostic questions or a representative sample of Dev questions).
   - Decompose each generated answer into atomic propositional claims.
   - Grade each claim under an explicit 4-category rubric:
     - **Supported [S]:** Claim is directly substantiated by the supplied evidence passage.
     - **Unsupported [U]:** Claim is not mentioned in or cannot be inferred from the supplied passage (extrinsic hallucination).
     - **Contradicted [C]:** Claim directly conflicts with facts stated in the supplied passage (intrinsic hallucination).
     - **Missing Critical Info [M]:** Answer omits essential caveats or conditions specified in the evidence.
   - Compute **Claim Faithfulness Ratio:** $\frac{N_{\text{Supported}}}{N_{\text{Total Claims}}}$.
   - Where feasible, conduct double-blind scoring on a subset to report inter-annotator agreement (Cohen's $\kappa$). If only one reviewer participates, report as single-reviewer expert audit without claiming inter-rater reliability.

---

## 5. Memory-Measurement Risk & System Profiling Protocol

### 5.1. The Ollama External Daemon Disconnect
- **Current Defect:** The evaluation script runs as a Python process that issues HTTP calls to `http://localhost:11434`. Calling `psutil.Process().memory_info().rss` inside the evaluation script measures **only the Python HTTP client** (~40–60 MB), completely missing the memory consumed by the Ollama server and the model runner (`ollama_llama_server.exe`).
- **Required Protocol:**
  1. Locate the active Ollama runner process tree during model execution using `psutil`:
     - Scan system processes for `ollama` or child worker processes (`ollama_llama_server.exe`).
  2. Measure three distinct memory states for each candidate model:
     - **Baseline OS Memory (Idle):** RAM utilized prior to loading the model.
     - **Model Load Memory (Cold Load):** Peak RAM after model weights are loaded into host memory during the warm-up call.
     - **Active Generation Peak Memory:** Maximum resident memory observed across the entire Ollama process tree during active token generation under maximum context window.
  3. If process-isolated tracking proves technically unreliable under Windows process permission boundaries, report system-level committed memory delta or mark memory as *exploratory / observational*, citing model weight file size as the verified lower bound.

---

## 6. Open Methodological Issue: RQ4 Retriever Selection Inconsistency

A critical contradiction between the RQ4 empirical Test table and the RAG pipeline design must remain recorded as an **open methodological issue**:

### 6.1. The Empirical Discrepancy
In [`eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md), the frozen QASPER Test results across 408 papers / 1,310 queries are:

| Retrieval Strategy | nDCG@10 (Primary) | $\Delta$ vs. Dense | 95% Bootstrap CI | Adjusted $p$-value (Holm) | Outcome |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dense Only (`e5-small-v2`)** | **0.5655** | Baseline (0.0) | — | — | Baseline |
| **BM25 Only (WordPiece)** | **0.5065** | -0.0589 | [-0.0788, -0.0390] | $p_{\text{adj}} = 0.0030^*$ | Significant degradation |
| **Hybrid RRF ($k=60$)** | **0.5662** | +0.0008 | [-0.0110, +0.0130] | $p_{\text{adj}} = 0.8696$ | **Not statistically significant** |
| **Hybrid Convex ($\alpha=0.7$)** | **0.5806** | **+0.0152** | **[+0.0045, +0.0262]** | **$p_{\text{adj}} = 0.0140^*$** | **Statistically significant improvement** |

### 6.2. The Contradiction & Audit Reconciliation (Stage C2.1 Resolution)
- **Production Implementation:** Verified in code that production retrieval in `DocumentRAG.query` and `RagService.search_hybrid_rrf` exclusively executes **Hybrid RRF ($k=60$)**. Convex combination is not implemented in production.
- **Root Cause of Empirical Discrepancy:**
  - In `evaluate_full_qasper_rq4_hybrid.py`, BM25 IDFs were calculated globally over the **entire split-wide background of 14,035 chunks**, enabling smooth min-max score normalization ($S_{\text{norm}} = \frac{S - S_{\min}}{S_{\max} - S_{\min}}$).
  - In production (`DocumentRAG`), the application operates locally over a **single document (~35–60 chunks)**. Over a single document, technical keywords repeat across sections, compressing IDFs. Furthermore, when no chunk matches, min-max normalization collapses to zero.
- **Mathematical Decoupling of Recall@20:** In the RQ4 Test hierarchical benchmark, Recall@20 was **0.6413 for RRF** and **0.6525 for Convex** over unique parent sections under a 1,600-token budget. The previously reported `Recall@20 = 0.9558` came from earlier flat chunking on 160 papers (`expanded_160_hybrid_rrf_benchmark.json`).
- **Resolution Decision:** RRF ($k=60$) is retained as the provisional production engine because its rank-based reciprocal formula ($\frac{1}{k + r_i}$) is mathematically invariant to score magnitude, local IDF compression, or zero-division scaling hazards. Convex fusion is documented as an offline benchmark finding under global IDF.

---

## 7. Statistical Design Requirements for Confirmatory Comparison

When comparing candidate models on paired question sets:
1. **Paired Structure:** Models must answer the exact same questions under identical prompts and evidence contexts.
2. **Cluster Resampling:** Must resample at the paper cluster level ($B=2,000$ bootstrap replicates, `seed=42`) to account for query correlation within the same paper.
3. **Multiple Testing Correction:** Control Family-Wise Error Rate (FWER) across pairwise model comparisons (`3b vs 0.5b`, `3b vs 1b`, `1b vs 0.5b`) using Holm-Bonferroni correction at $\alpha = 0.05$.
4. **Complete Reporting:** Report mean differences ($\Delta$), 95% bootstrap confidence intervals, and exact $p$-values.
5. **Practical vs. Statistical Significance:** A statistically significant difference in token F1 of $+0.01$ may be practically negligible if it requires a $2.5\times$ increase in latency and $4\times$ increase in RAM. The selection rule must explicitly weigh the quality-latency-memory Pareto trade-off.

---

## 8. Runtime Estimation & Mandatory Smoke Test Gate

### 8.1. Preliminary Runtime Estimates
Based on single-query latencies observed on the AMD Ryzen 5 5600 CPU (~17s per query across all 3 models combined):
- **Diagnostic Set (16 questions):** $16 \times 17\text{s} \approx 272\text{s} \approx 4.5\text{ minutes}$.
- **Representative Dev Sample (50 questions):** $50 \times 17\text{s} \approx 850\text{s} \approx 14.2\text{ minutes}$.
- **Full QASPER Dev Evidenced Set (927 questions):** $927 \times 17\text{s} \approx 15,759\text{s} \approx 4.4\text{ hours}$.
- **Full QASPER Test Evaluated Set (1,310 questions):** $1,310 \times 17\text{s} \approx 22,270\text{s} \approx 6.2\text{ hours}$.

*Caveat:* These estimates exclude model switching, Ollama cold-start overhead, garbage collection, and potential thermal throttling during sustained multi-hour CPU workloads.

### 8.2. Mandatory Smoke Test Pre-Requisite
Before launching any evaluation exceeding 16 questions, a **2-question smoke test across all 3 models** must be executed to verify:
1. Clean model loading and switching in Ollama without socket hangup.
2. Output JSON serialization schema adherence.
3. Accurate timing and process memory capture.
4. Deterministic output reproducibility (`temperature=0.0`).
5. Error handling and checkpoint resumability.

---

## 9. 6-Stage Approval-Gated Workflow

All future sessions working on RQ5 must strictly adhere to this phased progression. No stage may be started without explicit user confirmation of the preceding stage.

```text
[Stage A: Context & Provenance]  <-- CURRENT STATE (COMPLETE)
  - Codify candidate models, hardware boundaries, and metric definitions.
  - Document methodological risks: lexical faithfulness proxy, Ollama daemon memory,
    QASPER Test leakage, and RQ4 RRF vs Convex inconsistency.
  - Produce this Phase 9 master specification.
          │
          ▼ [Approval Gate 1]
[Stage B: Dataset Overlap Audit & RQ4 Reconciliation]
  - Audit paper/query overlap across RQ1-RQ4 vs RQ5.
  - Formalize dataset split policy (diagnostic 16-seed vs QASPER Dev sample vs full Dev).
  - Reconcile and resolve the RQ4 retriever selection inconsistency.
          │
          ▼ [Approval Gate 2]
[Stage C: Metric and Measurement Design]
  - Formalize claim-level human faithfulness rubric and sampling protocol.
  - Establish process-level Ollama memory measurement harness.
  - Pre-specify primary decision metric, comparison family, and model selection rule.
          │
          ▼ [Approval Gate 3]
[Stage D: Technical Smoke Test]
  - Execute 2-question representative pilot across all 3 models.
  - Verify error handling, timing accuracy, memory logging, and JSON persistence.
  - Compute empirical throughput to establish validated runtime estimate.
          │
          ▼ [Approval Gate 4]
[Stage E: Full RQ5 Evaluation & Analysis]
  - Execute benchmark on approved dataset under frozen controls.
  - Serialize raw JSON records and Markdown report.
  - Execute paired cluster bootstrap analysis and qualitative error taxonomy.
          │
          ▼ [Approval Gate 5]
[Stage F: Final End-to-End Evaluation & Thesis Integration]
  - Integrate winning generator into frozen RAG pipeline.
  - Conduct final combination evaluation on designated evaluation data.
  - Synchronize Chapter 5 and Chapter 6 of the graduation thesis.
```

---

## 10. RQ5 Document Hierarchy and Authoritative Sources

To ensure coherent navigation and prevent conflicting interpretations, documentation for RQ5 is structured hierarchically with distinct authoritative roles:

| Document Role | Authoritative File | Primary Scope & Contents |
| :--- | :--- | :--- |
| **Phase Entry Point & Overview** | [`eval/phases/phase_9_generation/README.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/README.md) *(This Document)* | High-level research question, hardware constraints, candidate models, document hierarchy, and artifact registry. |
| **Canonical Evaluation Protocol** | [`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md) | **Definitive Methodological Authority:** Pre-registered 250-paper sampling rules, NFR-03 prompt alignment, paper-clustered paired $t$-test & bootstrap specifications, claim-level label definitions, and worst-case failure precedence hierarchy. |
| **Reviewer Guide & Annotation Instrument** | [`HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md) | **Actionable Human Review Document:** Contains the 20 review question blocks, exact generation evidence context, 3 counterbalanced blinded answers (`Model_Alpha`, `Model_Beta`, `Model_Gamma`), structured annotation forms, and mandatory non-erasure directives. |
| **Protocol Audit Changelog** | [`PROTOCOL_AUDIT_CHANGELOG.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md) | **Chronological Provenance Record:** Complete audit log from Stage A through Stage C7, detailing pre-inference approvals, caveat codifications, benchmark execution, and verification of the human review package. |
| **Confirmatory Benchmark Report (500Q)** | [`RQ5_LLM_GENERATION_REPORT_500Q.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT_500Q.md) | Comprehensive quantitative report for the 1,500 inference runs across 250 papers, containing survival-function $p$-values, Holm-adjusted significance, clustered bootstrap CIs, and efficiency profiling. |

### Critical Methodological Distinctions:
1. **Automated Lexical Containment Proxy vs. Semantic Faithfulness:**
   - The automated metric `automated_containment_proxy` is a lexical token-containment heuristic against the prompt context (evaluating strictly to 0.0% on refusal).
   - It does **not** establish semantic entailment, factual truth, or logical consistency. It serves solely as an automated lexical check.
2. **Scope of the Blinded Human Faithfulness Review:**
   - The qualitative human audit evaluates 60 model answers across 20 deterministically sampled questions (Option A stride-25).
   - It is designed as a **single-reviewer descriptive diagnostic audit**.
   - It does **not** establish inter-rater reliability (no Cohen's $\kappa$) or generalizable ground-truth factuality beyond the audited sample.

---

## 11. Complete Artifact and Script Registry

### 11.1. Core Benchmark Scripts (`eval/phases/phase_9_generation/scripts/`)
| Script Path | Role & Functionality |
| :--- | :--- |
| [`evaluate_rq5_llm_generation.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py) | Full confirmatory benchmark runner: queries Ollama REST API, executes greedy decoding, logs memory, parses outputs, computes Token F1 and containment, executes paper-clustered paired $t$-tests with survival-function $p$-values, and computes 2,000-replicate bootstrap CIs. |
| [`generate_sample_manifest_250.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/generate_sample_manifest_250.py) | Generates the frozen 250-paper / 500-question manifest from eligible unexposed Train papers under `seed=42`, with pre-registered standby reserve queue. |
| [`generate_human_review_package.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/generate_human_review_package.py) | Extracts the Option A stride-25 review sample (20 questions $\times$ 3 models = 60 answers), applies Latin-square counterbalanced blinding with `seed=42`, and generates the reviewer guide, CSV/JSONL templates, restricted mapping, and integrity manifest. |
| [`validate_human_review_package.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/validate_human_review_package.py) | Comprehensive 13-point automated validator verifying checksums, question parity, checkpoint matching, counterbalancing distribution, blank templates, and zero model leaks. |

### 11.2. Frozen Benchmark Artifacts (`eval/phases/phase_9_generation/artifacts/`)
| Artifact Path | Format | Role & Contents |
| :--- | :---: | :--- |
| [`eval_sample_manifest_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json) | JSON | **Frozen 500-Question Manifest:** 250 primary papers ($m=2$), 50 standby reserve papers, verbatim text evidence, annotator answers. (SHA-256: `f411670c...`) |
| [`rq5_inference_checkpoint.jsonl`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_inference_checkpoint.jsonl) | JSONL | **Frozen Inference Checkpoint:** Exactly 1,500 raw inference records (500 questions $\times$ 3 models) with full outputs, timings, and token metrics. (SHA-256: `b53166ef...`) |
| [`rq5_llm_generation_benchmark_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json) | JSON | Complete serialized benchmark results: aggregate metrics, statistical tests, Wilcoxon sensitivities, and bootstrap intervals. |
| [`RQ5_LLM_GENERATION_REPORT_500Q.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT_500Q.md) | Markdown | Comprehensive markdown evaluation report with formatted tables and inferential conclusions. |

### 11.3. Blinded Human Review Package (`eval/phases/phase_9_generation/artifacts/human_faithfulness_review/`)
| Artifact Path | Format | Role & Contents |
| :--- | :---: | :--- |
| [`HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md) | Markdown | Reviewer-facing evaluation form: 20 question blocks, exact generation evidence context, blinded answers, rubric, and precedence rules. |
| [`faithfulness_annotation_template_60a.csv`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/faithfulness_annotation_template_60a.csv) | CSV | Spreadsheet annotation template with 60 records and empty annotation columns (`primary_label`, `secondary_label`, `supporting_evidence`, `reviewer_notes`). |
| [`faithfulness_annotation_template_60a.jsonl`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/faithfulness_annotation_template_60a.jsonl) | JSONL | Machine-readable annotation template with identical 60 records and blank annotation fields. |
| [`restricted_model_label_mapping.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/restricted_model_label_mapping.json) | JSON | **Restricted Audit Metadata:** True mapping connecting review item IDs and blind labels to candidate models. Kept separate from reviewer-facing files. |
| [`sampling_and_integrity_manifest.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/sampling_and_integrity_manifest.json) | JSON | Package provenance record: stride-25 rule, counterbalancing matrix, source hashes, generator/validator hashes, and validation status (`PASSED_ALL_13_CHECKS`). |
