#!/usr/bin/env python3
"""
Build Canonical Machine-Readable Experiment Provenance and Contamination Registry.

Outputs:
  - eval/experiment_provenance_registry.json

This registry tracks the exact historical exposure of all academic papers and questions
across RQ1, RQ2, RQ3, RQ4 (Dev & Test), RQ5 Pilot, and planned future experiments.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = WORKSPACE_ROOT / "eval"
DATA_DIR = EVAL_DIR / "data" / "qasper_official"
RESULTS_DIR = EVAL_DIR / "results"
PREPARED_DIR = EVAL_DIR / "prepared"
PHASE6_DIR = EVAL_DIR / "phases" / "phase_6_hybrid_retrieval" / "artifacts"
PHASE9_DIR = EVAL_DIR / "phases" / "phase_9_generation" / "artifacts"
SEED_PATH = WORKSPACE_ROOT / "backend" / "data" / "eval_benchmark_seed.json"

OUTPUT_REGISTRY_PATH = EVAL_DIR / "experiment_provenance_registry.json"


def main():
    print("[+] Loading official QASPER datasets...")
    with open(DATA_DIR / "qasper-train-v0.3.json", "r", encoding="utf-8") as f:
        train_data: Dict[str, Any] = json.load(f)
    with open(DATA_DIR / "qasper-dev-v0.3.json", "r", encoding="utf-8") as f:
        dev_data: Dict[str, Any] = json.load(f)
    with open(DATA_DIR / "qasper-test-v0.3.json", "r", encoding="utf-8") as f:
        test_data: Dict[str, Any] = json.load(f)

    train_pids = set(train_data.keys())
    dev_pids = set(dev_data.keys())
    test_pids = set(test_data.keys())
    all_qasper_pids = train_pids | dev_pids | test_pids

    # 1. Load RQ1
    print("[+] Loading RQ1 records...")
    with open(RESULTS_DIR / "rq1_extraction_queries_20261024_000639.jsonl", "r", encoding="utf-8") as f:
        rq1_records = [json.loads(line) for line in f]
    rq1_pids = sorted(list({r["paper_arxiv_id"] for r in rq1_records}))
    rq1_qids = sorted(list({r["query_id"] for r in rq1_records}))

    # 2. Load RQ2
    print("[+] Loading RQ2 records...")
    with open(RESULTS_DIR / "rq2_chunking_queries_20261024_013443.jsonl", "r", encoding="utf-8") as f:
        rq2_records = [json.loads(line) for line in f]
    rq2_pids = sorted(list({r["paper_arxiv_id"] for r in rq2_records}))
    rq2_qids = sorted(list({r["query_id"] for r in rq2_records}))

    # 3. Load RQ3
    print("[+] Loading RQ3 records...")
    with open(PREPARED_DIR / "expanded_corpus.json", "r", encoding="utf-8") as f:
        rq3_corpus = json.load(f)
    rq3_pids = sorted(list(rq3_corpus.keys()))
    with open(PREPARED_DIR / "expanded_qasper_sampled.json", "r", encoding="utf-8") as f:
        rq3_samp = json.load(f)
    rq3_qids = sorted(list({q["id"] for q in rq3_samp}))

    # 4. Load RQ4 Dev & Test
    print("[+] Loading RQ4 records...")
    def extract_rq4_items(split_dict: Dict[str, Any]) -> tuple[List[str], List[str]]:
        pids = set()
        qids = set()
        for pid, pdata in split_dict.items():
            has_ev = False
            for qa in pdata.get("qas", []):
                text_ev = []
                for ans in qa.get("answers", []):
                    a = ans.get("answer", {})
                    if not a.get("unanswerable", False):
                        for ev in a.get("evidence", []):
                            if isinstance(ev, str) and not ev.startswith("FLOAT SELECTED") and ev.strip():
                                text_ev.append(ev.strip())
                if text_ev:
                    has_ev = True
                    qids.add(qa.get("question_id"))
            if has_ev:
                pids.add(pid)
        return sorted(list(pids)), sorted(list(qids))

    rq4_dev_pids, rq4_dev_qids = extract_rq4_items(dev_data)
    rq4_test_pids, rq4_test_qids = extract_rq4_items(test_data)

    # 5. Load RQ5 Seed Pilot
    print("[+] Loading RQ5 pilot records...")
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        rq5_pilot_items = json.load(f)
    rq5_pilot_pids = sorted(list({x["paper_arxiv_id"] for x in rq5_pilot_items}))
    rq5_pilot_qids = sorted(list({x["id"] for x in rq5_pilot_items}))

    # 6. Audit Unexposed Train Reservoir & Eligible Candidates
    print("[+] Auditing Unexposed Train Reservoir...")
    rq3_train_pids = set(rq3_pids) & train_pids
    unexposed_train_dict = {pid: train_data[pid] for pid in train_data if pid not in rq3_train_pids}

    cand_487_pids = []
    cand_487_qids = []
    single_q_pids = []
    single_q_qids = []
    zero_q_pids = []

    for pid, pdata in unexposed_train_dict.items():
        el_qs = []
        for qa in pdata.get("qas", []):
            atomic_ev = [
                a["answer"] for a in qa.get("answers", [])
                if not a["answer"].get("unanswerable", False) and
                any("FLOAT SELECTED" not in t and t.strip() for t in a["answer"].get("evidence", []) if isinstance(t, str)) and
                (any(s.strip() for s in a["answer"].get("extractive_spans", []) if isinstance(s, str)) or
                 (a["answer"].get("free_form_answer") and a["answer"].get("free_form_answer").strip()) or
                 a["answer"].get("yes_no") is not None)
            ]
            if atomic_ev:
                el_qs.append(qa.get("question_id"))
        
        if len(el_qs) >= 2:
            cand_487_pids.append(pid)
            cand_487_qids.extend(el_qs)
        elif len(el_qs) == 1:
            single_q_pids.append(pid)
            single_q_qids.extend(el_qs)
        else:
            zero_q_pids.append(pid)

    cand_487_pids.sort()
    cand_487_qids.sort()
    single_q_pids.sort()
    zero_q_pids.sort()

    # 7. Load Frozen RQ5 Sample Manifest if generated
    manifest_path = PHASE9_DIR / "eval_sample_manifest_500q.json"
    sampled_primary_pids = []
    sampled_qids = []
    standby_pids = []
    manifest_sha256 = ""
    manifest_file_sha256 = ""
    if manifest_path.exists():
        print("[+] Loading frozen sample manifest (eval_sample_manifest_500q.json)...")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        with open(manifest_path, "rb") as mf:
            import hashlib
            manifest_file_sha256 = hashlib.sha256(mf.read()).hexdigest()
        sampled_primary_pids = sorted(list({item["paper_arxiv_id"] for item in manifest_data["selected_eval_items"]}))
        sampled_qids = [item["question_id"] for item in manifest_data["selected_eval_items"]]
        standby_pids = [s["paper_arxiv_id"] for s in manifest_data["manifest_metadata"].get("standby_queue", [])]
        manifest_sha256 = manifest_data["manifest_metadata"].get("manifest_sha256", "")
        print(f"[*] Loaded frozen manifest: {len(sampled_primary_pids)} primary papers, {len(sampled_qids)} questions, {len(standby_pids)} standby reserve papers.")

    # Build Registered Experiments Table
    registered_experiments = {
        "EXP-RQ1-EXTRACTION": {
            "experiment_id": "EXP-RQ1-EXTRACTION",
            "phase": "RQ1",
            "experiment_name": "PDF Layout Extraction Engine Benchmark",
            "date": "2026-10-24",
            "status": "COMPLETED",
            "dataset_name": "QASPER v0.3",
            "dataset_split": "dev",
            "source_manifest": "eval/data/qasper_official/qasper-dev-v0.3.json",
            "paper_count": len(rq1_pids),
            "question_count": len(rq1_qids),
            "paper_ids": rq1_pids,
            "question_ids": rq1_qids,
            "models_or_methods_evaluated": [
                "pymupdf_layout",
                "pymupdf_plain",
                "pypdf",
                "pdfminer",
                "pypdfium2"
            ],
            "evaluation_purpose": "DEVELOPMENT_SELECTION",
            "decisions_influenced": [
                "Selected PyMuPDF layout engine as default extractor for document ingestion (heading F1 48.01%, 26.2 ms/page latency)",
                "Selected PyMuPDF plain as fast fallback extractor"
            ],
            "exposure_classification": "DEVELOPMENT_SELECTION_EXPOSURE",
            "result_artifacts": [
                "eval/results/rq1_extraction_20261024_000639.json",
                "eval/results/rq1_extraction_queries_20261024_000639.jsonl"
            ],
            "script_path": "eval/phases/phase_1_extraction/scripts/evaluate_step1_full_dev.py",
            "provenance_notes": "Evaluated on 47 arXiv computer science preprints in QASPER Dev. Cannot claim universal OCR performance on multi-column non-arXiv formats."
        },
        "EXP-RQ2-CHUNKING": {
            "experiment_id": "EXP-RQ2-CHUNKING",
            "phase": "RQ2",
            "experiment_name": "Document Chunking Strategy Evaluation",
            "date": "2026-10-24",
            "status": "COMPLETED",
            "dataset_name": "QASPER v0.3",
            "dataset_split": "dev",
            "source_manifest": "eval/data/qasper_official/qasper-dev-v0.3.json",
            "paper_count": len(rq2_pids),
            "question_count": len(rq2_qids),
            "paper_ids": rq2_pids,
            "question_ids": rq2_qids,
            "models_or_methods_evaluated": [
                "naive_midpoint",
                "section_baseline",
                "section_token",
                "section_overlap_200",
                "section_overlap_400",
                "section_overlap_600",
                "hierarchical_small_to_big",
                "hierarchical_budget_1600"
            ],
            "evaluation_purpose": "DEVELOPMENT_SELECTION",
            "decisions_influenced": [
                "Selected hierarchical Small-to-Big chunking as champion architecture (nDCG@10 = 0.6880)",
                "Selected section_overlap sliding window as flat fallback"
            ],
            "exposure_classification": "DEVELOPMENT_SELECTION_EXPOSURE",
            "result_artifacts": [
                "eval/results/rq2_chunking_20261024_013443.json",
                "eval/results/rq2_chunking_queries_20261024_013443.jsonl"
            ],
            "script_path": "eval/phases/phase_2_chunking/scripts/evaluate_part1b_chunking.py",
            "provenance_notes": "Evaluated across same 47 Dev papers as RQ1. Measured IR containment only; deferred generative QA to RQ5."
        },
        "EXP-RQ3-EMBEDDING-UNIFIED": {
            "experiment_id": "EXP-RQ3-EMBEDDING-UNIFIED",
            "phase": "RQ3",
            "experiment_name": "Unified Dense Embedding Model Selection Benchmark",
            "date": "2026-10-18",
            "status": "COMPLETED",
            "dataset_name": "QASPER v0.3 Unified Cohort",
            "dataset_split": "dev+train",
            "source_manifest": "eval/prepared/expanded_corpus.json",
            "paper_count": len(rq3_pids),
            "question_count": len(rq3_qids),
            "paper_ids": rq3_pids,
            "question_ids": rq3_qids,
            "models_or_methods_evaluated": [
                "sentence-transformers/all-MiniLM-L6-v2",
                "intfloat/e5-small-v2",
                "BAAI/bge-small-en-v1.5",
                "Snowflake/snowflake-arctic-embed-s",
                "nomic-ai/nomic-embed-text-v1.5",
                "nomic-ai/modernbert-embed-base",
                "BM25"
            ],
            "evaluation_purpose": "DEVELOPMENT_SELECTION",
            "decisions_influenced": [
                "Selected intfloat/e5-small-v2 as production desktop embedding champion (0.5522 nDCG@10, 30.2 ms latency, 384 dims, 33M params)",
                "Calibrated prefix injection rules for asymmetric models (query: / passage:)"
            ],
            "exposure_classification": "DEVELOPMENT_SELECTION_EXPOSURE",
            "result_artifacts": [
                "eval/results/thesis_embedding_benchmark.json",
                "eval/phases/phase_3_embedding/artifacts/expanded_160_papers_benchmark_results.json"
            ],
            "script_path": "eval/phases/phase_3_embedding/scripts/run_thesis_embedding_benchmark.py",
            "provenance_notes": "Evaluated 207 active scored papers (97 Dev + 110 Train). Exactly 111 Train papers and 100 Dev papers were prepared in expanded_corpus.json. 0 Test papers were included."
        },
        "EXP-RQ4-HYBRID-DEV": {
            "experiment_id": "EXP-RQ4-HYBRID-DEV",
            "phase": "RQ4",
            "experiment_name": "Hybrid Retrieval Evaluation on QASPER Dev",
            "date": "2026-10-25",
            "status": "COMPLETED",
            "dataset_name": "QASPER v0.3",
            "dataset_split": "dev",
            "source_manifest": "eval/data/qasper_official/qasper-dev-v0.3.json",
            "paper_count": len(rq4_dev_pids),
            "question_count": len(rq4_dev_qids),
            "paper_ids": rq4_dev_pids,
            "question_ids": rq4_dev_qids,
            "models_or_methods_evaluated": [
                "Dense Only (e5-small-v2)",
                "BM25 Only (WordPiece)",
                "Hybrid RRF (k=60)",
                "Hybrid Convex (alpha=0.7)"
            ],
            "evaluation_purpose": "EXPLORATORY_ANALYSIS",
            "decisions_influenced": [
                "Verified that hybrid fusion does not degrade dense retrieval accuracy on Dev (p_adj = 1.000)",
                "Observed dense-lexical ranking stability on academic preprint vocabulary"
            ],
            "exposure_classification": "EXPLORATORY_EXPOSURE",
            "result_artifacts": [
                "eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_dev_hierarchical_benchmark.json",
                "eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_DEV_HIERARCHICAL_REPORT.md"
            ],
            "script_path": "eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py",
            "provenance_notes": "Evaluated across 276 Dev papers containing non-empty text evidence (5 of 281 Dev papers had 0 text chunks)."
        },
        "EXP-RQ4-HYBRID-TEST": {
            "experiment_id": "EXP-RQ4-HYBRID-TEST",
            "phase": "RQ4",
            "experiment_name": "Confirmatory Hybrid Retrieval Evaluation on QASPER Test",
            "date": "2026-10-25",
            "status": "COMPLETED",
            "dataset_name": "QASPER v0.3",
            "dataset_split": "test",
            "source_manifest": "eval/data/qasper_official/qasper-test-v0.3.json",
            "paper_count": len(rq4_test_pids),
            "question_count": len(rq4_test_qids),
            "paper_ids": rq4_test_pids,
            "question_ids": rq4_test_qids,
            "models_or_methods_evaluated": [
                "Dense Only (e5-small-v2)",
                "BM25 Only (WordPiece)",
                "Hybrid RRF (k=60)",
                "Hybrid Convex (alpha=0.7)"
            ],
            "evaluation_purpose": "CONFIRMATORY_EVALUATION",
            "decisions_influenced": [
                "Evaluated Convex fusion gain (nDCG@10 = 0.5806, p_adj = 0.0140*) under split-wide BM25 background IDF across 14,035 chunks",
                "Reconciled discrepancy with local document IDF in production (~35-60 chunks) where term repetition compresses IDF and causes division-by-zero risk",
                "Maintained provisionally RRF (k=60) in production DocumentRAG.query due to score-scale invariance"
            ],
            "exposure_classification": "CONFIRMATORY_EVALUATION_EXPOSURE",
            "result_artifacts": [
                "eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json",
                "eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md"
            ],
            "script_path": "eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py",
            "provenance_notes": "PERMANENT EXPOSURE BOUNDARY: 408 Test papers were evaluated. QASPER Test is permanently previously exposed and must never be described as an unexposed test set for the overall RAG system."
        },
        "EXP-RQ5-PILOT-SEED": {
            "experiment_id": "EXP-RQ5-PILOT-SEED",
            "phase": "RQ5",
            "experiment_name": "Preliminary 16-Question SLM Generation Pilot",
            "date": "2026-10-25",
            "status": "COMPLETED",
            "dataset_name": "Curated Seed Benchmark",
            "dataset_split": "non_qasper_seed",
            "source_manifest": "backend/data/eval_benchmark_seed.json",
            "paper_count": len(rq5_pilot_pids),
            "question_count": len(rq5_pilot_qids),
            "paper_ids": rq5_pilot_pids,
            "question_ids": rq5_pilot_qids,
            "models_or_methods_evaluated": [
                "qwen2.5:0.5b",
                "llama3.2:1b",
                "llama3.2:3b"
            ],
            "evaluation_purpose": "EXPLORATORY_ANALYSIS",
            "decisions_influenced": [
                "Verified local Ollama CPU inference execution, prompt templates, and coordinate mapping",
                "Motivated outlier sensitivity checks (Wilcoxon and 10% trimmed mean) due to observed paper-level variance (-0.12 to +0.19)",
                "Restricted pilot scope: descriptive evidence from 4 papers only; cannot establish 50-paper or 250-paper distribution"
            ],
            "exposure_classification": "EXPLORATORY_EXPOSURE",
            "result_artifacts": [
                "eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark.json",
                "eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT.md"
            ],
            "script_path": "eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py",
            "provenance_notes": "Completely disjoint from QASPER. 4 seminal arXiv preprints (ResNet, Attention, LoRA, RAG). Zero overlap with QASPER Train, Dev, or Test."
        },
        "EXP-RQ5-MAIN-SAMPLED": {
            "experiment_id": "EXP-RQ5-MAIN-SAMPLED",
            "phase": "RQ5",
            "experiment_name": "Frozen 250-Paper Confirmatory SLM Generation Evaluation",
            "date": "2026-10-26",
            "status": "COMPLETED",
            "dataset_name": "QASPER v0.3 Unexposed Train Reservoir",
            "dataset_split": "train_unexposed",
            "source_manifest": "eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json",
            "manifest_sha256": manifest_sha256,
            "manifest_file_sha256": manifest_file_sha256,
            "target_paper_count": 250,
            "target_question_count": 500,
            "paper_count": len(sampled_primary_pids),
            "question_count": len(sampled_qids),
            "paper_ids": sampled_primary_pids,
            "question_ids": sampled_qids,
            "standby_reserve_paper_count": len(standby_pids),
            "standby_reserve_paper_ids": standby_pids,
            "candidate_pool_paper_count": len(cand_487_pids),
            "candidate_pool_paper_ids": cand_487_pids,
            "models_or_methods_evaluated": [
                "llama3.2:3b",
                "llama3.2:1b",
                "qwen2.5:0.5b"
            ],
            "evaluation_purpose": "CONFIRMATORY_EVALUATION",
            "decisions_influenced": [
                "Frozen sample manifest (seed 42) evaluated across 500 questions (1,500 inference calls)",
                "Option A approved for human claim-level review (20 questions x 3 models = 60 model answers)",
                "llama3.2:3b demonstrated superior technical synthesis over llama3.2:1b (+0.0687 Delta, p=3.35e-9*)"
            ],
            "exposure_classification": "CONFIRMATORY_EVALUATION_EXPOSURE",
            "result_artifacts": [
                "eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json",
                "eval/phases/phase_9_generation/artifacts/RQ5_LLM_GENERATION_REPORT_500Q.md",
                "eval/phases/phase_9_generation/artifacts/rq5_inference_checkpoint.jsonl"
            ],
            "protocol_document": "eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md",
            "provenance_notes": "Target: 250 papers (m=2 questions/paper, total N=500 questions, 1,500 model outputs). Drawn strictly from the 487 verified unexposed candidate papers. Zero overlap with historical experiments (RQ1-RQ4, Pilot, Dev Partition)."
        }
    }

    # Build Master Paper Index (all QASPER + Seed papers)
    print("[+] Building Master Paper Index...")
    all_paper_ids = sorted(list(all_qasper_pids | set(rq5_pilot_pids)))
    paper_index: Dict[str, Dict[str, Any]] = {}

    for pid in all_paper_ids:
        # Determine split
        if pid in train_pids:
            orig_split = "train"
            title = train_data[pid].get("title", "")
        elif pid in dev_pids:
            orig_split = "dev"
            title = dev_data[pid].get("title", "")
        elif pid in test_pids:
            orig_split = "test"
            title = test_data[pid].get("title", "")
        else:
            orig_split = "non_qasper_seed"
            title = next((x["paper_title"] for x in rq5_pilot_items if x["paper_arxiv_id"] == pid), "Seed Paper")

        # Compile exposure events
        events = []
        classifications: Set[str] = set()

        if pid in rq1_pids:
            events.append({
                "experiment_id": "EXP-RQ1-EXTRACTION",
                "phase": "RQ1",
                "role": "EVALUATED_EXTRACTION",
                "outputs_inspected": True,
                "influenced_decision": "PyMuPDF layout selection",
                "classification": "DEVELOPMENT_SELECTION_EXPOSURE"
            })
            classifications.add("DEVELOPMENT_SELECTION_EXPOSURE")

        if pid in rq2_pids:
            events.append({
                "experiment_id": "EXP-RQ2-CHUNKING",
                "phase": "RQ2",
                "role": "EVALUATED_CHUNKING",
                "outputs_inspected": True,
                "influenced_decision": "Hierarchical chunking selection",
                "classification": "DEVELOPMENT_SELECTION_EXPOSURE"
            })
            classifications.add("DEVELOPMENT_SELECTION_EXPOSURE")

        if pid in rq3_pids:
            events.append({
                "experiment_id": "EXP-RQ3-EMBEDDING-UNIFIED",
                "phase": "RQ3",
                "role": "EVALUATED_EMBEDDING",
                "outputs_inspected": True,
                "influenced_decision": "e5-small-v2 champion selection",
                "classification": "DEVELOPMENT_SELECTION_EXPOSURE"
            })
            classifications.add("DEVELOPMENT_SELECTION_EXPOSURE")

        if pid in rq4_dev_pids:
            events.append({
                "experiment_id": "EXP-RQ4-HYBRID-DEV",
                "phase": "RQ4",
                "role": "EVALUATED_HYBRID_DEV",
                "outputs_inspected": True,
                "influenced_decision": "Hybrid ranking stability check",
                "classification": "EXPLORATORY_EXPOSURE"
            })
            classifications.add("EXPLORATORY_EXPOSURE")

        if pid in rq4_test_pids:
            events.append({
                "experiment_id": "EXP-RQ4-HYBRID-TEST",
                "phase": "RQ4",
                "role": "EVALUATED_HYBRID_TEST",
                "outputs_inspected": True,
                "influenced_decision": "Convex vs RRF reconciliation",
                "classification": "CONFIRMATORY_EVALUATION_EXPOSURE"
            })
            classifications.add("CONFIRMATORY_EVALUATION_EXPOSURE")

        if pid in rq5_pilot_pids:
            events.append({
                "experiment_id": "EXP-RQ5-PILOT-SEED",
                "phase": "RQ5",
                "role": "EVALUATED_GENERATION_PILOT",
                "outputs_inspected": True,
                "influenced_decision": "Harness execution & sensitivity protocol",
                "classification": "EXPLORATORY_EXPOSURE"
            })
            classifications.add("EXPLORATORY_EXPOSURE")

        if pid in dev_pids and not (pid in rq1_pids or pid in rq2_pids or pid in rq3_pids or pid in rq4_dev_pids):
            events.append({
                "experiment_id": "EXP-DEV-PARTITION",
                "phase": "DEV-PARTITION",
                "role": "MEMBER_DEV_PARTITION_UNRUN",
                "outputs_inspected": False,
                "influenced_decision": "Development split partition boundary (member of official Dev split, 0 text evidence in QASPER)",
                "classification": "DEVELOPMENT_SELECTION_EXPOSURE"
            })
            classifications.add("DEVELOPMENT_SELECTION_EXPOSURE")

        # Default classification if no exposure
        if not classifications:
            classifications.add("UNEXPOSED_REPOSITORY")

        # Eligibility for planned RQ5 main study
        is_in_cand_487 = pid in cand_487_pids
        rq5_eligibility_status = "ELIGIBLE_CANDIDATE_POOL" if is_in_cand_487 else (
            "EXCL_PREVIOUSLY_EXPOSED" if classifications != {"UNEXPOSED_REPOSITORY"} else (
                "EXCL_FEWER_THAN_2_QUESTIONS" if pid in single_q_pids else (
                    "EXCL_ZERO_ELIGIBLE_QUESTIONS" if pid in zero_q_pids else "EXCL_NON_TRAIN_SPLIT"
                )
            )
        )

        # RQ5 sampling status
        if pid in sampled_primary_pids:
            rq5_sample_status = "SAMPLED_PRIMARY"
        elif pid in standby_pids:
            rq5_sample_status = "STANDBY_RESERVE"
        elif pid in cand_487_pids:
            rq5_sample_status = "RESIDUAL_CANDIDATE"
        else:
            rq5_sample_status = "NOT_IN_CANDIDATE_POOL"

        paper_index[pid] = {
            "paper_arxiv_id": pid,
            "title": title,
            "original_split": orig_split,
            "exposure_events": events,
            "exposure_classifications": sorted(list(classifications)),
            "is_unexposed_to_repository_experiments": classifications == {"UNEXPOSED_REPOSITORY"},
            "potential_pretraining_contamination": "POSSIBLE_PUBLIC_ARXIV",
            "rq5_main_eligibility": rq5_eligibility_status,
            "rq5_sampling_status": rq5_sample_status
        }

    # Summary Statistics
    registry_output = {
        "registry_metadata": {
            "registry_name": "Scientific Document Manager - Persistent Experiment Provenance and Contamination Registry",
            "version": "1.0.0",
            "created_date": "2026-10-26",
            "canonical_file": "eval/experiment_provenance_registry.json",
            "documentation_file": "eval/EXPERIMENT_PROVENANCE_REGISTRY.md",
            "query_tool": "eval/scripts/check_experiment_overlap.py",
            "status": "ACTIVE_MANDATORY"
        },
        "exposure_classification_definitions": {
            "UNEXPOSED_REPOSITORY": "No prior experimental use identified in audited repository history. Does not establish absence from LLM pretraining.",
            "EXPLORATORY_EXPOSURE": "Used for preliminary experiments, debugging, diagnostics, or pilot evaluation.",
            "DEVELOPMENT_SELECTION_EXPOSURE": "Used to select models, chunking strategies, extractors, prompts, thresholds, or retrieval configurations.",
            "CONFIRMATORY_EVALUATION_EXPOSURE": "Used in a designated confirmatory evaluation (e.g. RQ4 Test). Cannot be repurposed as a blind evaluation set for the overall pipeline.",
            "HISTORICAL_UNCERTAIN_PROVENANCE": "Prior use is suspected or known from text notes, but exact item-level manifests cannot be verified.",
            "POTENTIAL_PRETRAINING_CONTAMINATION": "Standard scientific caveat acknowledging that public arXiv preprints cannot be conclusively proven absent from commercial or open-source LLM pretraining corpora."
        },
        "summary": {
            "official_qasper_counts": {
                "train_papers": len(train_pids),
                "dev_papers": len(dev_pids),
                "test_papers": len(test_pids),
                "total_papers": len(all_qasper_pids)
            },
            "historical_exposure_counts": {
                "train_papers_exposed": len(rq3_train_pids),
                "dev_papers_exposed": len(dev_pids),
                "test_papers_exposed": len(rq4_test_pids),
                "non_qasper_seed_papers_exposed": len(rq5_pilot_pids),
                "total_unique_papers_exposed_historically": 804,
                "active_experimental_run_papers": len(
                    set(rq1_pids) | set(rq3_pids) | set(rq4_dev_pids) | set(rq4_test_pids) | set(rq5_pilot_pids)
                ),
                "dev_papers_active_runs": len((set(rq1_pids) | set(rq2_pids) | set(rq3_pids) | set(rq4_dev_pids)) & dev_pids),
                "dev_papers_unrun_no_text_evidence": 2,
                "test_papers_unrun_zero_chunks": 8,
                "reconciliation_arithmetic": "111 Train (RQ3) + 281 Dev (all official Dev papers) + 408 Test (evaluated in RQ4 Test) + 4 Seed (RQ5 Pilot) = 804 unique exposed papers. If only papers with active experimental runs in Dev are counted, exactly 2 Dev papers (1804.00720, 1903.07406) had 0 text evidence and were not run, yielding 111 + 279 + 408 + 4 = 802 unique active-run papers."
            },
            "unexposed_train_reservoir": {
                "total_unexposed_train_papers": len(unexposed_train_dict),
                "papers_with_ge_2_eligible_questions": len(cand_487_pids),
                "papers_with_1_eligible_question": len(single_q_pids),
                "papers_with_0_eligible_questions": len(zero_q_pids),
                "total_eligible_questions_in_reservoir": len(cand_487_qids) + len(single_q_qids),
                "target_rq5_main_papers": 250,
                "target_rq5_main_questions": 500,
                "feasibility_margin_papers": len(cand_487_pids) - 250
            },
            "rq5_sampled_cohort": {
                "manifest_file": "eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json",
                "manifest_sha256": manifest_sha256,
                "manifest_file_sha256": manifest_file_sha256,
                "status": "SAMPLED_MANIFEST_FROZEN",
                "sampled_primary_papers_count": len(sampled_primary_pids),
                "sampled_primary_questions_count": len(sampled_qids),
                "standby_reserve_papers_count": len(standby_pids),
                "residual_candidate_papers_count": len(cand_487_pids) - len(sampled_primary_pids) - len(standby_pids)
            }
        },
        "registered_experiments": registered_experiments,
        "paper_index": paper_index
    }

    print(f"[+] Writing registry to {OUTPUT_REGISTRY_PATH}...")
    with open(OUTPUT_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry_output, f, indent=2)

    print(f"[+] Done! Registered {len(registered_experiments)} experiments across {len(paper_index)} papers.")


if __name__ == "__main__":
    main()
