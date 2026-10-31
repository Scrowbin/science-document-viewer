#!/usr/bin/env python3
"""
Chunk invariance fingerprint: SHA-256 of every unit's retrieval-relevant fields (text, child_text, parent_text,
char offsets, parent_id) for the 3 production chunkers on C-RET (pymupdf_layout sections).
Used to prove that app changes (e.g. citation location metadata) leave retrieval text unchanged.

Usage: python chunk_invariance_fingerprint.py --label before|after
Output: eval/phases/phase_2_chunking/artifacts/chunk_invariance/<label>.json ; with two files present, prints the diff.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
from apps.documents.services.chunking_utils import extract_sections_from_pdf  # noqa: E402

OUT = ROOT / "eval" / "phases" / "phase_2_chunking" / "artifacts" / "chunk_invariance"
FIELDS = ["text", "child_text", "parent_text", "parent_id", "char_start", "char_end", "section"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    groups = rr.group_items(rr.load_cohort("C-RET"))
    res = {}
    for pid in sorted(groups):
        secs = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, groups[pid][0]["pdf_version"])))
        sec_h = hashlib.sha256(json.dumps([[s.get("title"), s.get("text")] for s in secs], ensure_ascii=False).encode()).hexdigest()
        res[pid] = {"sections": sec_h}
        for st in ["hierarchical", "section_overlap", "fixed_size"]:
            units = rp.build_units(secs, st, pid)
            payload = [[u.get(f) for f in FIELDS] for u in units]
            res[pid][st] = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()
    (OUT / f"{a.label}.json").write_text(json.dumps(res, indent=0), encoding="utf-8")
    other = OUT / ("before.json" if a.label != "before" else "after.json")
    if other.exists() and a.label != "before":
        prev = json.load(open(other, encoding="utf-8"))
        diff = [(p, k) for p in res for k in res[p] if prev.get(p, {}).get(k) != res[p][k]]
        print(f"papers {len(res)}; differing entries: {len(diff)}", diff[:10])
    else:
        print(f"papers {len(res)} fingerprinted")


if __name__ == "__main__":
    main()
