#!/usr/bin/env python3
"""
Comprehensive parser and auditor for the RQ5 Human Faithfulness Review.
Parses review_and_signed.md and extracts all 60 annotation records,
then performs structural and semantic consistency checks.
"""
import re
import json
import csv
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict

REVIEW_FILE = Path(r"c:\DACNTT\eval\phases\phase_9_generation\artifacts\review_and_signed.md")
OUTPUT_DIR = Path(r"c:\DACNTT\eval\phases\phase_9_generation\artifacts\human_faithfulness_review\audit")

REFUSAL_BOILERPLATE = "The document does not contain sufficient relevant information to answer this question."

VALID_LABELS = [
    "SUPPORTED",
    "REFUSAL_VALID",
    "MISSING_INFO - PARTIAL",
    "MISSING_INFO - UNJUSTIFIED_REFUSAL",
    "UNSUPPORTED",
    "CONTRADICTED",
]

# Precedence index (lower = higher severity)
PRECEDENCE = {
    "CONTRADICTED": 0,
    "UNSUPPORTED": 1,
    "MISSING_INFO - UNJUSTIFIED_REFUSAL": 2,
    "MISSING_INFO - PARTIAL": 3,
    "REFUSAL_VALID": 4,
    "SUPPORTED": 5,
}


def parse_signed_review(filepath: Path) -> list[dict]:
    """Parse every annotation record from the signed review Markdown."""
    text = filepath.read_text(encoding="utf-8")
    records = []

    # Split by REV-NN headers: ### REV-NN
    # Each REV block contains the question context and 3 model answers
    rev_blocks = re.split(r"(?=### REV-\d+\s)", text)

    for block in rev_blocks:
        # Match the REV header
        header_match = re.match(
            r"### (REV-\d+)\s+\(Manifest Item #(\d+)\s*\|\s*Paper:\s*arXiv:([\d.]+)\)",
            block,
        )
        if not header_match:
            continue

        rev_id = header_match.group(1)
        manifest_idx = int(header_match.group(2))
        arxiv_id = header_match.group(3)

        # Extract question
        question_match = re.search(
            r"\*\*Question:\*\*\s*\*\*(.+?)\*\*", block
        )
        question = question_match.group(1).strip() if question_match else ""

        # Extract context (inside <details>...</details>)
        ctx_match = re.search(
            r"```text\s*\n(.*?)```", block, re.DOTALL
        )
        context = ctx_match.group(1).strip() if ctx_match else ""

        # Now extract each model answer block
        # Pattern: ##### [REV-NN] Model_XXX:
        model_blocks = re.split(r"(?=##### \[REV-\d+\]\s+Model_)", block)

        for mblock in model_blocks:
            model_match = re.match(
                r"##### \[(REV-\d+)\]\s+(Model_\w+):", mblock
            )
            if not model_match:
                continue

            check_rev = model_match.group(1)
            blind_label = model_match.group(2)

            # Extract answer (blockquote lines after the header)
            answer_match = re.search(
                r":\s*\n((?:>\s*.+\n?)+)", mblock
            )
            if answer_match:
                raw_answer = answer_match.group(1)
                answer = "\n".join(
                    line.lstrip("> ").strip()
                    for line in raw_answer.strip().split("\n")
                    if line.strip()
                ).strip()
            else:
                answer = ""

            # Extract primary label
            label_match = re.search(
                r"\*\*Primary Label:\*\*\s*`(.+?)`", mblock
            )
            primary_label = ""
            if label_match:
                label_str = label_match.group(1)
                # Find the checked option [X]
                checked = re.findall(r"\[X\]\s*([A-Z][A-Z_ -]+)", label_str)
                if checked:
                    primary_label = checked[0].strip()

            # Extract secondary label if present
            sec_match = re.search(
                r"\*\*Secondary Label.*?:\*\*\s*`(.+?)`", mblock
            )
            secondary_label = ""
            if sec_match:
                sec_str = sec_match.group(1)
                sec_checked = re.findall(r"\[X\]\s*([A-Z][A-Z_ -]+)", sec_str)
                if sec_checked:
                    secondary_label = sec_checked[0].strip()

            # Extract claim-by-claim breakdown (everything after "Claim-by-Claim Breakdown:**" until next field)
            claims_match = re.search(
                r"\*\*Claim-by-Claim Breakdown:\*\*\s*\n(.*?)(?=- \*\*Supporting|\*\*Supporting|$)",
                mblock,
                re.DOTALL,
            )
            claims = claims_match.group(1).strip() if claims_match else ""

            # Extract supporting context quote
            quote_match = re.search(
                r"\*\*Supporting Context Quote.*?\*\*\s*(.*?)(?=\n- \*\*Reviewer|\*\*Reviewer|\n##### |\n---|\Z)",
                mblock,
                re.DOTALL,
            )
            supporting_quote = ""
            if quote_match:
                supporting_quote = quote_match.group(1).strip()
                # Remove leading markdown artifacts
                supporting_quote = re.sub(r"^\s*\n", "", supporting_quote)

            # Extract reviewer notes (everything after "Reviewer Notes & Justification:**")
            notes_match = re.search(
                r"\*\*Reviewer Notes & Justification:\*\*\s*(.*?)(?=\n##### |\n---|\Z)",
                mblock,
                re.DOTALL,
            )
            reviewer_notes = ""
            if notes_match:
                reviewer_notes = notes_match.group(1).strip()

            records.append({
                "review_id": rev_id,
                "manifest_item_index": manifest_idx,
                "arxiv_id": arxiv_id,
                "blind_label": blind_label,
                "question": question,
                "context": context,
                "answer": answer,
                "is_refusal": answer.strip() == REFUSAL_BOILERPLATE,
                "primary_label": primary_label,
                "secondary_label": secondary_label,
                "claims_breakdown": claims,
                "supporting_quote": supporting_quote,
                "reviewer_notes": reviewer_notes,
            })

    return records


def audit_records(records: list[dict]) -> dict:
    """Run all audit checks and return findings."""
    findings = {
        "structural": [],
        "inconsistencies": [],
        "completeness": [],
        "summary": {},
    }

    # === STRUCTURAL CHECKS ===
    # Check total count
    if len(records) != 60:
        findings["structural"].append(
            f"CRITICAL: Expected 60 records, found {len(records)}"
        )

    # Check unique review IDs (should be REV-01 through REV-20)
    rev_ids = sorted(set(r["review_id"] for r in records))
    expected_revs = [f"REV-{i:02d}" for i in range(1, 21)]
    if rev_ids != expected_revs:
        findings["structural"].append(
            f"Review IDs mismatch. Found: {rev_ids}, Expected: {expected_revs}"
        )

    # Check each REV-XX has exactly 3 model records
    rev_counts = Counter(r["review_id"] for r in records)
    for rev, count in sorted(rev_counts.items()):
        if count != 3:
            findings["structural"].append(
                f"{rev}: Expected 3 models, found {count}"
            )

    # Check blind label distribution
    label_counts = Counter(r["blind_label"] for r in records)
    for label in ["Model_Alpha", "Model_Beta", "Model_Gamma"]:
        if label_counts.get(label, 0) != 20:
            findings["structural"].append(
                f"Expected 20 records for {label}, found {label_counts.get(label, 0)}"
            )

    # Check valid primary labels
    for r in records:
        if r["primary_label"] not in VALID_LABELS:
            findings["structural"].append(
                f"{r['review_id']}/{r['blind_label']}: Invalid primary label '{r['primary_label']}'"
            )

    # === SEMANTIC CONSISTENCY CHECKS ===
    for r in records:
        issues = []
        rid = f"{r['review_id']}/{r['blind_label']}"

        # Check 1: Refusal answer labeled SUPPORTED
        if r["is_refusal"] and r["primary_label"] == "SUPPORTED":
            issues.append({
                "type": "REFUSAL_LABELED_SUPPORTED",
                "severity": "HIGH",
                "description": (
                    f"Answer is the standard refusal boilerplate but labeled SUPPORTED. "
                    f"Should be either REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL."
                ),
            })

        # Check 2: Refusal answer labeled UNSUPPORTED
        if r["is_refusal"] and r["primary_label"] == "UNSUPPORTED":
            issues.append({
                "type": "REFUSAL_LABELED_UNSUPPORTED",
                "severity": "MEDIUM",
                "description": (
                    f"Answer is the standard refusal boilerplate but labeled UNSUPPORTED. "
                    f"Refusals should be REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL, "
                    f"not UNSUPPORTED (which is for fabricated/extrapolated claims)."
                ),
            })

        # Check 3: Refusal answer labeled CONTRADICTED
        if r["is_refusal"] and r["primary_label"] == "CONTRADICTED":
            issues.append({
                "type": "REFUSAL_LABELED_CONTRADICTED",
                "severity": "HIGH",
                "description": (
                    f"Answer is the standard refusal boilerplate but labeled CONTRADICTED. "
                    f"A refusal does not make contradicting claims."
                ),
            })

        # Check 4: Non-refusal answer labeled REFUSAL_VALID
        if not r["is_refusal"] and r["primary_label"] == "REFUSAL_VALID":
            issues.append({
                "type": "NONREFUSAL_LABELED_REFUSAL_VALID",
                "severity": "MEDIUM",
                "description": (
                    f"Answer provides substantive content but labeled REFUSAL_VALID."
                ),
            })

        # Check 5: Rationale says "Supported" but label is not SUPPORTED
        if r["reviewer_notes"]:
            notes_lower = r["reviewer_notes"].lower()
            if (
                r["primary_label"] in ("CONTRADICTED", "UNSUPPORTED")
                and ("supported" in notes_lower.split(".")[0])
                and "unsupported" not in notes_lower.split(".")[0]
                and "not supported" not in notes_lower.split(".")[0]
            ):
                issues.append({
                    "type": "RATIONALE_LABEL_MISMATCH",
                    "severity": "HIGH",
                    "description": (
                        f"Rationale text begins with support language but label is {r['primary_label']}. "
                        f"Notes: '{r['reviewer_notes'][:200]}'"
                    ),
                })

        if issues:
            for issue in issues:
                findings["inconsistencies"].append({
                    "review_id": r["review_id"],
                    "blind_label": r["blind_label"],
                    "primary_label": r["primary_label"],
                    "answer_excerpt": r["answer"][:150],
                    "is_refusal": r["is_refusal"],
                    **issue,
                })

    # === COMPLETENESS CHECKS ===
    for r in records:
        rid = f"{r['review_id']}/{r['blind_label']}"
        missing_fields = []

        if not r["primary_label"]:
            missing_fields.append("primary_label")

        # Claims breakdown and supporting quote are required per guide
        # but many are blank in the signed review - report as completeness issues
        if not r["claims_breakdown"] or r["claims_breakdown"] == "- *Claim 1:*":
            missing_fields.append("claims_breakdown")

        if not r["supporting_quote"]:
            missing_fields.append("supporting_quote")

        if missing_fields:
            findings["completeness"].append({
                "review_id": r["review_id"],
                "blind_label": r["blind_label"],
                "missing_fields": missing_fields,
            })

    # === SUMMARY STATISTICS ===
    label_dist = Counter(r["primary_label"] for r in records)
    label_by_model = defaultdict(Counter)
    for r in records:
        label_by_model[r["blind_label"]][r["primary_label"]] += 1

    findings["summary"] = {
        "total_records": len(records),
        "unique_rev_ids": len(rev_ids),
        "overall_label_distribution": dict(label_dist),
        "label_by_model": {k: dict(v) for k, v in label_by_model.items()},
        "total_inconsistencies": len(findings["inconsistencies"]),
        "total_structural_issues": len(findings["structural"]),
        "records_with_missing_fields": len(findings["completeness"]),
    }

    return findings


def main():
    print(f"Parsing: {REVIEW_FILE}")
    records = parse_signed_review(REVIEW_FILE)
    print(f"Parsed {len(records)} records")

    # Save parsed records
    parsed_path = OUTPUT_DIR / "parsed_annotations_60.json"
    with open(parsed_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"Saved parsed records to: {parsed_path}")

    # Run audit
    findings = audit_records(records)

    # Save findings
    findings_path = OUTPUT_DIR / "audit_findings.json"
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, ensure_ascii=False)
    print(f"Saved audit findings to: {findings_path}")

    # Print summary
    print("\n=== AUDIT SUMMARY ===")
    print(f"Total records: {findings['summary']['total_records']}")
    print(f"Unique REV IDs: {findings['summary']['unique_rev_ids']}")
    print(f"Structural issues: {findings['summary']['total_structural_issues']}")
    print(f"Semantic inconsistencies: {findings['summary']['total_inconsistencies']}")
    print(f"Records with missing fields: {findings['summary']['records_with_missing_fields']}")
    print(f"\nLabel distribution: {findings['summary']['overall_label_distribution']}")
    print(f"\nLabel by model:")
    for model, dist in sorted(findings["summary"]["label_by_model"].items()):
        print(f"  {model}: {dist}")

    print("\n=== INCONSISTENCIES ===")
    for i, issue in enumerate(findings["inconsistencies"], 1):
        print(f"\n--- Issue {i} ---")
        print(f"  {issue['review_id']}/{issue['blind_label']}")
        print(f"  Label: {issue['primary_label']}")
        print(f"  Type: {issue['type']} (Severity: {issue['severity']})")
        print(f"  Is Refusal: {issue['is_refusal']}")
        print(f"  Answer: {issue['answer_excerpt'][:100]}...")
        print(f"  Description: {issue['description'][:200]}")

    if findings["structural"]:
        print("\n=== STRUCTURAL ISSUES ===")
        for s in findings["structural"]:
            print(f"  - {s}")


if __name__ == "__main__":
    main()
