# Post-Audit Experiment Proposal

**Date:** 2026-10-29. **Status:** proposal only. Nothing below has been run.
**Inputs:**
- Audit reports in `reports/audit/`.
- Corrected RQ5 review in `eval/phases/phase_9_generation/artifacts/human_faithfulness_review/correction/`.
- The RQ2, RQ4 and RQ5 scripts and artifacts.
- The provenance registry.

## 0. What the second inspection found

The audit's findings were traced back to code. Four findings are new and change the plan:

| # | Finding | Evidence | Type |
|---|---|---|---|
| N1 | **The RQ4 arm labelled "RRF [Prod]" does not use production BM25.** The benchmark uses WordPiece tokens, a stopword list and IDF over the whole split (9,698 / 14,035 chunks). Production uses `rank_bm25.BM25Okapi` on `text.lower().split()`, no stopwords, and IDF over one document's ~35 chunks. Convex likewise was only measured with corpus-wide BM25 scores. | `evaluate_full_qasper_rq4_hybrid.py` L87–135 vs `rag_service.py` L799–906 | Protocol ≠ production |
| N2 | **RQ2's primary metrics are not budget-constrained.** nDCG@10 and Recall@20 are computed over the full ranked list of every parent (full text). The 1,600-token budget only enters the separate "budget coverage" metric. The thesis says all strategies were compared "dưới cùng ngân sách 1.600 tokens". The production parity script scores only the contexts that fit the budget (≤ 5 parents, windowed). This is the most likely main cause of 0.688 vs 0.505, but it is **not yet verified**. | `evaluate_rq2_chunking.py` L117–168 vs `verify_hierarchical_production_parity.py` L150–185 | Protocol / documentation defect |
| N3 | **The registry does not record RQ5 exposure.** The 250 RQ5 papers have empty `exposure_events` and are still flagged unexposed, so `check_experiment_overlap.py` would let a new experiment reuse them. Truly unused papers: 777 − 250 = **527 QASPER Train** (+ 8 Test papers without text evidence). | `experiment_provenance_registry.json`, e.g. `1602.00812` | Provenance defect |
| N4 | **Boolean answers are scored with Token F1** (F1 ≈ 0.00–0.04 for all models), because verbose "Yes, the paper…" answers are compared with "Yes" by token overlap. Token F1 cannot say whether a yes/no answer is correct. | `rq5_llm_generation_benchmark_500q.json` `answer_f1_by_type.boolean` | Metric validity |

The audit claim used in RQ5 was re-verified from `detailed_records`. On the 244 questions both `llama3.2:3b` and `qwen2.5:0.5b` answered, mean Token F1 is **0.3797 vs 0.3002**.

Classification of the remaining open items:
- **Measurement defects (fix):** N1, N2, N3, N4.
- **Protocol ≠ production (measure or disclose):**
  - RQ3/RQ4 use QASPER JSON text, not PDF extraction.
  - The RQ2 parity run is dense-only, while production is hybrid.
- **Dataset limitation (acknowledge):** QASPER is NLP/ML-only and English-only; the relevance labels are noisy (fresh-set precision 58%).
- **Statistical limitation (acknowledge):** the RQ5 human audit has n = 20 per model and one reviewer; RQ3 power is 38.6% at SESOI 0.03.
- **Out of scope by your instruction:** refusal-threshold calibration (keep as an uncalibrated heuristic) and RAM measurement (omit).

---

## 1. RRF vs Convex: recommendation

### 1a. Which method suits this system theoretically?

| Criterion | RRF (k = 60) | Convex (α = 0.7, per-query min-max) |
|---|---|---|
| Inputs used | Ranks only | Raw scores, min-max normalized per query |
| Calibration sensitivity | None: invariant to monotone score transforms | High. Dense cosine for e5 is compressed (~0.75–0.92) while BM25 is unbounded. Min-max stretches whatever range a query happens to have, so one outlier can dominate. |
| Effect of production's document-local BM25 | Ranks unaffected by IDF scale | With ~35 chunks, IDFs are compressed and `BM25Okapi` gives ~0 or ε-floored IDF to terms in > half the chunks. Normalized BM25 scores become unstable or all-zero for many queries, so Convex silently degrades towards dense or noise. |
| Tuning dependence | One constant, conventionally 60, rarely tuned | α must be chosen; α = 0.7 was carried over from the earlier Step 6 exploration and frozen; no α sweep was run on RQ4 Dev. Overfitting risk if retuned. |
| Robustness to distribution shift (new domains, other embedding models) | High | Lower: the right α depends on the relative informativeness and scale of both retrievers |
| Latency / complexity | Trivial; already implemented | Trivial extra arithmetic; needs both full score vectors and zero-division guards |
| Fit to the current pipeline | Implemented in `DocumentRAG.hybrid_search` | Would need code, tests and doc changes |

**Theory favours RRF** for a single-document, untuned, CPU-local system whose BM25 is computed over a few dozen chunks.

### 1b. Which method is empirically better supported?

| Evidence | Result |
|---|---|
| RQ4 Dev (276 papers) | Convex 0.5650, RRF 0.5573, Dense 0.5610; nothing significant (p_adj = 1.0) |
| RQ4 Test (408 papers) | Convex +0.0152 over Dense, CI [+0.0045, +0.0262], p_adj = 0.014; RRF +0.0008 (n.s.) |
| Production-faithful conditions | **No evidence.** Both fusions were tested only with corpus-wide WordPiece BM25 (N1) |

The empirical support for Convex is one significant, small effect (+0.015 nDCG@10, about 2.7% relative), on Test, under a BM25 that production does not use. It was not replicated on Dev.

### 1c. Recommendation

**Keep RRF in production.** Run **E1** to measure both fusions with production BM25.

Switch to Convex only if all three hold:
1. Under production-faithful BM25, Convex − RRF on Test is ≥ +0.01 nDCG@10 with a 95% CI lower bound > 0.
2. The sign agrees on Dev.
3. α in a ±0.1 neighbourhood gives a similar result on Dev (not a knife-edge).

Even then, call it a *candidate* change: Test has already been used (post-selection). A fresh confirmation (E5) would be needed before claiming it as a confirmed improvement. I will not change production code without your approval.

---

## 2. Ranked experiments

Tiers:
- **A:** < 1 h, no downloads.
- **B:** 1–3 h.
- **C:** too large or out of scope for this iteration.

All runtime estimates exclude downloads: no download is needed, because e5-small-v2, MiniLM, ModernBERT and the three Ollama models are already cached locally.

### E0 (Tier A, prerequisite, not an experiment): repair RQ5 exposure records

| Item | Detail |
|---|---|
| Motivation | N3: without it, new samples could silently reuse RQ5 papers |
| Action | Append (never overwrite) an `EXP-RQ5-MAIN-SAMPLED` exposure event to the 250 sampled papers (plus the 20 human-review papers as a sub-role); recompute the `is_unexposed…` flags; log in `audit_corrections` and the changelog |
| Check | `check_experiment_overlap.py --manifest eval_sample_manifest_500q.json` must now report these papers as exposed (by RQ5) |
| Runtime | 15 min |
| Recommendation | **Run now (required before E4/E5)** |

### E1 (Tier A): RQ4-P, fusion under production-faithful BM25

| Item | Detail |
|---|---|
| Research question | Does Convex beat RRF and Dense when BM25 is computed as production does? |
| Motivation | N1; the RRF-vs-Convex decision (§1) |
| Current evidence | RQ4 used corpus-wide WordPiece BM25 only |
| Hypothesis (H1) | With document-local whitespace BM25, the Convex gain over Dense shrinks below +0.01 nDCG@10 and Convex − RRF is not significantly > 0. Falsified if Convex − RRF ≥ +0.01 with CI lower bound > 0 |
| Dataset | Same as RQ4: Dev 276 papers / 892 q / 9,698 children; Test 408 / 1,310 / 14,035. Cached embeddings `phase_6…/artifacts/cache/*.npy` (no re-embedding). Unit: query; clusters: papers |
| Arms | Dense; RRF-bench (reproduces RQ4); **RRF-prod** (`BM25Okapi`, `lower().split()`, per-paper index, top-50 per list, k = 60, exactly as `hybrid_search`); Convex-bench (reproduces RQ4); **Convex-prod** (α = 0.7 frozen, per-paper BM25). Dev only, descriptive: Convex-prod α ∈ {0.5, 0.6, 0.7, 0.8, 0.9} |
| Downstream | Unchanged from RQ4: parent expansion, ≤ 5 parents, 1,600-token budget, τ = 0.50 |
| Primary metric (pre-declared) | nDCG@10 over the budgeted parent list (the RQ4 definition, so results are comparable) |
| Secondary | nDCG@4, MRR@10, Recall@20 (capped by ≤ 5 parents; reported for comparability only), Hit@5, fusion latency per query (ms, `perf_counter`, fusion step only) |
| Statistics | Paper-cluster paired bootstrap, B = 2,000, seed 42. Inferential family on Test: {RRF-prod vs Dense, Convex-prod vs Dense, Convex-prod vs RRF-prod}, Holm m = 3. Dev and the α sweep are descriptive |
| Gate | RRF-bench and Convex-bench must reproduce RQ4 Test nDCG@10 (0.5662 / 0.5806) to 4 decimals before the new arms are interpreted |
| Runtime | Setup/coding 25 min; Dev + Test execution ≈ 10 min; analysis/report 20 min; **≈ 1 h** |
| Compute | CPU only; < 2 GB RAM; no downloads |
| Outputs | `eval/phases/phase_6_hybrid_retrieval/artifacts/rq4p_production_fusion/` (protocol.md, config.json, per_query.jsonl, summary.json, stats.json, report.md, α-sweep plot); new script `scripts/evaluate_rq4p_production_fusion.py` |
| Decision rule | See §1c. If not met, keep RRF and report Convex's RQ4 gain as benchmark-specific |
| Risks | Test is already exposed, so this is a **post-selection diagnostic**, not confirmation (registered as such). Production BM25's IDF floor behaviour is reproduced by using `rank_bm25` itself |
| Recommendation | **Run now** |

### E2 (Tier B): RQ2-P, chunking under an equal budget and production retrieval

| Item | Detail |
|---|---|
| Research question | (a) Under the same budgeted context and the same retrieval, does `hierarchical` give the LLM more evidence than flat chunking? (b) How much of 0.688 vs 0.505 is explained by budget truncation and windowing? |
| Motivation | N2; audit finding R5; the thesis claim "dưới cùng ngân sách 1.600 tokens" |
| Current evidence | RQ2 scores unbounded lists of full parents; parity scores budgeted windowed contexts. The two are not comparable |
| Hypothesis (H2a) | Hierarchical has higher evidence coverage within 1,600 tokens than `section_overlap`, with a smaller margin than RQ2 suggested (Δ coverage < +0.10). (H2b) Budget truncation accounts for most of the nDCG@10 gap |
| Dataset | The same 47 Dev papers / 127 questions as RQ2 (PDF → `extract_sections_from_pdf`, as RQ2). Exposed (RQ1/RQ2), so exploratory |
| Strategies | `fixed_size` (RQ2 baseline), `section_overlap`, `hierarchical` (production parameters) |
| Conditions | U = unbounded full-parent list (reproduces RQ2); B = budget-truncated list (1,600 tokens, ≤ 5 parents); B+W = budget + production windowing (±200 words when parent > 800 tokens). Retrieval: dense exact (as RQ2) **and** production hybrid RRF (production BM25) |
| Primary metric (pre-declared) | **Evidence coverage@1600** = 1 if the concatenated assembled context (in rank order, up to 1,600 tokens) contains ≥ τ = 0.50 of the evidence's content words. This is unit-invariant, so chunks and parents are judged on the same text the LLM would receive |
| Secondary | nDCG@4 and nDCG@10 in conditions U and B (labelled by condition), MRR@10, tokens actually used, retrieval latency |
| Statistics | Paper-cluster paired bootstrap B = 2,000; inferential family under B+W with hybrid retrieval: {hierarchical vs section_overlap, hierarchical vs fixed_size}, Holm m = 2. Everything else descriptive; the gap decomposition is reported as a table, not tested |
| Gate | Condition U with dense retrieval must reproduce RQ2's nDCG@10 for the three strategies (0.6880 / 0.5409 / 0.5654) within ±0.002 |
| Runtime | Coding 30 min; embedding ≈ 5.1k chunks at ~6.5 chunks/s ≈ 13 min; scoring 5 min; analysis 25 min; **≈ 1.25 h** |
| Compute | CPU, e5 cached, < 3 GB RAM |
| Outputs | `eval/phases/phase_2_chunking/artifacts/rq2p_budget_parity/` (same file set as E1); script `phase_2_chunking/scripts/evaluate_rq2p_budget_parity.py` |
| Decision rule | H2a supported if Δ coverage > 0 with CI excluding 0; weakened if CI includes 0 (then the thesis must say hierarchical's advantage under an equal budget is not established); H2b supported if condition B reduces the hierarchical − section_overlap nDCG@10 gap by ≥ 50% |
| Risks | Containment labels are noisy (fresh precision 58%), equally for all arms; 47 papers give wide CIs (expect about ±0.06 on coverage differences); exploratory data |
| Recommendation | **Run now** |

### E3 (Tier A): RQ5-R, re-analysis of stored generations (no new inference)

| Item | Detail |
|---|---|
| Research question | What can the stored 1,500 generations and 60 corrected labels support about 3b vs qwen vs 1b? |
| Motivation | Model-selection argument; N4; your request to verify the 244-question figures |
| Sufficiency check | Stored `detailed_records` contain prediction, references (all annotators), type, refusal flag, F1, latency and tokens/s per question and model; the corrected review has labels per answer. **No new inference is needed** |
| Analyses (pre-declared) | (1) Recompute F1, refusal rate, containment and latency from records (reproduction). (2) Paired paper-clustered bootstrap CIs for refusal-rate differences. (3) Conditional answered-by-both F1 (3b vs qwen: n = 244; also 3b vs 1b) with paired bootstrap CI, plus a **selection check**: compare question-type mix and qwen's F1 on questions 3b refused vs answered; label it explicitly as conditional and selection-affected. (4) **Boolean accuracy** (new metric): normalize the prediction, take the first yes/no token (or a "no"/"not" polarity rule if no leading token); correct if it equals the majority annotator yes/no; refusals counted as incorrect; report unparseable answers separately. (5) Human review recomputed from `faithfulness_annotations_unblinded_corrected.csv`: counts, Wilson 95% intervals, and an exact paired sign test on per-question discordance for "unsupported or contradicted" (3b vs qwen), labelled exploratory |
| Primary metric | Unchanged (Token F1, paper-level paired t + Holm, already reported). Items (2)–(5) are explicitly secondary/descriptive |
| Hypotheses | H3a: 3b's conditional F1 advantage over qwen persists with a CI excluding 0. H3b: Boolean accuracy differs from the Boolean F1 ranking (that is, F1 mis-measures yes/no answers) |
| Runtime | **≈ 45 min**, CPU only |
| Outputs | `eval/phases/phase_9_generation/artifacts/rq5r_reanalysis/` (script, per_question.jsonl, summary.json, report.md) |
| Decision rule | If the conditional CI includes 0, the thesis drops the "higher quality when it answers" phrasing and keeps only the refusal-rate explanation |
| Risks | The conditional analysis is selection-biased (models refuse different questions); the Boolean parser can mis-parse, so disagreements on a 30-item sample are spot-checked manually and the parse-failure rate is reported |
| Recommendation | **Run now** |

### E4 (Tier B, optional, needs explicit approval): RQ6-lite, production-pipeline pilot for the default model

| Item | Detail |
|---|---|
| Research question | How much does answer quality of the production configuration (e5 + hierarchical + production RRF + `llama3.2:3b`) drop when the context comes from retrieval instead of gold evidence? |
| Motivation | The thesis has **no end-to-end evidence**; RQ5 is gold-evidence only |
| Dataset | New registered sample from the 527 unused Train papers: K = 50 papers, m = 2 → 100 questions, same eligibility rules and seed procedure as RQ5. Text = QASPER JSON sections (not PDF; disclosed) |
| Conditions (paired, same questions) | G = gold evidence (RQ5 prompt); R = production retrieval context (top-5 budgeted parents from `DocumentRAG`-equivalent code, including the 0.80 refusal gate recorded as a separate outcome) |
| Primary metric | Paper-level paired Token F1 difference R − G |
| Secondary | Refusal rate (model and gate separately), evidence coverage@1600 of R contexts, end-to-end latency (retrieval + generation), Boolean accuracy |
| Statistics | Paper-cluster paired bootstrap CI; expected precision about ±0.05 for the F1 difference (SD of paper-level differences ~0.18, K = 50). Descriptive pilot, not full RQ6 |
| Runtime | Sampling + registry 15 min; chunk/embed ~1.7k chunks ≈ 5 min; 200 generations × ~7.6 s ≈ 25 min; analysis 30 min; **≈ 1.5–2 h** |
| Compute | Ollama `llama3.2:3b` (installed), CPU |
| Risks | Small sample; uses 50 of 527 reservoir papers (leaves 477 for full RQ6); PDF extraction not exercised; 1 embedding × 1 LLM only, so it must be reported as an "RQ6 pilot", not RQ6 |
| Recommendation | **Run if you want any end-to-end evidence in the thesis**; otherwise keep RQ6 fully as future work |

### E5 (Tier C, defer): fresh confirmatory fusion comparison

To detect Δ ≈ 0.015 with ~80% power needs roughly the Test-scale sample (≈ 400 papers), which would consume most of the remaining reservoir and ~3 h with embedding. **Defer** unless E1 meets the §1c switch criteria.

### Tier C: not this iteration

| Item | Reason |
|---|---|
| Full RQ6 (3 embeddings × 3 LLMs) | ≥ 6–8 h inference + preparation |
| Refusal-threshold calibration | Out of scope by instruction; keep τ = 0.80 as an uncalibrated heuristic |
| RAM measurement | Out of scope by instruction; omit RAM claims |
| Second human reviewer / larger faithfulness audit | Needs a person; propose as future work |
| New datasets (below) | Weeks of adaptation for the single-document QA protocol |

---

### Requirement for every experiment report (added 2026-10-29 at your request)

Each report (E1, E2, E3) ends with a **Dataset adequacy** section covering:
1. Usable sample size after exclusions: papers, queries, answerable queries, and relevant-evidence cases.
2. The independent unit for uncertainty (queries, papers or reviewed answers) and why.
3. Confidence intervals for the main paired differences.
4. The claim boundary: what the data supports and what it cannot establish.
5. An expansion trigger: the result that would make the sample insufficient.

Status:
- **E1:** completed and included in `eval/phases/phase_6_hybrid_retrieval/artifacts/rq4p_production_fusion/REPORT.md` §5.
- **E2, E3:** pending.

---

## 3. Alternative datasets (investigated, not recommended this iteration)

Licence details must be verified before any use. They are listed here as I understand them, not as confirmed facts.

| Dataset | Task / evidence | Fit to this thesis | Verdict |
|---|---|---|---|
| SciFact | Claim verification over ~5k abstracts, with rationale sentences | Already used as an RQ3 sanity check. Corpus-level abstract retrieval, not single-document QA; useful only for embedding external validity | Keep as-is; no new work |
| QASA (2023) | QA over full CS papers, with evidence | Closest to QASPER; same domain, so little gain in external validity | Possible future work after licence and format check |
| PeerQA (2025) | Questions from peer reviews, with evidence in papers | Broader disciplines, but needs PDF-to-evidence alignment | Future work |
| BioASQ / PubMedQA | Biomedical QA | Different domain (external validity ↑), but different task formats (abstract-based, yes/no) | Future work; would need a separate protocol, not pooling |

Adding any of them now would mainly add work. External validity is better handled as an explicit limitation (QASPER: English NLP/ML papers) this iteration.

---

## 4. Thesis changes

Detailed in [`THESIS_REWRITE_PLAN.md`](THESIS_REWRITE_PLAN.md). In brief:
- **Without experiments:** RAM removal, threshold wording, the RQ2 budget-metric disclosure, the RQ4 BM25 disclosure, and the RQ5 Boolean-metric caveat.
- **After E1/E2/E3 (and optionally E4):** new evidence in §5.3, §5.5, §5.6, §5.7, §5.8, Chapter 6 and the abstract.

## 5. Other follow-ups (outside the experiment budget)

- **PDF licence:** `sample_documents/[2021 5th IEEE … Anna's Archive].pdf` is an IEEE paper with a shadow-library filename. It is almost certainly not redistributable. Remove it from the repository (and its git history) before any publication. It is not used by any test.

## 6. Approval checkpoints

1. **E0** registry repair: approve?
2. **E1, E2, E3** (Tier A/B, ≈ 3 h of work in total): approve as specified, or with changes?
3. **E4** RQ6-lite pilot (≈ 1.5–2 h, uses 50 reservoir papers): run or skip?
4. **RAM scope:** remove *all* RAM figures (including the RQ1/RQ3 Python-process RSS, which *was* measured with `psutil`), or only the unmeasured LLM/Ollama figures? Your instruction reads as "all"; the plan assumes **all** unless you say otherwise.
5. **Production change:** none now. Revisit RRF → Convex only if E1 meets §1c.
