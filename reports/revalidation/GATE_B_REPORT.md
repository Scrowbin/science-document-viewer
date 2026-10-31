# Gate B Report: Revalidation Protocol and Data (before any large inference)

**Date:** 2026-10-30.

**Status:** Phase B complete except the 30-case CEC human check, which is waiting for your labels. No Phase C experiment has been run, apart from smoke tests on 2–3 papers per script, whose outputs are kept in separate `smoke_*` folders and do not inform the protocol.

**Protocol:** frozen in `eval/experiment_provenance_registry.json` under `EXP-REVALIDATION-PROTOCOL`, label "pre-Gate-B protocol freeze". The freeze covers SHA-256 hashes of the validity matrix, the configs, the shared code, all experiment scripts, the cohort files, the version-check files and the hidden CEC key.

## 1. Data acquired

| Source | What | Result | Record |
|---|---|---|---|
| arXiv | Latest and v1 PDFs of the 463 unused QASPER Train papers that have ≥ 1 retrieval-eligible question | Latest: 461 of 463 (`1612.04675` and `1908.07822` return 404, so v1 is used). v1: 463 of 463. ~750 MB, git-ignored | `eval/pdfs/train_reservoir/download_manifest.json` (SHA-256, HTTP status, pages) |
| PeerQA v1.0 (UKP Lab) | QA data zip | SHA-256 `188fa8d1…09d8`. 579 questions, 208 papers. Data license **CC BY-NC-SA 4.0** (README inside the zip; non-commercial research use) | `eval/data/peerqa/` |
| PeerQA PDFs | 110 papers with ≥ 1 answerable question that has evidence | 8 EGU PDFs downloaded automatically. 102 OpenReview PDFs saved manually in a browser, because OpenReview demands a human challenge for all automated access, its API included. All 110 open in PyMuPDF | `eval/pdfs/peerqa/download_manifest.json` (`source: manual_browser_download`) |
| GROBID | Optional 6th RQ1 extractor | **Not running** (`localhost:8070` unreachable; Docker engine and WSL2 not set up) | Will be added with `--with-grobid` if it becomes available before Phase C |

## 2. Version check (evidence must match the downloaded PDF)

**Rule:** for each paper, check how many of its evidence paragraphs appear in the extracted text, separately for each of the 5 extractors.
- A paragraph counts as found if ≥ 80% of its content words appear in the text.
- If the latest PDF falls below 70% under every extractor, v1 is tried.
- The paper is kept if any extractor reaches ≥ 70%.
- `rapidfuzz` is not installed, so token containment is the only matching criterion; the protocol allows either method.

| Set | Papers | Usable PDF | Needed v1 check | Use v1 | **Kept** | Excluded (< 70%) |
|---|---|---|---|---|---|---|
| QASPER reservoir | 463 | 463 | 44 | 16 | **435** | 28 |
| PeerQA | 110 | 110 | 0 | 0 | **107** | 3 |

The median best-extractor match rate among kept papers is 1.0. Per-extractor match rates are stored, but they were **not analysed**, because they overlap with RQ1's primary metric.

## 3. Cohorts (seed 42; registered before any scoring)

| Cohort | Role | Papers | Questions | Questions per paper | Notes |
|---|---|---|---|---|---|
| **C-INT** | Confirmation (RQ6 only; never used for tuning) | 100 | 200 | exactly 2 | 122 extractive / 49 abstractive / 29 Boolean |
| **C-RET** | Selection (RQ1–RQ4) | 335 | 567 | mean 1.69, max 6 (212 papers have 1) | All remaining kept papers |
| **C-RET-150** | Selection (RQ3) | 150 | 249 | mean 1.66 | Seeded subset of C-RET |
| **PEERQA-PDF** | Descriptive (RQ1, RQ4, RQ6) | 107 | 288 | mean 2.69, max 9 | Mostly ICLR/NeurIPS; 8 EGU geoscience papers |
| **PEERQA-TEXT** | Descriptive (RQ4, shipped text) | 73 | 148 | mean 2.03 | NLPeer (ARR, COLING, ACL), F1000 public health, EGU |

**Overlap checks:**
- **`REVAL-01` (`reports/audit/scripts/cross_rq_audit.py`): PASS.**
  - Zero paper and zero question overlap between the new cohorts and every evaluated historical cohort (RQ1–RQ5, pilot, τ labels, RQ4 Dev/Test, RQ5 primary and human-review subset).
  - C-INT and C-RET are disjoint.
  - All new QASPER papers belong to the official Train split.
- **Expected overlap (information only):** some new papers come from the never-evaluated RQ5 reserve and residual pools (C-INT: 24 reserve and 76 residual papers; C-RET: 26 and 97). Those pools were set aside when RQ5 was sampled but never evaluated (the RQ5 replacement log is empty).

**Registry:**
- `EXP-REVAL-SELECTION-CRET`, `EXP-REVAL-RQ6-CINT`, `EXP-REVAL-PEERQA-PDF` and `EXP-REVAL-PEERQA-TEXT` are registered as `REGISTERED_PLANNED`, and planned-exposure events were appended for the 435 papers.
- Append-only was verified: every earlier experiment and every earlier event is unchanged.
- **92 Train papers remain completely unused.**

`check_experiment_overlap.py`:
- Its self-test fixture `1601.00901` is now in C-RET, so it was replaced with `1601.02166`. The self-test passes.
- `1601.00901` is now correctly reported as exposed.

## 4. Sample-size and precision check

The SESOIs were fixed before any new data were seen. The figures below come from existing variance (E1, RQ2), not from new outcomes.

| RQ | Cohort | Clusters | Expected 95% CI half-width | SESOI | Adequate? |
|---|---|---|---|---|---|
| RQ1 | C-RET | 335 papers | small (paper-level recall) | 0.03 | yes |
| RQ2 | C-RET | 335 papers / 567 q | ≈ ±0.035–0.04 (binary CEC) | 0.05 | yes, but with a narrow margin; 63% of papers contribute 1 question |
| RQ3 | C-RET-150 | 150 / 249 | ≈ ±0.035 | 0.04 | yes for the stated SESOI only |
| RQ4 | C-RET | 335 / 567 | ≈ ±0.012–0.016 | 0.02 | yes |
| RQ6 | C-INT | 100 / 200 | ≈ ±0.035 | 0.05 | yes for the primary; Boolean (29 q) and the human review are descriptive only |

**Caveat for RQ2–RQ4.** C-RET has 567 questions, fewer than the ≈ 730 planned, because the reservoir mostly holds papers with 1 eligible question. Precision depends mainly on the 335 paper clusters, so the shortfall widens the RQ2 interval only slightly. If an interval straddles its SESOI, the result is reported as **inconclusive**, not as a win.

## 5. Harness validation (`eval/phases/phase_0_baseline/artifacts/revalidation/harness_validation.json`)

| Check | Result |
|---|---|
| A. New ranking code fed into E1's expansion and metrics reproduces stored E1 Dev nDCG@10 | 48 of 48 per-query values match to 4 dp |
| B. New chunking and embedding from PDFs fed into RQ2's metric reproduces stored RQ2 nDCG@10 | 21 of 21 match to 4 dp |
| C. Harness `rank('rrf_prod')` + `assemble` gives the same context as the real `DocumentRAG.hybrid_search` | 7 of 7 queries give identical contexts |
| Unit tests (`eval_common/test_revalidation.py`, `test_stats.py`) | 5 of 5 and 15 of 15 pass |
| Smoke runs | RQ1-v2, RQ2-v2, RQ3-v2 (5 models), RQ4-v2 on 3 cohorts: all run end to end. All model prefixes were logged as specified |

Fixes made during the smoke runs, before the freeze:
- **BM25 index timing.** BM25 indexes are now built once per paper and outside the timed step, as production does. Before this, query latency included building the index.
- **RQ3 latency sample.** It now uses 100 queries from all of C-RET-150, independent of `--limit`.
- **Invalid characters from `pypdf`.** `pypdf` produced lone UTF-16 surrogates on one paper. These invalid code points are now replaced with U+FFFD; no real text changes. One consequence: `pypdf`'s memory peak covers only the resumed portion of the run, the last ~328 papers.

## 6. CEC human check (pending: needs you)

- **Sheet:** `eval/phases/phase_2_chunking/artifacts/cec_human_check/CEC_CHECK_SHEET.md`. It has 30 cases from the 47 Dev papers: 5 covered and 5 not covered for each strategy, with the strategy and CEC value hidden. The key is hashed in the registry.
- **Rule, fixed in advance:** if agreement with CEC is below 80%, budgeted nDCG@10 becomes RQ2's primary metric.
- **Phase C cannot start RQ2-v2 until this is done.** RQ1 and RQ3–RQ5 do not depend on it.

## 7. Hardware and memory measurement

- **CPU:** AMD Ryzen 7 7735HS (8 cores / 16 threads), 13.69 GB usable RAM, integrated Radeon GPU.
- **CPU-only:** Ollama reports `size_vram: 0`, and `nvidia-smi` is absent.
- **Different machine:** the historical thesis numbers name a Ryzen 5 5600. New latency and memory figures are compared only with other new runs.
- **Memory definition:** peak Windows working set (RSS), sampled every 0.1 s.
  - Python processes are measured per subprocess.
  - The Ollama figure sums `ollama.exe` and its runner processes.

## 8. Phase C plan and runtime estimate (this machine, run one after another so latencies are not contaminated)

| Step | Estimate |
|---|---|
| RQ1-v2 (extraction is cached; downstream embeddings for 4 extractors on C-RET-150) | ~50 min |
| RQ2-diag (Dev 47, diagnostic) | ~10 min |
| RQ2-v2 (C-RET, 3 strategies, ~42k units at ~13 units/s) | ~1 h |
| RQ3-v2 (C-RET-150, 5 models; ModernBERT ≈ 1 h of this) | ~1.8 h |
| RQ4-v2 (C-RET from cache; PEERQA-PDF and PEERQA-TEXT) | ~45 min |
| RQ5-R (no inference) and RQ5-M (3 models × 121 generations) | ~40 min |
| Production change (retrieval mode setting + `temperature=0`) and backend tests | ~1 h |
| RQ6 on C-INT: 6 conditions × 200 generations (retrieved contexts of ~1,300 tokens make 3b slower than in RQ5); PeerQA 2 × 288 | ~5–6 h (≈ 1.4 h less if no stage changes the system) |
| **Total** | **≈ 11–12 h of compute**, mostly unattended overnight runs |

## 9. Decisions needed

1. **Approve Phase C** as frozen.
2. **CEC sheet:** label the 30 cases. The other experiments can start before you finish.
3. **GROBID:** set it up now (WSL2 + Docker; it then adds ~40 min to RQ1), or report it as not evaluated.
4. **Second annotator for RQ6:** 20 of the 40 answers, later in Phase C.
