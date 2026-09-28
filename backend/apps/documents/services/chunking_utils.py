"""
Chunking utilities for scientific document processing and RAG evaluation pipeline.
Implements the 3 core comparative chunking strategies:
  1. 'section': Pure section-based chunking (Baseline).
  2. 'section_token': Section-based with token size boundaries.
  3. 'section_overlap': Section-based with token limits and sliding overlap window.
"""

import logging
import math
import os
import re
from typing import Any, Dict, List, Optional

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Standard academic section headings regex
SECTION_HEADING_REGEX = re.compile(
    r"^(?:"
    r"(?:(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[I|V|X]+)\.?\s+[A-Z][A-Za-z0-9\s\-_:,\(\)]{2,60})"
    r"|(?:Abstract|Introduction|Related Work|Background|Methodology|Methods|Model Architecture|System Overview|Experiments|Evaluation|Results|Discussion|Conclusion|Conclusions|References|Acknowledgments)"
    r")$",
    re.IGNORECASE,
)


def estimate_tokens(text: str) -> int:
    """
    Estimates token count for academic English text.
    Standard approximation: 1 word ~= 1.33 tokens.
    """
    if not text:
        return 0
    words = text.split()
    return max(1, math.ceil(len(words) * 1.33))


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


def extract_sections_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts structured academic sections from a PDF file using layout-aware PyMuPDF.
    Handles separate section number lines (e.g. '1\nIntroduction'), standard academic
    headings, and multi-level section numbering while preserving page boundaries.
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

                # In papers like Attention, LoRA, etc., the number ('1', '3.1') is on line 0, and title is on line 1
                if len(block_lines) >= 2 and re.match(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[I|V|X]+)\.?$", block_lines[0].strip()):
                    first_line = f"{block_lines[0].strip()} {block_lines[1].strip()}"
                    content_start_idx = 2
                else:
                    first_line = block_lines[0].strip()
                    content_start_idx = 1

                cleaned_line = re.sub(r"^[0-9]+(?:\.[0-9]+)*\.?\s*", "", first_line).strip().lower()

                is_heading = False
                if len(first_line) < 75:
                    if cleaned_line in KNOWN_ACADEMIC_HEADINGS:
                        is_heading = True
                    elif re.match(r"^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[I|V|X]+)\.?\s+[A-Z][A-Za-z0-9\s\-_:,\(\)]{2,50}$", first_line):
                        is_heading = True

                if is_heading:
                    # Flush previous section if it has content
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

    # Fallback: if no distinct sections detected, return full document as one section
    if not sections and len(doc) > 0:
        doc_retry = pymupdf.open(pdf_path)
        full_text = "\n\n".join([page.get_text("text") for page in doc_retry])
        doc_retry.close()
        sections.append({
            "title": "Document Body",
            "page_start": 1,
            "page_end": len(doc),
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
    Transforms structured sections into chunks according to the chosen experimental strategy.

    Strategies:
      - 'section': Pure section-based chunks. Each section is a single chunk regardless of length.
      - 'section_token': Section-based chunks with token limits (no overlap).
      - 'section_overlap': Section-based chunks with token limits and sliding window overlap.
    """
    valid_strategies = {"section", "section_token", "section_overlap"}
    if strategy not in valid_strategies:
        raise ValueError(f"Unknown strategy '{strategy}'. Must be one of {valid_strategies}")

    chunks: List[Dict[str, Any]] = []

    # Approximate character equivalents: 1 token ~= 4 characters
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
            # Strategy A: Baseline - Keep whole section as one chunk
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
            # Strategy B or C: Split with RecursiveCharacterTextSplitter
            if total_tokens <= max_tokens:
                # Small enough to keep as a single chunk
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
                    # Interpolate approximate page number across the section
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
    High-level entry point to extract and chunk a research paper PDF.
    """
    sections = extract_sections_from_pdf(pdf_path)
    return chunk_sections(sections, strategy=strategy, max_tokens=max_tokens, overlap=overlap)


def markdown_to_chunks(markdown: str) -> List[Dict[str, Any]]:
    """
    Backward-compatible markdown heading splitter.
    Split markdown text by heading levels (#, ##, ###) while preserving
    section hierarchy in metadata.
    """
    lines = markdown.splitlines()
    chunks: List[Dict[str, Any]] = []
    current: List[str] = []
    headings: List[str] = []

    for line in lines:
        if line.startswith("#"):
            if current:
                chunks.append({
                    "text": "\n".join(current).strip(),
                    "section": headings[-1] if headings else None,
                })
                current = []

            level = len(line) - len(line.lstrip("#"))
            title = line[level:].strip()
            headings = headings[: level - 1]
            headings.append(title)

        current.append(line)

    if current:
        chunks.append({
            "text": "\n".join(current).strip(),
            "section": headings[-1] if headings else None,
        })

    return [chunk for chunk in chunks if chunk["text"]]
