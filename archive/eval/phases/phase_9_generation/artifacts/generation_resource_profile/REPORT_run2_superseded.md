# RQ5-M: Resource and Stability Profile of the Local LLMs

**Protocol:** `reports/revalidation/protocol/rq5_rq6.json` "RQ5-M", frozen before Gate B. Memory sampler corrected by the registered deviation `rq5m_memory_fix.json` (protocol record version 3).
**Script:** `eval/phases/phase_9_generation/scripts/rq5_resource_profile.py`. Output: `summary.json` (run 2). Run 1 (`summary_run1_invalid_ollama_memory.json`) is kept for the record; its Ollama memory figure is invalid.
**Setup:**
- Ollama 0.40.13, CPU-only (`size_vram` = 0 for every model), on this laptop (Ryzen 7 7735HS, 13.69 GB RAM).
- 60 questions: every 8th item of the frozen RQ5 manifest, RQ5 prompt with gold evidence, temperature 0, `num_predict` 256.
- Per model: unload, one cold request, then 2 warm passes over the 60 questions.

## Results

| Model (digest prefix) | Cold load (s) | Cold first answer (s) | Warm answer P50 (s) | Warm prompt eval, mean (s) | Tokens/s, mean | Ollama tree peak working set | Python peak |
|---|---|---|---|---|---|---|---|
| llama3.2:3b (`a80c4f17`) | 3.9 | 11.3 | 4.84 | 1.34 | 13.7 | **4,563 MB** | 101 MB |
| llama3.2:1b (`baf6a787`) | 2.1 | 8.7 | 4.09 | 1.27 | 21.2 | 2,142 MB | 103 MB |
| qwen2.5:0.5b (`a8b0c515`) | 0.9 | 4.6 | 3.04 | 0.46 | 60.7 | 848 MB | 103 MB |

**Memory definition:**
- Peak of the summed Windows working set of `ollama.exe` and all its child processes (the model runs in `llama-server.exe`), sampled every 0.1 s. The tray app is excluded.
- Shared pages are counted once per process, so the sum can overstate physical RAM slightly.
- The figure includes the model weights and the KV cache at Ollama's default context window. That is why 3b (a 2.0 GB download) peaks at about 4.6 GB.
- **For a 13.69 GB laptop:** 3b plus the RAG backend (Python peak ~1.3–1.5 GB in the retrieval runs) fits, with about 7 GB left for the OS and browser.

**Timing:** cold-load figures are a single measurement each; they vary between runs (run 1: 6.0 / 2.5 / 1.2 s).

## Stability (temperature 0)

| Model | Identical across the 2 warm passes | Pass 1 identical to stored RQ5 answer (descriptive) |
|---|---|---|
| llama3.2:3b | 50/60 | 46/60 |
| llama3.2:1b | 50/60 | 60/60 |
| qwen2.5:0.5b | 40/60 | 60/60 |

- **Temperature 0 is not fully deterministic here.** 10–20 of 60 answers change between two passes in the same session. The counts were exactly the same in run 1.
- **Pass 1 matches the stored RQ5 answers exactly for 1b and qwen.** So the differences arise between passes, not between machines. A plausible cause, not tested: Ollama reuses cached prompt state on the second pass, which changes floating-point order on CPU.
- **3b matches the stored answers on 46/60.** The stored run came from another machine; its Ollama version and digest weren't recorded.
- **Implications:**
  - Single-run Token F1 differences carry run-to-run noise as well as sampling noise.
  - RQ6 should keep the fixed protocol (one pass, fresh model load per condition) and report this caveat.

## Does this support the intended claim?
- **Supported:**
  - All three models run CPU-only on a 16 GB-class laptop.
  - llama3.2:3b costs about 4.6 GB of RAM and about 5 s per answer warm (13.7 tokens/s). That is usable for interactive chat, at roughly 1.6× qwen's answer time and 5× its memory.
- **Not supported:** "outputs are reproducible at temperature 0". They are only partly reproducible (67–83% identical).

## Deviations
- **Memory sampler fixed before run 2** (registered; see `rq5m_memory_fix.json`). Timing and stability code unchanged.
- Run 1 timings are valid but superseded.
