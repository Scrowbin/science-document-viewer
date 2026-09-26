import re
from pypdf import PdfReader


ARXIV_RE = re.compile(
    r"""
    (?:
        arXiv\s*[:.]?\s*
    )?
    (
        \d{4}\.\d{4,5}
        (?:v\d+)?
        |
        [a-z-]+(?:\.[A-Z]{2})?/\d{7}
        (?:v\d+)?
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

DOI_RE = re.compile(
    r"""
    \b
    10\.\d{4,9}/
    [-._;()/:A-Z0-9]+
    """,
    re.IGNORECASE | re.VERBOSE,
)

URL_RE = re.compile(r"https?://[^\s<>\]\)]+", re.IGNORECASE)

YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def clean_text(text):
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_title(text):
    """
    Rough IEEE title extraction.
    Usually the title is near the beginning of page 1.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # Ignore obvious PDF/header metadata.
    lines = [
        line
        for line in lines
        if not re.match(r"^(IEEE|PROCEEDINGS|978-|DOI|arXiv)", line, re.IGNORECASE)
    ]

    for line in lines[:15]:
        # Skip obvious section headings.
        if re.match(r"^(abstract|index terms|keywords?)\b", line, re.IGNORECASE):
            continue

        # Title is usually reasonably long.
        if len(line.split()) >= 3:
            return line

    return None


def unique(items):
    """
    Preserve order while removing duplicates.
    """
    return list(dict.fromkeys(item for item in items if item))


def extract_authors(text):
    """
    Heuristic extraction of authors from the first page.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    title = extract_title(text)

    if not title:
        return []

    try:
        title_index = next(i for i, line in enumerate(lines) if line == title)
    except StopIteration:
        return []

    candidates = lines[title_index + 1 : title_index + 10]

    authors = []

    for line in candidates:
        lower = line.lower()

        # Stop at abstract.
        if "abstract" in lower or "index terms" in lower or "keywords" in lower:
            break

        # Ignore affiliation/email lines.
        if (
            "university" in lower
            or "institute" in lower
            or "department" in lower
            or "laboratory" in lower
            or "@" in line
        ):
            continue

        # Looks vaguely like an author line.
        if re.search(r"[A-Z][a-z]+.*[A-Z][a-z]+", line):
            authors.extend(split_authors(line))

    return authors


def split_authors(line):
    """
    Split common author formats:

        John Smith, Jane Doe
        John Smith and Jane Doe
        John Smith & Jane Doe
    """

    line = re.sub(r"[†‡*]+", "", line)

    parts = re.split(r",|\band\b|&", line, flags=re.IGNORECASE)

    result = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        # Remove numeric affiliation markers.
        part = re.sub(r"\d+$", "", part).strip()

        if len(part.split()) >= 2:
            result.append(part)

    return result


def extract_abstract(text):
    match = re.search(
        r"\babstract\b\s*[-—:]?\s*(.*?)(?="
        r"\bindex terms\b|"
        r"\bkeywords?\b|"
        r"\bI\.\s+INTRODUCTION\b|"
        r"\b1\.\s+INTRODUCTION\b"
        r")",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return None

    return clean_text(match.group(1))


def extract_keywords(text):
    match = re.search(
        r"(?:index terms|keywords?)\s*[-—:]?\s*(.*?)(?="
        r"\bI\.\s+INTRODUCTION\b|"
        r"\b1\.\s+INTRODUCTION\b"
        r")",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return []

    keyword_text = clean_text(match.group(1))

    return [x.strip() for x in re.split(r",|;", keyword_text) if x.strip()]


SECTION_RE = re.compile(
    r"^(?:"
    r"[IVXLCDM]+\.\s+.+|"
    r"\d+\.\s+.+|"
    r"[IVXLCDM]+\s+.+"
    r")$",
    re.IGNORECASE,
)


def extract_arxiv_id(text):
    matches = ARXIV_RE.findall(text)

    if not matches:
        return None

    # Normalize "ARXIV:1234.5678" -> "1234.5678"
    return matches[0]


def extract_doi(text):
    matches = DOI_RE.findall(text)

    if not matches:
        return None

    doi = matches[0]

    # PDF extraction often leaves punctuation after the DOI.
    doi = doi.rstrip(".,;:)]}")

    return doi


def extract_urls(text):
    urls = URL_RE.findall(text)

    cleaned = []

    for url in urls:
        url = url.rstrip(".,;:)]}")

        if url not in cleaned:
            cleaned.append(url)

    return cleaned


def extract_year(text):
    years = YEAR_RE.findall(text)

    if not years:
        return None

    # Prefer a year appearing near publication metadata.
    for year in years:
        context_match = re.search(rf".{{0,100}}{year}.{{0,100}}", text, re.IGNORECASE)

        if context_match:
            return int(year)

    return int(years[0])


def is_section_heading(line):
    line = line.strip()

    if not line:
        return False

    if re.match(r"^(REFERENCES|BIBLIOGRAPHY)$", line, re.IGNORECASE):
        return True

    return bool(SECTION_RE.match(line))


def extract_sections(text):
    lines = text.splitlines()

    sections = []
    current = None

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # References are separate.
        if re.match(r"^(REFERENCES|BIBLIOGRAPHY)$", line, re.IGNORECASE):
            break

        if is_section_heading(line):
            if current:
                current["text"] = clean_text(current["text"])
                sections.append(current)

            current = {"title": line, "text": ""}

        elif current:
            current["text"] += " " + line

    if current:
        current["text"] = clean_text(current["text"])
        sections.append(current)

    return sections


def extract_references(text):
    match = re.search(r"\bREFERENCES\b(.*)$", text, re.IGNORECASE | re.DOTALL)

    if not match:
        return []

    reference_text = match.group(1)

    # IEEE references normally start with [1], [2], ...
    references = re.split(r"\n(?=\s*\[\d+\])", reference_text)

    return [clean_text(ref) for ref in references if clean_text(ref)]


def auto_extract_metadata(path):
    reader = PdfReader(path)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append(
            {
                "page_number": page_number,
                "text": clean_text(text),
            }
        )

    raw_text = "\n\n".join(page["text"] for page in pages if page["text"])

    first_page_text = pages[0]["text"] if pages else ""

    metadata = dict(reader.metadata or {})

    return {
        # Bibliographic metadata
        "title": extract_title(first_page_text),
        "authors": extract_authors(first_page_text),
        "abstract": extract_abstract(raw_text),
        "keywords": extract_keywords(raw_text),
        "year": extract_year(first_page_text),
        # Identifiers
        "doi": extract_doi(raw_text),
        "arxiv_id": extract_arxiv_id(raw_text),
        "urls": extract_urls(raw_text),
        # Content
        "sections": extract_sections(raw_text),
        "references": extract_references(raw_text),
        # Raw/debug information
        "pages": pages,
        "metadata": metadata,
        "raw_text": raw_text,
    }
