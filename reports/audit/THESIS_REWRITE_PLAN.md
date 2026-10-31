# Thesis Rewrite Plan (post-audit iteration)

**Scope:** `DU_AN_CNTT_TOAN_VAN.md` (master) and the matching passages of `reports/chapter5/CHAPTER5.md` (re-synced from the master), plus `eval/results/THESIS_RQ5_LLM_REPORT.md` (regenerated from §5.6).
**Status:** plan only; no thesis text has been changed in this iteration.

Section numbers refer to the current master.

**"Evidence" column:**
- `existing`: can be changed now from current artifacts.
- `E1` / `E2` / `E3` / `E4`: needs that experiment from `POST_AUDIT_EXPERIMENT_PROPOSAL.md`.

## A. Changes that need no new experiment

| # | Section(s) | Current claim / content | Change | Evidence |
|---|---|---|---|---|
| A1 | Abstract (VN/EN), §1.2.2, §3.3.5 (item 1, sub-4B rationale), §3.4 item 3, Table 3.3, Table 5.1 (Peak RAM column), Table 5.3 (Peak RAM column), §5.4.3 Pareto text, Table 5.8 RQ3 row, §5.8 item 3, §5.9 item 3, §6.1.2 RQ3, §6.2 item 5, App. E | RAM figures: RQ1/RQ3 `psutil` RSS (e.g. 659.8 MB, 1,161.7 MB), and the LLM RAM estimates in §3.3.5 (~600 MB / ~1.6 GB / ~2.5 GB, the "4.0–5.5 GB" budget breakdown) | **Remove all RAM figures and memory-efficiency arguments.** Keep latency and throughput. In §3.3.5, justify the model selection by parameter count, latency and throughput only, and say RAM was not measured. One sentence in §5.8: memory was not measured reliably and is not reported. *Pending approval checkpoint 4: whether measured RQ1/RQ3 RSS is also removed. Default: yes.* | existing |
| A2 | §4.1.3 NFR-03, §4.7.4, §1.2.2, §4.10, §6.1.1 item 4, Abstract | 0.80 threshold described with "an toàn", "ranh giới quyết định", "hạn chế ảo giác" | One uniform wording: "ngưỡng heuristic kỹ thuật 0,80 (chưa hiệu chuẩn)". Remove "an toàn". State that calibration on real questions is future work (§6.3) | existing |
| A3 | §3.3.2, §5.3.1, Table 5.2 caption, §5.9 item 2, §6.1.2 RQ2, Abstract | "8 chiến lược … dưới cùng ngân sách 1.600 tokens" | Disclose that nDCG@10, nDCG@4, Recall@20 and MRR@10 in Table 5.2 rank the full candidate list (not budget-limited); only "budget coverage" uses the 1,600-token budget. Rename the claim to "so sánh xếp hạng; ngân sách 1.600 tokens chỉ áp dụng cho chỉ số độ bao phủ" | existing (code: `evaluate_rq2_chunking.py`) |
| A4 | §3.3.4, §5.5.2–5.5.3, Table 5.5 row label "[Sản phẩm]", §5.8 item 6 | "Hybrid RRF (k = 60) [Sản phẩm]" | Rename to "Hybrid RRF (k = 60, cấu hình benchmark)". State that the benchmark BM25 (WordPiece, stopwords, corpus-wide IDF) differs from production BM25 (whitespace tokens, IDF over one document), so RQ4 does not measure the production retriever exactly | existing |
| A5 | §5.6.2 Table 5.6 + note, §5.6 analysis item 1 | Boolean F1 0.0385 / 0.0006 / 0.0349 presented like the other F1 values | Add caveat: Token F1 is not a valid correctness measure for yes/no answers (verbose answers vs "Yes"). Report Boolean accuracy if E3 runs | existing caveat; numbers from E3 |
| A6 | §5.6.2 Table 5.6 column "Kích thước tệp mô hình" | Model file sizes | Keep (it is a file size, not RAM) but drop the "cận dưới gợi ý" RAM interpretation (A1) | existing |
| A7 | §5.8 item 1 / §3.2.1 | Reservoir "777 unexposed" | Say 250 of the 777 were used by RQ5; 527 remain. Note the registry repair (E0) | existing + E0 |
| A8 | Ch6 §6.3 | Future-work list | Add: threshold calibration, RAM / process-tree measurement, a second human reviewer, external datasets (QASA, PeerQA, biomedical) with separate protocols | existing |

## B. Changes that depend on new evidence

| # | Section(s) | Current claim | If the experiment supports it | If it does not / unresolved | Evidence |
|---|---|---|---|---|---|
| B1 | §5.5.4–5.5.6, Table 5.5 (add rows or a new Table 5.5b), §5.7.2 item 3, §5.9 item 4, §6.1.2 RQ4, Abstract, §4.7.4 (RRF justification) | "Convex +0.0152 significant; RRF comparable" (benchmark BM25 only) | Add the production-faithful results (RRF-prod, Convex-prod), clearly labelled as a post-selection diagnostic on exposed Test data, plus the α sensitivity on Dev. If Convex-prod meets the switch rule: say Convex is a *candidate* improvement that needs fresh confirmation | Say the Convex gain does not carry over to production-style BM25 (or is unresolved). Keep RRF, with the theory-based justification (scale-free, untuned, local IDF) presented as engineering reasoning, not as an empirical win | E1 |
| B2 | §5.3.3 items 1 and 5, §5.3.3 parity paragraph, Table 5.8 RQ2 row, §5.7.2 item 2, §5.9 item 2, §6.1.2 RQ2, Abstract | "hierarchical 0.6880 … production +0.0306 nDCG@10; gap not decomposed" | Add Table 5.2b: evidence coverage@1600 for fixed_size / section_overlap / hierarchical under conditions U, B, B+W, dense and hybrid; explain the 0.688 → 0.505 gap with the measured decomposition. Keep the original Table 5.2 as the answer to the narrower ranking question | If coverage differences include 0: "under an equal 1,600-token context, hierarchical's advantage is not established on 47 papers"; keep it as the production choice on design grounds (headings, citations), not as proven better | E2 |
| B3 | §5.6.2 item 2 (answered-both analysis), §5.6.3, §5.6.6, §5.9 item 5, §6.1.2 RQ5, Abstract | "3b 0.3797 vs qwen 0.3002 on 244 both-answered (descriptive)" | Replace with values plus paired paper-clustered CI, the selection-effect caveat and Boolean accuracy; refusal-rate differences with CIs | Remove the "better when it answers" claim and keep only the refusal-rate explanation | E3 |
| B4 | §5.6.4 human-review paragraphs | Counts and percentages | Add Wilson intervals and the exploratory paired sign test (3b vs qwen on unsupported/contradicted); keep the "not population estimates" wording | Same, without the test if discordant pairs are too few to say anything | E3 |
| B5 | §5.6.6 / §5.9 / Ch6 model-selection conclusion | "3b chosen: beats 1b; fewest unsupported in audit; refuses often" | Strengthen or weaken the trade-off statement according to E3 (and E4). Never claim a universal winner | Cautious engineering recommendation only | E3 (+E4) |
| B6 | §3.3.6, §5.1.3, §5.7.3, §6.2 item 4, §6.3.1, README | "RQ6 not executed" | If E4 runs: add §5.6.7 "RQ6 pilot", covering only the production configuration with llama3.2:3b, retrieved vs gold context on 100 new questions. State that the full RQ6 design remains future work | Unchanged (RQ6 future work) | E4 |

## C. Claims to remove or qualify (whatever the experiments show)

1. Any phrase implying that the complete production RAG system was evaluated end to end (unless E4 runs, and then only "pilot, 1 configuration").
2. "RRF tương đương Dense": always "không khác biệt có ý nghĩa thống kê".
3. "hierarchical vượt trội dưới cùng ngân sách": qualify per A3/B2.
4. Any RAM or memory-efficiency claim (A1).
5. Any wording calling the 0.80 threshold calibrated, validated or optimal (A2).
6. Containment proxy: never called "faithfulness", and Token F1 never called "factual correctness" (already mostly done; re-scan).

## D. Synchronisation and traceability

- After the master edits, regenerate the Chapter 5 copy (`reports/chapter5/CHAPTER5.md`, with link prefix `../../`) and `eval/results/THESIS_RQ5_LLM_REPORT.md` from §5.6, as in the audit.
- Add rows for E1–E4 to `reports/chapter5/TRACEABILITY_MAP.md`.
- Update statuses in `reports/audit/THESIS_CLAIM_AUDIT.md` (S5, R4, R5, R15, R18–R24) and `EXPERIMENT_AUDIT.md`.
- Re-run the integrity scan (corruption patterns, links, table gaps) and `verify_chapter5_exhaustive.py`. The latter will need updating if A1 removes RAM values it checks: it currently asserts e.g. "1.161,7 MB" in CHAPTER5.md. Its RAM assertions will be retired in a versioned way, with the change logged.
