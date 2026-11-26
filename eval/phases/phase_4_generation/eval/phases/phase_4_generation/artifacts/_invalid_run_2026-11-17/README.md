# Invalid outputs of the Phase 4 Kaggle run of 2026-11-17 (kept for the record, not used)

- The Kaggle datasets were not attached (`cp: cannot stat .../qasper-official`, `.../peerqa`), so
  - C-RET: 0 questions (all 567 "not in the QASPER JSON"); `c_ret/` is empty.
  - PeerQA retrieved (`gemma:dense`): contexts for 5 of 70 papers only; 166 of 181 questions were
    sent an empty context and scored as refusals (`peerqa_pdf/retrieved_gemma_dense/`).
- `qwen3:4b` now resolves to the thinking-only 2507 build: `think=false` was ignored and the
  reasoning was written into the answer, cut at 256 tokens (`peerqa_pdf/gold/per_query_qwen3_4b_thinking.jsonl`).
  Replaced by `qwen3:4b-instruct-2507-q4_K_M`.
- Gemini judge: every call returned HTTP 429 (rate limit); all labels are INVALID
  (`judge_validation.json`, `peerqa_pdf/gold/judge.jsonl`).

Valid and kept in place: PeerQA gold answers of llama3.2:3b, qwen2.5:1.5b, phi4-mini, gemma3:4b.
The script now stops when the QASPER JSON or PeerQA PDFs are missing or a context is empty.
