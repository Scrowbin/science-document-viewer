# FR-16 plan: fetch more context when the model says the context is not enough

**Status:** planned, **not implemented**. Default mode `strict` (today's behaviour). Implement after the combination experiment, because `query_document` is used by the experiments.

## Idea
When the model answers with the refusal sentence ("the context does not contain enough information"), the evidence may still be in the document, just ranked below the 5 sections that were sent. The feature retrieves the **next-ranked, not yet used sections** and asks again. This follows the common "corrective retrieval" practice with a sliding window over the ranking: each extra round replaces the context with new sections under the same budget, instead of growing one prompt (which would exceed `num_ctx` and slow down every round).

## Modes (one setting, `RAG_CONTEXT_RETRY`)

| Mode | Behaviour |
|---|---|
| `strict` (default) | No extra retrieval. Identical to the current system. |
| `once` | If the answer is a refusal, one more round with the next-ranked sections, then stop. At most 2 LLM calls. |
| `loop` | Repeat rounds until the model gives a non-refusal answer, no unseen sections remain, or `RAG_CONTEXT_RETRY_MAX_ROUNDS` is reached (default 3, so the loop always ends). |

## Mechanism (reuses existing code in `backend/apps/documents/services/rag_service.py`)
1. **Detect "not enough context":** the answer contains the fixed `REFUSAL_MESSAGE` that `build_answer_prompt` already tells the model to use (normalised substring match). No extra model call or classifier.
2. **Next sections:** add an optional `exclude_parent_ids: set | None = None` to `DocumentRAG.hybrid_search`. In the hierarchical branch it pre-seeds the existing `seen_parents` set, so the next-ranked parents are returned under the same limits (≤ 5 units, ≤ 1,600 tokens). With `None`, behaviour is unchanged. Non-hierarchical strategies exclude by `chunk_id` the same way.
3. **Ask again:** `build_answer_prompt(question, title, new_docs, REFUSAL_MESSAGE)` → `_generate_with_ollama`. The similarity gate (0.80) applies only to the first round, which already passed it.
4. **Result:** the first non-refusal answer is returned with its own sources and `"context_rounds": n`. If every round refuses, return the first round's refusal and sources, with `context_rounds`.
5. **Timeouts:** each round has the normal Ollama timeout; if a round times out, stop and use the existing excerpt fallback with the sources collected so far.
6. **Frontend:** when `context_rounds > 1`, the chat shows a small note: "Đã tìm thêm ngữ cảnh ở các mục khác (n vòng)".

## Costs and risks
- Each extra round adds about 30 s on CPU (`llama3.2:3b`); `loop` with 3 rounds can take about 2 minutes. Consider the elapsed-time message in the chat panel.
- Fewer refusals can mean more unsupported answers: lower-ranked sections are less relevant, and the model may stretch them.
- It only helps when the evidence is in sections ranked 6–15.

## Evaluation (required before calling it done)
On the combination experiment's generation sample (300 questions), production retrieval pipeline, compare `strict`, `once` and `loop`:
- refusal rate, and refusal rate split by whether the evidence was in the first context (as in Bảng 5.9);
- Token F1 and the containment proxy;
- answer time (p50/p95) and number of rounds;
- a small blinded human check of the answers that changed between modes (same 6-label rubric).

## Tests
- `strict`: the call path and output are unchanged (same prompt, one LLM call).
- `once`: at most two LLM calls; the second context shares no section with the first.
- `loop`: stops on acceptance, on exhausted sections and at the round limit.
- `context_rounds` is present in the response; sources belong to the round that answered.
