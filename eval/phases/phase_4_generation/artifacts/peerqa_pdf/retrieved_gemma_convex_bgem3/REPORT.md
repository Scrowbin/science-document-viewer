# Phase 4: LLM evaluation (peerqa_pdf / retrieved_gemma_convex_bgem3)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 181 | 0.0432 | 0.801 | 0.758 | – | 1.04 | 2.14 | 71.1 |
| qwen2.5:1.5b | 181 | 0.1687 | 0.166 | 0.742 | – | 0.9 | 2.3 | 128.5 |
| phi4-mini | 181 | 0.0678 | 0.718 | 0.789 | – | 1.3 | 3.71 | 52.5 |
| qwen3:4b-instruct-2507-q4_K_M | 181 | 0.0977 | 0.547 | 0.723 | – | 1.7 | 5.37 | 53.2 |
| gemma3:4b | 181 | 0.0755 | 0.668 | 0.905 | – | 1.43 | 3.12 | 55.9 |

## Judge labels

| Model | SUPPORTED | MISSING_INFO - PARTIAL | MISSING_INFO - UNJUSTIFIED_REFUSAL | REFUSAL_VALID | UNSUPPORTED | CONTRADICTED |
|---|---|---|---|---|---|---|
| llama3.2:3b | 24 | 3 | 89 | 55 | 6 | 4 |
| qwen2.5:1.5b | 45 | 23 | 16 | 15 | 54 | 28 |
| phi4-mini | 36 | 6 | 72 | 58 | 4 | 5 |
| qwen3:4b-instruct-2507-q4_K_M | 66 | 1 | 46 | 53 | 11 | 4 |
| gemma3:4b | 39 | 13 | 74 | 47 | 4 | 4 |
