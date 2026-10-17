from typing import List, Dict, Any
from bs4 import BeautifulSoup
from langchain_core.embeddings import Embeddings


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
