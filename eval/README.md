# Evaluation of the RAG pipeline

This document explains how each part of the RAG pipeline was evaluated, what the results show, why methods were selected, and how the final 16-configuration combination experiment is built. It is the single methodology and results document for the project.

All numbers are descriptive: mean scores over the questions of a named dataset, differences between methods, and computational costs. Each table states its dataset and setup and links the file the numbers come from. Results from different datasets or setups are kept in separate tables and are not compared directly.

---

## 1. What the system does

The Scientific Document Manager is a Zotero-style reference manager. For a PDF in the library, the assistant answers questions and writes summaries grounded in that document:

```
PDF -> section extraction -> chunking -> embeddings -> retrieval -> context assembly -> local LLM answer
```

Everything runs locally on a CPU-only desktop: Django backend, embedded Qdrant, Ollama.

## 2. Pipeline components and the baseline

Each component experiment changes one component and keeps the others at the **baseline**: the production setting of the application. Values were read from `backend/core/settings.py` and `backend/apps/documents/services/`.

| Component | Baseline (production setting) |
|---|---|
| Extraction | PyMuPDF layout-aware section extraction (`chunking_utils.extract_sections_from_pdf`) |
| Chunking | `CHUNKING_STRATEGY='hierarchical'`: child chunks of 200 estimated tokens with 40 overlap; the parent section is the context unit (`chunkers.chunk_hierarchical`) |
| Embedding | `EMBEDDING_MODEL='intfloat/e5-small-v2'` with prefixes `query: ` / `passage: ` (`rag_service.MODEL_PREFIX_SPECS`) |
| Retrieval | `RAG_RETRIEVAL_MODE='dense'` (cosine); `rrf_legacy` (dense + BM25 with RRF) is selectable |
| Context assembly | ranked parents in order, at most 5 units, 1,600 estimated tokens (words × 1.33); parents over 800 tokens cut to ±200 words around the matched child |
| Refusal gate | refuse without calling the LLM if the best dense cosine in the context is below `RAG_MIN_SIMILARITY_SCORE=0.80` |
| Generation | `OLLAMA_MODEL='llama3.2:3b'`, `OLLAMA_TEMPERATURE=0`, `OLLAMA_NUM_CTX=4096`, prompt `rag_service.build_answer_prompt` |

This table is the reference configuration for the component experiments. It does not claim that every historical experiment used exactly this baseline; any deviation is stated with the results it affects.

## 3. Data used

QASPER [1] contains NLP/ML papers with questions written by readers who saw only the title and abstract, and answers with evidence paragraphs written by other readers. PeerQA [2] (peer-review questions on papers from other venues) is used only as a cross-domain check of retrieval.

| Experiment | Dataset | Papers | Questions | Notes |
|---|---|---|---|---|
| Extraction: evidence recall | QASPER component set | 335 | (scored per paper) | QASPER Train papers with a downloaded PDF; evidence of all questions of the paper |
| Extraction: effect on retrieval | QASPER 150-paper subset | 150 | 249 | subset of the component set |
| Extraction: cross-domain | PeerQA (PDF) | 107 | (per paper) | |
| Chunking (and its extensions) | QASPER component set | 335 | 567 | |
| Embedding (and SPECTER2) | QASPER 150-paper subset | 150 | 249 | |
| Retrieval strategy, reranking | QASPER component set | 335 | 567 | |
| Retrieval: cross-domain | PeerQA PDF / PeerQA text | 107 / 73 | 288 / 148 | |
| Generation | QASPER generation set | 250 | 500 | **gold evidence given as context**, not retrieved context |
| Generation: human check | from the generation set | 20 | 20 × 3 models = 60 answers | single reviewer |
| Earlier combination grid (background) | QASPER 150-paper subset | 150 | 249 | 2 extractors × 3 chunkers × 5 embedders × 4 retrieval modes |
| **Combination (16 configurations)** | QASPER combination set | 1,142 | 3,122 | all splits; see Section 7.2 |

The paper and question ID lists are in `eval/phases/phase_0_baseline/artifacts/revalidation/` (component sets: `cohort_*.json`) and `eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json` (generation set). The counts above were taken from each experiment's `per_query.jsonl`.

The component sets were drawn from QASPER Train papers that earlier experiments had not used. The same papers were then used both to compare methods and to choose them. The results therefore describe these papers; they are not an independent test of how the chosen methods generalise.

## 4. Metrics

| Metric | What it measures |
|---|---|
| **Evidence recall** (extraction) | Share of a paper's gold evidence paragraphs found in the extracted text: verbatim, or with ≥ 80% of the paragraph's content words present |
| **nDCG@10** (retrieval, primary) | Ranking quality of the assembled context: units that contain ≥ 50% of an evidence paragraph's content words count as relevant, and higher positions weigh more [3] |
| **MRR@10** | 1 / rank of the first relevant unit |
| **CEC@0.5** (context evidence coverage) | 1 if the assembled context (what the LLM receives) covers ≥ 50% of the content words of at least one evidence paragraph, else 0 |
| **Token F1** (generation) | Word overlap between the answer and the best-matching reference answer (SQuAD/QASPER style); refusals score 0 |
| **Refusal rate** | Share of answers that refuse ("The document does not contain sufficient relevant information…") |
| **Containment proxy** | Share of the answer's content words that appear in the context. A lexical proxy, **not** semantic faithfulness |
| **Human faithfulness labels** | SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED, REFUSAL_VALID, UNJUSTIFIED_REFUSAL, judged against the context |
| **Cost** | Latency (P50/P95), indexing throughput (chunks/s), peak memory (working set) |

Two cautions:
- **Token F1 is not factual correctness.** It rewards word overlap.
- **nDCG across chunkers is not fully like-for-like.** For hierarchical chunking relevance is judged on whole parent sections, which are larger than flat chunks and therefore more likely to contain evidence. CEC is the fairer comparison across chunkers.

---

## 5. Component experiments

### 5.1 Document extraction

**Methods.**
- `pymupdf_layout`: PyMuPDF with layout sorting and heading detection (production).
- `pymupdf_plain`, `pypdf`, `pdfminer.six`, `pdfplumber`.
- GROBID: a separate run, using a local Docker service.

**Theory.** Layout-aware extraction keeps reading order and section headings, which section-based chunking needs. Plain text extractors recover the words but lose structure.

**Results.** Evidence recall is measured on the component set (335 papers). Retrieval quality is measured on the 150-paper subset, with hierarchical + e5 + dense.

| Extractor | Evidence recall | Heading F1 | ms/page (P50) | nDCG@10 | CEC@0.5 |
|---|---|---|---|---|---|
| pymupdf_layout | 0.985 | 0.466 | 12.3 | **0.454** | **0.739** |
| pymupdf_plain | 0.985 | 0 | 7.2 | 0.421 | 0.699 |
| pypdf | 0.982 | 0 | 48.2 | 0.396 | 0.659 |
| pdfminer.six | 0.985 | 0 | 94.4 | 0.414 | 0.687 |
| pdfplumber | 0.558 | 0 | 185.1 | 0.379 | 0.651 |
| GROBID (separate run) | 0.981 | 0.576 | 185.4* | 0.513 | 0.823 |

\* GROBID time is an HTTP round trip to a Docker container, not comparable with in-process extraction. The container reached its 4 GB memory limit.

Sources: `phase_1_extraction/artifacts/extraction/summary.json` and `.../extraction_grobid/summary.json`. The paths are relative to `eval/phases/`, here and below.

**Observation.**
- **As theory predicts,** recovering the words is not the difference. Four extractors find 98–99% of the evidence, but only layout-aware extraction gives section structure. With it, retrieval is better (0.454 vs 0.421 for plain PyMuPDF on the same text).
- **pdfplumber's low recall comes from configuration.** On the two lowest-scoring papers its output glues words together (e.g. `recurrentneuralnetworkarchitectures`) in both layout and plain mode. The cause is its default character-spacing settings, not the method itself, so the result applies only to "pdfplumber with default settings".
- **On PeerQA** (107 papers), PyMuPDF Layout recovers less evidence (0.933) than plain extractors (about 0.98). Its layout handling suits arXiv-style papers better than the other formats.
- **GROBID** recovers the same evidence but gives better retrieval. Possible explanations, **not yet tested**:
  - the evaluation's verbatim-match shortcut may favour text produced the same way as QASPER's own text, which comes from a GROBID-based pipeline;
  - GROBID's text contains no reference list (0 of 349 papers, against 304 of 349 for PyMuPDF Layout), so there are fewer distractor chunks.

  A small diagnostic was designed (switch off exact matching; remove references from the PyMuPDF text) but is kept optional.

**Decision.** PyMuPDF Layout is used for the combination experiment. This is a practical scope decision, not a claim that it is the best extractor. GROBID can run locally, but it needs a separate Java service with about 4 GB of memory plus integration and maintenance work, which is out of proportion for this project.

### 5.2 Text chunking

**Methods.**
- `hierarchical` (production): 200-token children for matching, the parent section as context.
- `fixed_size`: 400 tokens.
- `section_overlap`: 400 tokens with 80 overlap inside sections.
- Separate extensions: semantic chunking (two variants, from a teammate's implementation); children only, i.e. hierarchical without parent expansion; and a "fill" context assembly that skips a parent that does not fit instead of stopping.

**Theory.**
- **Small-to-big retrieval:** small units match questions precisely, and larger parents give the LLM enough surrounding text.
- **Semantic chunking:** boundaries at topic shifts should keep ideas together.

**Results.** Component set, 335 papers / 567 questions; e5 embeddings, 1,600-token budget, at most 5 units.

| Chunker | nDCG@10 | CEC@0.5 | Context tokens | Units in context |
|---|---|---|---|---|
| hierarchical | **0.445** | 0.732 | 1,318 | 3.4 |
| fixed_size | 0.386 | **0.758** | 1,579 | 4.0 |
| section_overlap | 0.384 | 0.743 | 1,244 | 4.9 |
| semantic_v1 (extension) | 0.358 | 0.711 | 1,098 | 4.9 |
| semantic_v2 (extension) | 0.353 | 0.690 | 834 | 5.0 |
| children only (extension) | 0.355 | 0.677 | 866 | 5.0 |
| hierarchical + fill assembly (check) | 0.458 | 0.769 | 1,469 | 4.7 |

Sources: `phase_2_chunking/artifacts/chunking/`, `chunking_semantic/`, `chunking_children/`, `assembly_fill_check/` (each `summary.json`).

**Observation.**
- **Small-to-big theory holds.** Hierarchical has the best ranking, and removing parent expansion (children only) loses most of the benefit (CEC 0.732 → 0.677).
- **Fixed-size has the highest CEC,** but it also puts about 260 more tokens into the context, so more evidence fits partly because more text fits.
- **Semantic chunking did worse than theory suggests, partly for a structural reason.** Its chunks are small, so the 5-unit cap is reached with only 830–1,100 tokens and part of the budget goes unused. Its nDCG gap (−0.09) is much larger than its CEC gap (−0.02 to −0.04), which fits the scoring-unit caution in Section 4. "Semantic chunking is worse" therefore holds for this budget and unit cap, not in general. It also costs about 6 s per paper to chunk. This is consistent with Qu et al. [11], who found that semantic chunking does not consistently beat fixed-size chunking (on QASPER the differences were small) and that different chunkers often retrieve the same evidence sentences. Their study does not cover hierarchical chunking, so it says nothing about hierarchical vs fixed-size.
- **Assembly matters.** In 48% of questions the production assembly stops before using the budget. The fill variant raises CEC by +0.037 (with +151 tokens). This is noted as a possible improvement; production is unchanged.

**Selection for the combination:** `hierarchical` (best ranking, theory-backed) and `fixed_size` (simplest method, best CEC). Semantic chunking is not selected: it is weaker on both metrics and slower.

### 5.3 Embedding model

**Methods.** Five open-source models up to 149M parameters:
- e5-small-v2 (production) [4]
- all-MiniLM-L6-v2 [5]
- snowflake-arctic-embed-s
- bge-small-en-v1.5 [6]
- ModernBERT-embed-base [7]

SPECTER2 [8], a scientific-paper model, was run separately.

**Theory.**
- Contrastively trained retrieval models with query/passage prefixes (e5, bge, arctic) should beat general sentence models (MiniLM).
- A larger model with a long context window (ModernBERT, 8,192 tokens) should be more accurate but slower.
- MiniLM truncates input at 256 tokens.
- SPECTER2 is trained for paper-to-paper similarity (citations), not for question-to-passage search.

**Results.** 150-paper subset, 249 questions; hierarchical, dense, production context.

| Model | Params | nDCG@10 | CEC@0.5 | Query latency P50 | Indexing (chunks/s) | Peak memory |
|---|---|---|---|---|---|---|
| ModernBERT-embed-base | 149M | **0.464** | 0.743 | 64.5 ms | 3.0 | 2.2 GB |
| e5-small-v2 | 33M | 0.454 | 0.739 | 17.3 ms | 17.3 | 1.3 GB |
| snowflake-arctic-embed-s | 33M | 0.440 | **0.751** | 17.5 ms | 16.2 | 1.3 GB |
| bge-small-en-v1.5 | 33M | 0.412 | 0.699 | 17.8 ms | 16.6 | 1.3 GB |
| all-MiniLM-L6-v2 | 23M | 0.383 | 0.679 | 9.4 ms | 44.4 | 1.1 GB |
| SPECTER2 (separate) | 110M | 0.281 | 0.606 | 48.9 ms | 4.9 | 2.0 GB |

Sources: `phase_3_embedding/artifacts/embedding/summary.json` and `embedding_specter2/summary.json`. Memory is the peak working set of the embedding process.

**Observation.**
- **The ordering agrees with theory.** The larger long-context model is most accurate, the retrieval-trained small models follow, and MiniLM is last.
- **ModernBERT's gain over e5 is small** (+0.010 nDCG@10) for about 4× the query latency and about 6× slower indexing.
- **SPECTER2's low score is consistent with its task mismatch.** It was loaded as its model card prescribes (ad-hoc query adapter for questions, proximity adapter for passages), so its training objective, not the setup, is the likely reason.
- **Memory needs measuring in the combination setting.** In the earlier 150-paper grid, the ModernBERT embedding process peaked at 13.8 GB, against 2.2 GB here; both are process working set. The grid process embedded six extractor × chunker unit sets, including pypdf text and 400-token chunks; this run embedded only hierarchical children. The cause of the higher peak was not isolated, which is why the combination profile run measures memory in its actual setting.

**Selection for the combination:** e5-small-v2 (production, best accuracy/cost balance) and ModernBERT (most accurate). Together they span the quality/cost trade-off. arctic-s is close to e5 but adds no new trade-off point.

### 5.4 Retrieval strategy

**Methods.**
- dense (production)
- BM25
- RRF (rank fusion of dense and BM25, k = 60) [9]
- hybrid-convex: 0.7 × min-max(dense) + 0.3 × min-max(BM25), over all chunks of the paper

BM25 was tested with two tokenizers: whitespace (`_prod`, as in the older production code) and regex with stopword removal (`_fix`). Cross-encoder rerankers (`ms-marco-MiniLM-L6-v2`, `bge-reranker-base`) re-scored the dense top 30 in a separate run.

**Theory.**
- BM25 [10] matches exact terms and helps when questions share words with the text: names, acronyms, numbers.
- Dense retrieval matches meaning and helps with paraphrases.
- Hybrids should help when both kinds of signal matter.
- Cross-encoders read the question and passage together, so they should rank better, at a higher cost.

**Results.** nDCG@10 per dataset; hierarchical, e5, production context.

| Method | QASPER (335 / 567) | PeerQA PDF (107 / 288) | PeerQA text (73 / 148) |
|---|---|---|---|
| dense | **0.445** | 0.340 | 0.476 |
| hybrid-convex (regex BM25) | 0.444 | 0.375 | 0.517 |
| RRF (regex BM25) | 0.432 | **0.380** | 0.512 |
| RRF (whitespace BM25, old production) | 0.432 | 0.354 | 0.494 |
| BM25 (regex) | 0.362 | 0.351 | 0.475 |
| BM25 (whitespace) | 0.319 | 0.308 | 0.451 |

Source: `phase_6_hybrid_retrieval/artifacts/retrieval_fusion/{C-RET,PEERQA-PDF,PEERQA-TEXT}/summary.json`.

| Reranker (QASPER component set) | nDCG@10 | CEC@0.5 | Added latency P50 / P95 |
|---|---|---|---|
| none (dense) | 0.445 | 0.732 | — |
| ms-marco-MiniLM-L6-v2 | 0.457 | 0.773 | 1.0 s / 1.4 s |
| bge-reranker-base | 0.355 | 0.681 | 6.3 s / 8.6 s |

Source: `phase_6_hybrid_retrieval/artifacts/reranking/summary.json`.

**Observation.**
- **On QASPER, hybrids add nothing over dense; on PeerQA they help.** This fits the theory and the data: QASPER questions were written from the abstract only and share few words with the evidence, while PeerQA questions come from reviewers who read the paper.
- **The earlier grid shows the hybrid effect depends on the rest of the pipeline.** On the 150-paper subset (`phase_12_combination/artifacts/stage1/summary.json`), hybrid-convex minus dense on nDCG@10 is about 0 for hierarchical + e5 (−0.005) and hierarchical + ModernBERT (+0.006), but +0.04 to +0.05 for fixed-size chunks with the same embedders. Hybrid helps where dense retrieval is weaker. The retrieval experiment ran in the production cell, where dense is strongest; this interaction is why both retrieval modes are kept.
- **The expected order hybrid > dense > BM25 holds only in part.** It needs the two retrievers to find different evidence and the fusion to turn that into net gains. Per question, on CEC@0.5 (from the same `per_query.jsonl` files):

  | Dataset | Evidence only dense finds | Evidence only BM25 finds | Hybrid rescues vs dense | Hybrid loses vs dense |
  |---|---|---|---|---|
  | QASPER | 16.8% | 11.1% | 42 questions | 37 questions |
  | PeerQA PDF | 8.7% | 9.0% | 19 | 14 |
  | PeerQA text | 2.0% | 4.1% | 7 | 1 |

  On QASPER the two retrievers do complement each other, but the fusion loses almost as many questions as it rescues. Possible reasons, not tested individually:
  - α = 0.7 was fixed, not tuned;
  - per-question min-max scaling inflates weak BM25 matches when questions share few words with the text;
  - BM25 term statistics come from one paper's ~66 chunks;
  - with at most 5 context units, one wrong unit displaces a right one.
- **The fusion weight was tuned, and 0.7 was kept.** α was swept over {0, 0.3, …, 0.9, 1} on Train papers only (150-paper subset, 249 questions; the 4 chunker × embedder pipelines of the combination run; `phase_6_hybrid_retrieval/scripts/tune_hybrid_alpha.py`, results in `artifacts/hybrid_alpha_sweep/summary.json`). α = 1 and α = 0 reproduce dense and BM25 exactly.

  | α | 0 (BM25) | 0.3 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 | 1 (dense) |
  |---|---|---|---|---|---|---|---|---|
  | mean nDCG@10 | 0.365 | 0.413 | 0.441 | 0.451 | **0.459** | **0.460** | 0.447 | 0.436 |
  | mean CEC@0.5 | 0.719 | 0.757 | 0.779 | 0.773 | 0.773 | 0.776 | 0.764 | 0.753 |

  The best region is 0.7–0.8. Hierarchical pipelines peak at 0.8 and fixed-size ones at 0.7, but the averages differ by 0.001, so the original 0.7 is kept. The tuned weight does not change the earlier conclusion: for the strong pipelines (hierarchical with e5 or ModernBERT) hybrid gains over dense are small (≤ +0.02 nDCG@10), and for fixed-size chunks they are larger (+0.04 to +0.05). Dev and Test papers were not used for this choice. (α = 0.7 itself was never tuned before: it was a fixed value from the first experiments.)
- **The tokenizer matters for BM25.** Whitespace splitting keeps punctuation attached ("model," ≠ "model") and keeps stopwords, which explains the gap between the two BM25 variants.
- **The MiniLM cross-encoder** helps a little (+0.012 nDCG@10) but adds about 1 s per question.
- **bge-reranker-base is far worse than no reranking.** Code checks found nothing wrong: question/passage order, descending score sort, 512-token limit against ~200-token children, and a classification-head model config. A load test confirmed the model works: no loader warnings, and on the model card's own example the raw scores separate the irrelevant and relevant passages clearly (−8.2 vs +6.2). So this is a real result of this setup, not a loading error. Its cause is **not established**; a mismatch between the reranker's training data and scientific question–paragraph pairs is plausible but untested. It is not interpreted as "cross-encoders do not work here".

**Selection for the combination:** dense (best on QASPER, simplest) and hybrid-convex (best on PeerQA; helps weaker pipelines in the grid). RRF and the whitespace-tokenizer variants are not selected, since they score no higher anywhere. Rerankers are not selected: the small gain is too slow for interactive use.

### 5.5 Answer generation

**Methods.** Local models through Ollama: llama3.2:1b and 3b (production), qwen2.5:0.5b and 1.5b, phi4-mini. All get the **gold evidence** as context, so this experiment measures the generator alone, not retrieval. Settings: temperature 0, at most 256 new tokens, a prompt that asks the model to refuse when the context is insufficient.

**Theory.** Larger models should follow instructions and stay grounded better. Smaller models are faster but more likely to add unsupported content.

**Results.** Generation set, 250 papers / 500 questions, gold-evidence context.

| Model | Token F1 | Refusal rate | Containment proxy | Latency P50 | Memory (Ollama process tree) |
|---|---|---|---|---|---|
| qwen2.5:1.5b | **0.240** | 29.2% | 0.523 | 4.0 s | 6.0 GB |
| phi4-mini | 0.233 | 50.0% | 0.398 | 6.0 s | 9.0 GB |
| qwen2.5:0.5b | 0.232 | 10.0% | 0.603 | 3.9 s | — |
| llama3.2:3b | 0.203 | 48.6% | 0.379 | 5.6–6.6 s | 8.8 GB |
| llama3.2:1b | 0.135 | 58.8% | 0.293 | 5.1 s | — |

Sources:
- first three models: `phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json` (llama3.2:3b, llama3.2:1b, qwen2.5:0.5b);
- extra models, plus a re-run of llama3.2:3b with F1 0.202: `generation_extra_llms/summary.json` (qwen2.5:1.5b, phi4-mini).

Memory is the peak over a 500-prompt session. In a separate warm-model profile (`generation_resource_profile/summary.json`), peaks were 4.9 / 2.2 / 0.85 GB for llama3.2:3b / 1b / qwen2.5:0.5b.

**Human check** (single reviewer; 20 questions × 3 models; labels corrected after an attribution fix; `phase_9_generation/artifacts/human_faithfulness_review/correction/`):

| Model | Supported | Unsupported or contradicted | Valid refusal | Unjustified refusal |
|---|---|---|---|---|
| llama3.2:3b | 10 | 1 | 5 | 3 |
| llama3.2:1b | 7 | 3 | 4 | 6 |
| qwen2.5:0.5b | 10 | 7 | 0 | 0 |

**Observation.**
- **The theory holds only partly.** The 3B model is better than the 1B model, but it has lower Token F1 than the much smaller qwen models.
  - Most of the gap comes from refusals: llama3.2:3b refuses about half the time, and every refusal scores 0.
  - In the human check, qwen2.5:0.5b almost never refuses but makes 7 unsupported or contradicted claims out of 20, against 1 out of 20 for llama3.2:3b.

  Token F1 and refusal rate therefore measure different things; neither alone ranks the models.
- **Yes/no questions are hard for every model:** boolean accuracy is 25% for llama3.2:3b (`generation_reanalysis/summary.json`). The answers often do not start with an explicit yes/no that the scorer can read.
- **qwen2.5:1.5b and phi4-mini have no human check.**

**Selection for the combination:** llama3.2:3b (production; most reliable in the human check) and qwen2.5:1.5b (highest Token F1, fast, less memory). These are complementary pieces of evidence, not a ranking: neither model is claimed to beat the other.

### 5.6 Indexing (short note)

An earlier check on v1 data measured approximate nearest-neighbour search (HNSW) against exact cosine search:
- Recall@10 was 100% for the 384-dimension models and 99% for ModernBERT (M = 16, ef_search = 64), with no change in nDCG@10.
- The cost was a few milliseconds per query.

The application's per-document collections are small, and the embedded Qdrant uses exact search, so indexing is not a component of the combination experiment. The experiment files are kept in the project archive.

---

## 6. Result checks

Before the selected methods were fixed, the results that could change a selection, plus a few other surprising ones, were checked. The checks read code, settings and per-query outputs; nothing was rerun.

| Result checked | What was checked | What was found | Effect on conclusions |
|---|---|---|---|
| Hybrid ≈ dense on QASPER but better in the grid | BM25 tokenizer at index and query time, candidate pool, min-max scope, α direction, missing candidates | Same tokenizer both sides. The convex fusion scores all chunks of the paper (no missing candidates), min-max per query, α = 0.7 weights dense. RRF uses the union of each list's top 50. Grid gains are large only where dense is weaker | No bug. The effect depends on the pipeline, so both modes are kept |
| Chunker ranking differs between chunking experiment and grid | Same-setting comparison inside the grid | With matched settings (pymupdf_layout, dense), hierarchical leads fixed_size on nDCG@10 for every embedder (e5 0.454 vs 0.400; ModernBERT 0.464 vs 0.426). Fixed_size leads on CEC and uses about 285 more tokens. The grid's averaged ranking is pulled by hybrid and pypdf cells | No reversal. Report CEC and context size next to nDCG |
| ModernBERT memory 13.8 GB vs 2.2 GB | What each figure measured | Both are the embedding process's peak working set, in different workloads (all grid unit sets vs hierarchical children only) | Cause not isolated; measured again in the combination profile |
| bge-reranker much worse than no reranking | Argument order, sort direction, truncation, model config, load test on known pairs | No error found; the model loads and scores a known relevant pair far above an irrelevant one | Real result of this setup; cause not established (domain mismatch plausible) |
| pdfplumber recall 0.558 | Raw output on the two lowest papers | Words glued together under default settings | Claim limited to default settings |
| SPECTER2 0.281 | Adapter loading and pooling | Set up as its model card prescribes | Consistent with task mismatch |
| Semantic chunking −0.09 nDCG@10 | Context size and unit count | Hits the 5-unit cap with a partly used budget; the CEC gap is smaller | Claim limited to this budget and cap |
| llama3.2:3b F1 below the qwen models | Refusal scoring and human labels | Refusals score 0; the human check shows fewer unsupported claims | Use F1, refusal rate and the human check together |

---

## 7. Combination experiment: 16 configurations

### 7.1 Design

The extractor is fixed to PyMuPDF Layout (Section 5.1). Two methods are selected for each of the other four components (Sections 5.2–5.5):

| Component | Method 1 | Method 2 |
|---|---|---|
| Chunker | hierarchical (200 / 40, parent expansion) | fixed_size (400) |
| Embedder | intfloat/e5-small-v2 | nomic-ai/modernbert-embed-base |
| Retrieval | dense | hybrid-convex (α = 0.7, chosen on Train papers; regex BM25) |
| LLM | llama3.2:3b | qwen2.5:1.5b |

That gives 2 × 2 × 2 = 8 retrieval pipelines, each with 2 LLMs, so **16 configurations**. IDs look like `HIER_E5_DENSE_LLAMA3B` or `FIXED_MBERT_HYBRID_QWEN15B`.

Each selected method is supported by its own component experiment. Those experiments used different datasets and setups, so they do not form one leaderboard; the combination run is the first time all selected methods are compared under one common setup. All other settings follow the component experiments:
- production section extraction;
- a 1,600-token budget with at most 5 units;
- temperature 0 and `num_ctx` 4096.

The refusal gate is calibrated per retrieval pipeline so that every pipeline refuses the same share of questions as production on the 150-paper grid (2.4%); see `GATES` in the runner.

### 7.2 Data: the QASPER combination set

The set is built by `phase_0_baseline/scripts/build_combination_set.py` and written to `phase_0_baseline/artifacts/combination_set.json`. All counts come from that file.
- **Papers:** every QASPER v0.3 paper, from any split, whose **latest** arXiv PDF is available and gives text with PyMuPDF Layout. There is no fallback to older PDF versions and no version check against the annotations.
- **Questions:** every question where an annotator gave both an answer and text evidence.
- **Exclusions,** each recorded with its reason:
  - no PDF downloaded;
  - latest PDF unavailable;
  - extraction failed;
  - unanswerable question;
  - figure/table-only evidence.
- **Train papers are the previously downloaded subset** (463 of 888), not all of Train. Dev and Test papers are downloaded by `download_pdfs.py`.
- **Version mismatch:** some PDFs may be a later version than the text QASPER annotated. This lowers scores for every configuration alike and is a limitation, not an exclusion.

| Split | QASPER papers / questions | Papers included | Questions included | Excluded |
|---|---|---|---|---|
| Train (previously downloaded subset) | 888 / 2,593 | 461 | 927 | 425 papers not downloaded, 2 with no latest PDF; 108 unanswerable and 84 figure/table-only questions |
| Dev | 281 / 1,005 | 275 | 891 | 5 papers not downloaded (no answerable question), 1 with no latest PDF; 55 unanswerable, 49 figure/table-only |
| Test | 416 / 1,451 | 406 | 1,304 | 8 papers not downloaded (no answerable question), 2 with no latest PDF; 74 unanswerable, 55 figure/table-only |
| **Total** | 1,585 / 5,049 | **1,142** | **3,122** | no ID conflicts; 1 pair of duplicate question texts kept |

**Generation sample.** Generating answers for all 3,122 questions × 16 configurations would take roughly 67 hours or more, so the workload is split:
- **Retrieval and context metrics** use every question of the set.
- **All 16 configurations generate answers for the same 300 questions** (`phase_0_baseline/artifacts/generation_sample.json`, from `sample_generation_questions.py`). The sample has 100 per split, at most one per paper, and answer types proportional within each split. Seed 42.

| Split | Extractive | Abstractive | Yes/no |
|---|---|---|---|
| Train | 61 | 24 | 15 |
| Dev | 62 | 27 | 11 |
| Test | 60 | 25 | 15 |

Every per-question result is kept, including failures, timeouts and refusals. Generation results are reported overall, per split and per answer type. The sample is a fixed, reproducible subset; it is not representative of all QASPER questions.

**This is an exploratory end-to-end comparison on the assembled evaluation set.** Many of its papers were also used to choose the methods. It shows which configuration did best on this set and how the components interact; it does not show that the winner generalises to unseen papers. It is not an independent confirmation of the component experiments.

### 7.3 Running it

```
backend/venv/Scripts/python.exe eval/phases/phase_12_combination/scripts/run_combinations.py --list      # the 16 configurations
backend/venv/Scripts/python.exe eval/phases/phase_12_combination/scripts/run_combinations.py --limit 3   # correctness smoke test
backend/venv/Scripts/python.exe eval/phases/phase_12_combination/scripts/run_combinations.py --profile   # ~10 papers: time + memory, full-run estimate
backend/venv/Scripts/python.exe eval/phases/phase_12_combination/scripts/run_combinations.py             # full run, retrieval on all questions (~43 h)
backend/venv/Scripts/python.exe eval/phases/phase_12_combination/scripts/run_combinations.py --retrieval-scope sample   # retrieval only on the 300 sampled papers (~32 h)
```

**Before the full run:**
- Free memory: close browsers and stop the Python language server and the idle WSL VM (`wsl --shutdown`).
- Optionally set `OLLAMA_NUM_PARALLEL=1` and restart Ollama, to reduce the Ollama runner's memory.
- The run is resumable: if it stops, rerun the same command and it continues from the JSONL files.

**Measured before the run** (`artifacts/combinations/profile/`, `artifacts/combinations/memory_check/`):
- On this CPU, llama3.2:3b takes about 32 s per answer with retrieved contexts of 1,300–1,600 tokens, against 5.6 s with short gold-evidence contexts. qwen2.5:1.5b takes about 14 s.
- Ollama uses 4.5–6.9 GB during llama generation, leaving under 100 MB free on a 14 GB machine.
- The runner unloads the model every 25 answers. This is memory handling only, not a generation setting.
- About 1% of llama answers exceed the production 60 s timeout. They are recorded as generation failures and score 0.

The run works in two phases, so the embedder and the LLM are never in memory together:
- **Retrieval,** per embedder: `retrieval_per_query.jsonl`, plus `contexts.jsonl` with the exact context given to the LLM.
- **Generation,** per LLM: `generation_per_query.jsonl`.

The summaries are `retrieval.csv` (8 rows) and `generation.csv` (16 rows), with main metrics also reported per split: Train papers were used to select the methods and check α; Dev papers were used in the first-round experiments (extractor, chunker and retrieval comparisons); Test papers were never used to choose a method, although the first-round retrieval experiment already evaluated dense vs hybrid on them, in `phase_12_combination/artifacts/combinations/`. Retrieval is evaluated once per retrieval pipeline. The 16-row view repeats those numbers for both LLMs; that does not mean 16 retrieval evaluations were done.

### 7.3a Setup checks (done before the run)

Checked on 20 papers of the grid subset with the runner's own code (cached embeddings, 37 questions × 8 retrieval pipelines):
- **BM25:** the same regex tokenizer is applied to chunks and questions (lower-cased, punctuation split off, 39 stopwords). Terms like `bert-base` and `v1.1` stay intact.
- **Prefixes:** e5 gets `query: ` / `passage: `; ModernBERT gets `search_query: ` / `search_document: `. Passage vectors are unit length (cosine).
- **Candidates and normalisation:** every ranking covers all chunks of the paper; hybrid min-max scaling is per question over all chunks; α weights dense.
- **Context:** every context respects the 5-unit / 1,600-token cap, with no duplicated units. Hierarchical overlap between children cannot duplicate text, because contexts are built from unique parents; fixed-size chunks have no overlap.
- **Comparable budgets:** the cap is the same, but actual use differs. Hierarchical contexts average about 1,300 tokens and fixed-size about 1,590, so differences in context metrics are partly differences in context size.
- **Same contexts for both LLMs:** both read the same saved context per (retrieval pipeline, question) from `contexts.jsonl`.
- **Documentation:** the runner's configuration table matches Section 7.1 (chunk sizes, α, budget, models, temperature 0, `num_ctx` 4096; 16 distinct IDs).

Checked after the run: equal question counts per configuration, and identical prompts for both LLMs (same `prompt_sha` per pipeline and question).

**Reading the results:**
- All questions in the set are answerable, so a refusal is justified only when the retrieved context lacks the evidence. Refusal rate and Token F1 are reported separately for contexts with and without evidence (CEC = 1 / 0).
- Each configuration also lists how many questions it answers better or worse than production (`HIER_E5_DENSE_LLAMA3B`), so per-question regressions are visible behind the averages.
- Token F1, refusal rate and the human check stay separate measurements.
- Results are reported per split. Train papers were used to select methods and check α. Dev papers were used in the first-round experiments. Test papers were never used to choose a method, although first-round retrieval was evaluated on them.

### 7.4 How results will be read

Results are reported by layer, with no composite score:

| Layer | Metrics | Question |
|---|---|---|
| Retrieval | nDCG@10, MRR@10 | Is relevant evidence ranked into the context? |
| Context | CEC@0.5, context tokens | Does the evidence reach the LLM? |
| Generation | Token F1, refusal rate (containment proxy as support) | Does the answer match the references, and how often does the model refuse? |
| Reliability | small human check | Does the model make unsupported claims? |
| Cost | latency, indexing time, peak memory (Python and Ollama), lowest free system memory | Is it practical on the desktop? |

Recall@20 is not reported: the assembled context holds at most 5 units, so a cutoff at 20 says nothing about what the LLM sees.

The best configuration on each layer is compared with the **Individually Best Component Configuration (IBCC)**: hierarchical + ModernBERT + dense, shown with both LLMs, with the production LLM used where one reference is needed. IBCC is a reference point, not an assumed winner. The comparison asks:
- Does combining the individually strongest methods give the strongest pipeline?
- Does a cheaper embedder become preferable with a particular chunker?
- Does hybrid help one embedder more than the other?
- Does an LLM behave differently with different contexts?

The final choice for the application will be argued from quality, reliability and cost together.

**Human check (planned):**
- **Sample:** 15 questions (seed 42, stratified by answer type) × 2 LLMs, all on the same retrieval pipeline, for 30 answers. The pipeline is chosen by a context-retention rule: highest CEC, then nDCG@10. This rule picks the context both LLMs see; it is not a claim that this is the best retrieval pipeline.
- **Labels:** the 6-label rubric, with answers and refusals judged against the retrieved context.
- **Status:** a single-reviewer, qualitative, supplementary check.

**Status:** runner, dataset (1,142 papers / 3,122 questions) and generation sample (300) ready. The smoke test, profile run and memory check are done. The full run has not started. **All combination results are pending.**

---

## 8. Limitations

- **Selection and evaluation share papers:** methods were chosen on the same QASPER papers they were evaluated on, and the combination set reuses many of them. The results describe these papers, not unseen ones.
- **One domain:** QASPER covers NLP/ML arXiv papers only. PeerQA is a small cross-domain check of retrieval only.
- **Pre-training contamination:** the LLMs may have seen these public papers during pre-training; nothing here rules that out.
- **Proxy metrics:** relevance and CEC are word-overlap rules, not human relevance judgements. Token F1 measures overlap with reference answers, not truth, and penalises valid paraphrases and refusals.
- **Small human checks:** one reviewer, 60 answers (generation) and 30 planned answers (combination). They are illustrations, not estimates of error rates.
- **Different setups across component experiments:** the component set (335 papers) and the 150-paper subset were used for different components, and the generation experiment uses gold evidence. Their numbers are not one leaderboard.
- **PDF versions:** latest arXiv PDFs may differ from the annotated text.
- **Hardware:** CPU-only desktop (Ryzen 7 7735HS, about 14 GB usable RAM). Latency and memory are specific to this machine.

## 9. How to reproduce

Use the backend virtual environment (`backend/venv`). Shared code is in `backend/scripts/eval_common/` (metrics, relevance rule, pipeline helpers). The cache of extractions and embeddings is in `eval/data/revalidation_cache/` (not in git; it is rebuilt automatically).

| Experiment | Script (under `eval/phases/`) | Output folder |
|---|---|---|
| Extraction | `phase_1_extraction/scripts/evaluate_extraction.py`, `evaluate_extraction_grobid.py` | `phase_1_extraction/artifacts/` |
| Chunking | `phase_2_chunking/scripts/evaluate_chunking.py` (+ `_semantic`, `_children`, `assembly_fill_check.py`) | `phase_2_chunking/artifacts/chunking*/` |
| Embedding | `phase_3_embedding/scripts/evaluate_embedding.py` (+ `_specter2`) | `phase_3_embedding/artifacts/embedding*/` |
| Retrieval | `phase_6_hybrid_retrieval/scripts/evaluate_retrieval_fusion.py --cohort C-RET\|PEERQA-PDF\|PEERQA-TEXT`, `evaluate_reranking.py` | `phase_6_hybrid_retrieval/artifacts/` |
| Generation | `phase_9_generation/scripts/evaluate_generation.py`, `evaluate_generation_extra_llms.py`, `profile_generation_resources.py` | `phase_9_generation/artifacts/` |
| Earlier grid | `phase_12_combination/scripts/combo_stage1_grid.py` | `phase_12_combination/artifacts/stage1/` |
| Combination data | `phase_0_baseline/scripts/download_pdfs.py`, `extract_combination_pdfs.py`, `build_combination_set.py` | `phase_0_baseline/artifacts/combination_set.json` |
| Combination | `phase_12_combination/scripts/run_combinations.py` | `phase_12_combination/artifacts/combinations/` |

Each script has a `--limit N` smoke-test option. Older result files kept their original form; some still contain fields from the earlier statistical analysis, and those fields are not used in this document.

## 10. References and models

1. P. Dasigi et al., "A Dataset of Information-Seeking Questions and Answers Anchored in Research Papers" (QASPER), NAACL 2021.
2. T. Baumgärtner, T. Briscoe and I. Gurevych, "PeerQA: A Scientific Question Answering Dataset from Peer Reviews", NAACL 2025, pp. 508–544.
3. K. Järvelin and J. Kekäläinen, "Cumulated Gain-Based Evaluation of IR Techniques", ACM TOIS, 2002.
4. L. Wang et al., "Text Embeddings by Weakly-Supervised Contrastive Pre-training" (E5), arXiv:2212.03533, 2022. Model: https://huggingface.co/intfloat/e5-small-v2
5. N. Reimers and I. Gurevych, "Sentence-BERT", EMNLP 2019. Model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
6. S. Xiao et al., "C-Pack: Packed Resources for General Chinese Embeddings" (BGE), SIGIR 2024. Model: https://huggingface.co/BAAI/bge-small-en-v1.5
7. B. Warner et al., "Smarter, Better, Faster, Longer: A Modern Bidirectional Encoder for Fast, Memory Efficient, and Long Context Finetuning and Inference" (ModernBERT), arXiv:2412.13663, 2024. Model: https://huggingface.co/nomic-ai/modernbert-embed-base
8. SPECTER2: https://huggingface.co/allenai/specter2_base (adapters `allenai/specter2`, `allenai/specter2_adhoc_query`)
9. G. V. Cormack, C. L. Clarke and S. Büttcher, "Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods", SIGIR 2009.
10. S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond", 2009.
11. R. Qu, R. Tu and F. S. Bao, "Is Semantic Chunking Worth the Computational Cost?", Findings of NAACL 2025, pp. 2155–2177. https://doi.org/10.18653/v1/2025.findings-naacl.114

Other models:
- https://huggingface.co/Snowflake/snowflake-arctic-embed-s
- https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2
- https://huggingface.co/BAAI/bge-reranker-base
- Ollama models `llama3.2:1b`/`3b`, `qwen2.5:0.5b`/`1.5b`, `phi4-mini` (https://ollama.com/library)
- GROBID 0.8.2: https://github.com/kermitt2/grobid
- PyMuPDF: https://pymupdf.readthedocs.io/

Embedding model revisions used in the combination run are recorded in `run_combinations.py`: e5-small-v2 `ffb93f3`, modernbert-embed-base `d556a88`.
