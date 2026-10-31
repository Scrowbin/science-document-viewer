# Experiment Provenance and Contamination Registry

**Single Source of Truth for Experimental Exposure, Dataset Stratification, and Anti-Contamination Governance across RQ1–RQ6**

---

## 1. Registry Architecture & Canonical Locations

| Component | Canonical Location | Description |
| :--- | :--- | :--- |
| **Machine-Readable Registry** | [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json) | Central JSON database tracking all registered experiments, paper IDs, question IDs, exposure classifications, and item-level event logs. |
| **Documentation & Governance Rules** | [`eval/EXPERIMENT_PROVENANCE_REGISTRY.md`](file:///c:/DACNTT/eval/EXPERIMENT_PROVENANCE_REGISTRY.md) | This document: defines schemas, classification semantics, historical provenance, and mandatory workflow rules for future AI agents. |
| **Reusable Overlap Audit Tool** | [`eval/scripts/check_experiment_overlap.py`](file:///c:/DACNTT/eval/scripts/check_experiment_overlap.py) | CLI utility and Python module to verify whether any proposed paper/question cohort contains previously exposed items before sampling. |

---

## 2. Mandatory Rules for All Future Experiments

All future AI agents, researchers, and automated scripts working on this repository **MUST** adhere to the following 10 directives:

1. **Mandatory Pre-Sampling Registry Query:** Before sampling papers or questions for any experiment, the agent **MUST** query `eval/scripts/check_experiment_overlap.py` or inspect `eval/experiment_provenance_registry.json` to verify that candidate items do not suffer from undocumented or disqualifying prior experimental exposure.
2. **Pre-Registration of Planned Experiments:** Whenever practical, register a new planned experiment in `eval/experiment_provenance_registry.json` under status `PLANNED` with target sample size, selection criteria, and research question before drawing samples or running evaluations.
3. **Immediate Recording of Finalized Samples:** As soon as a sample manifest is generated and frozen, register the exact paper and question IDs in the registry.
4. **Transparent Failure & Replacement Logging:** If physical ingestion or parsing fails during an experiment, log the failure and replacement in the manifest and registry with exact failure codes; never silently discard or replace papers.
5. **Decisions Influenced Recording:** When aggregate metrics or model outputs from an experiment influence architectural, prompt, model, or threshold selections, explicitly document the decisions influenced in the registry.
6. **Artifact & Script Traceability:** Every registered experiment must cite the exact scripts that produced it and the exact result artifacts on disk.
7. **Lifecycle State Updates:** Update the registry entry when an experiment moves through its lifecycle (`PLANNED` $\to$ `SAMPLED` $\to$ `RUNNING` $\to$ `COMPLETED`, `ABANDONED`, or `INVALIDATED`).
8. **Strict Confirmatory Labeling:** **NEVER describe a previously exposed dataset or paper cohort as an untouched or blind confirmatory evaluation set.** If a full-pipeline evaluation uses previously exposed papers (such as QASPER Test used in RQ4), it must be explicitly reported as *post-retrieval-selection evaluation*, not a blind test.
9. **Pretraining Contamination Boundary:** **NEVER claim that repository-level tracking proves the absence of pretrained-model contamination.** Commercial and open-source models may have crawled public arXiv preprints during pretraining. This possibility must always be acknowledged as an external caveat.
10. **Documented Exceptions:** If previously exposed papers are reused (e.g. for ablation or sensitivity comparisons), document the reuse event explicitly with its scientific rationale and methodological caveats.

---

## 3. Exposure Classification System

The registry categorizes each exposure event and item using six standardized classifications:

| Classification Code | Operational Definition | Re-Use Implication |
| :--- | :--- | :--- |
| **`UNEXPOSED_REPOSITORY`** | No relevant prior experimental use identified in audited repository records. | **Eligible** for confirmatory evaluation sampling (e.g. RQ5 main evaluation). |
| **`EXPLORATORY_EXPOSURE`** | Used for preliminary experiments, code debugging, diagnostics, or pilot smoke-testing (e.g. RQ4 Dev hybrid check, 16-question seed pilot). | Ineligible for blind confirmatory testing if exploratory findings tuned models or prompts; may be used for descriptive diagnostic comparisons. |
| **`DEVELOPMENT_SELECTION_EXPOSURE`** | Used to evaluate and select core pipeline components (e.g. PyMuPDF in RQ1, hierarchical chunking in RQ2, `intfloat/e5-small-v2` in RQ3). | **Permanently ineligible** for confirmatory testing of the selected component or upstream pipeline steps. |
| **`CONFIRMATORY_EVALUATION_EXPOSURE`** | Evaluated in a designated confirmatory study (e.g. RQ4 Test hybrid retrieval benchmark). | **Permanently ineligible** for subsequent confirmatory testing of the overall RAG system; any future reuse represents post-hoc or post-selection evaluation. |
| **`HISTORICAL_UNCERTAIN_PROVENANCE`** | Prior use is suspected or known from unstructured notes, but exact item-level manifests cannot be verified from disk records. | Treated conservatively as exposed until proven otherwise. |
| **`POTENTIAL_PRETRAINING_CONTAMINATION`** | Applied to all public arXiv preprints as an unverified external factor acknowledging potential exposure during base LLM pretraining. | Qualitative caveat; not a basis for discarding valid repository-unexposed papers. |

---

## 4. Historical Experiments Ledger (Reconciled Baseline)

The registry formally reconciles and registers all historical experiments conducted in this repository:

| Experiment ID | Phase & Name | Split & Dataset | Papers | Questions | Key Outputs / Decisions Influenced | Primary Classification | Status |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **`EXP-RQ1-EXTRACTION`** | RQ1: PDF Layout Extraction | QASPER Dev | 47 | 127 | Selected PyMuPDF layout (heading F1 48.01%, 26.2 ms/page) and plain fallback | `DEVELOPMENT_SELECTION_EXPOSURE` | 🟢 COMPLETED |
| **`EXP-RQ2-CHUNKING`** | RQ2: Document Chunking | QASPER Dev | 47 | 127 | Selected hierarchical Small-to-Big chunking (nDCG@10 = 0.6880) and section_overlap fallback | `DEVELOPMENT_SELECTION_EXPOSURE` | 🟢 COMPLETED |
| **`EXP-RQ3-EMBEDDING-UNIFIED`** | RQ3: Dense Embedding Selection | QASPER Dev + Train | 211 prepared (207 scored) | 615 scored (450 unique IDs) | Selected `intfloat/e5-small-v2` as desktop champion (0.5522 nDCG@10, 30.2 ms, 384 dims, 33M params) | `DEVELOPMENT_SELECTION_EXPOSURE` | 🟢 COMPLETED |
| **`EXP-RQ4-HYBRID-DEV`** | RQ4: Hybrid Retrieval Dev | QASPER Dev | 276 | 892 | Verified hybrid fusion does not degrade dense accuracy on Dev ($p_{\text{adj}} = 1.000$) | `EXPLORATORY_EXPOSURE` | 🟢 COMPLETED |
| **`EXP-RQ4-HYBRID-TEST`** | RQ4: Hybrid Retrieval Test | QASPER Test | 408 | 1,310 | Evaluated Convex gain under split-wide IDF (14,035 chunks); provisional RRF retained in production. **Permanently marks QASPER Test as exposed.** | `CONFIRMATORY_EVALUATION_EXPOSURE` | 🟢 COMPLETED |
| **`EXP-RQ5-PILOT-SEED`** | RQ5: Preliminary SLM Pilot | Curated Seed (Non-QASPER) | 4 | 16 | Tooling smoke test, greedy decoding verification, motivated Wilcoxon & trimmed mean sensitivity checks | `EXPLORATORY_EXPOSURE` | 🟢 COMPLETED |
| **`EXP-RQ5-MAIN-SAMPLED`** | RQ5: Confirmatory SLM Evaluation | QASPER Train Unexposed | **250 primary** (+50 standby reserve) | **500 items** (1,503 pool) | Frozen evaluation manifest (`eval_sample_manifest_500q.json`, SHA-256: `4a1117b8...`); Option A approved (60 human review answers). Zero historical overlap. | `CONFIRMATORY_EVALUATION_EXPOSURE` | 🟢 SAMPLED_FROZEN |

---

## 5. Summary of Dataset Exposure & Reservoir State

```text
========================================================================================
                              OFFICIAL QASPER v0.3 SPLITS
                              Total: 1,585 Papers / 5,049 Questions
────────────────────────────────────────────────────────────────────────────────────────
   QASPER Dev (281 papers)       QASPER Test (416 papers)       QASPER Train (888 papers)
   - 47 in RQ1 & RQ2             - 408 evaluated in RQ4 Test    - 111 in RQ3 Embedding
   - 100 in RQ3 Embedding        - 8 un-run (zero chunks)       - 777 EXPERIMENT-UNEXPOSED
   - 276 evaluated in RQ4 Dev    ────────────────────────────   ────────────────────────
   - 279 unique with runs        [PERMANENTLY EXPOSED]          [UNEXPOSED RESERVOIR]
   - 2 un-run (no text ev)
   ──────────────────────────
   [PERMANENTLY EXPOSED]
========================================================================================

                 HISTORICAL EXPOSURE RECONCILIATION: 804 vs 802 PAPERS
────────────────────────────────────────────────────────────────────────────────────────
1. Partition-Level Historical Exposure Total:               804 unique papers
   - 111 Train papers (RQ3 Embedding)
   - 281 Dev papers (all official Dev papers; development partition)
   - 408 Test papers (evaluated in RQ4 Test retrieval)
   -   4 Curated Seed papers (evaluated in RQ5 Pilot; non-QASPER)
   - Exact Arithmetic Sum: 111 + 281 + 408 + 4 = 804 unique papers.

2. Active Benchmark Run Exposure Total:                     802 unique papers
   - 111 Train papers (RQ3 Embedding)
   - 279 Dev papers with verified experimental runs (RQ1, RQ2, RQ3, or RQ4 Dev)
   - 408 Test papers with verified experimental runs (RQ4 Test)
   -   4 Curated Seed papers (RQ5 Pilot)
   - Exact Arithmetic Sum: 111 + 279 + 408 + 4 = 802 unique papers.
   - Note on Arithmetic Discrepancy: Exactly 2 Dev papers (1804.00720, 1903.07406) belong
     to the official Dev partition but had 0 text evidence in QASPER and were not run in
     RQ1–RQ4. Calculating 111 + 281 + 408 + 4 yields strictly 804, not 802. Writing
     111 + 281 + 408 + 4 = 802 was an arithmetic error that mistakenly substituted the
     281 partition count while reporting the 802 active-run total. Both calculations
     confirm 0 overlap with the 777-paper unexposed Train reservoir.

========================================================================================

                          UNEXPOSED TRAIN RESERVOIR (777 PAPERS)
────────────────────────────────────────────────────────────────────────────────────────
1. Total Unexposed Train Papers:                         777 papers (2,154 questions)
2. Question-Level Filtering:
   - Excluded strictly unanswerable consensus:           238 questions
   - Excluded float/figure/table-only evidence:          116 questions
   - Excluded empty evidence lists:                       71 questions
   - Excluded decoupled questions:                         0 questions
   - End-to-End Eligible Questions (Atomic Joint):     1,729 questions
3. Paper Breakdown by Eligible Question Count:
   - Papers with >= 2 eligible questions (Candidate Pool): 487 papers (1,503 questions)
   - Papers with == 1 eligible question:                   226 papers (  226 questions)
   - Papers with == 0 eligible questions:                    64 papers (    0 questions)
────────────────────────────────────────────────────────────────────────────────────────
4. RQ5 Main Evaluation Feasibility:
   - Target Sample Size:                                  250 papers (500 questions)
   - Available Candidate Pool:                            487 papers
   - Feasibility Margin (Reserve Surplus):               +237 papers (100% FEASIBLE)
========================================================================================
```

---

## 6. How to Use the Reusable Audit Tool (`check_experiment_overlap.py`)

The standalone audit script allows any agent or pipeline runner to verify candidate papers before taking action:

```powershell
# 1. Run deterministic self-test suite
python eval/scripts/check_experiment_overlap.py --test

# 2. Check candidate paper IDs passed directly on CLI
python eval/scripts/check_experiment_overlap.py --papers 1601.00901 1601.06068

# 3. Check an entire sample manifest before execution
python eval/scripts/check_experiment_overlap.py --manifest eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json

# 4. Generate machine-readable JSON audit output for programmatic gating
python eval/scripts/check_experiment_overlap.py --manifest eval/sample_manifest.json --json
```

**Exit Codes:**
- `0`: Verdict is `PASS_UNEXPOSED` (all queried papers have zero prior repository exposure).
- `1`: Verdict is `FAIL_EXPOSURE_DETECTED` (at least one queried paper was previously exposed in a prior experiment).
- `2`: File or arguments error.
