import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import pymupdf
import requests
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from ..data_extractor.data_extractor import data_extractor
from .crossref_service import clean_doi, fetch_metadata_from_doi
from ..models import (
    Author,
    Document,
    DocumentAuthor,
    DocumentDomain,
    DocumentTag,
    Domain,
    Tag,
)

logger = logging.getLogger(__name__)

ARXIV_ID_REGEX = re.compile(
    r"(?:arxiv(?::\s*|[/]|\.org/(?:abs|pdf)/)|arXiv\s+preprint\s+)([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)",
    re.IGNORECASE,
)
DOI_REGEX = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.IGNORECASE)


def parse_date_to_datetime(val: Optional[str]) -> Optional[datetime]:
    """Parse year ('2017') or ISO date string ('2017-06-12') into an aware datetime."""
    if not val:
        return None
    try:
        val = str(val).strip()
        if len(val) == 4 and val.isdigit():
            return timezone.make_aware(datetime(int(val), 1, 1))
        dt = parse_datetime(val)
        if dt:
            return dt if timezone.is_aware(dt) else timezone.make_aware(dt)
        d = parse_date(val[:10])
        if d:
            return timezone.make_aware(datetime(d.year, d.month, d.day))
    except Exception as e:
        logger.debug("Date parsing failed for %s: %s", val, e)
    return None


def apply_pdf_metadata_to_document(doc: Document) -> bool:
    """
    Extracts metadata from doc.file and updates the Document record in PostgreSQL.
    Returns True if enriched metadata was applied.
    """
    if not doc.file:
        return False

    # Use the higher‑level helper so tests can patch it
    meta = extract_metadata_from_pdf(doc.file.path)
    # Fallback to basic PDF info if GROBID/auto extractor returns nothing
    if not meta or not meta.get("title"):
        try:
            pdf_doc = pymupdf.open(doc.file.path)
            info = pdf_doc.metadata or {}
            pdf_doc.close()
            fallback_title = info.get("title") or ""
            meta = {"title": fallback_title.strip()}
        except Exception as e:
            logger.debug("Fallback PDF metadata extraction failed: %s", e)
            meta = {}
    if not meta.get("title"):
        return False

    file_name = doc.file.name or "document"
    basename = os.path.splitext(os.path.basename(file_name))[0]
    extracted_title = meta.get("title", "").strip()

    # Apply extracted title if available and doc.title is empty, raw filename, or generic
    is_raw_title = (
        not doc.title
        or doc.title == basename
        or basename.startswith(doc.title)
        or doc.title.startswith(basename)
        or bool(re.match(r"^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$", doc.title))
        or doc.title.lower()
        in ("sample_paper", "document", "uploaded document", "untitled document")
    )
    if extracted_title and (is_raw_title or doc.title != extracted_title):
        doc.title = extracted_title
        doc.short_title = meta.get("short_title", extracted_title[:100])

    if not doc.doi and meta.get("doi"):
        doc.doi = meta["doi"]

    if not doc.url and meta.get("url"):
        doc.url = meta["url"]

    if (
        not doc.repository or doc.repository in ("", "Local Upload", "Crossref")
    ) and meta.get("repository"):
        doc.repository = meta["repository"]

    if not doc.extra and meta.get("extra"):
        doc.extra = meta["extra"]

    if meta.get("date"):
        parsed_dt = parse_date_to_datetime(meta["date"])
        if parsed_dt:
            # Update date if empty or if currently set to default placeholder year (>= 2025)
            if not doc.date or (
                doc.date.year >= 2025 and parsed_dt.year < doc.date.year
            ):
                doc.date = parsed_dt

    doc.save()

    # Link Authors cleanly
    extracted_authors = meta.get("authors", [])
    if extracted_authors:
        # Purge any dummy placeholder authors on this document
        DocumentAuthor.objects.filter(
            document=doc,
            author__last_name__in=[
                "Unknown",
                "Unknown Author",
                "Uploaded Document",
                "",
            ],
        ).delete()

        for idx, author_name in enumerate(extracted_authors):
            clean_name = re.sub(r"[*∗†‡§0-9]+", "", author_name).strip()
            if not clean_name:
                continue
            parts = clean_name.rsplit(" ", 1)
            first_name = parts[0].strip() if len(parts) > 1 else ""
            last_name = parts[-1].strip() if len(parts) > 0 else "Unknown"
            if last_name:
                author_obj, _ = Author.objects.get_or_create(
                    first_name=first_name, last_name=last_name
                )
                DocumentAuthor.objects.get_or_create(
                    document=doc, author=author_obj, defaults={"author_order": idx + 1}
                )

    # Link Tags
    for tag_name in meta.get("tags", []):
        tag_clean = tag_name.strip()
        if tag_clean:
            tag_obj, _ = Tag.objects.get_or_create(name=tag_clean[:100])
            DocumentTag.objects.get_or_create(document=doc, tag=tag_obj)

    # Link Domains
    for domain_name in meta.get("domains", []):
        domain_clean = domain_name.strip()
        if domain_clean:
            domain_obj, _ = Domain.objects.get_or_create(name=domain_clean[:150])
            DocumentDomain.objects.get_or_create(document=doc, domain=domain_obj)
    return True


def extract_metadata_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extracts structured academic metadata from a PDF file using data_extractor pipeline.
    """
    meta = data_extractor(file_path)
    if isinstance(meta, dict):
        return meta
    return {}


def fetch_arxiv_metadata(arxiv_id: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """
    Query the official arXiv API to resolve academic metadata.
    """
    clean_id = re.sub(r"v\d+$", "", arxiv_id.strip())
    url = f"https://export.arxiv.org/api/query?id_list={clean_id}"
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=timeout,
        )
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is not None:
                title_elem = entry.find("atom:title", ns)
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip().replace("\n", " ")
                    authors = []
                    for a in entry.findall("atom:author", ns):
                        name_elem = a.find("atom:name", ns)
                        if name_elem is not None and name_elem.text:
                            authors.append(name_elem.text.strip())
                    published_elem = entry.find("atom:published", ns)
                    published = (
                        published_elem.text.strip()[:10]
                        if published_elem is not None and published_elem.text
                        else ""
                    )
                    summary_elem = entry.find("atom:summary", ns)
                    summary = (
                        summary_elem.text.strip().replace("\n", " ")
                        if summary_elem is not None and summary_elem.text
                        else ""
                    )
                    return {
                        "title": title,
                        "short_title": title[:100],
                        "authors": authors,
                        "date": published,
                        "doi": f"10.48550/arXiv.{clean_id}",
                        "url": f"https://arxiv.org/abs/{clean_id}",
                        "repository": "arXiv",
                        "extra": summary,
                    }
    except Exception as e:
        logger.warning("arXiv lookup failed for %s: %s", clean_id, e)
    return None


#
# def extract_metadata_from_pdf(file_path: str) -> Dict[str, Any]:
#     """
#     Extracts structured academic metadata from a PDF file.
#     Tiers:
#     1. First-Page Identifier Detection (arXiv ID / DOI) -> queries arXiv or Crossref/OpenAlex.
#     2. Embedded PDF Metadata Dictionary (/Info dict).
#     3. Layout & Font-Size Heuristic (Largest text on Page 1 = Title).
#     """
#     if not os.path.exists(file_path):
#         return {}
#
#     try:
#         doc = pymupdf.open(file_path)
#     except Exception as e:
#         logger.warning("Could not open PDF file %s with PyMuPDF: %s", file_path, e)
#         return {}
#
#     if len(doc) == 0:
#         return {}
#
#     page0 = doc[0]
#     raw_text = page0.get_text()
#     p0_text: str = raw_text if isinstance(raw_text, str) else str(raw_text or "")
#     basename = os.path.splitext(os.path.basename(file_path))[0]
#
#     # --- Tier 1: Check for arXiv ID ---
#     logger.info("[PDF-EXTRACT] [TIER 1] Scanning Page 1 text for arXiv ID...")
#     arxiv_match = ARXIV_ID_REGEX.search(p0_text)
#     if not arxiv_match and re.match(r"^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$", basename):
#         arxiv_match = re.match(r"^([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)$", basename)
#
#     if arxiv_match:
#         arxiv_id = arxiv_match.group(1)
#         logger.info(
#             "[PDF-EXTRACT] [TIER 1] Matched arXiv ID: %s. Querying arXiv registry API...",
#             arxiv_id,
#         )
#         meta = fetch_arxiv_metadata(arxiv_id)
#         if meta and meta.get("title"):
#             logger.info(
#                 "[PDF-EXTRACT] [TIER 1] Resolved successfully: '%s' by %d authors",
#                 meta.get("title"),
#                 len(meta.get("authors", [])),
#             )
#             doc.close()
#             return meta
#         else:
#             logger.warning(
#                 "[PDF-EXTRACT] [TIER 1] arXiv lookup did not return title for %s, falling back...",
#                 arxiv_id,
#             )
#
#     # --- Tier 2: Check for DOI on Page 1 ---
#     logger.info("[PDF-EXTRACT] [TIER 2] Scanning Page 1 for DOI...")
#     doi_match = DOI_REGEX.search(p0_text)
#     if doi_match:
#         raw_doi = doi_match.group(1).rstrip(".,;()[]")
#         doi = clean_doi(raw_doi)
#         if doi:
#             logger.info(
#                 "[PDF-EXTRACT] [TIER 2] Matched DOI: %s. Querying Crossref / OpenAlex...",
#                 doi,
#             )
#             meta = fetch_metadata_from_doi(doi)
#             if meta and meta.get("title"):
#                 logger.info(
#                     "[PDF-EXTRACT] [TIER 2] Resolved successfully: '%s'",
#                     meta.get("title"),
#                 )
#                 doc.close()
#                 return meta
#
#     # --- Tier 3: Embedded Metadata & Layout Heuristic Fallback ---
#     logger.info(
#         "[PDF-EXTRACT] [TIER 3] Running embedded metadata & visual layout heuristics..."
#     )
#     embedded = doc.metadata or {}
#     pdf_title = (embedded.get("title") or "").strip()
#     pdf_author = (embedded.get("author") or "").strip()
#
#     # Filter out generic LaTeX or empty titles
#     generic_titles = {
#         "latex with hyperref",
#         "untitled",
#         "document",
#         "microsoft word",
#         "",
#     }
#     if pdf_title.lower() in generic_titles or pdf_title.lower() == basename.lower():
#         pdf_title = ""
#
#     # If title not in metadata, inspect largest font spans on Page 1
#     heuristic_title = ""
#     heuristic_authors: List[str] = []
#     heuristic_abstract = ""
#     try:
#         raw_dict = page0.get_text("dict")
#         p_dict: Dict[str, Any] = raw_dict if isinstance(raw_dict, dict) else {}
#         spans = []
#         for b in p_dict.get("blocks", []):
#             if b.get("type") == 0:
#                 for line in b.get("lines", []):
#                     for s in line.get("spans", []):
#                         txt = s.get("text", "").strip()
#                         size = s.get("size", 0)
#                         y_pos = s.get("bbox", [0, 0, 0, 0])[1]
#                         if (
#                             txt
#                             and len(txt) > 2
#                             and not txt.lower().startswith(
#                                 (
#                                     "arxiv",
#                                     "http",
#                                     "doi",
#                                     "published as",
#                                     "under review",
#                                     "preprint",
#                                 )
#                             )
#                         ):
#                             spans.append((size, y_pos, txt))
#
#         title_y_max = 0.0
#         if spans:
#             spans.sort(key=lambda x: x[0], reverse=True)
#             max_size = spans[0][0]
#             if max_size >= 13.0:
#                 # Gather all spans with font size close to max_size and sort by vertical reading order
#                 title_candidates = [
#                     item for item in spans if abs(item[0] - max_size) < 1.0
#                 ]
#                 title_candidates.sort(key=lambda x: x[1])
#                 heuristic_title = " ".join(
#                     item[2] for item in title_candidates[:4]
#                 ).strip()
#                 title_y_max = max(item[1] for item in title_candidates)
#
#         # Detect abstract position & author candidates between title and abstract
#         abstract_y = 0.0
#         for b in p_dict.get("blocks", []):
#             if b.get("type") == 0:
#                 for line in b.get("lines", []):
#                     for s in line.get("spans", []):
#                         if s.get("text", "").strip().lower() == "abstract":
#                             abstract_y = s.get("bbox", [0, 0, 0, 0])[1]
#                             break
#                     if abstract_y:
#                         break
#
#         # Author detection heuristic: spans between title and abstract
#         not doc.title
#         or doc.title == basename
#         or basename.startswith(doc.title)
#         or doc.title.startswith(basename)
#         or bool(re.match(r'^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$', doc.title))
#         or doc.title.lower() in ('sample_paper', 'document', 'uploaded document', 'untitled document')
#     )
#     if extracted_title and (is_raw_title or doc.title != extracted_title):
#         doc.title = extracted_title
#         doc.short_title = meta.get('short_title', extracted_title[:100])
#
#     if not doc.doi and meta.get('doi'):
#         doc.doi = meta['doi']
#
#     if not doc.url and meta.get('url'):
#         doc.url = meta['url']
#
#     if (not doc.repository or doc.repository in ('', 'Local Upload', 'Crossref')) and meta.get('repository'):
#         doc.repository = meta['repository']
#
#     if not doc.extra and meta.get('extra'):
#         doc.extra = meta['extra']
#
#     if meta.get('date'):
#         parsed_dt = parse_date_to_datetime(meta['date'])
#         if parsed_dt:
#             # Update date if empty or if currently set to default placeholder year (>= 2025)
#             if not doc.date or (doc.date.year >= 2025 and parsed_dt.year < doc.date.year):
#                 doc.date = parsed_dt
#
#     doc.save()
#
#     # Link Authors cleanly
#     extracted_authors = meta.get('authors', [])
#     if extracted_authors:
#         # Purge any dummy placeholder authors on this document
#         DocumentAuthor.objects.filter(
#             document=doc,
#             author__last_name__in=['Unknown', 'Unknown Author', 'Uploaded Document', '']
#         ).delete()
#
#         for idx, author_name in enumerate(extracted_authors):
#             clean_name = re.sub(r'[*∗†‡§0-9]+', '', author_name).strip()
#             if not clean_name:
#                 continue
#             parts = clean_name.rsplit(' ', 1)
#             first_name = parts[0].strip() if len(parts) > 1 else ''
#             last_name = parts[-1].strip() if len(parts) > 0 else 'Unknown'
#             if last_name:
#                 author_obj, _ = Author.objects.get_or_create(
#                     first_name=first_name,
#                     last_name=last_name
#                 )
#                 DocumentAuthor.objects.get_or_create(
#                     document=doc,
#                     author=author_obj,
#                     defaults={'author_order': idx + 1}
#                 )
#
#     # Link Tags
#     for tag_name in meta.get('tags', []):
#         tag_clean = tag_name.strip()
#         if tag_clean:
#             tag_obj, _ = Tag.objects.get_or_create(name=tag_clean[:100])
#             DocumentTag.objects.get_or_create(document=doc, tag=tag_obj)
#
#     # Link Domains
#     for domain_name in meta.get('domains', []):
#         domain_clean = domain_name.strip()
#         if domain_clean:
#             domain_obj, _ = Domain.objects.get_or_create(name=domain_clean[:150])
#             DocumentDomain.objects.get_or_create(document=doc, domain=domain_obj)
#
#     return True
#
