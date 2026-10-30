"""
Applies dual-engine machine consensus physical page numbers from independent cross-validation
(circularity_audit_results.json) into eval/prepared/qasper_sampled.json.
Labels are explicitly designated as 'machine_consensus' (UNVERIFIED by human).
"""

import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SAMPLED_PATH = os.path.join(ROOT_DIR, "eval", "prepared", "qasper_sampled.json")
AUDIT_PATH = os.path.join(ROOT_DIR, "eval", "prepared", "circularity_audit_results.json")


def main():
    if not os.path.exists(AUDIT_PATH):
        print(f"Error: Audit results not found at {AUDIT_PATH}")
        return

    with open(AUDIT_PATH, "r", encoding="utf-8") as f:
        audit_data = json.load(f)

    consensus_map = {}
    for item in audit_data.get("full_results", []):
        qid = item.get("question_id")
        pages = item.get("page_machine_consensus")
        span = item.get("consensus_page_span")
        conf = item.get("confidence_level")
        m_type = item.get("worst_match_type")
        if qid:
            consensus_map[qid] = {
                "pages": pages,
                "span": span,
                "confidence": conf,
                "match_type": m_type,
            }

    with open(SAMPLED_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)

    updated_count = 0
    for q in queries:
        qid = q.get("id")
        if qid in consensus_map:
            entry = consensus_map[qid]
            pages = entry["pages"]
            span = entry["span"]
            if pages:
                q["target_page"] = pages[0]  # Primary page
                q["page_machine_consensus"] = pages
                q["consensus_page_span"] = span
            else:
                q["page_machine_consensus"] = None
                q["consensus_page_span"] = None

            q["page_verified"] = False  # Explicitly unverified until human audit is logged
            q["label_provenance"] = "machine_consensus_pymupdf_pypdf"
            q["page_consensus_confidence"] = entry["confidence"]
            q["page_match_type"] = entry["match_type"]
            updated_count += 1

    with open(SAMPLED_PATH, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)

    print(f"[PAGE-SYNC] Successfully synchronized {updated_count} questions with machine consensus page labels (page_verified=False).")


if __name__ == "__main__":
    main()
