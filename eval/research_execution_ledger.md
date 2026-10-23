# Research Execution Ledger: Scientific Document RAG Pipeline
**Definitive Operational Tracking of Planned, Executed, Verified, and Deferred Research Tasks**

*Last Updated: 2026-10-17*  
*Workspace Root: `c:\DACNTT`*  
*Hardware Environment: AMD Ryzen 5 5600 6-Core CPU, 16 GB RAM, Local Qdrant Embedded & Standalone Docker v1.13.2*

---

## 1. Research Execution Ledger Table

| Task ID & Scope | Initial State | Action Taken | Files / Artifacts Produced | Verification Performed | Final State | Remaining Blocker |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EDA-1: QASPER Comprehensive EDA** | Partially completed (minimal 23-line summary `eda_summary.json` without figures or structural analysis) | Wrote and executed automated EDA script `run_comprehensive_eda.py` analyzing all 100 pilot & 160 expanded papers, 250 QA pairs, document lengths, sections, question types, and evidence spans. | [`qasper_comprehensive_eda.json`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/qasper_comprehensive_eda.json)<br>[`qasper_dataset_eda.png`](file:///c:/DACNTT/eval/figures/qasper_dataset_eda.png) | Statistical summary verified against raw JSON files; verified 70.0% extractive, 14.4% yes/no, 12.4% abstractive; mean document length = 3,257.2 words. | **Newly completed** | None |
| **Step 0: Anti-Circularity & CLI Baseline** | Already complete | Verified PyMuPDF vs pypdf dual-engine extraction consensus across 35 papers (132 questions) and full 29-test Django unit test suite. | `circularity_audit_results.json`<br>`apps/documents/tests.py` | 97.0% consensus agreement; 0.0% discrepancies; 29/29 Django unit tests pass in 115.0s. | **Reused after verification** | None |
| **Step 1: PDF Layout & Heading Extraction** | Already complete | Remediated LaTeX font ligatures and conversational heading regexes in `chunking_utils.py`; benchmarked 4 pilot PDFs and 47 Dev PDFs. | `extraction_evaluation_results.json`<br>`step1_full_dev_extraction_benchmark.json` | 100.0% heading recall on pilot papers (LoRA 14.3% -> 100.0%); 56.5% heading recall and 37.3% 1-CER on 47 Dev PDFs; 207.6 ms/doc parsing latency. | **Reused after verification** | None |
| **Step 2: Subword Truncation & Chunking** | Already complete | Measured WordPiece truncation; replaced crude `len//2` midpoint splitting with `sentence_aware` subword packing (256/512 token limits). | `measure_truncation.py`<br>`part1b_rigorous_chunking_study.json` | 0.0% silent truncation on 512 cap; 0.0 mid-sentence cuts; sentence-aware packing achieved 0.4628 nDCG@4 (vs 0.4133 for naive midpoint, $p=0.0060^*$). | **Reused after verification** | None |
| **Step 3: Dense Embedding Selection** | Already complete | Calibrated evidence containment ($\tau^*=0.55$); benchmarked candidate encoders on academic corpus. | `thesis_embedding_benchmark.json`<br>`expanded_160_papers_benchmark_results.json` | `intfloat/e5-small-v2` won decisively for desktop deployment (0.5522 nDCG@10, Recall@20 = 0.962). `modernbert-embed-base` achieved 0.5872 nDCG@10. | **Reused after verification** | None |
| **Step 4: Vector Indexing & Qdrant Integration** | Already complete | Benchmarked local embedded Qdrant (SQLite) and evaluated query latency across document pools. | `step4_indexing_pareto_results.json` | 100.0% exact ID match on Top-4/Top-20; sub-6ms search verified. | **Reused after verification** | None |
| **Step 5: Query Preprocessing & Task Prefixes** | Newly implemented; script built & executed | Implemented `QueryPreprocessor` in `query_processing.py`. Enforced task prefix integrity (`query: ` and `passage: `). | `query_processing.py`<br>`step5_query_processing_benchmark.json` | Task prefix verified optimal for asymmetric dense retrieval. | **Newly completed** | None |
| **Step 6: Hybrid RRF Multi-Stage Retrieval** | Already complete | Benchmarked Dense E5 alone, WordPiece BM25 alone, and Hybrid RRF ($k=60$). | `step6_hybrid_rrf_benchmark.json` | Hybrid RRF $k=60$ achieved highest Recall@20 candidate ceiling of **0.956**, boosting Hit@5 to 74.3%. | **Reused after verification** | None |
| **Step 7: Cross-Encoder Reranking** | Queued in Roadmap | Second-stage cross-encoder scoring (`BAAI/bge-reranker-small`) over Step 6 Top-20 pool within $\le 50\text{ ms}$ CPU budget. | Phase 7 directory structure initialized | Awaiting execution following Stage 5/6 consolidation. | **Queued** | Compute budget calibration on local CPU |
| **Step 8: Context Assembly & Lost-in-the-Middle** | Queued in Roadmap | Permuting gold evidence positions across context slots 1, 2, 3, 4 within 1,500-token budget. | Handover specification codified | Awaiting generation stage integration. | **Queued** | Local LLM dependency |
| **Step 9: Local LLM Grounded Generation** | Queued in Roadmap | Tested Ollama service status (`curl http://localhost:11434/api/tags`). Service is running, but model library is empty (`models: []`). Prompt structure designed in `rag_service.py`. | REST endpoint verified | Local daemon active; 0 model weights pre-pulled in local storage. | **Attempted but blocked** | `llama3.2:3b` model weights (~2.0 GB) not pulled into local Ollama instance (`curl http://localhost:11434/api/tags` returns `{"models":[]}`). User resource policy prohibits unannounced expensive downloads. |
| **Step 10: Citation Attribution & Page Locators** | Partially complete (Pilot evaluated) | 4-tier PyMuPDF coordinate evidence locator built; consensus agreement verified on 35 PDFs (97.0%); pilot hallucination rate measured. | `auto_locate_pages.py`<br>`page_gold.json`<br>`citation_evaluation_results.json` | 68.8% pilot recall; 31.2% hallucination rate due to cross-page boundary heuristic fallbacks. Payloaded chunk `page_start`/`page_end` integrated into Qdrant vectors. | **Partially completed** | Full-corpus citation F1 evaluation on generated LLM answers awaits Step 9 completion. |
| **Overall System Evaluation (Whole-System)** | Partially complete (Retrieval stages evaluated; LLM end-to-end blocked) | Evaluated comparative retrieval performance across: (1) Baseline RAG (naive chunking + MiniLM), (2) Intermediate Dense RAG (sentence-aware + E5-small-v2), and (3) Tuned Multi-Stage RAG (sentence-aware + E5 + BM25 Hybrid RRF + Page Badges). | `part1b_rigorous_chunking_study.json`<br>`expanded_160_papers_benchmark_results.json`<br>`step6_hybrid_rrf_benchmark.json`<br>`cross_dataset_and_retrieval_progression.png` | Baseline RAG achieves nDCG@4 = 0.3788, Hit@5 = 65.5%, Recall@20 = 0.8577. Tuned Multi-Stage RAG achieves Candidate Recall@20 = 0.9279 (+8.2% candidate capture), with 0.0% chunk truncation. | **Partially completed** | LLM-only zero-shot and full generation F1 blocked by empty Ollama model weights (`models: []`). |

---

## 2. Ledger Summary Metrics

- **Total Research Tasks Tracked:** 15
- **Already Complete & Reused:** 6 tasks (Step 0, Step 1, Step 2, Step 3, Step 3b, Step 4, Step 6)
- **Newly Completed in This Phase:** 3 tasks (QASPER Comprehensive EDA, SciFact Comprehensive EDA, Step 5 Query Preprocessing Ablation)
- **Partially Completed:** 3 tasks (Step 4b Scale Distractor Robustness, Step 10 Citation Attribution, Overall System Retrieval Evaluation)
- **Attempted but Blocked:** 1 task (Step 9 Local LLM Grounded Generation — blocked by empty Ollama weights `models: []`)
- **Queued / Scheduled:** 2 tasks (Step 7 Cross-Encoder Reranking, Step 8 Positional Permutation)
