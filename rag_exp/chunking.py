from typing import List, Dict, Any, Optional
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
)
from langchain_core.documents import Document
from utils import extract_structured_body, assemble_full_text
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings


def recursive_chunker(
    xml_text: str, chunk_size: int = 500, chunk_overlap: int = 50, benchmark=False
) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    if not benchmark:
        sections = extract_structured_body(xml_text)
    else:
        sections = [{"text": xml_text}]
    if not sections:
        return []

    documents = []
    chunk_counter = 0

    for sec in sections:
        sec_text = sec.get("text", "")
        if not sec_text:
            continue

        raw_chunks = splitter.split_text(sec_text)
        for chunk in raw_chunks:
            chunk_counter += 1
            doc = Document(
                page_content=chunk,
                metadata={
                    "chunk_id": chunk_counter,
                    "chunk_size": len(chunk),
                },
            )
            documents.append(doc)

    return documents


def fixed_size_chunker(xml_text, chunk_size=550, chunk_overlap=150, benchmark=False):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    if not benchmark:
        doc = extract_structured_body(xml_text)
        chunks = text_splitter.split_text(assemble_full_text(doc))
    else:
        chunks = text_splitter.split_text(xml_text)
    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "chunk_id": i,
                "chunk_size": len(chunk),
            },
        )
        documents.append(doc)

    return documents


def semantic_chunker(xml_text, embeddings=None, benchmark=False):
    if embeddings is None:
        embeddings = HuggingFaceEmbeddings(
            model_name="ibm-granite/granite-embedding-125m-english"
        )
    text_splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=85,  # Splits text when similarity drops into bottom 15%
    )
    if not benchmark:
        doc = extract_structured_body(xml_text)
        chunks = text_splitter.split_text(assemble_full_text(doc))
    else:
        chunks = text_splitter.split_text(xml_text)
    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "chunk_id": i,
                "chunk_size": len(chunk),
            },
        )
        documents.append(doc)

    return documents
