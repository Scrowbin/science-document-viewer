# Phase 4: LLM evaluation (c_ret / gold)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 567 | 0.1963 | 0.459 | 0.762 | 24/86 | 0.4 | 1.78 | 72.7 |
| qwen2.5:1.5b | 567 | 0.2501 | 0.277 | 0.743 | 23/86 | 0.26 | 1.1 | 130.9 |
| phi4-mini | 567 | 0.2384 | 0.487 | 0.789 | 26/86 | 0.45 | 2.21 | 54.4 |
| qwen3:4b-instruct-2507-q4_K_M | 567 | 0.2381 | 0.367 | 0.755 | 38/86 | 0.58 | 3.22 | 56.0 |
| gemma3:4b | 567 | 0.1178 | 0.753 | 0.953 | 0/86 | 0.48 | 1.52 | 59.2 |

## Judge labels

| Model | SUPPORTED | MISSING_INFO - PARTIAL | MISSING_INFO - UNJUSTIFIED_REFUSAL | REFUSAL_VALID | UNSUPPORTED | CONTRADICTED |
|---|---|---|---|---|---|---|
| llama3.2:3b | 234 | 36 | 167 | 94 | 22 | 14 |
| qwen2.5:1.5b | 264 | 68 | 90 | 69 | 44 | 32 |
| phi4-mini | 248 | 24 | 174 | 101 | 14 | 6 |
| qwen3:4b-instruct-2507-q4_K_M | 309 | 23 | 111 | 97 | 19 | 8 |
| gemma3:4b | 112 | 26 | 326 | 100 | 2 | 1 |
