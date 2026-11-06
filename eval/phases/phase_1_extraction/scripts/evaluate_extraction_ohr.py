#!/usr/bin/env python3
"""
Phase 1 Extraction Evaluation with OHR-Bench.
Evaluates PDF extractors across extraction completeness, fidelity (LCS / containment),
speed (ms/page), and downstream RAG retrieval performance on the OHR-Bench benchmark.

Supported Extractors:
  1. pymupdf_layout: Production layout-aware extractor preserving headings & page layout.
  2. pymupdf_plain: Raw text extraction per page without font/layout heuristics.
  3. pypdf: Pure-Python page-level text extraction.
  4. pdfminer.six: Layout-analysis text extractor.
  5. pdfplumber: Visual layout & text extractor.
  6. grobid: TEI-XML structured document processing via live API (default: http://localhost:8070).

Usage:
  python evaluate_extraction_ohr.py [--domain academic] [--extractors all] [--limit N]
                                    [--grobid-url URL] [--force-extract]
                                    [--page-offset N] [--common-only] [--include-scanned]

By default, scanned / image-only PDFs (no text layer, which GROBID rejects with NO_BLOCKS) are
excluded from extraction and scoring so all extractors are compared on the same corpus.
Pass --include-scanned to keep them (text extractors then score 0 on those docs).
"""

import argparse
import json
import re
import string
import time
import xml.etree.ElementTree as ET
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Paths
ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = ROOT / "eval" / "data" / "ohr_bench"
BASE_RETRIEVAL_DIR = DATA_DIR / "retrieval_base"
ARTIFACTS_DIR = ROOT / "eval" / "phases" / "phase_1_extraction" / "artifacts"
QAS_FILE = DATA_DIR / "qas_v2.json"

EXTRACTORS = ["pymupdf_layout", "pymupdf_plain", "pypdf", "pdfminer.six", "pdfplumber", "grobid"]
DEFAULT_GROBID_URL = "http://localhost:8070"
EVIDENCE_TYPES = ["text", "table", "formula", "chart", "reading_order"]

# Lazy-loaded libraries
fitz = None
pypdf = None
pdfplumber = None
requests = None


def _load_libs():
    global fitz, pypdf, pdfplumber, requests
    if fitz is None:
        import pymupdf as fitz
    if pypdf is None:
        import pypdf
    if pdfplumber is None:
        import pdfplumber
    if requests is None:
        import requests


def _warm_imports():
    """Import everything up front so first-use import cost isn't charged to an extractor's timing."""
    _load_libs()
    import pdfminer.converter  # noqa: F401
    import pdfminer.layout  # noqa: F401
    import pdfminer.pdfinterp  # noqa: F401
    import pdfminer.pdfpage  # noqa: F401


# -----------------------------------------------------------------------------
# Metric Helpers (Aligned with OHR-Bench)
# -----------------------------------------------------------------------------
def normalize_answer(s: str) -> str:
    """Standard answer normalization matching OHR-Bench."""
    if not s:
        return ""
    # remove punctuation and lowercase
    s = s.lower()
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    exclude = set(string.punctuation)
    s = "".join(ch for ch in s if ch not in exclude)
    return " ".join(s.split())


def lcs_score(prediction: str, ground_truth: str) -> float:
    """Word-level Longest Common Subsequence score from OHR-Bench."""
    if not prediction or not ground_truth:
        return 0.0
    A = normalize_answer(ground_truth).split()
    B = normalize_answer(prediction).split()
    if not A or not B:
        return 0.0

    # Two-row DP (same result as the full table, O(len(B)) memory)
    prev = [0] * (len(B) + 1)
    for a in A:
        cur = [0] * (len(B) + 1)
        for j, b in enumerate(B, 1):
            cur[j] = prev[j - 1] + 1 if a == b else max(prev[j], cur[j - 1])
        prev = cur

    return prev[-1] / len(A)


def containment_score(prediction: str, ground_truth: str) -> float:
    """Share of content words from ground_truth found in prediction."""
    if not prediction or not ground_truth:
        return 0.0
    gold_words = set(normalize_answer(ground_truth).split())
    if not gold_words:
        return 0.0
    pred_words = set(normalize_answer(prediction).split())
    return len(gold_words & pred_words) / len(gold_words)


# -----------------------------------------------------------------------------
# PDF Extractors
# -----------------------------------------------------------------------------
def extract_pymupdf_plain(pdf_path: Path) -> List[Dict[str, Any]]:
    _load_libs()
    with fitz.open(pdf_path) as doc:
        return [{"page_idx": i, "text": doc[i].get_text()} for i in range(len(doc))]


def extract_pymupdf_layout(pdf_path: Path) -> List[Dict[str, Any]]:
    _load_libs()
    res = []
    with fitz.open(pdf_path) as doc:
        for i in range(len(doc)):
            # block tuple: (x0, y0, x1, y1, text, block_no, block_type); type 0 = text, 1 = image
            blocks = [b for b in doc[i].get_text("blocks") if len(b) > 6 and b[6] == 0]
            # Sort blocks top-to-bottom, left-to-right
            blocks.sort(key=lambda b: (b[1], b[0]))
            text = "\n\n".join(b[4].strip() for b in blocks if b[4].strip())
            res.append({"page_idx": i, "text": text})
    return res


def extract_pypdf(pdf_path: Path) -> List[Dict[str, Any]]:
    _load_libs()
    reader = pypdf.PdfReader(str(pdf_path))
    return [{"page_idx": i, "text": reader.pages[i].extract_text() or ""} for i in range(len(reader.pages))]


def extract_pdfminer(pdf_path: Path) -> List[Dict[str, Any]]:
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage

    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    res = []
    with open(pdf_path, "rb") as fp:
        for i, page in enumerate(PDFPage.get_pages(fp)):
            sio = StringIO()
            device = TextConverter(rsrcmgr, sio, laparams=laparams)
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            interpreter.process_page(page)
            device.close()
            res.append({"page_idx": i, "text": sio.getvalue()})
    return res


def extract_pdfplumber(pdf_path: Path) -> List[Dict[str, Any]]:
    _load_libs()
    res = []
    with pdfplumber.open(str(pdf_path)) as plum:
        for i, page in enumerate(plum.pages):
            res.append({"page_idx": i, "text": page.extract_text() or ""})
    return res


def has_text_layer(pdf_path: Path) -> bool:
    """True if any page has extractable text. False = scanned / image-only PDF."""
    _load_libs()
    try:
        with fitz.open(pdf_path) as d:
            return any(page.get_text().strip() for page in d)
    except Exception:
        return True  # can't tell: keep the doc rather than silently dropping it


def grobid_alive(grobid_url: str) -> bool:
    _load_libs()
    try:
        return requests.get(f"{grobid_url}/api/isalive", timeout=5).ok
    except Exception:
        return False


def _post_grobid(name: str, payload: bytes, grobid_url: str, no_consolidation: bool):
    """POST one PDF to GROBID. Backs off and retries on 503 (server busy)."""
    data: Dict[str, Any] = {"teiCoordinates": ["p", "head", "note", "biblStruct", "figure"]}
    if no_consolidation:
        # consolidation calls out to external services (CrossRef/glutton); if that errors, GROBID 500s
        data["consolidateHeader"] = "0"
        data["consolidateCitations"] = "0"
    resp = None
    for attempt in range(3):
        resp = requests.post(
            f"{grobid_url}/api/processFulltextDocument",
            files={"input": (name, payload, "application/pdf")},
            data=data,
            timeout=180,
        )
        if resp.status_code != 503:
            break
        time.sleep(2 * (attempt + 1))
    return resp


def extract_grobid(pdf_path: Path, grobid_url: str = DEFAULT_GROBID_URL) -> List[Dict[str, Any]]:
    _load_libs()
    raw = pdf_path.read_bytes()

    # Fallback ladder for 5xx / timeouts: as-is -> consolidation off -> PDF re-saved by PyMuPDF
    # (garbage-collected + cleaned) with consolidation off. 4xx is a client error: no retry.
    ladder = [("as-is", False), ("no-consolidation", True), ("repaired+no-consolidation", True)]
    resp = None
    errors: List[str] = []
    for label, no_consol in ladder:
        payload = raw
        if label.startswith("repaired"):
            try:
                with fitz.open(pdf_path) as d:
                    payload = d.tobytes(garbage=4, deflate=True, clean=True)
            except Exception as e:
                errors.append(f"{label}: repair failed ({e})")
                break
        try:
            resp = _post_grobid(pdf_path.name, payload, grobid_url, no_consol)
        except requests.RequestException as e:
            errors.append(f"{label}: {type(e).__name__}: {e}")
            resp = None
            continue
        if resp.ok:
            break
        errors.append(f"{label}: HTTP {resp.status_code} {resp.text.strip()[:200]!r}")
        if "NO_BLOCKS" in resp.text:
            # Scanned / image-only PDF: no text layer for GROBID to parse. Deterministic, so don't
            # retry; the real output is empty text, which is scored as such (like any other extractor).
            with fitz.open(pdf_path) as d:
                return [{"page_idx": i, "text": ""} for i in range(len(d))]
        if resp.status_code < 500:
            break
    if resp is None or not resp.ok:
        raise RuntimeError(" | ".join(errors))

    with fitz.open(pdf_path) as doc:
        num_pages = len(doc)
    pages: Dict[int, List[str]] = {i: [] for i in range(num_pages)}

    root = ET.fromstring(resp.text)
    NS = {"tei": "http://www.tei-c.org/ns/1.0"}

    def _t(el):
        return re.sub(r"\s+", " ", "".join(el.itertext())).strip()

    def _pg(el):
        c = el.get("coords")
        if c:
            try:
                return int(c.split(",")[0]) - 1
            except Exception:
                pass
        return None

    # Abstract
    for p_el in root.findall(".//tei:teiHeader//tei:abstract//tei:p", NS):
        t = _t(p_el)
        if t:
            pg = _pg(p_el)
            pg = pg if pg is not None else 0
            if 0 <= pg < num_pages:
                pages[pg].append(t)

    # Body divs
    for div in root.findall(".//tei:text//tei:div", NS):
        head = div.find("tei:head", NS)
        h_t = _t(head) if head is not None else ""
        h_pg = _pg(head) if head is not None else None

        for p_el in div.findall("tei:p", NS):
            t = _t(p_el)
            if t:
                pg = _pg(p_el)
                if pg is None:
                    pg = h_pg if h_pg is not None else 0
                if 0 <= pg < num_pages:
                    if h_t:
                        pages[pg].append(h_t)
                        h_t = ""
                    pages[pg].append(t)

    # References
    for bib in root.findall(".//tei:listBibl/tei:biblStruct", NS):
        t = _t(bib)
        if t:
            pg = _pg(bib)
            if pg is None:
                pg = num_pages - 1
            if 0 <= pg < num_pages:
                pages[pg].append(t)

    return [{"page_idx": i, "text": "\n\n".join(pages[i])} for i in range(num_pages)]


EXTRACTOR_FNS: Dict[str, Callable[[Path], List[Dict[str, Any]]]] = {
    "pymupdf_layout": extract_pymupdf_layout,
    "pymupdf_plain": extract_pymupdf_plain,
    "pypdf": extract_pypdf,
    "pdfminer.six": extract_pdfminer,
    "pdfplumber": extract_pdfplumber,
    "grobid": extract_grobid,
}


# -----------------------------------------------------------------------------
# BM25 Retriever
# -----------------------------------------------------------------------------
class SimpleBM25:
    """Lightweight in-memory BM25 index over page documents."""

    def __init__(self, pages: List[Dict[str, Any]]):
        from rank_bm25 import BM25Okapi

        self.pages = pages
        self.tokenized_corpus = [normalize_answer(p["text"]).split() for p in pages]
        # Handle empty corpus gracefully
        if not any(self.tokenized_corpus):
            self.bm25 = None
        else:
            self.bm25 = BM25Okapi(self.tokenized_corpus)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.bm25:
            return self.pages[:top_k]
        tokenized_query = normalize_answer(query).split()
        if not tokenized_query:
            return self.pages[:top_k]
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.pages[i] for i in ranked_indices]


# -----------------------------------------------------------------------------
# Report helpers
# -----------------------------------------------------------------------------
def build_observations(metrics: Dict[str, Any], selected: List[str]) -> List[str]:
    """Findings derived from the actual results (no hardcoded claims)."""
    ok = [e for e in selected if metrics[e]["n_evaluated"] > 0]
    if not ok:
        return ["No extractor produced evaluable output."]

    obs = []
    best = max(ok, key=lambda e: metrics[e]["evidence_lcs"])
    obs.append(f"**Best text fidelity:** `{best}` ({metrics[best]['evidence_lcs']:.1f}% LCS, "
               f"recall {metrics[best]['evidence_recall']:.3f}).")

    best = max(ok, key=lambda e: metrics[e]["retrieval_hit1"])
    obs.append(f"**Best BM25 retrieval:** `{best}` (Hit@1 {metrics[best]['retrieval_hit1']:.3f}, "
               f"Hit@2 {metrics[best]['retrieval_hit2']:.3f}).")

    timed = [e for e in ok if metrics[e]["timing"].get("ms_per_page") is not None]
    if timed:
        fast = min(timed, key=lambda e: metrics[e]["timing"]["ms_per_page"])
        slow = max(timed, key=lambda e: metrics[e]["timing"]["ms_per_page"])
        obs.append(f"**Speed:** fastest `{fast}` ({metrics[fast]['timing']['ms_per_page']} ms/page), "
                   f"slowest `{slow}` ({metrics[slow]['timing']['ms_per_page']} ms/page).")
    else:
        obs.append("**Speed:** not measured (all results came from cache; rerun with `--force-extract`).")

    empty = [(e, len(metrics[e]["timing"].get("empty_docs", []))) for e in selected
             if metrics[e]["timing"].get("empty_docs")]
    if empty:
        obs.append("**Empty output (no text extracted, scored as 0):** "
                   + ", ".join(f"`{e}` ({n} docs)" for e, n in empty)
                   + ". Likely scanned / image-only PDFs with no text layer.")

    partial = [e for e in selected
               if metrics[e]["timing"].get("success_docs", 0) < metrics[e]["timing"].get("total_docs", 0)]
    if partial:
        def _d(e):
            t = metrics[e]["timing"]
            names = ", ".join(Path(k).name for k in t.get("failed_docs", [])[:10])
            return f"`{e}` ({t['success_docs']}/{t['total_docs']}" + (f"; failed: {names}" if names else "") + ")"

        desc = ", ".join(_d(e) for e in partial)
        obs.append(f"**Incomplete coverage:** {desc}. Scores are averaged over the questions each "
                   f"extractor actually processed; use `--common-only` for a like-for-like comparison.")
    return obs


def _is_empty(pages: List[Dict[str, Any]]) -> bool:
    return not any(p["text"].strip() for p in pages)


def _fmt_src(src_m: Dict[str, Any]) -> str:
    return f"{src_m['lcs']:.1f}%" if src_m["count"] > 0 else "-"


# -----------------------------------------------------------------------------
# Main Evaluation Pipeline
# -----------------------------------------------------------------------------
def run_extraction_and_eval(
    domain: str = "academic",
    extractors: Optional[List[str]] = None,
    limit: Optional[int] = None,
    grobid_url: str = DEFAULT_GROBID_URL,
    force_extract: bool = False,
    page_offset: int = 0,
    common_only: bool = False,
    include_scanned: bool = False,
):
    if extractors is None or "all" in extractors:
        selected_extractors = list(EXTRACTORS)
    else:
        selected_extractors = [e for e in extractors if e in EXTRACTORS]
    if not selected_extractors:
        raise ValueError(f"No valid extractors selected. Choose from: {', '.join(EXTRACTORS)}")

    print("=" * 80)
    print("OHR-Bench PDF Extractor Benchmark (Phase 1)")
    print(f"Domain: {domain} | Extractors: {', '.join(selected_extractors)}")
    print(f"GROBID URL: {grobid_url} | page offset: {page_offset} | common-only: {common_only} "
          f"| include-scanned: {include_scanned}")
    print("=" * 80)

    # 1. Load QA dataset
    if not QAS_FILE.exists():
        raise FileNotFoundError(f"OHR-Bench QAs file not found at {QAS_FILE}")
    with open(QAS_FILE, encoding="utf-8") as f:
        all_qas = json.load(f)

    if domain == "all":
        qas = all_qas
    else:
        qas = [q for q in all_qas if q.get("doc_type") == domain]

    print(f"Loaded {len(qas)} questions for domain '{domain}'.")

    # 2. Identify PDF documents
    domain_pdf_dir = DATA_DIR / domain
    if domain == "all":
        pdf_files = sorted(DATA_DIR.glob("*/*.pdf"))
    else:
        if not domain_pdf_dir.exists():
            raise FileNotFoundError(f"Directory {domain_pdf_dir} does not exist.")
        pdf_files = sorted(domain_pdf_dir.glob("*.pdf"))

    if limit:
        pdf_files = pdf_files[:limit]
        allowed_docs = {f"{p.parent.name}/{p.stem}" for p in pdf_files}
        qas = [q for q in qas if q["doc_name"] in allowed_docs]
        print(f"Limited run: {len(pdf_files)} PDFs, {len(qas)} questions.")

    pdf_map = {f"{p.parent.name}/{p.stem}": p for p in pdf_files}

    # Scanned / image-only PDFs (no text layer) can't be read by text extractors like GROBID, so by
    # default they're dropped up front and every extractor is compared on the same corpus.
    scanned_docs: Dict[str, str] = {}
    if not include_scanned:
        for k, p in list(pdf_map.items()):
            if not has_text_layer(p):
                scanned_docs[k] = "no text layer"
                del pdf_map[k]
        n_q = sum(1 for q in qas if q["doc_name"] in scanned_docs)
        print(f"Excluded {len(scanned_docs)} scanned / no-text-layer PDFs ({n_q} questions); "
              f"use --include-scanned to keep them. {len(pdf_map)} PDFs remain.")

    # 3. Run Extraction & Cache
    _warm_imports()
    timing_stats: Dict[str, Dict[str, Any]] = {}
    total_pages_count = 0
    grobid_ok: Optional[bool] = None
    grobid_empty_docs: List[str] = []

    for ex in selected_extractors:
        print(f"\n--- Extracting with: {ex} ---")
        ex_dir = BASE_RETRIEVAL_DIR / ex
        ex_fn = EXTRACTOR_FNS[ex]

        pages_total = 0  # pages available (cached + fresh)
        success_count = 0
        fresh_docs = 0
        fresh_pages = 0
        fresh_elapsed = 0.0  # only time actually spent extracting (not JSON cache loads)
        failed_docs: List[str] = []
        empty_docs: List[str] = []  # docs where the extractor returned no text at all
        wall_t0 = time.perf_counter()

        for doc_key, pdf_p in pdf_map.items():
            out_file = ex_dir / f"{doc_key}.json"
            if out_file.exists() and not force_extract:
                with open(out_file, encoding="utf-8") as f:
                    doc_pages = json.load(f)
                pages_total += len(doc_pages)
                success_count += 1
                if _is_empty(doc_pages):
                    empty_docs.append(doc_key)
                continue

            if ex == "grobid":
                if grobid_ok is None:
                    grobid_ok = grobid_alive(grobid_url)
                    if not grobid_ok:
                        print(f"  [WARN] GROBID not reachable at {grobid_url}; only cached docs will be used.")
                if not grobid_ok:
                    continue

            out_file.parent.mkdir(parents=True, exist_ok=True)
            t1 = time.perf_counter()
            try:
                if ex == "grobid":
                    pages = ex_fn(pdf_p, grobid_url=grobid_url)
                else:
                    pages = ex_fn(pdf_p)
            except Exception as e:
                print(f"  [ERROR] {ex} failed on {pdf_p.name}: {e}")
                failed_docs.append(doc_key)
                continue
            dt = time.perf_counter() - t1

            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(pages, f, indent=2)
            fresh_elapsed += dt
            if _is_empty(pages):
                empty_docs.append(doc_key)
                print(f"  [EMPTY] {ex}: no text from {pdf_p.name} (scanned / no text layer?)")
            fresh_pages += len(pages)
            fresh_docs += 1
            pages_total += len(pages)
            success_count += 1

        wall = time.perf_counter() - wall_t0
        if ex == "grobid":
            grobid_empty_docs = list(empty_docs)
        ms_per_page = round(fresh_elapsed / fresh_pages * 1000, 2) if fresh_pages > 0 else None
        timing_stats[ex] = {
            "elapsed_sec": round(wall, 2),
            "extract_sec": round(fresh_elapsed, 2),
            "pages_processed": pages_total,
            "fresh_pages": fresh_pages,
            "fresh_docs": fresh_docs,
            "failed_docs": failed_docs,
            "empty_docs": empty_docs,
            "success_docs": success_count,
            "total_docs": len(pdf_map),
            "ms_per_page": ms_per_page,
        }
        total_pages_count = max(total_pages_count, pages_total)
        speed_str = f"{ms_per_page:.2f} ms/page" if ms_per_page is not None else "all cached, speed not measured"
        print(f"  {pages_total} pages across {success_count}/{len(pdf_map)} docs "
              f"({fresh_docs} freshly extracted in {fresh_elapsed:.2f}s; {speed_str})")

    # 4. Evaluate Extraction & Retrieval
    print("\n" + "=" * 80)
    print("Evaluating Extraction Fidelity & Downstream Retrieval...")
    print("=" * 80)

    # Preload extractor caches
    extracted_cache: Dict[str, Dict[str, List[Dict[str, Any]]]] = {ex: {} for ex in selected_extractors}
    for ex in selected_extractors:
        for doc_key in pdf_map.keys():
            doc_file = BASE_RETRIEVAL_DIR / ex / f"{doc_key}.json"
            if doc_file.exists():
                with open(doc_file, encoding="utf-8") as f:
                    extracted_cache[ex][doc_key] = json.load(f)

    # Also exclude docs where GROBID returned no text (NO_BLOCKS) that the probe above didn't catch.
    if not include_scanned and "grobid" in selected_extractors:
        for k in grobid_empty_docs:
            if k in pdf_map and k not in scanned_docs:
                others = [e for e in selected_extractors
                          if e != "grobid" and k in extracted_cache[e] and not _is_empty(extracted_cache[e][k])]
                scanned_docs[k] = "GROBID found no text" + (f" (but {', '.join(others)} did)" if others else "")
                if others:
                    print(f"  [WARN] excluded {Path(k).name}: GROBID found no text, "
                          f"but {', '.join(others)} extracted text from it.")
    for ex in selected_extractors:  # excluded docs shouldn't also show up as "empty output"
        t = timing_stats[ex]
        t["empty_docs"] = [k for k in t["empty_docs"] if k not in scanned_docs]
    n_excluded_q = sum(1 for q in qas if q["doc_name"] in scanned_docs)
    n_scored_docs = sum(1 for k in pdf_map if k not in scanned_docs)
    if scanned_docs:
        print(f"Scored docs: {n_scored_docs} | excluded: {len(scanned_docs)} docs / {n_excluded_q} questions.")

    # Restrict to docs every extractor handled, for an apples-to-apples comparison
    if common_only:
        common_docs = set(pdf_map.keys()) - set(scanned_docs)
        for ex in selected_extractors:
            common_docs &= {k for k, v in extracted_cache[ex].items() if v}
        before = len(qas)
        qas = [q for q in qas if q["doc_name"] in common_docs]
        print(f"--common-only: {len(common_docs)} docs shared by all extractors "
              f"({before} -> {len(qas)} questions).")

    metrics_summary: Dict[str, Any] = {
        ex: {
            "n_evaluated": 0,
            "evidence_recall": 0.0,
            "evidence_lcs": 0.0,
            "retrieval_hit1": 0.0,
            "retrieval_hit2": 0.0,
            "retrieval_hit5": 0.0,
            "retrieval_lcs": 0.0,
            "by_source": {
                src: {"count": 0, "recall": 0.0, "lcs": 0.0, "hit1": 0.0, "hit2": 0.0, "ret_lcs": 0.0}
                for src in EVIDENCE_TYPES
            },
        }
        for ex in selected_extractors
    }

    bm25_cache: Dict[Tuple[str, str], SimpleBM25] = {}  # one index per (extractor, doc)
    oob_gold: Dict[str, int] = {ex: 0 for ex in selected_extractors}  # gold page outside extracted range
    per_query_records = []
    total_qas_in_scope = 0

    for qa in qas:
        doc_key = qa["doc_name"]
        if doc_key not in pdf_map or doc_key in scanned_docs:
            continue

        q_id = qa.get("ID", qa.get("id"))
        question = qa["questions"]
        source_type = qa.get("evidence_source", "text")
        if source_type not in EVIDENCE_TYPES:
            source_type = "text"

        gold_ctx = qa["evidence_context"]
        if isinstance(gold_ctx, list):
            gold_ctx = "\n".join(gold_ctx)
        gold_page = qa["evidence_page_no"]
        gold_pages = [int(p) + page_offset for p in (gold_page if isinstance(gold_page, list) else [gold_page])]

        q_rec: Dict[str, Any] = {
            "id": q_id,
            "doc_name": doc_key,
            "question": question,
            "evidence_source": source_type,
            "evidence_pages": gold_pages,
            "extractors": {},
        }

        total_qas_in_scope += 1

        for ex in selected_extractors:
            doc_pages = extracted_cache[ex].get(doc_key, [])
            if not doc_pages:
                continue  # extractor produced nothing for this doc: not scored, tracked via n_evaluated

            if any(p < 0 or p >= len(doc_pages) for p in gold_pages):
                oob_gold[ex] += 1

            # 1. Page text fidelity on target page
            target_page_texts = [p["text"] for p in doc_pages if p["page_idx"] in gold_pages]
            combined_page_text = "\n\n".join(target_page_texts)

            cov = containment_score(combined_page_text, gold_ctx)
            lcs = lcs_score(combined_page_text, gold_ctx)
            is_recalled = 1.0 if cov >= 0.80 else 0.0

            # 2. Downstream BM25 retrieval
            cache_key = (ex, doc_key)
            if cache_key not in bm25_cache:
                bm25_cache[cache_key] = SimpleBM25(doc_pages)
            retrieved = bm25_cache[cache_key].retrieve(question, top_k=5)
            retrieved_pages = [r["page_idx"] for r in retrieved]

            hit1 = 1.0 if any(p in gold_pages for p in retrieved_pages[:1]) else 0.0
            hit2 = 1.0 if any(p in gold_pages for p in retrieved_pages[:2]) else 0.0
            hit5 = 1.0 if any(p in gold_pages for p in retrieved_pages[:5]) else 0.0

            # OHR-Bench retrieval LCS: LCS of retrieved context matching target page
            top2_text = [r["text"] for r in retrieved[:2] if r["page_idx"] in gold_pages]
            ret_lcs = lcs_score("\n\n".join(top2_text), gold_ctx) if top2_text else 0.0

            # Accumulate overall
            m = metrics_summary[ex]
            m["n_evaluated"] += 1
            m["evidence_recall"] += is_recalled
            m["evidence_lcs"] += lcs
            m["retrieval_hit1"] += hit1
            m["retrieval_hit2"] += hit2
            m["retrieval_hit5"] += hit5
            m["retrieval_lcs"] += ret_lcs

            # Accumulate by evidence source
            src_m = m["by_source"][source_type]
            src_m["count"] += 1
            src_m["recall"] += is_recalled
            src_m["lcs"] += lcs
            src_m["hit1"] += hit1
            src_m["hit2"] += hit2
            src_m["ret_lcs"] += ret_lcs

            q_rec["extractors"][ex] = {
                "containment": round(cov, 4),
                "is_recalled": is_recalled,
                "lcs": round(lcs, 4),
                "hit1": hit1,
                "hit2": hit2,
                "hit5": hit5,
                "ret_lcs": round(ret_lcs, 4),
            }

        per_query_records.append(q_rec)

    # Page-numbering sanity check
    for ex, n_oob in oob_gold.items():
        n_eval = metrics_summary[ex]["n_evaluated"]
        if n_oob:
            print(f"[WARN] {ex}: {n_oob}/{n_eval} questions have a gold page outside the extracted page range. "
                  f"Check OHR-Bench page numbering (0- vs 1-based) and try --page-offset.")

    # Average metrics: each extractor is averaged over the questions it actually processed
    for ex in selected_extractors:
        m = metrics_summary[ex]
        n = m["n_evaluated"]
        if n > 0:
            m["evidence_recall"] = round(m["evidence_recall"] / n, 4)
            m["evidence_lcs"] = round(m["evidence_lcs"] / n * 100, 2)
            m["retrieval_hit1"] = round(m["retrieval_hit1"] / n, 4)
            m["retrieval_hit2"] = round(m["retrieval_hit2"] / n, 4)
            m["retrieval_hit5"] = round(m["retrieval_hit5"] / n, 4)
            m["retrieval_lcs"] = round(m["retrieval_lcs"] / n * 100, 2)

            for src_m in m["by_source"].values():
                cnt = src_m["count"]
                if cnt > 0:
                    src_m["recall"] = round(src_m["recall"] / cnt, 4)
                    src_m["lcs"] = round(src_m["lcs"] / cnt * 100, 2)
                    src_m["hit1"] = round(src_m["hit1"] / cnt, 4)
                    src_m["hit2"] = round(src_m["hit2"] / cnt, 4)
                    src_m["ret_lcs"] = round(src_m["ret_lcs"] / cnt * 100, 2)
        m["timing"] = timing_stats.get(ex, {})

    # 5. Output Artifacts
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = ARTIFACTS_DIR / "summary.json"
    per_query_path = ARTIFACTS_DIR / "per_query.jsonl"
    report_path = ARTIFACTS_DIR / "REPORT.md"

    summary_data = {
        "benchmark": "OHR-Bench",
        "domain": domain,
        "page_offset": page_offset,
        "common_only": common_only,
        "include_scanned": include_scanned,
        "total_documents": len(pdf_map) + sum(1 for r in scanned_docs.values() if r == "no text layer"),
        "scored_documents": n_scored_docs,
        "excluded_scanned_docs": scanned_docs,
        "excluded_questions": n_excluded_q,
        "total_queries_in_scope": total_qas_in_scope,
        "extractors": metrics_summary,
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    with open(per_query_path, "w", encoding="utf-8") as f:
        for r in per_query_records:
            f.write(json.dumps(r) + "\n")

    # Generate Markdown Report
    if scanned_docs:
        names = ", ".join(Path(k).name for k in list(scanned_docs)[:10]) + (" …" if len(scanned_docs) > 10 else "")
        excl_note = (f"{len(scanned_docs)} docs / {n_excluded_q} questions excluded "
                     f"(no text layer, or GROBID found no text): {names}")
    elif include_scanned:
        excl_note = "included (`--include-scanned`); text extractors score 0 on them"
    else:
        excl_note = "none found"
    report_lines = [
        "# Phase 1 PDF Extraction Benchmark — OHR-Bench Results",
        "",
        "- **Benchmark:** [OHR-Bench](https://github.com/opendatalab/OHR-Bench) (OpenDataLab, ICCV 2025)",
        f"- **Domain:** `{domain}`",
        f"- **Documents scored:** {n_scored_docs} PDFs (up to {total_pages_count} pages extracted per extractor)",
        f"- **Scanned / no-text-layer PDFs:** {excl_note}",
        f"- **Questions in scope:** {total_qas_in_scope}"
        + (" (common docs only)" if common_only else " (each extractor averaged over the questions it processed)"),
        "",
        "## 1. Overall Performance Comparison",
        "",
        "| Extractor | Qs | Docs OK | Evidence Recall (≥0.80) | Text LCS (%) | Hit@1 | Hit@2 | Hit@5 | Retrieval LCS (%) | Latency (ms/page) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for ex in selected_extractors:
        m = metrics_summary[ex]
        t = m["timing"]
        if t.get("ms_per_page") is not None:
            lat = f"{t['ms_per_page']:.2f}"
        else:
            lat = "cached" if t.get("success_docs", 0) > 0 else "n/a"
        report_lines.append(
            f"| **{ex}** | {m['n_evaluated']} | {t.get('success_docs', 0)}/{t.get('total_docs', 0)} "
            f"| {m['evidence_recall']:.3f} | {m['evidence_lcs']:.1f}% | {m['retrieval_hit1']:.3f} "
            f"| {m['retrieval_hit2']:.3f} | {m['retrieval_hit5']:.3f} | {m['retrieval_lcs']:.1f}% | {lat} |"
        )

    report_lines.extend([
        "",
        "## 2. Performance Breakdown by Evidence Source (LCS Score %)",
        "",
        "| Extractor | Plain Text | Table | Formula | Chart | Reading Order |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])

    for ex in selected_extractors:
        src = metrics_summary[ex]["by_source"]
        report_lines.append(
            f"| **{ex}** | {_fmt_src(src['text'])} | {_fmt_src(src['table'])} | {_fmt_src(src['formula'])} "
            f"| {_fmt_src(src['chart'])} | {_fmt_src(src['reading_order'])} |"
        )

    report_lines.extend(["", "## 3. Key Observations & Findings", ""])
    for i, o in enumerate(build_observations(metrics_summary, selected_extractors), 1):
        report_lines.append(f"{i}. {o}")
    report_lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("\n" + "\n".join(report_lines))
    print("\nArtifacts successfully written to:")
    print(f"  Summary:   {summary_path}")
    print(f"  Per-Query: {per_query_path}")
    print(f"  Report:    {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate PDF extractors on OHR-Bench")
    parser.add_argument("--domain", default="academic", choices=["academic", "finance", "manual", "administration", "textbook", "law", "news", "all"])
    parser.add_argument("--extractors", nargs="+", default=["all"])
    parser.add_argument("--limit", type=int, default=None, help="Limit number of documents for testing")
    parser.add_argument("--grobid-url", default=DEFAULT_GROBID_URL, help="URL for GROBID service")
    parser.add_argument("--force-extract", action="store_true", help="Re-run extraction even if cached (needed for valid ms/page)")
    parser.add_argument("--page-offset", type=int, default=0, help="Added to evidence_page_no before matching 0-based page_idx (use -1 if the dataset is 1-based)")
    parser.add_argument("--common-only", action="store_true", help="Score only docs that every selected extractor processed")
    parser.add_argument("--include-scanned", action="store_true", help="Keep scanned / no-text-layer PDFs (default: exclude them so the comparison is fair)")
    args = parser.parse_args()

    run_extraction_and_eval(
        domain=args.domain,
        extractors=args.extractors,
        limit=args.limit,
        grobid_url=args.grobid_url,
        force_extract=args.force_extract,
        page_offset=args.page_offset,
        common_only=args.common_only,
        include_scanned=args.include_scanned,
    )


if __name__ == "__main__":
    main()