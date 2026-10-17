import grobid_tei_xml
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_core.documents import Document

# %%


def extract_structured_body(xml_text: str):
    soup = BeautifulSoup(xml_text, "xml")

    text = soup.find("text")
    if not text:
        return []

    text_body_section = []

    # Abstract
    abstract = soup.find("abstract")
    if abstract:
        abstract_paragraphs = [
            p.get_text(separator=" ", strip=True) for p in abstract.find_all("p")
        ]

        if not abstract_paragraphs:
            abstract_text = abstract.get_text(separator=" ", strip=True)
            if abstract_text:
                abstract_paragraphs = [abstract_text]

        if abstract_paragraphs:
            text_body_section.append(
                {
                    "section": "Abstract",
                    "paragraphs": abstract_paragraphs,
                    "text": "\n\n".join(abstract_paragraphs),
                }
            )

    # Body
    body = text.find("body")
    if not body:
        return text_body_section

    for div in body.find_all("div", recursive=False):
        head = div.find("head")
        head_title = (
            head.get_text(separator=" ", strip=True) if head else "Untitled Section"
        )

        paras = [
            p.get_text(separator=" ", strip=True)
            for p in div.find_all("p", recursive=False)
        ]

        if paras:
            text_body_section.append(
                {
                    "section": head_title,
                    "paragraphs": paras,
                    "text": "\n\n".join(paras),
                }
            )

    return text_body_section


def assemble_full_text(sections: list[dict]) -> str:
    """Combines all sections into a single continuous text block,

    prefixing each section with its title.
    """
    blocks = []
    for sec in sections:
        title = sec.get("section", "").strip()
        body_text = sec.get("text", "").strip()

        if not body_text:
            continue

        # Adding markdown-style headers preserves context when chunked
        if title:
            blocks.append(f"## {title}\n{body_text}")
        else:
            blocks.append(body_text)

    # Join distinct sections with double newlines
    return "\n\n".join(blocks)


# %%


def fixed_size_chunk(pure_tei_xml, chunk_size=250, chunk_overlap=50):
    doc = extract_structured_body(pure_tei_xml)
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(assemble_full_text(doc))

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


def recursive_chunking(pure_tei_xml, chunk_size=250, chunk_overlap=50):
    doc = extract_structured_body(pure_tei_xml)
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    chunks = text_splitter.split_text(assemble_full_text(doc))

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
