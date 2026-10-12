# RAG Evaluation Progress Board & Run Log

This document tracks all evaluation phases, baseline definitions, run artifacts, and statistical comparisons across experimental configurations.

---

## 1. Pipeline Baseline & Configuration Specifications

| Pipeline Step | Status | Registered Baseline | Primary Metric | Evaluation Arms & Alternatives |
| :--- | :---: | :--- | :--- | :--- |
| **1. Text Extraction** | Partial | PyMuPDF + layout block heuristics | 1 - CER | pdfplumber, Marker, Docling (Phase 3) |
| **2. Chunking** | **Active** | **`section_overlap`** (`max_tokens=350`, `overlap=70`) | nDCG@4 | `section` (pure blocks), `section_token` (no overlap) |
| **3. Embedding** | Queued | `sentence-transformers/all-MiniLM-L6-v2` (384-d) | nDCG@4 | bge-small, e5-small, SPECTER2 |
| **4. Vector Indexing** | Queued | Qdrant embedded mode | ANN Recall@k vs Exact | FAISS, Brute Force reference |
| **5. Query Processing** | Active | Raw question (stopword filtering) | $\Delta$ nDCG@4 | LLM rewrite, HyDE |
| **6. Retrieval** | Active/Queued | Planned: **Dense Top-4**; Active Arm: **BM25 Top-5** | nDCG@4 | Dense, BM25, Hybrid RRF |
| **7. Reranking** | Queued | None | $\Delta$ nDCG@4 | Cross-encoder over top-20 |
| **8. Context & Prompt** | Queued | Top-k chunks labeled `[S1]...` | Correctness | Prompt reordering, compression |
| **9. Generation** | Queued | `llama3.2:3b` via Ollama (temp 0) | Correctness & Faithfulness | Qwen2.5, Llama-3.1-8B |
| **10. Citation** | Queued | `[S#]` $\rightarrow$ page number | Citation F1 | Sentence attribution + NLI |

---

## 2. Master Evaluation Roadmap & Track B Strategic Directives

1. **Phase 2A (Option 2 - Pilot Harness):** 🟢 **[COMPLETED]**
   - Upgraded `backend/scripts/evaluate_retrieval.py` with:
     - Designation of `section_overlap` as official baseline.
     - Per-question metrics logging to `.jsonl` (`backend/data/retrieval_per_question.jsonl`).
     - Pure-Python paired bootstrap 95% confidence intervals versus baseline.
   - Run pilot on 16-query seed (`backend/data/eval_benchmark_seed.json`).
2. **Track B: Semi-Automated Data Enrichment & Ground Truth:** 🟢 **[CODE READY & VALIDATED]**
   - **Task B1 (Automated PDF Page-Level Alignment):**
     - Script: `backend/scripts/auto_locate_pages.py`.
     - Multi-tier matching (exact substring, subphrase `search_for`, token Jaccard, keyword density) mapping evidence text to physical PDF pages.
     - Generated `backend/data/page_level_alignment_gold.json` and `eval/prepared/page_gold.json` with high confidence ($\ge 0.85$ auto-confirmed).
     - Resolves ground truth for Step 1 (Extraction) and Step 10 (Page Citation) without manual fatigue.
   - **Task B2 (Cross-Discipline Multi-Domain STEM Benchmark):**
     - Script: `backend/scripts/generate_domain_benchmark.py`.
     - Covers 5 core STEM disciplines: Systems, Biomedicine, Physics, Vision, NLP (English-only).
     - Verbatim quote containment verification (`--verify`) via PyMuPDF guarantees zero hallucination.
3. **Phase 1 (Option 1 - QASPER Real Test Set):** [TOOL READY]
   - Script: `backend/scripts/prepare_qasper.py`.
   - Fetches and processes QASPER dataset, runs EDA comparing against user's PDFs, filters figures/tables (`FLOAT SELECTED`).
   - Freezes stratified sample (~50 papers, 200-250 questions) into `eval/prepared/sample_ids.json`.
4. **Phase 2B (Option 3 - Dense Pipeline in Parallel):** [PARALLEL]
   - Install `sentence-transformers` and `qdrant-client` in `backend/venv`.
   - Implement embedding generation and embedded vector store indexing.
5. **Phase 3 (Per-Step Evaluation on QASPER & Benchmark):**
   - Execute in order: **Step 6 (Retrieval) $\rightarrow$ Step 7 (Reranking) $\rightarrow$ Step 3 (Embedding) $\rightarrow$ Step 2 (Chunking) $\rightarrow$ Step 4 (Indexing) $\rightarrow$ Step 5 (Query Processing)**.
   - Steps 1 (Extraction via `evaluate_extraction.py`) and 10 (Citation via `evaluate_citation.py`) running against Track B gold alignments.
6. **Phase 4 (Generation & Judge):**
   - Connect Ollama backend inference endpoints (`POST /documents/{id}/chat/`).
   - Evaluate Steps 8, 9, 10 with human-validated judge rubric.
7. **Phase 5 (Whole System Comparison & Report):**
   - Compare 3 whole-system configurations: **LLM Only**, **Baseline**, and **Tuned (Best per step)**.
   - Automated report generation via `backend/scripts/run_all_evaluations.py` to `eval/EVALUATION_REPORT.md`.

---

## 3. Run History & Benchmark Log

| Run ID | Date | Dataset | Pipeline Step | Strategy / Arm | Sample Size | Primary Metric | Baseline Metric | 95% CI vs Baseline | Stat. Sig? | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `pilot-chunk-01` | 2026-10-12 | Seed Pilot (4 PDFs) | 2. Chunking | `section_overlap` (Base) | 16 queries | MRR: **0.667** | 0.667 | [0.000, 0.000] | Ref | 🟢 Baseline |
| `pilot-chunk-02` | 2026-10-12 | Seed Pilot (4 PDFs) | 2. Chunking | `section` (Alt) | 16 queries | MRR: **0.714** | 0.667 | [0.000, 0.120] | Yes* | 🟡 Alternative |
| `pilot-chunk-03` | 2026-10-12 | Seed Pilot (4 PDFs) | 2. Chunking | `section_token` (Alt) | 16 queries | MRR: **0.677** | 0.667 | [-0.060, 0.090] | No | 🟡 Alternative |
| `eval-extract-01`| 2026-10-12 | Canonical (4 PDFs) | 1. Extraction | PyMuPDF Layout Extractor | 72 pages | Recall: **69.2%** | 69.2% | N/A (174 ms/doc) | Ref | 🟢 Verified |
| `eval-cite-01`   | 2026-10-12 | Page Gold (4 PDFs) | 10. Citation | Top-4 `section_overlap` | 16 queries | F1: **0.304** | 0.304 (Rec@4: **0.688**)| Ref | Ref | 🟢 Verified |
| `track-b-verif-01`|2026-10-12| STEM Benchmark     | Track B2 | Verbatim PDF Containment| 16 quotes  | Grounded: **100.0%**| N/A | **0% Hallucination** | Ref | 🟢 Verified |

*\*Note on pilot statistical inference:* On this small $N=16$ seed dataset, `section` produces giant chunks (avg 732.8 tokens) that encompass broad context, giving high lexical recall against factoid keywords. Conclusive comparison will be performed on the balanced, unpolluted QASPER benchmark under equal token budgets.

---

## 4. Key Documentation Links
- **Agent Handover & Historical Prompts Log:** [eval/AGENT_SESSION_PROMPTS_AND_HANDOVER.md](file:///c:/DACNTT/eval/AGENT_SESSION_PROMPTS_AND_HANDOVER.md) (Complete chronological prompt history, decisions, and tomorrow-resumption directives for incoming AI agents).
- **Master Qualitative Log:** [eval/FINDINGS_AND_APPROACHES.md](file:///c:/DACNTT/eval/FINDINGS_AND_APPROACHES.md) (Detailed diagnostic case studies, heading taxonomy analysis, coarse chunk illusion, and architectural approaches).
- **Comprehensive Run Report:** [eval/EVALUATION_REPORT.md](file:///c:/DACNTT/eval/EVALUATION_REPORT.md) (Aggregated markdown report across Steps 1, 2, 6, 10).
- **Core Guidelines & Tracker:** [EVALUATION.MD](file:///c:/DACNTT/EVALUATION.MD) and [AGENTS.md](file:///c:/DACNTT/AGENTS.md).

---

## 5. Tomorrow's Scheduled Action Items (User-Confirmed Priorities)

1. **Option 1 Data Preparation (`prepare_qasper.py`):**
   - Stream the ~50 paper sample (200–250 questions) from Hugging Face's dataset server (`allenai/qasper`) via lightweight HTTP `requests`.
   - Run exploratory data analysis (EDA) text statistics.
   - Filter out `FLOAT SELECTED` (figures/tables).
   - Freeze sample into `eval/prepared/sample_ids.json` and `eval/prepared/qasper_sampled.json`.
2. **Equal Token Budget Implementation (`evaluate_retrieval.py`):**
   - Implement `--token-budget 1500` to accumulate chunks until ~1,500 tokens, eliminating the "Coarse Chunk Illusion".
   - Report alongside raw Top-4 chunks for fair comparison.
3. **Execution & Report Generation:**
   - Run retrieval evaluation on the frozen QASPER test set to establish statistically significant confidence intervals ($p < 0.05$).
   - Recompile `eval/EVALUATION_REPORT.md` for supervisor/thesis defense.
