# Canonical Protocol Audit Change Log: Stages C2.2 – C2.8

*Document Status:* **Canonical Living Change Log (Consolidated & Complete)**
*Canonical Location:* [`eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md)
*Supersedes and Replaces:* `C2_2_CHANGELOG.md`, `C2_3_CHANGELOG.md`, `C2_4_CHANGELOG.md`, and `C2_5_CHANGELOG.md`
*Date of Consolidation & Expansion:* 2026-10-26
*Workspace Root:* `c:\DACNTT`
*Governing Mandate:* Stage C2.8 — Reservoir Audit, 250-Paper Protocol Revision, and Persistent Experiment Provenance
*Related Master Artifacts:*
- Protocol Single Source of Truth: [`eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)
- Canonical Experiment Provenance Registry: [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json)
- Provenance Registry Documentation: [`eval/EXPERIMENT_PROVENANCE_REGISTRY.md`](file:///c:/DACNTT/eval/EXPERIMENT_PROVENANCE_REGISTRY.md)
- Overlap Audit Utility: [`eval/scripts/check_experiment_overlap.py`](file:///c:/DACNTT/eval/scripts/check_experiment_overlap.py)
- Detailed Statistical Audit: [`eval/phases/phase_9_generation/artifacts/C2_5_STATISTICAL_VALIDITY_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/C2_5_STATISTICAL_VALIDITY_AUDIT.md)
- Exposure & Independence Audit: [`eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md)
- Overlap & Count Verification Data: [`eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json)

---

## 1. Executive Summary & Audit Evolution

This canonical document consolidates the complete audit and refinement trail for the RQ5 Small Language Model (SLM) generation evaluation protocol across Stages C2.2, C2.3, C2.4, C2.5, and C2.6.

Across all stages, the governing hard stop constraints have been strictly enforced:
- **Zero papers or questions were sampled.**
- **Zero model outputs were generated.**
- **Zero models were downloaded.**
- **Zero benchmark evaluations were executed.**
- **Zero production code, configuration, or model settings were modified.**
- **Zero Git commits were made.**

The protocol has evolved through five systematic stages:
1. **Stage C2.2 (Eligibility & Feasibility):** Established ground-truth QASPER annotation eligibility, proved atomic joint grounding (0 decoupled cases across all 5,049 questions), confirmed feasibility of $K=50, m=2$ sampling across 487 eligible papers, and designed the deterministic sampling algorithm with a 10-paper standby replacement queue.
2. **Stage C2.3 (Protocol Integrity & Exposure Governance):** Recomputed split-wide arithmetic checksums across all 5 official splits/cohorts, eliminated ambiguous exposure terminology, codified objective PDF ingestion failure criteria, and instituted a mandatory hard stop if the reserve queue is exhausted.
3. **Stage C2.4 (Protocol Clarifications):** Formalized effect size calculation, specified Holm–Bonferroni step-down adjustment, established the human review claim-splitting and 4-tier rubric, corrected memory terminology to "Sum of Measured Process RSS Values" (disclosing shared DLL double-counting on Windows and pilot script status), and calibrated power language ($\Delta = 0.030$ as an unvalidated exploratory practical-effect heuristic).
4. **Stage C2.5 (Independent Statistical Validity Audit):** Audited the legacy bootstrap $p$-value in `backend/scripts/eval_common/stats.py: line 186` ($p = \min(1, 2(r+1)/(B+1))$). Proved that uncentered resampling violates Hall & Wilson (1991) Guideline 1, that the formula is a percentile CI tail-inversion statistic (pseudo-$p$-value) rather than an exact null test, and that Holm's FWER guarantees fail due to lack of sub-uniformity.
5. **Stage C2.6 (Final Inference Review & Consolidation):** Critiqued sign-flip exchangeability assumptions for fixed models on shared questions; assessed null-centered bootstrap and paper-level paired $t$-test; established the recommended primary inferential framework (Paper-Level Paired $t$-Test for hypothesis testing + 95% Cluster Bootstrap CI for parameter estimation); and consolidated all audit changelogs into this canonical record.

---

## 2. Stage C2.2: Eligibility Validation and Sampling Feasibility

### 2.1. Canonical Annotation Eligibility Rules
Auditing the raw JSON annotation structure of official QASPER v0.3 established:
- **Zero Decoupled Annotations (`decoupled_count = 0`):** In 100% of the 5,049 questions across QASPER v0.3, there is not a single case where non-float text evidence was provided by one annotator while the usable reference answer came from a different annotator.
- **Atomic Joint Grounding (`ev_unans_count = 0`):** In 100% of cases where an annotator highlighted text evidence, that same annotator provided a valid, non-empty, non-unanswerable answer in the same annotation object.
- **Float-Only Disconnect (187 Questions in Reservoir):** The difference between answer-generation eligibility ($1,916$) and end-to-end eligibility ($1,729$) consists entirely of questions answered strictly via figures and tables (`FLOAT SELECTED: ...`) without body text paragraphs.
- **Canonical Eligibility Rules Codified:**
  - *Retrieval Eligibility:* At least one annotator provides $\ge 1$ non-empty, non-float text evidence paragraph.
  - *Answer-Generation Eligibility:* At least one annotator provides a non-unanswerable, non-empty reference answer (extractive, abstractive, or boolean; `yes_no=False` correctly counted as eligible).
  - *End-to-End Eligibility (Atomic Joint Grounding Rule):* At least one annotator simultaneously provides BOTH a valid non-float text evidence paragraph AND a usable reference answer in the SAME annotation object.

### 2.2. Reconciled Reservoir Counts (777 Unexposed Train Papers)
- Total Questions: **2,154**
- Questions with Text Evidence (Retrieval-Eligible): **1,729**
- Answer-Generation-Eligible Questions: **1,916**
- End-to-End Eligible Questions (Atomic Joint): **1,729**
- Float/Table-Only Answerable Questions: **187**
- Strictly Unanswerable Questions: **238**
- Arithmetic Checksum: $1,729 + 187 + 238 = 2,154$ (100% agreement).
- **Paper Feasibility Breakdown ($m \ge 2$):**
  - Papers with $\ge 2$ end-to-end eligible questions: **487 papers** (Confirms feasibility of $K=50$ with wide margin).
  - Papers with $== 1$ end-to-end eligible question: **226 papers** (`EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS`).
  - Papers with $== 0$ end-to-end eligible questions: **64 papers** (`EXCL_ZERO_ELIGIBLE_QUESTIONS`).
  - Checksum: $487 + 226 + 64 = 777$ papers.

### 2.3. Deterministic Sampling & Pre-Registered Standby Queue
- Candidate pool: 487 papers sorted lexicographically ascending by arXiv ID.
- Random Seed: Fixed `seed = 42`.
- Shuffled list generated via `random.Random(42)`.
- Primary cohort: Indices 0..49 ($K=50$ papers).
- Pre-registered standby queue: Indices 50..59 (10 reserve papers).
- Question selection per paper: Sorted lexicographically by 40-character `question_id` hash ascending; sub-seed `42 + int(sha256(pid)[:8], 16)`; sample exactly 2 questions without replacement ($m=2$).

---

## 3. Stage C2.3: Protocol Integrity Audit and Exposure Governance

### 3.1. Split-Wide Verification Across All 5,049 Questions
Recomputed directly from raw JSON files on disk:
- **QASPER Train (Total, 888 papers):** 2,593 questions = 2,101 retrieval/e2e + 221 float-only + 271 unanswerable + 0 decoupled.
  - ├── **RQ3 Train Cohort (111 papers):** 439 questions = 372 retrieval/e2e + 34 float-only + 33 unanswerable + 0 decoupled.
  - └── **Unexposed Train Reservoir (777 papers):** 2,154 questions = 1,729 retrieval/e2e + 187 float-only + 238 unanswerable + 0 decoupled.
- **QASPER Dev (Total, 281 papers):** 1,005 questions = 892 retrieval/e2e + 53 float-only + 60 unanswerable + 0 decoupled.
- **QASPER Test (Total, 416 papers):** 1,451 questions = 1,310 retrieval/e2e + 62 float-only + 79 unanswerable + 0 decoupled.

### 3.2. Exposure and Leakage Terminology Governance
- **Unexposed Train Reservoir:** Formally defined as a *cohort of 777 papers unexposed to the identified experiments (RQ1–RQ5)* within this project's history. Prohibited labeling it as an "independent" or "pristine" holdout because it originates from official QASPER Train.
- **QASPER Test Boundary:** Disclosed that QASPER Test was previously evaluated in RQ4 retrieval benchmarking (408 papers, 1,310 queries). Prohibited describing it as an "untouched confirmatory benchmark"; classified any full-pipeline evaluation on it as a *post-retrieval-selection evaluation*.

### 3.3. Objective PDF Ingestion Failure Criteria & Hard Stop Rule
Replacement of a primary paper from the pre-registered standby queue is permitted if and only if:
1. `EXCL_PDF_HTTP_FETCH_FAILED`: Persistent arXiv HTTP 404/403/timeout after 3 retries (5s backoff).
2. `EXCL_PDF_CORRUPTED_BINARY`: PyMuPDF `fitz.FileDataError` or missing `%PDF-` magic bytes.
3. `EXCL_PDF_ZERO_SECTIONS_EXTRACTED`: 0 text sections or total extracted body text < 100 characters.
- **Strict Anti-Bias Prohibition:** Replacement is **strictly prohibited** based on model outputs, answer quality, refusal, low retrieval score, or inconvenient results.
- **Reserve Exhaustion Hard Stop:** If all 10 reserve papers are exhausted and fewer than 50 valid papers remain, **STOP IMMEDIATELY and request user approval**.

---

## 4. Stage C2.4: Statistical and Human-Review Protocol Clarifications

### 4.1. Mathematical Effect Size Calculation
$$\Delta_{\text{obs}} = \bar{S}_{\text{cand}} - \bar{S}_{\text{base}} = \frac{1}{N}\sum_{i=1}^N (S_{\text{cand}, i} - S_{\text{base}, i})$$
evaluated across $N=100$ questions ($K=50$ papers, $m=2$ questions per paper).

### 4.2. Human Claim-Level Faithfulness Review (30 Answers)
- **Sample:** 10 questions deterministically selected via fixed stride 10 (items 1, 11, ..., 91 of manifest) evaluated across all 3 models ($10 \times 3 = 30$ outputs).
- **Blinding:** Model names anonymized as `Model_Alpha`, `Model_Beta`, `Model_Gamma` with a permuted mapping per question.
- **Atomic Factual Claim:** Defined as the smallest self-contained declarative clause or subject-predicate proposition asserting a verifiable empirical fact. Compound conjunctions ("and", "as well as") and relative clauses asserting distinct facts are split. Conversational framing is excluded.
- **Evidence Bound:** Judged strictly against the **retrieved prompt context supplied to the model**. Facts in the original PDF but omitted from the prompt cannot substantiate a claim.
- **4-Tier Rubric:**
  - `SUPPORTED`: Directly entailed by retrieved context.
  - `UNSUPPORTED`: Extrapolated details absent from context, but non-conflicting.
  - `CONTRADICTED`: Directly conflicts with or inverts context statements.
  - `MISSING_INFO`: Answer-level omission of crucial qualifiers present in context.
- **Support Ratio Denominator:** $N_{\text{SUPPORTED}} / (N_{\text{SUPPORTED}} + N_{\text{UNSUPPORTED}} + N_{\text{CONTRADICTED}})$.
- **Holistic Rating Priority:** $\text{CONTRADICTED} > \text{UNSUPPORTED} > \text{MISSING\_INFO} > \text{SUPPORTED}$.
- **Abstentions:** Appropriate refusal when context lacks evidence $\to$ `SUPPORTED`; unjustified refusal when context has evidence $\to$ `MISSING_INFO`.
- **Reviewer Staffing Caveat:** Single-reviewer results must be explicitly reported as a **limited manual audit**, and **must NEVER be described or claimed as inter-rater validation**.

### 4.3. Corrected Memory Terminology & Instrumentation Disclosure
- Mandated separate reporting for **Python Process Peak RSS (MB)** and **Ollama Runner Peak RSS (MB)**.
- If summed, labeled strictly as **"Sum of Measured Process RSS Values (Python RSS + Ollama Runner RSS)"**.
- Prohibited describing the sum as "true total physical memory", "guaranteed upper bound", or "deduplicated process-tree memory" (due to shared Windows runtime DLL and memory page double-counting).
- Disclosed that the preliminary pilot script (`evaluate_rq5_llm_generation.py`) only tracked wall-clock latency, and that continuous 100 ms dual-process `psutil` sampling is the *planned Stage C3 protocol*.

### 4.4. Statistical Power & Equivalence Calibration
- Disclaimed $\Delta = 0.030$ as a statistical significance cutoff, framing it as an unvalidated exploratory practical-effect heuristic (borrowed from earlier retrieval SESOI conventions, representing a 3 percentage-point shift in Token F1).
- Emphasized that 2,000 bootstrap replicates improve numerical stability, but **do not increase independent paper sample size ($K=50$) or guarantee statistical power**.
- Nonsignificant differences ($p_{\text{adj}} \ge 0.05$) **must never be reported as proof of model equivalence**.

---

## 5. Stage C2.5: Independent Statistical Validity Audit

### 5.1. Audit of Legacy Bootstrap p-Value (`stats.py: line 186`)
We audited the legacy formula:
$$p = \min\left(1.0, 2 \cdot \frac{r + 1}{B + 1}\right)$$
where $r = \sum \mathbb{I}(\Delta_b^* \le 0)$ for $\Delta_{\text{obs}} \ge 0$.
- **Finding 1 (Uncentered Replicates):** The bootstrap distribution is drawn from empirical data without centering: $\mathbb{E}_*[\Delta_b^*] = \Delta_{\text{obs}} \ne 0$. This violates Hall & Wilson (1991) Guideline 1: *"Resampling should be done in a way that reflects the null hypothesis, even when the null hypothesis is false."*
- **Finding 2 (Nature of Statistic):** The formula is an **empirical inversion of the percentile bootstrap confidence interval** (pseudo-$p$-value / achieved significance level). It indicates the nominal level at which the percentile CI touches zero, not the probability of the data under a null distribution.
- **Finding 3 (Failure of +1 Correction for Uncentered Bootstrap):** Adding $+1$ is derived from permutation theory under exchangeability. In an uncentered bootstrap, $+1$ prevents claiming $p = 0.0000$, but cannot correct for lack of null centering, skewness, or cluster coverage error.
- **Finding 4 (Invalid Holm–Bonferroni FWER Guarantees):** Because marginal pseudo-$p$-values lack proven sub-uniformity ($\mathbb{P}_{H_0}(P \le \alpha) \le \alpha$), applying Holm–Bonferroni cannot guarantee family-wise error rate control at $\alpha = 0.05$.

---

## 6. Stage C2.6: Final Inference Review and Audit Consolidation

### 6.1. In-Depth Comparative Analysis of Candidate Inferential Methods

We evaluated three candidate methods for testing the null hypothesis of equal expected model performance ($H_0: \mu = \mathbb{E}[\bar{D}_p] = 0$) across $K=50$ papers ($m=2$ questions per paper):

| Evaluation Dimension | Candidate 1: Paper-Level Paired Sign-Flip Test | Candidate 2: Null-Centered Cluster Bootstrap Test | Candidate 3: Paper-Level Paired $t$-Test on Paper Means |
| :--- | :--- | :--- | :--- |
| **Statistical Form** | $T^{(m)} = \frac{1}{K}\sum_{p=1}^K s_p^{(m)}\bar{D}_p$, $s_p \in \{-1, +1\}$ | Shifted $\tilde{\Delta}_b^* = \frac{1}{K}\sum (\bar{D}_p^* - \bar{D})$ | $t = \frac{\bar{D}}{s_{\bar{D}} / \sqrt{K}}$, $df = K - 1 = 49$ |
| **Null Hypothesis Tested** | **Conditional Symmetry about 0** ($H_0^{\text{sym}}: \bar{D}_p \stackrel{d}{=} -\bar{D}_p$) | **Zero Population Mean** ($H_0: \mu = 0$) | **Zero Population Mean** ($H_0: \mu = 0$) |
| **Exchangeability / Symmetry Assumption** | **Assumes Reflection Symmetry.** *Critical Caveat:* Comparing two fixed, deterministic models on shared questions does NOT make paper-level differences exchangeable or symmetric! Models differ in architecture and prompt sensitivity; under $H_0: \mu = 0$, differences can be highly skewed (e.g. Model A wins by small margins on many questions, Model B wins by huge margins on few questions). If skewed, sign-flipping violates the true null distribution. | Does NOT assume symmetry. Assumes location-shift model (centered empirical distribution approximates null shape). | Does NOT assume symmetry. Assumes sample mean $\bar{D}$ is approximately normally distributed by CLT across $K=50$ independent clusters. |
| **Variance / Studentization** | Non-parametric; does not studentize. | Unstudentized shift assumes homoskedasticity; studentized bootstrap-$t$ is numerically unstable with discrete F1 scores. | Standard cluster-robust SE: $s_{\bar{D}} / \sqrt{K}$. Studentized by construction. |
| **Finite-Sample Calibration ($K=50$)** | Exact for testing symmetry, but **not exact for testing zero mean difference under skewness**. | Asymptotic approximation with Monte Carlo simulation noise; $O(K^{-1/2})$ error. | **Asymptotically valid under CLT ($K=50$); smooth continuous $t_{49}$ distribution.** |
| **Multiplicity Control (Holm)** | Valid only if symmetry holds. | Approximate. | **Rigorous FWER control: $p$-values are continuous and strictly sub-uniform under $H_0$.** |
| **Computation & Transparency** | Monte Carlo permutation ($M=10,000$), seed-dependent. | Monte Carlo bootstrap ($B=2,000$), seed-dependent. | **Closed-form algebraic formula; zero simulation randomness; 100% reproducible.** |

### 6.2. Methodological Decision and Primary Recommendation

#### Selected Primary Inferential Framework: Decoupled Dual-Architecture
1. **Primary Parameter Estimation & Uncertainty (Retained):**
   - **Observed Effect Size:** $\Delta_{\text{obs}} = \frac{1}{50}\sum_{p=1}^{50}\bar{D}_p = \bar{S}_{\text{cand}} - \bar{S}_{\text{base}}$ across the $N=100$ questions.
   - **Confidence Interval:** **95% Paper-Clustered Paired Bootstrap Percentile Confidence Interval** $[\Delta_{2.5\%}^*, \Delta_{97.5\%}^*]$ ($B=2,000$, `seed=42`).
   - *Rationale:* Completely non-parametric; captures empirical estimation uncertainty and potential skewness without imposing distributional assumptions.
2. **Primary Formal Hypothesis Testing (Recommended):**
   - **Paper-Level One-Sample Paired $t$-Test on the 50 Paper Mean Differences $\bar{D}_p$ ($df = 49$)** with Holm–Bonferroni step-down adjustment.
   - *Rationale:* Directly tests $H_0: \mu = 0$ (unlike the sign-flip test, which requires unjustified symmetry); absorbs all intra-paper correlation into independent paper clusters; justified by the Central Limit Theorem across 50 bounded random variables; provides continuous, strictly calibrated $p$-values that validate Holm–Bonferroni FWER control; and eliminates Monte Carlo simulation noise.
   - *Reporting:* Both unadjusted 95% bootstrap CIs and Holm-adjusted $t$-test $p$-values will be reported side-by-side. If a marginal CI excludes zero but $p_{\text{adj}} \ge 0.05$, it will be explicitly reported as failing to achieve family-wise statistical significance.

---

## 7. Consolidation Ledger and Document References

### 7.1. Superseded Files Removed
Following complete consolidation into this canonical document, the following four standalone changelog files were deleted:
- `eval/phases/phase_9_generation/artifacts/C2_2_CHANGELOG.md`
- `eval/phases/phase_9_generation/artifacts/C2_3_CHANGELOG.md`
- `eval/phases/phase_9_generation/artifacts/C2_4_CHANGELOG.md`
- `eval/phases/phase_9_generation/artifacts/C2_5_CHANGELOG.md`

### 7.2. Preserved In-Depth Reports
The detailed underlying audit reports remain active, intact, and cross-referenced:
- [`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md) (Master Protocol Single Source of Truth)
- [`C2_5_STATISTICAL_VALIDITY_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/C2_5_STATISTICAL_VALIDITY_AUDIT.md) (Complete Mathematical Bootstrap Audit)
- [`DEC03_EXPOSURE_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md) (Complete Dataset Exposure Audit)
- [`dec03_exposure_overlap_report.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json) (Verified Overlap and Stratification Data)

---

## 8. Formal Recording of Approved Decisions & Calibration Conditions (Stage C2.6)

On 2026-10-25, the user formally reviewed and approved the Stage C2.6 methodological decisions with the following strict conditions:

1. **Statistical Inference Approval & Required Caveats:**
   - **Approved Primary Test:** Paper-level one-sample paired $t$-test on the 50 paper-mean paired differences ($df = 49$), with Holm–Bonferroni multiple-testing correction across the 3 pre-registered comparisons.
   - **Retained Uncertainty Interval:** Paper-clustered paired bootstrap percentile 95% CI ($B = 2,000$, `seed = 42`) for parameter estimation.
   - **Calibrated Statistical Language:** Corrected all wording implying that the Central Limit Theorem or a continuous $t$-distribution automatically guarantees valid $p$-values. The $t$-test is explicitly characterized as **approximate inference whose reliability and finite-sample calibration depend on the underlying cluster score distribution and the cluster independence assumption**.
   - **Distribution of Paper-Level Differences & Scope of the 16-Question Pilot:**
     - Verified against `backend/data/eval_benchmark_seed.json` and `eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark.json`:
       - 16 questions across 4 seminal arXiv preprints (`ATTN: 1706.03762`, `RES: 1512.03385`, `LORA: 2106.09685`, `RAG: 2005.11401`).
       - Score field: `f1` (Token F1 in $[0, 1]$).
       - Question ID alignment: 100% matched across models.
       - Verified paper mean differences:
         - `llama3.2:3b` vs `qwen2.5:0.5b`: $[-0.1216, +0.1912]$ (ATTN: $+0.1912$, RES: $-0.0573$, LORA: $+0.1716$, RAG: $-0.1216$; mean $+0.0460$, std $0.1588$).
         - `llama3.2:3b` vs `llama3.2:1b`: $[-0.1110, +0.1863]$ (ATTN: $+0.1863$, RES: $-0.0363$, LORA: $+0.0765$, RAG: $-0.1110$; mean $+0.0289$, std $0.1302$).
         - `llama3.2:1b` vs `qwen2.5:0.5b`: $[-0.0209, +0.0952]$ (ATTN: $+0.0050$, RES: $-0.0209$, LORA: $+0.0952$, RAG: $-0.0107$; mean $+0.0171$, std $0.0531$).
         - Individual query differences span $[-0.3639, +0.4482]$.
       - Scope Caveats: The pilot consists of 16 questions across four papers only. Observed differences are descriptive evidence from those four papers only, motivating robustness checks but incapable of establishing the distribution of differences in the planned 50-paper study or proving $t$-test calibration. Pilot findings must never be presented as main study results.
   - **Pre-Registered Outlier-Sensitivity Protocol (Secondary Checks):**
     a. **Wilcoxon Signed-Rank Test:** Included strictly as a **secondary non-parametric sensitivity check**, NOT an assumption-free test.
        - *Symmetry & Location Shift:* While continuous differences are not an absolute requirement in modern software, the location-shift interpretation assumes reflection symmetry of paired differences about the median. Under skewness, it tests a complex pseudo-median rank shift.
        - *Discrete Ties & Software Implementation:* Paper-level Token F1 differences are bounded and discrete. In `scipy.stats.wilcoxon` (SciPy 1.17.1), tied non-zero absolute differences receive average ranks, and ties adjust the variance via $\text{Var}(W) = \frac{1}{24}[n(n+1)(2n+1) - \frac{1}{2}\sum (t_i^3 - t_i)]$. For $n > 13$ with ties/zeros, SciPy automatically uses the asymptotic normal approximation with tie-adjusted $z$-statistic.
        - *Zero-difference handling (Alternative Sensitivities):* The number of zero-difference papers $K_0$ will be logged. Pratt's method (`zero_method="pratt"`, ranking zeros to preserve $K=50$) and Wilcoxon's zero-dropping method (`zero_method="wilcox"`, reducing to $K_{\text{eff}} = 50 - K_0$) represent alternative sensitivity analyses exploring different rank conventions on the same data, NOT independent confirmations.
     b. **10% Trimmed Mean Difference:** Trimming the 5 highest and 5 lowest paper differences ($K_{\text{trim}} = 40$) to test robustness to cluster-level outliers.
     c. **Cluster Jackknife Influence Diagnostic:** Leave-one-out cluster difference $\Delta_{(-p)} - \Delta_{\text{obs}}$ for each of the 50 papers.
   - **Equivalence Prohibition:** A nonsignificant difference ($p_{\text{adj}} \ge 0.05$) **must never be reported as evidence of model equivalence**.

2. **Human Review Staffing & Generalizability Scope:**
   - **Approved Review:** Single-reviewer descriptive audit across 30 model answers (10 questions $\times$ 3 models) preserving the four-category rubric (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `MISSING_INFO`).
   - **Strict Boundaries:** Explicitly stated that this audit **does NOT establish inter-rater reliability or definitive general faithfulness performance**, functioning solely as a limited qualitative diagnostic audit.

3. **Standby Replacement Queue Authorization:**
   - **Approved Queue:** Exactly 10 pre-registered reserve papers (indices 50–59) with existing objective technical PDF-ingestion failure criteria (`EXCL_PDF_HTTP_FETCH_FAILED`, `EXCL_PDF_CORRUPTED_BINARY`, `EXCL_PDF_ZERO_SECTIONS_EXTRACTED`), deterministic replacement order, and a mandatory hard stop if the queue is exhausted.
   - **Strict Anti-Bias Prohibition:** **NEVER replace a paper based on question difficulty, model-output quality, answer correctness, or inconvenient results.**

---

## 9. Stage C2.7 — Final Statistical Wording Corrections and Pre-Stage-C3 Readiness Review

On 2026-10-26, a final audit of statistical phrasing and methodological boundaries was executed prior to authorizing Stage C3 sample manifest generation:

### 9.1. Methodological Clarifications Applied
1. **Wilcoxon Signed-Rank Test Assumptions and Implementation Behavior:**
   - **Removed Overstated Continuity Requirement:** Corrected prior wording that incorrectly suggested continuous differences were an absolute prerequisite for applying the Wilcoxon signed-rank test.
   - **Codified Location-Shift Symmetry Requirement:** Explicitly documented that the standard location-shift interpretation (testing whether the median difference is zero) assumes that the paired differences follow an appropriate symmetric distribution about the median. Under asymmetry/skewness, the test evaluates the Hodges–Lehmann pseudo-median rank shift rather than the pure median or mean.
   - **Discrete Values & Verified Implementation Behavior:** Acknowledged that paper-level Token F1 differences are bounded in $[-1, 1]$ and discrete (evaluated on $m=2$ questions per paper). Inspected the planned Python implementation directly from source (`scipy.stats.wilcoxon` in SciPy 1.17.1, `scipy/stats/_wilcoxon.py`):
     - Ranks: Non-zero absolute ties are assigned average ranks (`_rankdata(..., 'average')`).
     - Variance adjustment: The test statistic variance is tie-adjusted via $\text{Var}(W) = \frac{1}{24}[n(n+1)(2n+1) - \frac{1}{2}\sum (t_i^3 - t_i)]$.
     - Asymptotic fallback: In the presence of ties or zeros, SciPy's `method="auto"` automatically falls back from exact calculation to the asymptotic normal approximation (`method="asymptotic"`) for sample sizes $n > 13$. Thus, at $K=50$, $p$-values are computed from the standard normal distribution using the tie-adjusted $z$-statistic, rather than an exact combinatorial distribution.
   - **Pratt vs. Wilcoxon as Alternative Sensitivity Checks:** Pratt's method (`zero_method="pratt"`) and Wilcoxon's zero-dropping method (`zero_method="wilcox"`) evaluate different ranking conventions on the same dataset. They are explicitly designated as alternative sensitivity analyses, not independent confirmations.
   - **Retained Inferential Hierarchy:** The primary inferential framework remains strictly the paper-level paired $t$-test on the 50 paper means ($df=49$) with Holm–Bonferroni step-down correction. The Wilcoxon test is retained exclusively as a secondary sensitivity check.

2. **Methodological Scope of the 16-Question Pilot Benchmark:**
   - **Descriptive Evidence Only:** Reaffirmed that the 16 queries across 4 seminal papers (`ATTN`, `RES`, `LORA`, `RAG`) provide strictly descriptive evidence from those four papers only.
   - **Cannot Establish 50-Paper Distribution:** Clarified that while pilot variance (differences spanning $-0.1216$ to $+0.1912$) motivates robustness checks, it cannot establish the true distribution of differences in the planned 50-paper evaluation.
   - **Cannot Establish Calibration:** The pilot does not, by itself, demonstrate that the primary $t$-test will be well calibrated in the main study.
   - **Prohibition on Conflation:** Pilot results must never be reported as findings of the planned 50-paper evaluation.

### 9.2. Executed Validation Checks
- **Code Inspection:** Verified SciPy 1.17.1 implementation source (`scipy/stats/_wilcoxon.py`, `_wilcoxon_nd`, `_wilcoxon_statistic`, and `_morestats.py`).
- **Data Alignment Audit:** Verified `backend/data/eval_benchmark_seed.json` against `eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark.json` (exact 16-question matching, score field `f1`, paper mean difference ranges).
- **Git Status Inspection:** Ran `git status --short` and `git status -- eval/phases/phase_9_generation/`. Confirmed working tree status.
- **Checks Not Performed:** Did not run sample generation, did not sample papers, did not download models, did not generate model outputs, did not execute benchmarks.

### 9.3. Version-Control Status and Preservation Assessment
- **Status:** All Phase 9 evaluation protocol and audit artifacts located in `eval/phases/phase_9_generation/artifacts/` are currently **UNTRACKED** in Git (`git status` reports `?? eval/phases/phase_9_generation/`).
- **Preservation Risk:** These files exist exclusively on the local filesystem. A destructive git command (e.g. `git clean -fd`) would permanently erase them.
- **Preservation Recommendation:** Once the user authorizes proceeding, stage and commit `eval/phases/phase_9_generation/` to establish version-control tracking. Under current instructions, no commit or staging has been executed.

---

## 10. Stage C2.8 — Reservoir Audit, 250-Paper Protocol Revision, and Persistent Experiment Provenance

On 2026-10-26, the evaluation protocol underwent a major audit and scale revision under Stage C2.8:

### 10.1. Re-Audit of Train Reservoir and Exact Question Eligibility
Recomputed all counts directly from the raw dataset files (`eval/data/qasper_official/` and `eval/prepared/expanded_held_out_split.json`):
1. **Raw Split Counts:**
   - QASPER Train: 888 papers, 2,593 questions.
   - QASPER Dev: 281 papers, 1,005 questions.
   - QASPER Test: 416 papers, 1,451 questions.
   - Total Corpus: 1,585 papers, 5,049 questions. Cross-split paper/question overlap: 0.
2. **Prior RQ3 Exposure in Train:** Exactly 111 Train papers (439 questions) were exposed to RQ3 dense embedding experiments (`eval/prepared/expanded_corpus.json` / `expanded_held_out_split.json`).
3. **Unexposed Train Reservoir:** Exactly $888 - 111 = \mathbf{777\text{ papers}}$ (2,154 questions) are completely unexposed to repository experiments.
4. **Step-by-Step Question Eligibility Audit on 777 Papers:**
   - Total questions in reservoir: 2,154.
   - Excluded strictly unanswerable questions (`unanswerable: true` across all annotators): 238 questions.
   - Excluded float-only evidence (`FLOAT SELECTED:` in tables/figures without body text): 116 questions.
   - Excluded empty evidence lists (`evidence: []` or whitespace): 71 questions.
   - Decoupled annotations (evidence in annotator A, answer in annotator B): 0 questions (100% atomic).
   - **End-to-End Eligible Questions:** Exactly **1,729 questions** satisfy atomic joint grounding (usable answer + non-float text evidence in the same annotator object).
5. **Paper Cluster Distribution ($m \ge 2$ requirement):**
   - Papers with $\ge 2$ eligible questions: **487 papers** (contains 1,503 eligible questions).
   - Papers with $= 1$ eligible question: **226 papers** (`EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS`).
   - Papers with $= 0$ eligible questions: **64 papers** (`EXCL_ZERO_ELIGIBLE_QUESTIONS`).
   - Parity Checksum: $487 + 226 + 64 = \mathbf{777\text{ papers}}$ ($1,503 + 226 = 1,729$ questions). Exact arithmetic parity.

### 10.2. Prior Experimental Exposure and Overlap Audit
Audited all historical cohorts across the repository:
- **RQ1 & RQ2 (Extraction & Chunking):** 47 unique papers, 127 queries (all in QASPER Dev).
- **RQ3 (Dense Embeddings):** 211 prepared, 208 in split, 207 scored (48 Dev + 49 Dev + 110 Train; 1 Train paper `1612.02482` had 0 queries). Exactly 111 Train papers exposed.
- **RQ4 Dev (Retrieval):** 276 Dev papers, 892 queries.
- **RQ4 Test (Retrieval):** 408 Test papers, 1,310 queries (8 papers in QASPER Test had 0 text chunks and were excluded: `1710.07394`, `1808.10059`, `1802.09233`, `1711.11017`, `1602.07776`, `2003.10564`, `1910.09942`, `1910.12477`).
- **RQ5 Pilot (LLM Generation):** 4 papers, 16 queries from `backend/data/eval_benchmark_seed.json` (ResNet, Attention, RAG, LoRA; non-QASPER seed).
- **Overlap with 487 Candidate Pool:** **Identically 0 across all experiments**. The 487 candidate papers are completely unexposed to all prior repository experiments.

### 10.3. Feasibility of 250-Paper Main Evaluation
- **Target:** $K = 250$ papers, $m = 2$ questions per paper ($N = 500$ questions total, $1,500$ model outputs across 3 fixed models).
- **Candidate Pool Size:** 487 eligible unexposed papers.
- **Reserve Surplus Margin:** $487 - 250 = \mathbf{+237\text{ surplus papers}}$.
- **Conclusion:** The 250-paper evaluation is **100% FEASIBLE** without weakening any eligibility criteria or reusing any previously exposed paper.

### 10.4. Persistent Experiment Provenance and Contamination Registry
Established a central, machine-readable provenance system:
1. **Canonical Registry File:** [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json)
   - Created via reproducible builder script `eval/scripts/build_experiment_provenance_registry.py`.
   - Contains 7 registered historical cohorts (RQ1, RQ2, RQ3, RQ4-Dev, RQ4-Test, RQ5-Pilot, RQ5-Main-Planned).
   - Indexes 1,589 unique papers with complete exposure event logs, classification types, and artifact links.
2. **Registry Schema & Guide:** [`eval/EXPERIMENT_PROVENANCE_REGISTRY.md`](file:///c:/DACNTT/eval/EXPERIMENT_PROVENANCE_REGISTRY.md)
   - Documents the 6 exposure categories: `UNEXPOSED_REPOSITORY`, `EXPLORATORY_EXPOSURE`, `DEVELOPMENT_SELECTION_EXPOSURE`, `CONFIRMATORY_EVALUATION_EXPOSURE`, `HISTORICAL_UNCERTAIN_PROVENANCE`, `POTENTIAL_PRETRAINING_CONTAMINATION`.
   - Defines mandatory rules for all future experiments.
3. **Automated Overlap Checking Tool:** [`eval/scripts/check_experiment_overlap.py`](file:///c:/DACNTT/eval/scripts/check_experiment_overlap.py)
   - Provides CLI commands (`--manifest`, `--papers`, `--test`, `--json`).
   - Self-test fixture verified passing with 100% deterministic accuracy.

### 10.5. Protocol Revisions Applied to DEC-03
1. **Target Scaled to 250 Papers:**
   - Primary evaluation cohort: $K = 250$ papers, $m = 2$ questions per paper ($N = 500$ questions, $1,500$ model outputs across `llama3.2:3b`, `llama3.2:1b`, `qwen2.5:0.5b`).
   - Standby Reserve Queue: Expanded to **50 pre-registered reserve papers** (indices 250..299 of deterministic shuffle, seed 42).
   - Residual Pool: 187 unselected candidate papers (indices 300..486).
   - Reserve failure rules: strictly technical PDF failures (`EXCL_PDF_HTTP_FETCH_FAILED`, `EXCL_PDF_CORRUPTED_BINARY`, `EXCL_PDF_ZERO_SECTIONS_EXTRACTED`). Hard stop if all 50 reserve papers are exhausted.
2. **Statistical Justification & Power Revision (Calibrated Boundaries):**
   - Estimation standard error $\text{SE}(\bar{D}) = s_{\bar{D}} / \sqrt{K}$ drops by a factor of $\sqrt{5} \approx 2.236$ (a **55.3% reduction in estimation uncertainty** vs $K=50$).
   - Degrees of freedom increase from $df = 49$ to $df = 249$. Critical value $t_{0.975, 249} \approx 1.9695$, closely approaching standard normal $z = 1.960$.
   - **Explicit Caveats on Normality and Statistical Power:** Expanding to $K=250$ papers does **NOT guarantee that paper-level mean differences are strictly normal, nor does it guarantee adequate statistical power for arbitrary or subtle effect sizes ($\Delta < 0.020$)**. Because Answer Token F1 scores are discrete and bounded in $[0, 1]$, finite-sample departures from normality (such as empirical point-mass spikes at zero where models tie or both fail, and potential skewness) can persist. The paired $t$-test is strictly an approximate inferential procedure whose validity depends on independence and distributional assumptions.
   - Outlier sensitivity protocol updated:
     - Wilcoxon signed-rank test on 250 paper means (Pratt's and Wilcoxon's zero-handling reported as alternative sensitivity checks; tie-adjusted asymptotic $z$).
     - 10% trimmed mean on $K_{\text{trim}} = 200$ (trimming 25 top and 25 bottom paper means).
     - Cluster jackknife influence diagnostic on all 250 papers.
3. **Approved Human Claim-Level Faithfulness Review (Option A Approved):**
   - Following user authorization, **Option A** is the approved human review protocol:
     - Exactly **20 questions** deterministically sampled from the frozen 500-question manifest using a fixed stride of 25 (items 1, 26, 51, ..., 476) across 3 models ($20 \times 3 = \mathbf{60\text{ model answers}}$).
     - Single-reviewer descriptive audit with four-category rubric (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `MISSING_INFO`) and blinded model labels (`Model_Alpha`, `Model_Beta`, `Model_Gamma`).
     - Review burden: ~3.0 hours annotation time.
4. **Latency and Memory Measurement:**
   - End-to-end latency measured on 500 benchmark queries with 2 untimed warm-ups on a discarded unexposed paper.
   - Dual-process `psutil` sampling (Python peak RSS + Ollama runner peak RSS, labeled as "Sum of Measured Process RSS Values").
5. **Section 10 Codified & Exposure Reconciliation:**
   - Mandatory check against `eval/experiment_provenance_registry.json` using `check_experiment_overlap.py` prior to finalizing any evaluation sample manifest.
   - **Historical Exposure Reconciliation (804 vs 802):**
     - $111\text{ Train} + 281\text{ Dev} + 408\text{ Test} + 4\text{ Seed} = \mathbf{804\text{ unique papers}}$ (partition-level historical total).
     - $111\text{ Train} + 279\text{ Dev} + 408\text{ Test} + 4\text{ Seed} = \mathbf{802\text{ unique papers}}$ (active benchmark run total).
     - In QASPER Dev, exactly 2 papers (`1804.00720` and `1903.07406`) contained exclusively unanswerable questions with 0 text evidence and were omitted from experimental benchmark runs ($281 - 2 = 279$). Calculating $111 + 281 + 408 + 4$ yields strictly **804**, not 802. Writing $111 + 281 + 408 + 4 = 802$ was an arithmetic error that mistakenly substituted the 281 partition count while reporting the 802 active-run total. Both counts confirm 0 overlap with the 777-paper Train reservoir.

---

## 11. Stage C2 Completion & User Authorization

**STATUS: `STAGE C2 COMPLETED & APPROVED`**

All reservoir counts, question eligibility logic, prior experimental exposure overlaps, statistical parameters, and protocol documents were audited, reconciled, and updated to target **250 eligible, experiment-unexposed papers** ($N=500$ questions, $1,500$ model outputs).

User formalized authorization:
- **250-paper target** ($K=250, m=2 \to N=500$ questions, $1,500$ model outputs).
- **Option A for human faithfulness review** (60 model answers: 20 questions $\times$ 3 models, stride 25).
- **50-paper technical-failure reserve queue** (indices 250..299 of deterministic shuffle, seed 42).
- Explicit authorization granted to generate the frozen sample manifest under Stage C3 with hard stop before model downloads/inference.

---

## 12. Stage C3 — Frozen Manifest Generation & Overlap Audit Results

On 2026-10-26, following formal user authorization, Stage C3 was executed to produce the frozen evaluation manifest:

### 12.1. Frozen Manifest Generation Artifact
- **Generator Script:** [`eval/phases/phase_9_generation/scripts/generate_sample_manifest_250.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/generate_sample_manifest_250.py)
- **Frozen Manifest File:** [`eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json)
- **Manifest File Size:** 3.49 MB (3,660,186 bytes)
- **Manifest SHA-256 Checksum:** `4a1117b822bce31f0cb240e6c7c65434c23691e4d136b305a34d895135483dc0`
- **Deterministic Seed:** `seed = 42` (with SHA-256 sub-seeds per paper: `sub_seed = 42 + int(hashlib.sha256(pid.encode()).hexdigest()[:8], 16)`)

### 12.2. Selected Cohort and Eligibility Statistics
- **Reservoir Filtering:**
  - Total official QASPER Train papers: 888 papers (2,593 questions)
  - RQ3 exposed Train papers excluded: 111 papers (439 questions)
  - Unexposed Train reservoir: 777 papers (2,154 questions)
- **Eligibility Screening ($m \ge 2$ Atomic Joint Grounding):**
  - Candidate Pool ($m \ge 2$ eligible questions): **487 papers** (contains 1,503 eligible questions)
  - Single-question papers ($m = 1$): 226 papers (226 questions) — excluded under `EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS`
  - Zero-question papers ($m = 0$): 64 papers — excluded under `EXCL_ZERO_ELIGIBLE_QUESTIONS`
  - Total accounted papers: $487 + 226 + 64 = \mathbf{777\text{ papers}}$ (exact parity)
- **Deterministic Partition of Candidate Pool (487 Papers):**
  - **Primary Evaluation Cohort:** Exactly **250 papers** (indices 0..249 of shuffle, sorted lexicographically ascending for stable order)
  - **Standby Reserve Queue:** Exactly **50 reserve papers** (indices 250..299 of shuffle, pre-registered in rank order 1..50 with pre-selected questions)
  - **Residual Candidate Pool:** Exactly **187 unselected candidate papers** (indices 300..486 of shuffle)
  - Checksum: $250 + 50 + 187 = \mathbf{487\text{ papers}}$ (exact parity)
- **Selected Evaluation Items:**
  - Exactly **500 questions** ($m = 2$ questions per primary paper, $250 \times 2 = 500$).
  - All 500 questions verified: non-empty usable reference answer, non-float text evidence paragraph, atomic coupling (same annotator).
- **Natural Question Type Distribution (Unconstrained Uniform Sample):**
  - **Extractive:** 319 questions (**63.80%**)
  - **Abstractive:** 109 questions (**21.80%**)
  - **Boolean:** 72 questions (**14.40%**)
  - Total: 500 questions (**100.00%**)

### 12.3. Pre-Registered Standby Queue and Human Review Protocol
1. **Standby Reserve Queue (50 Papers):**
   - Pre-registered in `manifest_metadata.standby_queue` (ranks 1..50, arXiv IDs: `1704.05907`, `1805.02534`, `1910.12469`, ..., `1909.00694`).
   - Trigger condition: strictly technical PDF failures (`EXCL_PDF_HTTP_FETCH_FAILED`, `EXCL_PDF_CORRUPTED_BINARY`, `EXCL_PDF_ZERO_SECTIONS_EXTRACTED`).
   - Replacement policy: strictly in rank order with replacement logged in `manifest_metadata.replacement_log`.
2. **Approved Human Faithfulness Review (Option A):**
   - Pre-registered in `manifest_metadata.approved_human_review_option_a`.
   - Sample: 20 questions deterministically sampled with stride 25 (manifest item indices 1, 26, 51, 76, ..., 476).
   - Models to review: `llama3.2:3b`, `llama3.2:1b`, `qwen2.5:0.5b` ($20 \times 3 = \mathbf{60\text{ model answers}}$).
   - Review protocol: blinded (`Model_Alpha`, `Model_Beta`, `Model_Gamma`), 4-tier claim rubric (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `MISSING_INFO`).

### 12.4. Independent Overlap Audit Against Historical Experiments
Executed [`eval/scripts/check_experiment_overlap.py --manifest eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json`](file:///c:/DACNTT/eval/scripts/check_experiment_overlap.py):
- **Verdict:** `PASS_UNEXPOSED` (Exit code: 0)
- **Papers Audited:** 250 unique papers
  - Unexposed Papers: **250**
  - Exposed Papers (RQ1–RQ4, Pilot, Dev Partition): **0**
  - Unknown Papers: **0**
- **Questions Audited:** 500 unique questions
  - Exposed Questions: **0**
- **Conclusion:** Complete zero-exposure isolation confirmed against all prior experiments.

### 12.5. Provenance Registry Update
Updated [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json) via [`eval/scripts/build_experiment_provenance_registry.py`](file:///c:/DACNTT/eval/scripts/build_experiment_provenance_registry.py):
- Registered experiment ID: `EXP-RQ5-MAIN-SAMPLED`
- Status: `SAMPLED_MANIFEST_FROZEN`
- Recorded primary paper IDs (250), question IDs (500), standby reserve IDs (50), candidate pool IDs (487), and manifest SHA-256.
- Updated paper index: 250 primary papers tagged as `rq5_sampling_status: "SAMPLED_PRIMARY"`, 50 reserve papers tagged as `"STANDBY_RESERVE"`.

### 12.6. Hard Stop Enforced
- **Zero Model Downloads:** No models downloaded or pulled from Ollama.
- **Zero Model Inference:** No LLM prompts executed, no answers generated.
- **Current State:** Frozen manifest and registry fully synchronized, waiting for explicit user confirmation before proceeding to next stage.

---

## 13. Stage C4 Preflight Audit, NFR-03 Alignment, and Pre-Inference Prompt Refinement (2026-10-26)

### 13.1. Non-Functional Requirement Citation and Exact Production Wording
1. **System Specification Citation:**
   The exact wording of **NFR-03** in the system specification ([`DU_AN_CNTT_TOAN_VAN.md`](file:///c:/DACNTT/DU_AN_CNTT_TOAN_VAN.md) Table 4.2 / Section 4.1, and [`docs/CHAPTER4_DRAFT.md`](file:///c:/DACNTT/docs/CHAPTER4_DRAFT.md) Table 4.2 / Section 4.1) is:
   > *"NFR-03: Ngăn ngừa ảo giác và Tiếp đất học thuật — Mô hình AI chỉ được trả lời dựa trên ngữ cảnh trích xuất từ tài liệu. Khi điểm tương đồng ngữ nghĩa rơi vào vùng bất đối xứng không liên quan (< 0,80), hệ thống bắt buộc kích hoạt cơ chế từ chối (Refusal Guardrail), không được suy diễn ngụy tạo."*
2. **Production Service Alignment:**
   In [`backend/apps/documents/services/rag_service.py`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py#L1276-L1335):
   ```python
   REFUSAL_MESSAGE = "The document does not contain sufficient relevant information to answer this question."
   ```
   and lines 1329–1333:
   ```python
   f"Use ONLY the provided context below to answer the user's question clearly and accurately.\n"
   f"If the answer is not contained in the context, state clearly: '{REFUSAL_MESSAGE}'\n"
   f"Do NOT extrapolate, speculate, or fabricate details beyond the provided context.\n\n"
   ```

### 13.2. Pre-Inference Prompt Refinement and Rationale
1. **Discarded Pilot Instruction:**
   The second line of the preliminary prompt (*"If the answer is not contained in the context, synthesize the most relevant details available."*) was discarded prior to live inference. It actively encouraged extrapolation, ungrounded speculation, and hallucination when context was incomplete, contradicting NFR-03, production refusal behavior, and the intended faithfulness evaluation.
2. **Exact Revised Evaluation Prompt Template:**
   ```text
   You are a precise academic research assistant reading "{doc_title}".
   Use ONLY the provided context below to answer the user's question clearly and accurately.
   If the answer is not contained in the context, state clearly: 'The document does not contain sufficient relevant information to answer this question.'
   Do NOT extrapolate, speculate, or fabricate details beyond the provided context.

   Context:
   {context}

   Question: {question}

   Answer:
   ```
3. **Controlled Scope:** Applied identically across `llama3.2:3b`, `llama3.2:1b`, and `qwen2.5:0.5b` under greedy decoding (`temperature=0.0`, `num_predict=256`).

### 13.3. Refusal Behavior and Evidence Sufficiency Boundary
1. **Refusal Tracking in Harness:**
   [`evaluate_rq5_llm_generation.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py) now records `is_refusal` for every item and aggregates `refusal_count` and `refusal_rate_pct` per model.
2. **Evidence Sufficiency Limitation:**
   Passing atomic eligibility (Rule 3) guarantees that a human annotator marked $\ge 1$ non-empty text evidence paragraph for their answer. It does **not** guarantee that the highlighted text is self-sufficient without implicit background knowledge. Under the anti-extrapolation prompt, models may refuse on questions where context is partial.
3. **Empirical Impact Acknowledgment:**
   The prompt revision may increase model refusal rates and reduce Answer Token $F_1$ (since refusals receive $F_1 = 0.0$ against non-empty references). This impact is an empirical outcome to be observed and reported, not assumed to be negligible a priori.
4. **Corrected Faithfulness-Scoring Interpretation:**
   - In automated scoring: Refusals yield Token $F_1 = 0.0$ and Faithfulness Containment = 0.0 (refusal boilerplate is strictly prevented from receiving accidental grounded containment credit).
   - In human claim-level review (Option A: 60 answers): Refusals do **NOT** receive automatic credit. Appropriate abstention when context lacks evidence is scored as `SUPPORTED`. Unjustified refusal when context contains sufficient evidence is scored as `MISSING_INFO` (zero credit).

### 13.4. Preflight Audit Re-Verification Results
- **Syntax / Compilation:** Passed clean across all scripts (`evaluate_rq5_llm_generation.py --audit-only`).
- **File Hashes (SHA-256):**
  - Protocol (`DEC03_FINAL_EVALUATION_PROTOCOL.md`): `9b33c93e81ed4b6674f750a83aca1441a76cad8a5e059c31f51098bb57d3c950`
  - Manifest Payload Checksum: `4a1117b822bce31f0cb240e6c7c65434c23691e4d136b305a34d895135483dc0`
  - Manifest Disk File Checksum (`eval_sample_manifest_500q.json`): `f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5`
  - Evaluation Harness (`evaluate_rq5_llm_generation.py`): `639f3a0a200ab88767fe59ece7366f5e9729aef36a73ec6e54db4b2311dc6add`
- **Manifest Cohort Integrity:** Exactly 250 primary papers, 500 unique questions, 50 standby reserve papers (0 overlap).
- **Scoring Equivalence Regression Test:** 0 mismatches across 2,500 tests against official `qasper_evaluator.py`.
- **Overlap Audit:** `check_experiment_overlap.py` returned `PASS_UNEXPOSED` (250 unexposed papers, 500 questions).
- **Zero Live Inference / Model Pulls:** Enforced strictly. Ready for user authorization.

---

## 14. Stage C4 Final Metric-Definition Audit & Rubric Refinement (2026-10-26)

### 14.1. Automated Factual-Claim Containment Proxy Definition & Alias Removal
1. **Renaming & Compatibility Alias Excision:**
   - Renamed `compute_faithfulness()` to `compute_context_containment_proxy()` in [`evaluate_rq5_llm_generation.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py).
   - In accordance with the preflight audit directives, all legacy backwards-compatible aliases (`compute_faithfulness`, `faithfulness` in records, and `faithfulness_mean` in summaries) have been **completely excised** across all scripts and reports, as no real downstream dependencies required them.
2. **Strict Lexical Containment Naming:**
   - All evaluation scripts, data pipelines, JSON benchmarks, and markdown reports strictly use `automated_containment_proxy` and `automated_containment_proxy_mean` (reported in tables as **Containment Proxy (%)**).
   - Documented in code and reports that this metric is strictly an automated lexical containment heuristic measuring token overlap with context. It does **not** establish semantic faithfulness, logical consistency, or factual truth. Factual faithfulness is conclusively evaluated via the human claim-level audit.
3. **Refusal Handling:**
   - Refusal responses (`REFUSAL_MESSAGE`) strictly evaluate to **0.0% containment**, preventing boilerplate refusal tokens from receiving accidental credit.

### 14.2. Independent Reporting of Operational Metrics
The benchmark suite separately tracks, reports, and interprets:
1. `Answer Token F1`: Lexical overlap against ground-truth references (evaluates to 0.0 on refusal).
2. `is_refusal` and `refusal_rate_pct`: Frequency of explicit NFR-03 refusal responses. Emitting a refusal is not inherently faithful; its validity is judged conditionally based on context sufficiency.
3. `automated_containment_proxy`: Automated token overlap heuristic against prompt context (0.0% on refusal).
4. `Human Claim-Level Audit`: 60-answer blinded qualitative review.

### 14.3. Human Rubric Clarification (`MISSING_INFO` vs `UNSUPPORTED`)
To eliminate ambiguity without changing the frozen 60-answer sample:
1. **Claim-Level Labels:**
   - Any ungrounded, fabricated, or unverifiable factual assertion MUST be classified as **`UNSUPPORTED`**, never as `MISSING_INFO`.
   - Claims entailed by context are **`SUPPORTED`**; claims conflicting with context are **`CONTRADICTED`**.
2. **Answer-Level Holistic Classifications:**
   - **`MISSING_INFO - PARTIAL`**: The model attempted an answer with generated claims, but omitted crucial qualifiers or findings present in the context.
   - **`MISSING_INFO - UNJUSTIFIED_REFUSAL`**: The model emitted the refusal message despite the prompt context actually containing sufficient evidence to answer (abstention defect; 0% credit).
   - **`REFUSAL_VALID`**: The model emitted the refusal message, and human audit confirms the prompt context genuinely lacked sufficient factual evidence to answer (valid safe abstention).

### 14.4. Updated File Checksums (SHA-256)
- Protocol (`DEC03_FINAL_EVALUATION_PROTOCOL.md`): `0c2b12ec375b2b37259004329b9bdd601f4127741a6835775bace4e7d5debded`
- Evaluation Harness (`evaluate_rq5_llm_generation.py`): `46a16f4034aa4abcebd3a3ee44495a84add27895e639c16ec94380f14901e51b`
- Phase 9 README (`README.md`): `9625f594dce6bc429d2659ec2772539c3a447306ecdc3e7052a92f819dd96fe2`
- Manifest Disk File (`eval_sample_manifest_500q.json`): `f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5` (unchanged)
- Manifest Payload Checksum: `4a1117b822bce31f0cb240e6c7c65434c23691e4d136b305a34d895135483dc0` (unchanged)

---

## 15. Final RQ5 Pre-Inference Documentation Audit & Caveat Inventory (2026-10-26)

### 15.1. Methodological & Operational Caveats Codification
1. **Section 11 Added to Protocol:** Codified the Six Methodological and Operational Caveats directly into [`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md):
   - Caveat 1: Generator Isolation vs. End-to-End RAG (gold evidence supplied; retrieval pipeline bypassed; isolates generator).
   - Caveat 2: Automated Containment Proxy (Lexical Overlap) vs. Semantic Faithfulness (canonical naming; unigram non-stopword overlap; 0.0% on refusal; human review provides qualitative assessment).
   - Caveat 3: Answerable-Only Evaluation Cohort (500 questions are answerable with text evidence; unanswerable excluded; cannot estimate refusal on unanswerable questions).
   - Caveat 4: In-House Repository Independence vs. Web Pretraining Scrapes (100% unexposed in-repo; public arXiv pretraining cannot be ruled out).
   - Caveat 5: Human Review Design and Annotator Agreement (Option A: 20 questions x 3 models = 60 blinded answers; single-reviewer qualitative audit; no Cohen's kappa).
   - Caveat 6: Runtime Arithmetic, Checkpointing, and Process Memory (145.83m pure generation + overhead = 2.5-3.0 hours; JSONL incremental flush; RSS summation nuance; Ollama 5m keep-alive).

### 15.2. Portable Manifest Link Construction
- Replaced machine-specific `file:///c:/DACNTT/...` URLs in report generation with portable, repository-relative markdown links (`./eval_sample_manifest_500q.json` and `./DEC03_FINAL_EVALUATION_PROTOCOL.md`).
- Verified target existence and local resolution directly from the report's parent directory (`eval/phases/phase_9_generation/artifacts/`).

### 15.3. File Checksums (Post-Documentation Audit)
- Protocol (`DEC03_FINAL_EVALUATION_PROTOCOL.md`): `2853edaee097a159e96100dfe013223a4ed056ec760d8ae11a2f8a88c2f95bf5`
- Evaluation Harness (`evaluate_rq5_llm_generation.py`): `43c50d85796e14da89774adf4036ea189e1450de5620f183d921b8ea80462c91`
- Phase 9 README (`README.md`): `9625f594dce6bc429d2659ec2772539c3a447306ecdc3e7052a92f819dd96fe2`
- Manifest Disk File (`eval_sample_manifest_500q.json`): `f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5` (100% frozen & unchanged)
- Manifest Payload Checksum: `4a1117b822bce31f0cb240e6c7c65434c23691e4d136b305a34d895135483dc0` (100% frozen & unchanged)

---

## 16. Stage C4 Follow-Up Pre-Inference Documentation Audit (2026-10-26)

### 16.1. Runtime Overhead Arithmetic & Provisional Estimate Status
1. **Arithmetic Decomposition:**
   - Pure inference generation time: $1,750\text{s (0.5B)} + 2,750\text{s (1B)} + 4,250\text{s (3B)} = 8,750\text{s} = 145.83\text{ min} \approx \mathbf{146\text{ min}}$ (~2h 25m 50s).
   - Quantified deterministic overhead: ~26s initial model loading + ~15s REST localhost round-trips + ~15s JSONL checkpoint serialization/disk flush + ~15s scoring evaluation + ~20s paired bootstrap statistical analysis = **~91 seconds (~1.5 minutes)**. Deterministic baseline: **~147.3 minutes** (~2h 27m 20s).
   - Unquantified operational contingency: The remaining gap of **+2.7 to +32.7 minutes** required to reach the 2.5–3.0 hour window (150 to 180 min) accounts for background memory monitoring thread polling (100ms interval), host CPU thermal throttling and OS thread scheduling under continuous 100% thread load on the AMD Ryzen 5 5600, potential transient HTTP retry backoffs (`call_ollama_with_retry` exponential delay), and garbage collection pauses.
2. **Provisional Status:**
   - The 2.5–3.0 hour wall-clock figure is formally designated as a **provisional planning estimate**. It is not claimed to be explicitly justified or arithmetically derived from the ~1.5 minutes of itemized deterministic overhead alone.

### 16.2. Repository Independence vs. Selection & Pretraining Bias
1. **Precise Claim Formulation:**
   - The audit verdict `PASS_UNEXPOSED` supports **independence from recorded prior experimental exposure within the audited repository records** (covering RQ1–RQ4, QASPER Dev/Test partitions, and the preliminary RQ5 pilot).
   - It does **not** prove freedom from all methodological or selection bias (e.g. eligibility filtering requiring $\ge 2$ text-evidenced answerable questions inherently selects for information-dense papers).
   - It does **not** establish that public arXiv preprints were absent from public internet pretraining scrapes of Llama-3.2 (Meta) or Qwen-2.5 (Alibaba). The cohort must never be described as proven free of all bias or public-pretraining contamination.

### 16.3. Overlap Audit Scope Reconciliation
1. **Cohorts and Records Audited:**
   - Evaluated command: `python eval/scripts/check_experiment_overlap.py --manifest eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json`
   - Verified that the 250 primary papers and 500 questions in `eval_sample_manifest_500q.json` have zero overlap across all historical cohorts registered in `eval/experiment_provenance_registry.json`:
     - `EXP-RQ1-EXTRACTION`: 47 QASPER Dev papers
     - `EXP-RQ2-CHUNKING`: 47 QASPER Dev papers
     - `EXP-RQ3-EMBEDDING-UNIFIED`: 211 papers (111 Train + 100 Dev)
     - `EXP-RQ4-HYBRID-DEV`: 276 QASPER Dev papers
     - `EXP-RQ4-HYBRID-TEST`: 408 QASPER Test papers
     - `EXP-RQ5-PILOT-SEED`: 4 non-QASPER seed papers (ResNet, Attention, LoRA, RAG)
     - Full QASPER Partitions: 281 Dev papers and 416 Test papers in `paper_index` (with 408 papers in the active text-retrieval evaluation cohort `EXP-RQ4-HYBRID-TEST`).
2. **Resolution of Phrasing Ambiguity:**
   - Clarified that earlier mentions of "RQ1–RQ5" meant "historical experiments up through the preliminary RQ5 pilot", whereas "RQ1–RQ4 plus Dev" omitted the 4 non-QASPER seed papers. The authoritative scope is now codified explicitly as: *all completed historical experiments (RQ1, RQ2, RQ3, RQ4 Dev, RQ4 Test, and RQ5 Pilot), plus full Dev and Test split partitions.*

### 16.4. Checkpoint Recovery Implementation & Failure Modes
1. **Implementation Analysis (`CheckpointManager`):**
   - **Duplicate Records:** Keyed on `(model, item_index)`. Duplicate lines overwrite earlier memory entries (`loaded_records[key] = rec`), preserving set membership in `completed_keys`. Resumed runs safely skip completed items without re-running inference.
   - **Malformed / Partial Lines / Interrupted Writes:** Handled via `try ... json.loads(line) ... except Exception as e`. Any truncated line from a process crash or interrupted write is logged with a warning and skipped. The key is **not** added to `completed_keys`, guaranteeing that the incomplete item will be re-evaluated upon restart.
   - **Persistence & Durability Limitation (Buffer Flush vs. Power Loss):** `f.flush()` forces data out of Python's user-space buffers into the host operating system kernel file cache (`fflush()`); it does **not** call `os.fsync()` or Windows `FlushFileBuffers()` to guarantee immediate physical persistence to disk media. While this safeguards against Python process-level crashes and unhandled exceptions, it does **not** guarantee survival against host power loss, hardware reset, or OS kernel crashes.
   - **Changed Manifest Mappings (Non-Universal Limitation):** Resumption keys strictly on `(model, item_index)` and does not validate `question_id` against the checkpoint record. If the manifest order or composition is altered, `item_index` maps to wrong items (semantic misattribution). Therefore, safe recovery is **strictly conditional** upon using the permanently frozen manifest (`eval_sample_manifest_500q.json`).
2. **Safe Verification:**
   - Verified behavior via unit test `eval/scratch/test_checkpoint_behavior.py` (all tests passed with zero live model inference).

### 16.5. Process Memory Measurement Nuances & Resumed Runs
1. **Summed Process RSS vs. Physical RAM:**
   - `DualProcessMemoryMonitor` sums Python worker RSS and Ollama runner RSS. On Windows, process RSS includes shared working set pages (e.g. `ucrtbase.dll`, `vcruntime140.dll`, OS system libraries). Summing process RSS double-counts shared pages, yielding a figure **higher than actual physical RAM consumption**. It must never be labeled as true physical RAM usage, a guaranteed upper bound, or deduplicated process memory.
2. **Resumed Execution Boundary:**
   - In a resumed run, completed items bypass Ollama inference calls and are loaded from cache. The Ollama runner process remains idle for cached items. Therefore, peak memory recorded during a resumed run reflects only idle/cached execution and does **not** represent live inference-time peak memory. Peak inference memory is only valid from full, contiguous inference executions.

### 16.6. Relative-Link Validation & Report Path Verification
- **Actual Generated Report Path:** `eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT_500Q.md`
- **Report Parent Directory:** `eval/phases/phase_9_generation/artifacts/`
- **Link Resolution Checks:**
  - `./eval_sample_manifest_500q.json` resolves to `eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json` (Exists: `True`).
  - `./DEC03_FINAL_EVALUATION_PROTOCOL.md` resolves to `eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md` (Exists: `True`).
- Confirmed that both link targets resolve to existing files directly from the parent directory of the generated report.

### 16.7. File Version Integrity & Checksums
- **Harness Version Clarification & Comparison:**
  - The SHA-256 hash `43c50d85796e14da89774adf4036ea189e1450de5620f183d921b8ea80462c91` identifies the active version of `evaluate_rq5_llm_generation.py` prior to live execution.
  - Prior recorded hash (Section 15.3): `43c50d85796e14da89774adf4036ea189e1450de5620f183d921b8ea80462c91`.
  - Pre-relative-link hash (Section 14.4): `46a16f4034aa4abcebd3a3ee44495a84add27895e639c16ec94380f14901e51b`.
  - **Verdict:** Comparing the current on-disk hash with Section 15.3 confirms the harness code remained **100% unchanged** (`Current == Section 15.3`). Only documentation files were modified during this follow-up audit.
- Protocol (`DEC03_FINAL_EVALUATION_PROTOCOL.md`): `b59cee507cf70139883d4eca9e2e03afce64cec824d7ee876ec3e31ff78cd557`
- Manifest Disk File (`eval_sample_manifest_500q.json`): `f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5` (100% frozen & unchanged)
- Manifest Payload Checksum: `4a1117b822bce31f0cb240e6c7c65434c23691e4d136b305a34d895135483dc0` (100% frozen & unchanged)
- Overlap Audit Verdict: `PASS_UNEXPOSED` (250 unexposed papers, 500 questions, 0 conflicts)

---

## 17. Stage C5 Full Confirmatory Evaluation Execution & Results (2026-10-26)

### 17.1. Execution Overview & Checkpoint Durability
Following explicit user authorization, the full 500-question confirmatory evaluation harness was executed on the host AMD Ryzen 5 5600 CPU with 16 GB RAM and Ollama v0.40.8:
- **Evaluated Scope:** Exactly 1,500 model generations across the frozen 250-paper / 500-question cohort (`llama3.2:3b`, `llama3.2:1b`, and `qwen2.5:0.5b`).
- **Checkpoint Persistence:** All 1,500 item records were incrementally saved to [`eval/phases/phase_9_generation/artifacts/rq5_inference_checkpoint.jsonl`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_inference_checkpoint.jsonl) with immediate `f.flush()` buffer flushes.
- **Serialization Robustness:** Fixed serialization for NumPy boolean/scalar types via `numpy_json_serializer` fallback in `json.dump()`.
- **Registry Status:** Updated `EXP-RQ5-MAIN-SAMPLED` status to `COMPLETED` in [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json).

### 17.2. Consolidated Empirical Results

| Model | Parameters | Answer F1 (Overall) | Extractive F1 | Abstractive F1 | Boolean F1 | Refusal Count (Rate %) | Containment Proxy (%) | Latency P50 | Latency P95 | Throughput (tok/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` | 3.21B | **0.2033** | 0.2605 | 0.1438 | 0.0385 | 243 (48.6%) | **37.9%** | 6.55s | 15.16s | **12.7** |
| `llama3.2:1b` | 1.23B | **0.1346** | 0.1730 | 0.1108 | 0.0006 | 294 (58.8%) | **29.3%** | 5.08s | 9.83s | **20.4** |
| `qwen2.5:0.5b` | 0.49B | **0.2324** | 0.2912 | 0.1921 | 0.0349 | 50 (10.0%) | **60.3%** | 3.85s | 7.50s | **57.3** |

### 17.3. Pre-Registered Inferential Statistical Analysis (Paper Clusters K=250, df=249)

| Comparison | Observed $\Delta$ | 95% Clustered Bootstrap CI | Paper-Level $t$ ($df=249$) | Raw $p$-value | Holm-Bonferroni $p_{\text{adj}}$ | Practical Effect ($\Delta \ge 0.030$) | Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` vs `llama3.2:1b` | **+0.0687** | [+0.0480, +0.0902] | $t=6.2597$ | $1.68 \times 10^{-9}$ | **$3.35 \times 10^{-9} \ll 0.001^*$** | MET | **REJECT_NULL (Significant)** |
| `llama3.2:3b` vs `qwen2.5:0.5b` | **-0.0291** | [-0.0509, -0.0053] | $t=-2.5028$ | $1.30 \times 10^{-2}$ | **$1.30 \times 10^{-2} = 0.0130^*$** | NOT MET | **REJECT_NULL (Significant)** |
| `llama3.2:1b` vs `qwen2.5:0.5b` | **-0.0978** | [-0.1189, -0.0763] | $t=-8.9651$ | $7.57 \times 10^{-17}$ | **$2.27 \times 10^{-16} \ll 0.001^*$** | MET | **REJECT_NULL (Significant)** |

### 17.4. Outlier Sensitivity Diagnostics

| Comparison | Wilcoxon $p$ (drop zeros) | Wilcoxon $p$ (Pratt ranks) | Zero Diffs ($K_0$) | 10% Trimmed $\Delta_{\text{trim}}$ ($K=200$) | Max Jackknife Influence |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` vs `llama3.2:1b` | $3.49 \times 10^{-9}$ | $1.59 \times 10^{-9}$ | 48/250 | +0.0575 | 0.003071 |
| `llama3.2:3b` vs `qwen2.5:0.5b` | $2.84 \times 10^{-3}$ | $2.75 \times 10^{-3}$ | 5/250 | -0.0311 | 0.002753 |
| `llama3.2:1b` vs `qwen2.5:0.5b` | $6.61 \times 10^{-16}$ | $6.41 \times 10^{-16}$ | 12/250 | -0.0898 | 0.002324 |

### 17.5. Key Scientific Insights on Refusal Dynamics
1. **Llama 3.2 Scaling Effect:** `llama3.2:3b` significantly and decisively dominates `llama3.2:1b` across every metric ($\Delta = \mathbf{+0.0687}$, $p_{\text{adj}} = \mathbf{3.35 \times 10^{-9} \ll 0.001^*}$), achieving higher Answer F1 (0.2033 vs 0.1346) and lower refusal rate (48.6% vs 58.8%).
2. **Refusal Mechanism on Answerable-Only Questions:** Because all 500 questions in this cohort are answerable under gold ground-truth criteria, emitting the NFR-03 refusal message is strictly penalized to **Answer Token F1 = 0.0000** and **Containment Proxy = 0.0%**.
3. **Qwen vs. Llama Behavioral Trade-off:** `qwen2.5:0.5b` achieved a higher raw lexical Token F1 (0.2324) because it maintained an aggressive 90.0% response rate (only 10.0% refusals), whereas Llama models conservatively refused ~49–59% of the time. The planned blinded 60-answer human audit (Option A) is critical to separate valid grounded extractions from ungrounded hallucinations.
4. **Accurate Survival-Function p-Values:** Resolved floating-point cancellation underflow (`1.0 - t.cdf == 0.0`) in `evaluate_rq5_llm_generation.py` using `scipy.stats.t.sf(abs(t_stat), df=df) * 2.0`. The exact paper-cluster paired p-value for `llama3.2:1b` vs `qwen2.5:0.5b` ($t=-8.9651, df=249$) is reported as $p = 7.57 \times 10^{-17}$ (raw) and $p_{\text{adj}} = 2.27 \times 10^{-16}$ (Holm-Bonferroni adjusted).
5. **Paraphrased Refusals Limitation:** A post-hoc audit across the 1,500 outputs identified 13 instances (0.87%: 4 in Llama-3.2 1B, 9 in Qwen-2.5 0.5B) with paraphrased refusal phrasing (e.g., *"The provided context does not contain information about..."*). In strict accordance with pre-registration and methodological integrity, primary scores and refusal counts are preserved as generated without post-hoc rewriting, and this nuance is documented as a known string-matching limitation.

### 17.6. Output Artifacts & Checksums (Post-Execution)
- Benchmark JSON ([`rq5_llm_generation_benchmark_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json)): `9f7589e8c71092c3fd9ce3af1d68fb9d9939119aea6e5b309cb82e72f57d1004`
- Generated Report ([`RQ5_LLM_GENERATION_REPORT_500Q.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT_500Q.md)): `99fab76c22e22aab47194981b036dc273fa7c055ac2068b08f55ae88d1f4d7d4`
- Inference Checkpoint ([`rq5_inference_checkpoint.jsonl`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_inference_checkpoint.jsonl)): `b53166efe4e8f27e34fd9f3c6efc6816214f8f2ff374682ada0f67cb030eb4b4` (100% frozen & unchanged)
- Updated Harness ([`evaluate_rq5_llm_generation.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py)): `570fd7752c16764cb1c77fb341fd8240a550a2f44321d8dbea4f2cfe845a54db`
- Manifest Disk Checksum (`eval_sample_manifest_500q.json`): `f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5` (100% frozen & unchanged)
- Manifest Payload Checksum: `4a1117b822bce31f0cb240e6c7c65434c23691e4d136b305a34d895135483dc0` (100% frozen & unchanged)

---

## 18. Stage C6 Final Methodological Verification & Measurement Standards (2026-10-26)

### 18.1. Bootstrap Implementation Audit
1. **Resampling Algorithm Verification:**
   - Unit of resampling: exactly $K=250$ paper clusters (`unique_papers`).
   - For each paper $i$, the mean paired difference $D_i = \bar{Y}_{i, A} - \bar{Y}_{i, B}$ is computed across its $m=2$ questions.
   - For each replicate $b \in \{1..2000\}$, $K=250$ paper differences are sampled with replacement using `random.Random(42)`.
   - The bootstrap distribution is formed by the 2,000 replicate sample means $\bar{D}^*_b = \frac{1}{250} \sum_{j=1}^{250} D^*_{b, j}$.
   - Percentile confidence intervals are extracted at the 2.5th percentile (index 50) and 97.5th percentile (index 1950) from the sorted array.
2. **Implementation vs. Stored Parity:**
   - Both `RQ5_LLM_GENERATION_REPORT_500Q.md` and `rq5_llm_generation_benchmark_500q.json` were regenerated directly from the permanently frozen checkpoint (`rq5_inference_checkpoint.jsonl`, SHA-256: `b53166efe4e8f27e34fd9f3c6efc6816214f8f2ff374682ada0f67cb030eb4b4`) with zero live model inference.
   - Stored confidence intervals match the verified implementation to the 4th decimal place.

### 18.2. Precise Inferential Interpretation Standards
| Comparison | Reported Difference in F1 ($\Delta$) | Formal Interpretation |
| :--- | :---: | :--- |
| **`llama3.2:3b` − `llama3.2:1b`** | **+0.0687** | Statistically significant ($p_{\text{adj}} = 3.35 \times 10^{-9}$); exceeds exploratory practical threshold ($\Delta \ge 0.030$). |
| **`llama3.2:3b` − `qwen2.5:0.5b`** | **−0.0291** | Statistically significant ($p_{\text{adj}} = 0.0130$); falls just below exploratory practical threshold ($|\Delta| < 0.030$). |
| **`llama3.2:1b` − `qwen2.5:0.5b`** | **−0.0978** | Statistically significant ($p_{\text{adj}} = 2.27 \times 10^{-16}$); exceeds exploratory practical threshold ($|\Delta| \ge 0.030$). |

1. **Threshold Boundary:** The $\Delta = 0.030$ threshold is an exploratory practical-effect reference, **NOT a formal statistical equivalence boundary**. The fact that `llama3.2:3b` vs `qwen2.5:0.5b` falls slightly below 0.030 does **NOT** prove practical equivalence or absence of a meaningful difference.
2. **Metric Epistemology:** Because the primary metric is Answer Token F1, these results establish differences in **lexical agreement with human reference answers**, NOT necessarily differences in factual correctness, logical coherence, or semantic faithfulness.

### 18.3. Refusal Detection as an Unresolved Detector-Based Limitation
1. **Preservation of Primary Preregistered Counts:** In strict adherence to experimental integrity, the primary reported refusal counts (243 for 3B, 294 for 1B, 50 for 0.5B) and checkpoint records are preserved exactly as generated.
2. **Detector-Based Qualification:** Reported refusal rates (48.6%, 58.8%, 10.0%) are detector-based counts tied strictly to the NFR-03 template substring match (`REFUSAL_MESSAGE` or `"does not contain sufficient"`). They are not guaranteed counts of every actual refusal.
3. **Audit Evidence:** A post-hoc scan identified 13 instances (0.87% of all records: 4 in Llama 1B, 9 in Qwen 0.5B) containing paraphrased refusal phrasing (e.g., *"The provided context does not contain information about..."*).
4. **Protocol for Thesis & Future Analyses:** The thesis documents this as a known detector limitation. Any future sensitivity analysis with broader semantic refusal classification must be reported separately alongside its explicit classification rules, without overwriting the primary preregistered results.

---

## 19. Stage C7 — Blinded Human Faithfulness Review Package Implementation & Verification (2026-10-26)

### 19.1. Objective and Methodological Role
To complement automated Answer Token F1 and qualitative containment metrics without replacing them, Stage C7 implements the planned blinded human faithfulness audit instrument under **Option A** (20 questions $\times$ 3 models = 60 answers). The review evaluates whether factual claims generated by the candidate LLMs (`llama3.2:3b`, `llama3.2:1b`, `qwen2.5:0.5b`) are semantically supported by the exact evidence contexts provided during generation.

### 19.2. Sampling Procedure (Option A Stride-25)
1. **Source Manifest:** The sample was drawn strictly from the frozen 500-question manifest ([`eval_sample_manifest_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json), SHA-256: `f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5`).
2. **Sampling Rule:** Selected every 25th item starting from the first item without reshuffling or quality-based filtering:
   - Zero-based manifest indices ($i \in [0, 499]$): `0, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475`.
   - One-based human item numbers (`item_index`): `1, 26, 51, 76, 101, 126, 151, 176, 201, 226, 251, 276, 301, 326, 351, 376, 401, 426, 451, 476`.
   - Stable Review IDs assigned: `REV-01` through `REV-20`.
3. **Question Coverage:** Exactly 20 distinct questions from 20 distinct papers across diverse STEM fields (NLP, Vision, Biomedicine, Systems).
4. **Context Parity:** The evidence context for each review item is bit-for-bit identical to the context passed to the models during inference (`"\n\n".join(item["ground_truth_evidence"])`).

### 19.3. Blinding and Latin-Square Counterbalancing Procedure
1. **Permutation Structure:** For the 3 candidate models, there exist $3! = 6$ unique permutations. To guarantee balanced presentation without position skew across the 20 review questions, a Latin-square counterbalancing procedure was applied:
   - 3 complete blocks of all 6 permutations ($3 \times 6 = 18$ items), ensuring each model appears in each position (Alpha, Beta, Gamma) exactly 6 times.
   - Plus the complementary permutation pair $(M_0, M_2, M_1)$ and $(M_1, M_0, M_2)$ for the remaining 2 items.
   - The 20 permutation assignments were deterministically shuffled across the review questions (`REV-01` .. `REV-20`) using `seed=42`.
2. **Neutral Labels:** Permuted models were assigned labels `Model_Alpha`, `Model_Beta`, and `Model_Gamma`.
3. **Exact Counterbalanced Position Distribution Across 60 Answers:**
   - `llama3.2:3b`: Alpha = 7, Beta = 7, Gamma = 6 (Total = 20)
   - `llama3.2:1b`: Alpha = 7, Beta = 6, Gamma = 7 (Total = 20)
   - `qwen2.5:0.5b`: Alpha = 6, Beta = 7, Gamma = 7 (Total = 20)
   - Column sums: exactly 20 Alpha, 20 Beta, 20 Gamma.
   - Every individual cell is either 6 or 7 (maximum deviation of $\pm 1$ from the theoretical mean of $20/3 \approx 6.67$, completely eliminating position skew).
4. **Strict Isolation of Model Identities:** All reviewer-facing documents (`HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md`, `faithfulness_annotation_template_60a.csv`, `faithfulness_annotation_template_60a.jsonl`) contain zero model names, parameter counts, latencies, throughputs, automated Token F1 scores, or checkpoint internals.
5. **Restricted Mapping:** The exact association between review items, blind labels, and actual model identities is saved strictly in an isolated internal file ([`restricted_model_label_mapping.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/restricted_model_label_mapping.json)).

### 19.4. Canonical Rubric, Protocol Precedence & Non-Erasure Directive
1. **Canonical Protocol Authority:** The four-category rubric and the conflict precedence hierarchy are directly codified in Section 6.4 and Section 6.5 of the canonical evaluation protocol ([`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)):
   - **Primary Labels:**
     1. `CONTRADICTED`: At least one substantive factual claim is directly refuted by the context.
     2. `UNSUPPORTED`: At least one substantive factual claim lacks evidentiary backing in the context (extrapolations, hallucinations, ungrounded assumptions).
     3. `MISSING_INFO - UNJUSTIFIED_REFUSAL`: The model emitted a refusal message despite the context containing sufficient facts to answer.
     4. `MISSING_INFO - PARTIAL`: The answer makes supported claims but omits crucial contextual qualifiers, findings, or metrics.
     5. `REFUSAL_VALID`: The model correctly refused because the context genuinely lacks the required facts.
     6. `SUPPORTED`: All factual claims made are fully grounded in and justified by the supplied context.
   - **Worst-Case Failure Precedence:**
     $$\mathbf{CONTRADICTED} \succ \mathbf{UNSUPPORTED} \succ \mathbf{MISSING\_INFO - UNJUSTIFIED\_REFUSAL} \succ \mathbf{MISSING\_INFO - PARTIAL} \succ \mathbf{REFUSAL\_VALID} \succ \mathbf{SUPPORTED}$$
2. **Mandatory Non-Erasure Directive (Preserving Diagnostic Nuance):**
   - Assigning a primary holistic label based on the precedence hierarchy must **NOT** erase other observed defects or grounded elements.
   - Reviewers explicitly record individual atomic claim propositions and labels in the **Claim-by-Claim Breakdown**, quote verbatim evidence in **Supporting Context Quote**, and record co-occurring defects in **Secondary Label** (e.g., `MISSING_INFO - PARTIAL`) and **Reviewer Notes & Justification**.

### 19.5. Automated Verification Results (13/13 Checks Passed)
Executed independent validation script ([`validate_human_review_package.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/validate_human_review_package.py)):
1. `[PASS]` Checkpoint & Manifest SHA-256 match frozen reference hashes exactly.
2. `[PASS]` Exactly 20 distinct review questions.
3. `[PASS]` Exactly 3 candidate answers per question.
4. `[PASS]` Exactly 60 records across mapping, CSV, and JSONL templates.
5. `[PASS]` Stride-25 indices match manifest items 1..476 bit-for-bit.
6. & 7. `[PASS]` All 60 model answers and evidence contexts match frozen checkpoint records bit-for-bit.
8. `[PASS]` All question IDs and texts are stable and consistent.
9. `[PASS]` Reviewer-facing materials contain ZERO model names, sizes, or performance metrics.
10. `[PASS]` Restricted mapping contains all 60 (review_item_id, blind_label) tuples.
11. `[PASS]` All human annotation fields in CSV and JSONL templates are strictly blank.
12. `[PASS]` Exact balanced model frequencies (20 per model) and counterbalanced position distribution (all cells in [6, 7]) verified.
13. `[PASS]` Stable review IDs `REV-01` through `REV-20` verified.

### 19.6. Package Deliverables & Checksums
All artifacts reside under [`eval/phases/phase_9_generation/artifacts/human_faithfulness_review/`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/):
- **Reviewer Guide & Form (MD):** [`HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md) (SHA-256: `19dace386b93c9acc751a682e1a06ba629cb97352da9b7c72be8361277ee3cc8`)
- **Annotation Template (CSV):** [`faithfulness_annotation_template_60a.csv`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/faithfulness_annotation_template_60a.csv) (SHA-256: `92a66cfb420ccf599a94f0a8ccb49adc25bed0649235c80ccee39688983dad69`)
- **Annotation Template (JSONL):** [`faithfulness_annotation_template_60a.jsonl`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/faithfulness_annotation_template_60a.jsonl) (SHA-256: `20f675df1c5dd0e9d6104275666aeadd6fbf42b7591568070a31732b523bb369`)
- **Restricted Mapping (JSON):** [`restricted_model_label_mapping.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/restricted_model_label_mapping.json) (SHA-256: `86209129ee85c81ecf1b5af32e1685cb4f19b397e88278b54120f210d2137f49`)
- **Sampling & Integrity Manifest (JSON):** [`sampling_and_integrity_manifest.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/sampling_and_integrity_manifest.json) (SHA-256: `1ee49c453f2b55464c867d7ffb85c2b2f600e94b0f5bdafb375a10ee0e7cb5d3`)
- **Generation Script:** [`generate_human_review_package.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/generate_human_review_package.py) (SHA-256: `faff7dccba4b109b6137fb3b1ecc06106ccfee5f4bd3384dfcb1cd30a98fd812`)
- **Validation Script:** [`validate_human_review_package.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/validate_human_review_package.py) (SHA-256: `f65a36809c555c4e532dbd3438615e29eb039c1b542f1a5c502c2267101f5f6c`)

### 19.7. Strict Operational Confirmations
1. **Zero Model Inference:** No LLM inference calls or Ollama interactions were performed.
2. **Frozen Benchmark Integrity:** Source manifest (`eval_sample_manifest_500q.json`) and inference checkpoint (`rq5_inference_checkpoint.jsonl`) remain 100% frozen with identical SHA-256 checksums.
3. **No Fabricated Labels:** Annotation fields remain strictly blank. The package is **prepared and validated for human annotation, not completed**.
