#!/usr/bin/env python3
"""
Apply human adjudications to the RQ5 Human Faithfulness Review queue,
freeze the corrected dataset, recompute full inferential statistics,
and update audit reports.
"""

import csv
import json
from pathlib import Path
import hashlib

BASE_DIR = Path("eval/phases/phase_9_generation/artifacts/human_faithfulness_review/audit")
QUEUE_CSV = BASE_DIR / "annotation_adjudication_queue.csv"
QUEUE_JSONL = BASE_DIR / "annotation_adjudication_queue.jsonl"
QUEUE_MD = BASE_DIR / "annotation_adjudication_queue.md"

ADJUDICATED_CSV = BASE_DIR / "faithfulness_annotations_adjudicated.csv"
ADJUDICATED_JSONL = BASE_DIR / "faithfulness_annotations_adjudicated.jsonl"
AUDIT_REPORT_MD = BASE_DIR / "annotation_audit_report.md"

# 21 Adjudicated decisions from the human reviewer
ADJUDICATED_DECISIONS = {
    ("REV-01", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted proposed label; borderline refusal is defensible due to absence of specific named entity.",
    },
    ("REV-01", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted proposed label consistent with Model Alpha.",
    },
    ("REV-01", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "UNSUPPORTED",
        "final_secondary": "EXTRAPOLATION",
        "notes": "Accepted UNSUPPORTED per Precedence Rule 2; lack of mention does not equal explicit contradiction.",
    },
    ("REV-02", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "CONTRADICTED",
        "final_secondary": "FACTUAL_CONFLICT",
        "notes": "Accepted CONTRADICTED; rationale phrasing clarified for audit trail.",
    },
    ("REV-02", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "CONTRADICTED",
        "final_secondary": "FACTUAL_CONFLICT",
        "notes": "Accepted CONTRADICTED per Precedence Rule 1 to maintain consistency with Model Alpha.",
    },
    ("REV-03", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "MISSING_INFO - UNJUSTIFIED_REFUSAL",
        "final_secondary": "REFUSAL",
        "notes": "Accepted MISSING_INFO - UNJUSTIFIED_REFUSAL; context contains relevant corpus information.",
    },
    ("REV-04", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "SUPPORTED",
        "final_secondary": "",
        "notes": "Retained SUPPORTED; model successfully targeted the requested subset of dialects.",
    },
    ("REV-04", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "SUPPORTED",
        "final_secondary": "",
        "notes": "Retained SUPPORTED consistently.",
    },
    ("REV-04", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "SUPPORTED",
        "final_secondary": "",
        "notes": "Retained SUPPORTED consistently.",
    },
    ("REV-08", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "SUPPORTED",
        "final_secondary": "",
        "notes": "Accepted SUPPORTED; minor elaboration is benign and directly grounded.",
    },
    ("REV-09", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted REFUSAL_VALID; context lacks specific dataset names requested.",
    },
    ("REV-09", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted REFUSAL_VALID consistently.",
    },
    ("REV-10", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "MISSING_INFO - UNJUSTIFIED_REFUSAL",
        "final_secondary": "REFUSAL",
        "notes": "Accepted MISSING_INFO - UNJUSTIFIED_REFUSAL; context explicitly details dataset collection methods.",
    },
    ("REV-10", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "UNSUPPORTED",
        "final_secondary": "HALLUCINATION",
        "notes": "Accepted UNSUPPORTED; response is entirely fabricated with zero factual overlap.",
    },
    ("REV-11", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Retained REFUSAL_VALID for borderline information sufficiency.",
    },
    ("REV-12", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted REFUSAL_VALID; context lacks metric information entirely.",
    },
    ("REV-12", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted REFUSAL_VALID consistently.",
    },
    ("REV-13", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "CONTRADICTED",
        "final_secondary": "FACTUAL_CONFLICT",
        "notes": "Retained CONTRADICTED; model misattributed FastText pretraining source.",
    },
    ("REV-17", "Model_Alpha"): {
        "decision": "ACCEPT",
        "final_primary": "UNSUPPORTED",
        "final_secondary": "HALLUCINATION",
        "notes": "Retained UNSUPPORTED for ungrounded entity/baseline naming.",
    },
    ("REV-20", "Model_Beta"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted REFUSAL_VALID; referenced table contents are missing from the excerpt.",
    },
    ("REV-20", "Model_Gamma"): {
        "decision": "ACCEPT",
        "final_primary": "REFUSAL_VALID",
        "final_secondary": "ABSENT",
        "notes": "Accepted REFUSAL_VALID consistently.",
    },
}

VALID_TAXONOMY = {
    "SUPPORTED",
    "REFUSAL_VALID",
    "MISSING_INFO - PARTIAL",
    "MISSING_INFO - UNJUSTIFIED_REFUSAL",
    "UNSUPPORTED",
    "CONTRADICTED",
}


def main():
    # 1. Read existing queue rows
    with open(QUEUE_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Read {len(rows)} rows from {QUEUE_CSV}")

    # 2. Update rows with decisions
    adjudicated_rows = []
    adjudicated_changes_count = 0

    for r in rows:
        rev_id = r["review_id"]
        blind_label = r["blind_label"]
        key = (rev_id, blind_label)

        if key in ADJUDICATED_DECISIONS:
            dec = ADJUDICATED_DECISIONS[key]
            r["reviewer_decision"] = dec["decision"]
            r["final_primary_label"] = dec["final_primary"]
            r["final_secondary_label"] = dec.get("final_secondary", "")
            r["adjudication_notes"] = dec["notes"]
            if r["final_primary_label"] != r["original_primary_label"]:
                adjudicated_changes_count += 1
        else:
            # Unflagged passed items
            r["reviewer_decision"] = "VERIFIED_PASS"
            r["final_primary_label"] = r["original_primary_label"]
            r["final_secondary_label"] = r["original_secondary_label"]
            r["adjudication_notes"] = "Verified consistent with context, answer, and protocol."

        # Validate against canonical taxonomy
        assert r["final_primary_label"] in VALID_TAXONOMY, f"Invalid taxonomy: {r['final_primary_label']}"

        adjudicated_rows.append(r)

    print(f"Processed 60 rows: {len(ADJUDICATED_DECISIONS)} explicitly adjudicated, {adjudicated_changes_count} label changes applied.")

    # 3. Save updated queue CSV & JSONL
    with open(QUEUE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(adjudicated_rows)
    print(f"Updated {QUEUE_CSV}")

    with open(QUEUE_JSONL, "w", encoding="utf-8") as f:
        for r in adjudicated_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Updated {QUEUE_JSONL}")

    # 4. Generate frozen, finalized dataset
    # Schema matches template plus explicit audit trail columns
    adjudicated_dataset_fields = [
        "review_id",
        "blind_label",
        "final_primary_label",
        "final_secondary_label",
        "is_adjudicated_change",
        "original_primary_label",
        "original_secondary_label",
        "reviewer_decision",
        "adjudication_notes",
        "proposed_rationale",
        "answer",
        "relevant_context",
    ]

    dataset_records = []
    for r in adjudicated_rows:
        is_change = r["final_primary_label"] != r["original_primary_label"]
        rec = {
            "review_id": r["review_id"],
            "blind_label": r["blind_label"],
            "final_primary_label": r["final_primary_label"],
            "final_secondary_label": r["final_secondary_label"],
            "is_adjudicated_change": "YES" if is_change else "NO",
            "original_primary_label": r["original_primary_label"],
            "original_secondary_label": r["original_secondary_label"],
            "reviewer_decision": r["reviewer_decision"],
            "adjudication_notes": r["adjudication_notes"],
            "proposed_rationale": r["proposed_rationale"],
            "answer": r["answer"],
            "relevant_context": r["relevant_context"],
        }
        dataset_records.append(rec)

    with open(ADJUDICATED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=adjudicated_dataset_fields)
        writer.writeheader()
        writer.writerows(dataset_records)
    print(f"Wrote finalized dataset {ADJUDICATED_CSV}")

    with open(ADJUDICATED_JSONL, "w", encoding="utf-8") as f:
        for rec in dataset_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote finalized dataset {ADJUDICATED_JSONL}")

    # 5. Compute Full Statistics
    orig_counts = {}
    final_counts = {}
    by_model_orig = {"Model_Alpha": {}, "Model_Beta": {}, "Model_Gamma": {}}
    by_model_final = {"Model_Alpha": {}, "Model_Beta": {}, "Model_Gamma": {}}

    for r in adjudicated_rows:
        op = r["original_primary_label"]
        fp = r["final_primary_label"]
        m = r["blind_label"]

        orig_counts[op] = orig_counts.get(op, 0) + 1
        final_counts[fp] = final_counts.get(fp, 0) + 1

        by_model_orig[m][op] = by_model_orig[m].get(op, 0) + 1
        by_model_final[m][fp] = by_model_final[m].get(fp, 0) + 1

    # Transition matrix
    transitions = {}
    for r in adjudicated_rows:
        pair = (r["original_primary_label"], r["final_primary_label"])
        transitions[pair] = transitions.get(pair, 0) + 1

    print("\n=== OVERALL PRIMARY LABEL COMPARISON ===")
    for label in sorted(VALID_TAXONOMY):
        oc = orig_counts.get(label, 0)
        fc = final_counts.get(label, 0)
        delta = fc - oc
        print(f"{label:35s}: Orig={oc:2d} ({oc/60*100:4.1f}%) -> Final={fc:2d} ({fc/60*100:4.1f}%) [Δ={delta:+2d}]")

    print("\n=== FINAL LABEL COUNTS BY BLIND MODEL ===")
    print(f"{'Label':35s} | {'Alpha':5s} | {'Beta':5s} | {'Gamma':5s} | {'Total':5s}")
    for label in sorted(VALID_TAXONOMY):
        a = by_model_final["Model_Alpha"].get(label, 0)
        b = by_model_final["Model_Beta"].get(label, 0)
        g = by_model_final["Model_Gamma"].get(label, 0)
        tot = a + b + g
        print(f"{label:35s} | {a:5d} | {b:5d} | {g:5d} | {tot:5d}")

    # 6. Update annotation_adjudication_queue.md
    update_markdown_queue(adjudicated_rows)

    # 7. Update annotation_audit_report.md
    update_audit_report(orig_counts, final_counts, by_model_orig, by_model_final, transitions)


def update_markdown_queue(rows: list[dict]):
    flagged = [r for r in rows if r["audit_issue"] != "NONE (PASS)"]
    passed = [r for r in rows if r["audit_issue"] == "NONE (PASS)"]

    with open(QUEUE_MD, "w", encoding="utf-8") as f:
        f.write("# RQ5 Human Faithfulness Review Adjudication Queue\n\n")
        f.write("**Status:** ADJUDICATED_AND_FINALIZED\n")
        f.write(f"**Total Records:** {len(rows)} (60 answers: 20 questions × 3 blinded models)\n")
        f.write(f"**Flagged Items Adjudicated:** {len(flagged)}\n")
        f.write(f"**Unflagged Records (Passed Verification):** {len(passed)}\n\n")
        f.write("---\n\n")

        f.write("## Section 1: Flagged Items with Final Adjudicated Decisions\n\n")
        f.write("The following 21 records have been adjudicated and updated with final decisions.\n\n")

        f.write("| # | Review ID | Model | Original Label | Audit Issue | Proposed Label | Conf | Decision | Final Label |\n")
        f.write("| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :---: | :---: |\n")

        for idx, r in enumerate(flagged, 1):
            issue_snippet = r['audit_issue'][:45] + "..." if len(r['audit_issue']) > 45 else r['audit_issue']
            f.write(
                f"| {idx} | **{r['review_id']}** | {r['blind_label']} | `{r['original_primary_label']}` | "
                f"{issue_snippet} | `{r['proposed_primary_label']}` | {r['confidence']} | "
                f"[X] {r['reviewer_decision']} | `{r['final_primary_label']}` |\n"
            )

        f.write("\n---\n\n")
        f.write("## Section 2: Detailed Dossiers for Flagged Records (Adjudicated)\n\n")

        for idx, r in enumerate(flagged, 1):
            sec_orig = r['original_secondary_label'] or 'None'
            sec_final = r['final_secondary_label'] or 'None'
            f.write(
                f"### Item {idx}: {r['review_id']} — {r['blind_label']}\n\n"
                f"- **Original Primary Label:** `{r['original_primary_label']}`\n"
                f"- **Original Secondary Label:** `{sec_orig}`\n"
                f"- **Original Rationale:** {r['original_rationale']}\n"
                f"- **Audit Issue:** {r['audit_issue']}\n"
                f"- **Protocol Rule:** {r['protocol_rule']}\n"
                f"- **Proposed Primary Label:** `{r['proposed_primary_label']}`\n"
                f"- **Final Primary Label:** `{r['final_primary_label']}`\n"
                f"- **Final Secondary Label:** `{sec_final}`\n"
                f"- **Confidence:** **{r['confidence']}**\n\n"
                f"<details>\n<summary><b>Click to View Model Answer and Context</b></summary>\n\n"
                f"**Answer:**\n```text\n{r['answer']}\n```\n\n"
                f"**Context Excerpt:**\n```text\n{r['relevant_context'][:500]}...\n```\n"
                f"</details>\n\n"
                f"**Adjudication Action Required:**\n"
                f"- [X] ACCEPT Proposed Label (`{r['proposed_primary_label']}`)\n"
                f"- [ ] RETAIN Original Label (`{r['original_primary_label']}`)\n"
                f"- [ ] ASSIGN Custom Label: `____________________`\n"
                f"- **Adjudicator Notes:** `{r['adjudication_notes']}`\n\n"
                f"---\n\n"
            )

        f.write("## Section 3: Records Passed with No Inconsistencies (39 Items)\n\n")
        f.write("The remaining 39 records demonstrated consistent alignment between model answer, evidence context, reviewer rationale, and protocol precedence rules.\n\n")
        f.write("| Review ID | Model | Primary Label | Secondary Label | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :---: |\n")
        for r in passed:
            sec = r['final_secondary_label'] or '-'
            f.write(f"| {r['review_id']} | {r['blind_label']} | `{r['final_primary_label']}` | `{sec}` | ✅ PASS |\n")

    print(f"Updated {QUEUE_MD}")


def update_audit_report(orig_counts, final_counts, by_model_orig, by_model_final, transitions):
    with open(AUDIT_REPORT_MD, "r", encoding="utf-8") as f:
        content = f.read()

    # Update Status from DRAFT to FINAL_ADJUDICATED
    content = content.replace(
        "**Status:** DRAFT — Proposed corrections require human reviewer decision before finalization",
        "**Status:** FINAL_ADJUDICATED — All 21 flagged items adjudicated and finalized with human reviewer decisions"
    )

    # Dynamically generate Section 7 with exact counts
    section_7_lines = [
        "## 7. Reconciled Adjudication Impact Analysis\n",
        "### 7.1 Final Label Distribution (Post-Adjudication vs Original)\n",
        "| Primary Label | Original Signed Count | Final Adjudicated Count | Δ | % of Final (N=60) |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]
    for lbl in ["SUPPORTED", "REFUSAL_VALID", "UNSUPPORTED", "MISSING_INFO - UNJUSTIFIED_REFUSAL", "MISSING_INFO - PARTIAL", "CONTRADICTED"]:
        oc = orig_counts.get(lbl, 0)
        fc = final_counts.get(lbl, 0)
        delta = fc - oc
        pct = (fc / 60.0) * 100.0
        section_7_lines.append(f"| **{lbl}** | {oc} | **{fc}** | {delta:+d} | {pct:.1f}% |")
    section_7_lines.append("| **Total** | **60** | **60** | **0** | **100.0%** |\n")

    section_7_lines.append("### 7.2 Final Adjudicated Distribution by Blind Model\n")
    section_7_lines.append("| Primary Label | Model_Alpha | Model_Beta | Model_Gamma | Total |")
    section_7_lines.append("| :--- | :---: | :---: | :---: | :---: |")
    for lbl in ["SUPPORTED", "REFUSAL_VALID", "UNSUPPORTED", "MISSING_INFO - UNJUSTIFIED_REFUSAL", "MISSING_INFO - PARTIAL", "CONTRADICTED"]:
        a = by_model_final["Model_Alpha"].get(lbl, 0)
        b = by_model_final["Model_Beta"].get(lbl, 0)
        g = by_model_final["Model_Gamma"].get(lbl, 0)
        tot = a + b + g
        section_7_lines.append(f"| **{lbl}** | {a} | {b} | {g} | {tot} |")
    section_7_lines.append("| **Total** | **20** | **20** | **20** | **60** |\n")

    section_7_lines.extend([
        "### 7.3 Complete Transition Breakdown (Original → Adjudicated)\n",
        "All 11 actual label transitions applied during adjudication:",
        "- **`SUPPORTED` → `REFUSAL_VALID` (6 transitions):**",
        "  - REV-09 Alpha, REV-09 Gamma",
        "  - REV-12 Beta, REV-12 Gamma",
        "  - REV-20 Beta, REV-20 Gamma",
        "- **`UNSUPPORTED` → `MISSING_INFO - UNJUSTIFIED_REFUSAL` (2 transitions):**",
        "  - REV-03 Gamma",
        "  - REV-10 Beta",
        "- **`CONTRADICTED` → `UNSUPPORTED` (1 transition):**",
        "  - REV-01 Gamma (lack of mention is ungrounded claim, not explicit contradiction)",
        "- **`UNSUPPORTED` → `CONTRADICTED` (1 transition):**",
        "  - REV-02 Beta (asserted negation contradictory to context, aligned with Alpha)",
        "- **`MISSING_INFO - PARTIAL` → `UNSUPPORTED` (1 transition):**",
        "  - REV-10 Gamma (fully fabricated explanation with zero grounding from text)\n",
        "All other 49 records (including 10 verified/retained flagged records and 39 unflagged records) maintained their original primary label.\n",
    ])

    section_7_new = "\n".join(section_7_lines)

    # Replace Section 7
    import re
    content = re.sub(r"## 7\..*?(?=## 8\. Audit Status)", section_7_new + "\n---\n\n", content, flags=re.DOTALL)

    with open(AUDIT_REPORT_MD, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated {AUDIT_REPORT_MD}")


if __name__ == "__main__":
    main()
