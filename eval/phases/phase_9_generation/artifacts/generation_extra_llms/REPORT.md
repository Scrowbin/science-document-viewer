# EXT-RQ5-LLM: Additional Local LLM Candidates (Selection-Stage Extension)

**Protocol:** `reports/revalidation/protocol/ext_rq5_llm.json`, registered before the run (registry `EXP-REVAL-EXT-RQ5-LLM`, protocol record version 5).
**Script:** `eval/phases/phase_9_generation/scripts/rq5ext_llm_candidates.py`.
**Outputs:**
- `summary.json`, `per_query.jsonl`, `checkpoint.jsonl`: from the registered script.
- `descriptive_answered_by_both.json`: post-hoc descriptive analysis, see below.
- `smoke_3/`: smoke test, not part of these results.

**Role:** a **selection-stage comparison** on the previously evaluated RQ5 500-question manifest. It is **not** independent confirmation, and C-INT was not used.

## Counts and conditions
- 250 papers, 500 questions × 3 models = 1,500 generations, 0 errors.
- Conditions identical to RQ5: same prompt, gold evidence, temperature 0, `num_predict` 256, Ollama default context window.
- Every model ran from a cold start (all models unloaded first), CPU-only (`size_vram` 0), on Ollama 0.40.13.
- **Model digests:**
  - llama3.2:3b `a80c4f17`
  - phi4-mini `78fad5d1`
  - qwen2.5:1.5b `65ec0654`
- **Reference:** llama3.2:3b re-run in this session. It reaches Token F1 0.2018 (stored RQ5: 0.2033), and 431/500 answers are identical to the stored ones.

## Primary: Token F1 vs llama3.2:3b (Holm m = 2, paper-cluster bootstrap B = 10,000, seed 42)

| Model | Token F1 | Diff vs 3b [95% CI] | Holm p | CI half-width (planned ~0.02; report if > 0.035) |
|---|---|---|---|---|
| llama3.2:3b (reference) | 0.202 | — | — | — |
| phi4-mini (3.8B, MIT) | 0.233 | +0.031 [+0.009, +0.053] | 0.005 | 0.022 |
| qwen2.5:1.5b (Apache-2.0) | 0.240 | +0.038 [+0.015, +0.061] | 0.003 | 0.023 |

**Both candidates pass the registered rule** (difference ≥ +0.03, CI lower bound > 0, Holm p < 0.05). Precision is as planned.

## Secondary

| Model | Refusal rate | Diff vs 3b [CI] | Containment proxy | F1 extractive / abstractive / Boolean | Boolean accuracy [Wilson 95%] |
|---|---|---|---|---|---|
| llama3.2:3b | 0.486 | — | 0.383 | 0.260 / 0.137 / 0.041 | 0.26 [0.18, 0.38] |
| phi4-mini | 0.500 | +0.014 [−0.026, +0.054] | 0.398 | 0.303 / 0.160 / 0.035 | 0.15 [0.09, 0.25] |
| qwen2.5:1.5b | 0.292 | **−0.194** [−0.244, −0.144] | 0.523 | 0.315 / 0.163 / 0.023 | 0.21 [0.13, 0.32] |

**Efficiency (this CPU, warm, one request at a time):**

| Model | Latency P50 / P95 | Tokens/s | Ollama-tree peak over 500 prompts |
|---|---|---|---|
| llama3.2:3b | 5.6 / 12.5 s | 13.5 | **8,795 MB** |
| phi4-mini | 6.0 / 16.9 s | 11.2 | **9,035 MB** |
| qwen2.5:1.5b | 4.0 / 9.5 s | 26.5 | **5,972 MB** |

**About these memory peaks:**
- They are not each model's footprint. They include the growth of Ollama's default host prompt cache over 500 distinct prompts (see RQ5-M).
- For 3b the peak is 8.8 GB here, against about 2.5 GB just after loading.
- On this 13.69 GB laptop that is a real deployment risk for long sessions.

## Descriptive, post-hoc (not part of the decision): where does each gain come from?
Questions answered by both the reference and the candidate are a selection-affected subset. These figures were computed after the run, outside the registered script.

| Comparison | Questions / papers | F1 diff [95% CI] |
|---|---|---|
| phi4-mini − 3b | 197 / 157 | **+0.084** [+0.049, +0.119] |
| qwen2.5:1.5b − 3b | 221 / 173 | −0.006 [−0.035, +0.024] |

- **phi4-mini:** refuses about as often as 3b but gives better answers when it does answer.
- **qwen2.5:1.5b:** answers more often (refusal −19 points) but its answers are no better. Refusals score 0 Token F1 on these all-answerable questions, so answering more raises F1 by construction. This is the same pattern qwen2.5:0.5b showed in RQ5. There, the human review found more unsupported or contradicted answers for qwen (7/20, against 1/20 for 3b).
- No human faithfulness review exists for either candidate.

## Decision
- **Both candidates qualify, under the registered rule, as an extra RQ6 condition.** Neither replaces the production default.
- **The registered rule does not say what happens when both pass.** The script's `rq6_extra_condition: "phi4-mini"` field just takes the first eligible model in list order. It is **not** a registered tie-break and should not be read as a decision.
- **What goes into RQ6 is for the user to decide.** Options: no extra condition, phi4-mini, qwen2.5:1.5b, or both (+200 generations each on C-INT). Whatever is chosen has to be registered as an RQ6 amendment before RQ6 runs.

## Does this support the claim?
- **Supported, at selection stage only:** on gold evidence, two other ≤ 4B open-licence models score higher Token F1 than llama3.2:3b.
- **Not supported:** that either model is a better or more faithful assistant. qwen2.5:1.5b's gain comes from refusing less, not from better answers. phi4-mini's gain looks like answer quality, but only lexically, and Boolean accuracy did not improve.
- **Not independent confirmation:** this manifest was used before.

## Deviations
- None from the protocol.
- `descriptive_answered_by_both.json` is an extra post-hoc analysis, labelled as such.
