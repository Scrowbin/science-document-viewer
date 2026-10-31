# Thesis Claim Audit

**Scope:** `DU_AN_CNTT_TOAN_VAN.md` (primary), `reports/chapter5/CHAPTER5.md`, `eval/results/THESIS_RQ5_LLM_REPORT.md`, README / ARCHITECTURE / SETUP.
**Date:** 2026-10-29. Line numbers refer to the thesis before this audit (approximate).

**Statuses:**
- `VERIFIED`: claim matches code or artifact.
- `THESIS OUTDATED`: the thesis lagged behind the implementation.
- `IMPLEMENTATION CONFLICT`: the thesis contradicted the code or experiment.
- `UNVERIFIED`: no evidence.
- `NEEDS DECISION`: left for the author.

**Resolution column:** what was changed. "Kept" means no change was needed.

## 1. System / implementation claims

| # | Thesis claim (before) | What the code does (evidence) | Status | Resolution |
|---|---|---|---|---|
| S1 | Production pipeline: PyMuPDF layout extraction → hierarchical Small-to-Big → `e5-small-v2` → hybrid BM25 + cosine, RRF k=60 → refusal 0.80 → `llama3.2:3b` | `core/settings.py` (`CHUNKING_STRATEGY="hierarchical"`, `EMBEDDING_MODEL`, `RAG_MIN_SIMILARITY_SCORE=0.80`, `OLLAMA_MODEL`); `rag_service.DocumentRAG.hybrid_search` | VERIFIED | Kept; details added (top-50 dense + top-50 BM25, top-5 parents, ±200-word window for parents > 800 tokens) |
| S2 | Embedding runtime is "FastEmbed ONNX" (architecture diagram) | SentenceTransformers for e5; FastEmbed only for non-e5 models (`rag_service.py` ~L163–181) | IMPLEMENTATION CONFLICT (documentation error) | Corrected to SentenceTransformers |
| S3 | Child chunk "~150 tokens" (Ch4, Ch5, App. B/E) vs "~150 words" vs "~200 tokens" | `chunk_hierarchical(child_max_tokens=200, child_overlap=40)`; tokens = words × 1.33, so 200 tokens ≈ 150 words | THESIS OUTDATED (inconsistent) | Unified: "~200 estimated tokens ≈ 150 words, overlap 40" |
| S4 | `section_overlap` labelled "(Hệ thống)" / production in Table 5.2, §5.3, Table 5.8, conclusions | Production uses `hierarchical`; `section_overlap` remains only the `/chunks/` inspector default | THESIS OUTDATED | Relabelled as early flat configuration; `hierarchical` marked as production |
| S5 | Refusal threshold 0.80 "eliminates hallucination" / "tuyệt đối" | Compares max dense cosine of the top-5 contexts with 0.80; BM25-only hits score 0. The only evidence is a few manual off-topic probes (0.748–0.763) in `docs/thesis_alignment_decisions.md` | UNVERIFIED (overclaim) | Reworded as "hạn chế"; disclosed that it was never calibrated systematically |
| S6 | Upload auto-queries arXiv/Crossref; FR-04 resolves DOI, arXiv ID and ISBN | Upload uses the local heuristic parser only (GROBID off; arXiv/Crossref enrichment commented out in `pdf_metadata_service.py`). Crossref + OpenAlex only via the "Add from DOI" UI; no arXiv/ISBN UI | IMPLEMENTATION CONFLICT (documentation error) | FR-04, §4.7.2, §6.1.1 and the abstract corrected |
| S7 | Fallback `_query_fallback()` | No such function; fallback is inline in `query_document()` (first 250 characters of the top-3 contexts) | IMPLEMENTATION CONFLICT (documentation) | Corrected in NFR-05 and Fig. 4.5 |
| S8 | Chat checks `rag_status == INDEXED` | `chat` does not check `rag_status`; `get_or_create_rag` rebuilds if needed | IMPLEMENTATION CONFLICT (documentation) | Diagram corrected |
| S9 | 5 highlight colours (§4.7.3) vs 4 colours (§1.2.2) | `HIGHLIGHT_COLORS` has 4 entries | THESIS OUTDATED | Corrected to 4 |
| S10 | 8 NFRs (front matter, §1.2.2) vs 6 NFRs (Table 4.2) | Table 4.2 lists NFR-01..06 | THESIS OUTDATED | Unified to 6 |
| S11 | 42 automated tests | 42 before audit; 51 after the regression tests added in this audit | VERIFIED → updated | Updated to 51 |
| S12 | Sharing permissions VIEW/COMMENT/EDIT "completed and tested" | Before: every custom POST action (chat, summarize, annotations) was denied to shared users; notes and related links did not check document access | IMPLEMENTATION CONFLICT (code bug) | Code fixed with 9 regression tests; thesis §4.9 now describes the actual permission matrix and the missing sharing UI |
| S13 | AI panel answers come from the backend | `ragApi.ts` returned hard-coded "Attention Is All You Need" answers on any error | IMPLEMENTATION CONFLICT (code bug) | Fake answers removed; error message shown; §4.9 limitation added |
| S14 | Summarize uses key sections | Uses 5 evenly spaced child chunks (`summarize_document`) | THESIS OUTDATED (omitted) | Described in §4.7.4 |
| S15 | `AiChatPanel` path `components/PdfViewer/AiChatPanel.tsx` | `components/AiChatPanel/AiChatPanel.tsx` | THESIS OUTDATED | Path fixed |
| S16 | Qdrant parents hold "400–1,500 words"; HNSW "≈0.02 ms" | Local mode does exact search (no HNSW); EDA mean section 258.5 words; 0.02 ms has no source | UNVERIFIED | Removed or replaced with verified values |

## 2. Research / experiment claims

| # | Thesis claim (before) | Evidence | Status | Resolution |
|---|---|---|---|---|
| R1 | RQ1: `pymupdf_layout` is "optimal", "fastest" (26.16 ms/page) | `rq1_extraction_20261024_000639.json`: plain 0.5274 / 10.19 ms vs layout 0.5100 / 26.16 ms (Δ −0.0175, p = 0.56); artifact `champion_selected` = plain; layout is the only extractor with Heading F1 > 0 | IMPLEMENTATION CONFLICT (overclaim) | Selection now justified by heading recovery; speed claim corrected; automatic ranking disclosed |
| R2 | RQ1 metric "1-CER" | Script reports Char-Match (matching-block character accuracy, first 5,000 chars) and Evidence Coverage | THESIS OUTDATED | §3.3.1 and §3.4 metric definitions corrected |
| R3 | RQ2 `section_token` = 250 tokens | All RQ2 strategies run with `max_tokens=400, overlap=80` (`evaluate_rq2_chunking.py` L343) | IMPLEMENTATION CONFLICT (documentation) | Corrected to 400 |
| R4 | RQ2 hierarchical 0.6880 is a clean ranking win | Script header states that the hierarchical advantage is partly mechanical (scored on whole parent sections; Recall@20 ceiling at ~13 sections/paper) | THESIS OUTDATED (missing caveat) | Caveat added to §5.3.1, §5.3.3, abstract, Ch6 |
| R5 | Production parity "P50 31.76 vs 31.74 ms", nDCG@4 0.5139 | `hierarchical_production_parity.json`: P50 34.10 vs 32.85 ms; nDCG@10 0.5049 vs 0.4743 | IMPLEMENTATION CONFLICT (wrong numbers) | Numbers corrected; gap vs 0.6880 explained and flagged as not fully decomposed |
| R6 | τ = 0.30 sensitivity: ranking "fully preserved" | Table 5.2 itself shows `fixed_size`/`section` swap and `section_overlap` 4th → 6th | IMPLEMENTATION CONFLICT (misreading) | Reworded: top and bottom stable, middle not |
| R7 | `section_overlap` is the best flat strategy | Highest nDCG@4 / MRR@10 among flat strategies, but below `fixed_size` on primary nDCG@10 (0.5409 vs 0.5654, n.s.) | THESIS OUTDATED (cherry-picked) | Reworded: flat strategies are statistically indistinguishable |
| R8 | "Truncation 0.63%" attributed to hierarchical (§5.7.2) | 0.63% = `section_overlap`; hierarchical 0.00% | IMPLEMENTATION CONFLICT (typo) | Fixed |
| R9 | `section` truncation because sections are "800–2,500 words" | EDA: mean 258.5, P95 706 words; truncation counts estimated tokens (> 512) | IMPLEMENTATION CONFLICT | Corrected; marked as estimated tokens |
| R10 | Relevance threshold τ* = 0.55 "validated out-of-sample on 114 pairs" (82.46% / 81.08% / 75.00%) | `containment_validation_metrics.json`: those are combined n = 114 figures (incl. the 80 calibration pairs). Fresh n = 34: Acc 76.47%, Prec 58.33%, F1 63.64% | IMPLEMENTATION CONFLICT (statistical) | Corrected in §3.5, §5.3.1, §5.8; label noise disclosed |
| R11 | RQ3 "11 models + BM25" | `thesis_embedding_benchmark.json`: 10 dense + BM25 = 11 rows | THESIS OUTDATED | Corrected throughout |
| R12 | RQ3 corpus "96 Dev + 111 Train" vs "48 Dev + 159 Held-out" | Both true: in-house split names vs official QASPER splits (recomputed from split files: 96 Dev + 111 Train, 0 Test). Registry said 97 + 110 (wrong) | VERIFIED (clarified) | Both views explained; registry correction appended |
| R13 | RQ3 / RQ4 use the `pymupdf_layout` extractor | RQ3 uses prepared QASPER sections (`qasper_corpus.json`); RQ4 uses QASPER JSON `full_text`. Neither parses PDFs. RQ3 chunks with `section_overlap` 350/70, not hierarchical | IMPLEMENTATION CONFLICT (documentation) | §3.3.4, §5.4.1, §5.5.3, Table 5.0 and App. E corrected; limitation added in Ch6 |
| R14 | RQ3 Holm table | Recomputed by hand (m = 10); all p_adj match | VERIFIED | Kept |
| R15 | RQ4 Table 5.5 (all cells), Holm over 3 comparisons | `rq4_qasper_test_hierarchical_benchmark.json` | VERIFIED | Kept; "held-out" wording kept for RQ4 (Test was unused before RQ4) |
| R16 | RQ4 Dev runtime 1,230.45 s | Artifact: 24.32 s (cached-embedding rerun); no source for 1,230.45 | UNVERIFIED | Replaced with the artifact value |
| R17 | RQ5 context = retrieved context under a 1,600-token budget | `evaluate_rq5_llm_generation.py` L633: gold evidence joined | IMPLEMENTATION CONFLICT (documentation) | Corrected in §3.3.5, §5.6.1, §5.7.2, §5.8 |
| R18 | RQ5 automated numbers (F1, refusals, containment, Δ, t, p_adj) | Recomputed from `detailed_records` (500 per model) | VERIFIED | Kept |
| R19 | RQ5 refusal string "I could not find this information…" | Detector uses "The document does not contain sufficient…"; 13 paraphrased refusals missed | IMPLEMENTATION CONFLICT (documentation) | Corrected; limitation stated |
| R20 | RQ5 RAM "~2.5 GB / ~1.6 GB / ~0.6 GB", "never exceeded 2.5 GB" | `memory.samples_count` = 0 (3b), 1 (others, 41 MB) | UNVERIFIED | Removed; marked as unmeasured |
| R21 | RQ5 per-type n = 319 / 110 / 71 for all models | Type = best-matching reference type (QASPER evaluator convention); varies by model for 2 questions; manifest gives 319 / 109 / 72 | VERIFIED (clarified) | Footnote added |
| R22 | Human audit "double-blind" | Single reviewer; model identity hidden | IMPLEMENTATION CONFLICT | Corrected everywhere |
| R23 | Human audit: 3b 70% grounded / 15% hallucination / 5% unjustified refusal; qwen 25% hallucination; r = 0.4168 / 0.3125 / 0.0868 / −0.0897; Table 5.7b | **Attribution bug**: labels were joined to models by blind label although the signed sheet ordered answers differently. Corrected by exact answer matching (60/60): 3b 75% / 5% / 15%; 1b 55% / 15% / 30%; qwen 50% / 35% / 0%; r = +0.644 / +0.591 / +0.260 / −0.043 | IMPLEMENTATION CONFLICT (analysis bug) | All per-model figures replaced; method disclosed in §5.6.1 and §5.8; originals kept |
| R24 | RQ5 conclusion: 3b "optimal on all dimensions" | 3b > 1b (significant); qwen > 3b in F1 (significant, below SESOI); 3b fewest unsupported answers in the audit | THESIS OUTDATED (overclaim) | Conclusion rewritten as an explicit trade-off |
| R25 | RQ6 described twice (3×3 in §3.3.6; 2×2 + "4 configurations from Ch3" in §6.3.1) | Not executed; the "4 configurations" do not exist in Ch3 | NEEDS DECISION → decided by user | Kept §3.3.6 design; §6.3.1 rewritten; "not executed" added everywhere |
| R26 | Ch5 "limited to RQ1–RQ3; RQ4/RQ5 future work" (§5.1.3, §3.6) | RQ4 and RQ5 have been executed | THESIS OUTDATED | Scope statements and Table 5.0 (RQ4/RQ5 rows) updated |
| R27 | BGE-small non-significance "after Holm" | p_raw = 0.083 is already non-significant before correction | THESIS OUTDATED (imprecise) | Reworded |

## 3. Mechanical / formatting defects (master thesis)

| Defect | Count | Fix |
|---|---|---|
| `$p_$p_$p_{…}` | 4 | → `$p_{…}` |
| `$B$B$B=` / `$B$B=` | 5 / 10 | → `$B=` |
| `aall-` / `aaall-MiniLM` | 10 | → `all-MiniLM` |
| `$$$\tau^*…$$$`, inline `$$…$$` | 1 / 10 | → inline `$…$` |
| Literal TAB eating `\t` in `\text` | 1 | restored |
| Double-escaped LaTeX (`\\Delta`, `\\text`) in Ch6 | 14 | collapsed |
| Missing `$p_` (`({\text{raw}}…`, `{\text{adj}}…$$`) | 2 | rewritten |
| Broken Appendix E table / `$\$\tau` | 3 lines / 2 | repaired |
| Blank lines between table rows (Tables 5.0–5.3, both files) | 23 | removed |
| Absolute `file:///c:/DACNTT/…` links | 20 (+12 in TRACEABILITY_MAP) | made relative |
| GitHub-only `> [!IMPORTANT]` | 1 | plain blockquote |
| Duplicate bullet (§1.2.2), orphan "Hình 3.1" in figure list | 1 / 1 | removed |

Every pattern was previewed with match counts before replacement. Gate: after repair, master Chapter 5 matched the independently clean `CHAPTER5.md` line for line (991 = 991 lines, 0 differences) before the content corrections were applied.
