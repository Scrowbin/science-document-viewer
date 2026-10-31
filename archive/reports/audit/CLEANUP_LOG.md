# Cleanup Log (2026-10-29)

Level: aggressive, as chosen by the user, but limited to files with no reproducibility or provenance value. Before deleting anything I:
- searched references with `git grep` across code, tests, scripts, docs, config, `.vscode` and `pyrightconfig`;
- checked for dynamic paths (for example `xml_store`);
- confirmed that a complete replacement exists, or that the file has no value.

All removals are plain working-tree deletions. **Nothing was staged or committed.**

## Removed

| Path | Why it was safe to remove | References updated |
|---|---|---|
| `backend/apps/documents/services/tmp/` (`exp.py`, `main.py`, `rag.py`) | Tracked scratch prototypes; imported nowhere | none needed (`**/tmp` stays excluded in IDE configs) |
| `test.py` (root) | GROBID/langchain experiment with `/home/oracle/...` paths; not runnable here | removed from `.vscode/settings.json` and `pyrightconfig.json` excludes |
| `rag_exp/` (4 files) | Early chunking/eval prototype, superseded by `backend/scripts/evaluate_rq2_chunking.py`; no results | IDE excludes updated |
| `xml_store/*` (6 generated GROBID TEI/TXT outputs) | GROBID is off (`USE_GROBID` undefined); the code recreates the directory with `mkdir(exist_ok=True)`. `.gitkeep` kept | — |
| `extras/app_db_v2.sql` | Hand-written old schema, superseded by Django migrations | — |
| `docs/DU_AN_CNTT_TOAN_VAN.md` | Byte-identical copy of the master thesis (now stale) | none referenced it |
| `docs/CHAPTER4_DRAFT.md`, `docs/CHAPTER6_DRAFT.md` | Each differed from the master by one line; superseded by `DU_AN_CNTT_TOAN_VAN.md` | historical mentions in `DEC03_FINAL_EVALUATION_PROTOCOL.md`, `PROTOCOL_AUDIT_CHANGELOG.md` and `reports/chapter5/AUDIT_DISCREPANCIES.md` left unchanged (historical records) |
| `docs/THESIS_APPENDIX.md` | Superseded by the master's Appendices A–E; contained corrupted escapes | — |
| `docs/CHAPTER4_VERIFICATION_REPORT.md`, `docs/CHAPTER5_AUDIT_REPORT.md` | Superseded audits (pre-RQ4/RQ5); replaced by `reports/chapter5/*` and this audit | — |
| `docs/planning/` (midterm audit, slides) | Midterm planning, superseded | `docs/README.md` rewritten; dead link in `eval/README.md` de-linked |
| `docs/legacy/` (`App_db.sql`, `funcs.txt`, `thing.db`) | September prototype schema and notes, superseded by Django models; only referenced by the deleted planning doc | — |
| `docs/.$accounts.drawio.bkp`, `docs/.$documents.drawio.bkp`, `docs/.directory` | Editor backups / KDE metadata | — |
| `docs/figures/` (6 PNG) | Duplicate output of `generate_tables_and_plots.py`; the thesis embeds `reports/chapter5/figures/` | generator no longer writes there; `reports/chapter5/README.md` updated |
| `eval/results/figures/fig5_*.png` (5) and `eval/scripts/plot_chapter5_figures.py` | Stale earlier generation (4 of 5 differed from the canonical figures); script superseded by `reports/chapter5/scripts/generate_tables_and_plots.py` | Pareto figures in the same folder kept |

## Moved

| From | To | Reason |
|---|---|---|
| `hnsw_index_eval.ipynb` | `eval/phases/phase_4_indexing/notebooks/hnsw_index_eval.ipynb` | Phase-segregation rule; the notebook uses Colab `/content/` paths only, so it is location-independent |

## Deliberately preserved

- All datasets, manifests, raw outputs, checkpoints (`rq5_inference_checkpoint.jsonl`), embeddings caches.
- Original and adjudicated annotations, `review_and_signed.md`, the restricted mapping, and the superseded unblinded files and report.
- The provenance registry (corrections appended only), the DEC03 protocol and changelog, and every script that produced a cited artifact.
- `manifest.json` (root): written by `run_gate_g10_power_simulation.py`; `test_gate_scaffolding.py` asserts it exists.
- `thesis_system_specification.md`: deleted, then **restored** after finding that the thesis cites its IDs (SYS-001…006, ARCH-001/009). A status note was added instead.
- `eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT.md` (16-question pilot): referenced by the provenance registry.
- `notebooks/colab_gpu_offload_nougat_and_500k_e5.ipynb`: referenced by `eval/README.md`.
- `scratch/`: untracked, git-ignored local work.
- `docs/documents.drawio`: already deleted by the user before the audit; left as an unstaged deletion.

## Proposed (not removed: role or value uncertain)

| Path | Reason to consider | Why left |
|---|---|---|
| `dev_notes.txt` | Personal TODO list plus pasted October run stats | It is the author's own notes |
| `sample_documents/` (5 PDFs besides `attention.pdf`, one with a long "Anna's Archive" file name) | Only `attention.pdf` is used by tests | May be used for demos; check licensing of the book PDF before publishing the repo |
| `docs/SYSTEM_DESIGN_AUDIT.md`, `docs/DATA_VERIFICATION.md` | Pre-RQ4/RQ5 audits, partly outdated | Historical verification records |
| `eval/research_execution_ledger.md`, `eval/README.md` (116 KB) | Large, partly outdated narrative | Referenced widely; status rows were updated |
| `backend/grobid.json` vs `backend/apps/documents/data_extractor/grobid.json` | Two different GROBID configs | GROBID is optional; unclear which one is intended |
| Root `package.json` dependencies (`axios`, `pdfjs-dist`, `rest`) | Look misplaced (the root only runs `scripts/start-all.mjs`) | A dependency change was out of scope |
| `backend/apps/documents/services/webhook_service.py` post-ingestion POST to `localhost:8001` (default `RAG_WEBHOOK_URL`) and the unused `LLM_PROVIDER` setting | Dead integration | Code change outside this audit's defect list |

## Side effect noticed during verification

`eval/phases/phase_9_generation/scripts/validate_human_review_package.py` rewrites `validation_timestamp_utc` in the frozen `sampling_and_integrity_manifest.json` every time it runs. I reverted the change (`git checkout`). Consider making the validator read-only.
