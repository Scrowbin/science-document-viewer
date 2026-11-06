# Evaluation of the RAG pipeline

This is the single methodology and results document of the project. The RAG pipeline is evaluated in **four consecutive phases**; each phase starts from the choices of the previous one. All numbers are descriptive (means over a named dataset, differences between methods, costs); no statistical tests. Each table names its dataset and the file its numbers come from.

The earlier component experiments and the planned 16-configuration combination run were superseded by this design; their document is kept at `archive/eval/README_component_experiments_2026-10.md` and their scripts and results under `archive/eval/phases/`.

---

## 1. The system and its current configuration

```
PDF -> section extraction -> chunking -> embeddings -> retrieval -> context assembly -> local LLM answer
```

| Component | Application setting (`backend/core/settings.py`, `apps/documents/services/`) |
|---|---|
| Extraction | PyMuPDF layout-aware section extraction (`chunking_utils.extract_sections_from_pdf`) |
| Chunking | `hierarchical`: children of 200 estimated tokens, overlap 40; the parent section is the context unit |
| Embedding | `intfloat/e5-small-v2`, prefixes `query: ` / `passage: ` (`rag_service.MODEL_PREFIX_SPECS`) |
| Retrieval | dense (cosine) |
| Context assembly | ranked parents, at most 5 units, 1,600 estimated tokens; parents over 800 tokens cut to ±200 words around the matched child |
| Generation | `llama3.2:3b` via Ollama, temperature 0, `num_ctx` 4096, prompt `rag_service.build_answer_prompt` |

## 2. Data

| Phase | Dataset | Documents | Questions | Text source |
|---|---|---|---|---|
| 1. Extraction | OHR-Bench [1], 7 domains, PDFs with a text layer | 706 | 6,916 | each extractor's output |
| 2. Chunking × embedding | C-RET: QASPER [2] Train | 335 | 567 | QASPER `full_text` (on Kaggle; see note) |
| 2. Chunking × embedding | PEERQA-PDF: PeerQA [3] | 107 | 288 | PyMuPDF extraction of the PDFs |
| 3. Keyword, fusion, reranking | as Phase 2 | 335 / 107 | 567 / 288 | as Phase 2 |
| 4. Generation | C-RET; PeerQA questions with an author answer (`answer_free_form`) | 335 / 107 | 567 / ≤ 181 | gold evidence, or retrieved context |
| Preliminary generation study (CPU) | QASPER Train, disjoint from C-RET | 250 | 500 | gold evidence |

- Cohort files: `phase_0_baseline/artifacts/revalidation/cohort_{C-RET,PEERQA-PDF}.json`.
- **Text source note.** `evaluate_retrieval.py` reads a paper's PDF when it exists locally and otherwise QASPER's `full_text`. The Kaggle runs have no QASPER PDFs, so Phases 2–4 use QASPER's own text (section source `json:train` in the log). Retrieval results therefore exclude extraction errors of the application.
- Methods are chosen and evaluated on the same C-RET papers; results describe these papers and are not an independent test.

## 3. Metrics

| Metric | How it is computed |
|---|---|
| Evidence coverage (Phase 1) | a question counts as covered if ≥ 80% of the gold evidence words appear in the extracted text of the evidence page |
| Text LCS (Phase 1) | word-level longest common subsequence between page text and gold evidence, / evidence length |
| Hit@k (Phase 1) | the evidence page is in the top-k pages of a BM25 search over the document's pages |
| Relevance (Phases 2–3) | a unit is relevant if it contains an evidence passage verbatim or ≥ 50% of its content words (`eval_common.relevance.is_chunk_hit`, τ = 0.50); for `hierarchical` the unit is the parent section |
| nDCG@5/10, MRR@5/10, MAP@10/20, Recall@5/10/20, P@1/5/10, Hit@1/5/10 | over the top 20 units; R_q counted over all units of the paper; questions without any relevant unit are skipped. nDCG@10 is the primary metric |
| Token F1, refusal rate (Phase 4) | word overlap with the best reference answer; refusals score 0 |
| Containment proxy | share of the answer's content words found in the context (lexical, **not** faithfulness) |
| Boolean accuracy | yes/no questions: first yes/no in the answer equals the gold majority |
| Groundedness labels | SUPPORTED, MISSING_INFO - PARTIAL, MISSING_INFO - UNJUSTIFIED_REFUSAL, REFUSAL_VALID, UNSUPPORTED, CONTRADICTED, against the given context (human in the preliminary study; LLM judge in Phase 4) |
| Cost | ms/page; indexing throughput; latency p50/p95 (GPU on Kaggle, not the application's CPU) |

Cautions: Token F1 is not factual correctness; the containment proxy is not semantic faithfulness; hierarchical units (whole sections) are larger than flat chunks, so retrieval metrics across chunkers are not fully like-for-like.

---

## 4. Phase 1: PDF extraction (OHR-Bench)

Script `phases/phase_1_extraction/scripts/evaluate_extraction_ohr.py`; results `phases/phase_1_extraction/artifacts/{summary.json,per_query.jsonl,REPORT.md}`. Committed run: domain `all`, 1,261 documents, 555 excluded (no text layer, or GROBID returned no text), 706 scored, 6,916 questions. `pymupdf_layout` here is a block-sorting extractor inside the script, not the application's `extract_sections_from_pdf` (which also detects headings).

| Extractor | Evidence coverage | LCS % | Hit@1 | Hit@5 | ms/page |
|---|---|---|---|---|---|
| pymupdf_layout | **0.747** | 76.2 | **0.733** | **0.921** | 2.55 |
| pymupdf_plain | **0.747** | **77.0** | **0.733** | **0.921** | **2.25** |
| pypdf | 0.726 | 75.1 | 0.718 | 0.913 | 32.0 |
| pdfminer.six | 0.717 | 72.5 | 0.715 | 0.909 | 53.6 |
| pdfplumber | 0.705 | 73.9 | 0.711 | 0.907 | 88.9 |
| grobid | 0.494 | 54.3 | 0.577 | 0.775 | 143.3 |

Academic documents only (77 documents, 1,152 questions; computed from `per_query.jsonl`): evidence coverage PyMuPDF 0.629, pypdf 0.610, pdfminer.six 0.612, pdfplumber 0.490, GROBID 0.391.

- **Theory vs result.** Text-layer libraries were expected to be close; they are (0.705–0.747), PyMuPDF best and fastest. GROBID was expected to do well on scholarly PDFs; it is lowest even on the academic subset. The largest gaps are tables (LCS 84.9 vs 48.2) and formulas (74.6 vs 52.8): GROBID keeps the structured body text and drops or separates much non-body content, where OHR-Bench places many questions. This explanation fits how GROBID outputs text but was not tested separately.
- Layout and plain PyMuPDF have identical coverage and Hit@k because both metrics use word sets/bags; reading order shows only in LCS.
- **Choice:** keep PyMuPDF Layout (`extract_sections_from_pdf`) in the application: best coverage, fastest, and it supplies the headings hierarchical chunking needs; GROBID needs a separate Java service and scored lower.

## 5. Phase 2: chunking × embedding

Script `phases/phase_2_retrieval/scripts/evaluate_retrieval.py` (Kaggle notebook `retrieval-benchmark-full`; log `phases/phase_2_retrieval/artifacts/kaggle_full_run.log`). 3 chunkers (`hierarchical` 200/40 → parents; `section_overlap` 400/80; `fixed_size` 400) × 5 embedders (e5-small-v2, snowflake-arctic-embed-s, modernbert-embed-base, embeddinggemma-300m, Qwen3-Embedding-0.6B), dense retrieval.

C-RET, 566 questions with a relevant unit (source: the run log; replace with `artifacts/c_ret/summary.json` once downloaded):

| nDCG@10 | e5 | arctic | modernbert | gemma* | qwen |
|---|---|---|---|---|---|
| hierarchical | 0.703 | 0.711 | 0.713 | 0.719 | **0.721** |
| fixed_size | 0.620 | 0.637 | 0.637 | 0.689 | 0.662 |
| section_overlap | 0.585 | 0.577 | 0.592 | 0.627 | 0.586 |

\* gemma ran with an empty document prompt; the model card uses `title: none | text: ` (fixed in `rag_service.MODEL_PREFIX_SPECS`; rerun pending).

- **PeerQA: pending.** The first full run found PDFs for only 8/107 papers (26 questions). The loader now searches `eval/pdfs/peerqa` recursively and prints the coverage; rerun with `eval/kaggle/phase2_peerqa_gemma_rerun.ipynb`.
- **Theory vs result.**
  - Hierarchical (small-to-big) is best for every embedder (+0.03 to +0.08 over the best flat chunker), as expected; part of the gain comes from the larger scored unit.
  - Section-aware chunking does **not** beat fixed size, unlike the expectation; short sections give small chunks with little context (plausible, not tested).
  - With hierarchical chunking the embedders are within 0.018 (vs 0.069 with fixed size): chunking matters more than the embedder.
  - Larger models are slightly better at much higher cost: on the Kaggle GPU the hierarchical combination took about 1,650 s for Qwen3 vs about 120 s for e5 (from the log; includes indexing all units).
- **Choice for Phase 3:** hierarchical; embedders e5 (application default, cheapest), qwen (best), gemma (near-best, best on flat chunks), modernbert (long context).

## 6. Phase 3: keyword retrieval, fusion and reranking

Script `phases/phase_3_hybrid_reranking/scripts/evaluate_hybrid_reranking.py`; notebook `eval/kaggle/phase3_hybrid_reranking.ipynb`. Imports the Phase 2 functions, so data, units, relevance and metrics are identical (checked: its `dense` arm reproduces Phase 2 exactly on a smoke run).

- Per embedder (e5, qwen, gemma, modernbert), hierarchical chunking:
  - `dense`;
  - `rrf`: dense + BM25, top-50 of each list, k = 60;
  - `convex`: 0.7 · minmax(dense) + 0.3 · minmax(BM25) over all children;
  - `dense+minilm`, `dense+bgem3`, `convex+minilm`, `convex+bgem3`: cross-encoder rescoring of the top 30 children (`cross-encoder/ms-marco-MiniLM-L6-v2`, `BAAI/bge-reranker-v2-m3`, max_length 512).
- Plus `bm25` alone (regex tokenizer with stopwords). 29 arms; C-RET and PEERQA-PDF.
- Outputs `artifacts/<cohort>/{per_query.jsonl,summary.json,REPORT.md}`: means on the common question set, top-10 parent ids per arm, fusion latency, reranker latency (only from calls that scored all 30 pairs; cached reranker scores are reused across embedders). Resumable.
- **Expectations:** BM25 alone below dense on QASPER (questions share few words with the evidence) but closer on PeerQA; fusion at least as good as the better input, most useful for weaker embedders; rerankers improve the top ranks at a large latency cost (especially bge-reranker-v2-m3).
- **Results: pending.** The arm with the best nDCG@10 on both datasets, weighed against CPU latency, becomes the `--pipeline` of Phase 4.

## 7. Phase 4: answer generation

Script `phases/phase_4_generation/scripts/evaluate_llm_generation.py`; notebook `eval/kaggle/phase4_llm_generation.ipynb` (installs Ollama on the GPU).

- **Models:** llama3.2:3b (application), qwen2.5:1.5b, phi4-mini, qwen3:4b (`think: false`), gemma3:4b. Prompt `rag_service.build_answer_prompt`; temperature 0, `num_ctx` 4096, `num_predict` 256, seed 42.
- **Conditions:**
  - `gold`: the evidence passages;
  - `retrieved --pipeline <embedder:arm>`: context assembled exactly as the application does (≤ 5 parents, 1,600 tokens), cached to `retrieved_contexts_<pipeline>.jsonl`.
  - No similarity gate (the 0.80 cutoff is calibrated for e5 only). The gold − retrieved gap is the loss due to retrieval.
- **Questions:** C-RET references are rebuilt from QASPER JSON with `is_atomic_eligible` (all 567 have one); PeerQA uses `answer_free_form`.
- **Metrics:** Token F1 (refusals 0), refusal rate, containment proxy, boolean accuracy, latency and tokens/s, per answer type.
- **LLM-as-judge:** Gemini (`gemini-2.5-flash` by default, `--judge-model` to change) through the Gemini API, key in the environment variable `GEMINI_API` (read from `.env` at the repo root or `backend/`, or a Kaggle secret). JSON output with one of the 6 labels, judged only against the given context; retries with backoff on rate limits. Used only for evaluation (public papers), never by the application. Any non-`gemini` model name runs through Ollama instead.
  - `--judge-validate` first runs it on the **100 human-labelled answers** of the preliminary study (round 1: 60, round 2: 40, final labels) and reports agreement and Cohen's kappa on 6 labels and on 3 classes (grounded / not grounded / refusal).
  - Judge labels are reported only together with this agreement.
- **Status:** smoke-tested locally (gold and retrieved conditions, judge validation and judge pass); full runs pending.

### 7.1 Preliminary study (CPU, gold evidence)

`phases/phase_9_generation/` (500 questions, 250 papers, local CPU): qwen2.5:1.5b Token F1 0.240 (refusals 29%), phi4-mini 0.233 (50%), qwen2.5:0.5b 0.232 (10%), llama3.2:3b 0.203 (49%), llama3.2:1b 0.135 (59%).

Human check (20 questions × 5 models, one reviewer; round 2 aligned with round 1 on 7 labels): unsupported or contradicted answers were llama3.2:3b 1/20, phi4-mini 2/20, llama3.2:1b 3/20, qwen2.5:1.5b 5/20, qwen2.5:0.5b 7/20.

CPU cost with retrieved contexts of 1,300–1,600 tokens: llama3.2:3b about 32 s per answer, qwen2.5:1.5b about 14 s.

---

## 8. Running on Kaggle and bringing results back

1. In Kaggle, add the HF token as a secret named `HF_TOKEN` (Add-ons → Secrets). Never paste tokens into notebooks.
2. Attach the datasets `kristiko/qasper-official` and `kristiko/peerqa`; the notebooks copy them to `eval/data/qasper_official` and `eval/pdfs/peerqa`.
3. Run the notebook (`eval/kaggle/*.ipynb`): smoke cell first, then the full run. Scripts resume after a timeout.
4. Download the zip from the Output tab and unzip it into the repository at the same path (`eval/phases/<phase>/artifacts/`).
5. Regenerate figures with `backend/venv/Scripts/python.exe eval/scripts/make_thesis_figures.py`, then fill the **[Chờ kết quả]** places in the thesis (Chapter 5).

Local smoke tests (CPU, needs `backend/.env` with `DEBUG=True` or a `SECRET_KEY`):

```powershell
backend/venv/Scripts/python.exe eval/phases/phase_3_hybrid_reranking/scripts/evaluate_hybrid_reranking.py --cohort C-RET --embedders e5 --rerankers minilm --limit 2
backend/venv/Scripts/python.exe eval/phases/phase_4_generation/scripts/evaluate_llm_generation.py --cohort C-RET --condition gold --models llama3.2:3b --limit 2
```

## 9. Limitations

- Methods are chosen and evaluated on the same C-RET papers; QASPER is NLP/ML only; PeerQA is a small check on a different question style.
- Phase 1 uses a different, multi-domain dataset; its conclusion was checked on the academic subset.
- Phases 2–4 use QASPER's own text, so extraction errors of the application are not included.
- Automatic metrics are lexical; the LLM judge is validated on only 100 answers from one reviewer.
- Phases 2–4 latencies are measured on a Kaggle GPU, not on the application's CPU.

## 10. References and models

[1] Zhang, J. et al. (2025). OCR hinders RAG (OHR-Bench). arXiv:2412.02592.
[2] Dasigi, P. et al. (2021). A dataset of information-seeking questions and answers anchored in research papers (QASPER). NAACL.
[3] Baumgärtner, T., Briscoe, T., & Gurevych, I. (2025). PeerQA. NAACL.

Models: `intfloat/e5-small-v2`, `Snowflake/snowflake-arctic-embed-s`, `nomic-ai/modernbert-embed-base`, `google/embeddinggemma-300m`, `Qwen/Qwen3-Embedding-0.6B`; rerankers `cross-encoder/ms-marco-MiniLM-L6-v2`, `BAAI/bge-reranker-v2-m3`; LLMs via Ollama `llama3.2:3b`, `qwen2.5:1.5b`, `phi4-mini`, `qwen3:4b`, `gemma3:4b`, judge `gemini-2.5-flash` (Gemini API). Prefixes and instructions per model are in `rag_service.MODEL_PREFIX_SPECS`.
