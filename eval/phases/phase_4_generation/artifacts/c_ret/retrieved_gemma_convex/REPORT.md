# Phase 4: LLM evaluation (c_ret / retrieved_gemma_convex)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 567 | 0.1607 | 0.402 | 0.880 | 36/86 | 1.06 | 2.58 | 72.5 |
| qwen2.5:1.5b | 567 | 0.2139 | 0.099 | 0.865 | 43/86 | 0.69 | 1.92 | 129.5 |
| phi4-mini | 567 | 0.1746 | 0.510 | 0.894 | 20/86 | 1.2 | 3.27 | 55.0 |
| qwen3:4b-instruct-2507-q4_K_M | 567 | 0.1908 | 0.249 | 0.843 | 38/86 | 2.08 | 4.79 | 54.3 |
| gemma3:4b | 567 | 0.1125 | 0.630 | 0.944 | 17/86 | 1.28 | 3.14 | 58.0 |

## Judge labels

| Model | SUPPORTED | MISSING_INFO - PARTIAL | MISSING_INFO - UNJUSTIFIED_REFUSAL | REFUSAL_VALID | UNSUPPORTED | CONTRADICTED |
|---|---|---|---|---|---|---|
| llama3.2:3b | 245 | 44 | 162 | 68 | 32 | 16 |
| qwen2.5:1.5b | 288 | 93 | 31 | 29 | 75 | 51 |
| phi4-mini | 216 | 30 | 216 | 73 | 19 | 13 |
| qwen3:4b-instruct-2507-q4_K_M | 356 | 21 | 77 | 60 | 34 | 19 |
| gemma3:4b | 164 | 30 | 285 | 71 | 9 | 8 |
