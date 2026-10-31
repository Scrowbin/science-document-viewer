#!/usr/bin/env python3
"""
Version check + extraction cache for the revalidation study (Phase B1).

For every downloaded PDF, runs each RQ1 extractor in its own subprocess (one subprocess per extractor,
so memory is attributable), caches the extracted blocks, and records per-paper latency. Then, for each
paper, computes the share of its evidence paragraphs found in each extractor's text
(eval_common.revalidation.evidence_match_rate: >= 80% content-word containment or verbatim).

Version rule (pre-registered): QASPER evidence comes from one paper version. If the latest arXiv PDF
matches < 70% of the evidence under EVERY extractor, the v1 PDF is extracted too and the version with
the higher best-extractor match rate is kept. A paper is KEPT if ANY extractor reaches >= 70% on the
kept version (so the filter does not favour one extractor). Per-extractor match rates are stored but are
not analysed before Gate B (they overlap with the RQ1 primary metric).

Outputs:
  eval/data/revalidation_cache/extract/<set>/<version>/<extractor>.jsonl   (git-ignored cache)
  eval/phases/phase_0_baseline/artifacts/revalidation/version_check_<set>.json

Usage:
  python version_check_extract.py --set reservoir
  python version_check_extract.py --set peerqa
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
CACHE = ROOT / "eval" / "data" / "revalidation_cache" / "extract"
ART = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "revalidation"
EXTRACTORS = ["pymupdf_plain", "pymupdf_layout", "pypdf", "pdfminer.six", "pdfplumber"]
KEEP_THRESHOLD = 0.70

sys.path.insert(0, str(BACKEND / "scripts"))


# ----------------------------------------------------------------------------- inputs
def load_set(name):
    """Returns {paper_id: {"pdf": {version: path}, "evidence": [..]}} for downloaded, openable PDFs."""
    from eval_common.revalidation import peerqa_evidence, qasper_text_evidence
    papers = {}
    if name == "reservoir":
        pdf_dir = ROOT / "eval" / "pdfs" / "train_reservoir"
        man = json.load(open(pdf_dir / "download_manifest.json", encoding="utf-8"))
        train = json.load(open(ROOT / "eval" / "data" / "qasper_official" / "qasper-train-v0.3.json", encoding="utf-8"))
        for pid, e in sorted(man["papers"].items()):
            versions = {}
            for v, fname in (("latest", f"{pid}.pdf"), ("v1", f"{pid}v1.pdf")):
                if e.get(v, {}).get("status") == "ok" and e[v].get("opens_in_pymupdf") and e[v].get("bytes", 0) > 10000:
                    versions[v] = pdf_dir / fname
            ev = []
            for qa in train[pid]["qas"]:
                for p in qasper_text_evidence(qa):
                    if p not in ev:
                        ev.append(p)
            papers[pid] = {"pdf": versions, "evidence": ev}
    else:
        pdf_dir = ROOT / "eval" / "pdfs" / "peerqa"
        man = json.load(open(pdf_dir / "download_manifest.json", encoding="utf-8"))
        qa = [json.loads(line) for line in open(ROOT / "eval" / "data" / "peerqa" / "raw" / "qa.jsonl", encoding="utf-8")]
        for pid, e in sorted(man["papers"].items()):
            versions = {}
            if e.get("status") == "ok" and e.get("opens_in_pymupdf") and e.get("bytes", 0) > 10000:
                versions["latest"] = pdf_dir / e["file"]
            ev = []
            for q in qa:
                if q["paper_id"] == pid and q.get("answerable") is True:
                    for p in peerqa_evidence(q):
                        if p not in ev:
                            ev.append(p)
            papers[pid] = {"pdf": versions, "evidence": ev}
    return papers


# ----------------------------------------------------------------------------- worker
def clean(s: str) -> str:
    """Some extractors (e.g. pypdf) return lone UTF-16 surrogates; re-join valid pairs, replace lone ones
    with U+FFFD so the text can be stored as UTF-8. Only invalid code points change."""
    return s.encode("utf-16", "surrogatepass").decode("utf-16", "replace")


def worker(extractor, set_name, version, list_file):
    os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
    sys.path.insert(0, str(BACKEND))
    import django
    django.setup()
    import psutil
    import evaluate_rq1_extractors as rq1

    proc = psutil.Process()
    baseline = proc.memory_info().rss
    peak = [baseline]
    stop = threading.Event()

    def sample():
        while not stop.is_set():
            peak[0] = max(peak[0], proc.memory_info().rss)
            time.sleep(0.1)

    threading.Thread(target=sample, daemon=True).start()
    fn = rq1.EXTRACTOR_REGISTRY[extractor]
    out_path = CACHE / set_name / version / f"{extractor}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists():
        done = {json.loads(line)["paper_id"] for line in open(out_path, encoding="utf-8")}
    items = [json.loads(line) for line in open(list_file, encoding="utf-8")]
    with open(out_path, "a", encoding="utf-8") as f:
        for it in items:
            if it["paper_id"] in done:
                continue
            rec = {"paper_id": it["paper_id"], "extractor": extractor, "version": version}
            try:
                t0 = time.perf_counter()
                o = fn(Path(it["pdf"]))
                rec.update(ok=True, elapsed_sec=round(time.perf_counter() - t0, 4), page_count=o.page_count,
                           has_headings=o.has_headings, headings=[clean(h) for h in o.headings],
                           blocks=[{"text": clean(b.text), "page": b.page, "heading": clean(b.heading) if b.heading else None}
                                   for b in o.blocks],
                           full_text=clean(o.full_text))
            except Exception as e:
                rec.update(ok=False, error=f"{type(e).__name__}: {e}"[:300])
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
    stop.set()
    mem = {"extractor": extractor, "set": set_name, "version": version,
           "rss_working_set_baseline_mb": round(baseline / 2**20, 1),
           "rss_working_set_peak_mb": round(peak[0] / 2**20, 1),
           "rss_working_set_increase_mb": round((peak[0] - baseline) / 2**20, 1)}
    (out_path.parent / f"{extractor}.memory.json").write_text(json.dumps(mem, indent=1), encoding="utf-8")


def run_workers(set_name, version, items):
    list_file = CACHE / set_name / version / "_papers.jsonl"
    list_file.parent.mkdir(parents=True, exist_ok=True)
    with open(list_file, "w", encoding="utf-8") as f:
        for pid, path in items:
            f.write(json.dumps({"paper_id": pid, "pdf": str(path)}) + "\n")
    for ex in EXTRACTORS:
        print(f"[{set_name}/{version}] {ex}: {len(items)} papers", flush=True)
        subprocess.run([sys.executable, __file__, "--worker", ex, "--set", set_name, "--version", version,
                        "--list", str(list_file)], check=True)


def read_cache(set_name, version):
    out = {}
    for ex in EXTRACTORS:
        p = CACHE / set_name / version / f"{ex}.jsonl"
        if p.exists():
            for line in open(p, encoding="utf-8"):
                r = json.loads(line)
                out[(r["paper_id"], ex)] = r
    return out


def match_rates(papers, cache, pid):
    from eval_common.revalidation import evidence_match_rate
    rates = {}
    for ex in EXTRACTORS:
        r = cache.get((pid, ex))
        if r and r.get("ok"):
            found, total = evidence_match_rate(papers[pid]["evidence"], r["full_text"])
            rates[ex] = round(found / total, 4) if total else None
        else:
            rates[ex] = None
    return rates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=["reservoir", "peerqa"])
    ap.add_argument("--worker")
    ap.add_argument("--version", default="latest")
    ap.add_argument("--list")
    ap.add_argument("--with-grobid", action="store_true", help="add GROBID (localhost:8070) as a 6th extractor")
    a = ap.parse_args()
    if a.worker:
        worker(a.worker, a.set, a.version, a.list)
        return

    if a.with_grobid:
        EXTRACTORS.append("grobid")
    papers = load_set(a.set)
    with_pdf = {p: d for p, d in papers.items() if d["pdf"].get("latest") or d["pdf"].get("v1")}
    has_latest = [p for p in with_pdf if papers[p]["pdf"].get("latest")]
    run_workers(a.set, "latest", [(p, papers[p]["pdf"]["latest"]) for p in has_latest])
    latest = read_cache(a.set, "latest")
    rates_latest = {p: match_rates(papers, latest, p) if p in has_latest else {ex: None for ex in EXTRACTORS}
                    for p in with_pdf}

    def best(r):
        vals = [v for v in r.values() if v is not None]
        return max(vals) if vals else 0.0

    # v1 is tried when the latest PDF is missing or matches < 70% under every extractor
    need_v1 = [p for p in with_pdf if best(rates_latest[p]) < KEEP_THRESHOLD and papers[p]["pdf"].get("v1")]
    rates_v1 = {}
    if need_v1:
        run_workers(a.set, "v1", [(p, papers[p]["pdf"]["v1"]) for p in need_v1])
        v1 = read_cache(a.set, "v1")
        rates_v1 = {p: match_rates(papers, v1, p) for p in need_v1}

    decisions = {}
    for p, d in sorted(papers.items()):
        if p not in with_pdf:
            decisions[p] = {"kept": False, "reason": "no_usable_pdf", "n_evidence": len(d["evidence"])}
            continue
        chosen, rates = ("latest", rates_latest[p]) if p in has_latest else ("v1", rates_v1.get(p, {}))
        if p in rates_v1 and best(rates_v1[p]) > best(rates):
            chosen, rates = "v1", rates_v1[p]
        kept = best(rates) >= KEEP_THRESHOLD
        decisions[p] = {"kept": kept, "version": chosen, "reason": "ok" if kept else "evidence_match_below_0.70",
                        "n_evidence": len(d["evidence"]), "best_match_rate": best(rates),
                        "match_rate_by_extractor": rates}
    summary = {
        "set": a.set,
        "rule": f"keep if any of {len(EXTRACTORS)} extractors finds >= 70% of the paper's evidence paragraphs "
                "(>= 80% content-word containment each) in the latest PDF, else in v1 if better (v1 used when latest is missing)",
        "extractors": list(EXTRACTORS),
        "papers_in_population": len(papers),
        "papers_with_usable_pdf": len(with_pdf),
        "papers_needing_v1_check": len(need_v1),
        "papers_using_v1": sum(1 for d in decisions.values() if d.get("version") == "v1" and d["kept"]),
        "papers_kept": sum(1 for d in decisions.values() if d["kept"]),
        "papers_excluded_by_reason": {r: sum(1 for d in decisions.values() if d["reason"] == r)
                                      for r in sorted({d["reason"] for d in decisions.values()})},
    }
    ART.mkdir(parents=True, exist_ok=True)
    (ART / f"version_check_{a.set}.json").write_text(
        json.dumps({"summary": summary, "papers": decisions}, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
