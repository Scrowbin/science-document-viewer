import re
import unicodedata
import pymupdf
from pathlib import Path


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

YEAR_RE = re.compile(r"(?<![.\d])\b(?:19|20)\d{2}\b(?!\.\d)")  # not 1912 from arXiv:1912.01234


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
        r"\b(?:I|1)\.?\s+INTRODUCTION\b|"
        r"$"
        r")",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return []

    # The lazy match runs up to the Introduction heading, which on cover-page layouts
    # (e.g. Research Square preprints) swallows the abstract. Keep only the keyword block:
    # stop at a blank line or at the next metadata label.
    block = re.split(
        # "abstract"/"introduction" only as headings, so "abstract interpretation" survives
        r"\n\s*\n|\b(?:posted date|doi|license)\b|(?:^|\n)\s*(?:\d+\.?|[IVX]+\.)?\s*"
        r"(?:abstract|introduction)\b|\b(?:abstract|introduction)\s*[:.\u2014-]",
        match.group(1),
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    keyword_text = clean_text(block)

    keywords = []
    for x in re.split(r",|;|·|•", keyword_text):
        kw = " ".join(x.split()).strip(" .")
        # A keyword is a short phrase; longer pieces are body text that leaked in.
        if kw and len(kw) <= 60 and len(kw.split()) <= 6 and kw not in keywords:
            keywords.append(kw)
    return keywords[:10]


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


# ─── Layout-based title/author detection (font size + position on page 1) ─────────

# Lines that sit in the title area but are never the title.
_TITLE_JUNK_RE = re.compile(
    r"^(noname manuscript|\(will be inserted|preprint|accepted|published|proceedings|journal of|"
    r"vol\.|volume\b|research article|original (research )?article|review article|article\b|"
    r"contents lists available|available online|received\b|arxiv|doi\b|https?://|www\.|"
    r"©|copyright|page \d|\d+$|under review|draft\b|technical report|\(?dated\b|supplementary\b)",
    re.IGNORECASE,
)

_AFFILIATION_RE = re.compile(
    r"universit|univ\.|institut|department|dept\.?\b|school\b|college|laborator|\blab\b|faculty|"
    r"\bcent(er|re)\b|academy|hospital|foundation|corporation|\binc\b|\bltd\b|\bgmbh\b|research\b|"
    r"\bteam\b|google|microsoft|facebook|\bmeta\b|amazon|ibm\b|nvidia|deepmind|openai|alibaba|tencent|"
    r"baidu|huawei|samsung|street|road\b|avenue|\bp\.?o\.? box|email|e-mail|correspond|equal contribution|"
    r"@|https?://|www\.|\b\d{4,6}\b|\blabs?\b|scien|preprint|scholar|\bgroup\b|\bai\b|\btech|insti|consult|"
    r"engine|system|republic|\bchina\b|\busa\b|\bindia\b|\bjapan\b|\bkorea\b|\bgermany\b|\bfrance\b|"
    r"\bitaly\b|\bspain\b|\bcanada\b|\bafrica\b|\bunited\b|\bkingdom\b|politecnico|dipartimento|"
    r"\buniv|\bcampus\b|\bcity\b|\bstate\b|compan|\bsolutions\b|technolog|\bdivision\b|\bprogram",
    re.IGNORECASE,
)

_NAME_PARTICLES = {"de", "da", "di", "del", "della", "der", "den", "van", "von", "le", "la", "du",
                   "dos", "das", "bin", "al", "ibn", "y", "e", "ten", "ter", "zu"}

_MARKER_CHARS = "∗*†‡§¶♦♠♣♥♮⋆★☆✝‖#⊥⊤∓±°·•"

# LaTeX PDFs often store accented letters as a spacing accent next to the base letter
# ("Gr¨onroos", "Bok´anyi"); recombine them so names stay whole.
_SPACING_ACCENTS = {"¨": "̈", "´": "́", "`": "̀", "ˆ": "̂", "˜": "̃",
                    "¸": "̧", "ˇ": "̌", "˚": "̊", "˘": "̆", "˝": "̋"}
_ACCENT_RE = re.compile("([" + "".join(_SPACING_ACCENTS) + r"])\s?([A-Za-zıȷ])")


def _fix_accents(text):
    def comb(m):
        base = {"ı": "i", "ȷ": "j"}.get(m.group(2), m.group(2))
        return unicodedata.normalize("NFC", base + _SPACING_ACCENTS[m.group(1)])
    text = _ACCENT_RE.sub(comb, text)
    # Typographic ligatures (ﬁ, ﬂ, ﬀ, ...) as plain letters.
    return re.sub("[ﬀ-ﬆ]", lambda m: unicodedata.normalize("NFKC", m.group(0)), text)


def _is_accent_only(text):
    return all(ch in _SPACING_ACCENTS or unicodedata.combining(ch) for ch in text.strip())


def _page_lines(page):
    """Horizontal text lines of a page with their main font size; superscript spans
    (affiliation markers, footnote symbols) are dropped from the text."""
    lines = []
    data = page.get_text("dict")
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            dx, dy = line.get("dir", (1, 0))
            if abs(dy) > 0.1 or dx <= 0:  # vertical margin stamps (e.g. the arXiv id)
                continue
            spans = [s for s in line.get("spans", []) if s.get("text", "").strip()]
            if not spans:
                continue
            main_span = max(spans, key=lambda s: len(s["text"].strip()))
            main = main_span["size"]
            baseline = main_span.get("origin", (0, main_span["bbox"][3]))[1]
            kept = []
            prev_x1 = None
            for s in spans:
                accent = _is_accent_only(s["text"])
                # Superscript = smaller AND raised (affiliation/footnote markers). Smaller text on
                # or below the baseline is small caps or a subscript (Al2O3) and is kept.
                raised = baseline - s.get("origin", (0, s["bbox"][3]))[1] > main * 0.15
                is_super = not accent and ((s.get("flags", 0) & 1) or (s["size"] < main * 0.8 and raised))
                # Some PDFs put each word in its own span without a space character:
                # a horizontal gap between spans is a word break.
                if prev_x1 is not None and not accent and s["bbox"][0] - prev_x1 > main * 0.15:
                    kept.append(" ")
                kept.append(" " if is_super else s["text"])  # a marker between names still separates them
                prev_x1 = s["bbox"][2]
            text = _fix_accents(" ".join("".join(kept).split()))
            if not text:
                continue
            x0, y0, x1, y1 = line["bbox"]
            lines.append({"text": text, "size": round(main, 1), "x0": x0, "y0": y0, "y1": y1,
                          "bold": any(s.get("flags", 0) & 16 for s in spans)})
    lines.sort(key=lambda ln: (round(ln["y0"]), ln["x0"]))
    return lines


def _smart_title_case(text, acronyms=frozenset()):
    """Title Case for ALL-CAPS titles (ICLR/IEEE templates). A short name before a colon
    ("LORA:", "SGDA") is most likely an acronym and keeps its capitals, as does any word
    in `acronyms` (written in capitals in the page's mixed-case text, e.g. "BERT")."""
    if not text.isupper():
        return text
    small = {"a", "an", "the", "and", "or", "of", "for", "in", "on", "to", "with", "by", "at", "via", "from", "vs"}
    out = []
    after_colon = True  # the first word, and the first word after a colon, are capitalised
    for i, word in enumerate(text.split()):
        starts_phrase, after_colon = after_colon, word.endswith(":")
        if word.endswith(":") and len(word) <= 9 and i < 3:
            out.append(word)
            continue
        core = word.strip(".,:;?!()[]\"'")
        if core and core in acronyms:
            out.append(word)
            continue
        low = word.lower()
        if not starts_phrase and low in small:
            out.append(low)
            continue
        out.append("-".join(p[:1].upper() + p[1:] for p in low.split("-")))
    return " ".join(out)


# Prefixes whose line-end hyphen is a real compound hyphen ("Pre-" + "trained").
_HYPHEN_PREFIXES = {"pre", "post", "multi", "non", "self", "cross", "co", "semi", "sub", "anti", "inter",
                    "end", "low", "high", "large", "small", "zero", "few", "one", "open", "fine", "long",
                    "short", "data", "task", "domain", "language", "model", "real", "state", "deep", "meta"}


def _join_title_lines(parts):
    title = ""
    for part in parts:
        if not title:
            title = part
            continue
        m = re.search(r"([A-Za-z]+)-$", title)
        if m and m.group(1).lower() not in _HYPHEN_PREFIXES and part[:1].isalpha():
            title = title[:-1] + part  # hyphenation at a line break: "Lan-" + "guage"
        elif title.endswith("-"):
            title += part
        else:
            title += " " + part
    return title


def _page_acronyms(lines):
    """Capitalised tokens ("BERT", "GPT-4") found in the page's mixed-case lines."""
    found = set()
    for ln in lines:
        if any(c.islower() for c in ln["text"]):
            found.update(re.findall(r"\b[A-Z][A-Z0-9]*[A-Z][A-Z0-9-]*\b", ln["text"]))
    return found


def _layout_title(lines, page_height):
    """Largest-font text block in the upper part of the page, with its wrapped lines merged.
    Returns (title, title_size, index of the last title line) or (None, None, -1)."""
    top = [i for i, ln in enumerate(lines) if ln["y0"] < page_height * 0.6]
    sizes = sorted({lines[i]["size"] for i in top}, reverse=True)
    for size in sizes[:4]:
        idx = [i for i in top if abs(lines[i]["size"] - size) <= 0.6 and not _TITLE_JUNK_RE.match(lines[i]["text"])]
        if not idx:
            continue
        # Merge the first run of vertically adjacent lines at this size.
        run = [idx[0]]
        for i in idx[1:]:
            prev = lines[run[-1]]
            if lines[i]["bold"] != prev["bold"]:  # e.g. IEEE: bold title, regular authors at the same size
                break
            if lines[i]["y0"] - prev["y1"] <= size * 1.2:
                run.append(i)
            elif lines[i]["y0"] - prev["y0"] < 1:  # same baseline, another span block
                run.append(i)
            else:
                break
        title = _join_title_lines([lines[i]["text"] for i in run])
        title = re.sub(r"\s+([:?.,])", r"\1", title).strip(" .")
        title = re.sub(r"^title\s*:\s*", "", title, flags=re.IGNORECASE)
        words = re.findall(r"[A-Za-z]{2,}", title)
        if len(words) >= 2 and 10 <= len(title) <= 300:
            return _smart_title_case(title, _page_acronyms(lines)), size, run[-1]
    return None, None, -1


def _clean_author_name(name):
    name = name.translate({ord(c): " " for c in _MARKER_CHARS})
    name = re.sub(r"\d+", " ", name)
    name = re.sub(r"\s*,\s*$", "", name)
    name = " ".join(name.split()).strip(" ,;.-")
    return name


def _looks_like_name(name):
    tokens = name.split()
    if not 2 <= len(tokens) <= 5 or len(name) > 60:
        return False
    if re.match(r"^[IVX]{1,4}\.$", tokens[0]) and len(tokens[0]) > 2:  # section number "II. Methods"
        return False
    for t in tokens:
        if t.lower() in _NAME_PARTICLES:
            continue
        # Capitalised word, initial ("J." / "J.-P."), or hyphenated/apostrophe name part.
        if not re.match(r"^[A-ZÀ-ɏḀ-ỿ][\wÀ-ɏḀ-ỿ'’.\-]*$", t):
            return False
    if all(len(t.strip(".")) <= 1 for t in tokens):
        return False
    return True


def _layout_authors(lines, title_end, title_size):
    """Author names between the title and the abstract, without affiliation lines."""
    authors = []
    for ln in lines[title_end + 1:]:
        text = ln["text"]
        if re.match(r"^(abstract|a b s t r a c t|summary|keywords?|index terms|introduction|1\s*\.?\s*introduction)\b",
                     text, re.IGNORECASE):
            break
        if title_size and ln["size"] > title_size + 0.3:
            continue
        words = text.split()
        lower = [w for w in words if w[:1].islower() and w.lower() not in _NAME_PARTICLES and w != "and"]
        if len(words) > 12 and len(lower) > 0.3 * len(words):  # running text: the abstract started unlabelled
            break
        if _AFFILIATION_RE.search(text):
            continue
        for part in re.split(r",|;|\band\b|&|·|\s{2,}|\|", text):
            name = _clean_author_name(part)
            if name and _looks_like_name(name) and name not in authors:
                authors.append(name)
        if len(authors) >= 40:
            break
    return authors


def layout_title_authors(page):
    lines = _page_lines(page)
    if not lines:
        return None, []
    title, size, end = _layout_title(lines, page.rect.height)
    if not title:
        return None, []
    return title, _layout_authors(lines, end, size)


def _plausible_metadata_title(meta_title):
    t = (meta_title or "").strip()
    if len(re.findall(r"[A-Za-z]{2,}", t)) < 3 or len(t) > 300:
        return None
    if " " not in t or re.search(r"microsoft word|\.[a-z0-9]{2,4}$|untitled|^template|^slide", t, re.IGNORECASE):
        return None
    return t


def auto_extract_metadata(path):
    try:
        doc = pymupdf.open(str(path))
    except Exception:
        return None

    pages = []
    try:
        for page_number in range(1, len(doc) + 1):
            page = doc[page_number - 1]
            text = page.get_text() or ""
            pages.append(
                {
                    "page_number": page_number,
                    "text": clean_text(text),
                }
            )
        raw_text = "\n\n".join(page["text"] for page in pages if page["text"])
        first_page_text = pages[0]["text"] if pages else ""
        metadata = dict(doc.metadata or {})
        layout_title, layout_authors = (None, [])
        if len(doc) > 0:
            try:
                layout_title, layout_authors = layout_title_authors(doc[0])
            except Exception:
                layout_title, layout_authors = (None, [])
    finally:
        doc.close()

    # Layout (font size/position) first; then the PDF's own Title field; then plain text.
    title = layout_title or _plausible_metadata_title(metadata.get("title")) or extract_title(first_page_text)
    authors = layout_authors if layout_title else extract_authors(first_page_text)
    if not authors and metadata.get("author"):
        authors = [a for a in (_clean_author_name(x) for x in re.split(r",|;|\band\b", metadata["author"])) if _looks_like_name(a)]

    return {
        # Bibliographic metadata
        "title": title,
        "authors": authors,
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
