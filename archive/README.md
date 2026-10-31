# Archive

Superseded material moved out of the active project on 2026-10-31 during the simplification of the evaluation work. Files keep their original paths below `archive/` (for example `archive/reports/revalidation/...` was `reports/revalidation/...`), and git history is preserved (`git log --follow`). Nothing in the active code or documentation reads from this folder.

## What is here and why

| Group | Original location | Why it was archived | Where the content lives now |
|---|---|---|---|
| Experiment governance | `eval/experiment_provenance_registry.json`, `eval/EXPERIMENT_PROVENANCE_REGISTRY.md`, `eval/scripts/` (overlap check, registry builder, exposure events), `phase_0_baseline/scripts/register_protocol_hashes.py`, `validate_reval_harness.py`, `build_revalidation_cohorts.py`, `download_reservoir_pdfs.py` | Exposure registry, protocol hashing and approval gates are beyond the scope of the project | The component data sets themselves stay active (`eval/phases/phase_0_baseline/artifacts/revalidation/cohort_*.json`); `eval/README.md` §3 describes them |
| Revalidation protocols and logs | `reports/revalidation/` (17 protocol JSONs, Gate B report, execution log, pending decisions, candidate-selection audit, validity matrix) | Governance records of the second round of experiments | Settings are constants in the experiment scripts; results and decisions are in `eval/README.md` |
| Audit reports | `reports/audit/` | Records of the October audit | Corrections already applied to code, data and thesis |
| Statistical-inference scripts and outputs | `phase_3_embedding/scripts/{audit_and_correct_statistics, run_gate_g10_power_simulation, test_gate_scaffolding, test_cluster_bootstrap, update_readme_statistics}.py`, `eval/audit/verify_gate_g14_spot_check.py`, `eval/prepared/expansion_decision.json`, `phase_9_generation/artifacts/C2_5_STATISTICAL_VALIDITY_AUDIT.md` | Power analysis, bootstrap and significance testing are no longer used | — (descriptive results are in `eval/README.md`) |
| First-round (v1) experiments | `backend/scripts/` v1 evaluation scripts, `phase_3`/`phase_6` v1 scripts, `phase_4_indexing`, `phase_5_query_processing`, `phase_10_citation`, `phase_11_integrated` (never run), unused `eval/prepared/` and `eval/results/` files, `eval/figures/embedding_model_performance_comparison*.png`, `notebooks/`, `backend/data/` | Superseded by the second-round component experiments, which share one data set and one pipeline | Files still cited by the thesis or Chapter 5 were left in place until the thesis revision |
| Semantic-chunking add-on to the earlier grid | `phase_12_combination/scripts/combo_stage1b_semantic.py`, `artifacts/stage1b_semantic/` (partial: 4 of 5 embedders; stopped on 2026-10-31), `artifacts/stage2/` | Not part of the 16-configuration design; semantic chunking is covered by the chunking experiment | `eval/README.md` §5.2 |
| Superseded runs | `phase_9_generation/artifacts/` 250-question run and invalid memory-profile runs (`rq5m_run1_invalid_memory.log`, `rq5m_run2_contaminated_memory.log`, `generation_resource_profile/summary_run1…`, `summary_run2…`, `REPORT_run2_superseded.md`) | Replaced by later runs | `rq5_llm_generation_benchmark_500q.json`, `generation_resource_profile/summary.json` |
| Old documentation | `eval/README.md` (previous version), `eval/research_execution_ledger.md`, `eval/phases/phase_9_generation/README.md`, `docs/thesis_alignment_decisions.md`, `docs/DATA_VERIFICATION.md`, `docs/SYSTEM_DESIGN_AUDIT.md`, `thesis_system_specification.md` | Outdated or contradicting the current state | `eval/README.md`, `AGENTS.md`, `ARCHITECTURE.md` |

## Renamed files (still active)

Second-round scripts and result folders were renamed from research-question names to component names:

| Old | New |
|---|---|
| `phase_2_chunking/scripts/rq2v2_budgeted_chunking.py`, `rq2ext_children.py`, `rq2ext_semantic.py`, `rq2_diagnostic.py` | `evaluate_chunking.py`, `evaluate_chunking_children.py`, `evaluate_chunking_semantic.py`, `chunking_diagnostic.py` |
| `phase_2_chunking/artifacts/rq2v2/`, `rq2_ext_children/`, `rq2_ext_semantic/` | `chunking/`, `chunking_children/`, `chunking_semantic/` |
| `phase_3_embedding/scripts/rq3v2_shortlist.py`, `rq3ext_specter2.py`; artifacts `rq3v2/`, `rq3_ext_specter2/` | `evaluate_embedding.py`, `evaluate_embedding_specter2.py`; `embedding/`, `embedding_specter2/` |
| `phase_6_hybrid_retrieval/scripts/rq4v2_fusion.py`, `rq4ext_rerank.py`, `evaluate_rq4p_production_fusion.py`, `decompose_rq4p_bm25_dev.py`; artifacts `rq4v2/`, `rq4_ext_rerank/`, `rq4p_production_fusion/` | `evaluate_retrieval_fusion.py`, `evaluate_reranking.py`, `check_production_fusion.py`, `decompose_production_bm25.py`; `retrieval_fusion/`, `reranking/`, `production_fusion_check/` |
| `phase_9_generation/scripts/evaluate_rq5_llm_generation.py`, `rq5ext_llm_candidates.py`, `rq5_resource_profile.py`, `rq5_reanalysis.py`, `rq5m_diag_*.py`; artifacts `rq5_ext_llm/`, `rq5_resource_profile/`, `rq5r_reanalysis/` | `evaluate_generation.py`, `evaluate_generation_extra_llms.py`, `profile_generation_resources.py`, `generation_reanalysis.py`, `diag_generation_memory_*.py`; `generation_extra_llms/`, `generation_resource_profile/`, `generation_reanalysis/` |
| `phase_1_extraction/scripts/rq1v2_extractors.py`, `rq1v2_grobid_addon.py`; artifacts `rq1v2/`, `rq1v2_grobid_addon/` | `evaluate_extraction.py`, `evaluate_extraction_grobid.py`; `extraction/`, `extraction_grobid/` (embedding-cache tags keep the old `rq1v2_` prefix so cached vectors are reused) |
| `phase_12_combination/scripts/combo_stage2_e2e.py` | `run_combinations.py` (rewritten for the 16-configuration design) |
| `reports/revalidation/presentation/`, `progress_report_presentation.md` | `reports/presentation/` |

Result files cited by the thesis kept their names until the thesis revision (for example `rq5_llm_generation_benchmark_500q.json`, `rq4_qasper_test_hierarchical_benchmark.json`, `eval/results/rq1_extraction_20261024_000639.json`).

## Deleted (no unique content)

Ignored scratch folders (`scratch/`, `eval/scratch/`: one-off thesis-editing and inspection scripts), `xml_store/` (empty), `dev_notes.txt` and `manifest.json` (stale notes pointing to missing files), smoke-test output folders, `eval/pdfs/peerqa.zip` (same content as `eval/pdfs/peerqa/`) and `__pycache__/` folders.
