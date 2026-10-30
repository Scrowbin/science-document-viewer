"""
Downloader for QASPER 48-Paper Dev Split Physical PDFs (Workstream 2).
Downloads all 48 Dev arXiv PDFs into eval/pdfs/dev/ for full-corpus
extraction benchmarking, CER measurement, and heading recall evaluation.

Reuses any matching PDFs already present in eval/data/pdfs/ to minimize network overhead,
and adheres to polite arXiv rate limits (1.5s delay, academic user agent).
"""

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Set

import requests

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEV_SPLIT_PATH = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
DEV_PDF_DIR = WORKSPACE_ROOT / "eval" / "pdfs" / "dev"
EXISTING_PDF_DIR = WORKSPACE_ROOT / "eval" / "data" / "pdfs"

HEADERS = {
    "User-Agent": "ScientificDocViewerBot/1.0 (academic research; contact: eval@science-viewer.edu)"
}


def download_single_arxiv_pdf(arxiv_id: str, dest_path: Path, timeout: int = 30) -> bool:
    """Downloads an arXiv PDF with %PDF magic byte verification and caching."""
    # 1. Check if already downloaded and valid
    if dest_path.exists() and dest_path.stat().st_size > 10000:
        with open(dest_path, "rb") as f:
            if f.read(4) == b"%PDF":
                return True

    # 2. Check if present in existing PDFs directory
    existing_src = EXISTING_PDF_DIR / f"{arxiv_id}.pdf"
    if existing_src.exists() and existing_src.stat().st_size > 10000:
        with open(existing_src, "rb") as f:
            if f.read(4) == b"%PDF":
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(existing_src, dest_path)
                print(f"  [COPIED] {arxiv_id}.pdf copied from existing dataset cache.")
                return True

    # 3. Download from arXiv
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            with open(dest_path, "wb") as f:
                f.write(r.content)
            print(f"  [DOWNLOADED] {arxiv_id}.pdf ({len(r.content):,} bytes) from {url}")
            return True
        else:
            print(f"  [FAIL] {arxiv_id}: HTTP {r.status_code} or invalid PDF magic bytes.")
            return False
    except Exception as exc:
        print(f"  [ERROR] {arxiv_id}: Exception during fetch: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download 48 Dev Split arXiv PDFs")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on papers to fetch")
    parser.add_argument("--delay", type=float, default=1.5, help="Polite delay in seconds between downloads")
    args = parser.parse_args()

    if not DEV_SPLIT_PATH.exists():
        print(f"[ERROR] dev_held_out_split.json not found at: {DEV_SPLIT_PATH}")
        sys.exit(1)

    with open(DEV_SPLIT_PATH, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    dev_papers: List[str] = split_data.get("dev_papers", [])
    if args.limit:
        dev_papers = dev_papers[: args.limit]

    print(f"=== DOWNLOADING 48 DEV ARXIV PDFS ===")
    print(f"Destination: {DEV_PDF_DIR}")
    print(f"Total Dev Papers to process: {len(dev_papers)}\n")

    success_count = 0
    cached_count = 0

    for idx, aid in enumerate(dev_papers, start=1):
        target_path = DEV_PDF_DIR / f"{aid}.pdf"
        already_valid = target_path.exists() and target_path.stat().st_size > 10000

        print(f"[{idx}/{len(dev_papers)}] arXiv:{aid}...", end="", flush=True)
        ok = download_single_arxiv_pdf(aid, target_path)
        if ok:
            success_count += 1
            if already_valid:
                cached_count += 1
                print(" OK (Cached)")
            else:
                time.sleep(args.delay)
        else:
            print(" FAILED")

    print("\n=== DOWNLOAD SUMMARY ===")
    print(f"Total Papers: {len(dev_papers)}")
    print(f"Successfully Available: {success_count}/{len(dev_papers)}")
    print(f"Pre-cached / Reused: {cached_count}")
    print(f"New Downloads: {success_count - cached_count}")


if __name__ == "__main__":
    main()
