# Backend Scripts & Evaluation Harness Directory

This directory contains data preparation, document downloading, empirical benchmark runners, and shared statistical evaluation utilities for the Scientific Document RAG pipeline.

```
backend/scripts/
├── downloads/        # Downloading external raw corpora and PDFs (arXiv, QASPER)
├── data_prep/        # Data stratification, ground-truth page alignment, benchmark generation
├── evaluation/       # RQ1–RQ5 core benchmark harnesses, component ablations, and system evaluations
├── tools/            # Experiment utilities (Pareto frontier plotting, phase organizer)
├── eval_common/      # Canonical evaluation package (nDCG, MRR, bootstrap CI, relevance containment)
├── eval_common.py    # Backwards-compatibility shim re-exporting from eval_common
└── README.md         # Directory layout and script catalog (this file)
```

---

## 1. Directory Breakdown & Script Index

### `downloads/` — Corpus & PDF Retrieval
Utilities for polite, rate-limited downloading of external academic papers and validation corpora:
- **[`downloads/download_dev_pdfs.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/downloads/download_dev_pdfs.py)**: Downloads all 48 Dev arXiv PDFs into `eval/pdfs/dev/` for extraction benchmarking and CER measurement.
- **[`downloads/download_qasper_pdfs.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/downloads/download_qasper_pdfs.py)**: Downloads representative arXiv PDFs from the frozen QASPER evaluation sample into `eval/data/pdfs/`.

### `data_prep/` — Dataset Preparation & Alignment
Scripts for dataset stratification, ground-truth extraction, and vector export:
- **[`data_prep/prepare_qasper.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/prepare_qasper.py)**: Filters and stratifies the raw QASPER dataset into frozen 48 Dev / 48 Held-Out splits and extracts gold evidence.
- **[`data_prep/expand_qasper_benchmark.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/expand_qasper_benchmark.py)**: Expands the QASPER evaluation cohort to 160 papers / 487 queries.
- **[`data_prep/prepare_containment_queue.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/prepare_containment_queue.py)**: Prepares human review queues for calibrating evidence containment thresholds.
- **[`data_prep/auto_locate_pages.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/auto_locate_pages.py)**: 4-tier automated PDF page-level evidence locator generating ground-truth coordinates.
- **[`data_prep/cross_validate_page_locators.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/cross_validate_page_locators.py)**: Dual-engine anti-circularity validator (PyMuPDF vs. `pypdf`) verifying page ground truth.
- **[`data_prep/apply_consensus_pages.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/apply_consensus_pages.py)**: Applies consensus page boundaries resolved during cross-engine audits.
- **[`data_prep/generate_domain_benchmark.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/generate_domain_benchmark.py)**: Multi-discipline STEM benchmark generator and zero-hallucination quote containment verifier.
- **[`data_prep/prepare_researchqa.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/prepare_researchqa.py)**: Ingestion & multi-paper citation graph generator (Method B) mapping survey rubrics to target primary paper citations.
- **[`data_prep/prepare_researchqa_survey.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/prepare_researchqa_survey.py)**: Builds QASPER-schema-identical benchmark from 4 ResearchQA survey papers (Method A) — outputs corpus, sampled queries, and dev/held-out split to `eval/prepared/`.
- **[`data_prep/export_embeddings_for_hnsw.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/data_prep/export_embeddings_for_hnsw.py)**: Exports model embeddings and queries for large-scale Google Colab HNSW indexing evaluation.

### `evaluation/` — Benchmark Harnesses & Research Questions (RQ)
Empirical evaluation runners evaluating each pipeline stage against quantitative metrics:

#### Core Master Thesis Research Questions (RQs)
- **[`evaluation/evaluate_rq1_extractors.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_rq1_extractors.py)**: **[RQ1]** Multi-engine PDF layout parser evaluation (PyMuPDF layout vs. plain, `pypdf`, `pdfminer`, `pdfplumber`).
- **[`evaluation/evaluate_rq2_chunking.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_rq2_chunking.py)**: **[RQ2]** Sentence-aware subword packing vs. fixed, semantic, and hierarchical chunking under equal token budgets.
- **[`evaluation/run_rq3_embedding_benchmark.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/run_rq3_embedding_benchmark.py)** & **[`evaluation/run_thesis_embedding_benchmark.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/run_thesis_embedding_benchmark.py)**: **[RQ3]** Comprehensive benchmark across 11 open-source dense and sparse encoders with cluster bootstrap confidence intervals.
- **[`evaluation/evaluate_rq5_llms.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_rq5_llms.py)**: **[RQ5]** Grounded local generation comparison across compact LLM architectures.
- **[`evaluation/verify_hierarchical_production_parity.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/verify_hierarchical_production_parity.py)**: Validates parity between experimental hierarchical retrieval and production backend service.
- **[`evaluation/run_all_evaluations.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/run_all_evaluations.py)**: Master runner orchestrating multi-step evaluations and compiling `eval/EVALUATION_REPORT.md`.

#### Step & Component Ablations
- **[`evaluation/evaluate_citation.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_citation.py)**: Measures page-level citation precision, recall, and hallucination rate.
- **[`evaluation/evaluate_containment_labels.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_containment_labels.py)**: Calibrates strict evidence containment threshold $\tau^* = 0.55$.
- **[`evaluation/evaluate_extraction.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_extraction.py)** & **[`evaluation/evaluate_step1_full_dev.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_step1_full_dev.py)**: Heading taxonomy recall and document character error rate.
- **[`evaluation/evaluate_part1b_chunking.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_part1b_chunking.py)** & **[`evaluation/measure_truncation.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/measure_truncation.py)**: WordPiece subword truncation analysis.
- **[`evaluation/evaluate_part2_dev_candidates.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_part2_dev_candidates.py)** & **[`evaluation/evaluate_part2_held_out.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_part2_held_out.py)**: Dev and unblinded held-out evaluation for embedding model selection.
- **[`evaluation/evaluate_parity_fastembed.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_parity_fastembed.py)**: FastEmbed ONNX vs. PyTorch FP32 cosine similarity parity verification.
- **[`evaluation/evaluate_step4_indexing.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_step4_indexing.py)** & **[`evaluation/evaluate_step4_hnsw_scale.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_step4_hnsw_scale.py)**: Qdrant SQLite and server indexing latency vs. exact BLAS.
- **[`evaluation/evaluate_step6_hybrid_rrf.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_step6_hybrid_rrf.py)**: Dense + BM25 Reciprocal Rank Fusion ($k=60$) parameter tuning.
- **[`evaluation/evaluate_researchqa_citation_retrieval.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_researchqa_citation_retrieval.py)**: ResearchQA Method B benchmark evaluating cross-document multi-paper citation retrieval completeness (Paper Recall@k, Full Coverage@k, nDCG@10).
- **[`evaluation/evaluate_researchqa_survey_retrieval.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_researchqa_survey_retrieval.py)**: ResearchQA Method A benchmark — QASPER-schema-compatible harness using survey section ground-truth. Evaluates BM25/Dense/Hybrid RRF with nDCG@4/10, MRR@5, Hit@5, Recall@20, and the unique Section Hit@1 metric.
- **[`evaluation/evaluate_retrieval.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/evaluation/evaluate_retrieval.py)**: Multi-paper passage retrieval across candidate strategies.

### `tools/` — Utilities & Automation
- **[`tools/plot_pareto_frontier.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/tools/plot_pareto_frontier.py)**: Generates publication-grade Pareto frontier plots (accuracy vs. latency / throughput).
- **[`tools/organize_eval_phases.py`](file:///home/oracle/code/science-document-viewer/backend/scripts/tools/organize_eval_phases.py)**: Organizes evaluation artifacts and logs into modular phase subdirectories under `eval/phases/`.

### `eval_common/` & `eval_common.py` — Shared Evaluation Library
Shared module providing standard Information Retrieval metrics and non-parametric statistical tests:
- **`stats.py`**: `compute_dcg`, `compute_ndcg`, `compute_mrr`, `compute_recall`, `compute_hit_at_k`, `paired_cluster_bootstrap`, `holm_bonferroni_correction`.
- **`relevance.py`**: `clean_evidence`, `is_chunk_hit`, `count_relevant_chunks`, regex tokenization, and academic stopwords.
- **Unit Tests**: `test_stats.py`, `test_chunkers.py`, `test_prefixes.py`.
