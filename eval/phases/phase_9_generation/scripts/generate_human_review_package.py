"""
Stage C7: Generation of the Blinded Human Faithfulness Review Package (RQ5).

Extracts the frozen 20-question review sample (Option A: Stride-25 from the 500-question manifest),
retrieves the exact inference outputs from the frozen checkpoint for all three models
(llama3.2:3b, llama3.2:1b, qwen2.5:0.5b), applies deterministic blinding with random seed 42,
and outputs a complete, reviewer-ready audit package with empty annotation fields.

Zero live inference calls are performed. Frozen manifest and checkpoint are strictly read-only.
"""

import csv
from datetime import datetime, timezone
import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import sys
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PHASE9_DIR = SCRIPT_DIR.parent
WORKSPACE_ROOT = PHASE9_DIR.parent.parent.parent
ARTIFACTS_DIR = PHASE9_DIR / "artifacts"
PACKAGE_DIR = ARTIFACTS_DIR / "human_faithfulness_review"

MANIFEST_PATH = ARTIFACTS_DIR / "eval_sample_manifest_500q.json"
CHECKPOINT_PATH = ARTIFACTS_DIR / "rq5_inference_checkpoint.jsonl"

TARGET_MANIFEST_SHA256 = "f411670c7b360f72d5ecb457758011fd3af5058df43c294e95ff27c0b4d498b5"
TARGET_CHECKPOINT_SHA256 = "b53166efe4e8f27e34fd9f3c6efc6816214f8f2ff374682ada0f67cb030eb4b4"

CANDIDATE_MODELS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"]
BLIND_LABELS = ["Model_Alpha", "Model_Beta", "Model_Gamma"]
BLINDING_SEED = 42
SAMPLE_STRIDE = 25
SAMPLE_COUNT = 20


def compute_sha256(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_source_integrity():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")
    if not CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT_PATH}")

    man_hash = compute_sha256(MANIFEST_PATH)
    chk_hash = compute_sha256(CHECKPOINT_PATH)

    if man_hash != TARGET_MANIFEST_SHA256:
        raise ValueError(f"Manifest SHA-256 mismatch!\n  Expected: {TARGET_MANIFEST_SHA256}\n  Actual:   {man_hash}")
    if chk_hash != TARGET_CHECKPOINT_SHA256:
        raise ValueError(f"Checkpoint SHA-256 mismatch!\n  Expected: {TARGET_CHECKPOINT_SHA256}\n  Actual:   {chk_hash}")

    print(f"[+] Verified Manifest SHA-256: {man_hash}")
    print(f"[+] Verified Checkpoint SHA-256: {chk_hash}")


def main():
    print("=" * 80)
    print("STAGE C7: GENERATING BLINDED HUMAN FAITHFULNESS REVIEW PACKAGE (RQ5)")
    print("=" * 80)

    # 1. Verify inputs
    verify_source_integrity()
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Load manifest
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest_items = manifest_data["selected_eval_items"]
    assert len(manifest_items) == 500, f"Expected 500 manifest items, found {len(manifest_items)}"

    # 3. Load checkpoint
    checkpoint_records: Dict[Tuple[str, int], Dict[str, Any]] = {}
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            rec = json.loads(line_str)
            key = (rec["model"], rec["item_index"])
            checkpoint_records[key] = rec
    assert len(checkpoint_records) == 1500, f"Expected 1500 checkpoint records, found {len(checkpoint_records)}"

    # 4. Extract Stride-25 Review Sample (Option A: 20 questions)
    stride_indices_0 = [i * SAMPLE_STRIDE for i in range(SAMPLE_COUNT)]
    stride_item_indices_1 = [idx + 1 for idx in stride_indices_0]
    selected_manifest_items = [manifest_items[idx] for idx in stride_indices_0]

    print(f"\n[+] Selected {len(selected_manifest_items)} review questions via Stride-25:")
    print(f"    Zero-based manifest indices: {stride_indices_0}")
    print(f"    One-based manifest item_indices: {stride_item_indices_1}")

    # 5. Deterministic Blinding & Counterbalancing across models
    # Candidate models (K=3) have 3! = 6 unique permutations.
    # To achieve balanced counterbalancing across all 20 review items:
    # 3 complete 6-permutation blocks (18 items, exactly 6 per position for each model),
    # plus the complementary pair (P1, P2) which ensures each model appears either 6 or 7 times
    # in each position (max delta = 1 across any cell, column sums = 20, row sums = 20):
    #   llama3.2:3b:   Alpha=7, Beta=7, Gamma=6 (Total=20)
    #   llama3.2:1b:   Alpha=7, Beta=6, Gamma=7 (Total=20)
    #   qwen2.5:0.5b:  Alpha=6, Beta=7, Gamma=7 (Total=20)
    all_perms = list(itertools.permutations(CANDIDATE_MODELS))
    p1 = (CANDIDATE_MODELS[0], CANDIDATE_MODELS[2], CANDIDATE_MODELS[1])  # (3b, 0.5b, 1b)
    p2 = (CANDIDATE_MODELS[1], CANDIDATE_MODELS[0], CANDIDATE_MODELS[2])  # (1b, 3b, 0.5b)
    balanced_permutations = all_perms * 3 + [p1, p2]  # exactly 20 permutations
    # Deterministically shuffle the assignment across the 20 review items to avoid predictable ordering
    random.Random(BLINDING_SEED).shuffle(balanced_permutations)

    review_items_data: List[Dict[str, Any]] = []
    restricted_mapping: List[Dict[str, Any]] = []
    machine_template_records: List[Dict[str, Any]] = []

    pos_distribution: Dict[str, Dict[str, int]] = {m: {lbl: 0 for lbl in BLIND_LABELS} for m in CANDIDATE_MODELS}

    for q_idx, item in enumerate(selected_manifest_items, start=1):
        review_item_id = f"REV-{q_idx:02d}"
        item_index = item["item_index"]
        qid = item["question_id"]
        pid = item["paper_arxiv_id"]
        title = item.get("paper_title", "Scientific Document")
        q_text = item["question_text"]
        context_text = "\n\n".join(item["ground_truth_evidence"])

        # Counterbalanced model ordering for this question
        shuffled_models = list(balanced_permutations[q_idx - 1])

        blind_to_model = dict(zip(BLIND_LABELS, shuffled_models))
        model_to_blind = {m: lbl for lbl, m in blind_to_model.items()}

        answers_for_review: Dict[str, Dict[str, Any]] = {}

        for blind_lbl in BLIND_LABELS:
            actual_model = blind_to_model[blind_lbl]
            pos_distribution[actual_model][blind_lbl] += 1

            chk_key = (actual_model, item_index)
            if chk_key not in checkpoint_records:
                raise KeyError(f"Missing checkpoint record for {chk_key}")
            raw_rec = checkpoint_records[chk_key]

            answers_for_review[blind_lbl] = {
                "blind_label": blind_lbl,
                "answer_text": raw_rec["prediction"],
            }

            # Machine-readable record (reviewer-facing template with blank annotations)
            machine_template_records.append({
                "review_item_id": review_item_id,
                "manifest_item_index": item_index,
                "question_id": qid,
                "paper_arxiv_id": pid,
                "blind_label": blind_lbl,
                "question_text": q_text,
                "context_text": context_text,
                "model_answer": raw_rec["prediction"],
                "primary_label": "",
                "secondary_label": "",
                "supporting_evidence": "",
                "reviewer_notes": "",
            })

            # Restricted mapping record (internal audit metadata)
            restricted_mapping.append({
                "review_item_id": review_item_id,
                "manifest_item_index": item_index,
                "question_id": qid,
                "paper_arxiv_id": pid,
                "blind_label": blind_lbl,
                "actual_model": actual_model,
                "checkpoint_data": {
                    "is_refusal": raw_rec.get("is_refusal"),
                    "token_f1": raw_rec.get("token_f1"),
                    "token_precision": raw_rec.get("token_precision"),
                    "token_recall": raw_rec.get("token_recall"),
                    "automated_containment_proxy": raw_rec.get("automated_containment_proxy"),
                    "latency_s": raw_rec.get("latency_s"),
                    "tokens_per_second": raw_rec.get("tokens_per_second"),
                    "timestamp_utc": raw_rec.get("timestamp_utc"),
                }
            })

        review_items_data.append({
            "review_item_id": review_item_id,
            "manifest_item_index": item_index,
            "question_id": qid,
            "paper_arxiv_id": pid,
            "paper_title": title,
            "question_text": q_text,
            "context_text": context_text,
            "blinded_answers": answers_for_review,
        })

    print("\n[+] Blind Label Position Distribution (Seed 42):")
    for m in CANDIDATE_MODELS:
        counts = pos_distribution[m]
        print(f"    {m:15s}: Alpha={counts['Model_Alpha']:2d}, Beta={counts['Model_Beta']:2d}, Gamma={counts['Model_Gamma']:2d} (Total={sum(counts.values())})")

    # 6. Generate Deliverable A: Reviewer-Facing Markdown Sheet
    review_doc_path = PACKAGE_DIR / "HUMAN_FAITHFULNESS_REVIEW_GUIDE_AND_SHEET.md"
    generate_reviewer_markdown_doc(review_items_data, review_doc_path)
    print(f"\n[+] Saved Reviewer Document: {review_doc_path}")

    # 7. Generate Deliverable B: Machine-Readable Templates (CSV and JSONL)
    csv_template_path = PACKAGE_DIR / "faithfulness_annotation_template_60a.csv"
    jsonl_template_path = PACKAGE_DIR / "faithfulness_annotation_template_60a.jsonl"
    generate_machine_templates(machine_template_records, csv_template_path, jsonl_template_path)
    print(f"[+] Saved CSV Annotation Template: {csv_template_path}")
    print(f"[+] Saved JSONL Annotation Template: {jsonl_template_path}")

    # 8. Generate Deliverable C: Restricted Model-Label Mapping
    mapping_path = PACKAGE_DIR / "restricted_model_label_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "description": "RESTRICTED AUDIT METADATA - DO NOT SHARE WITH HUMAN REVIEWER BEFORE AUDIT COMPLETION",
                "purpose": "Decodes blind labels (Model_Alpha, Model_Beta, Model_Gamma) to actual models for RQ5 faithfulness evaluation",
                "blinding_seed": BLINDING_SEED,
                "total_records": len(restricted_mapping),
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
            },
            "records": restricted_mapping
        }, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved Restricted Mapping File: {mapping_path}")

    # 9. Generate Deliverable D: Sampling and Integrity Manifest
    integrity_manifest_path = PACKAGE_DIR / "sampling_and_integrity_manifest.json"
    script_sha256 = compute_sha256(Path(__file__))
    with open(integrity_manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "protocol_name": "RQ5 Blinded Human Faithfulness Audit (Option A: 20 Questions / 60 Answers)",
            "status": "PREPARED_FOR_HUMAN_ANNOTATION",
            "generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "generation_script": str(Path(__file__).resolve().relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
            "generation_script_sha256": script_sha256,
            "sampling_parameters": {
                "sampling_rule": "Option A: Stride-25 from frozen 500-question manifest",
                "sample_count_questions": SAMPLE_COUNT,
                "total_answers_evaluated": len(machine_template_records),
                "zero_based_manifest_indices": stride_indices_0,
                "one_based_manifest_item_indices": stride_item_indices_1,
                "models_evaluated": CANDIDATE_MODELS,
                "blinding_seed": BLINDING_SEED,
                "blinding_procedure": "Latin-square balanced counterbalancing across 3-model permutations (3 blocks of 6 + complementary pair, deterministically shuffled with seed 42)",
                "blind_labels": BLIND_LABELS,
                "position_distribution": pos_distribution,
            },
            "frozen_source_checksums": {
                "manifest_path": str(MANIFEST_PATH.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "manifest_sha256": TARGET_MANIFEST_SHA256,
                "checkpoint_path": str(CHECKPOINT_PATH.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "checkpoint_sha256": TARGET_CHECKPOINT_SHA256,
            },
            "output_artifacts": {
                "reviewer_guide_md": str(review_doc_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "annotation_template_csv": str(csv_template_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "annotation_template_jsonl": str(jsonl_template_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
                "restricted_mapping_json": str(mapping_path.relative_to(WORKSPACE_ROOT)).replace("\\", "/"),
            },
            "validation_status": "PENDING_FORMAL_VALIDATION"
        }, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved Sampling & Integrity Manifest: {integrity_manifest_path}")

    print("\n[PASS] Human Review Package generation complete!")


def generate_reviewer_markdown_doc(items: List[Dict[str, Any]], out_path: Path):
    lines = [
        "# RQ5 Qualitative Faithfulness Review: Reviewer Guide & Annotation Instrument",
        "",
        "> [!IMPORTANT]",
        "> **Reviewer Confidentiality & Blinding Directive:**",
        "> This document is a **blinded qualitative evaluation instrument**. Each question presents three candidate answers",
        "> labeled anonymously as `Model_Alpha`, `Model_Beta`, and `Model_Gamma`. Candidate identities, parameter counts,",
        "> latency, throughput, and automated Token F1 scores have been strictly removed to eliminate reviewer bias.",
        "> **Do NOT seek or infer model identities during annotation.**",
        "",
        "---",
        "",
        "## 1. Review Objective & Evaluation Principles",
        "",
        "The objective of this qualitative audit is to assess whether generated answers are **semantically faithful and factually grounded**",
        "in the supplied evidence context. This audit directly complements automated Answer Token F1 (which measures lexical precision/recall",
        "against reference answers) by evaluating whether models respect the strict grounding constraint (NFR-03).",
        "",
        "### Key Principles for Human Reviewers:",
        "1. **Strict Context Bound:** Judge each answer **exclusively against the provided context**. Do not use external domain knowledge or web searches to verify facts. If a claim is true in real life but absent from the text, it is ungrounded.",
        "2. **Decompose into Atomic Claims:** For complex multi-sentence responses, identify the core verifiable factual propositions.",
        "3. **Distinguish Fabrication vs. Contradiction:**",
        "   - **Unsupported:** Claims asserting details not mentioned in or entailed by the context, but not conflicting with it (extrapolation).",
        "   - **Contradicted:** Claims directly conflicting with or negating explicit statements in the context (inverted numbers, reversed relations).",
        "4. **Fair Evaluation of Refusals (Abstentions):**",
        "   - If the context genuinely lacks the required evidence, the refusal (*'The document does not contain sufficient...'*) is **faithful and correct** (`REFUSAL_VALID`).",
        "   - If the context contains clear evidence to answer the question, but the model refuses, it is an **abstention defect** (`MISSING_INFO - UNJUSTIFIED_REFUSAL`).",
        "5. **Incomplete Answers:** If a model answers but omits crucial qualifiers, condition bounds, or parameters present in the context, classify as `MISSING_INFO - PARTIAL`.",
        "",
        "---",
        "",
        "## 2. Canonical Annotation Rubric & Precedence Rules",
        "",
        "### Protocol Authority:",
        "This rubric and precedence hierarchy are directly codified in Section 6.4 and Section 6.5 of the canonical evaluation protocol ([`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)).",
        "",
        "For each answer, assign **one Primary Holistic Label** and note any secondary aspects:",
        "",
        "| Primary Label | Operational Definition | Scoring Meaning |",
        "| :--- | :--- | :---: |",
        "| **`SUPPORTED`** | All substantive claims are directly entailed by the supplied context. Free of unsupported extrapolations, contradictions, or core omissions. | Fully Faithful (100% Credit) |",
        "| **`REFUSAL_VALID`** | The model emitted an explicit refusal, and human audit confirms the context genuinely lacked sufficient information to answer. | Valid Abstention (Faithful) |",
        "| **`MISSING_INFO - PARTIAL`** | The answer is partially grounded but omits crucial contextual qualifiers, bounds, or findings necessary to answer accurately. | Incomplete Answer (Partial Defect) |",
        "| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | The model emitted the refusal message despite the supplied context containing sufficient evidence to answer. | False Abstention (Coverage Defect) |",
        "| **`UNSUPPORTED`** | At least one substantive claim asserts factual details neither stated nor entailed by the context (ungrounded hallucination/extrapolation). | Ungrounded / Hallucinated |",
        "| **`CONTRADICTED`** | At least one substantive claim directly conflicts with or negates explicit statements in the context. | Factually Contradicted |",
        "",
        "### Conflict Precedence Rule (Multiple Defects in One Answer):",
        "When an answer exhibits multiple competing issues, assign the primary label by strict failure precedence (as codified in Section 6.5 of `DEC03_FINAL_EVALUATION_PROTOCOL.md`):",
        "$$\\mathbf{CONTRADICTED} > \\mathbf{UNSUPPORTED} > \\mathbf{MISSING\\_INFO\\ -\\ UNJUSTIFIED\\_REFUSAL} > \\mathbf{MISSING\\_INFO\\ -\\ PARTIAL} > \\mathbf{REFUSAL\\_VALID} > \\mathbf{SUPPORTED}$$",
        "",
        "### Mandatory Non-Erasure Directive (Preserving Diagnostic Nuance):",
        "Assigning a primary label based on the precedence hierarchy must **NOT** erase other observed defects or grounded elements. Reviewers must explicitly record:",
        "1. In **Claim-by-Claim Breakdown**: List each extracted atomic proposition and label it individually (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`).",
        "2. In **Supporting Context Quote**: Quote the exact sentence or phrase from the context for any supported or partially supported claim.",
        "3. In **Secondary Label & Reviewer Notes**: Note co-occurring defects (e.g., if an answer contains an unsupported hallucination but also omits crucial context, assign `UNSUPPORTED` as Primary, note `MISSING_INFO - PARTIAL` as Secondary, and explain the omission in notes).",
        "",
        "---",
        "",
        "## 3. Review Items (20 Sampled Questions $\\times$ 3 Blinded Models = 60 Answers)",
        "",
    ]

    for item in items:
        rid = item["review_item_id"]
        midx = item["manifest_item_index"]
        pid = item["paper_arxiv_id"]
        title = item["paper_title"]
        qtxt = item["question_text"]
        ctxt = item["context_text"]
        answers = item["blinded_answers"]

        lines.extend([
            f"### {rid} (Manifest Item #{midx} | Paper: arXiv:{pid})",
            f"**Paper Title:** *{title}*  ",
            f"**Question:** **{qtxt}**",
            "",
            "<details>",
            f"<summary><b>Click to Expand Evidence Context supplied to models ({len(ctxt)} chars)</b></summary>",
            "",
            "```text",
            ctxt,
            "```",
            "</details>",
            "",
            "#### Candidate Answers for Evaluation:",
            "",
        ])

        for lbl in BLIND_LABELS:
            ans_info = answers[lbl]
            ans_text = ans_info["answer_text"]

            quoted_lines = [f"> {line}" if line.strip() else ">" for line in (ans_text.splitlines() if ans_text.strip() else ["*(Empty output)*"])]
            lines.extend([
                f"##### [{rid}] {lbl}:",
                "\n".join(quoted_lines),
                "",
                "- **Primary Label:** `[ ] SUPPORTED  [ ] REFUSAL_VALID  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`",
                "- **Secondary Label (if co-occurring issues exist):** `[ ] NONE  [ ] MISSING_INFO - PARTIAL  [ ] MISSING_INFO - UNJUSTIFIED_REFUSAL  [ ] UNSUPPORTED  [ ] CONTRADICTED`",
                "- **Claim-by-Claim Breakdown:**",
                "  - *Claim 1:*",
                "- **Supporting Context Quote (if supported/partial):**",
                "- **Reviewer Notes & Justification:**",
                "",
            ])

        lines.append("---")

    clean_lines = [l.rstrip() for l in lines]
    out_path.write_text("\n".join(clean_lines).rstrip() + "\n", encoding="utf-8")


def generate_machine_templates(records: List[Dict[str, Any]], csv_path: Path, jsonl_path: Path):
    # CSV
    fieldnames = [
        "review_item_id",
        "manifest_item_index",
        "question_id",
        "paper_arxiv_id",
        "blind_label",
        "question_text",
        "context_text",
        "model_answer",
        "primary_label",
        "secondary_label",
        "supporting_evidence",
        "reviewer_notes"
    ]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    # JSONL
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
