# DEC-03: Dataset and Experiment Exposure Audit (Corrected)
**Traceable Exposure Matrix, Overlap Verification, and Claim Boundary Analysis across RQ1–RQ5**

*Document Status:* **Corrected Exposure Audit Report (Deliverable 1 for Stage C2.1 / DEC-03)**
*Canonical Location:* [`eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md)
*Machine-Readable Artifact:* [`eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json)
*Workspace Root:* `c:\DACNTT`
*Audit Scope:* Official QASPER v0.3 release (`train`, `dev`, `test`), RQ1, RQ2, RQ3, RQ4 (Dev & Test), RQ5 (Diagnostic), and SciFact.

---

## 1. Traceable Exposure Matrix

The table below documents every dataset, paper cohort, and query partition evaluated in the repository, citing exact disk artifacts, field names, pipeline selection actions, and justified scientific boundaries:

| Research Question & Experiment | Dataset & Source Split | Papers & Queries Evaluated | Key Artifacts & Script Locations | Configuration Selected Based on Results | Role in Pipeline Lifecycle | Justified Claims | Unjustified Claims / Methodological Boundaries |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1: PDF Text Extraction** | Official QASPER `Dev` (Local arXiv PDFs) | **47 papers**, 127 answerable queries (635 records across 5 engines) | Script: `evaluate_step1_full_dev.py`<br>Artifacts: [`rq1_extraction_20261024_000639.json`](file:///c:/DACNTT/eval/results/rq1_extraction_20261024_000639.json), [`rq1_extraction_queries_20261024_000639.jsonl`](file:///c:/DACNTT/eval/results/rq1_extraction_queries_20261024_000639.jsonl) | Selected `pymupdf_layout` (heading F1 48.01%, 26.2 ms/page) and `pymupdf_plain` for fast fallback. | Exploratory Development & Extractor Selection | PyMuPDF improves heading recall and reduces extraction latency on QASPER Dev PDFs relative to pure-Python extractors. | Does **NOT** establish universal extraction superiority across arbitrary scientific publisher layouts (e.g. IEEE/Nature multi-column bounding boxes) without ground-truth OCR coordinates. |
| **RQ2: Document Chunking** | Official QASPER `Dev` (Same 47 Dev PDFs) | **47 papers**, 127 answerable queries (1,016 records across 8 strategies) | Script: `evaluate_part1b_chunking.py`<br>Artifacts: [`rq2_chunking_20261024_013443.json`](file:///c:/DACNTT/eval/results/rq2_chunking_20261024_013443.json), [`rq2_chunking_queries_20261024_013443.jsonl`](file:///c:/DACNTT/eval/results/rq2_chunking_queries_20261024_013443.jsonl) | Selected `hierarchical` Small-to-Big chunking as champion (nDCG@10 = 0.6880) and `section_overlap` as flat fallback. | Development & Chunking Architecture Selection | Small-to-Big hierarchical retrieval outperforms naive midpoint subword splitting under an equal 1,600-token budget on Dev ($p=0.0060^*$). | Does **NOT** establish downstream generative answer quality (RQ2 measured IR containment only, explicitly deferring generation). |
| **RQ3: Dense Embedding Selection** | Unified Cohort (QASPER `Dev` + `Train`) | **207 active scored papers**, 615 queries, 5,207 chunks | Script: `run_thesis_embedding_benchmark.py`<br>Artifacts: [`thesis_embedding_benchmark.json`](file:///c:/DACNTT/eval/results/thesis_embedding_benchmark.json), [`expanded_160_papers_benchmark_results.json`](file:///c:/DACNTT/eval/phases/phase_3_embedding/artifacts/expanded_160_papers_benchmark_results.json) | Selected `intfloat/e5-small-v2` as desktop champion (0.5522 nDCG@10, 30.2 ms latency, 384 dims, 33M params). | Development & Dense Encoder Selection | `e5-small-v2` achieves an optimal trade-off between latency (30.26 ms) and nDCG@10 (0.5522) on local CPU compared to larger architectures. | Cannot claim performance on unexposed test data; model was selected on this 207-paper cohort. **Crucially: Exactly 0 QASPER Test papers were included.** |
| **RQ4: Hybrid Retrieval (Dev Split)** | Official QASPER `Dev` | **276 papers**, 892 queries, 9,698 child chunks | Script: `evaluate_full_qasper_rq4_hybrid.py --split dev`<br>Artifacts: [`rq4_qasper_dev_hierarchical_benchmark.json`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_dev_hierarchical_benchmark.json) | Evaluated Dense vs BM25 vs RRF ($k=60$) vs Convex ($\alpha=0.7$). Neither hybrid arm was statistically significant on Dev ($p_{\text{adj}} = 1.000$). | Exploratory Retrieval Arm Check | On QASPER Dev under hierarchical context assembly, hybrid fusion does not degrade dense retrieval accuracy. | Cannot claim hybrid superiority over Dense on Dev ($p_{\text{adj}} = 1.000$). |
| **RQ4: Hybrid Retrieval (Test Split)** | Official QASPER `Test` | **408 papers**, 1,310 queries, 14,035 child chunks | Script: `evaluate_full_qasper_rq4_hybrid.py --split test`<br>Artifacts: [`rq4_qasper_test_hierarchical_benchmark.json`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json) | Evaluated Dense vs BM25 vs RRF vs Convex: Convex achieved $\text{nDCG@10}=0.5806$ ($p_{\text{adj}}=0.0140^*$). | Prior Confirmatory Retrieval Evaluation | Under split-wide BM25 background IDF across 14,035 chunks, Convex combination improved nDCG@10 on QASPER Test. | **EXPOSURE BOUNDARY:** Because QASPER Test was examined in RQ4, it is no longer an unexposed test set for the overall RAG pipeline. It must **not** be called an untouched confirmatory set; any subsequent full-pipeline evaluation on this set represents a post-retrieval-selection evaluation. |
| **RQ5: Preliminary Diagnostic Pilot** | Curated Seed Benchmark (`eval_benchmark_seed.json`) | **4 papers**, 16 queries (Non-QASPER arXiv preprints) | Script: [`evaluate_rq5_llm_generation.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py)<br>Artifacts: [`rq5_llm_generation_benchmark.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark.json) | Verified local Ollama CPU execution for `qwen2.5:0.5b`, `llama3.2:1b`, and `llama3.2:3b`. | Tooling Smoke Test & Harness Validation | Verifies harness execution, prompt formatting, and coordinate mapping on local CPU. | Cannot support statistical generalizability ($K=4$, $N=16$). Cannot be pooled with QASPER. |
| **Supplementary: SciFact Sanity Check** | SciFact Abstracts | **5,183 scientific abstracts**, 1,409 claims | Script: `evaluate_scifact_cross_dataset.py`<br>Artifact: `scifact_cross_dataset_benchmark.json` | Cross-domain transfer check (E5 achieved 0.6955 nDCG@10, 93.1% Recall@100). | Out-of-Domain Sanity Check | Confirms that E5 embedding weights generalize beyond NLP preprint vocabulary to broader biomedical/chemistry abstracts. | Task mismatch: SciFact evaluates binary claim verification (SUPPORT / CONTRADICT), not generative question answering over full papers. |

---

## 2. Reconciling the RQ3 Cohorts (211 vs. 160 vs. 207 Papers)

An audit of the source files clarifies the relationship between the paper counts in RQ3:

```text
                               Official QASPER v0.3
                                ┌──────────────────┐
                                │ Train:   888     │
                                │ Dev:     281     │
                                │ Test:    416     │
                                └─────────┬────────┘
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   │                                             │
      100 Dev Papers Streamed                       111 Train Papers Streamed
   (eval/prepared/qasper_corpus.json)          (expand_qasper_benchmark.py)
                   │                                             │
                   └──────────────────────┬──────────────────────┘
                                          │
                         Total Prepared in Expanded Corpus:
                                    211 Papers
                       (eval/prepared/expanded_corpus.json)
                                          │
         ┌────────────────────────────────┴────────────────────────────────┐
         │                                                                 │
   48 Dev Papers                                                   160 Held-out Papers
(dev_held_out_split.json)                                    (expanded_held_out_split.json)
[48 active with queries]                                      [49 Dev + 111 Train papers]
         │                                                                 │
         │                                                Inactive: 1612.02482 (0 queries)
         │                                                                 │
         │                                                    159 Active Papers with Queries
         │                                                                 │
         └────────────────────────────────┬────────────────────────────────┘
                                          │
                          Combined Active Scored Cohort:
                             207 Active Scored Papers
                            (615 Answerable Queries)
                     (eval/results/thesis_embedding_benchmark.json)
```

### Exact Reconciled Definitions:
1. **Prepared Corpus (`expanded_corpus.json` — 211 papers):**
   - 100 Dev papers + 111 Train papers.
   - Contains 3 Dev papers (`1806.04330`, `1812.10479`, `1909.04002`) that contain zero text-evidenced queries in QASPER.
2. **Listed Cohorts:**
   - Dev Cohort (`dev_held_out_split.json`): 48 papers (all from QASPER Dev), yielding 128 queries.
   - Held-Out Cohort (`expanded_held_out_split.json`): 160 papers (49 from Dev, 111 from Train).
   - Union of listed papers: $48 + 160 = 208$ papers. ($211 - 208 = 3$ extra Dev papers without text queries).
3. **Active Scored Cohort (`thesis_embedding_benchmark.json` — 207 papers):**
   - Paper `1612.02482` in `expanded_held_out_split.json` has 0 answerable queries in `expanded_qasper_sampled.json`.
   - Active papers scored: $48 + 159 = \mathbf{207}$ active papers.
   - Total queries scored: $128 + 487 = \mathbf{615}$ queries.
   - Total chunks indexed: $1,099 + 4,108 = \mathbf{5,207}$ chunks.

---

## 3. Detailed Overlap and Identifier Verification

An automated check across the source files produced the following verified intersections:

### 3.1. Official Split Overlap
- **Cross-Split Independence:**
  - Official QASPER Train (888 papers), Dev (281 papers), and Test (416 papers) share **0 overlapping paper IDs, 0 overlapping titles, and 0 overlapping question IDs**.
  - All 2,593 Train question IDs, 1,005 Dev question IDs, and 1,451 Test question IDs are globally unique 40-character SHA hashes.

### 3.2. RQ1 & RQ2 Query Verification
- Both `rq1_extraction_queries_20261024_000639.jsonl` and `rq2_chunking_queries_20261024_013443.jsonl` use the schema:
  - `paper_arxiv_id`: 47 unique arXiv IDs (100% in QASPER Dev; 0 in Train, 0 in Test).
  - `query_id`: Synthetic IDs (`Q_QASP_001` through `Q_QASP_250`) mapped directly via `original_id` in `eval/prepared/qasper_sampled.json`.
  - All 127 unique `query_id`s map to valid question hashes in official QASPER Dev. None map to Train or Test.

### 3.3. Diagnostic Seed Benchmark Disjointness
- The 16 queries in `backend/data/eval_benchmark_seed.json` span 4 papers (`1512.03385` ResNet, `1706.03762` Transformer, `2005.11401` RAG, `2106.09685` LoRA).
- None of these 4 arXiv IDs exist in QASPER Train, Dev, or Test.
- None of the 16 questions or titles match any record in QASPER Train, Dev, or Test.

### 3.4. Overlap with QASPER Test
- **RQ1, RQ2, and RQ3:** Exactly **0 QASPER Test papers or queries** were touched.
- **RQ4 Retrieval:** Evaluated **408 papers and 1,310 queries** from QASPER Test. (8 of the 416 Test papers contain only float tables/figures or unanswerable questions and produced 0 text chunks).
- **RQ5:** Exactly **0 QASPER Test papers** were evaluated.

### 3.5. Total Unique Historically Exposed Papers Across All Experiments (804 Partition-Level vs. 802 Active Runs)
To resolve the arithmetic discrepancy and methodological distinction in the reported total of historically exposed papers:
1. **804 Unique Exposed Papers (Partition-Level Historical Total):**
   $$111\text{ Train (RQ3)} + 281\text{ Dev (entire Dev split partition)} + 408\text{ Test (evaluated in RQ4 Test)} + 4\text{ Seed (RQ5 Pilot)} = \mathbf{804\text{ unique papers}}$$
   *Methodological Basis:* The entire official QASPER Dev split (281 papers) was designated as development/exploratory data and cannot be used as an unexposed test set. Adding the 111 exposed Train papers, 408 evaluated Test papers, and 4 non-QASPER seed papers yields strictly **804 unique papers**.
2. **802 Unique Exposed Papers (Active Benchmark Run Total):**
   $$111\text{ Train (RQ3)} + 279\text{ Dev (active runs)} + 408\text{ Test (evaluated in RQ4 Test)} + 4\text{ Seed (RQ5 Pilot)} = \mathbf{802\text{ unique papers}}$$
   *Source of Discrepancy:* In official QASPER Dev (281 papers), exactly 2 papers (`1804.00720` and `1903.07406`) contained exclusively unanswerable questions (`unanswerable: true`) with empty evidence (`evidence: []`), producing 0 non-empty text evidence paragraphs. Consequently, neither paper had an active evaluation run in RQ1, RQ2, RQ3, or RQ4 ($281 - 2 = 279$ Dev papers with active runs).
   *Resolution of Arithmetic Discrepancy:* Calculating $111 + 281 + 408 + 4$ yields strictly **804**, not 802. Writing $111 + 281 + 408 + 4 = 802$ was an arithmetic error that mistakenly substituted the 281 partition count while reporting the 802 active-run total.
3. **Zero Impact on the Unexposed Train Reservoir:**
   Both counts establish identically that the unexposed Train reservoir is **777 papers** ($888 - 111 = 777$) and the eligible candidate pool ($m \ge 2$) is **487 papers**, with **strictly zero prior exposure** across all repository experiments.

---

## 4. The Experiment-Unexposed QASPER Train Reservoir

A key result of this audit is the quantification and structural validation of the unexposed portion of QASPER Train:

```text
Total Official QASPER Train Papers:              888 papers (2,593 questions)
Papers Used in RQ3 Embedding Benchmark:          111 papers (  439 questions)
────────────────────────────────────────────────────────────────────────────
Experiment-Unexposed Train Papers:               777 papers (2,154 questions)
  - Retrieval-Eligible Questions (Text Evidence): 1,729 questions
  - Answer-Generation-Eligible Questions:         1,916 questions (incl. 187 float-only)
  - End-to-End Eligible Questions (Atomic Joint): 1,729 questions
  - Float/Table-Only Answerable Questions:          187 questions (no text evidence)
  - Strictly Unanswerable Questions:                238 questions (consensus unanswerable)
```

### 4.1. Paper Breakdown by End-to-End Eligible Question Count ($m \ge 2$):
- Papers with $\ge 2$ end-to-end eligible questions: **487 papers**
- Papers with exactly 1 end-to-end eligible question: **226 papers**
- Papers with 0 end-to-end eligible questions: **64 papers** (only float tables/figures or unanswerable)
- *Total unexposed papers:* $487 + 226 + 64 = \mathbf{777\text{ papers}}$

### 4.2. Verification of QASPER Annotation Coupling and Atomic Grounding:
To guarantee that benchmark evaluation does not pair unrelated evidence and answer annotations:
1. **Zero Decoupled Annotations:** We audited every question across official QASPER v0.3 (`train`, `dev`, `test`). In **100% of cases**, there are **0 decoupled questions** where non-float text evidence was provided by one annotator while the usable answer came exclusively from another annotator.
2. **Atomic Joint Grounding:** Whenever an annotator highlighted text evidence, that exact same annotator provided a valid, non-empty, non-unanswerable answer in the *same annotation object* (`annotator_evidence_with_unanswerable_flag = 0`).
3. **Float-Only Disconnect:** The difference of 187 questions between answer-generation eligibility ($1,916$) and end-to-end eligibility ($1,729$) consists entirely of questions answered strictly via figures and tables (`FLOAT SELECTED: ...`) without body text paragraphs. While valid for multimodal QA, they lack text-retrieval ground truth in a document text index and are properly excluded from text RAG evaluation.
4. **Multi-Annotator Ambiguity Audit:**
   - In the 777 unexposed Train papers, 2,106 questions have 1 annotator, and 48 questions have 2 annotators.
   - Among the 48 multi-annotator questions:
     - 41 questions have both annotators providing usable answers.
     - 6 questions have split votes: one annotator found text evidence (1–5 paragraphs) and answered, while the second marked `unanswerable: true` with 0 evidence.
     - 1 question has unanimous `unanswerable: true` from both annotators (`f7070b2e258beac9b09514be2bfcc5a528cc3a0e`).
   - All 6 split-vote questions contain at least one complete atomic text-evidence + answer pair and are retained with both references evaluated under the standard max-over-annotators SQuAD/QASPER protocol.

### 4.3. Nature of This Reservoir:
- **Project-Level Status:** This 777-paper cohort is **unexposed to the identified experiments (RQ1–RQ5)** within this project's development history.
- **Important Distinction from an Independent or Pristine Dataset:**
  While these papers were unexposed in our experiments, they originate from the **official QASPER Train split**. They share QASPER's domain distribution, LaTeX extraction format, and crowdworker collection protocol. They must be accurately described as a *paper cohort unexposed to the identified experiments drawn from QASPER Train*, and must **not** be described as an independent or pristine holdout.

---

## 5. Verification of Hybrid RRF vs. Convex Fusion Claims

We audited the retrieval implementations in `backend/apps/documents/services/rag_service.py` and `eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py` to assess previous assertions regarding RRF and Convex fusion:

### 5.1. Verified in Code:
1. **Production Retrieval Mechanism:**
   - Production retrieval in `DocumentRAG.query` (lines 904–920) and `RagService.search_hybrid_rrf` (lines 656–711) **exclusively uses Reciprocal Rank Fusion (RRF)** with $k=60$.
   - Convex fusion is not implemented in production `DocumentRAG` or `RagService`.
2. **BM25 Corpus Scope & IDF Computation:**
   - **Production (`DocumentRAG.__init__`):** `self.bm25 = BM25Okapi([text.lower().split() for text in self.content])`. BM25 is initialized locally on the child chunks of **that single document** (~35–60 chunks). IDF is computed locally within that document.
   - **RQ4 Offline Benchmark (`evaluate_full_qasper_rq4_hybrid.py`):** `bm25 = WordPieceBM25(chunks, tokenizer)`. BM25 was initialized globally across **all 14,035 chunks of the 408 Test papers**. IDF was computed against the entire split-wide background vocabulary.

### 5.2. Verified in Empirical Benchmark Artifacts:
In `rq4_qasper_test_hierarchical_benchmark.json` (evaluated under hierarchical context assembly across 408 Test papers):
- `Dense Only (e5-small-v2)`: nDCG@10 = 0.5655, Recall@20 = 0.6366
- `BM25 Only (WordPiece)`: nDCG@10 = 0.5065, Recall@20 = 0.5908
- `Hybrid RRF (k=60)`: nDCG@10 = 0.5662, Recall@20 = **0.6413** ($\Delta = +0.0008, p_{\text{adj}} = 0.8696$)
- `Hybrid Convex (alpha=0.7)`: nDCG@10 = 0.5806, Recall@20 = **0.6525** ($\Delta = +0.0152^*, p_{\text{adj}} = 0.0140^*$)

### 5.3. Clarification on Prior Recall@20 Values:
- Earlier project notes cited a `Recall@20 = 0.9279` or `0.9558` for RRF.
- **Audit Clarification:** Those values came from `step6_hybrid_rrf_benchmark.json` (48 papers) and `expanded_160_hybrid_rrf_benchmark.json` (160 papers), which evaluated **flat `section_overlap` chunking**.
- In the RQ4 Test hierarchical benchmark (`rq4_qasper_test_hierarchical_benchmark.json`), the evaluation units were **unique parent sections**, where RRF Recall@20 was **0.6413** and Convex Recall@20 was **0.6525**. These numbers must not be conflated across differing chunking strategies.

### 5.4. Labeling of Analytical Hypotheses:
- The argument that *single-document min-max normalization collapses because technical keywords repeat across sections, compressing IDFs* is a **mathematical and analytical deduction**, supported by the boundary condition in `convex_fuse` (`b_norm = np.zeros_like(b_vals) if b_max == b_min`).
- However, this has **not been tested as an empirical ablation** comparing local vs. global IDF on the same test split.
- **Status:** Analytical rationale for maintaining provisional RRF in production, pending future empirical validation if desired.
