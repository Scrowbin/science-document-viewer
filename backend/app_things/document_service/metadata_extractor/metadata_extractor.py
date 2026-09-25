from json import load
import requests
from dotenv import load_dotenv
import os
import arxiv
from manual_extractor_utils import auto_extract_metadata
from grobid_client.grobid_client import GrobidClient

load_dotenv()
ISBN_EXTRACTOR_API = os.getenv("GOOGLE_BOOKS_API")


def get_book_by_isbn(isbn):
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"isbn:{isbn}", "key": ISBN_EXTRACTOR_API}

    response = requests.get(url, params=params)

    # Raise an exception if the API call fails
    response.raise_for_status()

    data = response.json()

    # The API returns results inside an "items" array
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
        # client.results() returns a generator. next() grabs the first result.
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


def ai_extractor_metadata(path):
    client = GrobidClient(config_path="./grobid.json")
    output_dir = path.parent / "grobid_output"
    output_dir.mkdir(exist_ok=True)

    client.process(
        service="processFulltextDocument",
        input_path=str(path),
        output_path=str(output_dir),
        # Metadata
        consolidate_header=True,
        # References
        consolidate_citations=True,
        include_raw_citations=True,
        # Useful for RAG
        segment_sentences=True,
        # Generate Markdown
        markdown_output=True,
        # Keep TEI around as the rich source
        force=True,
    )

    markdown_path = output_dir / f"{path.stem}.md"
    tei_path = output_dir / f"{path.stem}.tei.xml"

    return {
        "markdown": markdown_path.read_text(encoding="utf-8"),
        "markdown_path": markdown_path,
        "tei_path": tei_path,
    }
