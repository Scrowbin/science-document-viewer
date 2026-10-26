# RQ5 Local LLM Generation Confirmatory Benchmark Report (250 Papers / 500 Questions)
**Canonical Experiment ID:** `EXP-RQ5-MAIN-SAMPLED`
**Protocol Document:** [`eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md`](./DEC03_FINAL_EVALUATION_PROTOCOL.md)
**Manifest File:** [`eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json`](./eval_sample_manifest_500q.json)
**Hardware Environment:** AMD Ryzen 5 5600 6-Core Processor, 16 GB DDR4, Windows 11
**Execution Timestamp:** 2026-10-26T14:08:31.530145+00:00
**Deterministic Settings:** `temperature=0.0`, `num_predict=256` across all candidate models.

## 1. Candidate Model Performance Summary

| Model | Parameters | Answer F1 (Overall) | Extractive F1 | Abstractive F1 | Boolean F1 | Refusal Count (Rate %) | Containment Proxy (Lexical Overlap) (%) | Latency P50 | Latency P95 | Throughput (tok/s) | Peak Python RSS | Peak Ollama RSS | Sum of Measured RSS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` | 3.21B | **0.2033** | 0.2605 | 0.1438 | 0.0385 | 243 (48.6%) | **37.9%** | 6.55s | 15.16s | **12.7** | 0.0 MB | 0.0 MB | 0.0 MB |
| `llama3.2:1b` | 1.23B | **0.1346** | 0.1730 | 0.1108 | 0.0006 | 294 (58.8%) | **29.3%** | 5.08s | 9.83s | **20.4** | 106.9 MB | 41.0 MB | 147.9 MB |
| `qwen2.5:0.5b` | 0.49B | **0.2324** | 0.2912 | 0.1921 | 0.0349 | 50 (10.0%) | **60.3%** | 3.85s | 7.50s | **57.3** | 107.4 MB | 41.0 MB | 148.4 MB |

> [!NOTE]
> **Operational Metric Distinctions & Interpretations:**
> 1. **Answer F1 (Overall):** Official QASPER-style token-level F1 measuring lexical overlap with human reference answers (max over annotators). Evaluates strictly to 0.0 when a refusal is emitted against an answerable question.
> 2. **Refusal Count & Rate (%):** Frequency and percentage of queries where the model returned the explicit NFR-03 refusal message (`is_refusal = True`). Emitting a refusal is not inherently faithful; validity depends on whether the context actually lacked the necessary evidence.
> 3. **Automated Containment Proxy (Lexical Overlap) (%):** Automated heuristic measuring the proportion of informative non-stopword answer tokens found verbatim in the prompt context (evaluates to 0.0% on refusal). This is strictly an automated lexical proxy and does **not** establish semantic entailment, factual correctness, valid mathematical reasoning, or correct handling of negation. Definitive factual support is evaluated via human claim-level review.
> 4. **Known Limitation in Refusal Detection (Paraphrased Refusals):** The automated refusal flag (`is_refusal`) requires an exact substring match against the NFR-03 prompt template ('The document does not contain sufficient...' or 'does not contain sufficient'). A post-hoc audit across all 1,500 outputs identified 13 instances (0.87% of all records: 4 in Llama-3.2 1B, 9 in Qwen-2.5 0.5B) where models emitted paraphrased or partial refusals (e.g. *'The provided context does not contain information about...'*). In strict accordance with pre-registration and methodological integrity, primary scores, refusal counts, and checkpoint records are preserved exactly as generated without post-hoc rewriting, and this nuance is documented as a known string-matching limitation.

## 2. Pre-Registered Pairwise Statistical Inferential Analysis (Paper Clusters K=250, df=249)

The formal hypothesis testing procedure across the 3 pre-registered comparisons is the **Paper-Level One-Sample Paired t-Test on the 250 Paper Mean Differences ($df=249$)** with **Holm-Bonferroni step-down multiple-testing correction** ($lpha=0.05$):

| Candidate vs. Baseline | Observed $\Delta$ | 95% Bootstrap Percentile CI | Paper-Level $t$ ($df=249$) | Raw $p$-value | Holm-Bonferroni Adj $p_{\text{adj}}$ | Practical Effect ($\Delta \ge 0.030$) | Formal Decision |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` vs `llama3.2:1b` | **+0.0687** | [+0.0480, +0.0902] | $t=6.2597$ | 1.6762e-09 | **3.3524e-09** | MET | **REJECT_NULL (Significant)** |
| `llama3.2:3b` vs `qwen2.5:0.5b` | **-0.0291** | [-0.0509, -0.0053] | $t=-2.5028$ | 1.2964e-02 | **1.2964e-02** | NOT MET | **REJECT_NULL (Significant)** |
| `llama3.2:1b` vs `qwen2.5:0.5b` | **-0.0978** | [-0.1189, -0.0763] | $t=-8.9651$ | 7.5730e-17 | **2.2719e-16** | MET | **REJECT_NULL (Significant)** |

## 3. Pre-Registered Outlier Sensitivity Diagnostics

| Comparison | Wilcoxon $p$ (Wilcox drop zeros) | Wilcoxon $p$ (Pratt rank zeros) | Zero Differences ($K_0$) | 10% Trimmed $\Delta_{\text{trim}}$ ($K_{\text{trim}}=200$) | Max Jackknife Influence |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `llama3.2:3b` vs `llama3.2:1b` | 3.4901e-09 | 1.5941e-09 | 48/250 | +0.0575 | 0.003071 |
| `llama3.2:3b` vs `qwen2.5:0.5b` | 2.8407e-03 | 2.7546e-03 | 5/250 | -0.0311 | 0.002753 |
| `llama3.2:1b` vs `qwen2.5:0.5b` | 6.6114e-16 | 6.4109e-16 | 12/250 | -0.0898 | 0.002324 |

## 4. Formal Methodological Verification & Measurement Boundaries

### 4.1. Paper-Cluster Bootstrap Implementation Verification
- **Resampling Unit:** Exactly 250 paper clusters ($K=250$), matching the cluster unit of the paired $t$-test. In each replicate, $K=250$ paper-level mean paired differences are sampled with replacement.
- **Replicates & Seed:** $B=2,000$ iterations using Python's standard `random.Random(42)`. Percentile confidence intervals are derived from sorted bootstrap sample means at indices $50$ (2.5th percentile) and $1,950$ (97.5th percentile).
- **Verification Parity:** The reported intervals match the implementation to 4 decimal places, independently recomputed and verified against the permanently frozen checkpoint (`rq5_inference_checkpoint.jsonl`, SHA-256: `b53166efe4e8f27e34fd9f3c6efc6816214f8f2ff374682ada0f67cb030eb4b4`).

### 4.2. Precise Inferential Interpretation Matrix

| Comparison | Reported Difference in F1 ($\Delta$) | Formal Interpretation |
| :--- | :---: | :--- |
| **`llama3.2:3b` − `llama3.2:1b`** | **+0.0687** | Statistically significant ($p_{\text{adj}} = 3.35 \times 10^{-9}$); exceeds exploratory practical threshold ($\Delta \ge 0.030$). |
| **`llama3.2:3b` − `qwen2.5:0.5b`** | **−0.0291** | Statistically significant ($p_{\text{adj}} = 0.0130$); falls just below exploratory practical threshold ($|\Delta| < 0.030$). |
| **`llama3.2:1b` − `qwen2.5:0.5b`** | **−0.0978** | Statistically significant ($p_{\text{adj}} = 2.27 \times 10^{-16}$); exceeds exploratory practical threshold ($|\Delta| \ge 0.030$). |

- **Threshold Caveat:** The $\Delta = 0.030$ cutoff is strictly an exploratory practical-effect reference, **NOT a formal statistical equivalence boundary**. The fact that `llama3.2:3b` vs `qwen2.5:0.5b` falls slightly below 0.030 does **NOT** prove the models are practically equivalent.
- **Metric Boundary:** Because the primary metric is Answer Token F1, these results establish differences in **lexical agreement with human reference answers**, NOT necessarily differences in factual correctness, logical coherence, or semantic faithfulness.

### 4.3. Refusal Detection as an Unresolved Measurement Limitation
- **Detector-Based Rates:** The reported refusal rates (48.6%, 58.8%, 10.0%) are detector-based counts tied strictly to the NFR-03 substring match, not guaranteed counts of every actual refusal.
- **Preservation of Primary Analysis:** In accordance with pre-registration integrity, primary scores and refusal counts are preserved as generated without post-hoc rewriting.
- **Sensitivity Guidance for Thesis:** Any future sensitivity analysis employing broader semantic or regex-based refusal classification must be reported separately alongside its explicit classification rules, without overwriting the primary preregistered results.
