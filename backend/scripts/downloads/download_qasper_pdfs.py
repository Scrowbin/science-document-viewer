"""
Downloader for QASPER Benchmark Physical PDFs.
Downloads 30-35 representative arXiv PDFs from the frozen QASPER evaluation sample
into eval/data/pdfs/ for physical layout extraction (Step 1) and page citation (Step 10).

Adheres strictly to arXiv rate-limiting guidelines (polite User-Agent, ~1.5s delay).
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from typing import Any, Dict, List, Tuple

import requests

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
EVAL_DIR = os.path.join(ROOT_DIR, "eval")
PDFS_DIR = os.path.join(EVAL_DIR, "data", "pdfs")
QASPER_SAMPLED_PATH = os.path.join(EVAL_DIR, "prepared", "qasper_sampled.json")

HEADERS = {
    "User-Agent": "ScientificDocRAG/1.0 (University Research IT Project; contact: student@university.edu)"
}


def download_arxiv_pdf(arxiv_id: str, dest_path: str, timeout: int = 25) -> bool:
    """Downloads a single PDF from arXiv and validates %PDF magic bytes."""
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
        with open(dest_path, "rb") as f:
            if f.read(4) == b"%PDF":
                return True

    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
            with open(dest_path, "wb") as f:
                f.write(r.content)
            return True
        else:
            print(f"  * [FAIL] arXiv:{arxiv_id} returned HTTP {r.status_code} or invalid PDF header.")
            return False
    except Exception as exc:
        print(f"  * [ERROR] Failed to download arXiv:{arxiv_id}: {exc}")
        return False


def get_top_qasper_papers(sampled_json: str, limit: int = 35) -> List[Tuple[str, str, int]]:
    """Returns top arXiv IDs from qasper_sampled.json ranked by question count."""
    with open(sampled_json, "r", encoding="utf-8") as f:
        queries = json.load(f)

    paper_titles: Dict[str, str] = {}
    paper_counts = Counter()
    for q in queries:
        aid = q.get("paper_arxiv_id")
        if aid:
            paper_counts[aid] += 1
            paper_titles[aid] = q.get("paper_title", aid)

    ranked = [(aid, paper_titles[aid], paper_counts[aid]) for aid, _ in paper_counts.most_common(limit)]
    return ranked


def main() -> None:
    parser = argparse.ArgumentParser(description="Download QASPER benchmark physical PDFs.")
    parser.add_argument(
        "--sampled-json",
        default=QASPER_SAMPLED_PATH,
        help="Path to frozen qasper_sampled.json",
    )
    parser.add_argument(
        "--dest-dir",
        default=PDFS_DIR,
        help="Destination directory for downloaded PDFs",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=35,
        help="Number of top papers to download (default: 35)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Polite delay between downloads in seconds (default: 1.5)",
    )
    args = parser.parse_args()

    os.makedirs(args.dest_dir, exist_ok=True)
    papers = get_top_qasper_papers(args.sampled_json, limit=args.count)

    print("\n" + "=" * 95)
    print(f"      QASPER PHYSICAL PDF DOWNLOADER -- TOP {len(papers)} BENCHMARK PAPERS")
    print("=" * 95)
    print(f"Destination Directory: {args.dest_dir}")
    print(f"Pacing: {args.delay}s delay between requests")
    print(f"Total Questions Covered: {sum(c for _, _, c in papers)} out of 250\n")

    successful = 0
    total_bytes = 0

    for idx, (aid, title, q_count) in enumerate(papers, 1):
        filename = f"{aid}.pdf"
        dest_path = os.path.join(args.dest_dir, filename)

        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 10000:
            sz = os.path.getsize(dest_path)
            total_bytes += sz
            successful += 1
            print(f"[{idx:02d}/{len(papers)}] [EXISTS] arXiv:{aid.ljust(12)} ({q_count} Qs) -> {title[:45]} ({sz//1024} KB)")
            continue

        print(f"[{idx:02d}/{len(papers)}] [FETCH]  arXiv:{aid.ljust(12)} ({q_count} Qs) -> {title[:45]}...", end="", flush=True)
        ok = download_arxiv_pdf(aid, dest_path)
        if ok:
            sz = os.path.getsize(dest_path)
            total_bytes += sz
            successful += 1
            print(f" OK ({sz//1024} KB)")
        else:
            print(" FAILED")

        time.sleep(args.delay)

    print("=" * 95)
    print(f"[SUMMARY] Successfully downloaded/verified {successful}/{len(papers)} PDFs.")
    print(f"  * Total Storage: {total_bytes / (1024 * 1024):.2f} MB")
    print(f"  * Questions Enabled with Physical PDFs: {sum(c for _, _, c in papers[:successful])}")
    print("=" * 95 + "\n")


if __name__ == "__main__":
    main()
