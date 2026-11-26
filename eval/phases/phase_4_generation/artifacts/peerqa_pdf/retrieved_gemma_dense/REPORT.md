# Phase 4: LLM evaluation (peerqa_pdf / retrieved_gemma_dense)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 181 | 0.0395 | 0.823 | 0.768 | – | 1.0 | 2.53 | 71.4 |
| qwen2.5:1.5b | 181 | 0.1636 | 0.188 | 0.715 | – | 0.91 | 2.38 | 125.0 |
| phi4-mini | 181 | 0.0617 | 0.768 | 0.758 | – | 1.21 | 3.17 | 53.0 |
| qwen3:4b-instruct-2507-q4_K_M | 181 | 0.0797 | 0.586 | 0.735 | – | 1.42 | 4.97 | 55.2 |
| gemma3:4b | 181 | 0.0650 | 0.674 | 0.898 | – | 1.37 | 3.29 | 55.4 |
