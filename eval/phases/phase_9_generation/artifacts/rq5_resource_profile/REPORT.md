# RQ5-M: Resource and Stability Profile of the Local LLMs

**Protocol:** `reports/revalidation/protocol/rq5_rq6.json` "RQ5-M", frozen before Gate B. Two registered deviations:
- `rq5m_memory_fix.json`: the sampler now covers the whole Ollama process tree.
- `rq5m_unload_fix.json`: every model is unloaded before each measurement. Its stated cause was wrong; see `rq5m_unload_fix_correction.json`.

**Script:** `eval/phases/phase_9_generation/scripts/rq5_resource_profile.py`.
**Outputs:**
- `summary.json` (= `summary_run3.json`, the reported run).
- `memory_diagnostics.json` (extra diagnostics outside the frozen script).
- Earlier runs, kept for the record: `summary_run1_invalid_ollama_memory.json`, `summary_run2_contaminated_memory.json` (name kept; its memory figures turned out valid, see below), `REPORT_run2_superseded.md`.

**Setup:**
- Ollama 0.40.13, CPU-only (`size_vram` = 0 for every model), on this laptop (Ryzen 7 7735HS, 13.69 GB RAM).
- 60 questions: every 8th item of the frozen RQ5 manifest, RQ5 prompt with gold evidence, temperature 0, `num_predict` 256.
- Per model: unload all models, one cold request, then 2 warm passes over the 60 questions (121 requests in total).

## Speed (run 3)

| Model (digest prefix) | Cold load (s) | Cold first answer (s) | Warm answer P50 (s) | Warm prompt eval, mean (s) | Tokens/s, mean |
|---|---|---|---|---|---|
| llama3.2:3b (`a80c4f17`) | 2.4 | 10.0 | 4.84 | 1.34 | 13.5 |
| llama3.2:1b (`baf6a787`) | 2.1 | 8.2 | 3.78 | 0.87 | 21.2 |
| qwen2.5:0.5b (`a8b0c515`) | 1.1 | 4.7 | 2.96 | 0.42 | 61.0 |

Cold-load times are single measurements and vary between runs (3b: 6.0 / 3.9 / 2.4 s in runs 1–3).

## Memory

| Model | Model size (`/api/ps`, context 4,096) | Ollama tree after load + 3 requests (diagnostic) | **Ollama tree peak over 121 requests (run 3)** | Python peak |
|---|---|---|---|---|
| llama3.2:3b | 2,449 MB | 2,552 MB | **4,872 MB** | 103 MB |
| llama3.2:1b | 1,453 MB | 1,555 MB | **2,222 MB** | 103 MB |
| qwen2.5:0.5b | 464 MB | 572 MB | **849 MB** | 103 MB |

- **Definition:** summed Windows working set of `ollama.exe` and all its child processes (the model runs in `llama-server.exe`), sampled every 0.1 s. The tray app is excluded.
- **Why the peak keeps growing:**
  - Ollama starts `llama-server` without `--cache-ram`, so llama.cpp's default **host-RAM prompt cache of up to 8,192 MiB** applies.
  - Each new prompt adds about 40 MB to the runner's private memory. For 3b: 2,497 MB after 1 request, 2,903 MB after 11, 3,632 MB after 30.
  - So memory depends on how many distinct prompts the session has served, and it is capped only at about model size + 8 GB.
- **Practical consequence for a 13.69 GB laptop:**
  - A fresh 3b session needs about 2.5 GB.
  - A long session can grow far beyond that: 4.9 GB after 121 prompts here, and up to about 10.5 GB at the cache cap.
  - Production could bound this, but Ollama 0.40 does not appear to expose `--cache-ram` to users; not verified. Restarting or unloading the model (`keep_alive`) also resets it.
  - This is a deployment recommendation, not a protocol change.
- **Correction to deviation 2:** it blamed other resident models for the run-2 peaks. Run 3, with every model unloaded first, gives nearly the same figures (run 2: 4,563 / 2,142 / 848 MB), so that explanation was wrong. The unload step stays because it guarantees a cold start.

## Stability (temperature 0; identical in runs 1–3)

| Model | Identical across the 2 warm passes | Pass 1 identical to stored RQ5 answer (descriptive) |
|---|---|---|
| llama3.2:3b | 50/60 | 46/60 |
| llama3.2:1b | 50/60 | 60/60 |
| qwen2.5:0.5b | 40/60 | 60/60 |

- **10–20 of 60 answers change between the two passes**, with exactly the same counts in all three runs.
- **Pass 1 matches the stored RQ5 answers exactly for 1b and qwen.** So the change comes from the second pass, not from the machine.
- **Likely mechanism, consistent with the prompt cache above but not tested directly:** on pass 2 the server reuses cached prompt state, which changes the floating-point computation path on CPU.
- **Implication for RQ6:** keep the frozen design (one pass per condition, fresh model load), and report this caveat.

## Does this support the intended claim?
- **Supported:** all three models run CPU-only on a 16 GB-class laptop. llama3.2:3b answers in about 5 s warm (13.5 tokens/s) and starts at about 2.5 GB of memory.
- **Qualified:** "the 3b model needs about 2.5 GB" is true only at the start of a session. Ollama's default prompt cache lets memory grow with use (4.9 GB after 121 prompts).
- **Not supported:** "outputs are reproducible at temperature 0". In these runs 67–83% of answers were identical between passes.

## Deviations
- Both deviations are registered (protocol record versions 3 and 4); the correction is recorded.
- The extra memory diagnostics were run outside the frozen script. They are descriptive only and don't replace any frozen output.
