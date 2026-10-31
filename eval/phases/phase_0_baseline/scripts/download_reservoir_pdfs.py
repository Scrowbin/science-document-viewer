#!/usr/bin/env python3
"""
Download arXiv PDFs for the unused QASPER Train reservoir (revalidation study, Phase B1).

Population: official QASPER v0.3 Train papers with no exposure event in
eval/experiment_provenance_registry.json and at least one retrieval-eligible question
(>= 1 non-unanswerable annotation with non-FLOAT text evidence, the RQ4 rule).

For each paper: try https://arxiv.org/pdf/<id> (latest), and also https://arxiv.org/pdf/<id>v1
so the version check can pick the version that matches QASPER's evidence. Files are saved to
eval/pdfs/train_reservoir/<id>.pdf and <id>v1.pdf. Polite: ~3 s between requests, resumable.

Writes eval/pdfs/train_reservoir/download_manifest.json (status, bytes, sha256, opens_in_pymupdf).

Usage:  backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/download_reservoir_pdfs.py
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pymupdf
import requests

ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = ROOT / "eval" / "pdfs" / "train_reservoir"
MANIFEST = OUT_DIR / "download_manifest.json"
REGISTRY = ROOT / "eval" / "experiment_provenance_registry.json"
TRAIN = ROOT / "eval" / "data" / "qasper_official" / "qasper-train-v0.3.json"
DELAY_S = 3.0
UA = {"User-Agent": "DACNTT-thesis-research/1.0 (academic evaluation; polite bulk download)"}


def rq4_eligible(qa):
    for ann in qa.get("answers", []):
        a = ann.get("answer", {})
        if not a.get("unanswerable", False) and any(
            (not ev.startswith("FLOAT SELECTED")) and ev.strip() for ev in a.get("evidence", [])
        ):
            return True
    return False


def reservoir_ids():
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    train = json.load(open(TRAIN, encoding="utf-8"))
    ids = []
    for pid, pdata in train.items():
        rec = reg["paper_index"].get(pid)
        if rec is None or rec.get("exposure_events"):
            continue
        if any(rq4_eligible(q) for q in pdata.get("qas", [])):
            ids.append(pid)
    return sorted(ids)


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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.load(open(MANIFEST, encoding="utf-8")) if MANIFEST.exists() else {"papers": {}}
    ids = reservoir_ids()
    manifest["population"] = {"rule": "QASPER v0.3 Train, no registry exposure event, >=1 RQ4-eligible question",
                              "count": len(ids)}
    for i, pid in enumerate(ids, 1):
        entry = manifest["papers"].setdefault(pid, {})
        for key, url, dest in (("latest", f"https://arxiv.org/pdf/{pid}", OUT_DIR / f"{pid}.pdf"),
                               ("v1", f"https://arxiv.org/pdf/{pid}v1", OUT_DIR / f"{pid}v1.pdf")):
            if entry.get(key, {}).get("status") == "ok" and dest.exists():
                continue
            entry[key] = fetch(url, dest)
            entry[key]["retrieved_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            time.sleep(DELAY_S)
        if i % 10 == 0 or i == len(ids):
            MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
            ok = sum(1 for e in manifest["papers"].values() if e.get("latest", {}).get("status") == "ok")
            print(f"[{i}/{len(ids)}] latest ok so far: {ok}", flush=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
