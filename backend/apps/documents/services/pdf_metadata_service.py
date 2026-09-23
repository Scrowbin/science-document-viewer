import logging
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional

import pymupdf
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .crossref_service import clean_doi, fetch_metadata_from_doi
from ..models import Author, Document, DocumentAuthor, DocumentDomain, DocumentTag, Domain, Tag

logger = logging.getLogger(__name__)

ARXIV_ID_REGEX = re.compile(r'arxiv:\s*([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)', re.IGNORECASE)
DOI_REGEX = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)', re.IGNORECASE)


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


def fetch_arxiv_metadata(arxiv_id: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Query the official arXiv API to resolve academic metadata for a given arXiv ID."""
    clean_id = re.sub(r'v\d+$', '', arxiv_id.strip())
    url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'SciDocManager/1.0 (mailto:contact@scidocmanager.org)'})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is None:
            return None

        title_elem = entry.find('atom:title', ns)
        if title_elem is None or not title_elem.text:
            return None

        title = title_elem.text.strip().replace('\n', ' ')
        if title.lower() in ('error', 'untitled', ''):
            return None

        authors: List[str] = []
        for a in entry.findall('atom:author', ns):
            name_elem = a.find('atom:name', ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text.strip())

        published_elem = entry.find('atom:published', ns)
        published = published_elem.text.strip() if published_elem is not None and published_elem.text else ''

        summary_elem = entry.find('atom:summary', ns)
        summary = summary_elem.text.strip().replace('\n', ' ') if summary_elem is not None and summary_elem.text else ''

        categories: List[str] = []
        for c in entry.findall('atom:category', ns):
            term = c.attrib.get('term')
            if term:
                categories.append(term)

        # Extract DOI if arXiv links a journal DOI
        journal_doi = None
        for link in entry.findall('atom:link', ns):
            if link.attrib.get('title') == 'doi':
                journal_doi = link.attrib.get('href', '').replace('http://dx.doi.org/', '').replace('https://doi.org/', '')

        doi = journal_doi if journal_doi else f"10.48550/arXiv.{clean_id}"

        return {
            'title': title,
            'short_title': title[:100],
            'authors': authors,
            'date': published[:10] if published else '',
            'doi': doi,
            'url': f"https://arxiv.org/abs/{clean_id}",
            'repository': 'arXiv',
            'item_type': 'preprint' if not journal_doi else 'journalArticle',
            'extra': summary,
            'tags': categories[:5] if categories else ['Computer Science'],
            'domains': ['Computer Science'] if any(c.startswith('cs.') for c in categories) else ['General Science'],
        }
    except Exception as e:
        logger.warning("arXiv lookup failed for %s: %s", clean_id, e)
        return None


def extract_metadata_from_pdf(file_path: str) -> Dict[str, Any]:
    """
    Extracts structured academic metadata from a PDF file.
    Tiers:
    1. First-Page Identifier Detection (arXiv ID / DOI) -> queries arXiv or Crossref/OpenAlex.
    2. Embedded PDF Metadata Dictionary (/Info dict).
    3. Layout & Font-Size Heuristic (Largest text on Page 1 = Title).
    """
    if not os.path.exists(file_path):
        return {}

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        logger.warning("Could not open PDF file %s with PyMuPDF: %s", file_path, e)
        return {}

    if len(doc) == 0:
        return {}

    page0 = doc[0]
    raw_text = page0.get_text()
    p0_text: str = raw_text if isinstance(raw_text, str) else str(raw_text or '')
    basename = os.path.splitext(os.path.basename(file_path))[0]

    # --- Tier 1: Check for arXiv ID ---
    arxiv_match = ARXIV_ID_REGEX.search(p0_text)
    if not arxiv_match and re.match(r'^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$', basename):
        arxiv_match = re.match(r'^([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)$', basename)

    if arxiv_match:
        arxiv_id = arxiv_match.group(1)
        meta = fetch_arxiv_metadata(arxiv_id)
        if meta and meta.get('title'):
            doc.close()
            return meta

    # --- Tier 2: Check for DOI on Page 1 ---
    doi_match = DOI_REGEX.search(p0_text)
    if doi_match:
        raw_doi = doi_match.group(1).rstrip('.,;()[]')
        doi = clean_doi(raw_doi)
        if doi:
            meta = fetch_metadata_from_doi(doi)
            if meta and meta.get('title'):
                doc.close()
                return meta

    # --- Tier 3: Embedded Metadata & Layout Heuristic Fallback ---
    embedded = doc.metadata or {}
    pdf_title = (embedded.get('title') or '').strip()
    pdf_author = (embedded.get('author') or '').strip()

    # Filter out generic LaTeX or empty titles
    generic_titles = {'latex with hyperref', 'untitled', 'document', 'microsoft word', ''}
    if pdf_title.lower() in generic_titles or pdf_title.lower() == basename.lower():
        pdf_title = ''

    # If title not in metadata, inspect largest font spans on Page 1
    heuristic_title = ''
    try:
        raw_dict = page0.get_text('dict')
        p_dict: Dict[str, Any] = raw_dict if isinstance(raw_dict, dict) else {}
        spans = []
        for b in p_dict.get('blocks', []):
            if b.get('type') == 0:
                for line in b.get('lines', []):
                    for s in line.get('spans', []):
                        txt = s.get('text', '').strip()
                        size = s.get('size', 0)
                        if txt and len(txt) > 3 and not txt.startswith('arXiv:'):
                            spans.append((size, txt))

        if spans:
            spans.sort(key=lambda x: x[0], reverse=True)
            max_size = spans[0][0]
            if max_size >= 13.0:
                # Gather all spans with font size close to max_size
                title_parts = [t for s, t in spans if abs(s - max_size) < 1.0]
                heuristic_title = ' '.join(title_parts[:3]).strip()
    except Exception as e:
        logger.debug("Layout heuristic extraction failed: %s", e)

    final_title = pdf_title or heuristic_title or basename
    authors = [pdf_author] if pdf_author else []

    doc.close()

    return {
        'title': final_title,
        'short_title': final_title[:100],
        'authors': authors,
        'date': embedded.get('creationDate', '')[:10] if embedded.get('creationDate') else '',
        'doi': '',
        'url': '',
        'repository': 'Direct PDF Upload',
        'item_type': 'journalArticle',
        'extra': embedded.get('subject', '') or '',
        'tags': [t.strip() for t in embedded.get('keywords', '').split(',') if t.strip()][:5],
        'domains': ['General Science'],
    }


def apply_pdf_metadata_to_document(doc: Document) -> bool:
    """
    Extracts metadata from doc.file and updates the Document record in PostgreSQL.
    Returns True if enriched metadata was applied.
    """
    if not doc.file:
        return False

    meta = extract_metadata_from_pdf(doc.file.path)
    if not meta or not meta.get('title'):
        return False

    file_name = doc.file.name or 'document'
    basename = os.path.splitext(os.path.basename(file_name))[0]
    extracted_title = meta.get('title', '').strip()

    # Apply extracted title if available and doc.title is empty, raw filename, or generic
    is_raw_title = (
        not doc.title
        or doc.title == basename
        or basename.startswith(doc.title)
        or doc.title.startswith(basename)
        or bool(re.match(r'^[0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?$', doc.title))
        or doc.title.lower() in ('sample_paper', 'document', 'uploaded document', 'untitled document')
    )
    if extracted_title and (is_raw_title or doc.title != extracted_title):
        doc.title = extracted_title
        doc.short_title = meta.get('short_title', extracted_title[:100])

    if not doc.doi and meta.get('doi'):
        doc.doi = meta['doi']

    if not doc.url and meta.get('url'):
        doc.url = meta['url']

    if (not doc.repository or doc.repository in ('', 'Local Upload', 'Crossref')) and meta.get('repository'):
        doc.repository = meta['repository']

    if not doc.extra and meta.get('extra'):
        doc.extra = meta['extra']

    if not doc.date and meta.get('date'):
        parsed_dt = parse_date_to_datetime(meta['date'])
        if parsed_dt:
            doc.date = parsed_dt

    doc.save()

    # Link Authors
    for idx, author_name in enumerate(meta.get('authors', [])):
        parts = author_name.strip().rsplit(' ', 1)
        first_name = parts[0].strip() if len(parts) > 1 else ''
        last_name = parts[-1].strip() if len(parts) > 0 else 'Unknown'
        if last_name:
            author_obj, _ = Author.objects.get_or_create(
                first_name=first_name,
                last_name=last_name
            )
            DocumentAuthor.objects.get_or_create(
                document=doc,
                author=author_obj,
                defaults={'author_order': idx + 1}
            )

    # Link Tags
    for tag_name in meta.get('tags', []):
        tag_clean = tag_name.strip()
        if tag_clean:
            tag_obj, _ = Tag.objects.get_or_create(name=tag_clean[:100])
            DocumentTag.objects.get_or_create(document=doc, tag=tag_obj)

    # Link Domains
    for domain_name in meta.get('domains', []):
        domain_clean = domain_name.strip()
        if domain_clean:
            domain_obj, _ = Domain.objects.get_or_create(name=domain_clean[:150])
            DocumentDomain.objects.get_or_create(document=doc, domain=domain_obj)

    return True
