# Phase 4: LLM evaluation (peerqa_pdf / gold)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 181 | 0.0359 | 0.851 | 0.606 | – | 0.25 | 0.68 | 84.4 |
| qwen2.5:1.5b | 181 | 0.1225 | 0.541 | 0.562 | – | 0.18 | 1.09 | 135.3 |
| phi4-mini | 181 | 0.0567 | 0.818 | 0.663 | – | 0.34 | 1.6 | 61.7 |
| qwen3:4b-instruct-2507-q4_K_M | 181 | 0.0569 | 0.779 | 0.641 | – | 0.36 | 1.82 | 59.7 |
| gemma3:4b | 181 | 0.0456 | 0.856 | 0.965 | – | 0.41 | 1.06 | 62.4 |

## Judge labels

| Model | SUPPORTED | MISSING_INFO - PARTIAL | MISSING_INFO - UNJUSTIFIED_REFUSAL | REFUSAL_VALID | UNSUPPORTED | CONTRADICTED |
|---|---|---|---|---|---|---|
| llama3.2:3b | 20 | 0 | 82 | 73 | 2 | 4 |
| qwen2.5:1.5b | 50 | 10 | 38 | 61 | 15 | 7 |
| phi4-mini | 31 | 2 | 74 | 72 | 1 | 1 |
| qwen3:4b-instruct-2507-q4_K_M | 0 | 0 | 0 | 0 | 0 | 0 |
| gemma3:4b | 21 | 4 | 83 | 72 | 0 | 1 |
