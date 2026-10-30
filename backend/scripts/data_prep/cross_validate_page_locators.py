"""
Independent Cross-Validation & Circularity Audit for PDF Page Locators (Track B).
Addresses critical methodological requirements:
  1. Record granular match_type (full / anchor_12word / token_fallback) per passage & report counts.
  2. Flag ambiguous multiple-page hits instead of greedy first-hit termination.
  3. Store multi-page spans [page_start, page_end] and evaluate all text evidence passages per question.
  4. Designate engine discrepancies and single-engine finds as 'unresolved', NOT consensus.
  5. Seeded random stratification across papers + mandatory inclusion of all low-confidence/ambiguous items.
  6. Calculate Rule-of-Three (3/N) statistical upper bound for the human review batch (60-100 items).
  7. Check version drift between QASPER text and downloaded arXiv PDF text.

Outputs:
  - eval/prepared/circularity_audit_results.json
"""

import argparse
import json
import os
import random
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import pypdf
import pymupdf

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
EVAL_DIR = os.path.join(ROOT_DIR, "eval")
PDFS_DIR = os.path.join(EVAL_DIR, "data", "pdfs")
QASPER_SAMPLED_PATH = os.path.join(EVAL_DIR, "prepared", "qasper_sampled.json")
AUDIT_OUTPUT_PATH = os.path.join(EVAL_DIR, "prepared", "circularity_audit_results.json")


def normalize_text(text: str) -> str:
    """De-hyphenates line breaks and standardizes whitespace."""
    if not text:
        return ""
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def tokenize(text: str) -> List[str]:
    """Extracts alphanumeric word tokens."""
    return re.findall(r"[A-Za-z0-9_\-\$]+", text.lower())


def scan_pages_for_evidence(
    pages_text: List[str],
    evidence: str,
) -> Dict[str, Any]:
    """
    Scans ALL pages for evidence without greedy early exit.
    Records match_type, detects ambiguous hits, and returns exact matching page numbers (1-indexed).
    """
    norm_ev = normalize_text(evidence)
    if not norm_ev:
        return {
            "matching_pages": [],
            "match_type": "none",
            "is_ambiguous": False,
            "anchor_words_matched": 0,
            "token_overlap_score": 0.0,
        }

    total_pages = len(pages_text)

    # 1. Full passage substring check across all pages
    full_hit_pages = []
    for p_idx, p_text in enumerate(pages_text):
        if norm_ev in p_text:
            full_hit_pages.append(p_idx + 1)

    if full_hit_pages:
        return {
            "matching_pages": full_hit_pages,
            "match_type": "full",
            "is_ambiguous": len(full_hit_pages) > 1,
            "anchor_words_matched": len(norm_ev.split()),
            "token_overlap_score": 1.0,
        }

    # 2. Robust 12-word anchor checks (start, middle, end)
    ev_words = norm_ev.split()
    anchor_len = 12
    anchors = []

    if len(ev_words) >= anchor_len:
        anchors.append(" ".join(ev_words[:anchor_len]))  # Start anchor
        mid_idx = len(ev_words) // 2
        anchors.append(" ".join(ev_words[mid_idx : mid_idx + anchor_len]))  # Mid anchor
        anchors.append(" ".join(ev_words[-anchor_len:]))  # End anchor
    elif len(ev_words) >= 6:
        anchors.append(" ".join(ev_words))  # Whole short quote as anchor

    anchor_hit_pages = set()
    for p_idx, p_text in enumerate(pages_text):
        for anchor in anchors:
            if anchor and anchor in p_text:
                anchor_hit_pages.add(p_idx + 1)
                break

    if anchor_hit_pages:
        sorted_hits = sorted(list(anchor_hit_pages))
        return {
            "matching_pages": sorted_hits,
            "match_type": "anchor_12word",
            "is_ambiguous": len(sorted_hits) > 1,
            "anchor_words_matched": min(len(ev_words), anchor_len),
            "token_overlap_score": 0.85,
        }

    # 3. Strict token overlap fallback (raised threshold: 0.60 to avoid spurious hits)
    ev_tokens = set(tokenize(norm_ev))
    best_score = 0.0
    fallback_pages = []

    for p_idx, p_text in enumerate(pages_text):
        p_toks = set(tokenize(p_text))
        if ev_tokens and p_toks:
            overlap = len(ev_tokens & p_toks) / max(1, len(ev_tokens))
            if overlap >= 0.60:
                fallback_pages.append((p_idx + 1, overlap))
            if overlap > best_score:
                best_score = overlap

    if fallback_pages:
        # Sort by score descending
        fallback_pages.sort(key=lambda x: x[1], reverse=True)
        top_score = fallback_pages[0][1]
        # Any page within 0.05 of top score is considered candidate
        top_candidates = [p for p, sc in fallback_pages if sc >= top_score - 0.05]
        return {
            "matching_pages": sorted(top_candidates),
            "match_type": "token_fallback",
            "is_ambiguous": len(top_candidates) > 1,
            "anchor_words_matched": 0,
            "token_overlap_score": round(top_score, 3),
        }

    return {
        "matching_pages": [],
        "match_type": "none",
        "is_ambiguous": False,
        "anchor_words_matched": 0,
        "token_overlap_score": round(best_score, 3),
    }


def extract_pages_with_pymupdf(pdf_path: str) -> List[str]:
    """Extracts normalized text for each page via PyMuPDF."""
    doc = pymupdf.open(pdf_path)
    pages = [normalize_text(str(page.get_text("text"))) for page in doc]
    doc.close()
    return pages


def extract_pages_with_pypdf(pdf_path: str) -> List[str]:
    """Extracts normalized text for each page via pypdf."""
    reader = pypdf.PdfReader(pdf_path)
    pages = [normalize_text(page.extract_text() or "") for page in reader.pages]
    return pages


def check_version_drift(pdf_full_text: str, qasper_item: Dict[str, Any]) -> Tuple[bool, float]:
    """Checks whether the downloaded arXiv PDF has significant lexical text drift from QASPER metadata."""
    title = normalize_text(qasper_item.get("paper_title", ""))
    norm_pdf = normalize_text(pdf_full_text)

    title_match = title in norm_pdf if len(title) > 10 else True
    # Check sample keywords from question evidence
    ev_sample = " ".join(qasper_item.get("evidence_keywords", []))
    ev_tokens = set(tokenize(ev_sample))
    pdf_tokens = set(tokenize(norm_pdf))

    overlap = len(ev_tokens & pdf_tokens) / max(1, len(ev_tokens)) if ev_tokens else 1.0
    has_drift = (not title_match and overlap < 0.50) or (overlap < 0.35)
    return has_drift, round(overlap, 3)


def run_rigorous_cross_validation(
    sampled_json: str = QASPER_SAMPLED_PATH,
    pdfs_dir: str = PDFS_DIR,
    output_path: str = AUDIT_OUTPUT_PATH,
    target_audit_size: int = 75,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Executes non-greedy dual-engine cross-validation, records match_types,
    detects multi-page spans, and constructs a stratified human audit batch.
    """
    with open(sampled_json, "r", encoding="utf-8") as f:
        queries = json.load(f)

    # 1. Discover physical PDFs in eval/data/pdfs/
    available_pdfs: Dict[str, str] = {}
    if os.path.exists(pdfs_dir):
        for fname in os.listdir(pdfs_dir):
            if fname.endswith(".pdf"):
                aid = fname.replace(".pdf", "")
                available_pdfs[aid] = os.path.join(pdfs_dir, fname)

    # Note: Canonical 4 seed papers are intentionally NOT mixed here, as they belong to the 16-query pilot.
    matched_queries = [
        q for q in queries
        if q.get("paper_arxiv_id") in available_pdfs and q.get("question_type") != "unanswerable"
    ]
    unanswerable_skipped = sum(
        1 for q in queries
        if q.get("paper_arxiv_id") in available_pdfs and q.get("question_type") == "unanswerable"
    )

    print(f"\n[CROSS-VAL] Physical PDFs in pool: {len(available_pdfs)}")
    print(f"[CROSS-VAL] Evaluated Answerable Questions: {len(matched_queries)} (Skipped {unanswerable_skipped} unanswerable)")

    # Cache extracted text per PDF to avoid repetitive parsing
    cache_pymupdf: Dict[str, List[str]] = {}
    cache_pypdf: Dict[str, List[str]] = {}

    match_type_counts = {
        "full": 0,
        "anchor_12word": 0,
        "token_fallback": 0,
        "none": 0,
    }

    results: List[Dict[str, Any]] = []
    exact_consensus_count = 0
    span_consensus_count = 0
    unresolved_count = 0
    drift_warning_count = 0

    for idx, q in enumerate(matched_queries):
        qid = q.get("id")
        aid = q.get("paper_arxiv_id")
        title = q.get("paper_title")
        q_text = q.get("question")
        pdf_path = available_pdfs[aid]

        # Extract text if not cached
        if aid not in cache_pymupdf:
            cache_pymupdf[aid] = extract_pages_with_pymupdf(pdf_path)
            cache_pypdf[aid] = extract_pages_with_pypdf(pdf_path)

        pages_mupdf = cache_pymupdf[aid]
        pages_pypdf = cache_pypdf[aid]

        # Check version drift
        full_pdf_text = " ".join(pages_mupdf)
        drift_flag, drift_overlap = check_version_drift(full_pdf_text, q)
        if drift_flag:
            drift_warning_count += 1

        # Collect ALL text evidence passages for this question
        passages: List[str] = []
        if q.get("verbatim_evidence_quote"):
            passages.append(q.get("verbatim_evidence_quote"))
        for ev in q.get("evidence_list", []):
            if ev and ev not in passages:
                passages.append(ev)

        if not passages:
            passages = [""]

        # Run dual-engine scan over all passages
        pages_mupdf_set: Set[int] = set()
        pages_pypdf_set: Set[int] = set()
        worst_match_type = "full"
        type_rank = {"full": 3, "anchor_12word": 2, "token_fallback": 1, "none": 0}
        any_ambiguous = False

        for passage in passages:
            res_mu = scan_pages_for_evidence(pages_mupdf, passage)
            res_py = scan_pages_for_evidence(pages_pypdf, passage)

            pages_mupdf_set.update(res_mu["matching_pages"])
            pages_pypdf_set.update(res_py["matching_pages"])

            if res_mu["is_ambiguous"] or res_py["is_ambiguous"]:
                any_ambiguous = True

            # Track worst match type across passages
            m_type = res_mu["match_type"]
            if type_rank.get(m_type, 0) < type_rank.get(worst_match_type, 3):
                worst_match_type = m_type

        match_type_counts[worst_match_type] = match_type_counts.get(worst_match_type, 0) + 1

        list_mupdf = sorted(list(pages_mupdf_set))
        list_pypdf = sorted(list(pages_pypdf_set))

        # Determine Consensus vs Unresolved (Never default to PyMuPDF on dispute)
        status = "unresolved"
        consensus_pages: List[int] = []
        consensus_span: List[int] = []
        confidence_level = "unresolved"

        if list_mupdf and list_pypdf:
            if list_mupdf == list_pypdf:
                status = "exact_consensus"
                consensus_pages = list_mupdf
                consensus_span = [min(list_mupdf), max(list_mupdf)]
                confidence_level = "high" if worst_match_type in ["full", "anchor_12word"] and not any_ambiguous else "low"
                exact_consensus_count += 1
            elif set(list_mupdf) & set(list_pypdf):
                # Overlapping multi-page paragraph
                status = "span_overlap_consensus"
                union_pages = sorted(list(set(list_mupdf) | set(list_pypdf)))
                consensus_pages = union_pages
                consensus_span = [min(union_pages), max(union_pages)]
                confidence_level = "medium"
                span_consensus_count += 1
            else:
                status = "engine_discrepancy"
                confidence_level = "unresolved"
                unresolved_count += 1
        elif list_mupdf or list_pypdf:
            status = "single_engine_only"
            confidence_level = "unresolved"
            unresolved_count += 1
        else:
            status = "undetected"
            confidence_level = "unresolved"
            unresolved_count += 1

        rec = {
            "question_id": qid,
            "paper_arxiv_id": aid,
            "paper_title": title,
            "question": q_text,
            "pages_pymupdf": list_mupdf,
            "pages_pypdf": list_pypdf,
            "page_machine_consensus": consensus_pages if confidence_level != "unresolved" else None,
            "consensus_page_span": consensus_span if confidence_level != "unresolved" else None,
            "status": status,
            "confidence_level": confidence_level,
            "worst_match_type": worst_match_type,
            "is_ambiguous": any_ambiguous,
            "version_drift_warning": drift_flag,
            "version_drift_overlap": drift_overlap,
            "evidence_snippets": [p[:160] for p in passages],
        }
        results.append(rec)

    # 2. Build Stratified Human Review Batch (60 to 100 Passages)
    # Mandatorily include all high-risk items:
    mandatory_human_items = [
        r for r in results
        if r["confidence_level"] in ["unresolved", "low"] or r["is_ambiguous"] or r["worst_match_type"] == "token_fallback" or r["version_drift_warning"]
    ]

    # Sample remaining high-confidence consensus items randomly across papers (seeded)
    remaining_pool = [r for r in results if r not in mandatory_human_items]
    rng = random.Random(seed)
    rng.shuffle(remaining_pool)

    needed = max(0, target_audit_size - len(mandatory_human_items))
    sampled_consensus = remaining_pool[:needed]

    human_audit_batch = mandatory_human_items + sampled_consensus
    rng.shuffle(human_audit_batch)

    # Rule of Three (95% upper bound confidence interval if 0 errors found in sample)
    audit_n = len(human_audit_batch)
    rule_of_three_bound_pct = round((3.0 / max(1, audit_n)) * 100, 2)

    total_eval = max(1, len(matched_queries))
    print("\n" + "=" * 90)
    print("      RIGOROUS DUAL-ENGINE AUDIT & CONSENSUS (PyMuPDF vs pypdf)")
    print("=" * 90)
    print(f"  * Total Questions Evaluated:         {total_eval}")
    print(f"  * Exact Consensus:                   {exact_consensus_count} ({round((exact_consensus_count/total_eval)*100, 1)}%)")
    print(f"  * Multi-Page Span Overlap:           {span_consensus_count} ({round((span_consensus_count/total_eval)*100, 1)}%)")
    print(f"  * Unresolved (Discrepancy/Single):   {unresolved_count} ({round((unresolved_count/total_eval)*100, 1)}%)")
    print(f"  * Version Drift Warnings:            {drift_warning_count}")
    print("------------------------------------------------------------------------------------------")
    print("  Match Type Breakdown across Evidence Passages:")
    print(f"    - Full Text Match:                 {match_type_counts['full']} ({round((match_type_counts['full']/total_eval)*100, 1)}%)")
    print(f"    - 12-Word Anchor Match:            {match_type_counts['anchor_12word']} ({round((match_type_counts['anchor_12word']/total_eval)*100, 1)}%)")
    print(f"    - Token Overlap Fallback:          {match_type_counts['token_fallback']} ({round((match_type_counts['token_fallback']/total_eval)*100, 1)}%)")
    print(f"    - Undetected:                      {match_type_counts['none']} ({round((match_type_counts['none']/total_eval)*100, 1)}%)")
    print("------------------------------------------------------------------------------------------")
    print(f"  * Human Verification Batch Size:     {audit_n} passages (Stratified + High-Risk)")
    print(f"  * Rule-of-Three 95% Bound (if 0 err): True Error Rate <= {rule_of_three_bound_pct}%")
    print("=" * 90 + "\n")

    summary_artifact = {
        "metadata": {
            "eval_date": time.strftime("%Y-%m-%d"),
            "total_questions_evaluated": total_eval,
            "exact_consensus_count": exact_consensus_count,
            "span_consensus_count": span_consensus_count,
            "unresolved_count": unresolved_count,
            "version_drift_warnings": drift_warning_count,
            "match_types": match_type_counts,
            "human_audit_batch_size": audit_n,
            "rule_of_three_upper_bound_pct": rule_of_three_bound_pct,
            "seed": seed,
        },
        "human_audit_batch": human_audit_batch,
        "full_results": results,
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_artifact, f, indent=2)

    print(f"[CROSS-VAL] Comprehensive audit saved to: {output_path}")
    return summary_artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Rigorous dual-engine cross-validation of PDF page locators.")
    parser.add_argument("--sampled-json", default=QASPER_SAMPLED_PATH)
    parser.add_argument("--pdfs-dir", default=PDFS_DIR)
    parser.add_argument("--output", default=AUDIT_OUTPUT_PATH)
    parser.add_argument("--audit-size", type=int, default=75)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_rigorous_cross_validation(
        sampled_json=args.sampled_json,
        pdfs_dir=args.pdfs_dir,
        output_path=args.output,
        target_audit_size=args.audit_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
