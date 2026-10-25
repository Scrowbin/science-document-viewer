# RQ4: Hybrid Retrieval Benchmark on Official QASPER Test Corpus
**Evaluation of Dense, Lexical, Reciprocal Rank Fusion, and Convex Score Fusion under Hierarchical Context Assembly**

---

## 1. Research Question and Experimental Scope

**Formal Research Question:**
> **RQ4:** *How do different retrieval strategies (Dense Only, BM25 Only, Hybrid RRF, and Hybrid Convex) affect the quality of the evidence context retrieved for scientific question answering, when evaluated using a fixed extraction, chunking, and embedding configuration?*

**Explicit Scope Delineation:**
RQ4 evaluates **retrieval strategies exclusively**. It measures the quality, coverage, and rank ordering of the assembled evidence context retrieved from academic papers. It does **not** evaluate end-to-end answer correctness, generation quality, or factual faithfulness (hallucination) of the downstream Large Language Model (LLM). Evaluating LLM-generated answers requires distinct generation metrics (e.g., token-level F1, Answer Relevance, and Faithfulness) and is delineated as a separate evaluation stage (RQ5).

---

## 2. Dataset and Evaluation Split

* **Dataset:** Official **QASPER v0.3** (*Question Answering on Scientific Papers*, Dasigi et al., NAACL 2021) released by the Allen Institute for AI.
* **Test Split Composition:**
  - Official QASPER Test split total: **416 papers**.
  - Papers with text-evidenced queries: **408 papers**.
  - Total queries evaluated: **1,310 answerable, text-evidenced queries** (mean: 3.21 queries/paper; range: 1 to 9 queries).
  - Total candidate chunks: **14,035 child chunks** (~200 tokens each).
* **Exclusion Criteria:**
  Eight papers (`1710.07394`, `1808.10059`, `1802.09233`, `1711.11017`, `1602.07776`, `2003.10564`, `1910.09942`, `1910.12477`) were excluded because they contain only unanswerable questions (`unanswerable`) or questions whose evidence consists purely of unextracted figures/tables (`FLOAT SELECTED`) with zero textual evidence ($R_q = \emptyset$). Evaluating retrieval metrics when $R_q = \emptyset$ produces undefined nDCG and Recall values.
* **Development versus Test Role:**
  - *Development Set (281 papers, 892 queries across 276 papers):* Used strictly for exploratory hyperparameter search and algorithm selection.
  - *Test Set (408 papers, 1,310 queries):* The selected configurations were completely **frozen** and evaluated on this held-out Test split. No iterative tuning, parameter exploration, or split pooling was performed.
* **Unit of Analysis:**
  Queries are naturally clustered within papers (mean: 3.21 queries/paper). Therefore, all statistical inferential procedures use paper-level cluster bootstrap resampling to preserve intra-paper correlations.

---

## 3. Compared Retrieval Strategies

| Strategy | Specific Configuration | Purpose in Experiment |
| :--- | :--- | :--- |
| **Dense Only** | `intfloat/e5-small-v2` (384-d, FP32 L2 normalized, `"passage: "` and `"query: "` task prefixes, exact BLAS cosine) | Primary semantic retrieval **Baseline** for all paired statistical comparisons |
| **BM25 Only** | Subword WordPiece BM25 ($k_1=1.5, b=0.75$, 39 stopwords stripped) | Classic lexical retrieval baseline (**Lexical Reference**) |
| **Hybrid RRF** | Unweighted Reciprocal Rank Fusion ($k=60$): $\text{RRF}(d) = \sum_{m} \frac{1}{60 + \text{rank}_m(d)}$ | Rank-based fusion combining dense and lexical rankings; **active production default** |
| **Hybrid Convex** | Min-max calibrated convex score fusion ($\alpha=0.7$): $S_{\text{convex}}(d) = 0.7 \cdot S_{\text{Dense}}^{\text{norm}}(d) + 0.3 \cdot S_{\text{BM25}}^{\text{norm}}(d)$ | Asymmetric score-based fusion prioritizing dense semantics |

* **Fixed Pipeline Controls:** All upstream and downstream pipeline components were held 100% constant across all four arms:
  - Text Extraction: `pymupdf_layout`.
  - Chunking Architecture: `hierarchical` Small-to-Big (~200 token child chunks, 40-token overlap).
  - Embedding Model: `intfloat/e5-small-v2` (384 dimensions).
  - Parent Section Cap: `MAX_PARENTS = 5`.
  - Context Token Budget: 1,600 tokens.
* **Ablation Boundary:** RRF with $k=20$ was explored on the Development set and excluded from the frozen Test comparison to preserve the pre-specified confirmatory testing budget.

---

## 4. Retrieval Pipeline and Fixed Parameters

### Flowchart from Paper to Assembled Evidence Context

```text
QASPER Paper Collection (408 evaluated papers)
                     │
                     ▼
14,035 Child Chunks (~200 tokens each, 40-token overlap)
                     │
                     ▼
Candidate Retrieval (Dense, BM25, RRF, or Convex)
                     │  (Retrieve top-20 child chunks per paper)
                     ▼
Small-to-Big Expansion (Expand child chunks into parent sections)
                     │  (Deduplicate parent sections; window parent if >800 tokens)
                     ▼
Context Assembly (Assemble prompt context)
                     │  (Cap at MAX_PARENTS = 5 sections; 1,600-token budget)
                     ▼
Evaluate Assembled Evidence Context (Compute nDCG, Recall, MRR, Hit Rate)
```

### Fixed Experimental Settings
- **Parent-section cap:** `MAX_PARENTS = 5`.
- **Context token budget:** 1,600 tokens (measured using `cl100k_base` via `tiktoken`).
- **Evidence containment threshold:** $\tau = 0.50$ (WordPiece token containment).
- **Random seed:** `seed = 42`.
- **Embedding model & dimension:** `intfloat/e5-small-v2`, 384 dimensions.
- **First-stage retrieval depth:** Top-20 child chunks retrieved per paper before parent expansion.
- **Handling of missing/empty retrievals:** Empty candidate lists receive a score of 0.0.

### Two Implementation Details That Must Not Be Hidden
1. **BM25 Implementation Difference:**
   - *Benchmark implementation:* Computes inverse document frequency (IDF) over the split-wide chunk background (14,035 chunks) to avoid negative or unstable IDFs on single-paper vocabularies (~35 chunks).
   - *Production implementation (`DocumentRAG`):* Computes BM25 over the active document's chunks (document-local BM25).
   - *Interpretation:* The benchmark result is a necessary engineering approximation for large-scale automated evaluation; it should not be interpreted as an exact measurement of document-local BM25 behavior.
2. **Metrics Are Computed After Context Assembly:**
   - All evaluation metrics are calculated **after** Small-to-Big parent expansion, parent deduplication, the 5-parent cap, and the 1,600-token budget cut.
   - Therefore, the metrics evaluate the **retrieval quality of the assembled evidence context** supplied to the LLM prompt, rather than unconstrained candidate ranking pools.

---

## 5. Metrics and Their Meanings

| Metric | Role | What It Tells the Reader |
| :--- | :---: | :--- |
| **nDCG@10** | **Primary** | Quality and ordering of relevant evidence within the evaluated top-10 context ranking |
| **nDCG@4** | Supporting | Quality of the highest-ranked evidence (directly aligns with LLM prompt context window) |
| **Recall@20** | Supporting | Coverage of relevant evidence within evaluated top-20 results (physically capped by MAX_PARENTS=5) |
| **MRR@10** | Supporting | How highly the first relevant result is ranked |
| **Hit@5** | Supporting | Proportion of queries with at least one relevant result in the top five |

* **Relevance Judgment Method:**
  Relevance between gold evidence passage $E$ and candidate chunk $C$ is computed via WordPiece subword token containment:
  $$\text{containment}(E, C) = \frac{|T(E) \cap T(C)|}{|T(E)|}$$
  A chunk is labeled relevant (binary 1) if $\text{containment}(E, C) \ge 0.50$, else 0.
* **Definition of Evaluated Result Unit:**
  Each unit in the evaluated ranking is an **expanded parent section**. A parent section is counted as relevant if it contains at least one child chunk satisfying $\tau \ge 0.50$.

---

## 6. Statistical Analysis Protocol

1. **Paired Comparisons:** Each candidate strategy is paired directly against `Dense Only` across the identical 1,310 queries.
2. **Paper-Cluster Bootstrap:** $B = 2,000$ bootstrap replicates with fixed `seed = 42`, resampling at the paper level to account for intra-paper query clustering.
3. **Confidence Intervals:** 95% two-sided bootstrap confidence intervals for the mean difference: $\Delta = \text{Metric}(\text{Candidate}) - \text{Metric}(\text{Dense Only})$.
4. **Multiple Comparisons Control:** Sequential **Holm-Bonferroni correction** applied across the three planned comparisons against Dense Only (`BM25`, `Hybrid RRF k=60`, `Hybrid Convex alpha=0.7`) to control Family-Wise Error Rate (FWER) at $\alpha = 0.05$.
5. **Pre-specified Significance Threshold:** $\alpha = 0.05$.
6. **Primary Decision Metric:** All confirmatory inferential conclusions are based on **nDCG@10**.
7. **Interpretation of Non-Significance:** A non-significant result (e.g., RRF $k=60$ with $p_{\text{adj}} = 0.8696$) is **not** mathematical proof that two strategies are equivalent. It means this experiment did not establish a statistically significant difference under this evaluation protocol.

---

## 7. Held-Out Test Results

*Table: Consolidated Retrieval Evaluation Results on QASPER Test Split (408 papers, 1,310 queries).*

| Strategy | nDCG@10 (Primary) | nDCG@4 | Recall@20 | MRR@10 | Hit@5 (%) | $\Delta$ vs. Dense [95% CI] | $p_{\text{raw}}$ | $p_{\text{adj}}$ (Holm) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Only (`e5-small-v2`)** | **0.5655** | 0.5724 | 0.6366 | 0.6415 | 82.7% | Baseline (0.0) | — | — |
| **BM25 Only (WordPiece)** | **0.5065** | 0.5135 | 0.5908 | 0.5688 | 77.9% | -0.0589 [-0.0788, -0.0390] | 0.0010 | **0.0030\*** |
| **Hybrid RRF ($k=60$) [Prod]** | **0.5662** | 0.5747 | 0.6413 | 0.6368 | 83.1% | +0.0008 [-0.0110, +0.0130] | 0.8696 | 0.8696 |
| **Hybrid Convex ($\alpha=0.7$)** | **0.5806** | 0.5870 | 0.6525 | 0.6556 | 84.5% | **+0.0152 [+0.0045, +0.0262]** | 0.0070 | **0.0140\*** |

*\* Indicates statistically significant difference from Dense Only baseline at $\alpha = 0.05$ after Holm-Bonferroni correction ($m=3$).*

### Prose Findings and Scientific Interpretation
1. **Convex Fusion Statistically Significant:**
   `Hybrid Convex (alpha=0.7)` achieved a statistically significant improvement over `Dense Only` on the primary metric ($\text{nDCG@10} = 0.5806$, $\Delta = +0.0152$, 95% CI $[+0.0045, +0.0262]$, $p_{\text{adj}} = 0.0140 < 0.05$). Weighting semantic dense similarity (70%) higher than lexical score (30%) effectively injects term match signals without corrupting semantic ranking.
2. **RRF Performs Comparably to Dense Only:**
   `Hybrid RRF (k=60)` achieved retrieval performance comparable to `Dense Only` ($\text{nDCG@10} = 0.5662$ vs. $0.5655$, $\Delta = +0.0008$, 95% CI $[-0.0110, +0.0130]$, $p_{\text{adj}} = 0.8696$). No statistically significant difference was established. Because keyword robustness was not separately ablated on vocabulary-mismatch sub-cohorts, RRF's keyword robustness is noted as an engineering property rather than an experimentally proven finding.
3. **BM25 Substantially Underperforms Dense:**
   `BM25 Only` scored significantly worse than `Dense Only` ($\text{nDCG@10} = 0.5065$, $\Delta = -0.0589$, $p_{\text{adj}} = 0.0030 < 0.05$), reflecting the high vocabulary mismatch typical in academic literature.
4. **Disciplined Boundaries:** These findings do not warrant claims of universal superiority across domains or improvements in downstream answer faithfulness.

---

## 8. Reproducibility and Computational Cost

* **Evaluation Script:** [`eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py).
* **Exact Execution Command:**
  ```powershell
  backend\venv\Scripts\python.exe eval\phases\phase_6_hybrid_retrieval\scripts\evaluate_full_qasper_rq4_hybrid.py --split test --strategy hierarchical
  ```
* **Software Environment:** Python 3.12, PyTorch 2.x, Transformers 4.x, NumPy, FastEmbed, Sentence-Transformers.
* **Hardware Environment:** AMD Ryzen 5 5600 6-Core / 12-Thread CPU, 16 GB DDR4 RAM, FP32 execution, fixed 4 compute threads (`torch.set_num_threads(4)`), zero GPU acceleration.
* **Cache Provenance:** 14,035 child chunk embeddings were loaded from verified pre-computed cache:
  `eval/prepared/cache/embeddings/intfloat_e5-small-v2_test_hierarchical_passage.npy`
* **Computational Cost:** Total benchmark execution time: **1,781.95 seconds (~29.7 minutes)** across 1,310 queries, 4 retrieval arms, Small-to-Big parent expansion, and 2,000 bootstrap resamples.
* **Generated Experiment Artifacts:**
  - Raw JSON metrics: [`eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json).
  - Markdown summary: [`eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md).

---

## 9. Limitations and Interpretation

1. **Cohort Boundary:** The evaluation excludes eight papers without suitable extractive text evidence; results apply strictly to the evaluated 408-paper / 1,310-query cohort.
2. **BM25 Background IDF:** Benchmark BM25 uses split-wide IDF, which differs from production document-local BM25.
3. **Context Assembly Scope:** Reported retrieval metrics evaluate assembled evidence context (after 5-parent cap and 1,600-token budget cut), not unconstrained candidate-ranking lists.
4. **Retrieval vs. Generation:** Retrieval performance measures context quality only; it does not measure downstream answer correctness, faithfulness, or user utility.
5. **Generalizability Limits:** Results are specific to QASPER, the hierarchical Small-to-Big pipeline, and the evaluated parameter set; they do not establish universal superiority across other academic domains or production workloads.
