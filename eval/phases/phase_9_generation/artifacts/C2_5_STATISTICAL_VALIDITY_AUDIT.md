# Stage C2.5: Independent Statistical Validity Audit of RQ5 Bootstrap Inference

*Document Status:* **Complete Independent Statistical Validity Audit**
*Canonical Location:* [`eval/phases/phase_9_generation/artifacts/C2_5_STATISTICAL_VALIDITY_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/C2_5_STATISTICAL_VALIDITY_AUDIT.md)
*Date:* 2026-10-25
*Workspace Root:* `c:\DACNTT`
*Primary Implementation Inspected:* [`backend/scripts/eval_common/stats.py`](file:///c:/DACNTT/backend/scripts/eval_common/stats.py)
*Canonical Audit Change Log:* [`eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md)

---

## 1. Executive Verdict

### **EXECUTIVE VERDICT: `NOT VALID / NOT ESTABLISHED` as a Formal Hypothesis Test**
*(Classified as `VALID WITH LIMITATIONS` strictly as a descriptive Parameter Estimation & Confidence Interval procedure, but `NOT VALID` as a formal null-hypothesis significance test with calibrated Type I error control).*

### Key Findings Summary:
1. **Uncentered Bootstrap Tail Area vs. Null Hypothesis Testing:**
   The formula `p = min(1.0, 2(r+1)/(B+1))` implemented in [`backend/scripts/eval_common/stats.py: line 186`](file:///c:/DACNTT/backend/scripts/eval_common/stats.py#L186) counts uncentered bootstrap replicates $\Delta_b^*$ on the opposite side of zero from the observed effect $\Delta_{\text{obs}}$. The bootstrap replicates are centered at $\mathbb{E}_*[\Delta_b^*] = \Delta_{\text{obs}}$, **not under the null hypothesis $\theta_0 = 0$**. It directly violates Guideline 1 of Hall & Wilson (1991): *"Resampling should be done in a way that reflects the null hypothesis, even when the null hypothesis is false."*
2. **True Nature of the Current Formula:**
   The current procedure is an **empirical inversion of the percentile bootstrap confidence interval** (sometimes termed an "achieved significance level" or pseudo-$p$-value). It identifies the nominal significance level $\tilde{\alpha}$ at which the $(1 - \tilde{\alpha})$ percentile confidence interval just touches zero. It does **not** approximate a null sampling distribution.
3. **Finite-Sample Correction (+1) Limitation:**
   The $+1$ finite-sample adjustment (Davison & Hinkley 1997) guarantees valid discrete uniform test size **only when the bootstrap replicates are exchangeable draws from a true null distribution** (as in exact permutation tests). In an uncentered bootstrap distribution, $+1$ merely prevents dividing by zero or claiming $p = 0.0000$; it does not correct the fundamental lack of null centering, skewness errors, or cluster-level coverage defects.
4. **Invalid Multiple-Testing Guarantees:**
   Because the raw pseudo-$p$-values lack proven sub-uniformity under $H_0$ ($\mathbb{P}_{H_0}(P \le \alpha) \le \alpha$), applying the Holm–Bonferroni step-down adjustment **cannot mathematically guarantee family-wise error rate (FWER) control at $\alpha = 0.05$**.
5. **Recommended Path Forward:**
   Decouple parameter estimation from hypothesis testing:
   - **Primary Estimation & Uncertainty:** Retain the **95% Paper-Clustered Paired Bootstrap Percentile Confidence Interval** ($B=2,000$, `seed=42`) for reporting the mean difference $\Delta_{\text{obs}}$ and its estimation uncertainty.
   - **Primary Hypothesis Testing:** If formal hypothesis testing and $p$-values are required for thesis claims, replace the uncentered pseudo-$p$-value with a **Paper-Cluster Paired Randomization / Sign-Flip Test ($M=10,000$, `seed=42`)** on paper cluster means $\bar{D}_p$, which is an exact finite-sample conditional test under label exchangeability.

---

## 2. Complete Implementation Trace

We inspected the actual implementation in [`backend/scripts/eval_common/stats.py`](file:///c:/DACNTT/backend/scripts/eval_common/stats.py) (235 lines), the RQ5 preliminary script [`eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py), and the governing protocol.

```
+───────────────────────────────────────────────────────────────────────────+
│ STEP 1: Observed Model Difference Calculation                             │
│ File: backend/scripts/eval_common/stats.py, Lines 158-163                │
│                                                                           │
│   all_diffs_actual = []                                                   │
│   for p in paper_keys:                                                    │
│       all_diffs_actual.extend(np.array(cand[p]) - np.array(base[p]))      │
│   mean_diff = float(np.mean(all_diffs_actual)) if all_diffs_actual else 0 │
│                                                                           │
│   Formula: Δ_obs = (1/N) * Σ_{i=1}^N (S_{cand, i} - S_{base, i})          │
│   Across N=100 questions (K=50 papers, m=2 questions per paper).          │
+─────────────────────────────────────┬─────────────────────────────────────+
                                      │
                                      ▼
+───────────────────────────────────────────────────────────────────────────+
│ STEP 2: Paper-Clustered Paired Bootstrap Resampling                       │
│ File: backend/scripts/eval_common/stats.py, Lines 165-177                │
│                                                                           │
│   rng = np.random.default_rng(seed)                                       │
│   boot_diffs = []                                                         │
│   for _ in range(n_bootstraps):                                           │
│       sampled_papers = rng.choice(paper_keys, size=K, replace=True)       │
│       resampled_diffs = []                                                │
│       for p in sampled_papers:                                            │
│           diffs_p = np.array(cand[p]) - np.array(base[p])                 │
│           resampled_diffs.extend(diffs_p)                                 │
│       boot_diffs.append(float(np.mean(resampled_diffs)))                  │
│                                                                           │
│   Replicates: B=2,000, seed=42, K=50 papers sampled with replacement.     │
│   Properties: Uncentered mean E_*[Δ_b*] = Δ_obs.                         │
+─────────────────────────────────────┬─────────────────────────────────────+
                                      │
                                      ▼
+───────────────────────────────────────────────────────────────────────────+
│ STEP 3: 95% Percentile Bootstrap Confidence Interval                      │
│ File: backend/scripts/eval_common/stats.py, Lines 178-179                │
│                                                                           │
│   ci_lower = float(np.percentile(boot_diffs, 2.5))                        │
│   ci_upper = float(np.percentile(boot_diffs, 97.5))                       │
│                                                                           │
│   Formula: [Δ*_{2.5%}, Δ*_{97.5%}] from the empirical sorted boot_diffs.  │
+─────────────────────────────────────┬─────────────────────────────────────+
                                      │
                                      ▼
+───────────────────────────────────────────────────────────────────────────+
│ STEP 4: Raw Two-Sided Pseudo-p-Value Calculation                          │
│ File: backend/scripts/eval_common/stats.py, Lines 181-186                │
│                                                                           │
│   if mean_diff >= 0:                                                      │
│       r = sum(1 for d in boot_diffs if d <= 0)                            │
│   else:                                                                   │
│       r = sum(1 for d in boot_diffs if d >= 0)                            │
│   p_val = min(1.0, 2.0 * (r + 1) / (n_bootstraps + 1))                    │
│                                                                           │
│   Nature: Tail inversion of percentile CI around Δ_obs, NOT a null test.  │
+─────────────────────────────────────┬─────────────────────────────────────+
                                      │
                                      ▼
+───────────────────────────────────────────────────────────────────────────+
│ STEP 5: Multiple Testing Correction (Holm-Bonferroni)                     │
│ File: backend/scripts/eval_common/stats.py, Lines 191-234                │
│                                                                           │
│   Sort raw p-values: p_(1) <= p_(2) <= p_(3).                             │
│   adj_p_(k) = min(1.0, max(accum, p_(k) * (m - k + 1))).                  │
│   Significant iff adj_p < alpha (alpha = 0.05).                           │
+───────────────────────────────────────────────────────────────────────────+
```

### Discrepancies Between Documentation and Executable Implementation:
1. **Pilot Evaluation Script Reality:**
   In [`eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py: lines 238–258`](file:///c:/DACNTT/eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py#L238-L258), the preliminary pilot script evaluated a 16-query seed and computed simple arithmetic means (`sum(f1_scores) / len(f1_scores)`). It did not invoke `stats.py` or execute bootstrap resampling. The integration of `paired_cluster_bootstrap` into RQ5 is part of the planned Stage C3 benchmark harness.
2. **Estimand Equivalence Under Balanced Design:**
   In [`backend/scripts/eval_common/stats.py: lines 146–163`](file:///c:/DACNTT/backend/scripts/eval_common/stats.py#L146-L163), the code provides two estimand branches: `estimand == "paper"` and `estimand == "query"`. Because the pre-registered RQ5 sample design fixes exactly $m=2$ questions for every paper cluster, both branches yield mathematically identical point estimates $\Delta_{\text{obs}}$ and replicate values $\Delta_b^*$.

---

## 3. Definition of Intended Estimand and Null Hypothesis

### 3.1. Target Estimand
Let $p \in \{1, \dots, K\}$ index the independent scientific papers sampled from the target population distribution $\mathcal{P}$ (the QASPER academic domain).
Within each paper $p$, exactly two eligible questions are evaluated: $q \in \{1, 2\}$.
Let $Y_{1, p, q}$ and $Y_{0, p, q} \in [0, 1]$ be the Answer Token F1 scores of the candidate model and baseline model, respectively.
Define the paired score difference for question $q$ of paper $p$ as:
$$D_{p, q} = Y_{1, p, q} - Y_{0, p, q} \in [-1, 1]$$
The mean difference for paper cluster $p$ is:
$$\bar{D}_p = \frac{1}{2}\left(D_{p, 1} + D_{p, 2}\right)$$
Because $m=2$ is constant across all $K=50$ papers, the population estimand $\theta$ is simultaneously the expected mean per-question difference and the expected mean paper difference:
$$\theta = \mathbb{E}_{\mathcal{P}}[D_{p, q}] = \mathbb{E}_{\mathcal{P}}[\bar{D}_p]$$
The sample estimator is:
$$\hat{\theta} = \Delta_{\text{obs}} = \frac{1}{2K}\sum_{p=1}^K \sum_{q=1}^2 D_{p, q} = \frac{1}{K}\sum_{p=1}^K \bar{D}_p$$

### 3.2. Disambiguation of Null Hypotheses
In statistical inference for paired AI model evaluation, four distinct null hypotheses can be formulated. They are **not interchangeable**:

| Null Hypothesis Formulation | Formal Mathematical Statement | Substantive Meaning | Planned Inference Match? |
| :--- | :--- | :--- | :---: |
| **1. Population Mean Difference is Zero** | $H_0: \theta = \mathbb{E}[D_{p, q}] = 0$ | On average across the population of scientific papers, candidate and baseline models achieve equal token F1. Models may differ on individual questions or have unequal variances. | **YES (Primary Intended Null)** |
| **2. Sharp Null of No Treatment Effect** | $H_0^{\text{sharp}}: D_{p, q} = 0 \quad \forall (p, q)$ | The candidate and baseline models produce identical token F1 on every single question in the entire paper population. | **NO (Vastly Too Restrictive)** |
| **3. Distributional Equality / Symmetry** | $H_0^{\text{dist}}: D_{p, q} \stackrel{d}{=} -D_{p, q}$ | The distribution of paired differences is symmetric around 0; model labels are exchangeable conditional on the question. | **NO (Distributional, though useful for permutation)** |
| **4. Sampling Distribution Null** | $H_0^{\text{samp}}: \hat{\theta} \sim \mathcal{N}(0, \sigma_K^2)$ | Asymptotic normal null model for the sample mean difference. | **NO (Parametric Approximation)** |

The planned scientific inference is intended to test **Hypothesis 1 ($H_0: \theta = 0$ vs. $H_1: \theta \ne 0$)**: whether one language model achieves superior average answer correctness over another in the target scientific RAG environment.

### 3.3. Clustered Structure and Cluster Integrity
- Questions from the same paper share identical document text, identical section structures, identical upstream retrieval pools, and correlated human annotation styles.
- Therefore, $\text{Cov}(D_{p, 1}, D_{p, 2}) \ne 0$.
- Resampling individual questions independently would break this intra-paper correlation, artificially inflating the effective sample size from $K=50$ to $N=100$, deflating the standard error, and causing severe anti-conservative Type I error inflation.
- **Cluster Integrity Rule:** When paper $p$ is resampled into bootstrap replicate $b$, the entire bivariate pair $(D_{p, 1}, D_{p, 2})$ must be included intact.

---

## 4. Mathematical Audit of the Current Bootstrap p-Value Formula

We audited the exact formula in `stats.py: line 186`:
$$p = \min\left(1.0, 2 \cdot \frac{r + 1}{B + 1}\right)$$
where $r$ counts bootstrap differences on the opposite side of zero from $\Delta_{\text{obs}}$, including ties ($\Delta_b^* = 0$).

### 4.1. Audit Questions and Detailed Findings

#### 1. Are the bootstrap replicates centered on the observed effect, or generated without null centering?
**Finding: Uncentered.**
In `stats.py: lines 166–176`, bootstrap replicates are drawn directly from the empirical sample:
$$\Delta_b^* = \frac{1}{K}\sum_{p \in \mathcal{P}_b^*} \bar{D}_p$$
Conditional on the observed sample, the expectation of the bootstrap distribution is:
$$\mathbb{E}_*[\Delta_b^*] = \Delta_{\text{obs}}$$
The distribution of $\Delta_b^*$ is centered at the sample point estimate $\Delta_{\text{obs}}$, **not at the null value $\theta_0 = 0$**.

#### 2. Does the implementation approximate a null distribution or sampling uncertainty around the observed effect?
**Finding: Sampling uncertainty around the observed effect only.**
The bootstrap replicates approximate the sampling distribution of $(\hat{\theta} - \theta)$ shifted by $\hat{\theta}$. They do not model how the data would behave if $H_0: \theta = 0$ were true.

#### 3. What assumptions would make the proposed p-value valid for the intended null hypothesis?
**Finding: Unrealistic and unverified assumptions.**
For this tail probability to behave as an exact, uniformly distributed $p$-value under $H_0$:
1. **Translation Invariance (Location-Shift Model):** The shape, variance, and skewness of $\hat{\theta}$ must be invariant to the true parameter value $\theta$, so that $\mathcal{L}(\hat{\theta} \mid \theta = 0) \equiv \mathcal{L}(\hat{\theta} - \Delta_{\text{obs}} \mid \theta = \Delta_{\text{obs}})$. For bounded metrics like Token F1 $\in [0, 1]$, variance depends strongly on the mean, violating pure shift invariance.
2. **Strict Symmetry of the Sampling Distribution:** Doubling the one-sided tail area assumes the distribution of $\hat{\theta}$ is symmetric about $\Delta_{\text{obs}}$. If the bootstrap distribution is skewed, the two tails have unequal probabilities, and $2 \times \text{tail}$ fails to reflect the true two-sided probability mass.
3. **Pivotal Inversion Accuracy:** Percentile bootstrap intervals are only first-order accurate ($O(K^{-1/2})$ coverage error; Hall 1992, Davison & Hinkley 1997). Inverting them inherits this $O(K^{-1/2})$ calibration error.

#### 4. Is the `+1` finite-resampling correction sufficient to establish valid Type I error control?
**Finding: No.**
The $+1$ adjustment (Davison & Hinkley 1997, p. 148; North, Curtis & Sham 2002) is derived from permutation theory, where under $H_0$, the observed test statistic and all $B$ permutations are identically distributed and exchangeable. Under exchangeability, $\frac{r + 1}{B + 1}$ is uniformly distributed on the grid $\{ \frac{1}{B+1}, \frac{2}{B+1}, \dots, 1 \}$.
In contrast, in an uncentered bootstrap:
- The observed statistic $\Delta_{\text{obs}}$ is the center of the bootstrap cloud, not an exchangeable draw from a null distribution.
- The replicates are not generated under $H_0$.
- Adding $+1$ prevents claiming $p = 0.0000$ when $r=0$, but it does not correct the bias, skewness, or uncentered nature of the distribution.

#### 5. Is doubling the smaller tail probability justified?
**Finding: Only under symmetry.**
If the distribution of Token F1 differences is skewed (e.g. when many questions yield near-zero differences while a few technical questions produce large differences), the probability mass in the left tail beyond zero does not equal the probability mass in the right tail beyond $2\Delta_{\text{obs}}$. Doubling the smaller tail is an ad-hoc heuristic that distorts two-sided error rates.

#### 6. Does counting zero-valued replicates conservatively resolve ties without introducing other calibration problems?
**Finding: Resolves the identical-model edge case, but distorts calibration near zero.**
Including $\Delta_b^* = 0$ in $r$ ensures that when two models produce identical predictions, $r = B$ and $p = 1.0$. However, because Token F1 differences on individual questions often produce exact zeros (when both models produce identical answers or both score 0.0), the distribution of $\Delta_b^*$ contains discrete mass spikes. Grouping all ties into $r$ causes discontinuous upward jumps in the pseudo-$p$-value, making it excessively conservative for small non-zero differences.

#### 7. Does the method correctly handle a zero observed difference and identical model scores?
**Finding: Yes.**
If Model A and Model B are identical: $\Delta_{\text{obs}} = 0$, all $\Delta_b^* = 0$, $r = B$, and $p = \min(1.0, 2(B+1)/(B+1)) = 1.0$.
If Model A and Model B are different but produce $\Delta_{\text{obs}} = 0.0$ by cancellation: $r \approx B/2$, yielding $p \approx 1.0$.

#### 8. Does the procedure have a defensible interpretation when model differences are nonzero but small?
**Finding: Only as an achieved confidence level (ASL), not as a p-value.**
When $\Delta_{\text{obs}} \ne 0$, the quantity represents:
$$\tilde{p} = 2 \cdot \mathbb{P}_*(\Delta_b^* \le 0 \mid \text{data})$$
This answers: *"At what nominal level $\tilde{\alpha}$ would the central percentile bootstrap confidence interval just include zero?"*
It does **not** answer: *"What is the probability of observing a difference this large if the models were equally effective in the population?"*

#### 9. Does Holm–Bonferroni provide valid FWER control when applied to these values?
**Finding: No theoretical guarantee.**
Holm's step-down method (Holm 1979) mathematically requires that each marginal $p$-value $P_i$ is sub-uniform under the null:
$$\mathbb{P}_{H_{0, i}}(P_i \le \alpha) \le \alpha \quad \forall \alpha \in [0, 1]$$
Because the uncentered percentile bootstrap pseudo-$p$-value has uncalibrated $O(K^{-1/2})$ error and can exhibit undercoverage in skewed finite samples ($K=50$), its Type I error rate can exceed $\alpha$. Applying Holm–Bonferroni to invalid marginal pseudo-$p$-values cannot guarantee that the family-wise error rate is controlled at $\alpha = 0.05$.

---

## 5. Comparison of Defensible Alternative Methods

We evaluated the four primary candidate methods suited for paired, paper-clustered data with $K=50$ papers and $m=2$ questions per paper:

| Dimension | Method A: Clustered Bootstrap CI Only (Estimation Focus) | Method B: Null-Centered Cluster Bootstrap Test | Method C: Paper-Cluster Paired Randomization / Sign-Flip Test | Method D: Paper-Cluster Paired $t$-Test |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Reference** | Efron & Tibshirani (1993), Ch. 13 | Hall & Wilson (1991), Biometrics | Fisher (1935); Lehmann & Romano (2005); Dror et al. (2018) | Standard Cluster-Robust OLS / Paired $t$ |
| **Target Null Hypothesis** | No formal NHST; parameter estimation: $\theta = \mathbb{E}[\bar{D}_p]$ | $H_0: \theta = 0$ (Mean Difference = 0) | $H_0^{\text{sym}}: \bar{D}_p \stackrel{d}{=} -\bar{D}_p$ (Label Exchangeability) | $H_0: \theta = 0$ (Mean Difference = 0) |
| **Test Statistic** | $\hat{\theta} = \Delta_{\text{obs}}$ with 95% Percentile CI | Shifted $\tilde{\Delta}_b^* = \Delta_b^* - \Delta_{\text{obs}}$ | $T_m = \frac{1}{K}\sum_{p=1}^K s_p \bar{D}_p$, $s_p \in \{-1, +1\}$ | $t = \frac{\bar{D}}{s_{\bar{D}} / \sqrt{K}}$ with $df = K-1 = 49$ |
| **Null Enforced?** | N/A (Estimation) | Yes (Centered by subtracting $\Delta_{\text{obs}}$) | Yes (Symmetric sign reflection under $H_0$) | Yes (Studentized null distribution $t_{49}$) |
| **Two-Sided Definition** | Empirical percentiles $[2.5\%, 97.5\%]$ | Symmetric absolute tail: $\mathbb{I}(\|\tilde{\Delta}_b^*\| \ge \|\Delta_{\text{obs}}\|)$ | Symmetric absolute tail: $\mathbb{I}(\|T_m\| \ge \|\Delta_{\text{obs}}\|)$ | Two-sided $2(1 - F_{t_{49}}(\|t\|))$ |
| **Exactness / Calibration** | $O(K^{-1/2})$ coverage error | Asymptotic; requires studentization for $O(K^{-1})$ | **Exact finite-sample conditional test** | Asymptotic under CLT ($K=50$ clusters) |
| **Compatibility with Design ($K=50, m=2$)** | Excellent; transparent representation of estimation uncertainty | Good; requires careful variance handling | **Excellent; $2^{50} \approx 1.12 \times 10^{15}$ exact sign combinations** | Excellent; collapses bivariate pairs into paper means $\bar{D}_p$ |
| **FWER Control with Holm?** | N/A (Not a test, unless 98.33% CIs reported) | Approximate (subject to bootstrap error) | **Fully guaranteed (Sub-uniformity holds exactly)** | Guaranteed under asymptotic normality |
| **Key Limitation** | Does not provide a binary decision threshold; requires Bonferroni CIs for multiplicity | Unstudentized shift assumes homoskedasticity; studentized shift unstable | Tests conditional symmetry rather than pure mean difference | Assumes cluster sample mean is approximately normal |

---

## 6. Recommended Primary Inferential Procedure

We recommend a scientifically sound, two-component inferential architecture that cleanly separates **Parameter Estimation** from **Hypothesis Testing**:

### 6.1. Primary Component 1: Parameter Estimation and Uncertainty
- **Estimand:** Mean paired per-question Answer Token F1 difference:
  $$\Delta_{\text{obs}} = \frac{1}{100}\sum_{i=1}^{100} (S_{\text{cand}, i} - S_{\text{base}, i}) = \frac{1}{50}\sum_{p=1}^{50} \bar{D}_p$$
- **Uncertainty Interval:** **95% Paper-Clustered Paired Bootstrap Percentile Confidence Interval** $[\Delta_{2.5\%}^*, \Delta_{97.5\%}^*]$ ($B=2,000$, `seed=42`).
- **Interpretation:** Reports the estimated effect magnitude and the plausible range of the population mean difference without making parametric assumptions.

### 6.2. Primary Component 2: Formal Hypothesis Testing (Replacing Flawed Pseudo-p-Value)
If formal hypothesis testing and $p$-values are required for thesis claims, the uncentered pseudo-$p$-value in `DEC03_FINAL_EVALUATION_PROTOCOL.md: Section 5.3` **must be replaced** by the:
**Paper-Cluster Paired Randomization / Sign-Flip Test ($M=10,000$ Monte Carlo permutations, `seed=42`)**.

#### Mathematical Specification:
1. For each paper cluster $p \in \{1, \dots, 50\}$, compute the cluster mean difference:
   $$\bar{D}_p = \frac{1}{2}\left(S_{\text{cand}, p, 1} - S_{\text{base}, p, 1} + S_{\text{cand}, p, 2} - S_{\text{base}, p, 2}\right)$$
2. The observed test statistic is:
   $$T_{\text{obs}} = \Delta_{\text{obs}} = \frac{1}{50}\sum_{p=1}^{50} \bar{D}_p$$
3. Under the null hypothesis of model exchangeability, the sign of each paper's difference is independent and equally likely to be $+1$ or $-1$.
4. For permutation $m \in \{1, \dots, M\}$ ($M=10,000$, `seed=42`), sample a Rademacher random vector $\mathbf{s}^{(m)} \in \{-1, +1\}^{50}$ with $\mathbb{P}(s_p^{(m)} = +1) = 0.5$, and compute:
   $$T^{(m)} = \frac{1}{50}\sum_{p=1}^{50} s_p^{(m)} \bar{D}_p$$
5. Compute the exact two-sided finite-sample corrected $p$-value:
   $$p = \frac{1 + \sum_{m=1}^M \mathbb{I}(|T^{(m)}| \ge |T_{\text{obs}}|)}{M + 1}$$
   - *Ties and Zeros:* If $\bar{D}_p = 0$, $s_p \bar{D}_p = 0$ for all signs. If $T_{\text{obs}} = 0$, $|T^{(m)}| \ge 0$ holds for all $m$, yielding $p = \frac{1 + M}{M + 1} = 1.0$.
6. **Multiplicity Control:** Apply Holm–Bonferroni step-down adjustment across the 3 pre-registered comparisons ($m=3$) to guarantee FWER $\le 0.05$. Because sign-flip $p$-values are exact under symmetry, Holm's condition $\mathbb{P}_{H_0}(P \le \alpha) \le \alpha$ is mathematically satisfied.

---

## 7. Separate Assessment of the 95% Bootstrap Confidence Interval

Is the 95% percentile cluster-bootstrap interval reasonable for parameter estimation under this design?
- **Sample Size ($K=50$ Clusters):** In econometrics and statistics literature on clustered data (Cameron et al. 2008, MacKinnon & Webb 2017), 50 clusters is a standard threshold where cluster bootstrap provides reliable standard errors and sensible central confidence intervals.
- **Balanced Design ($m=2$ Questions per Paper):** Because every paper has exactly 2 questions, the cluster bootstrap does not suffer from random sample-size distortion ($N^* \equiv 100$ in every replicate).
- **Monte Carlo Precision vs. Statistical Coverage:**
  Running $B=2,000$ replicates guarantees that the simulation error of the quantile estimation is negligible ($\text{SE} \approx 0.0035$). However, this precision must not be mistaken for guaranteed 95.0% coverage. In finite samples with bounded or skewed data, actual coverage may range between 92% and 95%.
- **Conclusion:** The 95% percentile bootstrap interval is **sound, defensible, and recommended as a descriptive uncertainty measure**, provided it is not casually inverted to manufacture pseudo-$p$-values.

---

## 8. Multiple Comparisons and Reporting Protocol

### 8.1. Pre-Registered Comparisons
1. **Comparison 1:** `llama3.2:3b` vs. `llama3.2:1b` ($\Delta = \bar{S}_{3\text{b}} - \bar{S}_{1\text{b}}$)
2. **Comparison 2:** `llama3.2:3b` vs. `qwen2.5:0.5b` ($\Delta = \bar{S}_{3\text{b}} - \bar{S}_{0.5\text{b}}$)
3. **Comparison 3:** `llama3.2:1b` vs. `qwen2.5:0.5b` ($\Delta = \bar{S}_{1\text{b}} - \bar{S}_{0.5\text{b}}$)

### 8.2. Canonical Reporting Schema
The final thesis report must present the results in this format:

| Comparison | Candidate | Baseline | $\Delta_{\text{obs}}$ (Token F1) | 95% Cluster Bootstrap CI (Unadjusted) | Raw $p$ (Sign-Flip Test) | Holm Adjusted $p_{\text{adj}}$ | Formal Decision ($\alpha = 0.05$) | Practical Effect ($\Delta \ge 0.030$) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `llama3.2:3b` | `llama3.2:1b` | TBD | [TBD, TBD] | TBD | TBD | Significant / Not Sig | Exceeded / Not Met |
| 2 | `llama3.2:3b` | `qwen2.5:0.5b` | TBD | [TBD, TBD] | TBD | TBD | Significant / Not Sig | Exceeded / Not Met |
| 3 | `llama3.2:1b` | `qwen2.5:0.5b` | TBD | [TBD, TBD] | TBD | TBD | Significant / Not Sig | Exceeded / Not Met |

### 8.3. Discrepancy Protocol (CI vs. p-Value)
- The reported 95% confidence intervals are **unadjusted marginal intervals** reflecting estimation uncertainty for that specific comparison.
- The Holm-adjusted $p$-values control family-wise Type I error across all three tests.
- If a comparison has a 95% CI that does not cover zero (e.g. $[+0.002, +0.025]$) but its Holm-adjusted $p$-value is $p_{\text{adj}} \ge 0.05$, the outcome must be reported as:
  *"The marginal difference was estimated positively, but the effect does not reach family-wise statistical significance after multiplicity correction across the three comparisons."*
- A nonsignificant outcome ($p_{\text{adj}} \ge 0.05$) **must never be described as evidence of model equivalence**. It indicates insufficient evidence to reject the null of equal performance at the available sample size ($K=50$).

---

## 9. Verification Checks Executed

| Verification Check | Method | Result |
| :--- | :--- | :--- |
| **Inspect `stats.py` Implementation** | Full file inspection (`view_file lines 1–235`) | Confirmed uncentered resampling, tie-handling logic, and Holm step-down. |
| **Inspect Preliminary RQ5 Script** | Full file inspection (`view_file lines 1–318`) | Confirmed preliminary pilot evaluated 16 seed questions without bootstrap statistics. |
| **Validate Exposure JSON Syntax** | `python -c "import json..."` in `backend/venv` | Verified `dec03_exposure_overlap_report.json` is syntactically valid and intact. |
| **Git Working Tree Status** | `git status --short` | Confirmed zero commits made; all changes remain uncommitted working tree edits. |

---

## 10. Confirmation of Hard Constraints

In strict compliance with the Stage C2.5 directives:
- **Zero papers or questions were sampled.**
- **Zero model outputs were generated.**
- **Zero models were downloaded.**
- **Zero benchmarks were run.**
- **Zero production code, configuration, or model settings were altered.**
- **Zero Git commits were made.**
- **Sample size ($K=50, m=2, N=100$), primary metric (Answer Token F1), and the 3 planned comparisons remain strictly fixed.**
