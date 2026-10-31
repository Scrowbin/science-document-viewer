#!/usr/bin/env python3
"""
Download PDFs for the PeerQA external check (revalidation study, Phase B1).

PeerQA v1.0 (UKPLab; data CC BY-NC-SA 4.0, used for non-commercial research only) does not ship
PDFs. Only papers with a public PDF source are used:
  - openreview/<venue>/<id>  -> https://openreview.net/pdf?id=<id>
  - egu/<journal>/<vol>-<page>-<year> -> https://<journal>.copernicus.org/articles/<vol>/<page>/<year>/<journal>-<vol>-<page>-<year>.pdf
NLPeer papers (ARR, COLING, F1000, PeerRead) have no public PDF here and are excluded.

Only papers with >= 1 question that is answerable (authors' label) and has evidence sentences are fetched.
PDFs are local evaluation copies (eval/pdfs is git-ignored) and are not redistributed.

Writes eval/pdfs/peerqa/download_manifest.json.
"""

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import requests

ROOT = Path(__file__).resolve().parents[4]
QA = ROOT / "eval" / "data" / "peerqa" / "raw" / "qa.jsonl"
OUT_DIR = ROOT / "eval" / "pdfs" / "peerqa"
MANIFEST = OUT_DIR / "download_manifest.json"
DELAY_S = 3.0
UA = {"User-Agent": "DACNTT-thesis-research/1.0 (academic evaluation)"}


def eligible(q):
    return q.get("answerable") is True and any(e and e.strip() for e in (q.get("answer_evidence_sent") or []))


def pdf_url(paper_id):
    parts = paper_id.split("/")
    if parts[0] == "openreview":
        return f"https://openreview.net/pdf?id={parts[-1]}"
    if parts[0] == "egu":
        journal = parts[1]
        vol, page, year = parts[2].split("-")
        return f"https://{journal}.copernicus.org/articles/{vol}/{page}/{year}/{journal}-{vol}-{page}-{year}.pdf"
    return None


def safe_name(paper_id):
    return paper_id.replace("/", "__") + ".pdf"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    qa = [json.loads(line) for line in open(QA, encoding="utf-8")]
    ids = sorted({q["paper_id"] for q in qa if eligible(q) and pdf_url(q["paper_id"])})
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if MANIFEST.exists() else {"papers": {}}
    manifest["population"] = {"rule": "PeerQA v1.0 openreview/egu papers with >=1 answerable question with evidence sentences",
                              "count": len(ids)}
    for i, pid in enumerate(ids, 1):
        dest = OUT_DIR / safe_name(pid)
        if manifest["papers"].get(pid, {}).get("status") == "ok" and dest.exists():
            continue
        url = pdf_url(pid)
        rec = {"url": url, "file": dest.name, "retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        try:
            r = requests.get(url, headers=UA, timeout=60)
            rec["http"] = r.status_code
            if r.status_code == 200 and r.content.startswith(b"%PDF"):
                dest.write_bytes(r.content)
                rec.update(status="ok", bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest())
                try:
                    with pymupdf.open(dest) as doc:
                        rec["pages"] = doc.page_count
                    rec["opens_in_pymupdf"] = True
                except Exception:
                    rec["opens_in_pymupdf"] = False
            else:
                rec["status"] = "unavailable"
        except Exception as e:
            rec["status"] = f"error:{type(e).__name__}"
        manifest["papers"][pid] = rec
        time.sleep(DELAY_S)
        if i % 10 == 0 or i == len(ids):
            MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
            print(f"[{i}/{len(ids)}] ok: {sum(1 for e in manifest['papers'].values() if e.get('status') == 'ok')}", flush=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")


def register_manual():
    """
    OpenReview requires a human challenge for automated access, so its PDFs are saved by hand in a browser
    (list: eval/phases/phase_0_baseline/artifacts/peerqa_manual_download_list.tsv). This records them without any network call.
    """
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    added = 0
    for pid, rec in sorted(manifest["papers"].items()):
        dest = OUT_DIR / rec["file"]
        if rec.get("status") == "ok" or not dest.exists():
            continue
        data = dest.read_bytes()
        if not data.startswith(b"%PDF"):
            rec["manual_status"] = "not a PDF"
            continue
        rec.update(status="ok", source="manual_browser_download", bytes=len(data),
                   sha256=hashlib.sha256(data).hexdigest(),
                   registered_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        try:
            with pymupdf.open(dest) as doc:
                rec["pages"] = doc.page_count
            rec["opens_in_pymupdf"] = True
        except Exception:
            rec["opens_in_pymupdf"] = False
        added += 1
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    ok = sum(1 for e in manifest["papers"].values() if e.get("status") == "ok")
    print(f"registered {added} manual PDFs; usable now: {ok}/{len(manifest['papers'])}")


if __name__ == "__main__":
    if "--register-manual" in sys.argv:
        register_manual()
    else:
        main()
