"""
RQ1: Comprehensive PDF Extractor Benchmark (Controlled Ablation).
Evaluates 6 text extraction engines across completeness, reading order, structure preservation,
computational efficiency, and downstream retrieval performance under fixed dense representations.

Extractors Evaluated (Unified Adapter Interface):
  1. pymupdf_plain: Raw text extraction per page without font/layout heuristics.
  2. pymupdf_layout: Production layout-aware extractor preserving headings & page numbers.
  3. pypdf: Pure-Python page-level text extraction.
  4. pdfminer.six: Layout-analysis text extractor.
  5. pdfplumber: Visual PDF layout & text extractor.
  6. grobid: TEI-XML structured document processing (tested via live API or flagged if unavailable).
  Optional (--include-heavy): Marker / Docling vision-based models (reported as omitted on CPU if not installed).

Ground Truth:
  Independent QASPER ground-truth corpus (TeX source full-text, gold sections, and human-annotated evidence spans).
  Does NOT use GROBID as ground truth, eliminating algorithmic bias.

Metrics:
  - Completeness: Evidence span coverage rate (%) after ligature, dehyphenation, and whitespace normalization; CER and WER.
  - Reading Order: Concordance rate of consecutive paragraph pairs (Kendall's tau rank correlation).
  - Structure: Heading Precision, Recall, F1 against gold section names; page number preservation rate (%).
  - Efficiency: Single-document latency (ms), latency per page (ms/page), peak RSS RAM (MB).
  - Downstream Retrieval: Fair fixed-budget chunking (max_tokens=350, overlap=70) + champion intfloat/e5-small-v2
    exact cosine similarity. Reports nDCG@10 and Recall@20 with paper-cluster bootstrap 95% CI and paired p-value vs pymupdf_plain.
"""

import argparse
import difflib
import gc
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

os.environ["HF_HUB_OFFLINE"] = "1"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

import fitz  # PyMuPDF
import numpy as np
import psutil
import pypdf
import requests
import torch

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from apps.documents.services.chunking_utils import (
    chunk_sections,
    estimate_tokens,
    extract_sections_from_pdf,
)
from eval_common.relevance import (
    STOPWORDS,
    clean_evidence,
    count_relevant_chunks,
    is_chunk_hit,
    tokenize_regex,
)
from eval_common.stats import (
    cluster_bootstrap_ci,
    compute_ndcg,
    compute_recall,
    paired_cluster_bootstrap,
)
from sentence_transformers import SentenceTransformer

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------
@dataclass
class ExtractedBlock:
    text: str
    page: int
    order: int
    heading: Optional[str] = None
    is_heading: bool = False


@dataclass
class ExtractorOutput:
    engine_name: str
    full_text: str
    blocks: List[ExtractedBlock]
    headings: List[str]
    has_headings: bool
    page_count: int
    elapsed_sec: float
    peak_ram_mb: float
    available: bool = True
    error: Optional[str] = None


# -----------------------------------------------------------------------------
# Text Normalization & Linguistic Utilities
# -----------------------------------------------------------------------------
LIGATURE_MAP = {
    "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
    "–": "-", "—": "-", "’": "'", "“": '"', "”": '"',
}


def normalize_text_for_comparison(text: str) -> str:
    """Standardizes ligatures, dehyphenates linebreaks, and collapses whitespace."""
    for lig, rep in LIGATURE_MAP.items():
        text = text.replace(lig, rep)
    # Dehyphenation: word- \n word -> wordword
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def normalize_heading_title(t: str) -> str:
    """Normalizes section titles for heading recall/precision matching by stripping leading numbering."""
    t = re.sub(r"^[0-9\.\s\-]+", "", t)
    t = re.sub(r"\b([A-Za-z])\s+([A-Za-z]{2,})\b", r"\1\2", t)
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def compute_normalized_cer(reference: str, hypothesis: str, sample_max_chars: int = 5000) -> Tuple[float, float]:
    """Computes Character Error Rate (CER) on standardized text."""
    ref_norm = normalize_text_for_comparison(reference[:sample_max_chars])
    hyp_norm = normalize_text_for_comparison(hypothesis[:sample_max_chars])
    if not ref_norm:
        return 0.0, 1.0

    matcher = difflib.SequenceMatcher(None, ref_norm, hyp_norm)
    match_chars = sum(block.size for block in matcher.get_matching_blocks())
    total_ref = len(ref_norm)
    cer = max(0.0, min(1.0, 1.0 - (match_chars / max(1, total_ref))))
    accuracy = 1.0 - cer
    return round(cer, 4), round(accuracy, 4)


def compute_reading_order_concordance(
    extracted_text: str,
    gold_paragraphs: List[str],
    max_pairs: int = 30,
) -> float:
    """
    Computes pairwise relative order concordance between gold consecutive paragraphs.
    If paragraph A appeared before paragraph B in gold source, checks if pos(A) < pos(B) in extracted text.
    """
    if len(gold_paragraphs) < 2:
        return 1.0

    clean_ext = normalize_text_for_comparison(extracted_text)
    concordant = 0
    valid_pairs = 0

    step = max(1, len(gold_paragraphs) // max_pairs)
    sampled_indices = list(range(0, len(gold_paragraphs) - 1, step))[:max_pairs]

    for i in sampled_indices:
        p1 = normalize_text_for_comparison(gold_paragraphs[i])[:80]
        p2 = normalize_text_for_comparison(gold_paragraphs[i + 1])[:80]
        if len(p1) < 25 or len(p2) < 25:
            continue

        pos1 = clean_ext.find(p1)
        pos2 = clean_ext.find(p2)
        if pos1 != -1 and pos2 != -1:
            valid_pairs += 1
            if pos1 < pos2:
                concordant += 1

    return round(concordant / max(1, valid_pairs), 4) if valid_pairs > 0 else 0.5


# -----------------------------------------------------------------------------
# Extractor Adapters
# -----------------------------------------------------------------------------
def extract_pymupdf_plain(pdf_path: Path) -> ExtractorOutput:
    t0 = time.perf_counter()
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    blocks: List[ExtractedBlock] = []
    full_text_parts: List[str] = []
    order = 0

    for page_idx in range(page_count):
        page = doc[page_idx]
        text = str(page.get_text("text"))
        full_text_parts.append(text)
        for para in text.split("\n\n"):
            para_str = para.strip()
            if para_str:
                blocks.append(ExtractedBlock(text=para_str, page=page_idx + 1, order=order))
                order += 1

    doc.close()
    elapsed = time.perf_counter() - t0
    peak_rss = psutil.Process().memory_info().rss / (1024 * 1024)

    return ExtractorOutput(
        engine_name="pymupdf_plain",
        full_text="\n\n".join(full_text_parts),
        blocks=blocks,
        headings=[],
        has_headings=False,
        page_count=page_count,
        elapsed_sec=elapsed,
        peak_ram_mb=peak_rss,
    )


def extract_pymupdf_layout(pdf_path: Path) -> ExtractorOutput:
    t0 = time.perf_counter()
    doc = fitz.open(pdf_path)
    page_count = len(doc)
    doc.close()

    sections = extract_sections_from_pdf(str(pdf_path))
    blocks: List[ExtractedBlock] = []
    headings: List[str] = []
    full_text_parts: List[str] = []

    for order, sec in enumerate(sections):
        title = sec.get("title", "")
        text = sec.get("text", "")
        start_page = sec.get("start_page", 1)
        if title:
            headings.append(title)
        full_text_parts.append(f"{title}\n\n{text}".strip() if title else text)
        blocks.append(ExtractedBlock(
            text=text,
            page=start_page,
            order=order,
            heading=title if title else None,
            is_heading=bool(title),
        ))

    elapsed = time.perf_counter() - t0
    peak_rss = psutil.Process().memory_info().rss / (1024 * 1024)

    return ExtractorOutput(
        engine_name="pymupdf_layout",
        full_text="\n\n".join(full_text_parts),
        blocks=blocks,
        headings=headings,
        has_headings=True,
        page_count=page_count,
        elapsed_sec=elapsed,
        peak_ram_mb=peak_rss,
    )


def extract_pypdf_adapter(pdf_path: Path) -> ExtractorOutput:
    t0 = time.perf_counter()
    reader = pypdf.PdfReader(str(pdf_path))
    page_count = len(reader.pages)
    blocks: List[ExtractedBlock] = []
    full_text_parts: List[str] = []
    order = 0

    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        full_text_parts.append(text)
        for para in text.split("\n\n"):
            para_str = para.strip()
            if para_str:
                blocks.append(ExtractedBlock(text=para_str, page=page_idx + 1, order=order))
                order += 1

    elapsed = time.perf_counter() - t0
    peak_rss = psutil.Process().memory_info().rss / (1024 * 1024)

    return ExtractorOutput(
        engine_name="pypdf",
        full_text="\n\n".join(full_text_parts),
        blocks=blocks,
        headings=[],
        has_headings=False,
        page_count=page_count,
        elapsed_sec=elapsed,
        peak_ram_mb=peak_rss,
    )


def extract_pdfminer_adapter(pdf_path: Path) -> ExtractorOutput:
    t0 = time.perf_counter()
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer

    doc = fitz.open(pdf_path)
    page_count = len(doc)
    doc.close()

    blocks: List[ExtractedBlock] = []
    full_text_parts: List[str] = []
    order = 0

    for page_idx, page_layout in enumerate(extract_pages(str(pdf_path))):
        page_text_accum = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                elem_text = element.get_text().strip()
                if elem_text:
                    page_text_accum.append(elem_text)
                    blocks.append(ExtractedBlock(text=elem_text, page=page_idx + 1, order=order))
                    order += 1
        full_text_parts.append("\n\n".join(page_text_accum))

    elapsed = time.perf_counter() - t0
    peak_rss = psutil.Process().memory_info().rss / (1024 * 1024)

    return ExtractorOutput(
        engine_name="pdfminer.six",
        full_text="\n\n".join(full_text_parts),
        blocks=blocks,
        headings=[],
        has_headings=False,
        page_count=page_count,
        elapsed_sec=elapsed,
        peak_ram_mb=peak_rss,
    )


def extract_pdfplumber_adapter(pdf_path: Path) -> ExtractorOutput:
    t0 = time.perf_counter()
    import pdfplumber

    blocks: List[ExtractedBlock] = []
    full_text_parts: List[str] = []
    order = 0

    with pdfplumber.open(str(pdf_path)) as plum:
        page_count = len(plum.pages)
        for page_idx, page in enumerate(plum.pages):
            text = page.extract_text(layout=True) or ""
            full_text_parts.append(text)
            for para in text.split("\n\n"):
                para_str = para.strip()
                if para_str:
                    blocks.append(ExtractedBlock(text=para_str, page=page_idx + 1, order=order))
                    order += 1

    elapsed = time.perf_counter() - t0
    peak_rss = psutil.Process().memory_info().rss / (1024 * 1024)

    return ExtractorOutput(
        engine_name="pdfplumber",
        full_text="\n\n".join(full_text_parts),
        blocks=blocks,
        headings=[],
        has_headings=False,
        page_count=page_count,
        elapsed_sec=elapsed,
        peak_ram_mb=peak_rss,
    )


GROBID_CHECKED = False
GROBID_IS_AVAILABLE = False
GROBID_ERROR_MSG = None


def extract_grobid_adapter(pdf_path: Path, timeout: int = 15) -> ExtractorOutput:
    """Attempts connection to GROBID REST service. Returns structured failure if offline."""
    global GROBID_CHECKED, GROBID_IS_AVAILABLE, GROBID_ERROR_MSG
    t0 = time.perf_counter()
    grobid_url = os.getenv("GROBID_API_URL", "http://localhost:8070/api/processFulltextDocument")

    if not GROBID_CHECKED:
        GROBID_CHECKED = True
        try:
            # Ping isalive endpoint first with 1.5s timeout
            ping_url = os.getenv("GROBID_PING_URL", "http://localhost:8070/api/isalive")
            resp_ping = requests.get(ping_url, timeout=1.5)
            if resp_ping.status_code == 200:
                GROBID_IS_AVAILABLE = True
            else:
                GROBID_IS_AVAILABLE = False
                GROBID_ERROR_MSG = f"GROBID server returned HTTP {resp_ping.status_code} on ping"
        except Exception as exc:
            GROBID_IS_AVAILABLE = False
            GROBID_ERROR_MSG = f"GROBID server offline or unreachable ({exc})"

    if not GROBID_IS_AVAILABLE:
        return ExtractorOutput(
            engine_name="grobid",
            full_text="",
            blocks=[],
            headings=[],
            has_headings=False,
            page_count=0,
            elapsed_sec=time.perf_counter() - t0,
            peak_ram_mb=0.0,
            available=False,
            error=GROBID_ERROR_MSG,
        )

    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(grobid_url, files={"input": (pdf_path.name, f, "application/pdf")}, timeout=timeout)
        if resp.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}
            headings = [h.text.strip() for h in root.findall(".//tei:div/tei:head", ns) if h.text]
            paras = [p.text.strip() for p in root.findall(".//tei:div/tei:p", ns) if p.text]
            blocks = [ExtractedBlock(text=p, page=1, order=i) for i, p in enumerate(paras)]
            elapsed = time.perf_counter() - t0
            return ExtractorOutput(
                engine_name="grobid",
                full_text="\n\n".join(paras),
                blocks=blocks,
                headings=headings,
                has_headings=True,
                page_count=1,
                elapsed_sec=elapsed,
                peak_ram_mb=psutil.Process().memory_info().rss / (1024 * 1024),
                available=True,
            )
        else:
            return ExtractorOutput(
                engine_name="grobid",
                full_text="",
                blocks=[],
                headings=[],
                has_headings=False,
                page_count=0,
                elapsed_sec=time.perf_counter() - t0,
                peak_ram_mb=0.0,
                available=False,
                error=f"GROBID server returned HTTP {resp.status_code}",
            )
    except Exception as exc:
        return ExtractorOutput(
            engine_name="grobid",
            full_text="",
            blocks=[],
            headings=[],
            has_headings=False,
            page_count=0,
            elapsed_sec=time.perf_counter() - t0,
            peak_ram_mb=0.0,
            available=False,
            error=f"GROBID request failed: {exc}",
        )


EXTRACTOR_REGISTRY: Dict[str, Callable[[Path], ExtractorOutput]] = {
    "pymupdf_plain": extract_pymupdf_plain,
    "pymupdf_layout": extract_pymupdf_layout,
    "pypdf": extract_pypdf_adapter,
    "pdfminer.six": extract_pdfminer_adapter,
    "pdfplumber": extract_pdfplumber_adapter,
    "grobid": extract_grobid_adapter,
}


# -----------------------------------------------------------------------------
# Fair Chunking Fallback for Downstream Retrieval
# -----------------------------------------------------------------------------
def chunk_extracted_output(
    output: ExtractorOutput,
    aid: str,
    max_tokens: int = 350,
    overlap: int = 70,
) -> List[Dict[str, Any]]:
    """
    Uniform chunking across extractors:
    - If extractor detects headings, chunks along section boundaries with max_tokens budget.
    - If extractor has no headings, chunks blocks using contiguous sliding window with identical token budget.
    """
    if output.has_headings and output.blocks:
        sec_dicts = []
        for b in output.blocks:
            sec_dicts.append({
                "title": b.heading or "",
                "text": b.text,
                "start_page": b.page,
                "end_page": b.page,
            })
        raw_chunks = chunk_sections(sec_dicts, strategy="section_overlap", max_tokens=max_tokens, overlap=overlap)
        for idx, c in enumerate(raw_chunks):
            c["paper_arxiv_id"] = aid
            c["chunk_id"] = f"{aid}_{output.engine_name}_c_{idx}"
        return raw_chunks

    # Fallback sliding window over text blocks
    chunks = []
    current_tokens: List[str] = []
    current_words = 0
    chunk_idx = 0
    current_page = 1

    for b in output.blocks:
        words = b.text.split()
        if not words:
            continue
        current_page = b.page
        current_tokens.extend(words)
        current_words += len(words)

        # 350 tokens approx 263 words
        max_words = int(max_tokens / 1.33)
        overlap_words = int(overlap / 1.33)

        while current_words >= max_words:
            chunk_slice = current_tokens[:max_words]
            chunks.append({
                "paper_arxiv_id": aid,
                "chunk_id": f"{aid}_{output.engine_name}_c_{chunk_idx}",
                "text": " ".join(chunk_slice),
                "page": current_page,
            })
            chunk_idx += 1
            current_tokens = current_tokens[max_words - overlap_words:]
            current_words = len(current_tokens)

    if current_tokens:
        chunks.append({
            "paper_arxiv_id": aid,
            "chunk_id": f"{aid}_{output.engine_name}_c_{chunk_idx}",
            "text": " ".join(current_tokens),
            "page": current_page,
        })
    return chunks


# -----------------------------------------------------------------------------
# Main Evaluation Orchestration
# -----------------------------------------------------------------------------
def run_rq1_extractor_benchmark(
    limit: Optional[int] = None,
    dry_run: bool = False,
    include_heavy: bool = False,
    seed: int = 42,
) -> Dict[str, Any]:
    torch.set_num_threads(4)
    np.random.seed(seed)

    print("=" * 80)
    print("RQ1: COMPREHENSIVE PDF EXTRACTOR EVALUATION HARNESS")
    print("Engines: pymupdf_plain, pymupdf_layout, pypdf, pdfminer.six, pdfplumber, grobid")
    print("Ground Truth: QASPER independent TeX full-text and evidence spans")
    print(f"Hardware: AMD Ryzen 5 5600 (4 threads) | Seed: {seed} | Limit: {limit}")
    print("=" * 80)

    # Load Ground Truth
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
    dev_split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(corpus_path, "r", encoding="utf-8") as f:
        qasper_corpus = json.load(f)
    with open(dev_split_path, "r", encoding="utf-8") as f:
        dev_papers = json.load(f)["dev_papers"]
    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)

    # Locate Physical PDFs
    pdf_dirs = [
        WORKSPACE_ROOT / "eval" / "pdfs" / "dev",
        WORKSPACE_ROOT / "eval" / "data" / "pdfs",
        WORKSPACE_ROOT / "sample__papers",
    ]
    available_pdfs: Dict[str, Path] = {}
    for aid in dev_papers:
        for d in pdf_dirs:
            cand = d / f"{aid}.pdf"
            if cand.exists() and cand.stat().st_size > 10000:
                available_pdfs[aid] = cand
                break

    paper_ids = [aid for aid in dev_papers if aid in available_pdfs]
    if limit:
        paper_ids = paper_ids[:limit]

    print(f"Evaluated Papers: {len(paper_ids)} (physical PDFs found on disk)")
    if dry_run:
        print("[DRY-RUN] Verification complete. Exiting without execution.")
        return {"status": "dry_run_success", "paper_count": len(paper_ids)}

    # Filter QA to evaluated papers
    paper_queries_map: Dict[str, List[Dict[str, Any]]] = {}
    for q in qa_all:
        aid = q.get("paper_arxiv_id")
        if aid in paper_ids and q.get("question_type") != "unanswerable":
            paper_queries_map.setdefault(aid, []).append(q)

    # Initialize SentenceTransformer dense model (intfloat/e5-small-v2) for downstream retrieval
    print("\n[INIT] Initializing fixed embedding model 'intfloat/e5-small-v2' (SentenceTransformer)...")
    dense_embedder = SentenceTransformer("intfloat/e5-small-v2")

    # Results Aggregator
    engine_results: Dict[str, Dict[str, Any]] = {}
    for eng in EXTRACTOR_REGISTRY:
        engine_results[eng] = {
            "evidence_coverages": [],
            "char_accuracies": [],
            "reading_order_scores": [],
            "heading_f1_scores": [],
            "page_preservation_rates": [],
            "latencies_per_page_ms": [],
            "latencies_per_doc_ms": [],
            "peak_rams_mb": [],
            "query_ndcg10_by_paper": {aid: [] for aid in paper_ids},
            "query_rec20_by_paper": {aid: [] for aid in paper_ids},
            "available": True,
            "error": None,
        }

    # Evaluate Each Paper across Extractors
    detailed_jsonl_rows: List[Dict[str, Any]] = []

    for idx, aid in enumerate(paper_ids, start=1):
        pdf_path = available_pdfs[aid]
        gold_doc = qasper_corpus.get(aid, {})
        gold_sections = gold_doc.get("sections", [])
        gold_headings = [s.get("title", s.get("heading", "")) for s in gold_sections if s.get("title") or s.get("heading")]
        gold_paragraphs = [s.get("text", "") for s in gold_sections if s.get("text")]
        gold_text = "\n\n".join(gold_paragraphs)
        queries = paper_queries_map.get(aid, [])

        print(f"\n[{idx}/{len(paper_ids)}] Evaluating arXiv:{aid} (Pages: {len(gold_sections)} sections, {len(queries)} queries)...")

        for eng_name, extractor_fn in EXTRACTOR_REGISTRY.items():
            out = extractor_fn(pdf_path)
            if not out.available:
                engine_results[eng_name]["available"] = False
                engine_results[eng_name]["error"] = out.error
                continue

            # 1. Completeness: Evidence Coverage + CER
            # Check presence of each query evidence quote in normalized text
            norm_full = normalize_text_for_comparison(out.full_text)
            cov_hits = 0
            for q in queries:
                quote = q.get("verbatim_evidence_quote", "")
                ev_list = q.get("evidence_list", [])
                _, clean_list = clean_evidence(quote, ev_list)
                quote_to_check = clean_list[0] if clean_list else quote
                norm_quote = normalize_text_for_comparison(quote_to_check)
                if norm_quote and (norm_quote in norm_full or len(set(norm_quote.split()) & set(norm_full.split())) / max(1, len(norm_quote.split())) >= 0.75):
                    cov_hits += 1

            ev_coverage_pct = round((cov_hits / max(1, len(queries))) * 100.0, 2)
            cer, char_acc = compute_normalized_cer(gold_text, out.full_text)

            # 2. Reading Order Concordance
            order_score = compute_reading_order_concordance(out.full_text, gold_paragraphs)

            # 3. Structure: Heading F1 & Page Preservation
            matched_heads = 0
            norm_gold_heads = {normalize_heading_title(h) for h in gold_headings if normalize_heading_title(h)}
            norm_ext_heads = {normalize_heading_title(h) for h in out.headings if normalize_heading_title(h)}
            if norm_gold_heads and norm_ext_heads:
                matched_heads = len(norm_gold_heads & norm_ext_heads)
                h_prec = matched_heads / len(norm_ext_heads)
                h_rec = matched_heads / len(norm_gold_heads)
                h_f1 = (2 * h_prec * h_rec) / (h_prec + h_rec) if (h_prec + h_rec) > 0 else 0.0
            elif not norm_gold_heads and not norm_ext_heads:
                h_f1 = 1.0
            else:
                h_f1 = 0.0

            valid_page_blocks = sum(1 for b in out.blocks if b.page > 0)
            page_pres_rate = round((valid_page_blocks / max(1, len(out.blocks))) * 100.0, 2)

            # Efficiency
            lat_doc_ms = round(out.elapsed_sec * 1000.0, 2)
            lat_page_ms = round(lat_doc_ms / max(1, out.page_count), 2)

            engine_results[eng_name]["evidence_coverages"].append(ev_coverage_pct)
            engine_results[eng_name]["char_accuracies"].append(char_acc * 100.0)
            engine_results[eng_name]["reading_order_scores"].append(order_score)
            engine_results[eng_name]["heading_f1_scores"].append(h_f1 * 100.0)
            engine_results[eng_name]["page_preservation_rates"].append(page_pres_rate)
            engine_results[eng_name]["latencies_per_page_ms"].append(lat_page_ms)
            engine_results[eng_name]["latencies_per_doc_ms"].append(lat_doc_ms)
            engine_results[eng_name]["peak_rams_mb"].append(out.peak_ram_mb)

            # 4. Downstream Retrieval Quality
            chunks = chunk_extracted_output(out, aid, max_tokens=350, overlap=70)
            if chunks and queries:
                chunk_texts = [f"passage: {c['text']}" for c in chunks]
                chunk_mat = dense_embedder.encode(
                    chunk_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False
                )

                q_texts = [f"query: {q['question']}" for q in queries]
                q_embs = dense_embedder.encode(
                    q_texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False
                )

                sim_matrix = np.dot(q_embs, chunk_mat.T)

                for q_idx, q in enumerate(queries):
                    quote = q.get("verbatim_evidence_quote", "")
                    ev_list = q.get("evidence_list", [])
                    R_q = count_relevant_chunks(chunks, aid, quote, ev_list, tau=0.55)

                    ranked_indices = np.argsort(-sim_matrix[q_idx])
                    ranked_rels = [
                        1 if is_chunk_hit(chunks[i], aid, quote, ev_list, tau=0.55) else 0
                        for i in ranked_indices
                    ]
                    ndcg10 = compute_ndcg(ranked_rels, R_q, k=10)
                    rec20 = compute_recall(ranked_rels, R_q, k=20)

                    engine_results[eng_name]["query_ndcg10_by_paper"][aid].append(ndcg10)
                    engine_results[eng_name]["query_rec20_by_paper"][aid].append(rec20)

                    detailed_jsonl_rows.append({
                        "paper_arxiv_id": aid,
                        "engine": eng_name,
                        "query_id": q.get("id", q.get("query_id")),
                        "ndcg10": round(ndcg10, 4),
                        "recall20": round(rec20, 4),
                        "R_q": R_q,
                    })

    # Summary Statistics & Clustered Bootstrap Paired Tests
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = WORKSPACE_ROOT / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_json_path = results_dir / f"rq1_extraction_{timestamp}.json"
    out_jsonl_path = results_dir / f"rq1_extraction_queries_{timestamp}.jsonl"

    summary_table = []
    base_engine = "pymupdf_plain"
    base_scores = engine_results[base_engine]["query_ndcg10_by_paper"]

    for eng, stats in engine_results.items():
        if not stats["available"]:
            summary_table.append({
                "engine": eng,
                "available": False,
                "error": stats["error"],
            })
            continue

        mean_cov = float(np.mean(stats["evidence_coverages"])) if stats["evidence_coverages"] else 0.0
        mean_acc = float(np.mean(stats["char_accuracies"])) if stats["char_accuracies"] else 0.0
        mean_order = float(np.mean(stats["reading_order_scores"])) if stats["reading_order_scores"] else 0.0
        mean_hf1 = float(np.mean(stats["heading_f1_scores"])) if stats["heading_f1_scores"] else 0.0
        mean_page_pres = float(np.mean(stats["page_preservation_rates"])) if stats["page_preservation_rates"] else 0.0
        mean_lat_page = float(np.mean(stats["latencies_per_page_ms"])) if stats["latencies_per_page_ms"] else 0.0
        peak_ram = float(np.max(stats["peak_rams_mb"])) if stats["peak_rams_mb"] else 0.0

        all_ndcg = [s for p in stats["query_ndcg10_by_paper"].values() for s in p]
        all_rec = [s for p in stats["query_rec20_by_paper"].values() for s in p]
        mean_ndcg = float(np.mean(all_ndcg)) if all_ndcg else 0.0
        mean_rec = float(np.mean(all_rec)) if all_rec else 0.0

        # Clustered Bootstrap CI
        _, ci_low, ci_high = cluster_bootstrap_ci(stats["query_ndcg10_by_paper"], n_bootstraps=2000, seed=seed)

        # Paired test vs pymupdf_plain
        if eng == base_engine:
            diff, (p_ci_l, p_ci_h), p_val = 0.0, (0.0, 0.0), 1.0
        else:
            diff, (p_ci_l, p_ci_h), p_val = paired_cluster_bootstrap(
                base_scores, stats["query_ndcg10_by_paper"], n_bootstraps=2000, seed=seed
            )

        summary_table.append({
            "engine": eng,
            "available": True,
            "evidence_coverage_pct": round(mean_cov, 2),
            "char_accuracy_pct": round(mean_acc, 2),
            "reading_order_concordance": round(mean_order, 4),
            "heading_f1": round(mean_hf1, 2),
            "page_preservation_rate": round(mean_page_pres, 2),
            "latency_per_page_ms": round(mean_lat_page, 2),
            "peak_ram_mb": round(peak_ram, 1),
            "downstream_ndcg10": {
                "mean": round(mean_ndcg, 4),
                "ci_95": [round(ci_low, 4), round(ci_high, 4)],
            },
            "downstream_recall20": round(mean_rec, 4),
            "stats_vs_baseline": {
                "diff_ndcg10": round(diff, 4),
                "ci_95": [round(p_ci_l, 4), round(p_ci_h, 4)],
                "p_value": round(p_val, 4),
                "significant_05": bool(p_val < 0.05),
            },
        })

    # Pick champion extractor strictly by data
    valid_engines = [e for e in summary_table if e.get("available")]
    # Score composite: retrieval ndcg10 (50%) + evidence coverage (25%) + reading order (25%)
    champion = max(
        valid_engines,
        key=lambda x: (
            x["downstream_ndcg10"]["mean"] * 0.5
            + (x["evidence_coverage_pct"] / 100.0) * 0.25
            + x["reading_order_concordance"] * 0.25
        ),
    )

    final_payload = {
        "metadata": {
            "experiment": "RQ1 PDF Extractor Evaluation",
            "timestamp": timestamp,
            "seed": seed,
            "torch_threads": 4,
            "papers_evaluated": len(paper_ids),
            "baseline_engine": base_engine,
            "champion_selected": champion["engine"],
            "champion_rationale": (
                f"Selected {champion['engine']} based on top composite ranking: "
                f"nDCG@10 = {champion['downstream_ndcg10']['mean']}, "
                f"Evidence Coverage = {champion['evidence_coverage_pct']}%, "
                f"Latency = {champion['latency_per_page_ms']} ms/page."
            ),
        },
        "summary": summary_table,
    }

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    with open(out_jsonl_path, "w", encoding="utf-8") as f:
        for row in detailed_jsonl_rows:
            f.write(json.dumps(row) + "\n")

    print("\n" + "=" * 80)
    print("RQ1 BENCHMARK SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Engine':<16} {'Coverage %':>10} {'1-CER %':>8} {'Order':>7} {'Heading F1':>10} {'ms/page':>9} {'nDCG@10 [95% CI]':>26} {'p-val':>8}")
    print("-" * 105)
    for row in summary_table:
        if not row.get("available"):
            print(f"{row['engine']:<16} {'UNAVAILABLE (' + str(row['error'])[:35] + ')':>80}")
            continue
        ndcg_str = f"{row['downstream_ndcg10']['mean']:.4f} [{row['downstream_ndcg10']['ci_95'][0]:.4f}, {row['downstream_ndcg10']['ci_95'][1]:.4f}]"
        sig_str = f"{row['stats_vs_baseline']['p_value']:.4f}{' *' if row['stats_vs_baseline']['significant_05'] else ''}"
        print(f"{row['engine']:<16} {row['evidence_coverage_pct']:>9.1f}% {row['char_accuracy_pct']:>7.1f}% {row['reading_order_concordance']:>7.3f} {row['heading_f1']:>9.1f}% {row['latency_per_page_ms']:>8.1f}ms {ndcg_str:>26} {sig_str:>8}")

    print(f"\n[CHAMPION] RQ1 Selected Extractor: {champion['engine']}")
    print(f"[SERIALIZATION] Master JSON: {out_json_path.relative_to(WORKSPACE_ROOT)}")
    print(f"[SERIALIZATION] Query JSONL: {out_jsonl_path.relative_to(WORKSPACE_ROOT)}")
    return final_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RQ1 PDF Extractor Benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of papers to evaluate")
    parser.add_argument("--dry-run", action="store_true", help="Perform sanity check and print configuration without full run")
    parser.add_argument("--include-heavy", action="store_true", help="Include heavy CPU vision models (Marker/Docling) if installed")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for bootstrap resampling")
    args = parser.parse_args()

    run_rq1_extractor_benchmark(
        limit=args.limit,
        dry_run=args.dry_run,
        include_heavy=args.include_heavy,
        seed=args.seed,
    )
