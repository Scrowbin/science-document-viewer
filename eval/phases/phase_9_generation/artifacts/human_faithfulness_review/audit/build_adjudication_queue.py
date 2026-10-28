#!/usr/bin/env python3
"""
Generate the RQ5 Human Faithfulness Review Adjudication Queue.
Creates:
  - eval/phases/phase_9_generation/artifacts/human_faithfulness_review/audit/annotation_adjudication_queue.csv
  - eval/phases/phase_9_generation/artifacts/human_faithfulness_review/audit/annotation_adjudication_queue.jsonl
  - eval/phases/phase_9_generation/artifacts/human_faithfulness_review/audit/annotation_adjudication_queue.md
"""

import csv
import json
from pathlib import Path

BASE_DIR = Path("eval/phases/phase_9_generation/artifacts/human_faithfulness_review/audit")

# Detailed dictionary of audit findings for specific items
FLAGGED_ITEMS = {
    # 1. Clear Protocol Inconsistencies (High Confidence)
    ("REV-03", "Model_Gamma"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled UNSUPPORTED when context contains answer",
        "rule": "Section 6.5 & Taxonomy: Refusals must be labeled REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL. When context contains answer, label must be MISSING_INFO - UNJUSTIFIED_REFUSAL.",
        "proposed_primary": "MISSING_INFO - UNJUSTIFIED_REFUSAL",
        "proposed_secondary": "REFUSAL",
        "proposed_rationale": "Model provided standard refusal boilerplate. However, context explicitly states 'The Sentence corpus (S) consists of domain-targeted ~80K sentences and 280 GB of plain text' and describes running Open IE v4 on it. The reviewer noted 'It claimed that there was no mentioned of the corpus, in which it did.' Under protocol taxonomy, a refusal when context contains the answer is MISSING_INFO - UNJUSTIFIED_REFUSAL.",
        "confidence": "HIGH",
    },
    ("REV-09", "Model_Alpha"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED",
        "rule": "Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. Genuinely absent answer in context must be labeled REFUSAL_VALID.",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave standard refusal boilerplate. Context only states 'JESSI is trained using only the datasets given on the shared task' without naming or detailing them. Because the requested information is absent from the context, the refusal is justified (REFUSAL_VALID).",
        "confidence": "HIGH",
    },
    ("REV-09", "Model_Gamma"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED",
        "rule": "Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. Genuinely absent answer in context must be labeled REFUSAL_VALID.",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave standard refusal boilerplate. Context does not specify dataset names. Under Section 6.5, this is a justified refusal (REFUSAL_VALID).",
        "confidence": "HIGH",
    },
    ("REV-10", "Model_Beta"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled UNSUPPORTED when context contains answer",
        "rule": "Section 6.5 & Taxonomy: Refusals must be labeled REFUSAL_VALID or MISSING_INFO - UNJUSTIFIED_REFUSAL, not UNSUPPORTED. When answer is in context, label must be MISSING_INFO - UNJUSTIFIED_REFUSAL.",
        "proposed_primary": "MISSING_INFO - UNJUSTIFIED_REFUSAL",
        "proposed_secondary": "REFUSAL",
        "proposed_rationale": "Model provided refusal boilerplate. Context explicitly describes the dataset construction methodology ('We construct the dataset by collecting...'). The reviewer noted 'Context gave a brief description of how it was built.' Under Section 6.5, an unwarranted refusal is MISSING_INFO - UNJUSTIFIED_REFUSAL.",
        "confidence": "HIGH",
    },
    ("REV-12", "Model_Beta"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED",
        "rule": "Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave refusal boilerplate. Context contains only a 34-character table heading fragment ('Building Extractive CNN/Daily Mail') and no metric information. Reviewer noted 'The text did not provide information on the problems with existing metrics.' Under Section 6.5, this justified refusal must be REFUSAL_VALID.",
        "confidence": "HIGH",
    },
    ("REV-12", "Model_Gamma"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED",
        "rule": "Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave refusal boilerplate. Context contains only a 34-character header fragment and no metric information. Reviewer noted text did not provide information. Under Section 6.5, this justified refusal must be REFUSAL_VALID.",
        "confidence": "HIGH",
    },
    ("REV-20", "Model_Beta"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED",
        "rule": "Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave refusal boilerplate. Context references '14 genres shown in Table TABREF8' but the table contents are not in the excerpt. Reviewer noted 'Context did not give the genre of songs.' Under Section 6.5, this justified refusal must be REFUSAL_VALID.",
        "confidence": "HIGH",
    },
    ("REV-20", "Model_Gamma"): {
        "issue": "PROTOCOL_VIOLATION: Refusal boilerplate labeled SUPPORTED",
        "rule": "Section 6.5 & Taxonomy: Refusals cannot be labeled SUPPORTED. When context lacks requested information, label must be REFUSAL_VALID.",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave refusal boilerplate. Context references a table of genres that was omitted from the snippet. Reviewer noted context did not give the genres. Under Section 6.5, this justified refusal must be REFUSAL_VALID.",
        "confidence": "HIGH",
    },

    # 2. Semantic Inconsistencies (Medium Confidence / Human Judgment Required)
    ("REV-01", "Model_Gamma"): {
        "issue": "SEMANTIC_INCONSISTENCY: Label CONTRADICTED applied to unmentioned/unsupported claim rather than direct contradiction",
        "rule": "Precedence Rule 1 (CONTRADICTED requires explicit conflict/negation) vs Rule 2 (UNSUPPORTED = ungrounded/missing claim)",
        "proposed_primary": "UNSUPPORTED",
        "proposed_secondary": "EXTRAPOLATION",
        "proposed_rationale": "Answer claims 'Grail theorem provers use a formalism called type-logical grammars.' Context describes automated theorem proving for type-logical grammars in the chapter introduction. The reviewer noted 'Given text did not mention that type-logical grammars was used by the Grail.' Because the reviewer's reasoning is absence of explicit link rather than an incompatible contradictory statement, Precedence Rule 2 designates this as UNSUPPORTED.",
        "confidence": "MEDIUM",
    },
    ("REV-02", "Model_Beta"): {
        "issue": "SEMANTIC_INCONSISTENCY: Model claims authors do not equate drunk texting/tweeting; labeled UNSUPPORTED while identical claim in Alpha labeled CONTRADICTED",
        "rule": "Precedence Rule 1: CONTRADICTED takes precedence over UNSUPPORTED when claims contradict context",
        "proposed_primary": "CONTRADICTED",
        "proposed_secondary": "FACTUAL_CONFLICT",
        "proposed_rationale": "Model asserts authors do not equate drunk tweeting with drunk texting and that context lacks information. Context directly defines drunk tweeting as the medium for drunk-texting prediction ('We refer to tweets written under the influence of alcohol as \"drunk tweets\"... drunk-texting prediction'). In REV-02 Alpha, the identical negative claim was labeled CONTRADICTED. Per Precedence Rule 1, CONTRADICTED takes precedence over UNSUPPORTED.",
        "confidence": "MEDIUM",
    },
    ("REV-10", "Model_Gamma"): {
        "issue": "SEMANTIC_INCONSISTENCY: Entirely fabricated response labeled MISSING_INFO - PARTIAL",
        "rule": "Precedence Rule 2 (UNSUPPORTED > MISSING_INFO) & Taxonomy: Partial coverage requires some supported facts from context; zero supported facts must be labeled UNSUPPORTED",
        "proposed_primary": "UNSUPPORTED",
        "proposed_secondary": "HALLUCINATION",
        "proposed_rationale": "Answer fabricates a generic process ('aggregating and analyzing a large corpus of text data from various sources, including online forums, social media, and scientific publications... annotated by human experts'). Context describes a specific, different automated collection. Reviewer noted 'did not directly come from the text provided.' Because zero factual claims are supported by context, this is an unsupported hallucination, not partial coverage.",
        "confidence": "MEDIUM",
    },

    # 3. Rationale Wording Ambiguity (Retain Label, Clarify Rationale)
    ("REV-02", "Model_Alpha"): {
        "issue": "RATIONALE_AMBIGUITY: Rationale opens with 'Supported' but meant 'Context supports equivalence', which correctly results in CONTRADICTED label for model's negation",
        "rule": "Precedence Rule 1: CONTRADICTED is correct when answer asserts negation of supported relationship",
        "proposed_primary": "CONTRADICTED",
        "proposed_secondary": "FACTUAL_CONFLICT",
        "proposed_rationale": "Label CONTRADICTED is correct. The reviewer's note 'Supported. The authors treat drunk tweeting as synonymous...' was intended to mean 'The context supports that the authors equate them, hence the model answer (stating they do not equate them) is CONTRADICTED.' Rationale clarified for audit trail.",
        "confidence": "HIGH",
    },

    # 4. Borderline Cases Flagged for Review (Retain Current Label Pending Reviewer Adjudication)
    ("REV-01", "Model_Alpha"): {
        "issue": "BORDERLINE_REVIEW: Context discusses type-logical grammars extensively but specific name 'Grail' does not appear in excerpt; refusal accepted as valid",
        "rule": "Section 6.5: Context sufficiency threshold for specific named entities",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model refused. In the supplied excerpt, the specific word 'Grail' is absent (though context is from a chapter on Grail). Reviewer judged information insufficient to establish Grail's formalism. Defensible borderline judgment; retain pending reviewer adjudication.",
        "confidence": "MEDIUM",
    },
    ("REV-01", "Model_Beta"): {
        "issue": "BORDERLINE_REVIEW: Same context and refusal as REV-01 Alpha",
        "rule": "Section 6.5: Context sufficiency threshold for specific named entities",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Same as REV-01 Alpha. Defensible borderline judgment; retain pending reviewer adjudication.",
        "confidence": "MEDIUM",
    },
    ("REV-04", "Model_Alpha"): {
        "issue": "BORDERLINE_REVIEW: Context lists 5 dialects; question asks for 4; model lists 4 (omits MSA)",
        "rule": "Taxonomy: SUPPORTED vs MISSING_INFO - PARTIAL when question framing constrains answer scope",
        "proposed_primary": "SUPPORTED",
        "proposed_secondary": "",
        "proposed_rationale": "Model lists Egyptian, Levantine, Gulf, and North African. Context also lists MSA. Because the question prompt explicitly asked 'Which are the four Arabic dialects?', listing 4 supported dialects satisfies the prompt. Retain SUPPORTED.",
        "confidence": "HIGH",
    },
    ("REV-04", "Model_Beta"): {
        "issue": "BORDERLINE_REVIEW: Context lists 5 dialects; question asks for 4; model lists 4 (omits MSA)",
        "rule": "Taxonomy: SUPPORTED vs MISSING_INFO - PARTIAL when question framing constrains answer scope",
        "proposed_primary": "SUPPORTED",
        "proposed_secondary": "",
        "proposed_rationale": "Same as REV-04 Alpha. Retain SUPPORTED.",
        "confidence": "HIGH",
    },
    ("REV-04", "Model_Gamma"): {
        "issue": "BORDERLINE_REVIEW: Context lists 5 dialects; question asks for 4; model lists 4 (omits MSA)",
        "rule": "Taxonomy: SUPPORTED vs MISSING_INFO - PARTIAL when question framing constrains answer scope",
        "proposed_primary": "SUPPORTED",
        "proposed_secondary": "",
        "proposed_rationale": "Same as REV-04 Alpha. Retain SUPPORTED.",
        "confidence": "HIGH",
    },
    ("REV-08", "Model_Beta"): {
        "issue": "BORDERLINE_REVIEW: Minor elaboration beyond literal context ('convey meaning through images')",
        "rule": "Taxonomy: SUPPORTED vs UNSUPPORTED for benign semantic elaboration",
        "proposed_primary": "SUPPORTED",
        "proposed_secondary": "",
        "proposed_rationale": "Model answer states approach involves connecting images and text, then provides elaboration. Core claim is directly supported by context. Elaboration is benign paraphrase. Retain SUPPORTED.",
        "confidence": "HIGH",
    },
    ("REV-11", "Model_Alpha"): {
        "issue": "BORDERLINE_REVIEW: Context mentions 'reference corpus of 21,093 tokens'; model refused; reviewer deemed info insufficient",
        "rule": "Section 6.5: Context sufficiency threshold for dataset identification",
        "proposed_primary": "REFUSAL_VALID",
        "proposed_secondary": "ABSENT",
        "proposed_rationale": "Model gave refusal. The context mentions token count of reference corpus but no formal dataset name. Reviewer considered information insufficient to name a dataset. Retain REFUSAL_VALID pending reviewer preference.",
        "confidence": "MEDIUM",
    },
    ("REV-13", "Model_Alpha"): {
        "issue": "BORDERLINE_REVIEW: Model misattributes FastText pretraining to UD Czech rather than Czech Wikipedia; labeled CONTRADICTED",
        "rule": "Precedence Rule 1 (CONTRADICTED > UNSUPPORTED)",
        "proposed_primary": "CONTRADICTED",
        "proposed_secondary": "FACTUAL_CONFLICT",
        "proposed_rationale": "Model claims FastText embeddings were trained on UD Czech data. Context explicitly states FastText was pretrained on Czech Wikipedia (and UD data was only used for segmentation/tokenization tools). Because the claim asserts an attribution contrary to context, CONTRADICTED is defensible. Retain CONTRADICTED.",
        "confidence": "HIGH",
    },
    ("REV-17", "Model_Alpha"): {
        "issue": "BORDERLINE_REVIEW: Model misattributes baseline name; labeled UNSUPPORTED",
        "rule": "Taxonomy: UNSUPPORTED for ungrounded entity name",
        "proposed_primary": "UNSUPPORTED",
        "proposed_secondary": "HALLUCINATION",
        "proposed_rationale": "Model claims baseline is 'Multi-cascaded Deep Model proposed in BIBREF3'. Context mentions model proposed in BIBREF3 and refers to it as McM. Label UNSUPPORTED is defensible. Retain UNSUPPORTED.",
        "confidence": "HIGH",
    },
}


def build_queue():
    with open(BASE_DIR / "parsed_annotations_60.json", "r", encoding="utf-8") as f:
        records = json.load(f)

    fieldnames = [
        "review_id",
        "blind_label",
        "original_primary_label",
        "original_secondary_label",
        "original_rationale",
        "answer",
        "relevant_context",
        "audit_issue",
        "protocol_rule",
        "proposed_primary_label",
        "proposed_secondary_label",
        "proposed_rationale",
        "confidence",
        "reviewer_decision",
        "final_primary_label",
        "final_secondary_label",
        "adjudication_notes",
    ]

    queue_rows = []

    for r in records:
        rev_id = r["review_id"]
        blind_label = r["blind_label"]
        key = (rev_id, blind_label)

        orig_primary = r.get("primary_label", "")
        orig_sec = r.get("secondary_label", "")
        
        # Combine reviewer notes and claim breakdown for full original rationale
        notes = r.get("reviewer_notes") or ""
        claims = r.get("claims_breakdown") or ""
        orig_rationale_parts = []
        if claims and claims != "- *Claim 1:*":
            orig_rationale_parts.append(claims)
        if notes:
            orig_rationale_parts.append(notes)
        orig_rationale = " | ".join(orig_rationale_parts) if orig_rationale_parts else "None recorded"

        if key in FLAGGED_ITEMS:
            flag = FLAGGED_ITEMS[key]
            issue = flag["issue"]
            rule = flag["rule"]
            prop_primary = flag["proposed_primary"]
            prop_sec = flag["proposed_secondary"]
            prop_rationale = flag["proposed_rationale"]
            confidence = flag["confidence"]
        else:
            issue = "NONE (PASS)"
            rule = "N/A"
            prop_primary = orig_primary
            prop_sec = orig_sec
            prop_rationale = orig_rationale
            confidence = "HIGH (CONFIRMED)"

        row = {
            "review_id": rev_id,
            "blind_label": blind_label,
            "original_primary_label": orig_primary,
            "original_secondary_label": orig_sec,
            "original_rationale": orig_rationale,
            "answer": r.get("answer", ""),
            "relevant_context": r.get("context", ""),
            "audit_issue": issue,
            "protocol_rule": rule,
            "proposed_primary_label": prop_primary,
            "proposed_secondary_label": prop_sec,
            "proposed_rationale": prop_rationale,
            "confidence": confidence,
            "reviewer_decision": "",      # Unfilled pending human adjudication
            "final_primary_label": "",   # Unfilled pending human adjudication
            "final_secondary_label": "", # Unfilled pending human adjudication
            "adjudication_notes": "",    # Unfilled pending human adjudication
        }
        queue_rows.append(row)

    # 1. Write CSV
    csv_path = BASE_DIR / "annotation_adjudication_queue.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in queue_rows:
            writer.writerow(row)
    print(f"Wrote {len(queue_rows)} rows to {csv_path}")

    # 2. Write JSONL
    jsonl_path = BASE_DIR / "annotation_adjudication_queue.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for row in queue_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(queue_rows)} rows to {jsonl_path}")

    # 3. Write Markdown Adjudication Queue
    md_path = BASE_DIR / "annotation_adjudication_queue.md"
    write_markdown_queue(md_path, queue_rows)
    print(f"Wrote Markdown queue to {md_path}")


def write_markdown_queue(path: Path, rows: list[dict]):
    flagged = [r for r in rows if r["audit_issue"] != "NONE (PASS)"]
    passed = [r for r in rows if r["audit_issue"] == "NONE (PASS)"]

    with open(path, "w", encoding="utf-8") as f:
        f.write("# RQ5 Human Faithfulness Review Adjudication Queue\n\n")
        f.write("**Status:** AWAITING_HUMAN_ADJUDICATION\n")
        f.write(f"**Total Records:** {len(rows)} (60 answers: 20 questions × 3 blinded models)\n")
        f.write(f"**Flagged Items Requiring Adjudication:** {len(flagged)}\n")
        f.write(f"**Unflagged Records (Passed Verification):** {len(passed)}\n\n")
        f.write("---\n\n")

        f.write("## Section 1: Flagged Items Requiring Reviewer Decision\n\n")
        f.write("The following 18 records require reviewer review or explicit sign-off.\n")
        f.write("Columns `Reviewer Decision`, `Final Primary Label`, `Final Secondary Label`, and `Adjudication Notes` remain unfilled pending human decision.\n\n")

        f.write("| # | Review ID | Model | Original Label | Audit Issue | Proposed Label | Conf | Decision | Final Label |\n")
        f.write("| :-: | :--- | :--- | :--- | :--- | :--- | :-: | :---: | :---: |\n")

        for idx, r in enumerate(flagged, 1):
            f.write(
                f"| {idx} | **{r['review_id']}** | {r['blind_label']} | `{r['original_primary_label']}` | "
                f"{r['audit_issue'][:50]}... | `{r['proposed_primary_label']}` | {r['confidence']} | "
                f"*[PENDING]* | *[PENDING]* |\n"
            )

        f.write("\n---\n\n")
        f.write("## Section 2: Detailed Dossiers for Flagged Records\n\n")

        for idx, r in enumerate(flagged, 1):
            sec_orig = r['original_secondary_label'] or 'None'
            sec_prop = r['proposed_secondary_label'] or 'None'
            f.write(
                f"### Item {idx}: {r['review_id']} — {r['blind_label']}\n\n"
                f"- **Original Primary Label:** `{r['original_primary_label']}`\n"
                f"- **Original Secondary Label:** `{sec_orig}`\n"
                f"- **Original Rationale:** {r['original_rationale']}\n"
                f"- **Audit Issue:** {r['audit_issue']}\n"
                f"- **Protocol Rule:** {r['protocol_rule']}\n"
                f"- **Proposed Primary Label:** `{r['proposed_primary_label']}`\n"
                f"- **Proposed Secondary Label:** `{sec_prop}`\n"
                f"- **Proposed Rationale:** {r['proposed_rationale']}\n"
                f"- **Confidence:** **{r['confidence']}**\n\n"
                f"<details>\n<summary><b>Click to View Model Answer and Context</b></summary>\n\n"
                f"**Answer:**\n```text\n{r['answer']}\n```\n\n"
                f"**Context Excerpt:**\n```text\n{r['relevant_context'][:500]}...\n```\n"
                f"</details>\n\n"
                f"**Adjudication Action Required:**\n"
                f"- [ ] ACCEPT Proposed Label (`{r['proposed_primary_label']}`)\n"
                f"- [ ] RETAIN Original Label (`{r['original_primary_label']}`)\n"
                f"- [ ] ASSIGN Custom Label: `____________________`\n"
                f"- **Adjudicator Notes:** `________________________________________`\n\n"
                f"---\n\n"
            )

        f.write("## Section 3: Records Passed with No Inconsistencies (42 Items)\n\n")
        f.write("The remaining 42 records demonstrated consistent alignment between model answer, evidence context, reviewer rationale, and protocol precedence rules.\n\n")
        f.write("| Review ID | Model | Primary Label | Secondary Label | Status |\n")
        f.write("| :--- | :--- | :--- | :--- | :---: |\n")
        for r in passed:
            f.write(f"| {r['review_id']} | {r['blind_label']} | `{r['original_primary_label']}` | `{r['original_secondary_label'] or '-'}` | ✅ PASS |\n")

    print(f"Markdown dossier written successfully.")


if __name__ == "__main__":
    build_queue()
