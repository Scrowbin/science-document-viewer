# Phase 4: LLM evaluation (peerqa_pdf / retrieved_e5_convex)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 181 | 0.0354 | 0.851 | 0.793 | – | 1.06 | 2.29 | 64.8 |
| qwen2.5:1.5b | 181 | 0.1582 | 0.182 | 0.726 | – | 0.85 | 2.4 | 120.7 |
| phi4-mini | 181 | 0.0662 | 0.768 | 0.806 | – | 1.3 | 3.65 | 48.0 |
| qwen3:4b-instruct-2507-q4_K_M | 181 | 0.0823 | 0.597 | 0.747 | – | 1.52 | 5.15 | 50.3 |
| gemma3:4b | 181 | 0.0615 | 0.735 | 0.920 | – | 1.41 | 2.96 | 51.9 |

## Judge labels

| Model | SUPPORTED | MISSING_INFO - PARTIAL | MISSING_INFO - UNJUSTIFIED_REFUSAL | REFUSAL_VALID | UNSUPPORTED | CONTRADICTED |
|---|---|---|---|---|---|---|
| llama3.2:3b | 21 | 2 | 92 | 62 | 2 | 2 |
| qwen2.5:1.5b | 39 | 11 | 19 | 15 | 63 | 34 |
| phi4-mini | 32 | 4 | 76 | 63 | 5 | 1 |
| qwen3:4b-instruct-2507-q4_K_M | 59 | 1 | 48 | 60 | 9 | 4 |
| gemma3:4b | 34 | 9 | 73 | 60 | 2 | 3 |
