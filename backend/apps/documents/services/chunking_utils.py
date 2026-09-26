"""
Chunking utilities for document processing and RAG pipeline.
Incorporates heading-aware semantic splitting alongside layout-aware character splitting.
"""

from typing import Any, Dict, List, Optional


def markdown_to_chunks(markdown: str) -> List[Dict[str, Any]]:
    """
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
