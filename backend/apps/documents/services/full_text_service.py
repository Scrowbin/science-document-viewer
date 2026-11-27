import logging
import re
from typing import List, Optional, Tuple

import requests

from .crossref_service import clean_doi

logger = logging.getLogger(__name__)

_ARXIV_ID_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arxiv[.:/]\s*)(\d{4}\.\d{4,5}(?:v\d+)?)",
    re.IGNORECASE,
)
_USER_AGENT = "ScientificDocumentManager/1.0 (mailto:contact@scidocmanager.org)"
_MAX_PDF_BYTES = 50 * 1024 * 1024  # 50 MB


def _extract_arxiv_id(doi: str, url: str) -> Optional[str]:
    """Extract an arXiv identifier from a document's DOI or URL."""
    for candidate in (doi or "", url or ""):
        m = _ARXIV_ID_RE.search(candidate)
        if m:
            return m.group(1)
    return None


def _candidate_pdf_urls(doi: str, url: str, timeout: int = 8) -> List[str]:
    """Collect candidate open-access PDF URLs from arXiv, OpenAlex, Semantic Scholar, and Crossref."""
    candidates: List[str] = []
    seen = set()

    def _add(u: Optional[str]) -> None:
        if u and isinstance(u, str):
            u = u.strip()
            if u.startswith(("http://", "https://")) and u not in seen:
                seen.add(u)
                candidates.append(u)

    arxiv_id = _extract_arxiv_id(doi, url)
    if arxiv_id:
        _add(f"https://arxiv.org/pdf/{arxiv_id}.pdf")

    cleaned_doi = clean_doi(doi) if doi else ""
    headers = {"User-Agent": _USER_AGENT}

    if cleaned_doi:
        # 1. OpenAlex open-access PDF URLs
        try:
            resp = requests.get(
                f"https://api.openalex.org/works/doi:{cleaned_doi}",
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                _add((data.get("best_oa_location") or {}).get("pdf_url"))
                _add((data.get("open_access") or {}).get("oa_url"))
                for loc in data.get("locations") or []:
                    _add((loc or {}).get("pdf_url"))
        except Exception as e:
            logger.debug("OpenAlex full-text lookup failed for %s: %s", cleaned_doi, e)

        # 2. Semantic Scholar openAccessPdf
        try:
            resp = requests.get(
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{cleaned_doi}",
                params={"fields": "openAccessPdf"},
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 200:
                oa_pdf = resp.json().get("openAccessPdf") or {}
                _add(oa_pdf.get("url"))
        except Exception as e:
            logger.debug("Semantic Scholar full-text lookup failed for %s: %s", cleaned_doi, e)

        # 3. Crossref link entries
        try:
            resp = requests.get(
                f"https://api.crossref.org/works/{cleaned_doi}",
                headers=headers,
                timeout=timeout,
            )
            if resp.status_code == 200:
                msg = resp.json().get("message") or {}
                for link in msg.get("link") or []:
                    link_url = (link or {}).get("URL", "")
                    ctype = ((link or {}).get("content-type") or "").lower()
                    if "pdf" in ctype or link_url.lower().endswith(".pdf"):
                        _add(link_url)
        except Exception as e:
            logger.debug("Crossref link lookup failed for %s: %s", cleaned_doi, e)

    if url and url.strip().lower().endswith(".pdf"):
        _add(url)

    return candidates


def _download_valid_pdf(pdf_url: str, timeout: int = 20) -> Optional[bytes]:
    """Download URL and return raw bytes only if it is a valid %PDF- file within size limits."""
    try:
        resp = requests.get(
            pdf_url,
            headers={"User-Agent": _USER_AGENT, "Accept": "application/pdf,*/*;q=0.8"},
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            return None

        chunks = []
        total = 0
        for chunk in resp.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total += len(chunk)
            if total > _MAX_PDF_BYTES:
                logger.warning("PDF from %s exceeded %d bytes limit", pdf_url, _MAX_PDF_BYTES)
                return None
            chunks.append(chunk)

        content = b"".join(chunks)
        if len(content) < 1024 or not content.lstrip().startswith(b"%PDF-"):
            return None
        return content
    except Exception as e:
        logger.debug("PDF download failed from %s: %s", pdf_url, e)
        return None


def find_and_download_full_text(doi: str, url: str, title: str = "") -> Optional[Tuple[str, bytes]]:
    """
    Search open-access sources for a full-text PDF matching the given DOI/URL.
    Returns (filename, pdf_bytes) on success, or None if no valid PDF could be retrieved.
    """
    candidates = _candidate_pdf_urls(doi, url)
    for pdf_url in candidates:
        content = _download_valid_pdf(pdf_url)
        if content:
            arxiv_id = _extract_arxiv_id(doi, url)
            if arxiv_id:
                filename = f"{arxiv_id}.pdf"
            else:
                safe_slug = re.sub(r"[^A-Za-z0-9._-]+", "_", (title or clean_doi(doi) or "paper"))[:60].strip("_")
                filename = f"{safe_slug or 'paper'}.pdf"
            return filename, content
    return None
