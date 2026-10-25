"""
Chunking utilities for scientific document processing and RAG evaluation pipeline.

Implements:
  - GROBID TEI XML structured extraction + recursive chunking (for RAG pipeline)
  - Layout-aware section extraction from PDF + configurable chunking strategies
    (for comparative evaluation: 'section', 'section_token', 'section_overlap')
"""
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymupdf
from bs4 import BeautifulSoup
from django.conf import settings
from langchain_core.documents import Document
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# TEI XML helpers (used by GROBID path → RAG service)
# ─────────────────────────────────────────────────────────────────────────────

def extract_structured_body(xml_text: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(xml_text, "xml")
    sections = []

    abstract = soup.find("abstract")
    if abstract:
        abstract_paragraphs = [
            p.get_text(separator=" ", strip=True) for p in abstract.find_all("p")
        ]
        if not abstract_paragraphs:
            text = abstract.get_text(separator=" ", strip=True)
            if text:
                abstract_paragraphs = [text]
        if abstract_paragraphs:
            sections.append(
                {
                    "section": "Abstract",
                    "paragraphs": abstract_paragraphs,
                    "text": "\n\n".join(abstract_paragraphs),
                }
            )

    text_elem = soup.find("text")
    if text_elem:
        body = text_elem.find("body")
        if body:
            for div in body.find_all("div", recursive=False):
                head = div.find("head")
                head_title = (
                    head.get_text(separator=" ", strip=True)
                    if head
                    else "Untitled Section"
                )
                paras = [
                    p.get_text(separator=" ", strip=True)
                    for p in div.find_all("p", recursive=False)
                ]
                if paras:
                    sections.append(
                        {
                            "section": head_title,
                            "paragraphs": paras,
                            "text": "\n\n".join(paras),
                        }
                    )

    return sections


def assemble_full_text(sections: List[Dict[str, Any]]) -> str:
    blocks = []
    for sec in sections:
        title = sec.get("section", "").strip()
        body_text = sec.get("text", "").strip()
        if not body_text:
            continue
        if title:
            blocks.append(f"## {title}\n{body_text}")
        else:
            blocks.append(body_text)
    return "\n\n".join(blocks)


def recursive_chunker(
    xml_text: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> List[Document]:
    sections = extract_structured_body(xml_text)
    if not sections:
        return []

    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    documents = []
    chunk_counter = 0

    for sec in sections:
        sec_title = sec.get("section", "General")
        sec_text = sec.get("text", "")
        if not sec_text:
            continue

        raw_chunks = splitter.split_text(sec_text)
        for chunk in raw_chunks:
            chunk_counter += 1
            doc = Document(
                page_content=chunk,
                metadata={
                    "chunk_id": f"chunk-sec-{chunk_counter}",
                    "section": sec_title,
                    "page": 1,
                    "chunk_size": len(chunk),
                },
            )
            documents.append(doc)

    return documents


def fixed_size_chunk(pure_tei_xml: str, chunk_size: int = 550, chunk_overlap: int = 150) -> List[Document]:
    sections = extract_structured_body(pure_tei_xml)
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(assemble_full_text(sections))

    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "chunk_id": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
            },
        )
        documents.append(doc)

    return documents


def process_pdf_with_grobid(pdf_path: str) -> Optional[str]:
    """
    Uses GrobidClient to process a PDF and return TEI XML text.
    Bypassed if USE_GROBID is False (default for lightweight local deployment).
    """
    if not getattr(settings, "USE_GROBID", False):
        return None

    try:
        from grobid_client.grobid_client import GrobidClient
        import shutil, tempfile

        project_root = Path(settings.BASE_DIR).parent
        xml_store = project_root / "xml_store"
        xml_store.mkdir(exist_ok=True)

        config_path = os.path.join(settings.BASE_DIR, "grobid.json")

        # GrobidClient.process() requires a DIRECTORY, not a file path.
        # Copy the single PDF into a temp dir, then process that dir.
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_name = Path(pdf_path).name
            shutil.copy2(pdf_path, os.path.join(tmp_dir, pdf_name))

            client = GrobidClient(config_path=config_path)
            client.process(
                service="processFulltextDocument",
                input_path=tmp_dir,
                output=str(xml_store),
                consolidate_header=True,
                consolidate_citations=False,
                include_raw_citations=False,
                segment_sentences=True,
                force=True,
                n=1,
            )

        # GROBID outputs <stem>.tei.xml; handle double-extension cases too
        stem = Path(pdf_path).stem
        xml_file = xml_store / f"{stem}.tei.xml"
        if not xml_file.exists():
            candidates = list(xml_store.glob(f"{stem}*.xml"))
            if candidates:
                xml_file = sorted(candidates)[-1]

        if xml_file.exists():
            logger.info(f"GROBID produced XML: {xml_file}")
            return xml_file.read_text(encoding="utf-8")
        else:
            logger.warning(f"GROBID ran but produced no XML for {pdf_path}")
    except Exception as e:
        logger.warning(f"GROBID TEI XML extraction failed for {pdf_path}: {e}")

    return None


def chunk_pdf_fallback(
    pdf_path: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> List[Document]:
    """
    Fallback plain text chunking using PyMuPDF page by page when GROBID XML is unavailable.
    """
    documents = []
    try:
        pdf_doc = pymupdf.open(pdf_path)
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " ", ""],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

        global_chunk_idx = 0
        for page_idx in range(len(pdf_doc)):
            page = pdf_doc[page_idx]
            page_text = page.get_text().strip()
            if not page_text:
                continue

            page_num = page_idx + 1
            chunks = splitter.split_text(page_text)
            for c_idx, chunk in enumerate(chunks):
                global_chunk_idx += 1
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "chunk_id": f"chunk-p{page_num}-c{c_idx + 1}",
                        "page": page_num,
                        "section": f"Page {page_num}",
                        "chunk_size": len(chunk),
                    },
                )
                documents.append(doc)
        pdf_doc.close()
    except Exception as e:
        logger.error(f"Fallback PDF chunking failed for {pdf_path}: {e}")

    return documents


def chunk_document(pdf_path: str, strategy: Optional[str] = None) -> List[Document]:
    """
    Main entry point for document chunking (used by RAG service).
    Attempts layout-aware section extraction first (extract_sections_from_pdf).
    Uses strategy from argument or settings.CHUNKING_STRATEGY ('section_overlap' or 'hierarchical').
    Falls back to GROBID TEI XML and then plain page-by-page chunking.
    """
    if not pdf_path or not os.path.exists(pdf_path):
        return []

    active_strategy = strategy or getattr(settings, "CHUNKING_STRATEGY", "hierarchical")
    paper_id = Path(pdf_path).stem

    # 1. Try layout-aware PyMuPDF section extraction first
    try:
        sections = extract_sections_from_pdf(pdf_path)
        if sections:
            if active_strategy in ("hierarchical", "hierarchical_child"):
                from .chunkers import chunk_hierarchical
                raw_chunks = chunk_hierarchical(
                    sections,
                    child_max_tokens=200,
                    child_overlap=40,
                    paper_id=paper_id,
                )
                docs = [
                    Document(
                        page_content=c["text"],
                        metadata={
                            "chunk_id": c.get("chunk_id", f"chunk_{i+1:02d}"),
                            "child_id": c.get("chunk_id", f"chunk_{i+1:02d}"),
                            "parent_id": c.get("parent_id", ""),
                            "parent_text": c.get("parent_text", ""),
                            "parent_tokens": c.get("parent_tokens", 0),
                            "child_text": c.get("child_text", ""),
                            "char_start": c.get("char_start", 0),
                            "char_end": c.get("char_end", len(c.get("child_text", ""))),
                            "chunk_index": c.get("chunk_index", i),
                            "page": c.get("page", 1),
                            "section": c.get("section", "Section"),
                            "chunk_size": len(c.get("text", "")),
                            "token_count": c.get("token_count", estimate_tokens(c.get("text", ""))),
                            "strategy": "hierarchical",
                        },
                    )
                    for i, c in enumerate(raw_chunks)
                ]
                logger.info(f"Successfully chunked {len(docs)} hierarchical children for {pdf_path}")
                return docs
            else:
                sec_chunks = chunk_sections(sections, strategy=active_strategy, max_tokens=400, overlap=80)
                if sec_chunks:
                    docs = [
                        Document(
                            page_content=c["text"],
                            metadata={
                                "chunk_id": c.get("chunk_id", f"chunk_{i+1:02d}"),
                                "page": c.get("page", 1),
                                "section": c.get("section", "Section"),
                                "chunk_size": len(c.get("text", "")),
                                "strategy": active_strategy,
                            },
                        )
                        for i, c in enumerate(sec_chunks)
                    ]
                    logger.info(f"Successfully chunked {len(docs)} sections via layout-aware {active_strategy} for {pdf_path}")
                    return docs
    except Exception as e:
        logger.warning(f"Layout-aware section chunking failed for {pdf_path}, trying fallbacks: {e}")

    # 2. Try GROBID if available
    xml_text = process_pdf_with_grobid(pdf_path)
    if xml_text:
        docs = recursive_chunker(xml_text)
        if docs:
            logger.info(f"Successfully chunked {len(docs)} sections via GROBID TEI XML")
            return docs

    # 3. Fallback to PyMuPDF page-by-page extraction
    logger.info(f"Using PyMuPDF fallback chunking for {pdf_path}")
    return chunk_pdf_fallback(pdf_path)



# ─────────────────────────────────────────────────────────────────────────────
# Section-based chunking (used by evaluation pipeline / frontend chunking API)
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_ACADEMIC_HEADINGS = {
    "abstract", "introduction", "background", "related work",
    "model architecture", "deep residual learning", "our method",
    "problem formulation", "problem statement", "experiments", "empirical experiments",
    "results", "discussion", "conclusion", "conclusions",
    "references", "scaled dot-product attention", "multi-head attention",
    "encoder and decoder stacks", "positional encoding", "optimizer",
    "network architectures", "identity mapping by shortcuts",
    "low-rank parametrized update matrices", "models", "retriever", "generator",
    "why self-attention", "training", "training data and batching",
    "hardware and schedule", "regularization", "terminologies and conventions"
}


def estimate_tokens(text: str) -> int:
    """Estimates token count for academic English (1 word ≈ 1.33 tokens)."""
    if not text:
        return 0
    words = text.split()
    return max(1, math.ceil(len(words) * 1.33))


def extract_sections_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts structured academic sections from a PDF using layout-aware PyMuPDF.
    Handles split section numbers (e.g. '1\\nIntroduction'), known headings,
    and multi-level section numbering while preserving page boundaries.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    sections: List[Dict[str, Any]] = []
    current_title = "Abstract"
    current_text_lines: List[str] = []
    current_start_page = 1
    current_end_page = 1

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_num = page_idx + 1
        d = page.get_text("dict")

        for b in d.get("blocks", []):
            if b.get("type") == 0:
                block_lines: List[str] = []
                for l in b.get("lines", []):
                    line_spans = [
                        s.get("text", "").strip()
                        for s in l.get("spans", [])
                        if s.get("text", "").strip()
                    ]
                    if line_spans:
                        block_lines.append(" ".join(line_spans))

                if not block_lines:
                    continue

                # Re-attach split small-caps: single uppercase letter followed by space and uppercase sequence (e.g. '1 I NTRODUCTION')
                def _normalize_title_text(s: str) -> str:
                    s_clean = re.sub(r"\b([A-Z])\s+([A-Z]{2,})\b", r"\1\2", s)
                    s_clean = re.sub(r"\bL\s+O\s+RA\b", "LoRA", s_clean, flags=re.IGNORECASE)
                    return re.sub(r"\s+", " ", s_clean).strip()

                # In papers like Attention/LoRA, the number ('1', '3.1') may be on its own line
                if (
                    len(block_lines) >= 2
                    and re.match(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[IVX]+)\.?$", block_lines[0].strip())
                ):
                    first_line = f"{block_lines[0].strip()} {block_lines[1].strip()}"
                    content_start_idx = 2
                else:
                    first_line = block_lines[0].strip()
                    content_start_idx = 1

                first_line = _normalize_title_text(first_line)
                cleaned_line = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s*", "", first_line).strip().lower()
                cleaned_line = re.sub(r"\b([a-z])\s+([a-z]{2,})\b", r"\1\2", cleaned_line)

                is_heading = False
                if 3 <= len(first_line) < 85:
                    if cleaned_line in KNOWN_ACADEMIC_HEADINGS:
                        is_heading = True
                    # Structural number prefix + title (supporting conversational punctuation like ?, ', ", -, :)
                    elif re.match(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[IVX]+)\.?\s+[A-Za-z0-9\s\-_:,\(\)\?\'\"\`]{2,75}[\.\?]?$", first_line):
                        is_heading = True
                    # Typographic bold heuristic on numbered or short title block
                    elif any(s.get("flags", 0) & 2 for l in b.get("lines", [])[:1] for s in l.get("spans", [])):
                        if re.match(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[I|V|X]+)\.?", first_line):
                            is_heading = True

                if is_heading:
                    if current_text_lines:
                        sec_text = "\n".join(current_text_lines).strip()
                        if sec_text:
                            sections.append({
                                "title": current_title,
                                "page_start": current_start_page,
                                "page_end": current_end_page,
                                "text": sec_text,
                                "token_count": estimate_tokens(sec_text),
                            })
                        current_text_lines = []

                    current_title = first_line
                    current_start_page = page_num
                    current_end_page = page_num

                    if len(block_lines) > content_start_idx:
                        current_text_lines.extend(block_lines[content_start_idx:])
                else:
                    current_text_lines.extend(block_lines)
                    current_end_page = page_num

    # Flush final section
    if current_text_lines:
        sec_text = "\n".join(current_text_lines).strip()
        if sec_text:
            sections.append({
                "title": current_title,
                "page_start": current_start_page,
                "page_end": current_end_page,
                "text": sec_text,
                "token_count": estimate_tokens(sec_text),
            })

    doc.close()

    # Fallback: no sections detected → return whole document as one section
    if not sections:
        doc_retry = pymupdf.open(pdf_path)
        full_text = "\n\n".join([str(page.get_text("text")) for page in doc_retry])
        num_pages = len(doc_retry)
        doc_retry.close()
        sections.append({
            "title": "Document Body",
            "page_start": 1,
            "page_end": num_pages,
            "text": full_text.strip(),
            "token_count": estimate_tokens(full_text),
        })

    return sections


def chunk_sections(
    sections: List[Dict[str, Any]],
    strategy: str = "section_overlap",
    max_tokens: int = 400,
    overlap: int = 80,
) -> List[Dict[str, Any]]:
    """
    Transforms structured sections into chunks according to the chosen strategy.

    Strategies:
      - 'section': Pure section-based chunks (one chunk per section).
      - 'section_token': Section-based chunks with token limits (no overlap).
      - 'section_overlap': Section-based chunks with token limits and sliding window overlap.
    """
    valid_strategies = {"section", "section_token", "section_overlap"}
    if strategy not in valid_strategies:
        raise ValueError(f"Unknown strategy '{strategy}'. Must be one of {valid_strategies}")

    chunks: List[Dict[str, Any]] = []

    char_chunk_size = max(200, max_tokens * 4)
    char_chunk_overlap = max(0, overlap * 4) if strategy == "section_overlap" else 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=char_chunk_size,
        chunk_overlap=char_chunk_overlap,
        separators=["\n\n", "\n", ". ", "; ", ", ", " "],
        keep_separator=True,
    )

    for sec_idx, sec in enumerate(sections):
        title = sec.get("title", "Section")
        sec_text = sec.get("text", "")
        start_page = sec.get("page_start", 1)
        end_page = sec.get("page_end", start_page)
        total_tokens = sec.get("token_count", estimate_tokens(sec_text))

        if not sec_text.strip():
            continue

        if strategy == "section":
            chunks.append({
                "chunk_id": f"chunk_sec_{sec_idx+1:02d}",
                "section": title,
                "page": start_page,
                "page_end": end_page,
                "strategy": strategy,
                "token_count": total_tokens,
                "preview": sec_text[:180].replace("\n", " ").strip() + "...",
                "text": sec_text,
            })
        else:
            if total_tokens <= max_tokens:
                chunks.append({
                    "chunk_id": f"chunk_sec_{sec_idx+1:02d}_p01",
                    "section": title,
                    "page": start_page,
                    "page_end": end_page,
                    "strategy": strategy,
                    "token_count": total_tokens,
                    "preview": sec_text[:180].replace("\n", " ").strip() + "...",
                    "text": sec_text,
                })
            else:
                sub_texts = splitter.split_text(sec_text)
                for sub_idx, sub_text in enumerate(sub_texts):
                    cleaned_sub = sub_text.strip()
                    if not cleaned_sub:
                        continue
                    sub_tokens = estimate_tokens(cleaned_sub)
                    ratio = (sub_idx / max(1, len(sub_texts) - 1)) if len(sub_texts) > 1 else 0
                    approx_page = min(end_page, start_page + int(ratio * (end_page - start_page)))
                    suffix = f"_ov_{sub_idx+1:02d}" if strategy == "section_overlap" else f"_p{sub_idx+1:02d}"
                    chunks.append({
                        "chunk_id": f"chunk_sec_{sec_idx+1:02d}{suffix}",
                        "section": title,
                        "page": approx_page,
                        "page_end": end_page,
                        "strategy": strategy,
                        "token_count": sub_tokens,
                        "preview": cleaned_sub[:180].replace("\n", " ").strip() + "...",
                        "text": cleaned_sub,
                    })

    return chunks


def chunk_document_pdf(
    pdf_path: str,
    strategy: str = "section_overlap",
    max_tokens: int = 400,
    overlap: int = 80,
) -> List[Dict[str, Any]]:
    """
    High-level entry point to extract and chunk a research paper PDF using
    the section-based chunking strategies (for evaluation pipeline / chunks API).
    Supports: 'section', 'section_token', 'section_overlap', 'hierarchical'.
    """
    sections = extract_sections_from_pdf(pdf_path)
    paper_id = Path(pdf_path).stem
    if strategy in ("hierarchical", "hierarchical_child"):
        from .chunkers import chunk_hierarchical
        return chunk_hierarchical(sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id)
    return chunk_sections(sections, strategy=strategy, max_tokens=max_tokens, overlap=overlap)
