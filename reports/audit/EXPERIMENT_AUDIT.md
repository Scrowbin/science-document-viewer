# Experiment Audit (RQ1–RQ6)

**Date:** 2026-10-29.

"Independently checked" means I read the canonical artifact fields myself or recomputed values from per-record data with separately written code. It does not mean that an existing script returned OK. No expensive experiment was re-run; every headline number could be checked from stored outputs.

---

## RQ1: PDF text extraction

| Item | Finding |
|---|---|
| Question | Which local PDF extractor best preserves text, structure and downstream retrieval for scientific papers? |
| Data | 47 QASPER Dev papers with local PDFs, 127 questions (`eval/prepared/dev_held_out_split.json`) |
| Script / artifact | `backend/scripts/evaluate_rq1_extractors.py` → `eval/results/rq1_extraction_20261024_000639.json` (the other two `rq1_*` files are 2-paper smoke runs) |
| Methods | `pymupdf_plain` (baseline), `pymupdf_layout`, `pypdf`, `pdfminer.six`, `pdfplumber`; GROBID listed but not run (server offline) |
| Metrics | Evidence Coverage (quote present verbatim or ≥ 75% word overlap), Char-Match (matching-block accuracy on the first 5,000 chars), Heading F1, reading order, ms/page, peak RSS, downstream nDCG@10 (paper-cluster bootstrap B = 2,000, seed 42) |
| Independently checked | All engine rows read from the JSON: plain 0.5274 / 10.19 ms; layout 0.5100 / 26.16 ms / Heading F1 48.01%, Δ −0.0175, p = 0.56; pdfplumber 0.3769, p = 0.001. Holm p_adj in the thesis (pdfplumber 0.004) = 4 × 0.001 ✔ |
| Problems | The artifact's automatic ranking selects `pymupdf_plain`, but the thesis claimed layout was "optimal / fastest". Heading F1 is only implemented for `pymupdf_layout`, so the other tools' 0% is an adapter artifact. The thesis named "1-CER" although Char-Match is what is reported |
| Thesis accuracy | **Corrected.** Selection is now justified by heading recovery, not speed or accuracy |

## RQ2: Chunking

| Item | Finding |
|---|---|
| Question | Which of 8 chunking strategies retrieves best under a fixed 1,600-token budget? |
| Data | Same 47 papers / 127 questions; text from `extract_sections_from_pdf` (PyMuPDF) |
| Script / artifact | `backend/scripts/evaluate_rq2_chunking.py` → `eval/results/rq2_chunking_20261024_013443.json` (`_004912` lacks hierarchical arms; `_005810` is a 2-paper run) |
| Settings | All strategies `max_tokens=400, overlap=80`; hierarchical children 200 estimated tokens / overlap 40; τ = 0.50 (sensitivity τ = 0.30); exact cosine with `e5-small-v2` |
| Independently checked | All 8 rows (chunks, tokens, truncation, nDCG@4, Recall@20, MRR@10, Δ, p, τ = 0.30). Holm p_adj (hierarchical 0.007, child 0.012, semantic 0.025) = 7×, 6×, 5× p_raw ✔ |
| Problems | (1) Hierarchical is scored on whole parent sections, so part of its +0.1225 is mechanical (the script header says so). (2) The production-path measurement (`hierarchical_production_parity.json`) gives only nDCG@10 0.5049 vs 0.4743 for `section_overlap`; the thesis quoted wrong latency figures (31.76/31.74 ms; actual 34.10/32.85 ms). The parity run is also dense-only, while production chat is hybrid. (3) τ = 0.30 does reorder the middle strategies. (4) "Truncation" counts estimated tokens > 512, not real subwords. (5) `section_token` is 400, not 250 |
| Thesis accuracy | **Corrected** (all five points) |

## RQ3: Embedding models

| Item | Finding |
|---|---|
| Question | Which open-source (MIT/Apache, ≤ 335M parameter) embedding model gives the best quality–cost balance on a desktop CPU? |
| Data | 207 active papers / 615 questions / 5,207 chunks. In-house split: 48 "Dev" + 159 "held-out". Official QASPER split, **recomputed**: 96 Dev + 111 Train, 0 Test. Text = prepared QASPER sections (no PDF extraction), chunked with `section_overlap` 350/70 |
| Script / artifact | `backend/scripts/run_thesis_embedding_benchmark.py` → `eval/results/thesis_embedding_benchmark.json` |
| Models | 10 dense models + BM25 |
| Independently checked | Model count; corpus composition (from the split files); Holm table recomputed (m = 10) ✔; ModernBERT 0.5872, e5 0.5522 (Δ +0.0497), BGE p = 0.083 |
| Problems | "11 models + BM25" wording (actually 10 + BM25); registry entry had the wrong composition (97 + 110), wrong script path and model list; chunking differs from production (flat vs hierarchical). Pipeline-level selection leakage (the 48 Dev papers also used in RQ1/RQ2) is already disclosed |
| Thesis accuracy | **Corrected**; registry correction appended (`audit_corrections`) |

## RQ4: Hybrid retrieval

| Item | Finding |
|---|---|
| Question | Do hybrid retrieval strategies beat dense-only retrieval with hierarchical chunking? |
| Data | QASPER Dev 276 papers / 892 questions (configuration selection) → frozen → QASPER Test 408 / 1,310 / 14,035 child chunks. Text = QASPER JSON `full_text` (not PDF extraction) |
| Script / artifacts | `eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py` → `rq4_qasper_{dev,test}_hierarchical_benchmark.json` |
| Statistics | Paper-cluster bootstrap B = 2,000, Holm over 3 comparisons vs Dense |
| Independently checked | Every cell of Table 5.5 vs `arms` ✔; Holm: BM25 3 × 0.001 = 0.003, Convex 2 × 0.007 = 0.014, RRF 0.87 ✔ |
| Problems | Thesis claimed `pymupdf_layout` was held fixed (it was not used). Dev runtime 1,230 s has no source (artifact: 24.3 s). BM25 IDF is corpus-wide here but per-document in production (already disclosed). RRF "comparable" to dense was worded as equivalence |
| Thesis accuracy | **Corrected**. Calling Test "held-out" is valid for RQ4 itself: it was unused before RQ4 (confirmed against the registry) |

## RQ5: Local LLM generation and human faithfulness audit

| Item | Finding |
|---|---|
| Question | How do `qwen2.5:0.5b`, `llama3.2:1b` and `llama3.2:3b` compare in answer quality, faithfulness and speed on CPU? |
| Data | 250 unexposed QASPER Train papers / 500 answerable questions (`eval_sample_manifest_500q.json`; overlap check `PASS_UNEXPOSED`). **Context = gold evidence** (`evaluate_rq5_llm_generation.py` L633), so this isolates the generator and is not end-to-end |
| Artifacts | `rq5_llm_generation_benchmark_500q.json`, `rq5_inference_checkpoint.jsonl` (1,500 records, 0 errors) |
| Independently checked (tier 1) | From `detailed_records`: F1 0.2033 / 0.1346 / 0.2324, refusals 243 / 294 / 50, containment 0.379 / 0.293 / 0.603, P50/P95 (harness order statistics), Δ and paper-level t (+6.2597, −2.5028, −8.9651) all reproduce exactly. Post-hoc descriptive: on the 244 questions both 3b and qwen answered, F1 is 0.3797 vs 0.3002 |
| Problems (tier 1) | Thesis said context was "retrieved under a 1,600-token budget" (wrong); quoted the wrong refusal string; reported unmeasured RAM (0–1 memory samples); per-type n varies by model (QASPER max-over-annotators convention) |
| Tier 2: human audit | 60 answers (20 questions × 3 models), one reviewer, model identities hidden, 21 items adjudicated (11 label changes) |
| **Defect found** | The signed sheet (`review_and_signed.md`) lists answers in a different Alpha/Beta/Gamma order than the package and the mapping. `unblind_and_analyze_faithfulness.py` joined on `(review_id, blind_label)`, so 26 of 45 distinguishable answers were credited to the wrong model |
| Correction | `scripts/remap_human_labels_by_answer.py`: exact answer-text match against the checkpoint, plus question and context checks and a one-to-one constraint. Result: 60/60 matched exactly, 45 VALID + 15 identical answers (with identical labels), 0 unresolved |
| Independent validation | (a) A separately written parser of the signed Markdown reproduced the same counts. (b) Corrected refusal labels per model (8 / 10 / 0) equal the automated detector's refusals on the same 20 items; the old attribution was inconsistent (5 vs 8 for 3b). (c) Summaries recomputed with new code (`corrected_human_review_summary.json`) |
| Corrected results | SUPPORTED 10 / 7 / 10; grounded compliance 15 / 11 / 10 of 20; unsupported + contradicted 1 / 3 / 7; unjustified refusals 3 / 6 / 0. Point-biserial r: SUPPORTED–F1 +0.644, SUPPORTED–containment +0.591, unsupported/contradicted–containment −0.043 |
| Interpretation | Exploratory only (n = 20 per model, one reviewer, no significance test). Supports: 3b produces the fewest ungrounded answers but refuses often; qwen answers almost always but more answers are ungrounded; containment does not detect hallucination |
| Preserved | `review_and_signed.md`, all `audit/` files, mapping, old unblinded CSV/JSONL and report (superseded, not edited) |
| Thesis accuracy | **Corrected** (§5.6, §5.7, §5.8, §5.9, Ch6, abstract); `THESIS_RQ5_LLM_REPORT.md` regenerated from §5.6 |

## RQ6: End-to-end combinations

Not executed. There are no artifacts, and `rag_exp/` (now removed) was an unrelated prototype. The thesis now defines RQ6 once, in §3.3.6 (3 embedding models × 3 LLMs, retrieved context), and marks it as future work everywhere (§3.3.6, §3.6.2, §5.1.3, §5.7.3, §6.2, §6.3.1, README).

## Cross-cutting statistical notes

- Bootstrap p-values have a floor around 0.001 (B = 2,000); "p = 0.0010" means "p ≤ 0.001".
- The relevance labels (τ) are noisy: precision is 58% on fresh pairs. This affects all compared methods equally, but caps how much the absolute values can be trusted.
- Non-significant differences (RRF vs dense, flat chunkers, BGE vs MiniLM) are now worded as "no significant difference", not equivalence.
- RQ3's power analysis (38.6% power for SESOI 0.03) is already disclosed; I added nothing more.
