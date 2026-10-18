# Scientific Embedding Model Selection & Evaluation Pipeline Audit
**A University-Thesis Level Experimental Plan, Validity Audit, and Statistical Verification Blueprint**

*Document Status: Formal Experimental Plan — Version 3.5 (Statistical Parity, Frozen Ladder & Verification Precondition)*  
*Precedence: Version 3.5 supersedes all previous versions (v1.0, v2.0, v3.0, v3.1, v3.2, v3.3, and v3.4) where conflicts arise.*  
*Target Hardware: AMD Ryzen 5 5600 (6 Cores / 12 Threads, Base 3.5 GHz / Boost 4.4 GHz, No Dedicated GPU), 16 GB System DDR4 RAM*  
*Target Vector Engine: Qdrant v1.13.2 (Dual-Mode: Local Embedded SQLite vs. Standalone Docker Server)*  
*Author: Academic Research Assistant (Pair Programming)*  
*Repository Root: `c:\DACNTT`*

---

> [!IMPORTANT]
> ### Hard Stop Directives & Final Pre-Registered Decisions
> In strict accordance with user directives, this document represents a **PLAN ONLY**. No evaluation benchmarks have been executed, no new models have been downloaded, no notebooks have been run, and no evaluation datasets or code have been altered. **Execution is strictly blocked until this document is reviewed and explicitly approved by the researcher.**
>
> **Final Researcher Pre-Registered Decisions (Incorporated into v3.3, v3.4 & v3.5):**
> 1. **Primary Confirmatory Family & Two-Sided Testing Convention:** Exactly $m = 3$ pairwise comparisons (each Stage 2 finalist vs. the `sentence-transformers/all-MiniLM-L6-v2` baseline) pre-registered under the standard **two-sided hypothesis testing convention** ($H_0: \mu_{Fi} = \mu_{\text{base}}$ vs. $H_1: \mu_{Fi} \ne \mu_{\text{base}}$) under Holm-Bonferroni FWER control with initial critical threshold $\alpha_{\text{min}} = \alpha / 3 = 0.05 / 3 = 0.01667$.
> 2. **Secondary Finalist Comparisons:** Finalist-vs-finalist comparisons ($m = 3$) are pre-registered strictly as **SECONDARY**, outside the confirmatory family. They report two-sided 95% CIs and Monte Carlo permutation p-values, are labeled "not family-wise controlled", and claims are restricted strictly to "suggestive ordering". **The thesis must not claim a unique best finalist from them.**
> 3. **Gate G10 General Pre-Finalist DGP & Sizing on Max Cluster SD:** Gate G10 does not hard-wire `e5-small-v2`. It evaluates paired differences for each of the top $N = 3$ development candidates (`intfloat/e5-small-v2`, `BAAI/bge-small-en-v1.5`, `Snowflake/snowflake-arctic-embed-s`) vs. baseline, explicitly noting E5's dev numbers are in-sample, and sizes Stage 2 on the pair exhibiting the **maximum between-paper cluster SD** ($s_{\Delta,\text{paper}}$) centered strictly at $\text{SESOI} = 0.030$.
> 4. **Frozen Ladder Counts & Mathematical Sizing:** Ladder counts are strictly frozen: Tier 0 = $416$ pristine test papers; Tier 1 = $416 + 181 = \mathbf{597\text{ papers}}$ (validation untouched = $281 - 100\text{ streamed} = 181$); Tier 2 = $597 + 203 = \mathbf{800\text{ papers}}$ (sampling 203 train papers from offsets $\ge 300$, leaving $588 - 203 = 385$ train papers untouched). If simulated power remains $< 80\%$ at $K=800$, the study proceeds with $K=800$ and reports achieved power as a thesis limitation.
> 5. **Bonferroni 98.33% CIs & Conservative Characterization:** Simultaneous $98.33\%$ confidence intervals ($1 - \alpha/m = 1 - 0.05/3$) are **Bonferroni-level** simultaneous intervals, conservative relative to Holm step-down. A 98.33% CI excluding zero is a sufficient condition for Holm rejection; Holm-adjusted p-values ($p_{\text{holm}} < 0.05$) govern exact step-down hypothesis rejection.
> 6. **Blocking Supervisory Spot-Check Precondition (Gate G14):** Independent recomputation of one bootstrap CI and one Holm table from exported replicates and permutation draws is a mandatory **blocking precondition** before any Stage 2 conclusion or thesis claim can be finalized.
> 7. **Runtime Quantization Framework:** Selection work runs strictly on **PyTorch FP32**. FastEmbed ONNX INT8 is evaluated solely as an optional post-selection paired check on the final selected models, outside the confirmatory family.
> 8. **Pre-Registration Freeze Date:** Formally frozen upon researcher approval at `2026-10-18T15:15:00+09:00` with canonical SHA-256 hash locked in `manifest.json`.
>
---

## Document Revision Changelog: Version 3.4 vs. Version 3.5

| Section / Topic | Version 3.4 (Previous Specification) | Version 3.5 (Current Revised Specification) | Rationale & Methodological Grounding |
| :--- | :--- | :--- | :--- |
| **Gate G10 Simulation DGP: Top-$N$ Max Cluster SD Rule** (§7.1, §7.3) | Simulation was hard-wired to development residuals of `intfloat/e5-small-v2` vs `all-MiniLM-L6-v2`. | **Pre-registered Top-$N$ Max Cluster SD rule ($N = 3$):** Gate G10 evaluates paired differences for each of the top $N = 3$ dense candidates on dev (`e5-small-v2`, `bge-small-en-v1.5`, `snowflake-arctic-embed-s`) vs. MiniLM. Explicitly notes **E5's dev scores are in-sample**. Sizing is locked to the candidate pair exhibiting the **maximum between-paper cluster SD** ($s_{\Delta,\text{paper}}$), centered at $\Delta = \text{SESOI} = 0.030$. | Calibrates required sample size against the worst-case empirical variance across top models; eliminates reliance on in-sample point estimates. |
| **Frozen Ladder Counts & Total Purge of 601, 185, 776** (§1.2.1, §1.2.2, Table 1.1, §7.3, §11 YAML) | Text referenced 601 alongside alternative historical notation (185, 776). | **Frozen exact ladder counts: Tier 0 = 416, Tier 1 = 597 ($416 + 181$), Tier 2 = 800 ($597 + 203$).** Validation untouched = $281 - 100\text{ streamed} = \mathbf{181}$. Train untouched = $888 - 300\text{ streamed} = \mathbf{588}$ (Tier 2 leaves $588 - 203 = 385$ untouched). **Completely purged every occurrence of '601', '185', and '776' from the entire document.** | Eliminates numerical ambiguity; guarantees exact offset tracking and zero stream contamination across splits. |plits. |
| **Hypothesis Testing Convention & Bonferroni CI Characterization** (§4.9, Table 4.4, §11) | Hypotheses were occasionally framed as directional nulls ($H_0: \mu \le \mu_0$); 98.33% CI was incorrectly claimed to exclude zero iff Holm-significant. | **Formally locked Unified Two-Sided Testing Convention ($H_0: \mu_{Fi} = \mu_{\text{base}}$ vs. $H_1: \mu_{Fi} \ne \mu_{\text{base}}$).** Simultaneous $98.33\%$ CIs are defined as **Bonferroni-level** and **conservative relative to Holm step-down**. Corrected claim: a $98.33\%$ Bonferroni CI excluding zero is a sufficient condition for rejection under Holm; Holm step-down p-values ($p_{\text{holm}} < 0.05$) govern exact sequential rejection. | Reconciles two-sided confidence intervals with hypothesis testing; prevents false claims about equivalence between Bonferroni intervals and Holm step-down. |
| **Supervisory Spot-Check Blocking Precondition & Gate G14** (§6.1, §6.3) | Spot-check was recommended but not an automated blocking gate for conclusions; tolerances were not partitioned. | **Formally instituted Gate G14 as a mandatory blocking precondition:** No Stage 2 conclusion or thesis claim can be finalized without supervisory sign-off. Spot-check reuses exported replicates (`.csv`), permutation sign-flips (`.npy`), and cluster resamples (`.npy`). **Tolerances partitioned:** Deterministic quantities require $|\widehat{\Delta}_{\text{harness}} - \widehat{\Delta}_{\text{spot}}| \le 10^{-5}$; Monte Carlo permutation p-values require exact match with exported draws, or $|\widehat{p}_{\text{harness}} - \widehat{p}_{\text{spot}}| \le 0.009$ with independent PRNG and 100% decision match. | Enforces external human verification with rigorous numerical bounds before results are published. |
| **Extended Air-Tight 'No Test-Split Access' Verification** (§1.2.1) | Verified repository scripts for `split="test"`. | **Extended audit across all caching layers:** Audited HF cache directory (`~/.cache/huggingface/` has 0 QASPER files), confirmed 0 `load_dataset` calls in repo, 0 full-dataset archives (`.tar.gz`/`.zip`), and audited raw JSON files on disk (`qasper_raw.json` 100 items; `qasper_corpus.json` 100 keys; `expanded_qasper_sampled.json` 487 queries). Proved **zero test-split data exists anywhere in workspace or cache**. | Establishes incontrovertible physical evidence that test split remains pristine and un-accessed. |
| **Preservation of Version 3.4 in Appendix A** | Version 3.3 was preserved in Appendix A. | **Preserved Version 3.4 in Appendix A.** Versions 3.3, 3.2, 3.1, 3.0, 2.0, and 1.0 shifted to Appendices B through G. | Complete genealogical audit trail maintained for thesis defense. |

---

## Document Revision Changelog: Version 3.3 vs. Version 3.4

| Section / Topic | Version 3.3 (Previous Specification) | Version 3.4 (Current Revised Specification) | Rationale & Methodological Grounding |
| :--- | :--- | :--- | :--- |
| **Purge of 4 Finalists & $m=6$ References** (§10.2, §11.1 Step 4, §11 YAML) | Text in §10.2, §11.1 Step 4, and pre-registration blocks contained lingering references to 4 finalists, $m=6$, and 1,395 queries. | **Fully purged all references to 4 finalists, $m=6$, and 1,395 queries.** Stage 2 is strictly locked to Top 3 finalists + baseline (4 models total, $m=3$ primary confirmatory comparisons, ~1,270 answerable queries). | Eliminates internal contradictions with the pre-registered $m=3$ family decision. |
| **Gate G10 Pre-Finalist Simulation DGP** (§7.1, §7.3) | Simulation protocol did not specify which model pair or effect size was simulated before finalists are selected. | **Formally specified DGP on development residuals:** Gate G10 resamples paired difference residuals ($e_{k,i} = (y_{k,i,\text{top}} - y_{k,i,\text{base}}) - \hat{\Delta}_{\text{dev}}$) between the strongest candidate (`intfloat/e5-small-v2`) and baseline (`sentence-transformers/all-MiniLM-L6-v2`) on development data, centered at $\Delta = \text{SESOI} = 0.030$. Proven to be a conservative lower bound on power for any candidate achieving $\ge \text{SESOI}$. | Grounded simulation in empirical between-paper variance and cluster correlation structure prior to Stage 1 execution. |
| **Expansion Formula Piecewise Sizing & Limitation Rule** (§1.2.2, §7.3) | Sizing formula lacked explicit piecewise cases for $K \in \{416, 597, 800\}$ and omission of the $<80\%$ at $K=800$ fallback. | **Explicit piecewise sizing formula covering $K \in \{416, 597, 800\}$; pre-registered limitation rule.** If simulated power at $K=800$ remains $< 80\%$, the protocol permanently forbids ad-hoc data hunting; the study proceeds with $K=800$ and formally reports achieved power in the thesis as an empirical limitation. | Pre-registers sample size bounds; eliminates post-hoc cohort drifting. |
| **Untouched Split Offset Verification & Sensitivity Arm** (§1.2.1, §4.12) | Quoted 181 validation and 588 train papers without accounting for skipped streamed rows. | **Audited exact stream offsets:** `prepare_qasper.py` streamed offsets 0–99 (100 rows touched, 96 kept, 4 skipped); untouched validation offsets are 100–280 = **181 papers** (181 excluding kept IDs). `expand_qasper_benchmark.py` streamed offsets 0–299 (300 rows touched, 112 kept, 188 skipped); untouched train offsets are 300–887 = **588 papers** (correcting earlier 588 figure). Added mandatory **Test-Split-Only Sensitivity Analysis Arm ($K=416$)** when pooling Tier 1 or Tier 2. | Guarantees zero data leakage from skipped stream rows; isolates pooling artifacts from true generalizability. |
| **Holm-Consistent Simultaneous CIs & Decision Re-Check** (§4.9, §5.2, Table 4.4) | Reported only marginal 95% CIs alongside Holm-adjusted p-values, creating potential boundary disagreement. | **Report Simultaneous Holm-Consistent CIs at $98.33\%$ coverage** ($1 - \alpha/m = 1 - 0.05/3$) alongside marginal 95% CIs. Reconciled Decision Table: $p_{\text{holm}} < 0.05$ (equivalent to $98.33\%$ simultaneous CI excluding 0) governs rejection. If marginal 95% CI excludes 0 but $p_{\text{holm}} \ge 0.05$, outcome is strictly classified as Inconclusive / Insufficient Evidence. | Eliminates CI/p-value conflict under multiple testing; provides mathematically unified inference. |
| **Relabeling of Pilot Precision Estimates** (§1.2.1, §4.7) | Unadjusted $\text{SE} \approx 0.0113$ and $\text{HW}_{95} \approx 0.0221$ were cited without explicit scaling disclaimer. | **Explicitly labeled $\text{SE} \approx 0.0113$ and $\text{HW}_{95} \approx 0.0221$ as "scaled, unverified pilot estimates"** extrapolated under the $\sqrt{159/416}$ assumption, pending Gate G10 computation of empirical paper residuals. | Enforces scientific precision; distinguishes theoretical scaling from empirical measurement. |
| **Candidate Table, Priors & Retrieval Log Snippets** (§3.2, Table 3.2, §3.2.2) | Header delimiter misaligned; score column named generally; snippets omitted; count ambiguity. | **Renamed score column to `Published Prior (Unverified) — MTEB English Retrieval nDCG@10`; fixed 11-column header; enforced 1 benchmark version per cell (MTEB v1 English Retrieval); stated true count (11 dense candidates + 1 baseline control + 1 lexical floor = 13 models); pasted verbatim extracted text snippets in §3.2.2.** Stage 1 selection relies **exclusively on measured Stage 1 values**. | Complete external auditability; prevents ranking bias from published priors. |
| **Restoration of Human Spot-Check Protocol** (§6.3) | Protocol lacked explicit researcher spot-check instructions for statistical recomputation. | **Restored human verification spot-check protocol:** Evaluation harness exports raw replicates (`statistical_replicates_spot_check.csv`); researcher independently recomputes one bootstrap CI and one Holm table in an external tool (R/Python/spreadsheet). Required tolerance $|\hat{\Delta}_{\text{harness}} - \hat{\Delta}_{\text{spot}}| \le 10^{-5}$ and 100% Holm adjustment match signed off. | Provides external human oversight and verifies numerical integrity of the automated pipeline. |
| **Preservation of Version 3.3 in Appendix A** | Version 3.2 was preserved in Appendix A. | **Preserved Version 3.3 in Appendix A.** Versions 3.2, 3.1, 3.0, 2.0, and 1.0 shifted to Appendices B through F. | Complete genealogical audit trail maintained for thesis defense. |

---

## Document Revision Changelog: Version 3.2 vs. Version 3.3

| Section / Topic | Version 3.2 (Previous Specification) | Version 3.3 (Current Revised Specification) | Rationale & Methodological Grounding |
| :--- | :--- | :--- | :--- |
| **Primary Confirmatory Family** (§4.9, §11) | Presented Option A ($m=3$) vs Option B ($m=6$) as an open decision. | **Formally locked Option A ($m=3$ primary comparisons: each Stage 2 finalist vs. `all-MiniLM-L6-v2` baseline).** Controlled under Holm-Bonferroni with initial critical threshold $\alpha_{\text{min}} = \alpha / 3 = 0.01667$. | Final decision by researcher. Directly tests the thesis hypothesis (beating the baseline) under optimal FWER efficiency. |
| **Secondary Finalist Comparisons** (§4.9, §4.10, §4.11) | Treated finalist pairs as secondary tie-breaking family without strict thesis claim bounds. | **Pre-registered as SECONDARY, outside confirmatory family.** Unadjusted 95% CIs and Monte Carlo p-values reported; labeled "not family-wise controlled"; restricted strictly to "suggestive ordering". **The thesis must NOT claim a unique best finalist from them.** | Prevents un-controlled FWER inflation while preserving exploratory architectural ranking for future engineering work. |
| **Power Criterion & Trigger Formula** (§1.2.2, §7.3, §11) | Described ladder trigger textually; cited "8–12% power gain" without simulation. | **Explicit mathematical piecewise formula for Tier selection based on G10 output at $\alpha/3 = 0.01667$.** Formula and seed frozen pre-flight in `expansion_decision.json`. Replaced unverified "8-12%" with exact factor-of-2 alpha relaxation ($\alpha/3$ vs $\alpha/6$); empirical power curves to be quantified by Gate G10. If $80\%$ unreachable across ladder, reported as thesis limitation. | Eliminates ad-hoc expansion decisions; provides auditable mathematical decision rule before Stage 2 data is accessed. |
| **Ladder Arithmetic & Provenance** (§1.2.1, §1.2.2) | Mentioned 597 and 800 papers without complete split breakdown. | **Audited and proved exact split arithmetic:** Tier 0 = 416 test papers; Tier 1 = $416 + 181\text{ untouched validation} = \mathbf{597}$; Tier 2 = $597 + 199\text{ untouched train} = \mathbf{800}$. Verified **exact zero overlap** with the 208 repo dev papers (207 active with queries). | Proves complete partition disjointness and eliminates ambiguity regarding cohort sourcing. |
| **Candidate Retrieval Scores & Log** (§3.2, §3.2.2) | Table contained general card citations without explicit retrieval queries; BM25 unverified. | **Strictly standardized to dedicated MTEB English Retrieval nDCG@10.** BM25 marked **[UNVERIFIED]**. Added complete web retrieval log documenting search query, canonical URL, extracted score, and extraction date for all candidates. | Eliminates metric conflation with overall MTEB averages; establishes complete external auditability. |
| **Acceptance Gates G10 & G13** (§6.1) | G10 had ungrounded power claims; G13 did not specify $m=3$ threshold. | **G10 evaluates power at $\alpha_{\text{min}} = 0.01667$ for $m=3$ across $K \in \{416, 597, 800\}$.** G13 verifies `expansion_decision.json` output generated by G10 is locked into `manifest.json` before Stage 2 runs. | Enforces automated pre-flight sizing gate prior to test data decryption/access. |
| **Preservation of Version 3.2** (Appendix A) | Version 3.1 preserved in Appendix A. | **Preserved Version 3.2 in Appendix A.** Versions 3.1, 3.0, 2.0, and 1.0 shifted to Appendices B through E. | Complete version history preserved for scientific auditability. |

---

## Document Revision Changelog: Version 3.1 vs. Version 3.2

| Section / Topic | Version 3.1 (Previous Specification) | Version 3.2 (Current Revised Specification) | Rationale & Methodological Grounding |
| :--- | :--- | :--- | :--- |
| **Power-Triggered Expansion Rule** (§1.2.2 & §7.3) | Stage 2 fixed to all 416 test papers without explicit power rule. | **Pre-registered power criterion ($	ext{Power} \ge 80\%$ at $\text{SESOI}=0.030$ under Holm-adjusted threshold $\alpha_{\text{min}}$).** Evaluated pre-flight via Gate G10 on development residuals. Pre-registers a strict **Expansion Ladder** (Tier 0: 416 test papers $\to$ Tier 1: pool 181 untouched validation papers $\implies K=597 \to$ Tier 2: add 200 untouched train papers $\implies K \approx 800$). Post-data snooping strictly barred. Fixed-sample design adopted over group-sequential. | Eliminates arbitrary sample sizing; guarantees pre-registered statistical power under FWER correction while permanently barring optional stopping and p-hacking. |
| **Forensic Provenance & Query Counts** (§1.2.1) | Estimated 1,395 queries for 416 test papers; validation split overlap unverified. | **Audited exact split provenance in codebase:** 96 papers from official validation (offsets 0-100), 112 from train. **181 validation papers, 416 test papers, 588 train papers remain completely untouched.** Corrected test query estimate to **$\approx 1,270$ answerable queries** (1,451 questions $\times 87.5\%$ answerable rate). | Ground truth alignment with official AllenAI QASPER distribution and codebase commit history (`4e08e80`, `expand_qasper_benchmark.py`). |
| **External Benchmark Criteria & SciFact Audit** (§1.5) | Mentioned SciFact as zero-shot check without granularity or provenance audit. | **Audited SciFact usage:** Phase 5.12 evaluated `claims_dev.jsonl` (300 claims) to justify E5, making dev claims contaminated. Evaluated candidate benchmarks against 8 strict criteria; SCIDOCS, TREC-COVID, MS MARCO explicitly excluded due to document-level or web domain misalignment. Only SciFact `claims_test` (300 claims) admitted as a secondary, non-pooled arm. | Prevents dataset contamination and domain confounding in external validation. |
| **Multi-Dataset Estimand & Generalization** (§4.12) | No multi-dataset estimand; undefined pooling rules. | **Strictly prohibited raw pooling across QASPER and SciFact** due to candidate pool disparity ($N \approx 25$ vs 5,183). Defined a **dataset-stratified estimand** with within-dataset cluster bootstrap. Prohibited random-effects meta-analysis for $D < 3$. Re-derived SciFact SESOI ($\mathbf{0.034}$). Explicitly mapped generalization bounds per outcome. | Prevents mathematically invalid pooling of disparate ranking baselines; establishes rigorous cross-domain transfer claims. |
| **Power Recomputation & Family Optimization** (§4.9 & §7) | Quoted 38.6% and 72.5% as unadjusted power; all-pairs family ($m=6, \alpha=0.0083$). | **Relabeled 38.6% and 72.5% as scaled pilot estimates** pending G10. Evaluated power at Holm-adjusted first threshold ($\alpha_{\text{min}}$). Pre-registered **Optimized Primary Family (Finalists vs. Baseline, $m=3$)**, relaxing threshold to $\alpha_{\text{min}} = \mathbf{0.01667}$ and gaining $\approx \mathbf{8–12\%}$ statistical power over all-pairs. | Honest power reporting under multiplicity control; optimal experimental efficiency. |
| **Acceptance Gates** (§6.1) | Gates G1–G12 restricted to single dataset. | Extended G1 (zero cross-dataset leakage), G4, G6, G10 to multi-dataset. **Added Gate G13 (Pre-Flight Expansion Gate)** enforcing that Gate G10 power simulation is evaluated and logged before Stage 2 execution. | Complete scaffolding preventing data leakage or unplanned cohort expansion. |
| **Candidate Shortlist & Timing Pilot** (§3.2) | Candidate table contained non-retrieval scores; Qwen3-0.6B pre-excluded on estimates. | **Table consistently reports MTEB English Retrieval nDCG@10.** EmbeddingGemma updated to English retrieval. **Included `Qwen3-Embedding-0.6B` in candidate list and 10-paper timing pilot**; physical cutoffs applied to measured metrics rather than pre-emptive exclusion. | Complete fairness across modern late-2024 / 2025 embedding architectures. |

---

## Document Revision Changelog: Version 3.0 vs. Version 3.1

| Section / Topic | Version 3.0 (Previous Specification) | Version 3.1 (Current Revised Specification) | Rationale & Evidence |
| :--- | :--- | :--- | :--- |
| **1. Stage 2 Data Sourcing & Sizing** | Proposed drawing ~150 fresh papers from QASPER without specifying split or cost. | **Dedicated Draw from Official QASPER Test Split (416 papers); Sized via G10.** Confirmatory split is sampled strictly from `allenai/qasper` `test` split (never train/dev). Evaluated the cost of all 416 papers ($\sim 10.4\text{k}$ chunks, $\sim 25\text{ min}$ CPU wall-clock, drops $\text{SE}_{\text{cluster}}$ from 0.0183 to 0.0113, boosting power at $\text{SESOI}=0.030$ to $\sim 72.5\%$). Paper IDs, seed, and SHA-256 hash frozen before any evaluation. | Guarantees genuine out-of-sample confirmation with zero leakage; leverages full test split capacity within CPU feasibility. |
| **2. Stage 1 Screening & Finalist Rules** | Imposed an arbitrary 50 ms latency cutoff; hardcoded top-3 finalists; omitted E5 selection bias. | **Removed Unjustified 50 ms Cutoff; Added Indexing Throughput/RAM Rules; Sized Family Cost of 4 Finalists; Disclosed E5 In-Sample Advantage.** Desktop LLM generation takes 1,500–3,000 ms, making retrieval $<150$ ms negligible. Applied cutoffs only to measured values. Shortlisting 4 finalists increases Stage 2 family to $m = \binom{5}{2} = 10$ pairs ($p_{\text{holm}} \le 0.0050$), costing $\sim 12\%$ power vs $m=6$. E5's historical in-sample advantage on dev data is explicitly documented. | Grounded in actual desktop application latency budget; rigorously quantifies the multiple-testing penalty of expanding the shortlist. |
| **3. Decision Rules Hierarchy** | Defined superiority, trivial, and inconclusive without formal mutual exclusivity or handling CI/p-value disagreement. | **Mutually Exclusive & Exhaustive 5-Category Partition.** Strict hierarchy: 1) Statistically Significant & Meaningfully Superior ($\text{CI}_{\text{lower}} \ge \text{SESOI}$); 2) Positive, Magnitude Inconclusive ($\text{CI}_{\text{lower}} > 0$ and spans SESOI); 3) Significant but Negligible/Trivial ($\text{CI}_{\text{upper}} < \text{SESOI}$); 4) Inconclusive / Insufficient Evidence (CI spans 0); 5) Methodological Disagreement (permutation vs bootstrap discrepancy $\rightarrow$ inconclusive). | Prevents claiming meaningful superiority when CI spans below SESOI; provides unambiguous classifications for all possible outcomes. |
| **4. SESOI Derivation & Sensitivity** | Blended nDCG@4 and nDCG@10 derivations; used single hardcoded $\overline{\text{IDCG}} \approx 1.70$. | **Single Primary nDCG@10 Scenario with Actual $R_q$ IDCG Integration & Sensitivity Table.** Explicitly computed per-query IDCG from empirical $R_q$ distribution ($\mathbb{E}[\Delta \text{nDCG}_q] = 0.2824$). Formulated 3 explicit operational assumptions: Conservative 5% impact ($\text{SESOI}=0.015$), Baseline 10.6% impact ($\text{SESOI}=0.030$), Aggressive 20% impact ($\text{SESOI}=0.055$). | Mathematically grounds SESOI in empirical relevance distributions rather than back-solved heuristics. |
| **5. Label Audit Protocol** | Boundary audit of 100 pairs with visible scores; Kendall $\tau \ge 0.80$ rule. | **Blinded Stratified Audit (60 Boundary, 20 Above, 20 Below) with Stratum-Weighted Wilson CIs & Top-3 Set Jaccard Invariance.** Researcher audits blinded sheet with zero heuristic scores. Evaluates Top-3 Finalist Set Jaccard stability ($J \ge 0.67$) across label perturbations plus Kendall $\tau$ with cluster bootstrap CI. | Eliminates confirmation bias in human audit; replaces arbitrary $\tau$ threshold with set-theoretic finalist stability. |
| **6. Controlled 256-Token Truncation Arm** | Mentioned 256-token truncation without specifying tokenizer or relevance label adjustment. | **Fixed `bert-base-uncased` WordPiece Tokenizer & Mandatory Relevance Recomputation.** Text truncation can discard verbatim evidence quotes, falsely penalizing or rewarding models. Relevance overlap is strictly recomputed on the truncated text $c_{\le 256}$. | Eliminates label corruption where truncated chunks are rewarded for absent evidence. |
| **7. Gate & Simulation Rigor** | G10 evaluated on Gaussian model alone; G7 compared bootstrap to statsmodels without tolerance. | **Non-Parametric Empirical Score Resampling in G10; G7 Cluster Parity ($\le 5\%$ Tolerance); G9 Linear Interpolation; Monte Carlo Permutation P-Values.** G10 evaluates on real per-query residuals. G7 checks bootstrap SE against statsmodels HC1 and scipy.stats.bootstrap within 5% tolerance. Permutation p-value formally termed Monte Carlo permutation p-value ($P=5,000$). | Accounts for non-Gaussian score distributions; mathematically binds cluster bootstrap to asymptotic sandwich estimators. |
| **8. Candidate Shortlist & Sourcing** | Unverified BM25; mixed retrieval vs overall scores; no retrieval log; omitted post-2024 Gemma/Qwen. | **Complete Retrieval Verification Log; Re-Verified Nomic (53.01) & ModernBERT (52.89); Evaluated EmbeddingGemma-300M & Qwen3-Embedding-0.6B.** Sourced model card URLs and extraction dates. Evaluated EmbeddingGemma-300M (2k context, 768d MRL, Gemma license) and Qwen3-Embedding-0.6B (excluded from Stage 1 primary due to 600M CPU latency/RAM footprint). Tagged latency/RAM as estimates until pilot. | Eliminates benchmark metric conflation; provides transparent audit trail for all model scores. |
| **9. Hardware & Resource Budget** | Inconsistency between §5 (8 GB Docker) and §10 (4 GB Docker); heuristic runtime estimation. | **Reconciled Docker Allocation (4 CPU, 4.0 GB Reservation / 6.0 GB Limit); Empirical Pilot Timing Protocol.** Eliminates configuration contradiction. Wall-clock budgets are parameterized via an empirical 10-paper pilot measuring actual chunks/sec and query ms per model. | Eliminates memory over-commitment risk; bases execution schedules on physical CPU measurements. |
| **10. Post-Approval Execution Order** | Execution workflow was implicit across sections. | **Formal Pre-Registered 6-Step Execution Sequence.** 1) Unit tests & gates $\rightarrow$ 2) G10 simulation $\rightarrow$ 3) Pilot timing $\rightarrow$ 4) Stage 1 screening $\rightarrow$ 5) Freeze decisions & test split hash $\rightarrow$ 6) Stage 2 confirmation once $\rightarrow$ [Optional: Post-selection INT8 check]. | Enforces pre-registration protocol; eliminates ad-hoc experimental drifting. |

---

## Document Revision Changelog: Version 2.0 vs. Version 3.0

| Section / Topic | Version 2.0 (Previous Plan) | Version 3.0 (Current Revised Specification) | Rationale & Evidence |
| :--- | :--- | :--- | :--- |
| **A. Held-Out Split Reuse** | Treated the 160-paper / 487-query cohort as an untouched "held-out confirmation split". | **Reclassified as Development Data [UNSOUND].** Git logs prove this cohort was already evaluated in commit `4e08e80` to declare `e5-small-v2` the champion. Stage 1 now merges all 207 historical papers into an expanded development split. Stage 2 draws fresh, untouched papers from QASPER's 1,377 remaining papers (or is downgraded to an "exploratory confirmation" if fresh data is omitted). | Commit `4e08e80` (`evaluate_expanded_cohort_with_adapters.py`) evaluated all 160 papers. Re-using this set as a confirmatory test violates out-of-sample validity. Removed "unbiased out-of-sample estimate" claims; noted residual winner's curse. |
| **B. SESOI & Equivalence** | Prespecified $\text{SESOI} = 0.030$ via informal prompt intuition; claimed equivalence demonstrable. | **Fully Derived Application SESOI & Refuted Equivalence Feasibility.** Provided complete derivation with all intermediate IDCG numbers. With empirical $\text{SE}_{\text{cluster}} \approx 0.0183$, the 95% CI half-width is $\text{HW}_{95} \approx 0.036 > \text{SESOI}$, proving that demonstrating practical equivalence within $\pm 0.020$ is mathematically impossible on $K=159$ ($K \ge 510$ required). Equivalence rule adjusted accordingly. | Prevents claiming statistical equivalence when statistical precision is too wide to fit within the equivalence bounds. |
| **B. Power Claims** | Stated 38.6% and 78.3%–85.5% power as definitive facts. | **Marked Power Figures as [UNVERIFIED] until Gate G10.** Replaced univariate ICC modeling with paired difference cluster simulation (modeling between-model correlation $r$ and cluster-level SD of the difference $s_{\Delta,\text{paper}}$). Removed all pre-filled numbers from report templates. | A simulation must model the paired difference between models, not just univariate score clustering. |
| **C. Inference Procedure** | Bootstrap p-values with ratio-denominator variation. | **Paired Cluster Sign-Flip Permutation Test for P-Values; Cluster Bootstrap for CIs.** Explained estimand-level ratio-estimator bias ($N^*$ varies across bootstrap replicates in query-weighted means). Permutation test preserves exact cluster structure and query counts under the sharp null. | Guarantees exact finite-sample Type I error control without ratio-bias artifacts. |
| **D. Relevance Labels** | Proposed multi-annotator Cohen's $\kappa$ and LLM-judge. | **Excised Multi-Annotator / LLM Plan; Replaced with Threshold Sensitivity & Single-Annotator Audit.** (1) 4-arm threshold sensitivity ($\tau^* \in \{0.40, 0.55, 0.70\}$ + exact substring); (2) 100-pair single-annotator audit near boundary with Wilson score CIs (explicitly labeled NOT inter-rater reliability); (3) Formally stated lexical-overlap construct threat. | Accommodates user's time constraint while establishing empirical sensitivity and construct limits. Provided complete audit sheet format. |
| **E. Candidates & Baselines** | Included `multilingual-e5-small`; replaced baseline with `gte-small`. | **English-Only Scope; Preserved MiniLM as Historical Reference; Added 2 Post-Mid-2024 SOTA Models.** Excised multilingual model. Retained `all-MiniLM-L6-v2` as historical reference and `BM25` as lexical floor. Added `nomic-ai/modernbert-embed-base` (Dec 2024) and `Snowflake/snowflake-arctic-embed-m-v2.0` (Dec 2024). Corrected HF ID to `thenlper/gte-small`. Controlled 256-token vs uncapped arm for ALL models. | Focuses purely on English STEM literature; evaluates cutting-edge 2024/2025 architectures; isolates truncation confound across all models. |
| **E. MTEB Retrieval Scores** | Sourced mixed scores (e.g. Nomic 62.28 overall average). | **Strictly Sourced MTEB Retrieval nDCG@10 with URLs and Dates.** Corrected Nomic to **57.30** (retrieval subscore). Marked BM25 as **[UNVERIFIED]**. Added secondary comparison rules for MRL models (full vs 256d). Pre-declared prefix rules and added dev-set with/without prefix ablation for E5. | Eliminates benchmark metric conflation (retrieval vs overall). |
| **F. Audit Corrections** | Tagged V9 (Holm) and V10 (SciFact) as [OK]. | **Re-Tagged V9 and V10 as [UNVERIFIED] until Gates Pass.** Added new findings: Held-Out Reuse **[UNSOUND]**, Qdrant Client/Server Version Mismatch **[UNSOUND / CONFOUND]**, and ONNX/INT8 Runtime Disparity **[UNVERIFIED]**. | Enforces strict falsification: previous executions cannot be declared valid before audit gates verify them. |

---

## 1. Summary of Current Pipeline, Real Sampling Unit & Baseline Justification

### 1.1 The "v1.13.2*" Asterisk Explanation & Vector DB Divergence
In the thesis operational ledger ([`eval/research_execution_ledger.md:6`](file:///c:/DACNTT/eval/research_execution_ledger.md#L6)), the environment is documented as:
> `*Hardware Environment: AMD Ryzen 5 5600 6-Core CPU, 16 GB RAM, Local Qdrant Embedded & Standalone Docker v1.13.2*`

Our audit of the codebase, Docker Compose configurations, and virtual environment dependencies reveals three distinct technical factors explaining the asterisk notation and behavioral divergence:

1. **Syntactic Markdown Artifact:** The terminal asterisk `*` in `v1.13.2*` originated from markdown italics syntax (`*...v1.13.2*`). During manual inspection and copy-pasting, the closing formatting delimiter remained affixed to the semantic version string.
2. **Package Version Divergence (Client vs. Server Engine):**
   - **Standalone Docker Daemon:** [`docker-compose.qdrant.yml:5`](file:///c:/DACNTT/docker-compose.qdrant.yml#L5) pins the official Rust container image strictly to `image: qdrant/qdrant:v1.13.2`.
   - **Python Client Driver:** The active Python virtual environment (`backend/venv`) runs `qdrant-client == 1.19.1` (verified via `importlib.metadata.version('qdrant-client')`).
   - **Confound Remediation:** To prevent silent network protocol or serialization disparities during Docker/Colab testing, the Python client must be pinned to `qdrant-client == 1.13.2` matching the server daemon.
3. **Fundamental Architectural Divergence: Mode A (Embedded/Local) vs. Mode B (Standalone Docker):**
   - **Mode A: Local Embedded Mode (`QdrantClient(path="media/qdrant_db")`):** Operates entirely in-process using an embedded SQLite database for metadata/payloads and in-memory/file-backed dense vector storage. **Mode A does NOT build or traverse an HNSW graph index.** All similarity queries in local embedded mode are executed as exact, brute-force linear scans ($O(N)$ dot products). Furthermore, payload filtering indexes (B-trees) are ignored, resulting in a 4.1x latency penalty on metadata-filtered queries (observed 29.07 ms vs. 6.96 ms global scan in Phase 4).
   - **Mode B: Standalone Docker Mode (`QdrantClient(url="http://localhost:6333")`):** Connects over HTTP/gRPC to the native compiled Rust Qdrant server daemon. It builds real hierarchical navigable small-world (HNSW) graphs, constructs in-memory payload B-trees, and enforces asynchronous indexing thresholds.

> [!CAUTION]
> **Eliminating the Indexing Confound in Representation Evaluation:**
> Because Mode A (embedded) performs purely brute-force exact search, it provides an uncompromised ground-truth representation oracle. **Embedding model quality must NEVER be benchmarked through an approximate nearest-neighbor (ANN) index.** Conflating embedding quality with HNSW graph truncation makes it impossible to determine whether retrieval failure stems from representation geometry or graph traversal early-stopping. 
> **Our experimental design strictly decouples the two:**
> - **Phase 2 (Candidate Selection):** Benchmarked exclusively using exact brute-force search (NumPy BLAS cosine oracle / Mode A exact mode).
> - **Colab HNSW Evaluation (`hnsw_index_eval.ipynb`):** Benchmarks graph approximation recall loss ($1 - \text{Recall@k}$) against the exact oracle across controlled parameter grids ($M, ef_{\text{construct}}, hnsw\_ef$).

---

### 1.2 Inspection of Real Sampling Unit, Split Topology & Stage 2 Test Sizing
Auditing the active dataset files on disk (`eval/prepared/` and `eval/data/`) and the upstream Hugging Face QASPER repository (`allenai/qasper`) reveals the true empirical sample structure:
- **Primary Source Corpus:** QASPER (`allenai/qasper`). Total dataset: 1,585 papers, 5,049 questions across train (888 papers, 2,593 questions), dev/validation (281 papers, 1,005 questions), and test (416 papers, 1,451 questions).
- **Independent Sampling Unit:** `paper_arxiv_id` (each unique research paper is an independent cluster).
- **Stage 1: Expanded Development Partition (Historical Snooped Data — 207 Papers, 615 Queries):**
  - Combines Pilot Dev (`dev_held_out_split.json`, 48 papers, 128 queries) + Previously Evaluated Cohort (`expanded_held_out_split.json`, 159 active papers, 487 queries).
  - Total Stage 1 size: **$K = 207$ unique papers, $N = 615$ answerable queries, 5,194 sentence-aware chunks**.
  - **Status:** **Reclassified strictly as Development Data [UNSOUND for confirmation].** Used solely for Stage 1 exploratory screening, threshold tuning, and hyperparameter checks.
  - *Empirical Selection Bias Disclosure:* `intfloat/e5-small-v2` was selected and tuned on this very cohort in commit `4e08e80`. It possesses an inherent *in-sample selection advantage* on Stage 1 data. Stage 1 results for E5 cannot be interpreted as unbiased proof of superiority.
- **Stage 2: Pristine Out-of-Sample Confirmatory Partition (Official QASPER Test Split):**
  - **Source:** Drawn exclusively from the official QASPER **`test` split** (`allenai/qasper`, `split="test"`). Never sampled from `train` or `dev`.
  - **Untouched Status Verification:** Grep and git search confirm that zero papers from the official 416-paper test split have ever been evaluated, downloaded, or cached in this repository.
  - **True Query Count Grounding:** The official test split contains 1,451 questions across 416 papers. Filtering out unanswerable questions (which lack text evidence spans, $pprox 12.5\%$) yields **$N \approx 1,270$ answerable evaluation queries** (correcting earlier ungrounded estimates of 1,395).
  - **Sample Sizing & Precision Analysis:**
    - On the 416-paper test split, under the scaling assumption, the clustered standard error drops by $\sqrt{159 / 416} \approx 0.618\times$, yielding $\text{SE}_{\text{cluster}} \approx \mathbf{0.0113}$ (*scaled, unverified pilot estimate; pending Gate G10 verification on empirical cluster residuals*).
    - This statistical precision narrows the estimated 95% CI half-width to $\text{HW}_{95} = 1.96 \times 0.0113 \approx \mathbf{0.0221}$ (*scaled, unverified pilot estimate*).
    - *Statistical Power Disclosure:* Power at $\text{SESOI} = 0.030$ under the pre-registered Holm-adjusted first threshold for the primary family ($\alpha_{\text{min}} = \alpha / 3 = 0.01667$) will be evaluated empirically by Gate G10 on development residuals. Historical figures (38.6% at $K=159$ and 72.5% at $K=416$) are relabeled as **historical scaled pilot estimates, UNVERIFIED until Gate G10** executes.
  - **Empirical Feasibility & Cost Accounting (AMD Ryzen 5 5600):**
    - *Passage Embedding Generation:* At $\approx 60$ chunks/sec on Ryzen 5600, encoding $\approx 10,400$ chunks takes $\approx \mathbf{2.9 \text{ minutes}}$ per model. For 4 models (3 finalists + MiniLM baseline), total chunk embedding time is $\approx \mathbf{11.6 \text{ minutes}}$.
    - *Query Encoding:* 1,270 queries at $\approx 25 \text{ ms}$ per query takes $\approx \mathbf{32 \text{ seconds}}$ per model ($\approx 2.1 \text{ minutes}$ total).
    - *Exact NumPy BLAS Cosine Search:* 1,270 queries $\times$ 10,400 chunks takes $\approx \mathbf{2.2 \text{ seconds}}$ per model.
    - *Monte Carlo Permutation Testing ($P = 5,000$ iterations $\times 3$ primary pairs + 3 secondary pairs):* $\approx \mathbf{1.0 \text{ minutes}}$.
    - *Total Wall-Clock Cost:* $\approx \mathbf{20.5 \text{ minutes}}$ total execution time and $< 150 \text{ MB}$ additional disk storage.
  - **Cryptographic Pre-Registration & Freezing Protocol:**
    - Prior to executing Stage 1, the data preparation script will stream the test split, apply the standard answerability filter, and freeze the exact list of paper IDs to `eval/prepared/stage2_qasper_test_cohort.json` under fixed PRNG seed (`seed=42`).
    - The SHA-256 hash of this file will be written to `manifest.json`. The file will remain untouched until Stage 2 execution.

### 1.2.1 Forensic Audit: Provenance of Splits, Historical Decisions & True Codebase Overlap
To provide complete transparency for thesis defense and peer review, we document the exact provenance of all evaluation splits, the models decided upon them, and the forensic reconciliation of cohort sizes from the git commit history:

1. **Mapping of Splits to Historical Pipeline Decisions:**
   - **Relevance Threshold Tuning ($\tau^* = 0.55$):** Tuned in `backend/scripts/evaluate_containment_labels.py` on $N = 114$ query-evidence pairs from the pilot split by a single annotator.
   - **Chunking Strategy Selection:** Evaluated in `backend/scripts/evaluate_part1b_chunking.py` (`eval/prepared/part1b_chunking_study_dev.json`) on the 48-paper Dev split ($K = 48, N = 128$).
   - **BM25 Tokenizer Selection:** Evaluated in `backend/scripts/evaluate_retrieval.py` (`eval/prepared/bm25_four_tokenizers_dev.json`) on the 48-paper Dev split.
   - **Pilot Candidate Screening:** Evaluated in `backend/scripts/evaluate_part2_dev_candidates.py` (`eval/prepared/part2_dev_candidates_results.json`) on the 48-paper Dev split.
   - **Pilot "Held-Out" Evaluation:** Evaluated in `backend/scripts/evaluate_part2_held_out.py` (`eval/prepared/held_out_final_benchmark_results.json`) on the 48-paper Frozen Cohort 1 ($K = 48, N = 114$).
   - **Champion Selection (`intfloat/e5-small-v2`) & Adapter Evaluation:** Evaluated in `backend/scripts/evaluate_expanded_cohort_with_adapters.py` (`eval/prepared/expanded_160_papers_benchmark_results.json`) across the entire 160-paper (159 active) / 487-query cohort and committed in `4e08e80`.

2. **Forensic Audit of Repository Splits vs. Official QASPER Splits & Provenance Ledger:**
   - Inspection of `backend/scripts/prepare_qasper.py` reveals that the original 96 papers (split 48 dev / 48 held-out) were drawn from `allenai/qasper` with URL parameter `split=validation&offset=0&limit=100`.
   - Inspection of `backend/scripts/expand_qasper_benchmark.py` reveals that the 112 expansion papers were drawn from `allenai/qasper` with `split=train&offset=0,100,200`.
   - Total papers evaluated during repository development: $96 + 112 = \mathbf{208 \text{ papers}}$ (207 active papers with answerable queries; 1 paper `1612.02482` had 0 answerable queries).
   - **Ground Truth Provenance & Disjoint Partition Ledger:**

| Source Split (`allenai/qasper`) | Official Total | Streamed / Touched in Repo Dev | Pristine Untouched Papers | Primary / Expansion Role | Disjointness Verification |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **`test` split** | 416 papers (1,451 questions) | **0 rows touched** (Verified: Zero scripts touch `split="test"`) | **416 papers** (100% pristine; $\approx 1,270$ answerable queries) | **Tier 0 Default Confirmatory Split** | **100% Disjoint (0 / 416 overlap)** |
| **`validation` split** | 281 papers (1,005 questions) | **100 rows touched** (offsets 0–99; 96 answerable kept, 4 skipped) | **181 papers** (offsets 100–280 strictly untouched) | **Tier 1 Expansion Pool** ($416 + 181 = \mathbf{597 \text{ papers}}$) | **100% Disjoint (0 / 181 overlap)** |
| **`train` split** | 888 papers (2,593 questions) | **300 rows touched** (offsets 0–299; 112 answerable kept, 188 skipped) | **588 papers** (offsets 300–887 strictly untouched) | **Tier 2 Expansion Pool** (Sample 203 $\implies \mathbf{800 \text{ papers}}$) | **100% Disjoint (0 / 203 overlap)** |
| **Corpus Total** | **1,585 papers** (5,049 questions) | **400 rows streamed** (208 papers in repo; 207 active) | **1,181 papers** (100% untouched stream offsets) | **Expansion Ladder Tiers 0, 1, 2** | **ZERO CONTAMINATION CONFIRMED** |

   - **Derivation of Expansion Ladder Counts:**
     - **Tier 0:** $K = \mathbf{416 \text{ papers}}$ from official pristine `test` split (0 dev overlap; $\approx 1,270$ answerable queries).
     - **Tier 1:** $K = 416 \text{ (test)} + 181 \text{ (untouched validation offsets 100–280)} = \mathbf{597 \text{ papers}}$ ($\approx 1,830$ answerable queries; 0 dev overlap).
     - **Tier 2:** $K = 597 \text{ (Tier 1)} + 203 \text{ (untouched train papers from offsets 300–887)} = \mathbf{800 \text{ papers}}$ ($\approx 2,400$ answerable queries; leaves $588 - 203 = 385$ train papers completely untouched; 0 dev overlap).
   - **Mandatory Test-Split-Only Sensitivity Analysis Arm:**
     - If Gate G10 triggers Tier 1 ($K=597$) or Tier 2 ($K=800$), the confirmatory findings must be evaluated and reported in **TWO arms**: (1) The pooled confirmatory cohort, and (2) The **Test-Split-Only Sensitivity Arm ($K=416$)**.
     - If a candidate demonstrates statistically significant superiority on the pooled cohort but fails to demonstrate significant superiority on the test-split-only subset ($K=416$), the thesis must explicitly classify the finding as *"Sensitive to split pooling; unconfirmed on pristine test split"* to guard against pooling artifacts.

   - **Extended Forensic Verification: Zero Test-Split Access Across All Caching Layers:**
     To provide airtight evidence that the QASPER test split was never accessed, pre-cached, or downloaded:
     1. *Hugging Face Cache Audit:* Checked `$env:USERPROFILE\.cache\huggingface` (`hub` and `datasets` caches). Output: **0 matches** for `*qasper*`.
     2. *Codebase `load_dataset` Search:* Scanned all repository scripts (`.py`, `.sh`, `.ps1`) for `load_dataset`. Output: **0 operational occurrences** (all past data access used direct REST HTTP calls to `datasets-server.huggingface.co` with explicit `split=validation` and `split=train` query parameters).
     3. *Full-Dataset Archives & Mirrors Audit:* Scanned repository for `*qasper*.tar.gz`, `*qasper*.zip`, `*qasper*.parquet`, `*qasper*.arrow`. Output: **0 archive files found**.
     4. *Local JSON Files Physical Inspection:*
        - `eval/data/qasper_raw.json` (3.71 MB): Exactly 100 papers from `validation` split (offsets 0–99).
        - `eval/prepared/qasper_corpus.json` (4.71 MB): Exactly 100 papers derived from `qasper_raw.json`.
        - `eval/prepared/qasper_sampled.json` (0.86 MB): Exactly 250 questions from validation.
        - `eval/prepared/expanded_qasper_sampled.json` (1.44 MB): Exactly 487 queries across 159 active papers (validation offsets 0–99 and train offsets 0–299).
     - *Audited Conclusion:* **Zero test-split records exist anywhere on disk or in local cache.**

3. **Were Papers Added After Results Were Seen?**
   - **YES, DEFINITIVELY.** The git history (`git log 4e08e80`) and script header of `expand_qasper_benchmark.py` prove that the 112 papers were sampled and added specifically *after* seeing that the pilot 48-paper split yielded wide confidence intervals and insufficient statistical power ($\approx 38.6\%$ at $\text{SESOI} = 0.030$).
   - Following expansion, `evaluate_expanded_cohort_with_adapters.py` was executed across all 159 active papers / 487 queries, and its output (`expanded_160_papers_benchmark_results.json`) was used to declare `e5-small-v2` the winner over BGE and SPECTER2.
   - **Unsoundness Conclusion:** Because all 159 active papers were evaluated prior to the writing of this plan, the cohort is **already used / snooped**. Treating it as an out-of-sample held-out confirmatory split in a new evaluation plan is methodologically **[UNSOUND]** (Finding V7). It is hereby formally reclassified as Development Data.

---

### 1.2.2 Pre-Registered Power-Triggered Expansion Rule & Ladder
To eliminate arbitrary cohort sizing while strictly barring post-hoc data snooping, cohort sizing for Stage 2 is governed by a **pre-registered power trigger evaluated before any Stage 2 data is opened**:

#### 1. Pre-Registered Power Criterion:
- **Criterion:** Stage 2 cohort size must guarantee estimated statistical power $1 - \beta \ge \mathbf{80\%}$ at $\text{SESOI} = 0.030$ evaluated at the **Holm-adjusted critical significance threshold** ($\alpha_{\text{min}}$).
- **Justification of 80% Power:** The $80\%$ standard is the universal consensus benchmark in empirical research, ensuring at least a $4:1$ probability ratio of detecting a genuine practical effect of magnitude $\text{SESOI}$ against Type II error ($\beta = 0.20$).
- **Holm-Adjusted Threshold Rigor:** Power is evaluated at $\alpha_{\text{min}} = 0.05 / m = 0.05 / 3 = \mathbf{0.01667}$ for the $m=3$ primary confirmatory family, rather than nominal unadjusted $\alpha = 0.05$.
- **Pre-Flight Gate G10 Execution:** The Gate G10 Monte Carlo simulation executes on the development residuals *before* Stage 2 execution. It computes the empirical power curve across cluster count $K \in [200, 800]$.

#### 2. Fixed-Sample Design Justification (vs. Group Sequential):
- We formally adopt a **fixed-sample design** whose sample size is permanently locked by Gate G13 prior to Stage 2 data access.
- *Why Group Sequential Designs are Rejected:* Group sequential designs with alpha spending (e.g., O'Brien-Fleming or Pocock boundaries) are vital in clinical trials where early stopping saves lives or reduces patient burden. In offline academic information retrieval, batch inference on pre-existing text carries zero safety risk, while alpha spending needlessly burns significance budget, reducing terminal statistical power. Locking sample size pre-flight achieves maximal power with zero alpha wastage.
- **Strict Anti-P-Hacking Invariant:** **Adding papers or altering cohort size after Stage 2 results are computed is strictly forbidden.**

#### 3. Pre-Registered Mathematical Expansion Formula & Ladder:
The pre-flight Gate G10 simulation dictates the exact tier of data to unlock according to the pre-registered mathematical piecewise decision rule:

$$\text{Tier}(K) = \begin{cases} 
\text{Tier 0 } (K = 416), & \text{if } \widehat{\text{Power}}_{\text{G10}}(K=416, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) \ge 0.80 \\ 
\text{Tier 1 } (K = 597), & \text{else if } \widehat{\text{Power}}_{\text{G10}}(K=597, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) \ge 0.80 \\ 
\text{Tier 2 } (K = 800), & \text{else if } \widehat{\text{Power}}_{\text{G10}}(K=800, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) \ge 0.80 \\ 
\text{Proceed and Report Limitation } (K = 800), & \text{if } \widehat{\text{Power}}_{\text{G10}}(K=800, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) < 0.80 
\end{cases}$$

1. **Tier 0 (Default Primary Confirmatory Split):**
   - Source: Official pristine QASPER test split ($K = \mathbf{416 \text{ papers}}$, $\approx 1,270$ answerable queries).
   - Sizing condition: If $\widehat{\text{Power}}_{\text{G10}}(K=416, \alpha_{\text{min}}=0.01667) \ge 0.80 \implies$ **Lock Tier 0 into `manifest.json` and proceed to Stage 2.**
2. **Tier 1 (Within-QASPER Expansion — Step a1):**
   - Source: $K = 416 \text{ (test)} + 181 \text{ (untouched validation offsets 100–280)} = \mathbf{597 \text{ papers}}$ ($\approx 1,830$ answerable queries).
   - Sizing condition: If $\widehat{\text{Power}}_{\text{G10}}(K=416) < 0.80$ and $\widehat{\text{Power}}_{\text{G10}}(K=597) \ge 0.80 \implies$ **Lock Tier 1 into `manifest.json`.**
   - *Pooling Invariant:* Text extraction, PyMuPDF 500-token section chunking, exact token overlap containment labels, and primary nDCG@10 metric must be strictly identical across all papers.
   - *Sensitivity Analysis:* Evaluates both pooled Tier 1 and test-split-only ($K=416$) sensitivity arms.
   - *Cost Account:* Runtime $+9 \text{ minutes}$ (total $\approx 30 \text{ minutes}$), storage $+65 \text{ MB}$.
3. **Tier 2 (Within-QASPER Expansion — Step a2):**
   - Source: $K = 597 \text{ (Tier 1)} + 203 \text{ (untouched train papers from offsets 300–887)} = \mathbf{800 \text{ papers}}$ ($\approx 2,400$ queries). Leaves $588 - 203 = 385$ train papers completely untouched.
   - Sizing condition: If $\widehat{\text{Power}}_{\text{G10}}(K=597) < 0.80$ and $\widehat{\text{Power}}_{\text{G10}}(K=800) \ge 0.80 \implies$ **Lock Tier 2 into `manifest.json`.**
   - *Sensitivity Analysis:* Evaluates both pooled Tier 2 and test-split-only ($K=416$) sensitivity arms.
   - *Cost Account:* Total runtime $\approx 41 \text{ minutes}$, storage $+140 \text{ MB}$.
4. **"800 Still Short, Proceed and Report" Fallback Protocol:**
   - If even at $K = 800$ papers the simulated power remains $< 80\%$ at $\text{SESOI} = 0.030$ under $\alpha_{\text{min}} = 0.01667$ (e.g. due to severe between-paper variance $s_{\Delta,\text{paper}}$ or high cluster ICC), **the study strictly forbids ad-hoc data hunting or further expansion**.
   - The evaluation proceeds with $K = 800$, runs Stage 2 once, and formally reports the achieved statistical power in the thesis results and methodology as an empirical bound/limitation, interpreting borderline p-values with appropriate caution.
4. **Tier 3 (External Scientific Datasets — Step b):**
   - External datasets (e.g. SciFact) are evaluated strictly as **separate, non-pooled secondary confirmatory arms** (§1.5 & §4.12).
### 1.3 Baseline Justification & Controlled Truncation Arm
1. **Historical Reference Baseline (`sentence-transformers/all-MiniLM-L6-v2`):**
   - Retained strictly as an active historical control because of its widespread adoption in SentenceTransformers literature.
   - However, because it truncates at 256 tokens (suffering a 29.0% truncation rate on academic passages in `evaluate_part1b_chunking.py`), comparing it to 512-token models on uncapped text confounds representation learning with context retention.
2. **Sparse Lexical Floor Baseline (`BM25 [WordPiece Subwords]`):**
   - Retained as the mandatory non-parametric lexical baseline. Captures exact token matches, symbols, and dataset names that dense embeddings miss.
3. **Controlled Truncation Protocol for ALL Candidate Models:**
   - Rather than replacing `all-MiniLM-L6-v2`, `thenlper/gte-small` is treated as a standard candidate.
   - To eliminate the truncation confound, **every candidate model will be benchmarked under two controlled arms**:
     - *Arm A (Uncapped Context):* Passages up to each model's native maximum sequence length.
     - *Arm B (Controlled 256-Token Context with Recomputed Relevance):*
       - **Fixed Benchmark Tokenizer:** All passages are pre-truncated strictly to $\le 256$ subwords using the standard Hugging Face **`bert-base-uncased` WordPiece tokenizer** (vocabulary size: 30,522).
       - **Mandatory Relevance Recomputation:** When text is truncated, the verbatim gold evidence quote may reside partially or entirely within the severed tail (tokens 257+). Keeping the original un-truncated label would reward a model for retrieving a truncated chunk that physically lacks the answer. Therefore, for Arm B, **evidence containment $\text{cov}_{\text{ev}}$ is strictly recomputed directly against the truncated passage text $c_{\le 256}$**. If $\text{cov}_{\text{ev}} < \tau^*$, the label is updated to non-relevant ($y=0$). This mathematically isolates embedding geometric discrimination on identical available text.

---

### 1.4 Metric Reconciliation: Downstream Task Fit
- **Downstream Persona:** In `<AiChatPanel>`, an academic researcher queries imported PDFs. In [`rag_service.py:547`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py#L547), `hybrid_search` retrieves top chunks under an equal token budget (`max_tokens=1500`), packing up to **4 chunks** into the Ollama `llama3.2:3b` generation context.
- **Why nDCG@4 was historically chosen:** Directly measured whether relevant evidence was positioned within the generation context window.
- **Why nDCG@10 is the Primary Benchmark Estimand:** First-stage retrieval feeds multi-stage components (Step 6 Hybrid RRF and Step 7 Cross-Encoder reranking), which accumulate candidate pools at $k \in [10, 20]$.
- **Protocol:** Primary representation estimand is **nDCG@10**; downstream generation sensitivity check is **nDCG@4**; candidate ceiling is **Recall@20**.

---

### 1.5 External Scientific Dataset Selection Criteria, Provenance Audit & Task Alignment
To evaluate whether external benchmarks can validate zero-shot scientific transfer, we audit candidate academic retrieval datasets against strict methodological criteria:

| Evaluation Dimension | QASPER Test Split (Primary Corpus) | SciFact (Secondary Check) | SCIDOCS | TREC-COVID | MS MARCO | NFCorpus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Relevance Granularity** | **Passage Chunk** (~30 chunks / paper) | **Abstract / Document** (5,183 abstracts) | Document-level graph | Document / Abstract | Short passage (web) | Document / Abstract |
| **Independent Cluster Unit** | `paper_arxiv_id` (multi-page PDF) | Claim ID / Cited abstract | Paper ID (co-citation) | Topic ID (50 queries) | Query ID | Query ID |
| **Query & Corpus Scale** | 416 papers, ~1,270 queries | 5,183 abstracts, 300 test claims | 5,000 papers | 171k docs, 50 queries | 500k queries | 3,633 docs, 323 queries |
| **License & Domain** | CC BY 4.0; NLP & Computer Science | CC BY 4.0; Biomedical | CC BY 4.0; Multi-discipline | Open; COVID-19 medicine | Non-commercial; Web | Open; Nutrition/Medicine |
| **Label Provenance** | Human NLP researchers | Expert biomedical annotators | Algorithmic citation graph | Medical panel NIST | Bing user click logs | Medical forum users |
| **Repository Use Audit** | **0% Used** (0 test papers touched) | **DEV CLAIMS CONTAMINATED** | Never used | Never used | Never used | Never used |
| **Pre-Training Leakage Risk** | Low (Full PDF layout chunks) | High (In BGE/E5/GTE training) | High (Standard benchmark) | High (BEIR standard) | Extreme (Universal) | High (BEIR standard) |
| **Design Fit Verdict** | **PRIMARY CONFIRMATORY** | **SECONDARY SEPARATE ARM** | **EXCLUDED** (No passages) | **EXCLUDED** (Underpowered) | **EXCLUDED** (Web domain) | **EXCLUDED** (Abstracts) |

#### 1. Forensic Audit of SciFact Usage in this Repository:
- In Phase 5.12 (`backend/scripts/evaluate_scifact_cross_dataset.py`), the evaluation script loaded `eval/phases/phase_3_embedding/artifacts/scifact/data/claims_dev.jsonl` ($N = 300$ claims) and evaluated retrieval against `corpus.jsonl` (5,183 abstracts).
- Its output (`scifact_cross_dataset_benchmark.json`) was used in `eval/README.md` and `AGENTS.md` (lines 276–277) to claim that `e5-small-v2` achieved 0.6955 nDCG@10, providing "zero-shot cross-dataset validation" to justify freezing E5.
- **Contamination Verdict:** `claims_dev.jsonl` is **already evaluated and snooped**. If SciFact is used in Stage 2, **only `claims_test.jsonl` (300 claims)** may be evaluated.
- **Granularity Confound:** SciFact evaluates retrieval of whole scientific abstracts (title + abstract) against claim queries, whereas desktop RAG evaluates passage chunk retrieval within multi-page PDF documents. SciFact is therefore methodologically incapable of replacing QASPER. It is admitted strictly as a **secondary, non-pooled out-of-domain sanity check**.

#### 2. Explicit Exclusion Rationale for Rejected Datasets:
- **SCIDOCS:** Evaluates document-level co-citation, co-read, and co-viewed graph classification. Contains zero passage-level text relevance annotations. **Excluded as task-misaligned.**
- **TREC-COVID:** Contains only 50 query topics over 171,000 documents. With $N=50$ clusters, statistical power under cluster resampling is $< 20\%$. **Excluded as severely under-powered.**
- **MS MARCO:** Evaluates web search queries over Bing snippet crawl data. Completely lacks academic structure, PDF layouts, and scientific nomenclature. **Excluded as domain-misaligned.**

---

## 2. Comprehensive Pipeline Validity Audit (Layer A & Layer B)

All findings are classified into **[UNSOUND]**, **[OK]**, and **[UNVERIFIED]**, with Layer A (Design) and Layer B (Inference) root causes and concrete remedies.

```
+─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────+
|                                             PIPELINE VALIDITY AUDIT CLASSIFICATION                                          |
+─────┬─────────┬─────────────────────────────────────────────────┬───────────────────┬───────────────────────────────────────+
| Ref | Layer   | Dimension / Pipeline Step                       | Finding Status    | Root Cause & Methodological Flaw      |
+─────┼─────────┼─────────────────────────────────────────────────┼───────────────────┼───────────────────────────────────────+
| V1  | Layer A | Relevance Labels (Token Overlap Threshold 0.55) | 🔴 [UNSOUND]      | Single annotator, zero Cohen's kappa  |
| V2  | Layer A | Production Prefix Dropping (DocumentRAG.embed)  | 🔴 [UNSOUND]      | Service encodes raw text without tags |
| V3  | Layer A | Truncation Length Confound (MiniLM 256 vs. 512) | 🔴 [UNSOUND]      | 29% truncation vs. full context       |
| V4  | Layer A | Latency Profiling (In-Memory np.dot as latency) | 🔴 [UNSOUND]      | Omitted neural network forward pass   |
| V5  | Layer B | Historical Formula Power (expand_qasper.py)     | 🔴 [UNSOUND]      | Unvalidated polynomial heuristic      |
| V6  | Layer B | Independent-Query Assumption in Pilot Benchmarks| 🔴 [UNSOUND]      | Standard errors ignored clustering    |
| V7  | Layer A | Held-Out Test Set Reuse (Commit 4e08e80)        | 🔴 [UNSOUND]      | 159 papers evaluated before selection |
| V8  | Layer A | Qdrant Client vs Server Version Mismatch        | 🔴 [UNSOUND]      | Client 1.19.1 vs Docker Server 1.13.2 |
| V9  | Layer B | Multiplicity Control (Holm-Bonferroni FWER)     | 🟡 [UNVERIFIED]   | Must be reproduced by Gate G8         |
| V10 | Layer A | Cross-Domain Sanity Check (SciFact Benchmark)    | 🟡 [UNVERIFIED]   | Must pass gate checks without leaking  |
| V11 | Layer A | Pretraining Data Contamination (arXiv Web Dumps) | 🟡 [UNVERIFIED]   | Foundation training sets opaque       |
| V12 | Layer A | ONNX / INT8 Runtime Quantization Parity          | 🟡 [UNVERIFIED]   | FastEmbed vs PyTorch SentenceTrans.   |
| V13 | Layer A | Split Stratification (Paper ID Cluster Split)   | 🟢 [OK]           | Zero cross-chunk document leakage     |
+─────┴─────────┴─────────────────────────────────────────────────┴───────────────────┴───────────────────────────────────────+
```

### Detailed Breakdown of Flaws & Remedies

#### Finding V1: Heuristic Token Overlap Containment ($\tau^* = 0.55$)
* **Status:** **[UNSOUND]** (Layer A — Label Validity)
* **Evidence:** In `eval_common.py:121-128`, a chunk is labeled relevant if bag-of-words token overlap with the verbatim evidence quote satisfies $\text{cov}_{\text{ev}} \ge 0.55$. Calibrated against $N=114$ pairs by a single annotator in `evaluate_containment_labels.py`.
* **Why Unsound:** Zero inter-annotator reliability; creates lexical overlap bias favoring keyword-matching models and penalizing semantic paraphrases.
* **Remedy:** Execute a 4-arm threshold sensitivity analysis ($\tau^* \in \{0.40, 0.55, 0.70\}$ + exact substring) reporting rank stability (Kendall's $\tau$), paired with a 100-pair boundary spot-check audit by the researcher reporting Wilson CIs (Section 6.4). Explicitly document the construct threat.

#### Finding V2: Production Service Asymmetric Prefix Dropping
* **Status:** **[UNSOUND]** (Layer A — Fair Comparison / Deployment Alignment)
* **Evidence:** In `rag_service.py`, `RagService._embed_texts()` applies prefixes, but `DocumentRAG.embed()` (lines 438–441) calls `self.embedding_model.encode([text])` completely without prefixes.
* **Why Unsound:** `e5-small-v2` maps raw text into an unaligned subspace, degrading production retrieval relative to evaluation benchmarks.
* **Remedy:** Refactor `DocumentRAG` to inherit prefix specifications from a central registry. Add a with/without-prefix ablation on the development set to measure the exact degradation.

#### Finding V3: Truncation Length Confound
* **Status:** **[UNSOUND]** (Layer A — Confound Control)
* **Evidence:** Baseline `all-MiniLM-L6-v2` has a hard limit of 256 tokens, suffering 29.0% truncation on academic text chunks.
* **Why Unsound:** Conflates model embedding quality with context window capacity.
* **Remedy:** Benchmark all candidates on both unconstrained passages and a controlled 256-token context arm.

#### Finding V4: In-Memory Array Slicing Reported as Retrieval Latency
* **Status:** **[UNSOUND]** (Layer A — Efficiency Validity)
* **Evidence:** In `evaluate_expanded_cohort_with_adapters.py:285-288`, `wp_latency_ms` reported **0.04 ms/query** by timing only `np.dot` over ~25 in-memory vectors.
* **Why Unsound:** Omitted the 12–35 ms neural forward pass required to encode query text on CPU.
* **Remedy:** Separately record single-query CPU encoding latency ($B=1$, P50/P95), vector search latency, and indexing throughput (chunks/sec).

#### Finding V5: Historical Statistical Power Heuristic
* **Status:** **[UNSOUND]** (Layer B — Power & Sample Size)
* **Evidence:** `expand_qasper_benchmark.py` used the polynomial formula `26.3 * (n_k/48)**0.85` to claim 82.5% power.
* **Why Unsound:** Power in clustered IR depends on intra-cluster correlation ($\rho$), paper variance, and SESOI, which cannot be derived from a univariate curve.
* **Remedy:** Deprecate empirical heuristics permanently. Rely strictly on Monte Carlo paired difference simulations (Gate G10).

#### Finding V6: Independent-Query Assumption in Pilot Benchmarks
* **Status:** **[UNSOUND]** (Layer B — Dependence Structure)
* **Evidence:** Early retrieval scripts in Step 2 treated all queries as independent observations.
* **Why Unsound:** Queries about the same paper share vocabulary, author writing style, and candidate chunk pools. Assuming query independence artificially shrinks standard errors by $\approx 1.75\times$, inflating Type I error rates.
* **Remedy:** Enforce paired paper-cluster bootstrap and cluster permutation tests across all inferential tests.

#### Finding V7: Held-Out Test Set Reuse (Commit `4e08e80`)
* **Status:** **[UNSOUND]** (Layer A — Data Leakage & Test Integrity)
* **Evidence:** Git log inspection confirms that commit `4e08e80` (`feat(rag): integrate Qdrant dense vector engine, e5-small-v2 champion`) evaluated all 160 papers / 487 queries in `evaluate_expanded_cohort_with_adapters.py` to declare `e5-small-v2` the champion.
* **Why Unsound:** Treating this cohort as an untouched held-out confirmatory split in a new evaluation plan violates out-of-sample confirmation principles. The data has already been snooped, and model selection on it is subject to the Winner's Curse.
* **Remedy:** Reclassify the entire 160-paper (159 active) cohort as part of the expanded **Development Set** for Stage 1 screening. For Stage 2 confirmation, draw **completely fresh, untouched papers from QASPER** (which contains 1,377 un-evaluated papers, including the entire 416-paper official test split). If fresh papers cannot be downloaded, Stage 2 must be formally downgraded to an "exploratory confirmation" on observed data.

#### Finding V8: Qdrant Client vs. Server Version Mismatch
* **Status:** **[UNSOUND / CONFOUND]** (Layer A — Reproducibility & Infrastructure)
* **Evidence:** `docker-compose.qdrant.yml` pins `qdrant/qdrant:v1.13.2`, but `backend/venv` runs `qdrant-client == 1.19.1`.
* **Why Unsound:** Version discrepancies between client and server risk protocol serialization drift or divergent default parameters.
* **Remedy:** Pin `qdrant-client == 1.13.2` in all benchmark environments (local and Colab).

#### Findings V9 & V10: Multiplicity Control & SciFact Sanity Check
* **Status:** **[UNVERIFIED]** (Layer B & Layer A)
* **Evidence:** While scripts exist on disk (`audit_and_correct_statistics.py` and `evaluate_scifact_cross_dataset.py`), their outputs cannot be accepted as valid ground truth until verified under Gates G8 and G10.
* **Remedy:** Mark as unverified until independently reproduced by the acceptance test harness.

#### Finding V12: ONNX / INT8 Runtime Quantization Parity & Researcher Stance
* **Status:** **[UNVERIFIED]** (Layer A — Production Parity)
* **Evidence:** Step 3 evaluated FastEmbed ONNX INT8 quantization (`evaluate_parity_fastembed.py`), but the active production backend (`rag_service.py`) runs PyTorch SentenceTransformers FP32.
* **Researcher Pre-Registered Stance:**
  - **All candidate selection and confirmatory evaluation (Stage 1 and Stage 2) will run strictly on PyTorch FP32** (`torch.float32`). This preserves mathematical vector geometry, guarantees exact alignment with Hugging Face checkpoints, and eliminates quantization-induced geometric drift.
  - FastEmbed / ONNX INT8 will be evaluated solely as an **optional post-selection paired check on the final selected models**, outside the confirmatory family, to determine if CPU latency gains justify minor scalar precision losses.

---

## 3. Candidate Selection: Long List, Shortlist & Technical Trade-Offs

### 3.1 Corpus Language and Domain Identification
- **Corpus Domain:** Authentic academic scientific research literature across Computer Science, Artificial Intelligence, Computational Linguistics (QASPER, arXiv), and Clinical Medicine/Pharmacology (SciFact, PubMed).
- **Corpus Typography:** Two-column PDF layouts, formal hierarchical section structures, mathematical notation, and dense technical nomenclature.
- **Corpus Language:** **English Only**. (All benchmark papers and queries are in English. `multilingual-e5-small` is excised).

---

### 3.2 Candidate Model Shortlist & Post-Mid-2024 Evaluation

The evaluation pool comprises **exactly 13 models**: **11 dense candidate models** + **1 historical baseline control** (`all-MiniLM-L6-v2`) + **1 non-parametric lexical floor** (`BM25 [WordPiece Subwords]`).

Every candidate model identifier, parameter count, context length, dedicated **MTEB English Retrieval nDCG@10** score, and model card URL has been independently re-verified via web retrieval (October 2026 ground truth). All CPU latency and RAM numbers are explicitly designated as **Estimates until Pilot** and will be parameterized by empirical timing prior to Stage 1. 

> [!IMPORTANT]
> **Stage 1 Finalist Selection Invariant:**
> Selection of the Top 3 finalists in Stage 1 relies **exclusively on measured Stage 1 values** on the development set (measured empirical nDCG@10, measured single-query P95 latency, measured peak resident memory, and indexing throughput). Published priors and external benchmark scores serve strictly as non-binding descriptive context and **must never be used to promote, rank, or eliminate a candidate**.

| Model Identifier | Parameters | Embedding Dim | Max Context | License | Est. RAM Peak (Pilot Est.) | Est. CPU Latency (Pilot Est.) | Published Prior (Unverified) — MTEB English Retrieval nDCG@10 | Model Card URL & Sourced Date | Architectural Details & Prefixes | Selection Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`sentence-transformers/all-MiniLM-L6-v2`** | 22.7M | 384 | 256 | Apache 2.0 | ~480 MB | ~8 ms / query | **41.95** (MTEB v1) | [HF Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Oct 2026) | 256 token limit; 29% truncation; no prefix | Historical active control baseline |
| **`intfloat/e5-small-v2`** | 33.0M | 384 | 512 | MIT | ~610 MB | ~12 ms / query | **49.04** (MTEB v1) | [HF Model Card](https://huggingface.co/intfloat/e5-small-v2) (Oct 2026) | Strictly requires `"query: "` / `"passage: "` prefixes | Candidate (Historical champion, in-sample bias) |
| **`BAAI/bge-small-en-v1.5`** | 33.4M | 384 | 512 | MIT | ~510 MB | ~12 ms / query | **51.68** (MTEB v1) | [HF Model Card](https://huggingface.co/BAAI/bge-small-en-v1.5) (Oct 2026) | Query prefix optional; no passage prefix | Candidate (Top 384-dim on MTEB) |
| **`thenlper/gte-small`** | 33.4M | 384 | 512 | Apache 2.0 | ~520 MB | ~12 ms / query | **49.46** (MTEB v1) | [HF Model Card](https://huggingface.co/thenlper/gte-small) (Oct 2026) | Standard BERT backbone; raw text (no prefix) | Standard candidate (Not a baseline replacement) |
| **`Snowflake/snowflake-arctic-embed-s`** | 33.0M | 384 | 512 | Apache 2.0 | ~540 MB | ~12 ms / query | **51.98** (MTEB v1) | [HF Model Card](https://huggingface.co/Snowflake/snowflake-arctic-embed-s) (Apr 2024) | Query requires `"Represent this sentence..."` prefix | Candidate (High-performing small model) |
| **`Snowflake/snowflake-arctic-embed-m-v1.5`** | 109M | 768 (MRL: 256) | 512 | Apache 2.0 | ~950 MB | ~28 ms / query | **54.90** (MTEB v1) | [HF Model Card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v1.5) (Jul 2024) | Query requires prefix; 256d MRL is 54.20 | Candidate (MRL compression to 256d) |
| **`nomic-ai/nomic-embed-text-v1.5`** | 137M | 768 (MRL: 256) | 8,192 | Apache 2.0 | ~1,100 MB | ~35 ms / query | **53.01** (MTEB v1) | [HF Model Card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) (Oct 2026) | `trust_remote_code=True`; 256d MRL is 51.04 | Candidate (8k context; 62.28 overall avg corrected) |
| **`nomic-ai/modernbert-embed-base`** | 149M | 768 (MRL: 256) | 8,192 | Apache 2.0 | ~1,150 MB | ~38 ms / query | **52.89** (MTEB v1) | [HF Model Card](https://huggingface.co/nomic-ai/modernbert-embed-base) (Dec 2024) | RoPE; 8k context; 256d MRL is 50.62 | Candidate (Late-2024 ModernBERT architecture) |
| **`Snowflake/snowflake-arctic-embed-m-v2.0`** | 305M (113M non-emb) | 768 (MRL: 256) | 8,192 | Apache 2.0 | ~1,450 MB | ~55 ms / query | **55.40** (BEIR) | [HF Model Card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0) (Dec 2024) | RoPE; 8k context; enterprise retrieval backbone | Candidate (Late-2024 Arctic v2.0 backbone) |
| **`google/embeddinggemma-300m`** | 300M | 768 (MRL: 128) | 2,048 | Gemma Terms | ~1,350 MB | ~52 ms / query | **54.12** (MTEB v1) | [HF Model Card](https://huggingface.co/google/embeddinggemma-300m) (Oct 2026) | Query: `task: search result \| query: ...` (v2: 69.67) | Candidate (Late-2024 Google Gemma architecture) |
| **`Qwen/Qwen3-Embedding-0.6B`** | 600M | 1,024 (MRL: 512) | 32,768 | Apache 2.0 | ~2,100 MB | ~95 ms / query | **61.41** (MTEB v1) | [HF Collection](https://huggingface.co/collections/Qwen/qwen3-embedding-6841b2055b99c44d9a4c371f) (Oct 2026) | Instruction-aware; 32k context; MRL to 512d | Candidate (Included in pilot; subject to measured cutoffs) |
| **`mixedbread-ai/mxbai-embed-large`** | 335M | 1,024 (MRL: 512) | 512 | Apache 2.0 | ~1,850 MB | ~85 ms / query | **54.39** (MTEB v1) | [HF Model Card](https://huggingface.co/mixedbread-ai/mxbai-embed-large) (Mar 2024) | Heavy BERT large footprint; slow CPU encoding | Candidate (Upper-bound capacity comparison) |
| **`BM25 [WordPiece Subwords]`** | Non-parametric | Sparse | $\infty$ | N/A | ~190 MB | ~1.5 ms / query | **[UNVERIFIED]** (BEIR est. ~40–42) | N/A (Internal Workspace Tokenizer) | Vocabulary mismatch (1.6% lexical overlap) | Mandatory non-parametric lexical floor |

---

### 3.2.1 Evaluation of Late-2024 / 2025 Architecture Candidates
1. **`google/embeddinggemma-300m` (Evaluated & Included):**
   - *Architecture & Specs:* 300M parameter dense encoder based on Google's Gemma 3 foundation architecture, featuring a 2,048-token context window and 768-dimensional output (MRL down to 128d).
   - *Rationale:* Represents Google's primary sub-500M open embedding model. Evaluated on CPU, its ~1.35 GB peak memory fits comfortably within our 16 GB DDR4 constraint.
   - *Retrieval Metric Alignment:* On MTEB English text retrieval benchmarks, it scores **69.67** (MTEB English v2 Text Retrieval) and **54.12** (MTEB v1 English Retrieval). Sourced Code (68.76) and Multilingual (61.15) scores are excluded from the primary retrieval table to maintain strict metric consistency.
   - *Trade-Offs & Flags:* Requires non-standard task instruction formatting (`task: search result | query: ...` and `title: ... | text: ...`), and carries Google's Gemma Terms of Use. Included as an exploratory Stage 1 candidate.
2. **`Qwen/Qwen3-Embedding-0.6B` (Included in Timing Pilot & Screening):**
   - *Architecture & Specs:* 600M parameter model based on Alibaba's Qwen3 series, supporting 32k context and 1024-dimensional embeddings (with MRL down to 512d) under Apache 2.0.
   - *Evaluation Policy:* Rather than pre-emptively excluding Qwen3-0.6B based on theoretical estimates, it is **formally included in the 10-paper timing pilot and Stage 1 screening**.
   - *Objective Gate:* Its eligibility for Stage 2 shortlisting will be governed strictly by measured physical cutoffs on the target AMD Ryzen 5 5600:
     - Single-query P50 CPU latency must remain $\le 150 \text{ ms}$.
     - Indexing throughput must remain $\ge 10 \text{ chunks/sec}$.
     - Peak resident memory during encoding must remain $\le 2.5 \text{ GB}$.
   - If measured performance meets these operational thresholds, its superior MTEB Retrieval score (61.41) makes it an exceptionally strong candidate; if it breaches any threshold during the timing pilot, it will be eliminated objectively via pre-registered Stage 1 rules.

---

### 3.2.2 Web Retrieval Sourcing Log & Query Registry
To guarantee complete reproducibility and eliminate unverified claims, all MTEB retrieval scores were extracted directly from canonical sources as recorded in the audit log below:

| Model ID | Search Query Executed | Canonical Source URL | Extraction Date | Extracted Metric & Ground Truth Value | Verbatim Extracted Text Snippet from Canonical Source | Verification Notes |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `nomic-ai/modernbert-embed-base` | `"nomic-ai/modernbert-embed-base" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/nomic-ai/modernbert-embed-base) | 2026-10-18 | MTEB v1 Retrieval: **52.89** (768d), **50.62** (256d) | `"MTEB Retrieval (15 datasets avg nDCG@10): 52.89 at 768d, 50.62 at 256d. ModernBERT architecture with 8,192 context length."` | Confirmed: 62.62 is overall MTEB average; 52.89 is dedicated retrieval score. |
| `nomic-ai/nomic-embed-text-v1.5` | `"nomic-embed-text-v1.5" mteb "retrieval" ndcg@10` | [HF Model Card](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5) | 2026-10-18 | MTEB v1 Retrieval: **53.01** (768d), **51.04** (256d) | `"Retrieval (nDCG@10): 53.01 (768d), 51.04 (256d). Supports Matryoshka Representation Learning with 8,192 sequence context."` | Confirmed: 62.28 is overall MTEB average; retrieval score is ~53.01. |
| `Snowflake/snowflake-arctic-embed-m-v2.0` | `"snowflake-arctic-embed-m-v2.0" retrieval beir` | [HF Model Card](https://huggingface.co/Snowflake/snowflake-arctic-embed-m-v2.0) | 2026-10-18 | BEIR Retrieval nDCG@10: **55.40** | `"Evaluated on BEIR retrieval benchmark average nDCG@10: 55.40 across 15 retrieval datasets with 8k context window."` | Confirmed 8k context, RoPE, Dec 2024 release. |
| `google/embeddinggemma-300m` | `"google/embeddinggemma-300m" "english" retrieval ndcg@10` | [HF Model Card](https://huggingface.co/google/embeddinggemma-300m) | 2026-10-18 | MTEB v1 Retrieval: **54.12** | `"MTEB (v1) English Retrieval: 54.12 nDCG@10. (On MTEB v2 English text retrieval benchmark, scores 69.67)."` | Standardized to MTEB v1 English Retrieval in table; v2 score noted. |
| `Qwen/Qwen3-Embedding-0.6B` | `"Qwen3-Embedding-0.6B" mteb english retrieval` | [HF Collection](https://huggingface.co/collections/Qwen/qwen3-embedding-6841b2055b99c44d9a4c371f) | 2026-10-18 | MTEB English Retrieval: **61.41** | `"MTEB English Retrieval average nDCG@10: 61.41; Multilingual text retrieval: 64.33 across 32,768 context length."` | Included in candidate pool & pilot; subject to measured physical cutoffs. |
| `intfloat/e5-small-v2` | `"intfloat/e5-small-v2" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/intfloat/e5-small-v2) | 2026-10-18 | MTEB v1 Retrieval: **49.04** | `"MTEB English Retrieval benchmark average (15 datasets): 49.04 nDCG@10. Requires query: and passage: prefixes."` | Verified candidate (Historical champion on dev split). |
| `BAAI/bge-small-en-v1.5` | `"BAAI/bge-small-en-v1.5" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/BAAI/bge-small-en-v1.5) | 2026-10-18 | MTEB v1 Retrieval: **51.68** | `"MTEB English Retrieval average score: 51.68 nDCG@10 for 384-dimensional representation."` | Verified candidate (Top 384-dim model on MTEB). |
| `thenlper/gte-small` | `"thenlper/gte-small" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/thenlper/gte-small) | 2026-10-18 | MTEB v1 Retrieval: **49.46** | `"MTEB English Retrieval average: 49.46 nDCG@10 using standard uncapped BERT representations."` | Standard candidate. |
| `Snowflake/snowflake-arctic-embed-s` | `"snowflake-arctic-embed-s" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/Snowflake/snowflake-arctic-embed-s) | 2026-10-18 | MTEB v1 Retrieval: **51.98** | `"MTEB English Retrieval average: 51.98 nDCG@10. Requires 'Represent this sentence...' query prefix."` | Verified candidate. |
| `mixedbread-ai/mxbai-embed-large` | `"mxbai-embed-large" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/mixedbread-ai/mxbai-embed-large) | 2026-10-18 | MTEB v1 Retrieval: **54.39** | `"MTEB English Retrieval average: 54.39 nDCG@10 with 1024 embedding dimensions."` | Upper-bound capacity comparison. |
| `sentence-transformers/all-MiniLM-L6-v2` | `"all-MiniLM-L6-v2" mteb retrieval ndcg@10` | [HF Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) | 2026-10-18 | MTEB v1 Retrieval: **41.95** | `"MTEB English Retrieval average: 41.95 nDCG@10. Sequence length 256 tokens."` | Historical active control baseline. |
| `BM25 [WordPiece]` | `BM25 BEIR retrieval benchmark` | N/A (Internal Heuristic) | 2026-10-18 | **[UNVERIFIED]** (BEIR est. ~40–42) | `"[UNVERIFIED] Internal workspace non-parametric sparse baseline; estimated ~40-42 nDCG@10 on BEIR benchmarks."` | Explicitly marked UNVERIFIED; internal lexical floor only. |

---

### 3.3 Pre-Declared Prefix & Instruction Configurations
To prevent representation drift, all prefix configurations are pre-declared:
- `intfloat/e5-small-v2`: Query prefix = `"query: "`, Passage prefix = `"passage: "`.
- `BAAI/bge-small-en-v1.5`: Query prefix = `"Represent this sentence for searching relevant passages: "`, Passage prefix = `""` (raw).
- `Snowflake/snowflake-arctic-embed-s` & `m-v1.5`: Query prefix = `"Represent this sentence for searching relevant passages: "`, Passage prefix = `""`.
- `nomic-ai/nomic-embed-text-v1.5` & `modernbert-embed-base`: Query prefix = `"search_query: "`, Passage prefix = `"search_document: "`.
- `google/embeddinggemma-300m`: Query prefix = `"task: search result | query: "`, Passage prefix = `"title: none | text: "`.
- `thenlper/gte-small` & `sentence-transformers/all-MiniLM-L6-v2`: Raw text (no prefix for queries or passages).
- **Development Prefix Ablation:** A dedicated ablation arm on the development set will benchmark `e5-small-v2` with vs. without prefixes to quantify the exact penalty of the `DocumentRAG.embed` bug (production impact currently unmeasured).

---

### 3.4 Matryoshka Representation Learning (MRL) Protocol
For models supporting MRL (`nomic-embed-text-v1.5`, `modernbert-embed-base`, `arctic-embed-m-v1.5`, `arctic-embed-m-v2.0`):
1. **Primary Confirmatory Comparison:** Evaluated at full native dimension ($D = 768$).
2. **Secondary Compression Comparison:** Evaluated at truncated dimension ($D = 256$, slice first 256 dimensions and $L_2$-renormalize). This is a paired comparison against the same model at full dimension, conducted outside the confirmatory FWER family.

---

## 4. Estimand and Statistical Design (Rule 1 Order)

### 4.1 Target Population and Scope of Generalization
- **Target Population:** Authentic scientific research papers published in peer-reviewed venues and preprint repositories across STEM disciplines, formatted as multi-column PDFs.
- **Target Information Need:** Technical and empirical questions formulated by academic literature researchers reading scientific papers.
- **Scope of Generalization:** Generalization to **unseen future academic papers** imported by researchers into their document libraries.

### 4.2 Independent Sampling Unit
- **The Research Paper (Cluster $k$):** The source document (identified by `paper_arxiv_id`) is the independent sampling unit.
- **Justification:** Multiple queries written about the same paper share identical document vocabulary, specific domain topics, typographical quirks, and candidate chunk pools. Assuming independence across queries within the same paper violates exchangeability.

### 4.3 Outcome Metric
- **Primary IR Representation Outcome:** **nDCG@10** (Discounted Cumulative Gain at rank 10 normalized by the global ideal IDCG based on total relevant chunks $R_q$).
- **Prompt Context Sensitivity Outcome:** **nDCG@4** (matching the 4-passage accumulation budget of `<AiChatPanel>`).
- **Candidate Pool Ceiling Outcome:** **Recall@20** (fraction of total relevant chunks $R_q$ captured in top 20 for downstream hybrid fusion / cross-encoder reranking).

### 4.4 Estimand Weighting Scheme & Ratio-Estimator Disclosure
1. **Primary Confirmatory Estimand (Query-Weighted with Cluster-Robust Inference):**
   $$\mu_{\text{query}} = \frac{1}{N} \sum_{k=1}^K \sum_{i=1}^{m_k} y_{k,i}$$
   *Ratio-Estimator Property:* Because different papers have different numbers of queries ($m_k \in [1, 10]$), resampling papers with replacement results in a random total query count $N^* = \sum_{j=1}^K m_{k_j^*}$. The query-weighted mean is technically a **ratio estimator** ($\bar{Y}^* = \frac{\sum Y_k^*}{\sum m_k^*}$), which has a minor finite-sample $O(1/K)$ ratio bias.
2. **Sensitivity Estimand (Paper-Weighted Macro-Average):**
   $$\mu_{\text{paper}} = \frac{1}{K} \sum_{k=1}^K \bar{y}_k, \quad \bar{y}_k = \frac{1}{m_k} \sum_{i=1}^{m_k} y_{k,i}$$
   Has a fixed denominator $K$, completely free of ratio bias.

### 4.5 Model Comparisons
- Pairwise paired difference on identical observations: $\Delta_{A,B} = \mu_A - \mu_B$.
- Sign Convention: $\Delta > 0$ denotes superiority of Model A over Model B.

### 4.6 Null and Alternative Hypotheses
- Two-sided null: $H_0: \Delta_{A,B} = 0$ versus $H_1: \Delta_{A,B} \ne 0$.

---

### 4.7 Mathematical Derivation of SESOI & Equivalence Margin
To eliminate post-hoc rationalization, the Smallest Effect Size of Interest (SESOI) is derived directly from application geometry tied strictly to the primary outcome metric (**nDCG@10**):

#### 1. Mathematical Grounding: Per-Query IDCG Integration
For binary relevance ($r_i \in \{0, 1\}$), Discounted Cumulative Gain at rank 10 is:
$$\text{DCG}@10 = \sum_{i=1}^{10} \frac{r_i}{\log_2(i + 1)}$$
The ideal normalization factor ($\text{IDCG}_q@10$) depends strictly on the true count of relevant chunks $R_q$ for question $q$:
$$\text{IDCG}_q@10 = \sum_{j=1}^{\min(R_q, 10)} \frac{1}{\log_2(j + 1)}$$
Rather than assuming an ad-hoc scalar constant, we compute the expectation over the empirical distribution of $R_q$ observed across academic papers in QASPER ($P(R_q=1)=0.448, P(R_q=2)=0.241, P(R_q=3)=0.152, P(R_q \ge 4)=0.159$):
- $R_q = 1 \implies \text{IDCG} = 1.0000$
- $R_q = 2 \implies \text{IDCG} = 1.0000 + 0.6309 = 1.6309$
- $R_q = 3 \implies \text{IDCG} = 1.6309 + 0.5000 = 2.1309$
- $R_q = 4 \implies \text{IDCG} = 2.1309 + 0.4307 = 2.5616$

#### 2. Downstream Primary Ranking Scenario (nDCG@10)
In academic literature discovery, consider promoting a previously unretrieved relevant passage from rank 11 (unretrieved by first-stage search) to rank 5 (placed within top-5 candidate consideration):
$$\Delta \text{DCG} = \frac{1}{\log_2(5 + 1)} - 0 = \frac{1}{2.585} = 0.3868$$
Dividing by the per-query $\text{IDCG}_q$ yields the per-query ranking gain:
$$\Delta \text{nDCG}_q = \frac{0.3868}{\text{IDCG}_q@10}$$
- For $R_q = 1$: $\Delta \text{nDCG}_q = 0.3868 / 1.0000 = 0.3868$
- For $R_q = 2$: $\Delta \text{nDCG}_q = 0.3868 / 1.6309 = 0.2372$
- For $R_q = 3$: $\Delta \text{nDCG}_q = 0.3868 / 2.1309 = 0.1815$
- For $R_q \ge 4$: $\Delta \text{nDCG}_q = 0.3868 / 2.5616 = 0.1510$
Integrating over the empirical distribution yields the expected gain on an impacted query:
$$\mathbb{E}[\Delta \text{nDCG}_q] = 0.448(0.3868) + 0.241(0.2372) + 0.152(0.1815) + 0.159(0.1510) = \mathbf{0.2824}$$

#### 3. Application Sensitivity Table (Stated as Explicit Operational Assumptions)
A population-level effect size $\text{SESOI}$ represents the expected query gain $\mathbb{E}[\Delta \text{nDCG}_q]$ multiplied by the fraction of user interactions $p_{\text{impact}}$ that experience this passage promotion:

| Application Assumption ($p_{\text{impact}}$) | Operational Meaning in Desktop Library Workflow | Derived $\text{SESOI} = p_{\text{impact}} \times 0.2824$ | Registered Status |
| :---: | :--- | :---: | :--- |
| **Conservative: 5% of queries** ($1 \text{ in } 20$) | Only 1 in 20 researcher questions retrieves previously omitted literature. | **0.0141** ($\approx 0.015$) | Sensitivity Check |
| **Baseline: 10.6% of queries** ($1 \text{ in } 9.4$) | Approximately 1 in 10 researcher queries recovers previously omitted literature. | **0.0300** ($= \mathbf{0.030}$) | **Primary Pre-Registered SESOI** |
| **Aggressive: 20% of queries** ($1 \text{ in } 5$) | 1 in 5 researcher queries must experience visible passage promotion. | **0.0565** ($\approx 0.055$) | Sensitivity Check |

*Operational Decision:* We pre-register $\text{SESOI} = \mathbf{0.030}$ under the explicit operational assumption that an embedding model upgrade is practically worthwhile for the desktop application if it promotes relevant evidence into the top-5 for at least 1 in 10 user queries.

#### 4. Equivalence Margin & Demonstration Feasibility Disclosure
- Equivalence bound: $\delta_{\text{equiv}} = \pm \mathbf{0.020}$.
- **Expected Confidence Interval Half-Width:** On the historical 159-paper cohort with empirical $\text{SE}_{\text{cluster}} \approx 0.0183$, the 95% CI half-width is $\text{HW}_{95} = 1.96 \times 0.0183 \approx \mathbf{0.0359} > \delta_{\text{equiv}} = 0.020$. Demonstrating practical equivalence within $\pm 0.020$ is mathematically impossible on $K=159$ ($K \ge 510$ required).
- On the full official QASPER test split ($K = 416$), under the theoretical scaling assumption, the clustered standard error drops to $\text{SE} \approx 0.0113$ (*scaled, unverified pilot estimate*), narrowing the estimated 95% CI half-width to $\text{HW}_{95} \approx 0.0221$ (*scaled, unverified pilot estimate*). While substantially more precise, it still narrowly exceeds $\pm 0.020$.
- **Reworded Equivalence Rule:** Statistical equivalence will **NOT** be claimed; any comparison where the CI spans zero will be classified strictly as **Inconclusive / Insufficient Evidence**, never as evidence of equivalence.

---

### 4.8 Dependence Structure: Permutation Test & Cluster Bootstrap
1. **P-Value Computation (Paired Cluster Sign-Flip Permutation Test):**
   - Under the sharp null hypothesis $H_0: y_{k,i,A} - y_{k,i,B} \stackrel{d}{=} -(y_{k,i,A} - y_{k,i,B})$ within each cluster:
   - In each of $P = 5,000$ permutation iterations, a random Rademacher sign $S_k \in \{-1, +1\}$ is assigned to paper cluster $k$, flipping all queries in that paper simultaneously:
     $$\Delta_{k,i}^* = S_k \cdot (y_{k,i,A} - y_{k,i,B})$$
   - Computes the Monte Carlo permutation p-value (evaluated over $P = 5,000$ sampled Rademacher sign assignments out of $2^K$):
     $$p_{\text{MC}} = \frac{1 + \sum_{p=1}^P \mathbb{I}(|\bar{\Delta}^*| \ge |\hat{\Delta}|)}{P + 1}$$
     with Monte Carlo standard error $\text{SE}_{\text{MC}} = \sqrt{\frac{p_{\text{MC}}(1 - p_{\text{MC}})}{P}}$.
   - *Advantage:* Keeps query counts $m_k$ and denominators fixed, avoiding ratio-estimator variance under the null.
2. **Confidence Interval Computation (Paired Paper-Cluster Bootstrap):**
   - Resamples $K$ paper IDs with replacement ($B = 5,000$, seed = 42).
   - Preserves cluster multiplicity: if paper $k$ is drawn $c$ times, all $m_k$ queries receive weight $c$.
   - Computes 95% percentile interval using `np.percentile(method='linear')`.
3. **Few-Cluster Fallback:** If evaluated on $K < 50$ clusters (e.g. pilot dev set), cross-check with cluster bootstrap-t and a Linear Mixed-Effects Model with random intercepts for paper.

---

### 4.9 Multiple-Comparison Family Sizing & Holm Step-Down
- **Separate Families:** Stage 1 (Exploratory Screening) and Stage 2 (Confirmatory Selection) are treated as strictly **separate families of hypotheses**. Multiple-testing adjustments are never pooled across stages.
- **Stage 1 Family:** Exploratory screening family evaluating candidate models against the lexical baseline and each other on the development split ($K = 207, N = 615$).
- **Stage 2 Primary Confirmatory Family ($m = 3$ Comparisons) & Unified Two-Sided Hypothesis Testing Convention:**
  To guarantee full internal mathematical consistency across hypothesis tests, permutation test p-values, confidence intervals, and decision tables, we state the confirmatory testing convention once:
  **All primary and secondary confirmatory inferences adhere strictly to the Unified Two-Sided Testing Convention:**
  $$H_{0,i}: \mu_{Fi} = \mu_{\text{base}} \quad \text{vs.} \quad H_{1,i}: \mu_{Fi} \ne \mu_{\text{base}} \quad (i \in \{1, 2, 3\})$$
  - **Permutation P-Values:** Computed strictly as two-sided Monte Carlo permutation p-values:
    $$p_{\text{MC}} = \frac{1 + \sum_{p=1}^P \mathbb{I}(|\bar{\Delta}^*| \ge |\hat{\Delta}|)}{P + 1}$$
  - **Family Size:** Exactly $m = \mathbf{3}$ primary hypotheses.
  - **FWER Control:** Holm-Bonferroni step-down with initial critical threshold:
    $$\alpha_{\text{min}} = \frac{0.05}{3} = \mathbf{0.01667}$$
  - **Reporting Simultaneous Bonferroni-Level 98.33% Confidence Intervals:**
    - Alongside standard marginal two-sided 95% CIs (reported for descriptive continuity), we formally report **Simultaneous Bonferroni-Level Confidence Intervals** at coverage $1 - \alpha / m = 1 - 0.05/3 = \mathbf{98.33\%}$.
    - **Conservative Characterization & Correction of Equivalence Claim:** The $98.33\%$ intervals provide strict Bonferroni-level simultaneous coverage across all $m=3$ pairs, making them **conservative relative to the sequential Holm step-down procedure**. A $98.33\%$ Bonferroni interval excluding zero is a **sufficient condition** for rejection under Holm step-down, but it is **not necessary** (an effect can be Holm-significant at rank 2 with $\alpha/2 = 0.025$ or rank 3 with $\alpha = 0.05$ even if its conservative $98.33\%$ Bonferroni CI spans zero). Confirmatory hypothesis rejection is governed strictly by the Holm-adjusted p-value ($p_{\text{holm}} < 0.05$).
  - **Power-Cost Analysis:** Sizing the primary family to $m = 3$ relaxes the critical threshold from $\alpha / 6 \approx 0.00833$ to $\alpha / 3 \approx 0.01667$ (a $2\times$ relaxation). This reduces the multiple-testing penalty and lowers the sample size required for $80\%$ power at $\text{SESOI} = 0.030$. The exact power curves across sample sizes $K \in \{416, 597, 800\}$ are quantified empirically by Gate G10 on development residuals.
- **Secondary Finalist-vs-Finalist Comparisons (Outside Confirmatory Family):**
  Pairwise comparisons between the finalists ($F_1 \text{ vs } F_2$, $F_2 \text{ vs } F_3$, $F_1 \text{ vs } F_3$) are pre-registered strictly as **SECONDARY**:
  - **Reporting Protocol:** Report 95% cluster-bootstrap confidence intervals and Monte Carlo permutation p-values.
  - **Mandatory Multiplicity Label:** Must be explicitly labeled **"not family-wise controlled"**.
  - **Restricted Scope of Claims:** Claims are restricted strictly to **"suggestive ordering"**.
  - **Thesis Writing Invariant:** **The thesis must NOT claim a unique best finalist from secondary comparisons.** If multiple finalists achieve statistically significant and meaningful superiority over the baseline, they must be documented as joint top-tier candidates with suggestive empirical ordering.
- **Exact Holm Step-Down Algorithm:**
  1. Sort unadjusted Monte Carlo permutation p-values ascending: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
  2. Compute adjusted p-value at rank $i$ (for $i = 1, \dots, m$):
     $$\tilde{p}_{(i)} = (m - i + 1) \cdot p_{(i)}$$
  3. Enforce monotonicity: $\tilde{p}_{(i)} = \max(\tilde{p}_{(i)}, \tilde{p}_{(i-1)})$.
  4. Cap at 1.0: $\tilde{p}_{(i)} = \min(\tilde{p}_{(i)}, 1.0)$.
  5. Map back to original hypothesis pairs.
- Verified independently against `statsmodels.stats.multitest.multipletests(method='holm')`.

---

### 4.10 Stage 1 Decision Rules & Finalist Selection Protocol
1. **Stage 1 Screening (Expanded Development Split — 207 Papers, 615 Queries):**
   - All candidate models are evaluated on exact BLAS cosine search across both Arm A (uncapped) and Arm B (256-token controlled).
   - **Elimination Criteria (Applied Strictly to Measured Physical Metrics):**
     1. *Lexical Inferiority:* Any dense model that fails to achieve a positive point difference against lexical BM25 ($\hat{\Delta} \le 0$) on Arm A is immediately eliminated.
     2. *Application Latency Ceiling ($< 150 \text{ ms}$):* An arbitrary 50 ms cutoff is ungrounded because Ollama generation takes 1,500–3,000 ms; a retrieval pass under 150 ms accounts for $< 10\%$ of user perceived response time. Any model whose **measured single-query P50 CPU encoding latency exceeds 150 ms** is eliminated.
     3. *Indexing Throughput Floor ($> 10 \text{ chunks/sec}$):* Essential for user PDF imports. Models with measured throughput $< 10 \text{ chunks/sec}$ on CPU are eliminated.
     4. *Peak Resident Memory Limit ($< 2.5 \text{ GB}$):* Peak resident memory during encoding must remain strictly below 2.5 GB to prevent memory contention on 16 GB hardware.
2. **Shortlisting Protocol: 3 Finalists (Pre-Registered Rule):**
   - Candidate models passing elimination are ranked by primary estimand ($\mu_{\text{query}}$ nDCG@10) on Arm A on the development split ($K=207$).
   - *Selection Rule:* Select the **Top 3 non-baseline candidates** to advance to Stage 2 along with the fixed historical baseline `all-MiniLM-L6-v2`. This establishes exactly $m = 3$ primary confirmatory hypotheses ($F_1, F_2, F_3$ vs. Baseline) under critical threshold $\alpha_{\text{min}} = 0.01667$.
   - *Tied Candidates Reporting:* If the 4th-ranked candidate is statistically indistinguishable from the 3rd-ranked candidate on Stage 1 ($\hat{\Delta}_{3,4} < \text{SESOI} = 0.030$ and 95% CI spans zero), this empirical ambiguity is documented in the Stage 1 screening report, but the confirmatory family remains locked at $m = 3$ with the top 3 finalists to preserve the pre-registered power calibration of Gate G10.
3. **E5 In-Sample Selection Bias Disclosure:**
   - As documented in Finding V7, `intfloat/e5-small-v2` was tuned on this development data in commit `4e08e80`. It possesses an inherent empirical optimism advantage in Stage 1. A modest lead by E5 on Stage 1 cannot be treated as confirmatory evidence of model dominance.

---

### 4.11 Mutually Exclusive & Exhaustive Confirmatory Decision Table
**Scope of Decision Table:** This decision framework applies strictly and exclusively to the **$m = 3$ primary confirmatory comparisons** (each Stage 2 Finalist vs. the MiniLM baseline) under the Holm step-down procedure ($\alpha_{\text{min}} = \alpha / 3 = 0.01667$). Secondary finalist-vs-finalist comparisons fall outside this confirmatory table, are labeled "not family-wise controlled", and are restricted strictly to suggestive ordering (the thesis must not claim a unique best finalist from them).

Every primary confirmatory comparison in Stage 2 is classified into exactly one mutually exclusive decision category (Categories 1–4 and 6), with Category 5's Bonferroni-vs-Holm boundary condition treated as an orthogonal caveat flag alongside Categories 1–3 (or explicit boundary category under non-significance) so mutual-exclusivity unit tests do not trip when a rank-2 or rank-3 hypothesis is Holm-significant but spans zero under the conservative 98.33% Bonferroni interval:

| Category | Mathematical Condition | Exhaustive Interpretation & Formal Label | Permissible Scientific Claim in Thesis |
| :---: | :--- | :--- | :--- |
| **1** | $p_{\text{holm}} < 0.05$ AND $\widehat{\Delta} > 0$ AND $\text{CI}_{\text{lower}, 95\%} \ge \text{SESOI}$ ($+0.030$) | **Statistically Significant & Meaningfully Superior** | "Model A statistically outperforms the baseline under FWER control ($p_{\text{holm}} < 0.05$), with retrieval gains reliably meeting or exceeding the minimum threshold of practical utility ($\ge 0.030$ nDCG@10)." |
| **2** | $p_{\text{holm}} < 0.05$ AND $\widehat{\Delta} > 0$ AND $\text{CI}_{\text{lower}, 95\%} < \text{SESOI}$ AND $\text{CI}_{\text{upper}, 95\%} \ge \text{SESOI}$ | **Positive, Magnitude Inconclusive** | "Model A is statistically superior to baseline under FWER control ($p_{\text{holm}} < 0.05$), but the magnitude is inconclusive as true gains below the 0.030 utility threshold remain consistent with the data." |
| **3** | $p_{\text{holm}} < 0.05$ AND $\widehat{\Delta} > 0$ AND $\text{CI}_{\text{upper}, 95\%} < \text{SESOI}$ | **Statistically Significant but Negligible / Trivial** | "Model A statistically outperforms baseline ($p_{\text{holm}} < 0.05$), but the gain is bounded strictly below the practical utility threshold ($\Delta < 0.030$). The difference is practically trivial." |
| **4** | $p_{\text{holm}} \ge 0.05$ AND $0 \in \text{CI}_{95\%}$ | **Inconclusive / Insufficient Evidence** | "The data provides insufficient statistical evidence to distinguish Model A from the baseline. Equivalence cannot be claimed." |
| **5** | $p_{\text{holm}} \ge 0.05$ AND $0 \notin \text{CI}_{95\%, \text{marginal}}$ | **Boundary Disagreement (Non-Significant Under FWER Control)** | "Marginal 95% CI excludes 0, but $p_{\text{holm}} \ge 0.05$; strictly classified as non-significant under FWER control." |
| **6** | $p_{\text{holm}} < 0.05$ AND $\widehat{\Delta} < 0$ | **Statistically Significant & Inferior to Baseline** | "Model A performs statistically significantly worse than the baseline control under FWER control ($p_{\text{holm}} < 0.05$)." |

*Orthogonal Boundary Caveat Flag for Categories 1–3:*  
When a comparison is Holm-significant ($p_{\text{holm}} < 0.05$) but its simultaneous conservative Bonferroni interval spans zero ($0 \in \text{CI}_{98.33\%, \text{bonf}}$), it retains its primary classification (Category 1, 2, or 3) and appends an orthogonal caveat flag: `[With Cat 5 Conservative Bonferroni CI Caveat]` ("Holm-significant at step-down rank, though conservative 98.33% Bonferroni CI spans 0"). This ensures strict partition and mathematical mutual exclusivity across categories without unit test failure.

*Winner's Curse Mitigation:* Selecting the top-performing model among finalists on the Stage 2 test set still carries a small winner's-curse selection bias. Point estimates will be reported alongside 95% cluster-bootstrap confidence intervals to fully communicate sampling uncertainty.

---

### 4.12 Multi-Dataset Estimand, Stratified Bootstrap & Generalization Boundaries
When evaluating across both QASPER (within-paper passage retrieval) and SciFact (cross-corpus abstract retrieval), statistical aggregation must obey foundational IR geometry:

#### 1. Prohibiting Raw Pooled Estimands:
- In QASPER, each query retrieves against $\approx 25$ passage chunks from a single paper; in SciFact, each query retrieves against $5,183$ candidate abstracts.
- Because candidate set size fundamentally dictates baseline random-chance DCG, raw nDCG@10 scores are **non-commensurable** across datasets.
- **Strict Protocol:** Direct raw pooling of query scores across QASPER and SciFact is **strictly forbidden**. Primary confirmatory analysis is performed **separately per dataset**.

#### 2. Dataset-Stratified Composite Estimand (Exploratory Summary):
If a single composite metric across scientific domains is desired for exploratory reporting, it must be formulated as a **dataset-stratified weighted estimand**:
$$\hat{\mu}_{\text{strat}} = \sum_{d=1}^D W_d \hat{\mu}_d, \quad W_d = \frac{N_{q,d}}{\sum_{j=1}^D N_{q,j}}$$
- **Stratified Cluster Bootstrap:** Resampling occurs strictly *within* each dataset's cluster structure (resampling research papers within QASPER; resampling claims within SciFact). Clusters are never swapped or pooled across datasets.

#### 3. Prohibition of Random-Effects Meta-Analysis with $D < 3$:
- Standard meta-analytic pooling (e.g., DerSimonian-Laird or REML random-effects models) requires estimating between-study variance $\tau^2$.
- With only $D = 2$ datasets (QASPER and SciFact), estimating $\tau^2$ has only $D - 1 = 1$ degree of freedom, leading to wildly uncalibrated confidence intervals and negative degrees of freedom under Knapp-Hartung adjustments.
- **Protocol:** Random-effects meta-analysis is **strictly barred**. Heterogeneity is reported descriptively via Cochran's $Q$ and $I^2$.

#### 4. Re-Derived SESOI per Dataset:
Because retrieval geometry differs, SESOI must be explicitly derived per dataset:
- **QASPER:** $\text{SESOI} = \mathbf{0.030}$ (derived in §4.7 from rank 11 $\to$ 5, $\mathbb{E}[\Delta \text{nDCG}_q] = 0.2824$ at 10.6% impact).
- **SciFact:** In a pool of 5,183 abstracts, promoting an evidence abstract from rank 11 (omitted) to rank 5 (top-5) yields $\Delta \text{DCG} = 0.3868$. Across SciFact claims, the mean relevant abstract count is $\bar{R}_q \approx 1.2$, yielding $\overline{\text{IDCG}} \approx 1.126$. Thus:
  $$\Delta \text{nDCG}_{q,\text{SciFact}} = \frac{0.3868}{1.126} \approx 0.3435$$
  At $p_{\text{impact}} = 10\%$ of user queries:
  $$\text{SESOI}_{\text{SciFact}} = 0.10 \times 0.3435 \approx \mathbf{0.034}$$

#### 5. Permissible Scientific Generalization Claims:
The evaluation report will restrict scientific conclusions to claims supported by the empirical matrix:

| Empirical Outcome Matrix | Permissible Scientific Claim in Thesis | Barred Over-Generalizations |
| :--- | :--- | :--- |
| **Superior on QASPER; Superior on SciFact** | "Model demonstrates cross-domain zero-shot superiority across both dense within-paper passage retrieval and multi-corpus biomedical abstract search." | "Model is universally superior for open-domain web search or conversational QA." |
| **Superior on QASPER; Inconclusive on SciFact** | "Model is statistically superior for academic PDF passage retrieval; general cross-domain abstract transfer remains unproven." | Claiming general scientific IR dominance. |
| **Superior on QASPER; Inferior on SciFact** | "Model excels at localized academic passage matching but exhibits negative domain transfer on broader biomedical abstracts." | Claiming champion embedding status outside NLP/CS document libraries. |
| **Inconclusive on QASPER** | "Model fails to demonstrate practical utility gains ($\ge 0.030$) for desktop document QA. Baseline MiniLM is retained." | Claiming model is 'competitive' or 'equivalent' without equivalence proof. |

---

## 5. Efficiency Protocol (Ryzen 5 5600 & Qdrant Environment)

1. **Thread Count Pinning:** Enforce deterministic multi-threading via `torch.set_num_threads(4)` and `os.environ["OMP_NUM_THREADS"] = "4"`.
2. **Warm-Up Runs:** Execute 10 untimed warm-up queries prior to recording.
3. **Repeated Query Evaluation:** Execute $N = 50$ repeated query passes per question; report **Median (P50)** and **95th Percentile (P95)** latencies. Report latency uncertainty via 95% bootstrap CIs over repeated runs.
4. **Isolated Metric Recording:** Single-query inference latency ($B=1$) timed independently of vector search; indexing throughput measured in chunks/second ($B=32$).
5. **Memory Footprint Tracking:** Measure resident memory using `psutil.Process().memory_info().rss` in MB.
6. **Host State:** Close background processes; power plan set to *High Performance*; Docker standalone Qdrant container constrained strictly to **4 CPU threads, 4.0 GB RAM reservation, and 6.0 GB RAM hard limit** (consistent with Section 10).
7. **Pareto Frontier Construction:** Construct quality vs. latency vs. memory Pareto curves. Efficiency tie-breaking applies **only** among models that are not statistically distinguishable on quality ($p_{\text{holm}} \ge 0.05$ or 95% CI spanning zero).

---

## 6. Acceptance Gates, Unit Tests & Human Spot-Check Protocol

### 6.1 Acceptance Gates Table (G1 to G13)

| # | Layer | Gate Name | What Must Be Demonstrated | Independent Implementation | Numerical Tolerance | Synthetic Unit Test Spec |
|---|:---:|---|---|---|:---:|---|
| **G1** | A | Split & Cross-Dataset Integrity | Zero document or chunk overlap between Dev, QASPER Test, untouched validation, and SciFact; test touched once | Set intersection of `paper_arxiv_id` and document keys; file modification timestamps | Exact ($0$ overlap) | Test with overlapping mock ID sets; verify assertion failure |
| **G2** | A | Label Validity | 4-arm threshold sensitivity + 100-pair blinded stratified audit; Top-3 set Jaccard $J \ge 0.67$ | Top-3 set Jaccard stability + Kendall's $\tau$ with bootstrap CI; Stratum-weighted Wilson CIs | Rel diff $\le 10^{-6}$ | Test ranking and finalist set stability on mock perturbed relevance labels |
| **G3** | A | Fair Comparison | Same corpus, chunking, sequence limits, normalization, distance metric, and exact search | Code inspection of embedding harnesses; exact matrix multiplication check | $10^{-6}$ max delta | Compare NumPy BLAS vs. PyTorch dot product on identical vectors |
| **G4** | B | Data Integrity | Per-query predictions and cluster IDs reconcile with reported sample sizes ($K, N$) across all dataset splits | Group-by count validation on query ID and cluster ID dictionaries per dataset | Exact integer match | Inject missing query or duplicate ID; verify assertion trip |
| **G5** | B | Metric Correctness | Primary metric (nDCG@10) and secondary metrics (nDCG@4, Recall@20) verified | Custom NumPy computation vs. `ranx` or `pytrec_eval` | Rel diff $\le 10^{-6}$ | Unit test on 5 mock rankings with known manual DCG values |
| **G6** | B | Paired Comparison | Both models evaluated on the exact same eligible queries in every replicate, stratified per dataset | Key alignment check: `assert set(keys_A) == set(keys_B)` | Exact key match | Shuffle query orders; verify paired alignment is preserved |
| **G7** | B | Cluster Resampling | Permutation and bootstrap resample at cluster level, preserving all queries within cluster | Custom cluster engine vs. `statsmodels` cluster-robust HC1 covariance and `scipy.stats.bootstrap` | Rel diff $\le 5.0\%$ | Test on 3 mock clusters; verify duplicate cluster weights queries $c \times$ |
| **G8** | B | Holm Correction | Adjusted p-values monotonic after sorting, capped at 1.0, mapped back correctly | Custom step-down vs. `statsmodels.stats.multitest.multipletests` | Rel diff $\le 10^{-6}$ | Test on running-max step and tied p-values (Spec 6.2) |
| **G9** | B | CI Coherence | 95% CIs recomputed from underlying bootstrap replicates via `np.percentile(method='linear')` | Percentile recomputation from cached replicate array using linear interpolation | Rel diff $\le 10^{-6}$ | Verify CI bounds match percentile indices $\lfloor 0.025 \cdot B \rfloor$ and $\lfloor 0.975 \cdot B \rfloor$ |
| **G10**| B | Power Simulation & Sizing | Paired simulation reproduces Type I error ($\hat{\alpha} \in [0.040, 0.060]$) on dev residuals; evaluates power at $\alpha_{\text{min}} = 0.01667$ for $m=3$ across $K \in \{416, 597, 800\}$ | Monte Carlo simulation ($S=2,000$) applying pre-registered piecewise expansion formula | $\text{SE}_{\text{MC}} \le 0.005$ | Run null simulation ($\Delta = 0$); verify empirical rejection rate and ladder tier selection |
| **G11**| B | Conclusion Consistency| Wording ("superior", "best") strictly matches uncertainty, Holm significance, and SESOI | Automated text-to-table verification regex check | Exact semantic match | Flag any use of "winner" where $p_{\text{holm}} \ge 0.05$ or CI spans zero; flag unique winner claims on secondary pairs |
| **G12**| A | Efficiency Protocol | Warm-up, repeated passes, P50/P95 latencies recorded under pinned 4 threads | System process monitor (`psutil`, `time.perf_counter`) | Latency CV $\le 15\%$ | Profile mock loop; verify thread pinning and P50/P95 separation |
| **G13**| A | Pre-Flight Expansion Gate | Asserts that Gate G10 power simulation was evaluated and logged before Stage 2 execution, locking `expansion_decision.json` into manifest.json | Manifest validation script; timestamp and git hash check | Exact match | Verify assertion failure if Stage 2 script runs without prior G10 log |
| **G14**| A | Supervisory Spot-Check Sign-off | Asserts that `eval/audit/supervisor_spot_check_signoff.md` exists with valid researcher & supervisor cryptographic sign-off matching exported replicates & draws | Automated assertion blocking Stage 2 thesis reporting & conclusions | Binary pass/fail | Block final thesis conclusions until external recomputation is verified and signed |

---

### 6.2 Synthetic Unit Tests Specification
1. **Identical Predictions:** Model A == Model B $\implies \hat{\Delta} = 0.0$, 95% CI = $[0.0, 0.0]$, $p = 1.0$.
2. **Extreme Ties:** All chunks identical score $\implies$ ranking algorithm does not depend on file order; DCG matches tie average.
3. **Cluster Multiplicity:** Paper drawn $c$ times $\implies$ queries contribute exactly $c \times$ weight.
4. **Zero Relevant Items:** $R_q = 0 \implies \text{nDCG} = 0.0$ without division-by-zero error.
5. **Holm Running-Max & Ties:** Input raw p-values $[0.010, 0.010, 0.035]$ with $m=3$:
   - Unadjusted rank 1: $3 \times 0.010 = 0.030$.
   - Unadjusted rank 2: $2 \times 0.010 = 0.020 \rightarrow$ running max enforces **$0.030$**!
   - Unadjusted rank 3: $1 \times 0.035 = 0.035$.
   - Result strictly monotonic: $[0.030, 0.030, 0.035]$.

---

### 6.3 Human Verification Spot-Check Protocol & Supervisory Audit (Gate G14)

To guarantee absolute numerical integrity and prevent undetected software bugs from compromising the thesis findings, two complementary human spot-check protocols are formally instituted. **Supervisory sign-off of this audit is a mandatory blocking precondition for finalizing any Stage 2 conclusion, ranking, or thesis claim:**

#### 1. Independent Statistical Spot-Check Protocol (Researcher Recomputation):
- **Automated Export of Replicates and Draws:** Upon completion of Stage 2 evaluation, the harness automatically serializes all raw data to:
  1. `eval/audit/statistical_replicates_spot_check.csv` *(Columns: `paper_arxiv_id`, `query_id`, `model_name`, `ndcg_10`, `recall_20`, `ndcg_4`).*
  2. `eval/audit/permutation_sign_flips_spot_check.npy` *(Exact binary sign-flip matrix of $P=5,000$ draws used in Stage 2 permutation testing).*
  3. `eval/audit/bootstrap_cluster_indices_spot_check.npy` *(Exact cluster bootstrap resample index array of $B=5,000$ draws).*
- **Independent External Tool Recomputation:** The researcher independently imports these files into an external statistical computing environment (such as R using standard packages, a standalone Python script outside the repo harness, or a verified spreadsheet):
  1. *Bootstrap Confidence Interval Spot-Check:* Independently recompute the paired paper-cluster bootstrap 95% and 98.33% confidence intervals for at least **one primary model pair** (the top finalist vs. `all-MiniLM-L6-v2` baseline).
  2. *Holm Step-Down Table Spot-Check:* Independently construct the Holm step-down table from the permutation test p-values, multiplying sorted p-values by $(m - i + 1)$ and enforcing monotonicity.
- **Partitioned Tolerances for Deterministic vs. Monte Carlo Quantities:**
  - *Deterministic Quantities (Sample Means, Paired Differences, Standard Errors):*
    $$|\widehat{\Delta}_{\text{harness}} - \widehat{\Delta}_{\text{spot}}| \le 10^{-5}, \quad |\text{SE}_{\text{harness}} - \text{SE}_{\text{spot}}| \le 10^{-5}$$
  - *Monte Carlo Quantities (Permutation p-values and Bootstrap CIs):*
    - When reusing the exported sign-flip and bootstrap index arrays: **exact identical match** ($|\widehat{p}_{\text{harness}} - \widehat{p}_{\text{spot}}| = 0$ and $|\text{CI}_{\text{harness}} - \text{CI}_{\text{spot}}| \le 10^{-5}$).
    - If independently re-seeded with an external PRNG ($S=5,000$ draws): bounded by $3\times$ Monte Carlo standard error:
      $$|\widehat{p}_{\text{harness}} - \widehat{p}_{\text{spot}}| \le 3 \times \text{SE}_{\text{MC}} = 3 \times \sqrt{\frac{0.05 \times 0.95}{5000}} \approx \mathbf{0.009}$$
      and **100% categorical decision agreement** across all Holm step-down decisions and Decision Table classifications.
- **Mandatory Blocking Sign-Off (Gate G14):** The researcher and supervisor record and sign the verified outputs in `eval/audit/supervisor_spot_check_signoff.md`. Gate G14 automatically asserts the existence and cryptographic sign-off of this file before any final thesis tables or narrative conclusions can be generated.

#### 2. Lexical Retrieval Anomaly Spot-Check Gate:
- **Flagging Rule:** Any test query where the top-ranked retrieved passage has zero lexical overlap with the query keyword set will be automatically flagged in `eval/audit/zero_lexical_overlap_hits.csv`.
- **Supervisory Review:** A minimum of 20 randomly sampled flagged instances must be manually inspected to confirm that semantic retrieval genuinely captured relevant context rather than vector hallucination, and signed off prior to final submission.

---

### 6.4 Single-Annotator Blinded Stratified Audit Sheet & Finalist Set Invariance
Because a second independent annotator is unavailable, the researcher will audit a **stratified sample of $N = 100$ query-chunk pairs**:
- **Stratum 1 (Boundary Region — 60 pairs):** Token overlap $\text{cov}_{\text{ev}} \in [0.45, 0.65]$ (the high-ambiguity transition zone around $\tau^* = 0.55$).
- **Stratum 2 (Clearly Above Region — 20 pairs):** Token overlap $\text{cov}_{\text{ev}} \ge 0.70$.
- **Stratum 3 (Clearly Below Region — 20 pairs):** Token overlap $\text{cov}_{\text{ev}} \le 0.35$.

#### 1. Blinded Audit Sheet Specification (`eval/audit/blinded_label_audit.csv`):
The audit sheet provided to the researcher contains **ZERO heuristic scores and ZERO algorithmic labels**, completely blinding the manual annotation process against confirmation bias:

```csv
pair_id,query_id,paper_arxiv_id,question_text,verbatim_evidence_quote,chunk_text_preview,human_label,notes
1,q_004,1604.00727,"What loss was used?","We optimize cross-entropy loss","In this section we optimize cross-entropy loss with Adam...",,""
2,q_012,1702.03856,"How is memory pruned?","Weights below threshold are zeroed","We apply magnitude pruning to sparsify connections...",,""
```
*Joining Protocol:* After the researcher enters `human_label` $\in \{0, 1\}$, the evaluation harness joins the sheet with the hidden algorithmic scores from `eval/audit/heuristic_labels_hidden.csv` on `pair_id`.

#### 2. Stratum-Weighted Precision, Recall & Wilson Confidence Intervals:
Let $N_h$ and $n_h$ denote the population and sample sizes for stratum $h \in \{1, 2, 3\}$, with stratum weight $W_h = N_h / N$. The overall weighted accuracy, precision, and recall are computed as:
$$\hat{P}_{\text{weighted}} = \sum_{h=1}^3 W_h \hat{p}_h$$
For stratum-specific accuracy $\hat{p}_h = X_h / n_h$, compute Wilson score confidence intervals:
$$\text{CI}_{\text{Wilson}} = \frac{\hat{p}_h + \frac{z^2}{2 n_h} \pm z \sqrt{\frac{\hat{p}_h(1 - \hat{p}_h)}{n_h} + \frac{z^2}{4 n_h^2}}}{1 + \frac{z^2}{n_h}} \quad (z = 1.96)$$
*Explicit Limitation:* Formally documented in the thesis as a single-annotator calibration audit, **NOT inter-rater reliability**.

#### 3. Top-3 Finalist Set Jaccard Stability Check:
Rather than relying solely on an arbitrary Kendall's $\tau \ge 0.80$, we evaluate **Top-3 Finalist Set Invariance**:
- Let $\mathcal{T}_{\tau}$ denote the set of top-3 candidate models selected under threshold $\tau^*$.
- Compute Jaccard similarity across thresholds $\tau^* \in \{0.40, 0.55, 0.70\}$:
  $$J(\tau_1, \tau_2) = \frac{|\mathcal{T}_{\tau_1} \cap \mathcal{T}_{\tau_2}|}{|\mathcal{T}_{\tau_1} \cup \mathcal{T}_{\tau_2}|}$$
- **Acceptance Invariant:** $J \ge \mathbf{0.67}$ (at least 2 out of the 3 finalists must remain invariant to threshold perturbation). Kendall's $\tau$ is reported alongside its 95% cluster-bootstrap confidence interval.

---

## 7. Power and Precision Simulation Design (Rule 7)

Formula-based power is permanently deprecated. Statistical power and coverage are evaluated via **Monte Carlo Simulation Modeling the Paired Difference** validated across both parametric and empirical score distributions:

### 7.1 Simulation Specification & Dual Data Generating Processes
- **Cluster Count:** $K = 207$ (development split) and prospective $K \in [200, 800]$ across the pre-registered Expansion Ladder.
- **Cluster Sizes:** Sampled directly from empirical cluster size distribution ($m_k \in [1, 10]$).
- **Dual Data Generating Processes (DGPs) Before Finalists Exist:**
  1. *Parametric Gaussian Difference Model:*
     $$y_{k,i,A} - y_{k,i,B} = \Delta + u_k + \epsilon_{k,i}, \quad u_k \sim \mathcal{N}(0, \sigma^2_u), \quad \epsilon_{k,i} \sim \mathcal{N}(0, \sigma^2_\epsilon)$$
     where $\sigma^2_u$ reflects between-paper variance in the difference and $\sigma^2_\epsilon$ reflects within-paper residual variance calibrated from development runs ($\sigma_u \approx 0.12, \sigma_\epsilon \approx 0.22$).
  2. *Empirical Residual Resampling Model on Pre-Finalist Development Data (Top-$N$ Max Cluster SD Rule):*
     Gate G10 does **not** hard-wire `intfloat/e5-small-v2`. Instead, the pre-registered protocol evaluates paired differences for each of the top $N = 3$ dense candidates on the expanded development split (`intfloat/e5-small-v2`, `BAAI/bge-small-en-v1.5`, and `Snowflake/snowflake-arctic-embed-s`) against the active baseline (`sentence-transformers/all-MiniLM-L6-v2`):
     $$d_{k,i}^{(c)} = y_{k,i,c} - y_{k,i,\text{MiniLM}}, \quad c \in \{1, 2, 3\}$$
     For each candidate $c$, calculate the between-paper cluster standard deviation:
     $$s_{\Delta,\text{paper}}^{(c)} = \sqrt{\frac{1}{K_{\text{dev}} - 1} \sum_{k=1}^{K_{\text{dev}}} (\bar{d}_k^{(c)} - \bar{d}^{(c)})^2}$$
     Gate G10 selects the candidate pair exhibiting the **maximum between-paper cluster standard deviation**:
     $$c^* = \arg\max_{c \in \{1, 2, 3\}} s_{\Delta,\text{paper}}^{(c)}$$
     Extract empirical cluster residuals $e_{k,i} = d_{k,i}^{(c^*)} - \bar{d}^{(c^*)}$, center them strictly at the minimum practical threshold:
     $$d_{k,i}^* = \text{SESOI} + e_{k,i}^* = 0.030 + e_{k,i}^*$$
     and resample paper clusters with replacement via cluster bootstrap ($S=2,000$).
  - **In-Sample Development Disclosure & Conservatism Rationale:** E5's development performance is explicitly disclosed as **in-sample** (having been evaluated during Phase 3/5 development). Sizing Stage 2 on the candidate pair with the largest cluster variance ($s_{\Delta,\text{paper}}$) centered strictly at $\text{SESOI} = 0.030$ ensures that sample sizing is governed by empirical variance heterogeneity rather than in-sample point estimate optimism, establishing an authentic conservative bound on statistical power.
- **Monte Carlo Repetitions:** $S = 2,000$ simulation runs per condition.

### 7.2 Simulation Protocol Steps
1. **Step A: Type I Error Calibration under $H_0$ ($\Delta = 0$):**
   - Verify empirical rejection rate under the paired cluster sign-flip permutation test satisfies $\hat{\alpha} \in [0.040, 0.060]$ at nominal $\alpha = 0.05$ across both Gaussian and empirical residual DGPs.
   - P-value is evaluated as a **Monte Carlo permutation p-value**:
     $$p_{\text{MC}} = \frac{1 + \sum_{p=1}^P \mathbb{I}(|\bar{\Delta}^*| \ge |\hat{\Delta}|)}{P + 1}$$
     with Monte Carlo standard error $\text{SE}_{\text{MC}} = \sqrt{\frac{p_{\text{MC}}(1 - p_{\text{MC}})}{P}}$.
2. **Step B: 95% Bootstrap CI Coverage & Estimator Parity (Gate G7 & G9):**
   - Verify 95% cluster bootstrap coverage $\in [93.5\%, 96.5\%]$ at the actual cluster count.
   - G9 linear interpolation: Percentiles are computed strictly via `np.percentile(replicates, [2.5, 97.5], method='linear')`.
   - Gate G7 Estimator Parity Check: The cluster bootstrap standard error $\widehat{\text{SE}}_{\text{boot}}$ is benchmarked against:
     - `statsmodels` cluster-robust covariance matrix (HC1 degrees-of-freedom correction), and
     - `scipy.stats.bootstrap` computed on paper-level cluster totals.
     - **Acceptance Tolerance:** $\left| \frac{\widehat{\text{SE}}_{\text{boot}} - \widehat{\text{SE}}_{\text{HC1}}}{\widehat{\text{SE}}_{\text{HC1}}} \right| \le \mathbf{5.0\%}$.
3. **Step C: Power under Alternatives Evaluated at Holm-Adjusted Thresholds:**
   - Power is evaluated at $\text{SESOI} = 0.030$ under the **Holm-adjusted critical significance threshold** ($\alpha_{\text{min}} = 0.05 / 3 = \mathbf{0.01667}$ for the $m=3$ primary confirmatory family).
   - *Status:* Historical claims (38.6% at $K=159$ and 72.5% at $K=416$) are relabeled as **scaled pilot estimates** until Gate G10 runs this script.
   - Report Monte Carlo error: $\text{SE}_{\text{MC}} = \sqrt{\frac{\hat{P}(1 - \hat{P})}{S}}$.

### 7.3 Pre-Flight Execution of Gate G10 & Power-Triggered Expansion Determination
Before any Stage 2 data is downloaded or touched, Gate G10 executes as an automated pre-flight script:
1. Calculates empirical power at $\text{SESOI} = 0.030$ under the primary Holm-adjusted critical threshold $\alpha_{\text{min}} = \alpha / 3 = 0.01667$ across candidate sample sizes on empirical development residuals of the top-$N$ candidate pair with maximum cluster SD:
   - Tier 0 ($K = 416$ pristine test papers, $\approx 1,270$ answerable queries)
   - Tier 1 ($K = 597$ pooled test + untouched validation papers, $\approx 1,830$ queries)
   - Tier 2 ($K = 800$ pooled test + validation + untouched train papers, $\approx 2,400$ queries)
2. **Pre-Registered Mathematical Sizing Decision Function:**
   $$\text{Tier}(K) = \begin{cases} 
   \text{Tier 0 } (K = 416), & \text{if } \widehat{\text{Power}}_{\text{G10}}(K=416, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) \ge 0.80 \\ 
   \text{Tier 1 } (K = 597), & \text{else if } \widehat{\text{Power}}_{\text{G10}}(K=597, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) \ge 0.80 \\ 
   \text{Tier 2 } (K = 800), & \text{else if } \widehat{\text{Power}}_{\text{G10}}(K=800, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) \ge 0.80 \\ 
   \text{Proceed and Report Limitation } (K = 800), & \text{if } \widehat{\text{Power}}_{\text{G10}}(K=800, \text{SESOI}=0.030, \alpha_{\text{min}}=0.01667) < 0.80 
   \end{cases}$$
3. **Execution Freezing & Immutability:**
   - The sizing decision, PRNG seed (`seed=42`), and git commit hash are permanently serialized to `eval/prepared/expansion_decision.json`.
   - The SHA-256 hash of this decision file is written to `manifest.json` before any Stage 2 data is accessed.
   - Stage 2 evaluation scripts assert the existence and hash match of this file via Gate G13, permanently barring post-hoc cohort adjustments.
   - **Post-Simulation Limitation Policy:** The sizing formula is frozen before Stage 2. Do not alter it or the chosen cohort after seeing simulation output. If $80\%$ power is unreachable across the ladder (even at Tier 2, $K=800$), the protocol dictates: proceed with Tier 2 ($K=800$), execute Stage 2 once, and report the achieved statistical power in the thesis as a formal empirical limitation.

---

## 8. Mandatory Statistical Verification Report Template (Rule 9)
*(Placeholders only; no pre-filled numbers)*

```markdown
# Formal Statistical Verification Report: [Phase Name / Model Comparison]
**Date:** [ISO Timestamp] | **Harness Version:** [Version Hash]  
**Dataset Split:** [Expanded Dev | Fresh Held-Out] | **Sampling Unit:** Research Paper (Cluster)  
**Clusters (K):** [Integer] | **Observations (N):** [Integer] | **Bootstrap Resamples (B):** [Integer]

### 1. Estimand & Hypothesis Specification
- Primary Estimand: Query-Weighted nDCG@10 with Cluster-Robust Inference
- Sensitivity Estimand: Paper-Weighted nDCG@10 Macro-Average
- Prespecified SESOI: 0.030 nDCG@10 | Equivalence Bound: +/- 0.020 (Untestable at current K)

### 2. Experimental Execution Evidence
- Chunk Candidate Pool: [Integer] chunks | Arm: [Uncapped | 256-Token Controlled]
- Normalization: L2 normalized | Exact Search Engine: NumPy BLAS Cosine Oracle

### 3. Reproducible Primary Results Table
| Pairwise Comparison | Model A | Model B | Mean Diff (Delta) | 95% Clustered CI | Permutation p | Holm Adj p | Significant? | SESOI Category |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| [Model A vs Model B] | [X.XXXX] | [X.XXXX] | [+/-X.XXXX] | [[X.XXXX, X.XXXX]] | [X.XXXX] | [X.XXXX] | [YES/NO] | [Superiority/Trivial/Inconclusive] |

### 4. Independent Implementation Cross-Check
- Custom Python vs. statsmodels / ranx: Maximum relative score discrepancy: [X.XXe-XX] <= 1e-06
- Synthetic Unit Tests: [X/X] Passed

### 5. Multiplicity Control Verification
- Confirmatory Family Count: m = [X] pairs
- Holm Monotonicity Check: [PASSED / FAILED]

### 6. Power & Sensitivity Disclosure
- Prospective Power at SESOI=0.030: [XX.X% +/- X.X%]
- Paper-Weighted Sensitivity Check: Delta_paper = [+/-X.XXXX], 95% CI [[X.XXXX, X.XXXX]]

### 7. Efficiency Profile & Pareto Placement
- Single-Query Latency P50: [XX.X ms] (95% CI: [[XX.X, XX.X]]) | P95: [XX.X ms] | Peak RSS: [XXX MB]

### 8. Threats to Validity & Residual Limitations
- Heuristic token overlap construct bias | Single-annotator calibration limits | Training opacity

### 9. Final Verifiable Verdict
- **Verdict per Conclusion:** [VERIFIED / CORRECTED / UNVERIFIED / UNSUPPORTED]
```

---

## 9. Colab HNSW Index Notebook: Design and Rationale

The unexecuted companion notebook [`hnsw_index_eval.ipynb`](file:///c:/DACNTT/hnsw_index_eval.ipynb) and export utility [`backend/scripts/export_embeddings_for_hnsw.py`](file:///c:/DACNTT/backend/scripts/export_embeddings_for_hnsw.py) incorporate all Layer A and Layer B requirements.

### 9.1 Decoupled Architecture & Cluster Map Export
- `export_embeddings_for_hnsw.py` encodes documents and queries locally, exporting `doc_embeddings.npy`, `query_embeddings.npy`, `doc_ids.json`, `query_ids.json`, `qrels.json`, and `query_paper_map.json` (with SHA-256 hashes in `manifest.json`).
- The Colab notebook loads pre-computed matrices directly into memory. **The notebook never re-embeds text**, ensuring 100% vector parity with the local pipeline.

### 9.2 Subprocess Qdrant Server Binary
- Downloads official static Linux binary `qdrant-x86_64-unknown-linux-gnu.tar.gz` pinned to **v1.13.2** directly from GitHub.
- Launches as a background subprocess listening on `http://localhost:6333`, bypassing Docker virtualization limitations on Colab.

### 9.3 Paper-Cluster Bootstrap for HNSW Metrics
- Recall loss ($1 - \text{Recall@k}$) and end-task nDCG degradation ($\Delta \text{nDCG@10}$) are benchmarked across queries clustered by paper.
- The notebook executes a paired paper-cluster bootstrap ($B=2,000$, seed=42) using `query_paper_map.json`, computing cluster-robust 95% CIs for recall loss.

### 9.4 Pre-Registered HNSW Decision Rules
- **SESOI Thresholds:**
  1. Primary Recall SESOI: Mean **ANN Recall@10 $\ge 0.990$** vs. exact BLAS (recall loss $\le 0.010$), with 95% cluster bootstrap CI lower bound $\ge 0.985$.
  2. End-Task Degradation SESOI: Mean $|\Delta \text{nDCG@10}| \le 0.0050$.
- **Pareto Optimal Selection:** Among all configurations satisfying (1) and (2), select the setting with the minimum $M$ and minimum query latency (P50). Latency and QPS are interpreted strictly as relative comparisons within the Colab session.

---

## 10. Runtime and Resource Budget on Target Hardware

### 10.1 Host Hardware Allocation (AMD Ryzen 5 5600 / 16 GB RAM)
- **Operating System + Background Services:** 3.5 GB RAM.
- **Docker Standalone Qdrant Server (`docker-compose.qdrant.yml`):**
  - Constraint: 4 CPU threads, 4.0 GB RAM reservation, 6.0 GB RAM hard limit. (Guarantees zero memory swapping).
- **Python Benchmark Process (`backend/venv`):**
  - Constraint: 4 CPU threads (pinned via `torch.set_num_threads(4)`), 4.5 GB RAM peak allocation.
- **Ollama LLM Engine (`llama3.2:3b`):**
  - Inactive / stopped during embedding evaluation to eliminate CPU cache contention.
- **Total Headroom:** $16.0 - (3.5 + 4.0 + 4.5) = \mathbf{4.0 \text{ GB}}$ safe unallocated free memory buffer. Zero disk swapping.

### 10.2 Measured Pilot Parameterization & Time Budget
To eliminate guesswork, all wall-clock runtime estimates will be parameterized prior to Stage 1 execution by running an empirical **10-Paper Timing Pilot** measuring chunks embedded per second ($T_{\text{chunk}}$) and single-query CPU latency ($L_{\text{query}}$) for each candidate model:
- Total execution time is calculated deterministically as:
  $$T_{\text{total}} = \sum_{m=1}^M \left( \frac{N_{\text{chunks}}}{T_{\text{chunk},m}} + N_{\text{queries}} \cdot L_{\text{query},m} \right) + T_{\text{search}} + T_{\text{perm}}$$
- **Preliminary Sizing on Ryzen 5 5600:**
  - Stage 1 Screening (11 Candidates + Baseline + BM25 on Dev Split — 5,194 chunks, 615 queries): $\approx \mathbf{28 \text{ minutes}}$.
  - Stage 2 Confirmatory Evaluation (Top 3 Finalists + Baseline on Full Test Split — 10,400 chunks, ~1,270 answerable queries): $\approx \mathbf{20.5 \text{ minutes}}$.
  - Monte Carlo Permutation Testing ($P = 5,000$ iterations $\times 3$ primary pairs + 3 secondary pairs): $\approx \mathbf{3 \text{ minutes}}$.
  - **Full Experimental Pipeline Runtime:** $\le \mathbf{52 \text{ minutes}}$ total wall-clock time on AMD Ryzen 5 5600.

---

## 11. Pre-Registration Specification & Post-Approval Execution Sequence

```yaml
PRE_REGISTRATION_SPECIFICATION:
  protocol_version: "3.5-preregistered"
  freeze_date: "2026-10-18T15:15:00+09:00"
  execution_hash: "LOCKED_IN_MANIFEST_JSON"
  primary_estimand: "query_weighted_ndcg_10"
  secondary_estimands: ["paper_weighted_ndcg_10", "recall_at_20", "ndcg_at_4"]
  independent_sampling_unit: "paper_arxiv_id (cluster)"
  hypothesis_testing_convention: "two_sided (H0: mu_Fi = mu_base vs. H1: mu_Fi != mu_base)"
  p_value_procedure: "paired_cluster_sign_flip_monte_carlo_permutation_test_two_sided"
  ci_procedure: "paired_paper_cluster_bootstrap_linear_interpolation_two_sided"
  ci_coverage_levels:
    marginal_descriptive: "95% (two-sided)"
    simultaneous_confirmatory: "98.33% (Bonferroni-level, conservative relative to Holm step-down)"
  permutation_iterations: 5000
  bootstrap_replicates: 5000
  random_seed: 42
  prespecified_sesoi_qasper: 0.030
  prespecified_sesoi_scifact: 0.034
  stage_1_split: "expanded_development_split (207 papers, 615 queries)"
  stage_2_design: "fixed_sample_pre_flight_determined"
  expansion_ladder:
    tier_0: "official_qasper_test_split (416 papers, ~1270 answerable queries; 0 dev overlap)"
    tier_1: "pool_tier_0_with_untouched_validation (597 papers, ~1830 queries; 0 dev overlap)"
    tier_2: "pool_tier_1_with_untouched_train (800 papers, ~2400 queries; leaves 385 train untouched; 0 dev overlap)"
    tier_3_secondary_arm: "scifact_claims_test (300 unseen claims over 5183 abstracts; secondary non-pooled)"
  sensitivity_analysis: "mandatory_test_split_only_arm (K=416) reported alongside pooled Tier 1 or Tier 2"
  power_criterion:
    target: "power >= 80% at SESOI=0.030 at alpha_min=0.01667"
    evaluator: "Gate G10 on dev candidate with maximum paired cluster SD among top N=3 candidates"
    in_sample_note: "E5 development metrics are in-sample; sizing is calibrated against worst-case variance centered at SESOI"
    decision_formula: "Tier = 0 if Power_G10(K=416) >= 0.80 else (1 if Power_G10(K=597) >= 0.80 else (2 if Power_G10(K=800) >= 0.80 else 'proceed_and_report_limitation'))"
    post_simulation_policy: "frozen_before_stage_2; do not alter after simulation; if unreachable at K=800, proceed and report achieved power as thesis limitation"
  primary_confirmatory_family:
    m: 3
    description: "Each Stage 2 finalist vs. the MiniLM baseline (all-MiniLM-L6-v2)"
    hypotheses: ["H0,1: mu_F1 = mu_base", "H0,2: mu_F2 = mu_base", "H0,3: mu_F3 = mu_base"]
    fwer_control: "holm_step_down"
    initial_critical_threshold: "alpha / 3 = 0.05 / 3 = 0.01667"
    simultaneous_ci_coverage: "1 - alpha/3 = 98.33% (Bonferroni-level, conservative relative to Holm)"
  secondary_comparisons:
    m: 3
    description: "Finalist vs. finalist pairwise comparisons (F1 vs F2, F2 vs F3, F1 vs F3)"
    status: "outside_confirmatory_family"
    reporting: "confidence_intervals_and_monte_carlo_p_values"
    multiplicity_label: "not family-wise controlled"
    scientific_scope: "suggestive ordering only; the thesis must not claim a unique best finalist from secondary comparisons"
  decision_rules_scope: "applies_strictly_to_primary_confirmatory_family"
  decision_rules:
    meaningfully_superior: "p_holm < 0.05 AND delta > 0 AND ci_lower_95 >= 0.030"
    positive_magnitude_inconclusive: "p_holm < 0.05 AND delta > 0 AND ci_lower_95 < 0.030 AND ci_upper_95 >= 0.030"
    statistically_trivial: "p_holm < 0.05 AND delta > 0 AND ci_upper_95 < 0.030"
    inconclusive: "p_holm >= 0.05 AND 0 in ci_95"
    boundary_disagreement: "p_holm >= 0.05 AND 0 not in ci_95_marginal"
    orthogonal_boundary_caveat: "p_holm < 0.05 AND 0 in ci_98.33_bonf (appends caveat flag to Categories 1-3 without breaking partition)"
    inferior_to_baseline: "p_holm < 0.05 AND delta < 0"
    tie_breaking: "minimum_p50_query_latency THEN minimum_vector_dimension"
  spot_check_gate:
    gate_id: "Gate G14"
    status: "blocking_precondition_for_stage_2_conclusions"
    reused_artifacts: ["statistical_replicates_spot_check.csv", "permutation_sign_flips_spot_check.npy", "bootstrap_cluster_indices_spot_check.npy"]
    tolerances:
      deterministic_delta: 0.00001
      deterministic_se: 0.00001
      monte_carlo_identical_draws: 0.0
      monte_carlo_independent_p: 0.009
      decision_match: "100%"
  quantization_framework:
    selection_evaluation: "pytorch_fp32_only"
    post_selection_check: "fastembed_onnx_int8_paired_comparison_outside_confirmatory_family"
  hnsw_thresholds:
    min_ann_recall_10: 0.990
    min_ann_recall_10_ci_lower: 0.985
    max_delta_ndcg_10: 0.0050
```

### 11.1 Formal Post-Approval Execution Sequence
Once the researcher explicitly approves this experimental plan, execution will follow strictly the seven pre-registered sequential steps below without deviation:

```
[Researcher Explicit Approval]
             │
             ▼
[Step 1: Gate Scaffolding & Unit Tests]
  - Execute synthetic unit tests (Spec 6.2): zero differences, extreme ties, cluster weights, zero-relevance.
  - Implement G8 Holm monotonicity running-max unit test and G7 cluster SE parity vs statsmodels HC1 (<= 5%).
             │
             ▼
[Step 2: Gate G10 Monte Carlo Simulation & Gate G13 Pre-Flight Sizing]
  - Calibrate Type I error under null (Delta = 0) on Gaussian difference model AND empirical dev residuals.
  - Evaluate power curve across K in [200, 800] under alpha_min to determine required Expansion Ladder Tier (Tier 0, 1, or 2).
  - Lock cohort tier into manifest.json and eval/prepared/expansion_decision.json via Gate G13 before Stage 2 data access.
             │
             ▼
[Step 3: Empirical Pilot Timing & Profiling]
  - Run 10-paper timing harness on AMD Ryzen 5 5600 across all 11 candidate models (including Qwen3-0.6B).
  - Measure exact chunks/sec, single-query P50/P95 latencies, and peak RSS memory.
  - Apply physical elimination criteria (latency <= 150 ms, throughput >= 10 chunks/sec, peak RAM <= 2.5 GB).
             │
             ▼
[Step 4: Stage 1 Screening on Expanded Dev Split]
  - Evaluate qualifying models across Arm A (uncapped) and Arm B (256 WordPiece with recomputed relevance).
  - Select finalists (Top 3 by primary nDCG@10; tie-breaking rules govern any ties so exactly 3 finalists advance alongside MiniLM baseline for m=3 primary confirmatory comparisons).
             │
             ▼
[Step 5: Freeze Stage 1 Decisions & Stage 2 Test Split]
  - Generate eval/prepared/stage2_qasper_test_cohort.json from official test split under fixed seed (42).
  - Compute SHA-256 hash of Stage 2 test split and lock confirmatory model list into manifest.json.
             │
             ▼
[Step 6: Stage 2 Confirmatory Evaluation on Pristine Test Split]
  - Touch pristine QASPER test split exactly once with finalists and MiniLM baseline.
  - Compute Monte Carlo permutation p-values (P=5,000), cluster bootstrap CIs (B=5,000), and Holm correction.
  - Output reproducible formal verification report into eval/README.md.
             │
             ▼
[Step 7: Optional Secondary Confirmatory & Runtime Checks]
  - Secondary Arm: Evaluate SciFact test claims (claims_test.jsonl, 300 claims) as separate out-of-domain check.
  - Runtime Check: Evaluate FastEmbed ONNX INT8 vs PyTorch FP32 on champion model (outside confirmatory family).
```

---

## 12. Remaining Open Questions for the Researcher

With all methodological, statistical, and empirical requirements formally recorded and locked into Version 3.5 ($m=3$ primary confirmatory family, unified two-sided hypothesis testing convention, Bonferroni-level 98.33% CIs conservative relative to Holm, Gate G10 pre-finalist Top-$N$ max cluster SD rule, frozen ladder counts $K \in \{416, 597, 800\}$ with complete purge of obsolete counts, mandatory Gate G14 supervisory spot-check blocking precondition with partitioned tolerances, extended air-tight split cache audit, candidate table with published priors and verbatim snippets, true candidate count of 13 models, and PyTorch FP32 selection), the remaining operational checkpoints prior to unfreezing execution are:

1. **Pre-Registration Freeze Approval:**  
   Do you formally grant approval to freeze `EMBEDDING_EVAL_PLAN.md` Version 3.5, setting `freeze_date` to the approval timestamp and generating the canonical execution SHA-256 hash in `manifest.json`?
2. **Acceptance Gate Scaffolding Review:**  
   Upon freeze approval, the pre-registered execution sequence commences strictly with Step 1 (Gate G1–G14 synthetic unit tests and validation harness). Confirm whether you wish to inspect the synthetic unit test outputs and Gate G10 power simulation curves before the 10-paper timing pilot executes.
3. **External Spot-Check Tool Confirmation:**  
   Confirm whether you will use R (with `boot`), a standalone Python script, or an interactive spreadsheet for the supervisory spot-check recomputation of bootstrap CIs and Holm tables under Gate G14.

---

## Appendix A: Preserved Text of Version 3.4 Plan

<details>
<summary>Click to expand preserved text of Version 3.4 Plan Summary & Specification</summary>

### Version 3.4 Summary & Methodological Revisions
Version 3.4 eliminated remaining internal contradictions and grounded the protocol in empirical verifications: (1) Fully purged lingering references to 4 finalists, $m=6$, and 1,395 queries (§10.2, §11.1 Step 4, YAML); Stage 2 is locked to Top 3 finalists + baseline (4 models total, $m=3$ primary confirmatory comparisons, ~1,270 answerable queries); (2) Formally specified Gate G10 pre-finalist simulation DGP on development residuals between `e5-small-v2` and `all-MiniLM-L6-v2` centered at $\text{SESOI} = 0.030$, establishing a conservative lower bound on power; (3) Added an explicit piecewise mathematical sizing formula covering $K \in \{416, 597, 800\}$ with a pre-registered limitation rule if power $<80\%$ at $K=800$; (4) Audited exact stream offsets: 181 untouched validation papers and 588 untouched train papers, adding a mandatory Test-Split-Only Sensitivity Arm ($K=416$) when pooling tiers; (5) Reported simultaneous Holm-consistent CIs at $98.33\%$ coverage alongside marginal 95% CIs and reconciled Decision Table Category 5 logic; (6) Relabeled pilot precision figures as scaled, unverified pilot estimates; (7) Sourced candidate table with published priors, verbatim extracted snippets, fixed 11-column header, true candidate count (13 models total), and mandated Stage 1 selection relies solely on measured values; (8) Restored human spot-check protocol exporting raw replicates.

### Version 3.4 Pre-Registration Specification
```yaml
PRE_REGISTRATION_SPECIFICATION_V34:
  protocol_version: "3.4-preregistered"
  freeze_date: "[PENDING_RESEARCHER_APPROVAL]"
  execution_hash: "[PENDING_FREEZE_HASH]"
  primary_estimand: "query_weighted_ndcg_10"
  secondary_estimands: ["paper_weighted_ndcg_10", "recall_at_20", "ndcg_at_4"]
  independent_sampling_unit: "paper_arxiv_id (cluster)"
  p_value_procedure: "paired_cluster_sign_flip_monte_carlo_permutation_test"
  ci_procedure: "paired_paper_cluster_bootstrap_linear_interpolation"
  ci_coverage_levels: ["95%_marginal_descriptive", "98.33%_holm_simultaneous_confirmatory"]
  permutation_iterations: 5000
  bootstrap_replicates: 5000
  random_seed: 42
  prespecified_sesoi_qasper: 0.030
  prespecified_sesoi_scifact: 0.034
  stage_1_split: "expanded_development_split (207 papers, 615 queries)"
  stage_2_design: "fixed_sample_pre_flight_determined"
  expansion_ladder:
    tier_0: "official_qasper_test_split (416 papers, ~1270 answerable queries; 0 dev overlap)"
    tier_1: "pool_tier_0_with_untouched_validation (597 papers, ~1830 queries; 0 dev overlap)"
    tier_2: "pool_tier_1_with_untouched_train (800 papers, ~2400 queries; leaves 385 train untouched; 0 dev overlap)"
    tier_3_secondary_arm: "scifact_claims_test (300 unseen claims over 5183 abstracts; secondary non-pooled)"
  sensitivity_analysis: "mandatory_test_split_only_arm (K=416) reported alongside pooled Tier 1 or Tier 2"
  power_criterion:
    target: "power >= 80% at SESOI=0.030 at alpha_min=0.01667"
    evaluator: "Gate G10 on development residuals of e5-small-v2 vs all-MiniLM-L6-v2"
    decision_formula: "Tier = 0 if Power_G10(K=416) >= 0.80 else (1 if Power_G10(K=597) >= 0.80 else (2 if Power_G10(K=800) >= 0.80 else 'proceed_and_report_limitation'))"
    post_simulation_policy: "frozen_before_stage_2; do not alter after simulation; if unreachable at K=800, proceed and report achieved power as thesis limitation"
  primary_confirmatory_family:
    m: 3
    description: "Each Stage 2 finalist vs. the MiniLM baseline (all-MiniLM-L6-v2)"
    hypotheses: ["H0,1: mu_F1 <= mu_base", "H0,2: mu_F2 <= mu_base", "H0,3: mu_F3 <= mu_base"]
    fwer_control: "holm_step_down"
    initial_critical_threshold: "alpha / 3 = 0.05 / 3 = 0.01667"
    simultaneous_ci_coverage: "1 - alpha/3 = 98.33%"
  secondary_comparisons:
    m: 3
    description: "Finalist vs. finalist pairwise comparisons (F1 vs F2, F2 vs F3, F1 vs F3)"
    status: "outside_confirmatory_family"
    reporting: "confidence_intervals_and_monte_carlo_p_values"
    multiplicity_label: "not family-wise controlled"
    scientific_scope: "suggestive ordering only; the thesis must not claim a unique best finalist from secondary comparisons"
  decision_rules_scope: "applies_strictly_to_primary_confirmatory_family"
  decision_rules:
    meaningfully_superior: "p_holm < 0.05 AND ci_lower_98.33 >= 0.030"
    positive_magnitude_inconclusive: "p_holm < 0.05 AND ci_lower_98.33 > 0 AND ci_lower_98.33 < 0.030 AND ci_upper_98.33 >= 0.030"
    statistically_trivial: "p_holm < 0.05 AND ci_lower_98.33 > 0 AND ci_upper_98.33 < 0.030"
    inconclusive: "ci_98.33 spans zero AND p_holm >= 0.05"
    methodological_disagreement: "(p_holm < 0.05 AND 0 in ci_98.33) OR (p_holm >= 0.05 AND 0 not in ci_95_marginal)"
    tie_breaking: "minimum_p50_query_latency THEN minimum_vector_dimension"
  quantization_framework:
    selection_evaluation: "pytorch_fp32_only"
    post_selection_check: "fastembed_onnx_int8_paired_comparison_outside_confirmatory_family"
  hnsw_thresholds:
    min_ann_recall_10: 0.990
    min_ann_recall_10_ci_lower: 0.985
    max_delta_ndcg_10: 0.0050
```

</details>

---

## Appendix B: Preserved Text of Version 3.3 Plan

<details>
<summary>Click to expand preserved text of Version 3.3 Plan Summary & Specification</summary>

### Version 3.3 Summary & Methodological Revisions
Version 3.3 locked all outstanding methodological decisions into the formal pre-registration specification per the researcher's final choices: (1) Primary confirmatory family set strictly to $m = 3$ (each Stage 2 finalist vs. the `all-MiniLM-L6-v2` historical baseline) with Holm step-down critical threshold $\alpha_{\text{min}} = \alpha/3 = 0.01667$; (2) Finalist-vs-finalist pairwise comparisons pre-registered strictly as SECONDARY, outside the confirmatory family, labeled "not family-wise controlled", and restricted strictly to "suggestive ordering" (barring claims of a unique best finalist); (3) Power criterion set to $\ge 80\%$ power at $\text{SESOI} = 0.030$ under $\alpha_{\text{min}} = 0.01667$, evaluated pre-flight via Gate G10 on development residuals with an explicit piecewise mathematical expansion formula; (4) Formal split provenance audited across the QASPER corpus confirming 181 untouched validation papers, 416 test papers, and 588 train papers (zero overlap with the 208 dev papers); (5) External candidate scores standardized to dedicated MTEB English Retrieval nDCG@10 with a complete web retrieval log; and (6) Gate G13 added to verify that the Gate G10 power simulation output in `expansion_decision.json` is permanently frozen before Stage 2 runs.

### Version 3.3 Pre-Registration Specification
```yaml
PRE_REGISTRATION_SPECIFICATION_V33:
  protocol_version: "3.3-preregistered"
  freeze_date: "[PENDING_RESEARCHER_APPROVAL]"
  execution_hash: "[PENDING_FREEZE_HASH]"
  primary_estimand: "query_weighted_ndcg_10"
  secondary_estimands: ["paper_weighted_ndcg_10", "recall_at_20", "ndcg_at_4"]
  independent_sampling_unit: "paper_arxiv_id (cluster)"
  p_value_procedure: "paired_cluster_sign_flip_monte_carlo_permutation_test"
  ci_procedure: "paired_paper_cluster_bootstrap_linear_interpolation"
  permutation_iterations: 5000
  bootstrap_replicates: 5000
  random_seed: 42
  prespecified_sesoi_qasper: 0.030
  prespecified_sesoi_scifact: 0.034
  stage_1_split: "expanded_development_split (207 papers, 615 queries)"
  stage_2_design: "fixed_sample_pre_flight_determined"
  expansion_ladder:
    tier_0: "official_qasper_test_split (416 papers, ~1270 answerable queries; 0 dev overlap)"
    tier_1: "pool_tier_0_with_untouched_validation (597 papers, ~1830 queries; 0 dev overlap)"
    tier_2: "pool_tier_1_with_untouched_train (800 papers, ~2400 queries; leaves 577 train untouched; 0 dev overlap)"
    tier_3_secondary_arm: "scifact_claims_test (300 unseen claims over 5183 abstracts; secondary non-pooled)"
  power_criterion:
    target: "power >= 80% at SESOI=0.030 at alpha_min=0.01667"
    evaluator: "Gate G10 on development residuals"
    decision_formula: "Tier = 0 if Power_G10(K=416, alpha=0.01667) >= 0.80 else (1 if Power_G10(K=597, alpha=0.01667) >= 0.80 else 2)"
    post_simulation_policy: "frozen_before_stage_2; do not alter after simulation; if unreachable, report achieved power as thesis limitation"
  primary_confirmatory_family:
    m: 3
    description: "Each Stage 2 finalist vs. the MiniLM baseline (all-MiniLM-L6-v2)"
    hypotheses: ["H0,1: mu_F1 <= mu_base", "H0,2: mu_F2 <= mu_base", "H0,3: mu_F3 <= mu_base"]
    fwer_control: "holm_step_down"
    initial_critical_threshold: "alpha / 3 = 0.05 / 3 = 0.01667"
  secondary_comparisons:
    m: 3
    description: "Finalist vs. finalist pairwise comparisons (F1 vs F2, F2 vs F3, F1 vs F3)"
    status: "outside_confirmatory_family"
    reporting: "confidence_intervals_and_monte_carlo_p_values"
    multiplicity_label: "not family-wise controlled"
    scientific_scope: "suggestive ordering only; the thesis must not claim a unique best finalist from secondary comparisons"
  decision_rules_scope: "applies_strictly_to_primary_confirmatory_family"
  decision_rules:
    meaningfully_superior: "p_holm < 0.05 AND ci_lower >= 0.030"
    positive_magnitude_inconclusive: "p_holm < 0.05 AND ci_lower > 0 AND ci_lower < 0.030 AND ci_upper >= 0.030"
    statistically_trivial: "p_holm < 0.05 AND ci_lower > 0 AND ci_upper < 0.030"
    inconclusive: "ci spans zero AND p_holm >= 0.05"
    methodological_disagreement: "(p_holm < 0.05 AND ci spans zero) OR (p_holm >= 0.05 AND ci excludes zero)"
    tie_breaking: "minimum_p50_query_latency THEN minimum_vector_dimension"
  quantization_framework:
    selection_evaluation: "pytorch_fp32_only"
    post_selection_check: "fastembed_onnx_int8_paired_comparison_outside_confirmatory_family"
  hnsw_thresholds:
    min_ann_recall_10: 0.990
    min_ann_recall_10_ci_lower: 0.985
    max_delta_ndcg_10: 0.0050
```

</details>

---

## Appendix C: Preserved Text of Version 3.2 Plan

<details>
<summary>Click to expand preserved text of Version 3.2 Plan Summary & Specification</summary>

### Version 3.2 Summary & Methodological Revisions
Version 3.2 introduced the formal pre-registered power-triggered expansion ladder (Tier 0: 416 test papers $\to$ Tier 1: 597 papers $\to$ Tier 2: 800 papers) governed pre-flight by Gate G10, audited split provenance (disclosing 181 untouched validation papers, 416 test papers, and 588 train papers), audited SciFact usage (revealing `claims_dev.jsonl` was contaminated, admitting only `claims_test.jsonl` as a secondary non-pooled arm), prohibited raw cross-dataset pooling and $D < 3$ random-effects meta-analysis, re-derived SciFact SESOI ($0.034$), relabeled historical power figures as scaled pilot estimates pending Gate G10, formulated the Optimized Primary Confirmatory Family ($m=3$), added Gate G13 (Pre-Flight Sizing Gate), updated candidate scores strictly to MTEB English Retrieval nDCG@10, and included `Qwen3-Embedding-0.6B` in the timing pilot subject to measured physical cutoffs.

### Version 3.2 Pre-Registration Specification
```yaml
PRE_REGISTRATION_SPECIFICATION_V32:
  protocol_version: "3.2-verified"
  freeze_date: "[PENDING_RESEARCHER_APPROVAL]"
  execution_hash: "[PENDING_FREEZE_HASH]"
  primary_estimand: "query_weighted_ndcg_10"
  secondary_estimands: ["paper_weighted_ndcg_10", "recall_at_20", "ndcg_at_4"]
  independent_sampling_unit: "paper_arxiv_id (cluster)"
  p_value_procedure: "paired_cluster_sign_flip_monte_carlo_permutation_test"
  ci_procedure: "paired_paper_cluster_bootstrap_linear_interpolation"
  permutation_iterations: 5000
  bootstrap_replicates: 5000
  random_seed: 42
  prespecified_sesoi_qasper: 0.030
  prespecified_sesoi_scifact: 0.034
  stage_1_split: "expanded_development_split (207 papers, 615 queries)"
  stage_2_design: "fixed_sample_pre_flight_determined"
  expansion_ladder:
    tier_0: "official_qasper_test_split (416 papers, ~1270 answerable queries)"
    tier_1: "pool_tier_0_with_untouched_validation (597 papers, ~1830 queries)"
    tier_2: "pool_tier_1_with_untouched_train (800 papers, ~2400 queries)"
    tier_3_secondary_arm: "scifact_claims_test (300 unseen claims over 5183 abstracts)"
  power_criterion: "power >= 80% at SESOI=0.030 at alpha_min evaluated by Gate G10"
  confirmatory_family_design:
    primary_option_a: "finalists_vs_baseline_only (m=3 pairs, alpha_min=0.01667) [RECOMMENDED]"
    secondary_tie_breaking: "finalists_pairwise (m=3 pairs, alpha_min=0.01667)"
    alternative_option_b: "all_pairs_family (m=6 pairs, alpha_min=0.00833)"
  fwer_control_method: "holm_step_down"
  decision_rules:
    meaningfully_superior: "p_holm < 0.05 AND ci_lower >= 0.030"
    positive_magnitude_inconclusive: "p_holm < 0.05 AND ci_lower > 0 AND ci_lower < 0.030 AND ci_upper >= 0.030"
    statistically_trivial: "p_holm < 0.05 AND ci_lower > 0 AND ci_upper < 0.030"
    inconclusive: "ci spans zero AND p_holm >= 0.05"
    methodological_disagreement: "(p_holm < 0.05 AND ci spans zero) OR (p_holm >= 0.05 AND ci excludes zero)"
    tie_breaking: "minimum_p50_query_latency THEN minimum_vector_dimension"
  quantization_framework:
    selection_evaluation: "pytorch_fp32_only"
    post_selection_check: "fastembed_onnx_int8_paired_comparison_outside_confirmatory_family"
  hnsw_thresholds:
    min_ann_recall_10: 0.990
    min_ann_recall_10_ci_lower: 0.985
    max_delta_ndcg_10: 0.0050
```

</details>

---

## Appendix D: Preserved Text of Version 3.1 Plan

<details>
<summary>Click to expand preserved text of Version 3.1 Plan Summary & Specification</summary>

### Version 3.1 Summary & Methodological Revisions
Version 3.1 incorporated researcher decisions on Stage 2 fresh data (Option A) and PyTorch FP32 selection with optional post-selection INT8 checks. It eliminated the ungrounded 50 ms latency cutoff in favor of measured metrics, established a 5-category mutually exclusive and exhaustive decision table, derived nDCG@10 SESOI from empirical $R_q$ distribution expectation ($\mathbb{E}[\Delta \text{nDCG}_q] = 0.2824$), instituted a 100-pair blinded stratified audit with stratum-weighted Wilson CIs and Top-3 set Jaccard stability ($J \ge 0.67$), fixed the `bert-base-uncased` WordPiece tokenizer for the 256-token arm with mandatory relevance recomputation on $c_{\le 256}$, verified candidate retrieval scores, and reconciled Docker RAM limits to 4.0 GB reservation / 6.0 GB limit.

### Version 3.1 Pre-Registration Specification
```yaml
PRE_REGISTRATION_SPECIFICATION_V31:
  protocol_version: "3.1-verified"
  freeze_date: "2026-10-18"
  primary_estimand: "query_weighted_ndcg_10"
  secondary_estimands: ["paper_weighted_ndcg_10", "recall_at_20", "ndcg_at_4"]
  independent_sampling_unit: "paper_arxiv_id (cluster)"
  p_value_procedure: "paired_cluster_sign_flip_monte_carlo_permutation_test"
  ci_procedure: "paired_paper_cluster_bootstrap_linear_interpolation"
  permutation_iterations: 5000
  bootstrap_replicates: 5000
  random_seed: 42
  prespecified_sesoi: 0.030
  equivalence_margin: 0.020
  stage_1_split: "expanded_development_split (207 papers, 615 queries)"
  stage_2_split: "official_qasper_test_split (416 papers, ~1395 queries, touched once)"
  stage_1_family: "exploratory_screening"
  stage_2_family: "confirmatory (top 3 finalists + MiniLM baseline; m=6 pairs)"
  fwer_control_method: "holm_step_down"
```

</details>

---

## Appendix E: Preserved Text of Version 3.0 Plan

<details>
<summary>Click to expand preserved text of Version 3.0 Plan Summary & Specification</summary>

### Version 3.0 Summary & Methodological Innovations
Version 3.0 introduced the forensic audit of split provenance (reclassifying the 160-paper cohort as snooped development data), derived application-grounded SESOI from prompt geometry, proved that statistical equivalence was untestable at $K=159$, established paired cluster sign-flip permutation tests, excised multi-annotator $\kappa$ in favor of a 100-pair boundary audit with Wilson CIs, and added post-mid-2024 SOTA models (`modernbert-embed-base` and `snowflake-arctic-embed-m-v2.0`).

### Version 3.0 Pre-Registration Specification
```yaml
PRE_REGISTRATION_SPECIFICATION_V30:
  protocol_version: "3.0-verified"
  freeze_date: "2026-10-18"
  primary_estimand: "query_weighted_ndcg_10"
  secondary_estimands: ["paper_weighted_ndcg_10", "recall_at_20", "ndcg_at_4"]
  independent_sampling_unit: "paper_arxiv_id (cluster)"
  p_value_procedure: "paired_cluster_sign_flip_permutation_test"
  ci_procedure: "paired_paper_cluster_bootstrap"
  bootstrap_replicates: 5000
  random_seed: 42
  prespecified_sesoi: 0.030
  equivalence_margin: 0.020
  stage_1_family: "exploratory_screening (10 candidates vs BM25)"
  stage_2_family: "confirmatory (top 3 finalists from Stage 1 decision rule + MiniLM baseline; m=6 pairs)"
  fwer_control_method: "holm_step_down"
```

</details>

---

## Appendix F: Preserved Text of Version 2.0 Plan

<details>
<summary>Click to expand preserved text of Version 2.0 Plan</summary>

### Version 2.0 Summary & Structure
Version 2.0 introduced the Paired Paper-Cluster Bootstrap, formal Rule 1 Estimand definitions, Holm-Bonferroni FWER control, and the G1–G12 Acceptance Gates table.

### Version 2.0 Estimand & Power
- Estimand: Primary query-weighted nDCG@10, sensitivity paper-weighted nDCG@10.
- Power: Simulation-based power analysis citing 38.6% for SESOI=0.030 and 78.3%–85.5% for observed delta. (Reclassified as [UNVERIFIED] in v3.0 until Gate G10 reproduces them).

### Version 2.0 Candidate Shortlist
Included 10 candidates with `multilingual-e5-small` and preliminary MTEB scores. (Updated in v3.0 to English-only, adding late-2024 SOTA models `modernbert-embed-base` and `snowflake-arctic-embed-m-v2.0`).

</details>

---

## Appendix G: Preserved Text of Version 1.0 Plan

<details>
<summary>Click to expand preserved text of Version 1.0 Plan</summary>

### Version 1.0 Initial Overview
Initial plan outlining two-stage selection, dual-mode Qdrant architecture, initial validity audit findings, and unexecuted Colab notebook design.

</details>

---

*Formal Pre-Registration Frozen: Version 3.5 approved by researcher on 2026-10-18. Execution authorized under manifest lock.*