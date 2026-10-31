#!/usr/bin/env python3
"""
Freezes the revalidation protocol: appends SHA-256 hashes of the protocol documents and configs to
eval/experiment_provenance_registry.json under EXP-REVALIDATION-PROTOCOL (append-only: each call adds a
new version entry; earlier entries are never changed).

Usage: python register_protocol_hashes.py --label "pre-Gate-B" [extra files ...]
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REGISTRY = ROOT / "eval" / "experiment_provenance_registry.json"
DEFAULT_FILES = [
    "reports/revalidation/RESEARCH_VALIDITY_MATRIX.md",
    "reports/revalidation/protocol/common.json",
    "reports/revalidation/protocol/rq1_rq4.json",
    "reports/revalidation/protocol/rq5_rq6.json",
    "backend/scripts/eval_common/revalidation.py",
    "backend/scripts/eval_common/reval_pipeline.py",
    "backend/scripts/eval_common/reval_runner.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("files", nargs="*")
    a = ap.parse_args()
    files = DEFAULT_FILES + a.files
    entry = {"label": a.label, "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "files": {f: sha256(ROOT / f) for f in files}}
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    exp = reg["registered_experiments"].setdefault("EXP-REVALIDATION-PROTOCOL", {
        "experiment_id": "EXP-REVALIDATION-PROTOCOL", "phase": "REVALIDATION",
        "experiment_name": "Pre-registered revalidation protocol (hash record)", "status": "FROZEN",
        "versions": []})
    exp["versions"].append(entry)
    REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(entry, indent=1))


if __name__ == "__main__":
    main()
