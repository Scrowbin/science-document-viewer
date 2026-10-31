# Project Audit Summary (2026-10-29)

Independent audit of `C:\DACNTT`: Zotero-style document manager with a local RAG assistant, the RQ1–RQ6 evaluation, and the Vietnamese thesis `DU_AN_CNTT_TOAN_VAN.md`.

Detail is in three companion files:
- [`THESIS_CLAIM_AUDIT.md`](THESIS_CLAIM_AUDIT.md): claim-by-claim evidence.
- [`EXPERIMENT_AUDIT.md`](EXPERIMENT_AUDIT.md): per-RQ checks.
- [`CLEANUP_LOG.md`](CLEANUP_LOG.md): file removals and moves.

## 1. Actual project state

- **Application (implemented):**
  - React 19 / Vite three-column UI, PDF.js reader with highlights and sticky notes, collections and tags, 22 metadata fields.
  - Django 5 + DRF backend with JWT; 15 models.
  - Upload pipeline: local PDF metadata heuristic → background indexing (PyMuPDF sections → `hierarchical` chunks → `intfloat/e5-small-v2` → embedded Qdrant with a vectorless parent collection).
  - Chat: hybrid dense + BM25 with RRF k=60 → parent expansion within a 1,600-token budget → refuse if max cosine < 0.80 → Ollama `llama3.2:3b`, with a snippet fallback. Summarize samples 5 chunks.
  - Sharing is enforced by the API only; there is no sharing UI.
- **Experiments:**
  - RQ1–RQ5 executed, each component evaluated in isolation.
  - RQ5 uses gold evidence as context, not retrieved context.
  - RQ6 (end-to-end) not executed.
- **Authoritative artifacts:** listed per RQ in `EXPERIMENT_AUDIT.md`; the thesis's Table 5.0 now lists RQ1–RQ5.

## 2. Major findings

1. **RQ5 human-review labels were attributed to the wrong models.**
   - The signed review sheet orders answers differently from the blind mapping, and the analysis joined labels on the blind label. 26 of 45 distinguishable answers moved.
   - I re-attributed them by exact answer-text matching: 60/60 matched, 0 unresolved. Two independent checks agree: a separate parser of the signed sheet, and agreement with the refusal detector.
   - Corrected (3b / 1b / qwen): SUPPORTED 10 / 7 / 10; unsupported or contradicted 1 / 3 / 7; unjustified refusals 3 / 6 / 0.
   - The claim "3b has the highest SUPPORTED rate" no longer holds. 3b still has the fewest ungrounded answers.
2. **The thesis described the methodology incorrectly in several places:**
   - RQ5 context was gold evidence, not retrieved context.
   - RQ3 and RQ4 used QASPER-provided text, not `pymupdf_layout`.
   - RQ2 `section_token` used 400 tokens, not 250.
   - The τ* = 0.55 "out-of-sample" figures were combined-set figures; on the 34 fresh pairs precision is 58.3%.
   - The production-parity latencies were wrong.
   - The τ = 0.30 sensitivity "fully preserved" claim was false.
3. **Overclaims were toned down:**
   - `pymupdf_layout` is "optimal/fastest" (actually it is slower and statistically tied; chosen because it recovers headings).
   - The 0.80 threshold "eliminates hallucination" (actually uncalibrated).
   - `hierarchical` +0.1225 (partly due to parent-section scoring).
   - RRF "equivalent" to dense (actually not significantly different).
   - Unmeasured LLM RAM figures were removed.
4. **Application defects fixed:**
   - Shared users got 403 on chat, summarize and annotations.
   - Notes and related links did not check document access.
   - Deleting a duplicated document deleted the original's PDF.
   - The chat panel showed fabricated "Attention Is All You Need" answers when the backend failed.
   - `.env.example` overrode the embedding model with MiniLM.
5. **Document corruption fixed:** the master thesis had about 40 corrupted LaTeX fragments, broken tables and absolute `file:///` links. Supporting docs (README, ARCHITECTURE, SETUP, eval/README, AGENTS) were out of date.

## 3. Corrections made

- **RQ5 correction workflow:** `eval/phases/phase_9_generation/scripts/remap_human_labels_by_answer.py` plus outputs in `human_faithfulness_review/correction/`, including a corrected report and a record-level validation report. The changelog and registry got append-only entries. Original files are untouched.
- **Code:**
  - `backend/apps/documents/permissions.py` and `views.py`, with 9 new tests in `apps/documents/tests.py`.
  - `frontend/src/api/ragApi.ts` and `AiChatPanel.tsx`.
  - `backend/.env.example`, `SETUP.md`, and the `chunkers.py` docstring.
- **Thesis:** `DU_AN_CNTT_TOAN_VAN.md` repaired and reconciled. `reports/chapter5/CHAPTER5.md` re-synced from it. `eval/results/THESIS_RQ5_LLM_REPORT.md` regenerated from §5.6. `TRACEABILITY_MAP.md` extended with RQ4/RQ5.
- **Docs:** README (RQ table with status), ARCHITECTURE (runtime sections and a historical-design notice), `eval/README.md` status rows, a status note in `thesis_system_specification.md`, and `AGENTS.md`.
- **Cleanup:** 42 tracked files removed and 1 notebook moved; see `CLEANUP_LOG.md`.

## 4. Verification

| Check | Result | How |
|---|---|---|
| `manage.py check` | **Passed** | 0 issues |
| Backend tests | **Passed**: 51/51 (190 s) | `manage.py test --noinput apps.documents.tests apps.users.tests`. The 9 new tests failed before the fixes (8 failures; the 9th already passed) and pass after |
| Frontend | **Passed** | `npm run lint` (exit 0) and `npm run build` (exit 0); there is no frontend test runner, so no component test |
| RQ5 remap | **Passed**: 60/60 VALID, 0 unresolved | New script; cross-checked with an independent Markdown parser and against detector refusals |
| RQ5 automated numbers | **Reproduced** | Recomputed F1, refusals, containment, Δ and t from `detailed_records` |
| RQ1–RQ4 headline numbers | **Matched** | Read canonical JSON fields directly; Holm adjustments recomputed by hand (RQ1, RQ2, RQ3, RQ4) |
| RQ3 corpus composition | **Recomputed** | From the split files and the official QASPER split JSON |
| `verify_chapter5_exhaustive.py` | **Passed** 109/109 | Covers RQ1–RQ3 only; regenerated figures and CSVs were byte-identical |
| `check_experiment_overlap.py` on the RQ5 manifest | **PASS_UNEXPOSED** | Registry still parses after the appended corrections |
| `validate_human_review_package.py` | **Passed** 13/13 | It rewrote a timestamp in a frozen manifest; reverted |
| Thesis integrity scan | **Passed** | 0 corruption patterns; 0 missing relative links or images; 0 blank-line table gaps (thesis, CHAPTER5, RQ5 report, README, ARCHITECTURE, TRACEABILITY_MAP) |
| RQ6 status | **Consistent** | Every RQ6 mention says "not executed / future work" |
| Not attempted | — | Re-running any benchmark or LLM inference (not needed: every number traced to stored outputs); live smoke test against Ollama; GROBID path |

## 5. Remaining issues and decisions for the author

1. **RQ4 Convex vs production RRF:** Convex is significantly better on the benchmark but is not implemented in production. Either implement it, or keep the current justification (stated in the thesis).
2. **RQ2 parity gap:** production `hierarchical` reaches nDCG@10 0.5049 vs 0.6880 in RQ2. The cause has not been decomposed; a small ablation (windowing on or off, dense vs hybrid) would settle it.
3. **The refusal threshold 0.80 is uncalibrated.** A small labelled set of on-topic and off-topic questions would allow reporting false-refusal rates.
4. **Human faithfulness audit:** one reviewer, 20 answers per model. A second reviewer would allow an agreement statistic.
5. **RQ5 memory:** Ollama RSS was not captured. Re-measuring needs a short run, not the full benchmark.
6. **Proposed cleanup items** (not removed): see `CLEANUP_LOG.md`. Includes a licensing check of a book PDF in `sample_documents/`.
7. **Not fixed (out of scope):** frontend demo fallbacks (mock documents, demo login accounts), the dead `localhost:8001` webhook, and the unused `LLM_PROVIDER` setting. These are documented in thesis §4.9.

## 6. Readiness

After these corrections, the thesis accurately describes the implemented system and the experiments actually run. RQ1–RQ5 results are traceable to artifacts and internally consistent, and the limitations are stated. The project is in a defensible state for submission, provided the author reviews the rewritten RQ5 conclusion (§5.6.6) and the items in Section 5. All changes are uncommitted in the working tree.
