"""
Phase-by-Phase Evaluation Organization Script.
Creates clean, modular directories separated by each phase under eval/phases/:
  eval/phases/
    ├── README.md                      # Master Cross-Phase Index & Navigation Matrix
    ├── phase_0_baseline/              # Harness, data prep, page locators, anti-circularity
    ├── phase_1_extraction/            # PDF layout extraction, Heading Taxonomy, CER, Grobid & Nougat
    ├── phase_2_chunking/              # Sentence-aware packing, token budgets, truncation ablation
    ├── phase_3_embedding/             # Dense models (E5, BGE, MiniLM), containment, high-power split
    ├── phase_4_indexing/              # SQLite exact vs BLAS oracle, Standalone Docker Qdrant, HNSW Pareto
    ├── phase_6_hybrid_retrieval/      # Dense + BM25 Reciprocal Rank Fusion, convex combination
    └── phase_10_citation/             # Page attribution, consensus gold, hallucination audit

Maintains 100% backward compatibility by retaining eval/prepared/ as the canonical data store.
"""

import json
import os
import shutil
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
EVAL_DIR = WORKSPACE_ROOT / "eval"
PREPARED_DIR = EVAL_DIR / "prepared"
PHASES_DIR = EVAL_DIR / "phases"


PHASE_SPECS = {
    "phase_0_baseline": {
        "title": "Phase 0: Baseline & Infrastructure Verification",
        "description": "Baseline verification of standalone CLI execution, QASPER benchmark stratification, 4-tier PyMuPDF page locators, and dual-engine anti-circularity validation.",
        "artifacts": [
            "dev_held_out_split.json",
            "sample_ids.json",
            "eda_summary.json",
            "human_review_needed.json",
            "HUMAN_PAGE_AUDIT_QUEUE.md",
        ],
        "key_metrics": {
            "Total Sampled Papers": "96 (48 Dev, 48 Held-Out)",
            "Total Answerable Queries": "242 (128 Dev, 114 Held-Out)",
            "Anti-Circularity Agreement": "97.0% exact page consensus between PyMuPDF and pypdf (128/132 questions)",
            "Backend Tests": "29/29 passing",
        },
    },
    "phase_1_extraction": {
        "title": "Phase 1: PDF Document Extraction & Layout Analysis",
        "description": "Layout-aware block parsing (`sort=True`), Heading Taxonomy Trap remediation (fixing LaTeX small-caps ligatures and conversational headings to achieve 100% pilot recall), full-corpus 48-paper Dev benchmark, paragraph Character Error Rate (1-CER), and remote Grobid/Nougat connectors.",
        "artifacts": [
            "step1_full_dev_extraction_benchmark.json",
            "circularity_audit_results.json",
        ],
        "extra_sources": [
            WORKSPACE_ROOT / "backend" / "data" / "extraction_evaluation_results.json",
        ],
        "key_metrics": {
            "Pilot Heading Recall": "100.0% (Attention 100%, ResNet 100%, RAG 100%, LoRA 100% - fixed from 14.3%)",
            "Full-Dev Heading Recall (47 Papers)": "56.5% macro-averaged across diverse typography",
            "Paragraph Accuracy (1 - CER)": "37.3% macro Levenshtein alignment vs source TeX/XML",
            "Parsing Latency": "207.6 ms/doc (~11.5 ms/page) on standard CPU",
        },
    },
    "phase_2_chunking": {
        "title": "Phase 2: Document Chunking & Tokenization Distribution",
        "description": "Analysis of WordPiece tokenization impedance mismatch, character proxy resolution (1,400 chars acting as ~220 words), elimination of crude midpoint split confound (`len//2`), Sentence-Aware Subword Packing with 0.0% silent truncation, and controlled 3-arm ablation on Dev set.",
        "artifacts": [
            "part1b_rigorous_chunking_study.json",
            "part1b_chunking_study_dev.json",
            "bm25_four_tokenizers_dev.json",
            "bm25_tokenizer_dev_results.json",
        ],
        "key_metrics": {
            "Sentence-Aware Silent Truncation": "0.0% (vs 29.0% for 1400-char sliding window on 256-cap MiniLM)",
            "Sentence-Aware Dev nDCG@4": "0.4628 (MRR@5 = 0.5483, Hit@5 = 65.6%)",
            "Naive Midpoint Split Degradation": "-0.0379 nDCG@4 (p = 0.0060* statistically significant loss, +29% pool inflation)",
            "Chunk Count Stability": "1,086 sentence-aware chunks (vs 1,418 for naive midpoint)",
        },
    },
    "phase_3_embedding": {
        "title": "Phase 3: Dense Representation & Embedding Model Selection",
        "description": "Evidence Containment calibration (tau*=0.55), FastEmbed ONNX vs PyTorch FP32 parity (1.00000 cos sim), Dev candidate model comparison, unblinded held-out benchmark on 48 papers selecting intfloat/e5-small-v2 as official champion (+0.1252 nDCG@4, Holm-significant), direct pairwise E5 vs BGE cluster bootstrap, and high-power QASPER scaling to 160 papers / 487 queries (>= 82.5% power).",
        "artifacts": [
            "held_out_final_benchmark_as_is.json",
            "held_out_final_benchmark_minimal_intervention.json",
            "held_out_final_benchmark_results.json",
            "part2_dev_candidates_results.json",
            "fastembed_parity_results.json",
            "containment_validation_metrics.json",
            "containment_label_queue_labeled.json",
            "expanded_held_out_split.json",
        ],
        "key_metrics": {
            "Champion Dense Model": "intfloat/e5-small-v2 (384-dim FP32, asymmetric passage:/query: prefixes)",
            "Within-Paper nDCG@4": "0.4952 (+0.1252 over MiniLM baseline, p=0.0020* Holm-significant, >4x SESOI)",
            "Within-Paper MRR@5": "0.5446 (Hit@5 = 81.6%, Recall@20 = 0.980)",
            "Cross-Paper nDCG@4": "0.1811 (Hit@5 = 33.3%, only dense model beating BM25)",
            "Direct Head-to-Head vs BGE": "+0.0555 nDCG@4 in favor of E5 (p=0.0750 on N=114; projected p<0.01* on N=487)",
            "Expanded Benchmark Scale": "160 papers, 487 queries (Statistical power >= 82.5% at Delta=0.030)",
        },
    },
    "phase_4_indexing": {
        "title": "Phase 4: Vector Indexing & ANN Retrieval at Scale",
        "description": "Evaluation of Qdrant local embedded mode (SQLite exact scan) against NumPy BLAS cosine oracle across 114 held-out queries (10 warm-up + 5 timed passes, N=570), disclosure of 4.1x filtered search latency penalty in SQLite, transition to standalone Docker Qdrant server (docker-compose.qdrant.yml), Google Colab T4 GPU notebook for 500k distractor vector offload, and true HNSW parameter sweep (M in {16, 32}, ef_construct in {64, 100}, ef in {32, 64, 128}).",
        "artifacts": [
            "step4_indexing_pareto_results.json",
            "step4_hnsw_scale_pareto.json",
        ],
        "key_metrics": {
            "BLAS Exact Parity": "100.0% Exact ID Match on Top-4 and Top-20 across all settings",
            "Max Float32 Score Delta": "2.16 x 10^-7 <= 10^-5 (exact mathematical equivalence)",
            "SQLite File Footprint": "4.43 MB disk footprint, 20.27 MB Python heap (1,119 vectors)",
            "SQLite Latency Penalty": "6.96 ms global P50 vs 29.07 ms filtered P50 (4.1x linear scan penalty)",
            "Standalone Docker Qdrant": "Pinned v1.13.2, 8GB RAM, 4 CPU, ports 6333 REST & 6334 gRPC",
        },
    },
    "phase_6_hybrid_retrieval": {
        "title": "Phase 6: Multi-Stage & Hybrid Retrieval (Dense + BM25 RRF)",
        "description": "Pre-registered evaluation of Reciprocal Rank Fusion (RRF with k_rrf in {20, 60}) and score-normalized convex combination (alpha=0.7) combining semantic dense embeddings (intfloat/e5-small-v2) and exact lexical matching (WordPiece BM25) on 48 held-out papers (114 queries) under strict containment (tau*=0.55).",
        "artifacts": [
            "step6_hybrid_rrf_benchmark.json",
        ],
        "key_metrics": {
            "Primary Hypothesis": "Hybrid RRF captures both semantic paraphrases and exact symbolic tokens",
            "Dense Alone": "nDCG@4 = 0.4952, MRR@5 = 0.5446, Recall@20 = 0.980",
            "Lexical Alone (BM25)": "nDCG@4 = 0.3647, MRR@5 = 0.4266, Recall@20 = 0.775",
            "Production RRF Fusion": "k_rrf = 60 implemented in rag_service.py:301-355",
        },
    },
    "phase_10_citation": {
        "title": "Phase 10: Page Attribution & Citation Verification",
        "description": "Multi-tier PyMuPDF lexical evidence locator mapping retrieved chunks to physical PDF pages, evaluation of page consensus, disclosure of 31.2% pilot citation hallucination rate, and target design for zero-hallucination interactive PDF badges.",
        "artifacts": [
            "page_gold.json",
        ],
        "extra_sources": [
            WORKSPACE_ROOT / "backend" / "data" / "citation_evaluation_results.json",
        ],
        "key_metrics": {
            "Page Agreement (Dual-Engine)": "97.0% consensus across 35 PDFs (132 questions)",
            "Citation Recall": "68.8% on pilot sample",
            "Citation Hallucination Rate": "31.2% pilot hallucination rate (unverified fallbacks)",
            "Target Production Pipeline": "Page citation badges with interactive jump-to-page navigation",
        },
    },
}


def build_phase_structure():
    print("=== ORGANIZING EVALUATION BENCHMARKS & ARTIFACTS BY PHASE ===")
    PHASES_DIR.mkdir(parents=True, exist_ok=True)

    master_rows = []

    for phase_key, spec in PHASE_SPECS.items():
        phase_dir = PHASES_DIR / phase_key
        artifacts_dir = phase_dir / "artifacts"
        phase_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        copied_count = 0

        # Copy canonical artifacts from prepared/
        for fname in spec["artifacts"]:
            src = PREPARED_DIR / fname
            if src.exists():
                dst = artifacts_dir / fname
                shutil.copy2(src, dst)
                copied_count += 1

        # Copy extra sources if specified
        for extra_src in spec.get("extra_sources", []):
            if extra_src.exists():
                dst = artifacts_dir / extra_src.name
                shutil.copy2(extra_src, dst)
                copied_count += 1

        # Generate Phase README.md
        readme_path = phase_dir / "README.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"# {spec['title']}\n\n")
            f.write(f"## 1. Phase Overview\n{spec['description']}\n\n")

            f.write("## 2. Key Empirical Metrics\n")
            f.write("| Metric | Observed Value |\n")
            f.write("| :--- | :--- |\n")
            for m_key, m_val in spec["key_metrics"].items():
                f.write(f"| **{m_key}** | {m_val} |\n")
            f.write("\n")

            f.write("## 3. Serialized Result Artifacts\n")
            f.write(f"Artifacts stored in `eval/phases/{phase_key}/artifacts/`:\n")
            for fname in spec["artifacts"]:
                art_path = artifacts_dir / fname
                status_icon = "🟢" if art_path.exists() else "⏳ (pending run)"
                size_str = f"({art_path.stat().st_size:,} bytes)" if art_path.exists() else ""
                f.write(f"- {status_icon} [`{fname}`]({fname}) {size_str}\n")
            for extra_src in spec.get("extra_sources", []):
                art_path = artifacts_dir / extra_src.name
                status_icon = "🟢" if art_path.exists() else "⏳ (pending run)"
                size_str = f"({art_path.stat().st_size:,} bytes)" if art_path.exists() else ""
                f.write(f"- {status_icon} [`{extra_src.name}`]({extra_src.name}) {size_str}\n")
            f.write("\n")

            f.write("## 4. Associated Scripts & Repositories\n")
            f.write(f"- Master Data Catalog: [`eval/DATA_CATALOG_AND_PROVENANCE.md`](../../DATA_CATALOG_AND_PROVENANCE.md)\n")
            f.write(f"- Master Audit Report: [`eval/RESEARCH_PLAN_IMPLEMENTATION_AUDIT.md`](../../RESEARCH_PLAN_IMPLEMENTATION_AUDIT.md)\n")
            f.write(f"- Independent Review: [`eval/INDEPENDENT_RESEARCH_AUDIT_REVIEW.md`](../../INDEPENDENT_RESEARCH_AUDIT_REVIEW.md)\n")

        print(f"  [OK] {phase_key}: copied {copied_count} artifacts, created {readme_path.relative_to(WORKSPACE_ROOT)}")
        master_rows.append((phase_key, spec["title"], copied_count, spec["key_metrics"]))

    # Generate Master eval/phases/README.md
    master_readme_path = PHASES_DIR / "README.md"
    with open(master_readme_path, "w", encoding="utf-8") as f:
        f.write("# Scientific Document Viewer — Phase-by-Phase Evaluation Index\n\n")
        f.write("This directory contains self-contained benchmark results, artifacts, and documentation organized cleanly by research phase.\n\n")
        f.write("| Phase | Title | Artifact Count | Primary Result |\n")
        f.write("| :--- | :--- | :---: | :--- |\n")
        for p_key, p_title, a_cnt, metrics in master_rows:
            first_m = list(metrics.items())[0] if metrics else ("Status", "Complete")
            f.write(f"| [`{p_key}`]({p_key}/README.md) | **{p_title}** | {a_cnt} files | {first_m[0]}: {first_m[1]} |\n")
        f.write("\n---\n")
        f.write("## Directory Architecture\n```\n")
        f.write("eval/phases/\n")
        for p_key, _, _, _ in master_rows:
            f.write(f"├── {p_key}/\n")
            f.write(f"│   ├── README.md\n")
            f.write(f"│   └── artifacts/\n")
        f.write("```\n")

    print(f"\n[SUCCESS] Generated Master Phase Index: {master_readme_path.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    build_phase_structure()
