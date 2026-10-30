"""
ResearchQA Full Dataset Downloader.

Downloads the real realliyifei/ResearchQA dataset from HuggingFace via the
Datasets Server REST API (no `datasets` library required, no auth needed).

Creates two evaluation artifacts:

1. researchqa_full_queries.json
   All answerable queries (with >=1 citation rubric item) across the requested
   splits, in our standard benchmark schema.  Citation titles are used as weak
   paper-level supervision (ground-truth paper IDs = slugified citation titles).

2. researchqa_full_corpus.json
   A "stub corpus" — one entry per unique cited paper, with the paper title as
   both abstract and section text so BM25 / TF-IDF can match query terms to
   paper entities.  This gives a *paper-retrieval* evaluation (not chunk-level
   passage retrieval) analogous to Method B.

3. researchqa_full_split.json
   HF split provenance labels: {"test": [...], "test_mini": [...], "valid": [...]}

Outputs to eval/prepared/.

Usage:
  python3 backend/scripts/data_prep/download_researchqa_full.py
  python3 backend/scripts/data_prep/download_researchqa_full.py --splits test test_mini valid
  python3 backend/scripts/data_prep/download_researchqa_full.py --splits full --max-rows 5000
"""

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
EVAL_PREP_DIR = WORKSPACE_ROOT / "eval" / "prepared"

HF_ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET = "realliyifei/ResearchQA"
PAGE_SIZE = 100  # max rows per API call


# ---------------------------------------------------------------------------
# HuggingFace Dataset Server helpers
# ---------------------------------------------------------------------------

def fetch_rows(split: str, offset: int, length: int, retries: int = 3) -> List[Dict[str, Any]]:
    """Fetch a page of rows from the HF Datasets Server API."""
    params = urllib.parse.urlencode({
        "dataset": DATASET,
        "config": "default",
        "split": split,
        "offset": offset,
        "length": length,
    })
    url = f"{HF_ROWS_API}?{params}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "science-doc-eval/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [r["row"] for r in data.get("rows", [])]
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"  [WARN] fetch failed (attempt {attempt+1}): {e} — retrying in {wait}s")
                time.sleep(wait)
            else:
                print(f"  [ERROR] fetch failed after {retries} attempts: {e}")
                return []
    return []


def fetch_all_rows(split: str, max_rows: Optional[int] = None) -> List[Dict[str, Any]]:
    """Download all rows for a given split with progress printing."""
    all_rows: List[Dict[str, Any]] = []
    offset = 0
    while True:
        remaining = (max_rows - len(all_rows)) if max_rows else PAGE_SIZE
        batch_size = min(PAGE_SIZE, remaining)
        print(f"  [{split}] Fetching rows {offset}–{offset + batch_size - 1} ...", end="\r")
        rows = fetch_rows(split, offset, batch_size)
        if not rows:
            break
        all_rows.extend(rows)
        offset += len(rows)
        if len(rows) < batch_size:
            break  # last page
        if max_rows and len(all_rows) >= max_rows:
            break
        time.sleep(0.25)  # be polite to the API
    print(f"  [{split}] Downloaded {len(all_rows)} rows.          ")
    return all_rows


# ---------------------------------------------------------------------------
# Schema conversion
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert a citation title to a stable paper ID slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text[:80]  # cap length


def extract_citation_papers(rubric: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return unique cited papers from a query's rubric (type == Citation)."""
    seen: Set[str] = set()
    papers = []
    for item in rubric:
        cm = item.get("citation_metadata")
        if not cm:
            continue
        title = cm.get("title", "").strip()
        if not title:
            continue
        slug = slugify(title)
        if slug in seen:
            continue
        seen.add(slug)
        papers.append({
            "paper_id": slug,
            "title": title,
            "first_author": cm.get("first_author", ""),
            "year": cm.get("year"),
            "url": cm.get("url", ""),
        })
    return papers


def row_to_query(row: Dict[str, Any], q_idx: int, split: str) -> Optional[Dict[str, Any]]:
    """
    Convert a ResearchQA row to our benchmark query schema.
    Returns None for rows with no citation rubric items.
    """
    cited_papers = extract_citation_papers(row.get("rubric", []))
    if not cited_papers:
        return None  # no retrievable ground truth

    rubric_items_text = [item["rubric_item"] for item in row.get("rubric", []) if item.get("rubric_item")]

    return {
        "id": f"Q_RQA_FULL_{q_idx:05d}",
        "original_id": row.get("id", ""),
        "hf_split": split,
        "general_domain": row.get("general_domain", ""),
        "subdomain": row.get("subdomain", ""),
        "field": row.get("field", ""),
        "question": row.get("query", ""),
        "question_type": "multi_paper_synthesis",
        "date": str(row.get("date", "")),
        # Ground truth: IDs of cited papers that must be retrieved
        "target_paper_ids": [p["paper_id"] for p in cited_papers],
        "cited_papers": cited_papers,
        # Rubric summary text for reference
        "rubric_summary": rubric_items_text,
        "n_rubric_items": len(row.get("rubric", [])),
        "n_citation_items": len(cited_papers),
        # Method A compatibility fields — None since we have no verbatim quotes
        "paper_arxiv_id": None,
        "verbatim_evidence_quote": None,
        "evidence_list": [],
        "label_provenance": "researchqa_hf_download",
    }


def build_corpus_entry(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a corpus entry for a cited paper using title + metadata as text.
    Since we have no full text, we use the title as a proxy — this supports
    paper-level retrieval evaluation (can BM25/TF-IDF match the right paper
    given the query?).
    """
    pid = paper["paper_id"]
    title = paper["title"]
    author = paper.get("first_author", "")
    year = paper.get("year", "")
    url = paper.get("url", "")

    # Construct a rich title-based description as the only available "text"
    description = (
        f"{title}. "
        f"{'By ' + author + '. ' if author else ''}"
        f"{'Published ' + str(year) + '.' if year else ''}"
    ).strip()

    return {
        "paper_arxiv_id": pid,
        "paper_title": title,
        "first_author": author,
        "year": year,
        "url": url,
        "abstract": description,
        "sections": [
            {
                "heading": "Title",
                "text": title,
                "page_start": 1,
                "page_end": 1,
            }
        ],
    }


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Download full ResearchQA dataset from HuggingFace.")
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["test_mini", "test", "valid"],
        choices=["test_mini", "test", "valid", "full"],
        help="HF splits to download.",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Cap rows per split (for testing). Default: all rows.",
    )
    parser.add_argument("--output-dir", type=Path, default=EVAL_PREP_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_queries: List[Dict[str, Any]] = []
    corpus: Dict[str, Dict[str, Any]] = {}
    split_map: Dict[str, List[str]] = {}
    q_idx = 0

    for split in args.splits:
        print(f"\n[INFO] Downloading split: '{split}' ...")
        rows = fetch_all_rows(split, max_rows=args.max_rows)
        print(f"[INFO] Processing {len(rows)} rows ...")

        split_query_ids: List[str] = []
        skipped = 0
        for row in rows:
            q = row_to_query(row, q_idx, split)
            if q is None:
                skipped += 1
                continue
            all_queries.append(q)
            split_query_ids.append(q["id"])
            q_idx += 1

            # Add cited papers to corpus (deduplicated)
            for paper in q["cited_papers"]:
                pid = paper["paper_id"]
                if pid not in corpus:
                    corpus[pid] = build_corpus_entry(paper)

        split_map[split] = split_query_ids
        print(f"[INFO] Split '{split}': {len(split_query_ids)} queries with citations, {skipped} skipped (no citations).")

    # Save outputs
    queries_path = args.output_dir / "researchqa_full_queries.json"
    corpus_path = args.output_dir / "researchqa_full_corpus.json"
    split_path = args.output_dir / "researchqa_full_split.json"

    with open(queries_path, "w", encoding="utf-8") as f:
        json.dump(all_queries, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Saved {len(all_queries)} queries → {queries_path}")

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {len(corpus)} unique corpus papers → {corpus_path}")

    with open(split_path, "w", encoding="utf-8") as f:
        json.dump(split_map, f, indent=2)
    print(f"[OK] Saved split map → {split_path}")

    # Summary
    print("\n" + "=" * 60)
    print("  RESEARCHQA FULL DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  Splits downloaded : {', '.join(args.splits)}")
    print(f"  Total queries     : {len(all_queries)}")
    print(f"  Unique papers     : {len(corpus)}")
    for split, qids in split_map.items():
        print(f"  {split:<12} : {len(qids)} queries")
    print("=" * 60)
    print("\nNext step:")
    print("  python3 backend/scripts/evaluation/evaluate_researchqa_full.py")


if __name__ == "__main__":
    main()
