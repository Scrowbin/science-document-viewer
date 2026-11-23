import re
from pathlib import Path
import requests
from dotenv import load_dotenv
import os
import arxiv
from .manual_pdf_parser import auto_extract_metadata
from grobid_client.grobid_client import GrobidClient

load_dotenv()
ISBN_EXTRACTOR_API = os.getenv("GOOGLE_BOOKS_API")


def get_book_by_isbn(isbn):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"isbn:{isbn}", "key": ISBN_EXTRACTOR_API}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if "items" in data:
        book_info = data["items"][0]["volumeInfo"]
        print(f"Title: {book_info.get('title')}")
        print(f"Author(s): {', '.join(book_info.get('authors', ['Unknown']))}")
        print(f"Published Date: {book_info.get('publishedDate')}")
        print(f"Page Count: {book_info.get('pageCount')}")
    else:
        print("No book found for this ISBN.")


def arxiv_id_extractor(arxiv_id):
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    try:
        paper = next(client.results(search))
        return {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "published": paper.published.strftime("%Y-%m-%d"),
            "summary": paper.summary,
            "pdf_url": paper.pdf_url,
        }
    except StopIteration:
        print(f"Error: Paper with arXiv ID '{arxiv_id}' not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def ai_extractor_metadata(path) -> dict:
    """
    Runs GROBID on the PDF and parses the resulting TEI XML into a metadata dict.
    GrobidClient.process() requires a directory — we copy the PDF to a temp dir first.
    Returns dict with keys: title, authors, date, extra, doi, repository — or None.
    """
    import shutil
    import tempfile
    from bs4 import BeautifulSoup
    from django.conf import settings as django_settings

    document_path = Path(path)
    if not document_path.exists():
        return None

    # Pick config: local data_extractor/grobid.json or fall back to backend/grobid.json
    local_config = Path(__file__).parent / "grobid.json"
    backend_config = Path(django_settings.BASE_DIR) / "grobid.json"
    config_path = str(local_config) if local_config.exists() else str(backend_config)

    project_root = Path(django_settings.BASE_DIR).parent
    xml_store = project_root / "xml_store"
    xml_store.mkdir(exist_ok=True)

    # GrobidClient.process() needs a DIRECTORY — copy PDF into a temp dir
    with tempfile.TemporaryDirectory() as tmp_dir:
        shutil.copy2(str(document_path), os.path.join(tmp_dir, document_path.name))
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

    # Find the output XML file
    stem = document_path.stem
    xml_file = xml_store / f"{stem}.tei.xml"
    if not xml_file.exists():
        candidates = sorted(xml_store.glob(f"{stem}*.xml"))
        if candidates:
            xml_file = candidates[-1]

    if not xml_file.exists():
        return None

    # Parse TEI XML → metadata dict
    try:
        soup = BeautifulSoup(xml_file.read_text(encoding="utf-8"), "xml")

        # Title — try main title attribute first
        title = ""
        t = soup.find("title", {"level": "a", "type": "main"})
        if t:
            title = t.get_text(strip=True)
        if not title:
            t = soup.find("title")
            if t:
                title = t.get_text(strip=True)

        # Authors
        authors = []
        for author in soup.find_all("author"):
            persname = author.find("persName")
            if persname:
                forename = persname.find("forename")
                surname = persname.find("surname")
                parts = []
                if forename:
                    parts.append(forename.get_text(strip=True))
                if surname:
                    parts.append(surname.get_text(strip=True))
                name = " ".join(parts).strip()
                if name and name not in authors:
                    authors.append(name)

        # Publication date
        date_tag = soup.find("date", {"type": "published"})
        date = date_tag.get("when", "") if date_tag else ""

        # DOI
        doi_tag = soup.find("idno", {"type": "DOI"})
        doi = doi_tag.get_text(strip=True) if doi_tag else ""

        # Abstract
        abstract_tag = soup.find("abstract")
        abstract = (
            abstract_tag.get_text(separator=" ", strip=True) if abstract_tag else ""
        )

        if not title:
            return None

        return {
            "title": title,
            "short_title": title[:100],
            "authors": authors,
            "date": date,
            "doi": doi,
            "extra": abstract,
            "repository": "GROBID",
        }
    except Exception as e:
        print(f"TEI XML parsing failed: {e}")
        return None


def data_extractor(path):
    from django.conf import settings
    if getattr(settings, "USE_GROBID", False):
        # Tier 1: GROBID full-text → TEI XML → parsed metadata
        try:
            result = ai_extractor_metadata(path)
            if result and result.get("title"):
                return result
        except Exception as e:
            print(f"GROBID failed: {e}")

    # Tier 2: layout heuristic PDF parser — maps raw keys to standard schema
    try:
        raw = auto_extract_metadata(path)
        if raw and raw.get("title"):
            pages = raw.get("pages") or []
            first_page = pages[0]["text"] if pages else ""
            arxiv_id = _page_one_arxiv_id(first_page)
            doi = raw.get("doi") or ""
            year = raw.get("year")
            if arxiv_id:  # the id encodes the submission date; other years on page 1 may be citations
                year = 2000 + int(arxiv_id[:2])
            meta = {
                "title": raw.get("title", ""),
                "short_title": (raw.get("title") or "")[:100],
                "authors": raw.get("authors") or [],
                "date": str(year) if year else "",
                "doi": doi,
                "url": _best_url(raw.get("urls") or [], doi, arxiv_id),
                "extra": re.sub(r"^abstract\s*[-—:.]\s*", "", " ".join((raw.get("abstract") or "").split()), flags=re.IGNORECASE),
                "repository": "arXiv" if arxiv_id else "Local Upload",
                "tags": raw.get("keywords") or [],
            }
            return _enrich_online(meta, arxiv_id, _page_one_doi(first_page))
    except Exception as e:
        print(f"Auto extractor failed: {e}")

    return None


# ─── Online enrichment (exact record from arXiv / Crossref when page 1 names one) ───

_ARXIV_ON_PAGE_RE = re.compile(r"arXiv\s*:\s*(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE)
_DOI_ON_PAGE_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)", re.IGNORECASE)
_URL_NOISE_RE = re.compile(r"orcid\.org|creativecommons\.org|mailto:|github\.com/.+/issues|twitter\.com|x\.com/", re.IGNORECASE)


def _page_one_arxiv_id(text):
    m = _ARXIV_ON_PAGE_RE.search(text or "")
    return m.group(1) if m else None


def _page_one_doi(text):
    m = _DOI_ON_PAGE_RE.search(text or "")
    return m.group(1).rstrip(".,;:)]}") if m else None


def _best_url(urls, doi, arxiv_id):
    """A link to the paper itself, not to an author's ORCID or a licence page."""
    if doi:
        return f"https://doi.org/{doi}"
    if arxiv_id:
        return f"https://arxiv.org/abs/{arxiv_id}"
    for u in urls:
        if not _URL_NOISE_RE.search(u):
            return u
    return ""


def _title_words(t):
    return set(re.findall(r"[a-z0-9]{3,}", (t or "").lower()))


def _same_paper(local_title, online_title):
    a, b = _title_words(local_title), _title_words(online_title)
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= 0.5


def _enrich_online(meta, arxiv_id, doi):
    """Replace heuristic fields with the published record when page 1 carries an arXiv id or
    a DOI and the record's title matches the PDF's. Any network failure keeps the local result."""
    from django.conf import settings
    if not getattr(settings, "METADATA_ONLINE_LOOKUP", True) or not (arxiv_id or doi):
        return meta
    online = None
    try:
        if arxiv_id:
            from ..services.pdf_metadata_service import fetch_arxiv_metadata
            online = fetch_arxiv_metadata(arxiv_id, timeout=5)
        if not online and doi:
            from ..services.crossref_service import fetch_metadata_from_doi
            online = fetch_metadata_from_doi(doi, timeout=5)
    except Exception as e:
        print(f"Online metadata lookup failed: {e}")
        online = None
    if not online or not online.get("title") or not _same_paper(meta["title"], online["title"]):
        return meta
    merged = dict(meta)
    for key in ("title", "short_title", "authors", "date", "doi", "url", "repository", "item_type", "language"):
        if online.get(key):
            value = online[key]
            if isinstance(value, str):  # Crossref titles may carry markup: Al<sub>2</sub>O<sub>3</sub>
                value = " ".join(re.sub(r"<[^>]+>", "", value).split())
            merged[key] = value
    if online.get("extra"):
        merged["extra"] = online["extra"]
    if not merged.get("tags") and online.get("tags"):
        merged["tags"] = online["tags"]
    merged["metadata_source"] = "arXiv" if arxiv_id and online.get("repository") == "arXiv" else "Crossref"
    return merged
