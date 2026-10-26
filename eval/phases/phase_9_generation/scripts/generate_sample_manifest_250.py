#!/usr/bin/env python3
"""
Generate the Frozen 250-Paper / 500-Question Evaluation Manifest (eval_sample_manifest_500q.json).

Protocol: eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md (Section 4.3)
Sampling Seed: 42
Target: K = 250 papers, m = 2 questions/paper -> N = 500 questions (1,500 model outputs)
Standby Queue: 50 pre-registered reserve papers (indices 250..299 of shuffle)
"""

import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Workspace paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
TRAIN_DATA_PATH = WORKSPACE_ROOT / "eval" / "data" / "qasper_official" / "qasper-train-v0.3.json"
RQ3_SPLIT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "expanded_held_out_split.json"
OUTPUT_MANIFEST_PATH = WORKSPACE_ROOT / "eval" / "phases" / "phase_9_generation" / "artifacts" / "eval_sample_manifest_500q.json"


def get_canonical_answer(answer_info: Dict[str, Any]) -> Tuple[str, str]:
    """
    Extract canonical answer string and answer type matching official qasper_evaluator.py.
    """
    if answer_info.get("extractive_spans"):
        spans = [s.strip() for s in answer_info["extractive_spans"] if isinstance(s, str) and s.strip()]
        if spans:
            return ", ".join(spans), "extractive"

    if answer_info.get("free_form_answer"):
        ff = answer_info["free_form_answer"].strip()
        if ff:
            return ff, "abstractive"

    if answer_info.get("yes_no") is True:
        return "Yes", "boolean"

    if answer_info.get("yes_no") is False:
        return "No", "boolean"

    return "", "none"


def is_atomic_eligible(qa: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]], List[str]]:
    """
    Determine if a question satisfies atomic joint grounding:
    At least one annotator provides BOTH a non-empty usable reference answer AND >= 1 non-float text evidence paragraph.
    Returns (is_eligible, references, evidence_list).
    """
    references = []
    text_evidence = []

    for ann in qa.get("answers", []):
        ans = ann.get("answer", {})
        if ans.get("unanswerable", False):
            continue

        # Extract non-float text evidence
        ev_paragraphs = [
            t.strip() for t in ans.get("evidence", [])
            if isinstance(t, str) and not t.startswith("FLOAT SELECTED") and t.strip()
        ]

        ans_str, ans_type = get_canonical_answer(ans)

        # Atomic joint grounding: BOTH answer string and evidence in same annotation object
        if ans_str and ev_paragraphs:
            references.append({
                "worker_id": ann.get("worker_id", "unknown"),
                "answer": ans_str,
                "type": ans_type
            })
            for ev in ev_paragraphs:
                if ev not in text_evidence:
                    text_evidence.append(ev)

    return (len(references) > 0), references, text_evidence


def generate_manifest(
    train_data_path: Path = TRAIN_DATA_PATH,
    rq3_split_path: Path = RQ3_SPLIT_PATH,
    seed: int = 42,
    target_k: int = 250,
    standby_k: int = 50,
    m: int = 2
) -> Dict[str, Any]:
    print("[+] Loading official QASPER Train split...")
    with open(train_data_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)

    print("[+] Loading RQ3 split to exclude previously exposed Train papers...")
    with open(rq3_split_path, "r", encoding="utf-8") as f:
        rq3_pids = set(json.load(f).get("held_out_papers", []))

    # 1. Identify 777 unexposed Train papers
    unexposed_train = {pid: p for pid, p in train_data.items() if pid not in rq3_pids}
    assert len(unexposed_train) == 777, f"Expected 777 unexposed Train papers, got {len(unexposed_train)}"
    print(f"[*] Verified 777 unexposed Train papers (total questions: {sum(len(p['qas']) for p in unexposed_train.values())})")

    # 2. Audit question eligibility across all 777 papers
    paper_eligible_map: Dict[str, List[Dict[str, Any]]] = {}
    question_details_map: Dict[str, Dict[str, Any]] = {}

    single_eligible_pids: List[str] = []
    zero_eligible_pids: List[str] = []

    q_excl_unanswerable: List[str] = []
    q_excl_float_only: List[str] = []
    q_excl_empty_evidence: List[str] = []
    q_eligible_e2e: List[str] = []

    for pid, pdata in unexposed_train.items():
        eligible_qs_for_paper = []
        for qa in pdata.get("qas", []):
            qid = qa["question_id"]
            is_e2e, refs, ev_list = is_atomic_eligible(qa)

            # Categorize non-eligible
            if not is_e2e:
                all_unans = all(a.get("answer", {}).get("unanswerable", False) for a in qa.get("answers", []))
                has_float = any(
                    any(isinstance(t, str) and t.startswith("FLOAT SELECTED") for t in a.get("answer", {}).get("evidence", []))
                    for a in qa.get("answers", [])
                )
                has_no_ev = all(len(a.get("answer", {}).get("evidence", [])) == 0 for a in qa.get("answers", []))

                if all_unans:
                    q_excl_unanswerable.append(qid)
                elif has_float:
                    q_excl_float_only.append(qid)
                else:
                    q_excl_empty_evidence.append(qid)
            else:
                q_eligible_e2e.append(qid)
                eligible_qs_for_paper.append(qa)
                question_details_map[qid] = {
                    "question_id": qid,
                    "paper_arxiv_id": pid,
                    "question_text": qa["question"],
                    "references": refs,
                    "evidence": ev_list,
                    "primary_type": refs[0]["type"] if refs else "unknown",
                    "all_types": list(set(r["type"] for r in refs))
                }

        if len(eligible_qs_for_paper) >= m:
            paper_eligible_map[pid] = eligible_qs_for_paper
        elif len(eligible_qs_for_paper) == 1:
            single_eligible_pids.append(pid)
        else:
            zero_eligible_pids.append(pid)

    print(f"[*] Total End-to-End Eligible Questions: {len(q_eligible_e2e)}")
    print(f"[*] Candidate Pool Papers (m >= 2): {len(paper_eligible_map)}")
    print(f"[*] Papers with m == 1 eligible question: {len(single_eligible_pids)}")
    print(f"[*] Papers with m == 0 eligible questions: {len(zero_eligible_pids)}")

    assert len(q_eligible_e2e) == 1729, f"Expected 1729 eligible questions, got {len(q_eligible_e2e)}"
    assert len(paper_eligible_map) == 487, f"Expected 487 candidate papers, got {len(paper_eligible_map)}"
    assert len(single_eligible_pids) == 226, f"Expected 226 single-question papers, got {len(single_eligible_pids)}"
    assert len(zero_eligible_pids) == 64, f"Expected 64 zero-question papers, got {len(zero_eligible_pids)}"

    # 3. Stable sorting of candidate papers
    candidate_pids = sorted(paper_eligible_map.keys())

    # 4. Deterministic shuffle
    rng = random.Random(seed)
    shuffled_pids = list(candidate_pids)
    rng.shuffle(shuffled_pids)

    primary_pids = sorted(shuffled_pids[:target_k])
    standby_pids = shuffled_pids[target_k:target_k + standby_k]
    residual_pids = shuffled_pids[target_k + standby_k:]

    assert len(primary_pids) == 250
    assert len(standby_pids) == 50
    assert len(residual_pids) == 187

    # 5. Question selection for primary papers
    selected_eval_items: List[Dict[str, Any]] = []
    selected_qids: Set[str] = set()

    for pid in primary_pids:
        q_pool = sorted(paper_eligible_map[pid], key=lambda x: x["question_id"])
        sub_seed = seed + int(hashlib.sha256(pid.encode()).hexdigest()[:8], 16)
        paper_rng = random.Random(sub_seed)
        chosen_qas = sorted(paper_rng.sample(q_pool, m), key=lambda x: x["question_id"])

        for qa in chosen_qas:
            qid = qa["question_id"]
            selected_qids.add(qid)
            details = question_details_map[qid]

            selected_eval_items.append({
                "item_index": len(selected_eval_items) + 1,
                "paper_arxiv_id": pid,
                "paper_title": unexposed_train[pid].get("title", ""),
                "question_id": qid,
                "question_text": qa["question"],
                "question_type": details["primary_type"],
                "all_question_types": details["all_types"],
                "ground_truth_references": details["references"],
                "ground_truth_evidence": details["evidence"],
                "raw_answers": qa.get("answers", []),
                "eligibility_status": "ELIGIBLE_E2E"
            })

    assert len(selected_eval_items) == 500, f"Expected 500 selected items, got {len(selected_eval_items)}"
    assert len(selected_qids) == 500, f"Expected 500 unique question IDs, got {len(selected_qids)}"

    # 6. Pre-select questions for standby reserve papers (to guarantee deterministic reserve replacements if needed)
    standby_queue_records: List[Dict[str, Any]] = []
    for rank_idx, s_pid in enumerate(standby_pids):
        sq_pool = sorted(paper_eligible_map[s_pid], key=lambda x: x["question_id"])
        s_sub_seed = seed + int(hashlib.sha256(s_pid.encode()).hexdigest()[:8], 16)
        s_rng = random.Random(s_sub_seed)
        s_chosen_qas = sorted(s_rng.sample(sq_pool, m), key=lambda x: x["question_id"])

        s_items = []
        for qa in s_chosen_qas:
            qid = qa["question_id"]
            s_details = question_details_map[qid]
            s_items.append({
                "question_id": qid,
                "question_text": qa["question"],
                "question_type": s_details["primary_type"],
                "ground_truth_references": s_details["references"],
                "ground_truth_evidence": s_details["evidence"]
            })

        standby_queue_records.append({
            "standby_rank": rank_idx + 1,
            "shuffle_index": target_k + rank_idx,
            "paper_arxiv_id": s_pid,
            "paper_title": unexposed_train[s_pid].get("title", ""),
            "preselected_questions": s_items
        })

    # 7. Identify human review sample (Option A: 20 questions, stride 25: items 1, 26, 51, ..., 476)
    human_review_option_a = [
        {
            "human_review_index": idx + 1,
            "manifest_item_index": (idx * 25) + 1,
            "paper_arxiv_id": selected_eval_items[idx * 25]["paper_arxiv_id"],
            "question_id": selected_eval_items[idx * 25]["question_id"],
            "question_text": selected_eval_items[idx * 25]["question_text"]
        }
        for idx in range(20)
    ]

    # 8. Build exhaustive Exclusion Manifest
    # Primary unselected questions
    q_unselected_primary = []
    for pid in primary_pids:
        for qa in paper_eligible_map[pid]:
            if qa["question_id"] not in selected_qids:
                q_unselected_primary.append(qa["question_id"])

    # Standby questions
    q_standby_pool = [qa["question_id"] for pid in standby_pids for qa in paper_eligible_map[pid]]

    # Residual pool questions
    q_residual_pool = [qa["question_id"] for pid in residual_pids for qa in paper_eligible_map[pid]]

    # Single-eligible questions
    q_single_eligible = [qa["question_id"] for pid in single_eligible_pids for qa in unexposed_train[pid]["qas"] if qa["question_id"] in q_eligible_e2e]

    total_accounted_qs = (
        len(selected_qids) +
        len(q_unselected_primary) +
        len(q_standby_pool) +
        len(q_residual_pool) +
        len(q_single_eligible) +
        len(q_excl_unanswerable) +
        len(q_excl_float_only) +
        len(q_excl_empty_evidence)
    )
    assert total_accounted_qs == 2154, f"Expected 2154 accounted questions, got {total_accounted_qs}"

    exclusion_manifest = {
        "summary": {
            "total_unexposed_train_papers": 777,
            "total_unexposed_train_questions": 2154,
            "selected_primary_papers_count": len(primary_pids),
            "selected_primary_questions_count": len(selected_qids),
            "standby_reserve_papers_count": len(standby_pids),
            "standby_reserve_questions_count": len(q_standby_pool),
            "residual_candidate_papers_count": len(residual_pids),
            "residual_candidate_questions_count": len(q_residual_pool),
            "unselected_primary_questions_count": len(q_unselected_primary),
            "single_eligible_papers_count": len(single_eligible_pids),
            "single_eligible_questions_count": len(q_single_eligible),
            "zero_eligible_papers_count": len(zero_eligible_pids),
            "strictly_unanswerable_questions_count": len(q_excl_unanswerable),
            "float_only_evidence_questions_count": len(q_excl_float_only),
            "empty_evidence_questions_count": len(q_excl_empty_evidence),
            "accounting_checksum_parity": "EXACT_2154_PARITY"
        },
        "exclusion_codes_paper_level": {
            "EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS": {
                "count": len(single_eligible_pids),
                "paper_ids": single_eligible_pids
            },
            "EXCL_ZERO_ELIGIBLE_QUESTIONS": {
                "count": len(zero_eligible_pids),
                "paper_ids": zero_eligible_pids
            },
            "STANDBY_RESERVE_PAPERS": {
                "count": len(standby_pids),
                "paper_ids": standby_pids
            },
            "RESIDUAL_UNSELECTED_CANDIDATE_PAPERS": {
                "count": len(residual_pids),
                "paper_ids": residual_pids
            }
        },
        "exclusion_codes_question_level": {
            "EXCL_STRICTLY_UNANSWERABLE": {
                "count": len(q_excl_unanswerable),
                "description": "All annotators marked unanswerable: true"
            },
            "EXCL_FLOAT_ONLY_EVIDENCE": {
                "count": len(q_excl_float_only),
                "description": "Evidence consists solely of figure/table floats (FLOAT SELECTED) with no body text"
            },
            "EXCL_EMPTY_EVIDENCE": {
                "count": len(q_excl_empty_evidence),
                "description": "Evidence list is empty or whitespace"
            },
            "EXCL_UNSELECTED_SAME_PAPER": {
                "count": len(q_unselected_primary),
                "description": "Eligible question in selected primary paper not chosen by deterministic sub-seed"
            },
            "EXCL_STANDBY_RESERVE_QUESTION": {
                "count": len(q_standby_pool),
                "description": "Question belongs to standby reserve paper"
            },
            "EXCL_RESIDUAL_CANDIDATE_QUESTION": {
                "count": len(q_residual_pool),
                "description": "Question belongs to residual unselected candidate paper"
            },
            "EXCL_SINGLE_ELIGIBLE_PAPER_QUESTION": {
                "count": len(q_single_eligible),
                "description": "Question belongs to paper with only 1 eligible question (ineligible for m=2 design)"
            }
        }
    }

    # Stratification distribution summary
    type_counts = {"extractive": 0, "abstractive": 0, "boolean": 0}
    for item in selected_eval_items:
        t = item["question_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    manifest = {
        "manifest_metadata": {
            "manifest_name": "RQ5 LLM Generation Confirmatory Evaluation Frozen Manifest (250 Papers / 500 Questions)",
            "version": "1.0.0",
            "generation_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "protocol_document": "eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md",
            "provenance_registry": "eval/experiment_provenance_registry.json",
            "seed": seed,
            "target_papers_k": target_k,
            "questions_per_paper_m": m,
            "total_questions_n": len(selected_eval_items),
            "standby_reserve_papers_k": standby_k,
            "candidate_pool_papers_count": len(candidate_pids),
            "unexposed_train_reservoir_papers_count": len(unexposed_train),
            "stratification_distribution": {
                "extractive": {
                    "count": type_counts.get("extractive", 0),
                    "percentage": round(100.0 * type_counts.get("extractive", 0) / len(selected_eval_items), 2)
                },
                "abstractive": {
                    "count": type_counts.get("abstractive", 0),
                    "percentage": round(100.0 * type_counts.get("abstractive", 0) / len(selected_eval_items), 2)
                },
                "boolean": {
                    "count": type_counts.get("boolean", 0),
                    "percentage": round(100.0 * type_counts.get("boolean", 0) / len(selected_eval_items), 2)
                }
            },
            "approved_human_review_option_a": {
                "stride": 25,
                "sampled_questions_count": 20,
                "models_to_evaluate": ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"],
                "total_model_answers_to_review": 60,
                "review_items": human_review_option_a
            },
            "standby_queue": standby_queue_records,
            "replacement_log": []
        },
        "selected_eval_items": selected_eval_items,
        "exclusion_manifest": exclusion_manifest
    }

    return manifest


def main():
    print("=" * 70)
    print("  RQ5 FROZEN EVALUATION MANIFEST GENERATOR (STAGE C3)")
    print("=" * 70)

    manifest = generate_manifest()

    # Serialize without sha256 first
    manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest["manifest_metadata"]["manifest_sha256"] = manifest_sha256

    OUTPUT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n[+] Manifest successfully generated and frozen at:")
    print(f"    {OUTPUT_MANIFEST_PATH}")
    print(f"[*] Manifest SHA-256 Checksum: {manifest_sha256}")
    print(f"[*] Total Selected Items: {len(manifest['selected_eval_items'])}")
    print(f"[*] Total Primary Papers: {manifest['manifest_metadata']['target_papers_k']}")
    print(f"[*] Total Standby Papers: {manifest['manifest_metadata']['standby_reserve_papers_k']}")
    print(f"[*] Distribution: {manifest['manifest_metadata']['stratification_distribution']}")
    print(f"[*] Human Review Option A: {len(manifest['manifest_metadata']['approved_human_review_option_a']['review_items'])} questions (60 model answers)")
    print("=" * 70)


if __name__ == "__main__":
    main()
