"""
Step 1 Full-Dev Corpus PDF Extraction, CER & 3-Engine Benchmark (Workstream 2).
Evaluates extraction performance across the 48 Dev papers against QASPER TeX ground truth:
  - Engine A: Improved PyMuPDF Layout-Aware Parser (Local Production)
  - Engine B: Grobid REST API (TEI/XML Fulltext Processing with Local Caching)
  - Engine C: Nougat Vision-Transformer (Markdown Extraction via Colab Cache / Live API)

Metrics:
  - Section Heading Recall (%)
  - Character Error Rate (CER) and Character Accuracy (1 - CER)
  - Extraction Latency (ms/doc and ms/page)
"""

import argparse
import difflib
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from apps.documents.services.chunking_utils import (
    estimate_tokens,
    extract_sections_from_pdf,
)

DEV_SPLIT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
CORPUS_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
DEV_PDF_DIRS = [
    WORKSPACE_ROOT / "eval" / "pdfs" / "dev",
    WORKSPACE_ROOT / "eval" / "data" / "pdfs",
    WORKSPACE_ROOT / "sample__papers",
]
GROBID_CACHE_DIR = WORKSPACE_ROOT / "eval" / "cache" / "grobid"
NOUGAT_CACHE_DIR = WORKSPACE_ROOT / "eval" / "cache" / "nougat"
OUTPUT_BENCHMARK_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "step1_full_dev_extraction_benchmark.json"

DEFAULT_GROBID_URL = os.getenv("GROBID_API_URL", "https://grobidOrg-grobid.hf.space/api/processFulltextDocument")
DEFAULT_NOUGAT_URL = os.getenv("NOUGAT_API_URL", "")


def compute_levenshtein_cer(reference: str, hypothesis: str, sample_max_chars: int = 5000) -> Tuple[float, float]:
    """
    Computes Character Error Rate (CER) and Character Accuracy (1 - CER) using SequenceMatcher.
    Sampled to sample_max_chars for high-speed deterministic alignment across large papers.
    """
    ref_sub = re.sub(r"\s+", " ", reference.strip()[:sample_max_chars])
    hyp_sub = re.sub(r"\s+", " ", hypothesis.strip()[:sample_max_chars])

    if not ref_sub:
        return 0.0, 1.0

    matcher = difflib.SequenceMatcher(None, ref_sub, hyp_sub)
    match_chars = sum(block.size for block in matcher.get_matching_blocks())
    total_ref = len(ref_sub)

    # Edit distance approximation: insertions + deletions + substitutions
    cer = max(0.0, min(1.0, 1.0 - (match_chars / max(1, total_ref))))
    accuracy = 1.0 - cer
    return round(cer, 4), round(accuracy, 4)


def normalize_title(t: str) -> str:
    """Normalizes section titles for fuzzy recall matching."""
    t = re.sub(r"^[0-9\.\s\-]+", "", t)
    t = re.sub(r"\b([A-Za-z])\s+([A-Za-z]{2,})\b", r"\1\2", t)
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def find_pdf_for_aid(aid: str) -> Optional[Path]:
    """Finds physical PDF across configured search directories."""
    for d in DEV_PDF_DIRS:
        cand = d / f"{aid}.pdf"
        if cand.exists() and cand.stat().st_size > 10000:
            return cand
    return None


# ─── Engine A: Local PyMuPDF Parser ─────────────────────────────────────────
def run_engine_a_pymupdf(pdf_path: Path) -> Dict[str, Any]:
    t0 = time.perf_counter()
    sections = extract_sections_from_pdf(str(pdf_path))
    latency_ms = (time.perf_counter() - t0) * 1000.0

    full_text = "\n\n".join(s.get("text", "") for s in sections)
    headings = [s.get("title", "") for s in sections if s.get("title")]

    return {
        "engine": "PyMuPDF_Local",
        "latency_ms": round(latency_ms, 2),
        "sections_count": len(sections),
        "extracted_headings": headings,
        "full_text": full_text,
    }


# ─── Engine B: Grobid REST API ───────────────────────────────────────────────
def run_engine_b_grobid(pdf_path: Path, paper_id: str, timeout: int = 40) -> Dict[str, Any]:
    GROBID_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = GROBID_CACHE_DIR / f"{paper_id}.xml"

    xml_content = ""
    is_cached = False
    latency_ms = 0.0

    if cache_file.exists() and cache_file.stat().st_size > 500:
        with open(cache_file, "r", encoding="utf-8") as f:
            xml_content = f.read()
        is_cached = True
    else:
        t0 = time.perf_counter()
        try:
            with open(pdf_path, "rb") as f:
                files = {"input": (pdf_path.name, f, "application/pdf")}
                r = requests.post(DEFAULT_GROBID_URL, files=files, timeout=timeout)
                if r.status_code == 200:
                    xml_content = r.text
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(xml_content)
                else:
                    logger_msg = f"Grobid returned HTTP {r.status_code}"
        except Exception as exc:
            logger_msg = f"Grobid request failed: {exc}"
        latency_ms = (time.perf_counter() - t0) * 1000.0

    headings = []
    paragraphs = []
    if xml_content:
        try:
            root = ET.fromstring(xml_content)
            # Find TEI namespace
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}
            for head in root.findall(".//tei:div/tei:head", ns):
                if head.text:
                    headings.append(head.text.strip())
            for p in root.findall(".//tei:div/tei:p", ns):
                if p.text:
                    paragraphs.append(p.text.strip())
        except Exception:
            pass

    full_text = "\n\n".join(paragraphs) if paragraphs else xml_content[:10000]
    return {
        "engine": "Grobid_TEI",
        "latency_ms": round(latency_ms, 2),
        "is_cached": is_cached,
        "available": bool(xml_content),
        "sections_count": len(headings),
        "extracted_headings": headings,
        "full_text": full_text,
    }


# ─── Engine C: Nougat Vision-Transformer ─────────────────────────────────────
def run_engine_c_nougat(pdf_path: Path, paper_id: str) -> Dict[str, Any]:
    NOUGAT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = NOUGAT_CACHE_DIR / f"{paper_id}.mmd"

    mmd_content = ""
    is_cached = False
    latency_ms = 0.0

    if cache_file.exists() and cache_file.stat().st_size > 200:
        with open(cache_file, "r", encoding="utf-8") as f:
            mmd_content = f.read()
        is_cached = True
    elif DEFAULT_NOUGAT_URL:
        t0 = time.perf_counter()
        try:
            with open(pdf_path, "rb") as f:
                r = requests.post(f"{DEFAULT_NOUGAT_URL}/predict", files={"file": f}, timeout=60)
                if r.status_code == 200:
                    mmd_content = r.text
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(mmd_content)
        except Exception:
            pass
        latency_ms = (time.perf_counter() - t0) * 1000.0

    headings = []
    if mmd_content:
        for line in mmd_content.splitlines():
            line_str = line.strip()
            if line_str.startswith("#") and not line_str.startswith("###"):
                title = re.sub(r"^#+\s*", "", line_str)
                if len(title) > 2:
                    headings.append(title)

    return {
        "engine": "Nougat_Vision",
        "latency_ms": round(latency_ms, 2),
        "is_cached": is_cached,
        "available": bool(mmd_content),
        "sections_count": len(headings),
        "extracted_headings": headings,
        "full_text": mmd_content,
        "status": "cached" if is_cached else ("live_api" if mmd_content else "colab_batch_ready"),
    }


def main():
    parser = argparse.ArgumentParser(description="Step 1 Full-Dev Extraction & CER Benchmark")
    parser.add_argument("--max-papers", type=int, default=48, help="Max papers to evaluate")
    parser.add_argument("--include-grobid", action="store_true", default=False, help="Include live Grobid API calls")
    args = parser.parse_args()

    print("=== STEP 1 FULL-DEV CORPUS EXTRACTION BENCHMARK ===")
    print(f"Loading Dev Papers from: {DEV_SPLIT_PATH}")
    print(f"Loading Ground-Truth Corpus from: {CORPUS_PATH}\n")

    with open(DEV_SPLIT_PATH, "r", encoding="utf-8") as f:
        dev_aids = json.load(f)["dev_papers"][: args.max_papers]

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)

    results_per_paper: List[Dict[str, Any]] = []
    engine_stats = {
        "PyMuPDF": {"recalls": [], "accuracies": [], "latencies": []},
        "Grobid": {"recalls": [], "accuracies": [], "latencies": []},
        "Nougat": {"recalls": [], "accuracies": [], "latencies": []},
    }

    evaluated_count = 0
    missing_pdf_count = 0

    for idx, aid in enumerate(dev_aids, start=1):
        pdf_file = find_pdf_for_aid(aid)
        if not pdf_file:
            missing_pdf_count += 1
            continue

        gold_doc = corpus_all.get(aid, {})
        gold_sections = gold_doc.get("sections", [])
        gold_headings = [s.get("title", s.get("heading", "")) for s in gold_sections if s.get("title") or s.get("heading")]
        gold_text = "\n\n".join(s.get("text", "") for s in gold_sections)
        norm_gold = {normalize_title(h) for h in gold_headings if normalize_title(h)}

        # 1. Run Engine A (PyMuPDF)
        res_a = run_engine_a_pymupdf(pdf_file)
        norm_a = {normalize_title(h) for h in res_a["extracted_headings"] if normalize_title(h)}
        matched_a = len(norm_a.intersection(norm_gold))
        recall_a = round((matched_a / max(1, len(norm_gold))) * 100.0, 2)
        cer_a, acc_a = compute_levenshtein_cer(gold_text, res_a["full_text"])

        engine_stats["PyMuPDF"]["recalls"].append(recall_a)
        engine_stats["PyMuPDF"]["accuracies"].append(acc_a)
        engine_stats["PyMuPDF"]["latencies"].append(res_a["latency_ms"])

        # 2. Run Engine B (Grobid)
        res_b = {"available": False, "status": "skipped"}
        if args.include_grobid or (GROBID_CACHE_DIR / f"{aid}.xml").exists():
            res_b = run_engine_b_grobid(pdf_file, aid)
            if res_b.get("available"):
                norm_b = {normalize_title(h) for h in res_b["extracted_headings"] if normalize_title(h)}
                matched_b = len(norm_b.intersection(norm_gold))
                recall_b = round((matched_b / max(1, len(norm_gold))) * 100.0, 2)
                cer_b, acc_b = compute_levenshtein_cer(gold_text, res_b["full_text"])
                engine_stats["Grobid"]["recalls"].append(recall_b)
                engine_stats["Grobid"]["accuracies"].append(acc_b)
                engine_stats["Grobid"]["latencies"].append(res_b["latency_ms"])

        # 3. Run Engine C (Nougat)
        res_c = run_engine_c_nougat(pdf_file, aid)
        if res_c.get("available"):
            norm_c = {normalize_title(h) for h in res_c["extracted_headings"] if normalize_title(h)}
            matched_c = len(norm_c.intersection(norm_gold))
            recall_c = round((matched_c / max(1, len(norm_gold))) * 100.0, 2)
            cer_c, acc_c = compute_levenshtein_cer(gold_text, res_c["full_text"])
            engine_stats["Nougat"]["recalls"].append(recall_c)
            engine_stats["Nougat"]["accuracies"].append(acc_c)

        evaluated_count += 1
        results_per_paper.append({
            "paper_arxiv_id": aid,
            "gold_headings_count": len(gold_headings),
            "pymupdf": {
                "heading_recall_pct": recall_a,
                "char_accuracy_pct": round(acc_a * 100.0, 2),
                "cer": cer_a,
                "latency_ms": res_a["latency_ms"],
                "extracted_sections": res_a["sections_count"],
            },
            "grobid": {
                "available": res_b.get("available", False),
                "heading_recall_pct": engine_stats["Grobid"]["recalls"][-1] if engine_stats["Grobid"]["recalls"] else None,
            },
            "nougat": {
                "status": res_c.get("status", "colab_batch_ready"),
                "available": res_c.get("available", False),
            },
        })

        if evaluated_count % 5 == 0 or evaluated_count == 1:
            print(f"[{evaluated_count}] arXiv:{aid} -> PyMuPDF Recall: {recall_a:5.1f}%, 1-CER: {acc_a * 100:5.1f}%, Latency: {res_a['latency_ms']:6.1f} ms")

    # Macro averages
    macro_summary = {}
    for eng, vals in engine_stats.items():
        if vals["recalls"]:
            macro_summary[eng] = {
                "papers_evaluated": len(vals["recalls"]),
                "mean_heading_recall_pct": round(sum(vals["recalls"]) / len(vals["recalls"]), 2),
                "mean_char_accuracy_pct": round((sum(vals["accuracies"]) / len(vals["accuracies"])) * 100.0, 2),
                "mean_latency_ms": round(sum(vals["latencies"]) / len(vals["latencies"]), 2) if vals["latencies"] else 0.0,
            }

    out_payload = {
        "benchmark": "Step 1 Full-Dev 48-Paper PDF Extraction & CER Benchmark",
        "date": "2026-10-17",
        "total_dev_papers": len(dev_aids),
        "evaluated_papers": evaluated_count,
        "missing_local_pdfs": missing_pdf_count,
        "macro_summary": macro_summary,
        "per_paper_results": results_per_paper,
    }

    OUTPUT_BENCHMARK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_BENCHMARK_PATH, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)

    print("\n=== STEP 1 EXTRACTION BENCHMARK SUMMARY ===")
    print(f"Evaluated Papers: {evaluated_count}/{len(dev_aids)} (Missing PDFs: {missing_pdf_count})")
    for eng, stats in macro_summary.items():
        print(f"Engine: {eng:<12} | Mean Heading Recall: {stats['mean_heading_recall_pct']:5.1f}% | Mean 1-CER Accuracy: {stats['mean_char_accuracy_pct']:5.1f}% | Latency: {stats['mean_latency_ms']:6.1f} ms/doc")
    print(f"Results serialized to: {OUTPUT_BENCHMARK_PATH.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()
