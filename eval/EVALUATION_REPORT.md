# Scientific Document RAG Pipeline -- Comprehensive Evaluation Report

*Generated on: 2026-10-12 22:34:41*

---

## Executive Summary

This report aggregates empirical evaluations across the academic paper RAG pipeline,
incorporating Track B (Semi-Automated Data Enrichment & Multi-Discipline STEM Ground Truth).

| Pipeline Step | Evaluated Component | Primary Metric | Baseline Value | Status |
| :--- | :--- | :--- | :---: | :---: |
| **Step 1: Text Extraction** | PyMuPDF Layout Extractor | Heading Recall | **69.2%** | 🟢 Verified |
| **Steps 2 & 6: Retrieval** | `section_overlap` (Baseline) | MRR | **0.719** | 🟢 Verified |
| **Step 10: Citation** | Page-Level Attribution | Citation F1 | **0.304** | 🟢 Verified |

---

## 1. Step 1: PDF Text & Section Extraction

- **Extractor:** PyMuPDF_layout_aware_section_extractor
- **Mean Section Heading Recall:** 69.2%
- **Total Documents:** 4
- **Total Pages:** 72
- **Corpus Tokens:** 56425
- **Average Extraction Latency:** 174.73 ms (9.71 ms/page)

| Document | Pages | Extracted Sections | Tokens | Heading Recall | Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Attention.pdf` | 15 | 25 | 8662 | 87.5% | 264.08 ms |
| `LoRa.pdf` | 26 | 19 | 20051 | 14.3% | 205.52 ms |
| `Retrieval-Augmented.pdf` | 19 | 21 | 14053 | 75.0% | 130.65 ms |
| `deep_residual.pdf` | 12 | 12 | 13659 | 100.0% | 98.67 ms |

---

## 2. Steps 2 & 6: Chunking Strategies & Retrieval Evaluation

Evaluation evaluated queries against a unified multi-paper chunk corpus using BM25 relevance scoring.
Paired bootstrap 95% confidence intervals are computed against the baseline strategy (`section_overlap`).

| Strategy | Chunks | Hit Rate@1 | Hit Rate@3 | MRR | Difference vs Base | 95% Bootstrap CI | Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |

---

## 3. Step 10: Page-Level Citation & Attribution Accuracy

Evaluates whether the physical PDF page numbers referenced by top retrieved chunks align with
the ground-truth evidence pages established by Track B (Task B1 `auto_locate_pages.py`).

| Strategy | Queries | Recall@1 | Recall@3 | Recall@4 | Precision | Citation F1 | Hallucination Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `section_overlap` **[BASE]** | 16 | 0.438 | 0.625 | 0.688 | 0.198 | **0.304** | 0.312 |
| `section` | 16 | 0.562 | 0.625 | 0.812 | 0.224 | **0.348** | 0.188 |
| `section_token` | 16 | 0.5 | 0.562 | 0.625 | 0.182 | **0.279** | 0.375 |

---

## 4. Track B: Multi-Domain STEM Ground Truth Verification

- **Discipline Coverage:** 5 Core STEM Domains (Systems, Biomedicine, Physics, Vision, NLP).
- **Hallucination Prevention:** Verbatim quotes verified via PyMuPDF coordinate containment.
- **Page-Level Ground Truth:** Auto-located via 4-tier lexical engine, outputting to `eval/prepared/page_gold.json`.
