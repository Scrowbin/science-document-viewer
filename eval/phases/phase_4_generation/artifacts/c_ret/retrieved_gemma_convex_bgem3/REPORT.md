# Phase 4: LLM evaluation (c_ret / retrieved_gemma_convex_bgem3)

| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |
|---|---|---|---|---|---|---|---|---|
| llama3.2:3b | 567 | 0.1604 | 0.397 | 0.874 | 36/86 | 1.15 | 3.12 | 62.5 |
| qwen2.5:1.5b | 567 | 0.2187 | 0.092 | 0.854 | 42/86 | 0.7 | 2.28 | 121.5 |
| phi4-mini | 567 | 0.1743 | 0.524 | 0.897 | 23/86 | 1.28 | 3.87 | 46.9 |
| qwen3:4b-instruct-2507-q4_K_M | 567 | 0.1887 | 0.250 | 0.841 | 39/86 | 2.19 | 5.55 | 46.4 |
| gemma3:4b | 567 | 0.1137 | 0.614 | 0.939 | 16/86 | 1.35 | 3.42 | 51.7 |
