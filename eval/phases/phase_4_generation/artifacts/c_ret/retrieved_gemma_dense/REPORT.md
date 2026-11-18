# Phase 4: LLM evaluation (c_ret / retrieved_gemma_dense)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 567 | 0.1530 | 0.436 | 0.866 | 29/86 | 1.06 | 3.08 | 69.5 |
| qwen2.5:1.5b | 567 | 0.2178 | 0.099 | 0.847 | 40/86 | 0.69 | 2.05 | 128.7 |
| phi4-mini | 567 | 0.1704 | 0.531 | 0.887 | 17/86 | 1.19 | 3.14 | 55.3 |
| qwen3:4b-instruct-2507-q4_K_M | 567 | 0.1849 | 0.258 | 0.833 | 37/86 | 2.03 | 4.94 | 55.3 |
| gemma3:4b | 567 | 0.1049 | 0.644 | 0.947 | 13/86 | 1.28 | 3.15 | 58.5 |
