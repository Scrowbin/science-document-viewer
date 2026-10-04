import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pymupdf
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_core.documents import Document
from django.conf import settings

logger = logging.getLogger(__name__)


def extract_structured_body(xml_text: str) -> List[Dict[str, Any]]:
    """
    Extracts structured abstract and body sections with paragraphs from TEI XML.
    """
    soup = BeautifulSoup(xml_text, "xml")
    sections = []

    # 1. Extract Abstract
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

    # 2. Extract Body
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
    """
    Combines sections into a formatted text block with section headings.
    """
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


def chunk_tei_xml(
    xml_text: str, chunk_size: int = 500, chunk_overlap: int = 50
) -> List[Document]:
    """
    Chunks TEI XML into LangChain Document objects with section metadata.
    """
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


def process_pdf_with_grobid(pdf_path: str) -> Optional[str]:
    """
    Uses GrobidClient to process full text PDF and save TEI XML in xml_store.
    """
    try:
        from grobid_client.grobid_client import GrobidClient

        project_root = Path(settings.BASE_DIR).parent
        xml_store = project_root / "xml_store"
        xml_store.mkdir(exist_ok=True)

        config_path = os.path.join(settings.BASE_DIR, "grobid.json")

        client = GrobidClient(config_path=config_path)
        client.process(
            service="processFulltextDocument",
            input_path=pdf_path,
            output=str(xml_store),
            consolidate_header=True,
            consolidate_citations=True,
            include_raw_citations=True,
            segment_sentences=True,
            force=True,
        )

        stem = Path(pdf_path).stem
        xml_file = xml_store / f"{stem}.tei.xml"
        if xml_file.exists():
            return xml_file.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Grobid TEI XML extraction failed for {pdf_path}: {e}")

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


def chunk_document(pdf_path: str) -> List[Document]:
    """
    Main entry point for document chunking.
    Attempts GROBID TEI XML chunking first, falling back to PyMuPDF page-by-page chunking.
    """
    if not pdf_path or not os.path.exists(pdf_path):
        return []

    # Try GROBID first
    xml_text = process_pdf_with_grobid(pdf_path)
    if xml_text:
        docs = chunk_tei_xml(xml_text)
        if docs:
            logger.info(f"Successfully chunked {len(docs)} sections via GROBID TEI XML")
            return docs

    # Fallback to PyMuPDF page extraction
    logger.info(f"Using PyMuPDF fallback chunking for {pdf_path}")
    return chunk_pdf_fallback(pdf_path)
