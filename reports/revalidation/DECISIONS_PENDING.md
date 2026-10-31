# Revalidation: Status and Decisions Needed (2026-10-30)

## Context
This program re-checks the thesis research questions under a protocol frozen before any results were seen.
- **Cohorts** (all unused QASPER Train papers):
  - C-RET (335 papers / 567 questions): **selection**. Choose each component.
  - C-INT (100 / 200): **confirmation**. Touched only once, by RQ6, the end-to-end test of the final system.
  - PeerQA: external check, descriptive only.
- **Method:** each stage varies one component and keeps the others at the production setting. A change is adopted only if a rule written before the run fires: gain ≥ a set minimum, with the 95% interval above 0 (bootstrap over papers).
- **Extensions:** the extra candidates from the candidate audit were registered separately before they ran, and they never touch C-INT.
- **Done:** every run that didn't need you. **Nothing was committed, and no thesis chapter was edited.**

## Results so far

| Stage | Result | Production impact |
|---|---|---|
| RQ1 extraction (5 tools) | Keep `pymupdf_layout`; no challenger beats it | none |
| RQ1 add-on: GROBID | Evidence recall the same. Downstream context coverage +0.084 [+0.040, +0.130] (secondary): probably because GROBID drops the reference list | none (lead, see decision 5) |
| RQ3 embedding (5 models) | Keep e5-small-v2. ModernBERT +0.010 [−0.024, +0.044] at 3.7× latency; MiniLM significantly worse | none |
| RQ3 extension: SPECTER2 | −0.173 [−0.219, −0.128], 2.8× slower | none |
| RQ4 fusion (7 arms, C-RET) | **Dense wins.** Production RRF −0.013 [−0.042, +0.016]; no hybrid reaches +0.02 | **switch RRF → dense** (decision 3) |
| RQ4 on PeerQA (descriptive) | The opposite: fixed hybrids beat dense by about +0.04 (CI > 0) | caveat for the thesis |
| RQ4 extension: reranking | MiniLM +0.012 [−0.018, +0.041] but P95 +1.4 s; BGE −0.090 | none |
| RQ5 reanalysis | Boolean accuracy 3b 0.25, 1b 0.01, qwen0.5b 0.18; much of qwen's F1 comes from refusing less | reporting fix |
| RQ5 resources | Ollama memory grows with use (prompt cache): 3b 2.5 GB fresh → 8.8 GB after 500 prompts. Temperature 0 isn't fully reproducible (67–83% identical answers across passes) | deployment risk (decision 3) |
| RQ5 extension: extra LLMs | Both pass: phi4-mini +0.031 [+0.009, +0.053], qwen2.5:1.5b +0.038 [+0.015, +0.061] vs 3b | RQ6 condition (decision 2) |

Details: `reports/revalidation/EXECUTION_LOG.md` and each experiment's `REPORT.md`.

## Decisions needed (in the order they unblock work)

### 1. Label the 30 CEC cases (blocks RQ2 and RQ6)
- **What:** open `eval/phases/phase_2_chunking/artifacts/cec_human_check/CEC_CHECK_SHEET.md`, read each case, and mark whether the context lets a reader answer the question. About 20 minutes. Don't open the key file.
- **Why:** CEC (context evidence coverage) is RQ2's primary metric. If your labels agree with it on fewer than 80% of cases, RQ2 falls back to nDCG@10, as fixed in advance.
- **Unblocks:** the RQ2 chunking comparison and the children-only extension. RQ6 waits on RQ2 because chunking is part of the production config.

### 2. Which extra LLM goes into RQ6
Both candidates passed the rule, which has no tie-break.

| Option | Cost | Note |
|---|---|---|
| **phi4-mini (recommended)** | +200 generations | Gain comes from better answers: +0.084 on questions both models answered. Refuses as often as 3b |
| qwen2.5:1.5b | +200 generations | Gain comes from refusing less (−19 points); answers are no better (−0.006). Same pattern as qwen0.5b, which hallucinated more in the human review |
| both | +400 | |
| none | — | RQ6 stays as originally frozen |

Neither model can replace llama3.2:3b as the default: neither has a human faithfulness review. The choice gets registered before RQ6.

### 3. Production changes before the RQ6 config is frozen

| Change | Recommendation | Why |
|---|---|---|
| Retrieval RRF → dense (keep `rrf_legacy` selectable) | **Yes** | Rule fired on C-RET. PeerQA disagrees, but it was declared descriptive in advance |
| `temperature=0` in `_generate_with_ollama` | **Yes** | Production currently sets none; RQ6 was designed at temperature 0 |
| Bound Ollama memory growth (e.g. a periodic `keep_alive` unload or restart) | Optional; at least document it | 3b can grow from 2.5 GB to 9 GB on a 13.7 GB laptop |

After you approve, I implement the changes, run the backend tests (≥ 51 plus new mode tests), hash the RQ6 config, and confirm C-INT is still unexposed.

### 4. Second reviewer for RQ6
- **Ask:** can a group member blindly label 20 of the 40 RQ6 answers?
- **If not:** the review is reported as single-reviewer, with that limitation stated.

### 5. Optional follow-up: GROBID's gain without GROBID
- **What:** test whether simply removing the References section from `pymupdf_layout` output reproduces GROBID's +0.084 coverage gain, without GROBID's ~3.5 GB container.
- **How:** it would be a new extension on C-RET, registered before it runs.
- **Recommendation:** worth doing. It is cheap and could be a real production improvement.
- **Status:** not run, because it was suggested by results.
- **Update 2026-10-31 (approved, after RQ6):** the app shows the same problem. Asked "What problem does this paper solve?" on the RAG paper, the system retrieved two reference-list passages and no abstract or introduction. That answer was also the fallback text (Ollama returned nothing, probably timing out while stage 1 used the CPU), so the LLM was not at fault. The planned post-RQ6 change has three parts:
  1. **Indexing:** drop References / Bibliography / Acknowledgments sections, and chunks that are mostly citation lines. Re-index once.
  2. **Broad questions** ("what is this paper about / what problem / contribution"): always include the abstract and the first paragraph of the introduction. Alternatively, route these questions to the summary path.
  3. **Measure once, paired old vs new,** on the same RQ6 questions. Report it as a post-evaluation improvement and register it before it runs.
- **Also check:** how often the experiment questions retrieve reference passages at all. If rarely, there is a gap between the specific questions we tested and the broad questions real users ask. State it as a limitation.
- **Not chosen:** sending the whole paper to the LLM. It is 8–15k tokens against Ollama's default 2–4k input limit, would take minutes per question on this CPU, and small models get worse with long inputs.

- **Update 2026-10-31 (decision: option A, after RQ6):** GROBID's downstream gain on C-RET-150 is significant: CEC@0.5 +0.084 [+0.040, +0.130] and nDCG@10 +0.059 [+0.023, +0.094]. That is larger than any combination in stage 1. It is not adopted now, for four reasons:
  1. it was registered as an add-on "not eligible for adoption", and RQ1's primary metric (evidence recall) shows no difference;
  2. QASPER's texts come from S2ORC, which parsed the PDFs with GROBID, so GROBID's paragraphs likely line up with the gold evidence and inflate CEC and nDCG (not yet measured);
  3. part of the gain is probably the dropped reference list;
  4. it needs a 4 GB Docker container on top of Ollama, and the app's GROBID path differs from the experiment's.
- **Planned post-RQ6 test:** compare three extractions on **answer quality** (Token F1 + human review), not on CEC or nDCG:
  - pymupdf_layout;
  - pymupdf_layout + reference stripping;
  - GROBID.

  Register it before it runs. Report it as a post-evaluation finding.

### 6. Post-RQ6 efficiency checks (approved 2026-10-31; not selection, run after RQ6)
1. **e5-small-v2 in ONNX INT8:**
   - parity against the current PyTorch FP32 e5: cosine similarity of the vectors, and identical top-k / nDCG@10 on C-RET;
   - indexing speed (chunks/s) and query latency on this laptop.

   It is the same model, so it is the most likely real-world speed gain. Adopt only if parity holds.
2. **ModernBERT-embed with `max_seq_length = 512`:**
   - re-measure peak memory, indexing speed and query latency;
   - confirm nDCG@10 is unchanged on C-RET-150 (our chunks are ≤ 400 tokens, so it should be).

   In stage 1 it peaked at 13.8 GB (2.2 GB in RQ3-v2) and took ~8.5 h. This decides whether "ModernBERT is too expensive" is true in general or only a configuration artefact (it accepts up to 8,192 tokens). Either answer goes in the thesis.

## What happens next
- After decisions 1–3: RQ2, then the production change, then RQ6 (one run on C-INT), then human review.
- After that: the consolidated report with thesis recommendations. No chapter edits.
