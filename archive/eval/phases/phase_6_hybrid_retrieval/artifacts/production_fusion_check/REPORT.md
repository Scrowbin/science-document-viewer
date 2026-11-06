# E1 / RQ4-P: RRF vs Convex under production-style BM25

**Experiment ID:** `EXP-RQ4P-PRODUCTION-FUSION` (registered 2026-10-29).
**Script:** `eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_rq4p_production_fusion.py` (`--split dev`, `--split test`).
**Follow-up:** `scripts/decompose_rq4p_bm25_dev.py` (post-hoc, Dev only).
**Status:** completed. This analysis corrects and extends RQ4. The original RQ4 artifacts are unchanged and remain valid for the benchmark configuration they describe.

## 1. Question and design

The original RQ4 measured fusion with a benchmark BM25 (WordPiece tokens, a 39-word stopword list, IDF over the whole split). Production (`DocumentRAG.hybrid_search`) uses `rank_bm25.BM25Okapi` on `text.lower().split()` over one document's child chunks, no stopwords, then RRF k = 60 over the top-50 dense and top-50 BM25 candidates.

**Question:** which fusion is better when BM25 is computed as production computes it?

**Held fixed (identical to RQ4):**
- Corpus: QASPER v0.3 `full_text`; hierarchical children, 200 estimated tokens / overlap 40.
- Embeddings: cached e5-small-v2 vectors (`artifacts/cache/full_qasper_{dev,test}_hierarchical_*.npy`).
- Relevance: τ = 0.50 containment on unique parent sections; R_q floored at 1.
- Downstream: parent expansion with ≤ 5 parents and a 1,600-token budget. Parents over 800 tokens are trimmed to their first 400 words; this is the RQ4 rule, whereas production windows ±200 words around the matched child.
- Metrics: as in RQ4.

**Arms:** dense; bm25_bench; rrf_bench; convex_bench (α = 0.7); bm25_prod; rrf_prod (exact production fusion logic); convex_prod (α = 0.7). Dev only: convex_prod with α ∈ {0.5, 0.6, 0.8, 0.9}.

**Primary metric:** nDCG@10 over the budgeted parent list. **Secondary:** nDCG@4, MRR@10, Recall@20 (capped by ≤ 5 parents), Hit@5, and per-query latency of the scoring and fusion step.

**Statistics:**
- Paired paper-cluster bootstrap: B = 2,000, seed 42. Estimand: query-weighted mean nDCG@10 difference; resampling unit: paper.
- p-values: finite-sample bootstrap bound.
- Pre-declared family on Test, Holm m = 3: {rrf_prod − dense, convex_prod − dense, convex_prod − rrf_prod}.
- Dev and the α sweep are descriptive.

**Data exposure:** Dev and Test were both used by RQ4, so Test results are a post-selection diagnostic, not an independent confirmation.

**Reproduction gate (passed):** dense, rrf_bench and convex_bench reproduce RQ4 nDCG@10 to 4 decimals on both splits (Dev 0.5610 / 0.5573 / 0.5650; Test 0.5655 / 0.5662 / 0.5806).

## 2. Results

### Test (408 papers, 1,310 queries, 14,035 children)

| Arm | nDCG@10 | nDCG@4 | MRR@10 | Recall@20* | Hit@5 |
|---|---|---|---|---|---|
| dense | 0.5655 | 0.5724 | 0.6415 | 0.6366 | 0.8267 |
| bm25_bench | 0.5065 | 0.5135 | 0.5688 | 0.5908 | 0.7794 |
| rrf_bench | 0.5662 | 0.5747 | 0.6368 | 0.6413 | 0.8305 |
| convex_bench | 0.5806 | 0.5870 | 0.6556 | 0.6525 | 0.8450 |
| **bm25_prod** | 0.4125 | 0.4196 | 0.4716 | 0.4911 | 0.6771 |
| **rrf_prod** | 0.5229 | 0.5316 | 0.5936 | 0.6025 | 0.7985 |
| **convex_prod** | 0.5566 | 0.5637 | 0.6253 | 0.6390 | 0.8282 |

\*Recall@20 is computed over at most 5 budgeted parents.

| Pre-declared comparison (Test) | Δ nDCG@10 | 95% CI | p_raw | p_Holm |
|---|---|---|---|---|
| rrf_prod − dense | −0.0426 | [−0.0563, −0.0280] | 0.001 | 0.003 |
| convex_prod − dense | −0.0089 | [−0.0191, +0.0021] | 0.121 | 0.121 |
| convex_prod − rrf_prod | +0.0337 | [+0.0243, +0.0431] | 0.001 | 0.003 |

The benchmark comparisons reproduce RQ4: rrf_bench − dense +0.0008 (p 0.87); convex_bench − dense +0.0152 [+0.0045, +0.0262].

### Dev (276 papers, 892 queries): direction check and α sensitivity

| Arm | nDCG@10 | Δ vs rrf_prod [95% CI] |
|---|---|---|
| dense | 0.5610 | |
| rrf_prod | 0.5148 | |
| convex_prod α = 0.5 | 0.5076 | −0.0072 [−0.0187, +0.0039] |
| convex_prod α = 0.6 | 0.5318 | +0.0170 [+0.0058, +0.0278] |
| convex_prod α = 0.7 | 0.5442 | +0.0294 [+0.0173, +0.0413] |
| convex_prod α = 0.8 | 0.5588 | +0.0440 [+0.0291, +0.0587] |
| convex_prod α = 0.9 | 0.5619 | +0.0471 [+0.0314, +0.0635] |

On Dev, rrf_prod − dense = −0.0462 [−0.0644, −0.0283] and convex_prod − dense = −0.0168 [−0.0313, −0.0026].

### Latency (Test, per query, one CPU core, `perf_counter`)

| Step | P50 (ms) | P95 (ms) |
|---|---|---|
| production BM25 scoring (`get_scores`) | 0.126 | 0.279 |
| RRF fusion | 0.014 | 0.028 |
| Convex fusion | 0.032 | 0.065 |

All three are negligible compared with query embedding (~30 ms) and LLM generation (seconds).

### Post-hoc decomposition (Dev only, exploratory, not pre-declared)

| BM25 variant | BM25 alone | RRF with dense |
|---|---|---|
| WordPiece + stopwords, IDF over the split (benchmark) | 0.4844† | 0.5571 |
| WordPiece + stopwords, per-document IDF | 0.4724 | 0.5571 |
| whitespace + stopwords, per-document IDF | 0.4179 | 0.5073 |
| whitespace, per-document IDF (**production**) | 0.3991 | 0.5148 |

†Differs from RQ4's 0.4860 only by tie-breaking order (`argsort` vs `sorted`).

## 3. Interpretation

1. **The original RQ4 "RRF [Prod]" result does not describe production.** With production BM25, hybrid RRF scores significantly *below* dense-only on both Test (−0.043) and Dev (−0.046).
2. **The cause is mainly tokenization, not document-local IDF** (exploratory). Whitespace splitting keeps punctuation attached ("model," ≠ "model"). With WordPiece tokens and per-document IDF, RRF recovers to 0.5571, close to dense (0.5610). The earlier argument that "local IDF compression destabilizes score fusion" is not supported as the main mechanism.
3. **Switching rule (RRF → Convex), as approved:**

   | Criterion | Result |
   |---|---|
   | Δ ≥ +0.01 | met (+0.0337) |
   | CI excludes 0 | met |
   | Same direction on Dev | met (+0.0294) |
   | Not sensitive to α ± 0.1 | met (α 0.6 / 0.8: +0.017 / +0.044, both CIs > 0) |

   **The rule is satisfied: Convex outperforms RRF under production BM25.**
4. **But Convex does not beat dense-only.** On Test, convex_prod − dense = −0.009 (n.s.); on Dev it is −0.017 (significant, descriptive). Higher α (less BM25 weight) moves Convex towards dense. Under the current production BM25, the lexical branch adds no measurable value on this benchmark.
5. **Theory vs evidence:** the theoretical arguments for RRF (scale-free, untuned) still hold. Empirically, however, RRF is more exposed than Convex to a weak lexical retriever, because it weights both ranked lists equally regardless of their quality.

## 4. Engineering options (no production change made)

| Option | Evidence | Note |
|---|---|---|
| A. Switch to Convex α = 0.7 (as the rule permits) | Test +0.034 vs current RRF; still −0.009 vs dense (n.s.) | Smallest code change; α is a tuned weight |
| B. Fix BM25 tokenization (WordPiece or regex + stopwords), keep RRF | Dev only (exploratory): RRF 0.5571 ≈ dense 0.5610 | Not measured on Test; needs a pre-declared check before claiming parity |
| C. Dense-only retrieval | Best or tied-best on all measurements here | Loses any keyword robustness (never measured on this benchmark) |

Recommendation for your decision: **B** (fix the tokenization defect), optionally combined with A. A gives the largest measured gain over the current production behaviour and meets the approved rule. B removes the root cause, but its benefit has only exploratory Dev evidence. No production code was changed.

## 5. Dataset adequacy

Counts are from `dataset_adequacy_counts.json`, recomputed with the RQ4 loaders.

1. **Usable sample after exclusions.**

   | | Dev | Test |
   |---|---|---|
   | Papers in split | 281 | 416 |
   | Papers with ≥ 1 usable question | 276 | 408 |
   | Usable questions | 892 | 1,310 |
   | Child chunks | 9,698 | 14,035 |
   | Questions with no relevant parent at τ = 0.50 (R_q floored to 1; every arm scores 0 on them) | 2 | 0 |
   | Questions per paper: mean / max | 3.23 / 10 | 3.21 / 9 |

   **Inclusion rule:** a question counts if it has at least one non-unanswerable annotation with non-float text evidence. Unanswerable and figure/table-only questions are excluded.

2. **Independent unit.** The paper. Questions from the same paper share chunks, vocabulary and difficulty, so they are not independent. Uncertainty therefore comes from a paired bootstrap that resamples **papers** (B = 2,000). The estimand is the query-weighted mean nDCG@10 difference between two arms on the same questions.

3. **Precision of the main paired differences (Test).**

   | Difference | Δ | 95% CI | Half-width |
   |---|---|---|---|
   | convex_prod − rrf_prod | +0.0337 | [+0.0243, +0.0431] | ±0.009 |
   | rrf_prod − dense | −0.0426 | [−0.0563, −0.0280] | ±0.014 |
   | convex_prod − dense | −0.0089 | [−0.0191, +0.0021] | ±0.011 |

   On Dev, half-widths are about ±0.012–0.018.

4. **Claim boundary.**
   - **Supported:** on QASPER Test and Dev, with production-style BM25 and the RQ4 downstream rules:
     - Convex (α = 0.7) ranks better than production RRF.
     - Production RRF ranks worse than dense-only.
     - Convex is not better than dense-only by +0.01 or more (on Test the CI upper bound is +0.002).
   - **Not supported:**
     - (a) Claims about the deployed system's absolute quality. Text comes from QASPER JSON rather than PDF extraction, parent trimming follows the RQ4 rule instead of production windowing, and production uses top-5 contexts.
     - (b) Independent confirmation. Test was already used by RQ4.
     - (c) Keyword-heavy or out-of-domain queries. QASPER is English NLP/ML only.
     - (d) The tokenization explanation beyond Dev. The decomposition is post-hoc and exploratory.
     - (e) Any end-to-end answer-quality effect.

5. **Expansion trigger.** The current sample is sufficient for the decisions made here: every decision-relevant CI lies wholly on one side of the ±0.01 thresholds. More data (a fresh, registered sample from the 527 unused Train papers) would be needed only if:
   - (i) a proposed production change, for example a tokenization fix, is evaluated on a pre-declared split and its Δ vs dense has a CI that straddles −0.01 or +0.01; or
   - (ii) the switching decision is to be stated as independently confirmed rather than post-selection.

## 6. Files

- `dev_summary.json`, `test_summary.json`: summaries, gates, statistics, latency, metadata.
- `dev_per_query.jsonl`, `test_per_query.jsonl`: per-query metrics for every arm.
- `dev_bm25_decomposition.json`: post-hoc decomposition.
