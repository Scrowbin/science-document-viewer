# Phase 4: LLM evaluation (peerqa_pdf / retrieved_gemma_convex)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 181 | 0.0314 | 0.862 | 0.772 | – | 1.02 | 2.04 | 71.9 |
| qwen2.5:1.5b | 181 | 0.1610 | 0.193 | 0.755 | – | 0.9 | 2.41 | 127.2 |
| phi4-mini | 181 | 0.0682 | 0.735 | 0.802 | – | 1.24 | 3.52 | 54.3 |
| qwen3:4b-instruct-2507-q4_K_M | 181 | 0.0824 | 0.602 | 0.753 | – | 1.43 | 5.13 | 55.9 |
| gemma3:4b | 181 | 0.0760 | 0.680 | 0.930 | – | 1.39 | 3.68 | 57.5 |
