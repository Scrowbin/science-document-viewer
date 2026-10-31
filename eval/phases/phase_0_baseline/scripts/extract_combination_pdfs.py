#!/usr/bin/env python3
"""
Extract the downloaded Dev/Test PDFs with pymupdf_layout (the extractor fixed for the combination experiment).

Reuses the extraction worker of version_check_extract.py, so records have the same format and land in the same
cache layout: eval/data/revalidation_cache/extract/<split>/latest/pymupdf_layout.jsonl. Only PDFs listed as
"ok" in eval/pdfs/<split>/download_manifest.json are extracted. Resumable (papers already cached are skipped).

Usage:  backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/extract_combination_pdfs.py [--split dev|test]
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import version_check_extract as vce  # noqa: E402

EXTRACTOR = "pymupdf_layout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], action="append")
    args = ap.parse_args()
    for split in args.split or ["dev", "test"]:
        pdf_dir = ROOT / "eval" / "pdfs" / split
        man = json.load(open(pdf_dir / "download_manifest.json", encoding="utf-8"))
        items = [(pid, pdf_dir / f"{pid}.pdf") for pid, e in sorted(man["papers"].items())
                 if e.get("status") == "ok" and (pdf_dir / f"{pid}.pdf").exists()]
        list_file = vce.CACHE / split / "latest" / "_papers.jsonl"
        list_file.parent.mkdir(parents=True, exist_ok=True)
        with open(list_file, "w", encoding="utf-8") as f:
            for pid, path in items:
                f.write(json.dumps({"paper_id": pid, "pdf": str(path)}) + "\n")
        print(f"[{split}] {EXTRACTOR}: {len(items)} papers", flush=True)
        vce.worker(EXTRACTOR, split, "latest", str(list_file))


if __name__ == "__main__":
    main()
