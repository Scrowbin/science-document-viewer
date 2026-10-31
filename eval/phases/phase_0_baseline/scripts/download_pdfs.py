#!/usr/bin/env python3
"""
Download the latest arXiv PDF of QASPER v0.3 Dev and Test papers for the combination experiment.

Rule: latest version only (https://arxiv.org/pdf/<id>), no v1 fallback. A paper is fetched only if it has
at least one answerable question with text (non-figure) evidence, since only those can be evaluated.
Files already present in eval/pdfs/<split>/<id>.pdf are kept. Polite: ~3 s between requests, resumable.
Writes eval/pdfs/<split>/download_manifest.json (url, http status, bytes, sha256, opens in PyMuPDF).

Usage:  backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/download_pdfs.py [--split dev|test]
"""

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import requests

ROOT = Path(__file__).resolve().parents[4]
QASPER = ROOT / "eval" / "data" / "qasper_official"
DELAY_S = 3.0
UA = {"User-Agent": "DACNTT-thesis-research/1.0 (academic evaluation; polite bulk download)"}


def has_text_evidence_question(paper):
    for qa in paper.get("qas", []):
        for ann in qa.get("answers", []):
            a = ann.get("answer", {})
            if not a.get("unanswerable", False) and any(
                    ev.strip() and not ev.startswith("FLOAT SELECTED") for ev in a.get("evidence", [])):
                return True
    return False


def fetch(url, dest):
    try:
        r = requests.get(url, headers=UA, timeout=60)
    except Exception as e:  # network error
        return {"url": url, "status": f"error:{type(e).__name__}"}
    rec = {"url": url, "http": r.status_code}
    if r.status_code != 200 or not r.content.startswith(b"%PDF"):
        rec["status"] = "unavailable"
        return rec
    dest.write_bytes(r.content)
    rec.update(status="ok", bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest())
    try:
        with pymupdf.open(dest) as doc:
            rec["pages"] = doc.page_count
        rec["opens_in_pymupdf"] = True
    except Exception:
        rec["opens_in_pymupdf"] = False
    return rec


def download_split(split):
    out_dir = ROOT / "eval" / "pdfs" / split
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "download_manifest.json"
    manifest = json.load(open(manifest_path, encoding="utf-8")) if manifest_path.exists() else {"papers": {}}
    data = json.load(open(QASPER / f"qasper-{split}-v0.3.json", encoding="utf-8"))
    ids = sorted(pid for pid, p in data.items() if has_text_evidence_question(p))
    manifest["population"] = {"rule": f"QASPER v0.3 {split}, >=1 answerable question with text evidence; "
                                      "latest arXiv PDF only", "count": len(ids)}
    for i, pid in enumerate(ids, 1):
        dest = out_dir / f"{pid}.pdf"
        entry = manifest["papers"].get(pid, {})
        if dest.exists() and entry.get("status") != "unavailable":
            if not entry:
                entry = {"status": "ok", "source": "already present",
                         "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
                manifest["papers"][pid] = entry
            continue
        if entry.get("status") == "unavailable":
            continue
        entry = fetch(f"https://arxiv.org/pdf/{pid}", dest)
        entry["retrieved_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        manifest["papers"][pid] = entry
        time.sleep(DELAY_S)
        if i % 10 == 0:
            manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
            ok = sum(1 for e in manifest["papers"].values() if e.get("status") == "ok")
            print(f"[{split} {i}/{len(ids)}] ok so far: {ok}", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    ok = sum(1 for e in manifest["papers"].values() if e.get("status") == "ok")
    print(f"{split}: {ok}/{len(ids)} PDFs available", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], action="append")
    args = ap.parse_args()
    for split in args.split or ["dev", "test"]:
        download_split(split)


if __name__ == "__main__":
    main()
