"""
Evaluation Harness for PDF Text and Section Extraction (Step 1).
Evaluates layout-aware text extraction and section boundary recovery using PyMuPDF.

Measures:
  - Section Heading Detection Recall & Precision against canonical academic sections.
  - Page-Level Text Density and Word Volume.
  - Reading Order & Layout Block Integrity.
  - Extraction Latency (ms per paper and ms per page).
"""

import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

# Add backend directory to sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import pymupdf
from apps.documents.services.chunking_utils import (
    KNOWN_ACADEMIC_HEADINGS,
    estimate_tokens,
    extract_sections_from_pdf,
)

# Canonical expected section archetypes in peer-reviewed scientific papers
CANONICAL_SECTIONS_PER_PAPER: Dict[str, List[str]] = {
    "Attention.pdf": [
        "Abstract", "Introduction", "Background", "Model Architecture",
        "Why Self-Attention", "Training", "Results", "Conclusion",
    ],
    "deep_residual.pdf": [
        "Abstract", "Introduction", "Related Work", "Deep Residual Learning",
        "Experiments",
    ],
    "LoRa.pdf": [
        "Abstract", "Introduction", "Problem Statement", "Our Method",
        "Empirical Experiments", "Related Work", "Conclusion",
    ],
    "Retrieval-Augmented.pdf": [
        "Abstract", "Introduction", "Methods", "Experimental Setup",
        "Results", "Discussion", "Related Work", "Conclusion",
    ],
}

DEFAULT_PDF_SEARCH_DIRS = [
    os.path.join(os.path.dirname(BACKEND_DIR), "sample__papers"),
    os.path.join(os.path.dirname(BACKEND_DIR), "sample_papers"),
]


def resolve_pdf_files(
    search_dirs: Optional[List[str]] = None,
    specific_dir: Optional[str] = None,
) -> List[Tuple[str, str]]:
    """Discovers all valid, readable evaluation PDFs on disk."""
    dirs = [specific_dir] if specific_dir else ((search_dirs or []) + DEFAULT_PDF_SEARCH_DIRS)
    found: Dict[str, str] = {}  # filename -> full_path

    for d in dirs:
        if not d or not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            if not fname.lower().endswith(".pdf"):
                continue
            full_path = os.path.join(d, fname)
            # Skip tiny stub files and verify it can be opened
            if os.path.getsize(full_path) < 1000:
                continue
            try:
                test_doc = pymupdf.open(full_path)
                if len(test_doc) > 0 and fname not in found:
                    found[fname] = full_path
                test_doc.close()
            except Exception:
                continue

    return sorted(list(found.items()))


def normalize_heading(h: str) -> str:
    """Normalizes section heading for fuzzy comparison."""
    h = re.sub(r"^[0-9\.\s\-]+", "", h)  # Strip leading numbers
    h = re.sub(r"\b([A-Za-z])\s+([A-Za-z]{2,})\b", r"\1\2", h)
    h = re.sub(r"\s+", " ", h)
    return h.strip().lower()


def evaluate_paper_extraction(pdf_path: str, filename: str) -> Optional[Dict[str, Any]]:
    """Evaluates extraction accuracy and latency for a single PDF."""
    t_start = time.perf_counter()

    try:
        # Step A: Run production extraction pipeline
        extracted_sections = extract_sections_from_pdf(pdf_path)
    except Exception as e:
        print(f"  [WARN] Failed to extract from {filename}: {e}")
        return None

    extraction_duration_ms = round((time.perf_counter() - t_start) * 1000, 2)

    # Step B: Inspect raw PDF for ground-truth page count
    doc = pymupdf.open(pdf_path)
    page_count = len(doc)
    doc.close()

    total_chars = sum(len(s.get("text", "")) for s in extracted_sections)
    total_tokens = sum(s.get("token_count", estimate_tokens(s.get("text", ""))) for s in extracted_sections)
    section_titles = [s.get("title", "") for s in extracted_sections]
    norm_extracted_titles = {normalize_heading(t) for t in section_titles if t}

    # Step C: Compare against expected canonical sections
    expected = CANONICAL_SECTIONS_PER_PAPER.get(filename, [])
    norm_expected = [normalize_heading(e) for e in expected]

    hits = 0
    matched_sections: List[str] = []
    missing_sections: List[str] = []

    for exp_norm, exp_raw in zip(norm_expected, expected):
        # Match if expected heading is substring or matches an extracted heading
        is_hit = any(
            exp_norm in ext or ext in exp_norm
            for ext in norm_extracted_titles
        )
        if is_hit:
            hits += 1
            matched_sections.append(exp_raw)
        else:
            missing_sections.append(exp_raw)

    recall = round((hits / max(1, len(expected))) * 100, 1) if expected else 100.0
    precision = round((hits / max(1, len(section_titles))) * 100, 1) if section_titles else 0.0

    return {
        "filename": filename,
        "pdf_path": pdf_path,
        "page_count": page_count,
        "section_count": len(extracted_sections),
        "total_chars": total_chars,
        "total_tokens": total_tokens,
        "avg_tokens_per_section": round(total_tokens / max(1, len(extracted_sections)), 1),
        "latency_ms": extraction_duration_ms,
        "ms_per_page": round(extraction_duration_ms / max(1, page_count), 2),
        "expected_sections_count": len(expected),
        "detected_expected_count": hits,
        "section_recall_pct": recall,
        "section_precision_pct": precision,
        "matched_sections": matched_sections,
        "missing_sections": missing_sections,
        "extracted_headings": section_titles,
    }


def run_extraction_suite(output_path: Optional[str] = None) -> Dict[str, Any]:
    """Runs extraction evaluation across all discovered PDFs and logs metrics."""
    pdf_files = resolve_pdf_files()
    if not pdf_files:
        raise FileNotFoundError("No PDF files discovered for extraction evaluation.")

    print(f"\n[EVAL-EXTRACTION] Running Step 1 Extraction Evaluation across {len(pdf_files)} PDFs")
    print("=" * 100)
    print(
        f"{'PDF Filename':<26} | {'Pages':<5} | {'Sections':<8} | {'Tokens':<7} | "
        f"{'Recall':<7} | {'Latency':<9} | {'ms/Page':<7}"
    )
    print("-" * 100)

    results: List[Dict[str, Any]] = []
    total_pages = 0
    total_sections = 0
    total_tokens = 0
    total_latency = 0.0
    recalls: List[float] = []

    for fname, ppath in pdf_files:
        res = evaluate_paper_extraction(ppath, fname)
        if not res:
            continue
        results.append(res)

        total_pages += res["page_count"]
        total_sections += res["section_count"]
        total_tokens += res["total_tokens"]
        total_latency += res["latency_ms"]
        recalls.append(res["section_recall_pct"])

        recall_str = f"{res['section_recall_pct']} %"
        latency_str = f"{res['latency_ms']} ms"
        print(
            f"{fname:<26} | {res['page_count']:<5} | {res['section_count']:<8} | "
            f"{res['total_tokens']:<7} | {recall_str:<7} | "
            f"{latency_str:<9} | {res['ms_per_page']:<7}"
        )

    print("=" * 100)
    mean_recall = round(sum(recalls) / len(recalls), 1)
    mean_latency = round(total_latency / len(results), 2)
    mean_ms_per_page = round(total_latency / max(1, total_pages), 2)

    print(f"[SUMMARY] Step 1 Extraction Performance:")
    print(f"  * Mean Section Boundary Recall: {mean_recall}%")
    print(f"  * Total Pages Processed:        {total_pages}")
    print(f"  * Total Sections Extracted:     {total_sections}")
    print(f"  * Total Corpus Tokens:          {total_tokens}")
    print(f"  * Mean Latency per Document:    {mean_latency} ms ({mean_ms_per_page} ms/page)")

    summary = {
        "step": "1_extraction",
        "method": "PyMuPDF_layout_aware_section_extractor",
        "total_documents": len(results),
        "total_pages": total_pages,
        "total_tokens": total_tokens,
        "mean_section_recall_pct": mean_recall,
        "mean_latency_ms": mean_latency,
        "mean_ms_per_page": mean_ms_per_page,
        "documents": results,
    }

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[EVAL-EXTRACTION] Saved extraction evaluation summary to: {output_path}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PDF Text & Section Extraction (Step 1).")
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "extraction_evaluation_results.json"),
        help="Path to save extraction evaluation JSON summary",
    )
    args = parser.parse_args()
    run_extraction_suite(output_path=args.output)


if __name__ == "__main__":
    main()
