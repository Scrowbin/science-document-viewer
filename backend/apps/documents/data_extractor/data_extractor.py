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

    # Tier 2: heuristic PDF parser — maps raw keys to standard schema
    try:
        raw = auto_extract_metadata(path)
        if raw and raw.get("title"):
            year = raw.get("year")
            urls = raw.get("urls") or []
            return {
                "title": raw.get("title", ""),
                "short_title": (raw.get("title") or "")[:100],
                "authors": raw.get("authors") or [],
                "date": str(year) if year else "",
                "doi": raw.get("doi") or "",
                "url": urls[0] if urls else "",
                "extra": raw.get("abstract") or "",
                "repository": "Local Upload",
                "tags": raw.get("keywords") or [],
            }
    except Exception as e:
        print(f"Auto extractor failed: {e}")

    return None
