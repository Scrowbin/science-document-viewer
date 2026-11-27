# Phase 4: LLM evaluation (c_ret / retrieved_e5_convex)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 567 | 0.1498 | 0.443 | 0.882 | 34/86 | 1.1 | 2.56 | 71.0 |
| qwen2.5:1.5b | 567 | 0.2092 | 0.092 | 0.861 | 39/86 | 0.7 | 2.04 | 124.7 |
| phi4-mini | 567 | 0.1763 | 0.522 | 0.896 | 20/86 | 1.23 | 3.38 | 54.0 |
| qwen3:4b-instruct-2507-q4_K_M | 567 | 0.1875 | 0.275 | 0.841 | 40/86 | 1.9 | 5.01 | 53.3 |
| gemma3:4b | 567 | 0.1134 | 0.617 | 0.937 | 21/86 | 1.31 | 3.34 | 55.8 |

## Judge labels

| Model | SUPPORTED | MISSING_INFO - PARTIAL | MISSING_INFO - UNJUSTIFIED_REFUSAL | REFUSAL_VALID | UNSUPPORTED | CONTRADICTED |
|---|---|---|---|---|---|---|
| llama3.2:3b | 228 | 45 | 181 | 72 | 23 | 18 |
| qwen2.5:1.5b | 279 | 102 | 30 | 31 | 74 | 51 |
| phi4-mini | 219 | 25 | 220 | 76 | 11 | 16 |
| qwen3:4b-instruct-2507-q4_K_M | 347 | 19 | 87 | 70 | 31 | 13 |
| gemma3:4b | 169 | 27 | 275 | 75 | 13 | 8 |
