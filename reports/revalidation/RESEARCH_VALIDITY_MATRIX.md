# Research Validity Matrix and Experiment Decisions (Revalidation, Phase B0)

**Date:** 2026-10-29. **Status:** pre-registered protocol (hashed in `eval/experiment_provenance_registry.json` under `EXP-REVALIDATION-PROTOCOL` before Gate B).

**Basis:** the cross-RQ audit (`reports/audit/CROSS_RQ_DATASET_VALIDITY_AUDIT.md`, 55-claim matrix) and the approved plan.

The machine-readable configs are in `reports/revalidation/protocol/`.

## 1. Validity matrix (existing experiments)

| | RQ1 Extraction | RQ2 Chunking | RQ3 Embedding | RQ4 Hybrid retrieval | RQ5 Generation | RQ6 Integrated |
|---|---|---|---|---|---|---|
| **Question** | Which PDF extractor gives the most complete, structured text for the app? | Which chunking gives the best evidence in the LLM context under the app's budget? | Which embedder ranks evidence best at acceptable CPU cost? | Does hybrid lexical+dense fusion improve the context over dense-only, as implemented in the app? | Which small local LLM answers best given correct evidence? | How well does the deployed pipeline answer real questions from PDFs? |
| **Population** | Born-digital arXiv/journal scientific PDFs | Same | Same | Same | Scientific QA questions with text evidence | Same, end to end |
| **Unit** | Paper | Question nested in paper | Question nested in paper | Question nested in paper | Question nested in paper | Question nested in paper |
| **Existing data** | 47 Dev papers / 127 q (recorded) | Same 47 / 127 | 207 papers / 615 q (Dev + Train) | Dev 276 / 892; Test 408 / 1,310 | 250 Train papers / 500 q | none |
| **Main validity problem** | Small, single-domain; references are QASPER JSON text | Metrics not budget-constrained; relevance depends on the unit; 0.688 vs 0.505 unexplained | e5 re-ranked on its selection papers (category A); wrong Pareto claim | "Production RRF" arm used benchmark BM25; E1 diagnostic on an already-used Test set | Gold-evidence only; Token F1 unsuitable for Boolean; human review 20 q per model, 1 reviewer | Not measured |
| **Leakage / reuse** | B (shared Dev) | B | A (low) | A for E1 | Clean within the project; C unknown | — |
| **Reproducible from artifacts** | Yes (per-query JSONL) | Yes | Yes (loader reconstruction) | Yes (E1 reproduces RQ4) | Yes | — |
| **Supported now** | Layout extractor is the only one with headings; no large difference detected | Hierarchical best on unbudgeted parent ranking only | ModernBERT best, e5 > MiniLM on a development corpus | Benchmark-BM25 Convex > dense (small); production RRF < dense (diagnostic) | 3b > 1b on Token F1 with gold evidence | Nothing |
| **Planned action** | Retain + confirm on fresh data (RQ1-v2) | Diagnostic (RQ2-diag) + budget-compliant rerun (RQ2-v2) | Qualify + shortlist rerun on fresh data (RQ3-v2) | Clean rerun with app-identical implementations (RQ4-v2) → production decision | Retain; reanalysis (RQ5-R); resource and stability profile (RQ5-M) | New confirmatory study (RQ6) |

## 2. Experiment decision matrix

| Experiment | Decision | Justification |
|---|---|---|
| RQ1 (historical) | **Retain + confirm** | Valid, but 47 papers from one domain; RQ1-v2 on about 360 fresh papers plus PeerQA |
| RQ2 (historical) | **Rerun (budget-compliant) + diagnostic** | Primary metrics ignore the budget; the unit-dependent relevance makes nDCG across strategies non-comparable |
| RQ3 (historical) | **Qualify + shortlist confirm** | Development benchmark; e5 needs a comparison on papers that were not used to select it |
| RQ4 (historical) | **Rerun clean** | Benchmark BM25 ≠ app; production claim requires app-identical arms on fresh data |
| E1 (diagnostic) | **Retain as diagnostic** | Motivated the tokenizer candidate (`bm25_fix`); not confirmation |
| RQ5 (historical) | **Retain + reanalysis + resource profile** | Clean cohort; metric issues are fixable without inference; memory was not measured |
| RQ5 pilot (16 q) | **Historical only** | Smoke test on famous non-QASPER papers |
| RQ6 | **New (confirmatory)** | No end-to-end evidence exists |

## 3. Design rules (pre-registered)

1. **One component at a time.** RQ1–RQ4 each vary one component and hold the rest at production. Production here means `pymupdf_layout`, `hierarchical` (200/40), `intfloat/e5-small-v2`, dense-only retrieval for RQ1–RQ3, a budget of 1,600 estimated tokens and at most 5 units. Winners are combined only in RQ6.
2. **Roles.**
   - C-RET = **selection**.
   - C-INT = **confirmation** (RQ6 only; never used for any tuning, including the refusal gate).
   - Dev 47 = **diagnostic**.
   - PeerQA = **descriptive**.
3. **Smallest effect sizes of interest (SESOI) and decision rule.** A challenger replaces the production component only if it beats it by at least the SESOI and the 95% CI lower bound is above 0.

   | RQ | Primary metric | SESOI | Achievable precision (from existing variance) |
   |---|---|---|---|
   | RQ1 | Evidence recall | 0.03 | — |
   | RQ2 | CEC | 0.05 | ≈ ±0.035 at about 360 papers |
   | RQ3 | Budgeted nDCG@10 | 0.04 | ≈ ±0.035 at 150 papers |
   | RQ4 | Budgeted nDCG@10 | 0.02 | ≈ ±0.010–0.015 at about 360 papers |
   | RQ6 | Token F1 | 0.05 | ≈ ±0.035 at 100 papers |

4. **Statistics.** Paired paper-cluster bootstrap, B = 10,000, seed 42, query-weighted estimand (`eval_common.stats.paired_cluster_bootstrap`). Holm correction within each pre-declared family.
5. **RQ4 tie order:** `bm25_fix` < `rrf_fix` < `convex_fix`. `rrf_prod` and `convex_prod` are never adopted.
6. **Refusal gate:** if RQ3 changes the embedder, the gate is recalibrated on C-RET answerable questions only, to e5's refusal rate at 0.80.
7. **CEC fallback:** if CEC agrees with the human check on fewer than 80% of the 30 cases, budgeted nDCG@10 becomes RQ2's primary metric.
8. **Version check:** a paper is kept if any of the 5 extractors finds ≥ 70% of its evidence paragraphs (≥ 80% content-word containment). RQ1 also reports evidence recall on all opened papers as a sensitivity check.

## 4. Metric definitions

- **Evidence of a question:** the non-FLOAT text evidence paragraphs of any answerable annotator (QASPER), or the authors' evidence sentences (PeerQA).
- **Context:** the production assembly. Ranked units are taken in order. Hierarchical parents are deduplicated, and parents over 800 tokens are windowed ±200 words around the matched child. Assembly stops before a unit would exceed 1,600 estimated tokens (words × 1.33); the first unit is always taken. At most 5 units.
- **CEC (Context Evidence Coverage):** 1 if the context contains some evidence paragraph verbatim, or ≥ τ of its content words (regex tokens, 39 stopwords). τ = 0.50 is primary; 0.30 and 0.70 are reported as sensitivity checks.
- **Budgeted nDCG@10:** relevance of each context unit at τ = 0.50 (`is_chunk_hit`); R_q is counted over the candidate units (unique full parents, or chunks) and floored at 1. This is the RQ4/E1 convention.
- **Evidence recall (RQ1):** the share of evidence paragraphs found (≥ 80% containment) in the extractor's full text.
- **Token F1:** SQuAD/QASPER normalisation, maximum over annotator references. Refusals score 0 in the primary analysis.
- **Boolean accuracy:** the first yes/no token of the answer compared with the majority yes/no reference. Refusals count as wrong; unparseable answers are reported.
- **Memory:** peak working set (Windows RSS) of the evaluating Python process, and the peak summed working set of the Ollama process tree. Both are sampled every 0.1 s and reported separately; shared pages are double-counted. The run is CPU-only (`size_vram` = 0).

## 5. Known limitations accepted in advance

- **Single-paper QA only.** Papers are mostly NLP/ML; PeerQA adds a few other domains, descriptively only.
- **Lexical, automatic relevance labels.** CEC and nDCG use them; a 30-case human check validates CEC.
- **Token F1 is a lexical proxy** for answer quality.
- **The version check removes papers** whose evidence no extractor can find, so a version mismatch shared by all extractors is not measurable.
- **C-RET results are selection results.** Only RQ6 on C-INT is confirmatory.
- **Pretraining exposure of the LLMs and embedders to these public papers cannot be ruled out.**
- **Hardware differs from the historical results.** The new runs are on an AMD Ryzen 7 7735HS laptop (8 cores / 16 threads, CPU-only); the historical latency figures were reported on a Ryzen 5 5600. Latency is compared only within the new runs.
