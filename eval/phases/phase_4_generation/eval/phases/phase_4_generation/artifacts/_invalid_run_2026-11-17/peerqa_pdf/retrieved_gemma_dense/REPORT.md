# Phase 4: LLM evaluation (peerqa_pdf / retrieved_gemma_dense)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 181 | 0.0024 | 0.983 | 0.486 | – | 0.21 | 0.78 | 80.2 |
| qwen2.5:1.5b | 181 | 0.0427 | 0.740 | 0.146 | – | 0.12 | 1.12 | 141.2 |
| phi4-mini | 181 | 0.0009 | 0.995 | 0.333 | – | 0.26 | 0.97 | 63.1 |
| qwen3:4b | 181 | 0.0548 | 0.326 | 0.075 | – | 4.41 | 5.36 | 59.0 |
| gemma3:4b | 181 | 0.0013 | 0.983 | 0.878 | – | 0.33 | 1.09 | 62.2 |
