# Candidate-Selection Audit: RQ2–RQ5

**Date:** 2026-10-30. **Scope:** a research-design audit. The audit itself ran nothing, downloaded nothing and changed no protocol.
**Bases:**
- the thesis (`DU_AN_CNTT_TOAN_VAN.md` §3, §5, §6.3);
- the frozen protocol (`reports/revalidation/protocol/`);
- the historical artifacts (`eval/results/rq2_chunking_20261024_013443.json`, `rq3_embedding_20261024_000029.json`, Table 5.3);
- the production code (`rag_service.py`, `chunkers.py`);
- the primary model cards cited below.

**Limits and assumptions:**
- **Hardware:** CPU-only Ryzen 7 7735HS with 13.69 GB of RAM.
- **Embedding models:** MIT or Apache-2.0 licence, ≤ 335M parameters.
- **LLMs:** local Ollama, ≤ ~4B parameters, open licence for research use.
- **Task:** single-paper question answering over a scientific PDF.

## A. Executive assessment

**Coverage by RQ:**
- **RQ2 (chunking) and RQ3 (embeddings):** broadly representative once the historical runs are counted. RQ2 v1 covered 8 strategies and RQ3 covered 10 dense models plus BM25.
  - The re-runs (v2) deliberately test a subset. That is fine for re-validation, as long as the thesis states that the conclusion holds only for the tested pool.
  - **RQ2 gap:** the comparison does not separate the two things hierarchical chunking changes: smaller retrieval units, and expanding to the parent section. One control arm, with no new embeddings, closes it.
  - **RQ3 gap:** v2 has no scientific-domain model. SPECTER2 was tested historically under a now-superseded protocol and is missing from the thesis table.
- **RQ4 (retrieval) has the most important gap: second-stage reranking.** RQ4 compares only first-stage fusion (dense, BM25, RRF, convex). Cross-encoder reranking is a different technique. The thesis names it as future work (§6.3.2) but never tests it. Without it, the RQ4 conclusion must be worded as "fusion choice", not "retrieval technique".
- **RQ5 (generation) is narrow.** It has 3 models from 2 families. The production default (llama3.2:3b) is the only model at its size, and family is confounded with size: Qwen has only 0.5b and Llama only 1b/3b. Hence "3b is best" and "qwen 0.5b beats llama 1b" cannot be split into a model-family effect and a size effect.

**Neither too broad nor too narrow overall.** No addition is needed to answer RQ2–RQ5 as currently worded. The recommended additions below make the conclusions defensible rather than larger. Each is cheap on this hardware.

## B. Candidate coverage matrix

| RQ | Category | Current candidates (v2 / historical) | Potentially missing | Coverage |
|---|---|---|---|---|
| RQ2 | Fixed-size (± overlap) | `fixed_size` 400 / + `fixed_size_overlap` | none | Adequate |
| RQ2 | Structure / section-aware | `section_overlap` / + `section`, `section_token` | none | Adequate |
| RQ2 | Sentence-based packing | — / sentence-aware packing (WS3, Dev 48) | none needed | Covered historically (diagnostic) |
| RQ2 | Semantic | — / `semantic` (significantly worse, Δ −0.080) | none | Covered historically |
| RQ2 | Hierarchical (parent–child) | `hierarchical` / + `hierarchical_child` | **children-only control in v2** | Gap: the parent-expansion effect is not isolated |
| RQ2 | Long-document-specific (late chunking, RAPTOR-style summary trees) | — | late chunking, summary trees | Out of scope: long-context embedder or LLM summarisation at index time |
| RQ3 | General contrastive, small | MiniLM, e5-small, BGE-small, arctic-s / + gte-small | none | Adequate |
| RQ3 | Larger / long-context | ModernBERT-embed / + arctic-m v1.5 & v2.0, nomic v1.5, mxbai-large | none | Adequate (historical) |
| RQ3 | Instruction / prefix-asymmetric | e5, BGE, arctic, nomic, ModernBERT | none | Adequate |
| RQ3 | Scientific-domain | — / SPECTER2 + adhoc_query adapter (old protocol, not in thesis) | **SPECTER2 in v2** | Gap: family absent from the current protocol |
| RQ4 | Dense | `dense` | none | Adequate |
| RQ4 | Lexical sparse | `bm25_prod`, `bm25_fix` | none | Adequate |
| RQ4 | Fusion (rank, score) | RRF ×2, convex ×2 | none | Adequate |
| RQ4 | Learned sparse | — | opensearch neural-sparse doc-v2-distill (Apache, 67M) | Defer (see C) |
| RQ4 | Second-stage reranking | — | **cross-encoder rerankers** | **Gap: a different technique, never tested** |
| RQ4 | Query rewriting / expansion | — / acronym expansion (Step 5, 160 papers) | HyDE / LLM rewriting | Exclude (see C) |
| RQ5 | Llama family | llama3.2:1b, 3b | — | — |
| RQ5 | Qwen family | qwen2.5:0.5b | **qwen2.5:1.5b** | Gap: only one Qwen size |
| RQ5 | Other family, same tier as production | — | **phi4-mini (3.8B)** | Gap: no peer for the production model |
| RQ5 | Science-tuned small LLMs | — | none with a fitting licence, CPU footprint and instruction quality | Exclude |
| RQ5 | Generation technique (prompt / refusal wording) | one prompt (NFR-03) | prompt without the strict refusal rule | Defer (see C) |

## C. Recommended additional candidates

**EXT-RQ4-RERANK: cross-encoder reranking. Add (highest priority).**
- **What it does:** a cross-encoder scores each question–passage pair jointly; the reranked top-K then feeds the unchanged context assembly. Category: second-stage reranking.
- **Candidates:**
  - `cross-encoder/ms-marco-MiniLM-L6-v2` (22.7M, Apache-2.0; model card: MS MARCO dev MRR@10 39.0, TREC DL19 nDCG@10 74.3), as the efficient option.
  - `BAAI/bge-reranker-base` (278M, MIT), as the stronger option. If the stronger one also fails, "reranking doesn't help here" is robust.
- **Fairness:** same C-RET papers, same e5 + hierarchical + `pymupdf_layout` cached vectors, the dense top-30 children reranked, the rest kept in dense order, and the same 1,600-token / 5-unit assembly. It is compared against `dense`, the current RQ4 baseline arm.
- **Rule (registered before running):** adopt only if Δ nDCG@10 ≥ +0.02 with CI lower bound > 0 (Holm m = 2), **and** the P95 added rerank latency is ≤ 1,000 ms per query on this CPU, a usability bound for interactive chat.
- **Effort:** about 1 h compute, no new data.
- **Evidence caveat:** both rerankers are trained on web QA (MS MARCO and others). Published results do not predict results on scientific papers.

**EXT-RQ2-CHILD: hierarchical children without parent expansion. Add (cheap, cleaner attribution).**
- **What it does:** the same children and vectors as `hierarchical`, but the assembly returns the children themselves instead of their parents.
- **Why:** it isolates the "small-to-big" effect. Without it, hierarchical vs `fixed_size` mixes unit size with expansion.
- It reuses the RQ2-v2 vectors.
- **Rule:** descriptive, with its own single comparison against `hierarchical`. It cannot be adopted, because it would remove parent expansion; it only informs wording.
- It runs with RQ2-v2, after the CEC labels arrive.

**EXT-RQ3-SPECTER2: scientific-domain embedding. Add (cheap, closes a family gap).**
- **Model:** `allenai/specter2_base` (110M, Apache-2.0) with the `specter2_adhoc_query` adapter for questions and the `specter2` proximity adapter for passages, as the model card prescribes for ad-hoc search.
- **Why:** it is citation-contrastive and trained on scientific text, the obvious family a reviewer would ask about. The historical result (0.2522 nDCG@4, older relevance and protocol) is not comparable with v2.
- **Fairness:** same C-RET-150 pipeline and metrics as RQ3-v2.
- **Rule:** the frozen RQ3 rule against e5 (≥ +0.04, CI lower bound > 0, P50 latency ≤ 1.5× e5), as a separate single test.
- **Caveat:** SPECTER2 was trained for paper-level similarity rather than passage QA, so a poor result is expected. That would still be a finding worth reporting.
- **Effort:** about 45 min.

**EXT-RQ5-LLM: phi4-mini (3.8B, MIT) and qwen2.5:1.5b (Apache-2.0). Add.**
- **Why:**
  - phi4-mini is a different family at the production model's size tier.
  - qwen2.5:1.5b separates family from size within Qwen.
  - qwen2.5:3b is excluded: Qwen Research License, not Apache (Alibaba Cloud release notes).
  - gemma2:2b is not added: its slot as another family is filled by phi4-mini, and the Gemma terms aren't an OSI licence.
- **Fairness:**
  - Same RQ5 500-question manifest, gold evidence, prompt, `temperature=0`, `num_predict=256` and scoring as RQ5.
  - **llama3.2:3b is re-run in the same session** as the paired reference, because the stored answers come from another machine and Ollama version.
  - **Selection-stage only:** the manifest has been evaluated before and is not independent confirmation.
- **Rule:**
  - A model is a candidate for RQ6 only if its Token F1 is ≥ +0.03 above the re-run llama3.2:3b, with CI lower bound > 0 (Holm m = 2).
  - Even then it is added as an **extra** RQ6 condition, registered before RQ6. It does not replace the production default, because it has no human faithfulness review.
- **Also reported:** refusal rate, Boolean accuracy, latency and Ollama-tree memory.
- **Effort:** about 3–4 h CPU; RAM about 3–4 GB for phi4-mini.

**Deferred or excluded:**
- **Learned sparse (neural-sparse doc-v2-distill, Apache, 67M; model card BEIR-13 average nDCG@10 0.504): defer.** RQ4 already tests whether a lexical signal helps dense retrieval, through two BM25 variants. A learned-sparse arm is a different index type that production does not support. It would answer a new question rather than strengthen the current one.
- **HyDE / LLM query rewriting: exclude.** It needs an LLM call per query (seconds on CPU) before retrieval, which is a different system design. Rule-based acronym expansion was already tested historically.
- **Prompt variant without the strict refusal rule: defer.** NFR-03 requires the refusal. The refusal rate is already reported, and RQ6 separates gate refusals from model refusals.
- **RQ2 late chunking / summary trees, science-tuned LLMs: exclude.** Outside the hardware or licence limits, or not mature at ≤ 4B.

## D. Impact on existing conclusions

- **RQ2:** without EXT-RQ2-CHILD, "hierarchical is better" cannot be attributed to parent expansion. With it, the thesis can say which part helps.
- **RQ3:** the conclusion must read "best of the tested pool (10 general-purpose models plus SPECTER2), under this protocol", not "best embedding model".
- **RQ4:** without reranking, the conclusion is limited to the **choice of fusion method**. If a reranker passes, the production retrieval recommendation changes.
- **RQ5:** current results support "llama3.2:3b vs these two smaller models". They do not support "the best local model at this size" or anything about model family. The extension makes the size and family statements possible. The RQ5 human review (60 answers) covers only the original 3 models.

## E. Prioritised list

1. **Essential before finalising:** EXT-RQ4-RERANK. It is the only gap that could change the production retrieval recommendation.
2. **Valuable:** EXT-RQ5-LLM, then EXT-RQ2-CHILD, then EXT-RQ3-SPECTER2.
3. **Out of scope / future work:** learned sparse, HyDE, prompt variants, late chunking, larger models.

## F. Final recommendation

- **Keep the frozen Phase C unchanged.** No omission justifies changing the frozen design.
- **Run the four extensions above as clearly labelled additions.** Each is registered before running (`EXP-REVAL-EXT-*`), runs on selection data only (C-RET, C-RET-150, or the RQ5 manifest; never C-INT), and keeps its own artifact folder.
- **Minimum work to close the most important gap:** the reranking extension, about 1 h compute.
- **Order:**
  - The extensions run after the original runs and before RQ6.
  - EXT-RQ2-CHILD waits with RQ2-v2 for the CEC labels.

### Sources (model cards and release notes)
- [cross-encoder/ms-marco-MiniLM-L6-v2 (Mixpeek mirror of the card)](https://mixpeek.com/model/cross-encoder/ms-marco-MiniLM-L6-v2)
- [allenai/specter2_base](https://huggingface.co/allenai/specter2_base) and [allenai/specter2 README](https://huggingface.co/allenai/specter2/blob/main/README.md?code=true)
- [opensearch-neural-sparse-encoding-doc-v2-distill](https://huggingface.co/opensearch-project/opensearch-neural-sparse-encoding-doc-v2-distill)
- [Ollama phi4-mini:3.8b (MIT)](https://registry.ollama.ai/library/phi4-mini:3.8b-q8_0)
- [Qwen2.5 licences (Alibaba Cloud blog)](https://www.alibabacloud.com/blog/601786) and [Qwen2.5-1.5B-Instruct LICENSE](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/commits/main/LICENSE)
- `BAAI/bge-reranker-base` licence: to be confirmed from its Hugging Face card at download time; it is dropped if the card does not say MIT or Apache.
