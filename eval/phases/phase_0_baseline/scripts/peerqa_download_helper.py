#!/usr/bin/env python3
"""
Human-in-the-loop helper for the PeerQA OpenReview PDFs (OpenReview requires a human challenge for
automated access, so the download itself is done by the user in their own browser).

For each row of reports/revalidation/peerqa_manual_download_list.tsv that is not yet saved:
  1. opens the URL in the default browser;
  2. waits until a new, finished .pdf appears in the Downloads folder (the user completes any challenge
     and the download);
  3. moves it to eval/pdfs/peerqa/<save_as>, then continues with the next row.
Already-saved papers are skipped, so the helper can be stopped (Ctrl+C) and resumed.

Tip: in Chrome/Edge set "Download PDFs" (instead of opening them in the browser) so a link downloads at once.

Usage: backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/peerqa_download_helper.py
       [--downloads "C:/Users/<you>/Downloads"] [--timeout 180]
Afterwards: download_peerqa_pdfs.py --register-manual
"""

import argparse
import csv
import shutil
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LIST = ROOT / "reports" / "revalidation" / "peerqa_manual_download_list.tsv"
DEST = ROOT / "eval" / "pdfs" / "peerqa"


def finished_pdfs(folder: Path):
    return {p for p in folder.glob("*.pdf") if p.is_file()}


def wait_for_new_pdf(folder: Path, before: set, timeout: int):
    deadline = time.time() + timeout
    while time.time() < deadline:
        new = finished_pdfs(folder) - before
        for p in sorted(new, key=lambda x: x.stat().st_mtime, reverse=True):
            size = p.stat().st_size
            time.sleep(1.0)  # make sure the browser has finished writing
            if p.exists() and p.stat().st_size == size and size > 0:
                return p
        time.sleep(1.0)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--downloads", default=str(Path.home() / "Downloads"))
    ap.add_argument("--timeout", type=int, default=180, help="seconds to wait per paper before skipping")
    args = ap.parse_args()
    downloads = Path(args.downloads)
    DEST.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(LIST, encoding="utf-8"), delimiter="\t"))
    todo = [r for r in rows if not (DEST / r["save_as (in eval/pdfs/peerqa/)"]).exists()]
    print(f"{len(rows) - len(todo)} already saved, {len(todo)} to go. Downloads folder: {downloads}")
    skipped = []
    for n, r in enumerate(todo, 1):
        target = DEST / r["save_as (in eval/pdfs/peerqa/)"]
        before = finished_pdfs(downloads)
        print(f"[{n}/{len(todo)}] {r['paper_id']} -> opening browser, waiting for the PDF...", flush=True)
        webbrowser.open(r["url"])
        got = wait_for_new_pdf(downloads, before, args.timeout)
        if got is None:
            print("   no PDF arrived in time; skipped (rerun the helper later to retry)")
            skipped.append(r["paper_id"])
            continue
        if not got.read_bytes()[:5].startswith(b"%PDF"):
            print(f"   {got.name} is not a PDF; skipped")
            skipped.append(r["paper_id"])
            continue
        shutil.move(str(got), str(target))
        print(f"   saved as {target.name}")
    print(f"done. skipped: {len(skipped)}")
    if skipped:
        print("\n".join(skipped))
    print("Next: backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/download_peerqa_pdfs.py --register-manual")


if __name__ == "__main__":
    main()
