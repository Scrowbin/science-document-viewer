#!/usr/bin/env python3
"""
extraction experiment GROBID add-on (post-Gate-B, separate test; protocol rq1_grobid_addon.json (archived)).

GROBID was not running before Gate B, so the frozen extraction experiment family (4 challengers vs pymupdf_layout, Holm m=4)
and the version-check cohorts stay as they are. GROBID is compared with pymupdf_layout in its OWN test, on the
same frozen papers and PDF versions, and is not eligible for adoption in this run.

Extraction: GROBID 0.8.2 (CRF image, local Docker, docker-compose.grobid.yml), /api/processFulltextDocument,
one request at a time, teiCoordinates for page numbers. TEI -> one block per <div> (head = heading, paragraphs
joined with itertext() so inline <ref> citations do not truncate the text); the abstract is the first block.
The historical adapter in backend/scripts/evaluate_rq1_extractors.py is NOT used: it reads p.text (cut at the
first inline citation), hard-codes page_count=1 and uses a 15 s timeout.

Primary (the QASPER component set): evidence recall, grobid - pymupdf_layout, paper-cluster bootstrap (B=10,000, seed 42), unadjusted.
Sensitivity: all opened reservoir papers except the former hold-out set (same set as the frozen extraction experiment sensitivity).
Secondary: heading F1, client ms/page, failures, container memory (docker stats), downstream CEC/nDCG on the 150-paper QASPER subset.
Descriptive: PeerQA-PDF evidence recall.

Usage: python evaluate_extraction_grobid.py [--limit N]
Cache:  eval/data/revalidation_cache/extract_grobid/<set>/<version>/grobid.jsonl   (separate from the frozen cache)
Output: eval/phases/phase_1_extraction/artifacts/evaluate_extraction_grobid/
"""

import argparse
import json
import re
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
import fitz  # noqa: E402
import numpy as np  # noqa: E402
import requests  # noqa: E402
import evaluate_extraction as base  # noqa: E402  (frozen script; only its helpers are reused)
from eval_common.revalidation import evidence_match_rate, qasper_text_evidence  # noqa: E402

GROBID = "http://localhost:8070"
CONTAINER = "science_doc_grobid"
TIMEOUT_S = 300
CACHE = ROOT / "eval" / "data" / "revalidation_cache" / "extract_grobid"
OUT = ROOT / "eval" / "phases" / "phase_1_extraction" / "artifacts" / "evaluate_extraction_grobid"
NS = {"tei": "http://www.tei-c.org/ns/1.0"}
ARMS = ["pymupdf_layout", "grobid"]


# ----------------------------------------------------------------------------- extraction
def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def _page(el):
    coords = el.get("coords")
    return int(coords.split(",")[0]) if coords else None


def parse_tei(tei: str):
    root = ET.fromstring(tei)
    blocks = []
    abstract = [_text(p) for p in root.findall(".//tei:teiHeader//tei:abstract//tei:p", NS)]
    if any(abstract):
        blocks.append({"text": "\n\n".join(a for a in abstract if a), "page": 1, "heading": "Abstract"})
    for div in root.findall(".//tei:text/tei:body/tei:div", NS):
        head = div.find("tei:head", NS)
        heading = _text(head) if head is not None else None
        paras = [p for p in div.findall("tei:p", NS) if _text(p)]
        if not paras:
            continue
        page = _page(paras[0]) or (_page(head) if head is not None else None) or (blocks[-1]["page"] if blocks else 1)
        blocks.append({"text": "\n\n".join(_text(p) for p in paras), "page": page, "heading": heading or None})
    headings = [b["heading"] for b in blocks if b["heading"] and b["heading"] != "Abstract"]
    full_text = "\n\n".join(f"{b['heading']}\n\n{b['text']}" if b["heading"] else b["text"] for b in blocks)
    return blocks, headings, full_text


def extract(pdf: Path):
    with fitz.open(pdf) as d:
        pages = len(d)
    t0 = time.perf_counter()
    with open(pdf, "rb") as f:
        resp = requests.post(f"{GROBID}/api/processFulltextDocument", timeout=TIMEOUT_S,
                             files={"input": (pdf.name, f, "application/pdf")},
                             data={"teiCoordinates": ["p", "head"]})
    elapsed = time.perf_counter() - t0
    resp.raise_for_status()
    blocks, headings, full_text = parse_tei(resp.text)
    return {"ok": bool(full_text), "elapsed_sec": round(elapsed, 4), "page_count": pages, "has_headings": True,
            "headings": headings, "blocks": blocks, "full_text": full_text,
            **({} if full_text else {"error": "empty TEI body"})}


class DockerMemory:
    """Container memory from `docker stats` (each call takes ~1-2 s, so this is a coarse sampler)."""

    def __init__(self):
        self.samples = []
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    @staticmethod
    def read_mb():
        out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", CONTAINER],
                             capture_output=True, text=True).stdout.strip()
        m = re.match(r"([\d.]+)\s*([KMG]i?B)", out)
        if not m:
            return None
        return float(m.group(1)) * {"KiB": 1 / 1024, "KB": 1 / 1000, "MiB": 1, "MB": 1, "GiB": 1024, "GB": 1000}[m.group(2)]

    def _run(self):
        while not self._stop.is_set():
            v = self.read_mb()
            if v is not None:
                self.samples.append(v)

    def __enter__(self):
        self.idle = self.read_mb()
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()

    def report(self):
        return {"definition": "docker stats MemUsage of the GROBID container (cgroup memory incl. JVM heap), "
                              "sampled about every 1-2 s; not comparable 1:1 with a Windows process working set",
                "container_idle_mb": round(self.idle, 1) if self.idle else None,
                "container_peak_mb": round(max(self.samples), 1) if self.samples else None,
                "container_mean_mb": round(float(np.mean(self.samples)), 1) if self.samples else None,
                "samples": len(self.samples)}


def run_extraction(set_name, todo):
    """todo: [(paper_id, version, pdf_path)]. Appends to the cache; resumable."""
    done = {}
    for version in {v for _, v, _ in todo}:
        p = CACHE / set_name / version / "grobid.jsonl"
        if p.exists():
            done.update({(json.loads(line)["paper_id"], version): True for line in open(p, encoding="utf-8")})
    pending = [t for t in todo if (t[0], t[1]) not in done]
    print(f"[{set_name}] grobid: {len(pending)} to extract ({len(todo) - len(pending)} cached)", flush=True)
    with DockerMemory() as mem:
        for n, (pid, version, pdf) in enumerate(pending, 1):
            rec = {"paper_id": pid, "extractor": "grobid", "version": version}
            try:
                rec.update(extract(pdf))
            except Exception as e:
                rec.update(ok=False, error=f"{type(e).__name__}: {e}"[:300])
            out = CACHE / set_name / version / "grobid.jsonl"
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if n % 25 == 0:
                print(f"  {n}/{len(pending)}", flush=True)
    if pending:
        (CACHE / set_name / "grobid.memory.json").write_text(json.dumps(mem.report(), indent=1), encoding="utf-8")


def load(set_name):
    out = {}
    for p in (CACHE / set_name).glob("*/grobid.jsonl"):
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            out[(r["paper_id"], r["version"], "grobid")] = r
    return out


# ----------------------------------------------------------------------------- analysis
def recall_rows(versions, evidence, cache):
    rows = []
    for pid, version in versions.items():
        ev = evidence.get(pid, [])
        if not ev:
            continue
        rec = {"paper_id": pid, "question_id": pid}
        for ex in ARMS:
            c = cache.get((pid, version, ex))
            if c and c.get("ok"):
                found, total = evidence_match_rate(ev, c["full_text"])
                rec[ex] = {"evidence_recall": found / total, "ok": 1}
            else:
                rec[ex] = {"evidence_recall": 0.0, "ok": 0}
        rows.append(rec)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    import evaluate_rq1_extractors as rq1

    alive = requests.get(f"{GROBID}/api/isalive", timeout=5).text.strip()
    version = requests.get(f"{GROBID}/api/version", timeout=5).json()
    image = subprocess.run(["docker", "inspect", "--format", "{{.Image}}", CONTAINER], capture_output=True, text=True).stdout.strip()
    assert alive == "true", "GROBID is not running"

    vc = json.load(open(rr.COHORT_DIR / "version_check_reservoir.json", encoding="utf-8"))["papers"]
    c_int = set(rr.load_cohort("C-INT")["papers"])
    c_ret = rr.load_cohort("C-RET")
    train = json.load(open(ROOT / "eval/data/qasper_official/qasper-train-v0.3.json", encoding="utf-8"))

    ret_versions = {it["paper_arxiv_id"]: it["pdf_version"] for it in c_ret["items"]}
    ret_evidence = {}
    for it in c_ret["items"]:
        ret_evidence.setdefault(it["paper_arxiv_id"], [])
        ret_evidence[it["paper_arxiv_id"]] += [e for e in it["retrieval_evidence"] if e not in ret_evidence[it["paper_arxiv_id"]]]
    sens_versions = {p: d.get("version", "latest") for p, d in vc.items() if d["reason"] != "no_usable_pdf" and p not in c_int}
    sens_evidence = {p: list(dict.fromkeys(e for qa in train[p]["qas"] for e in qasper_text_evidence(qa))) for p in sens_versions}
    pc = rr.load_cohort("PEERQA-PDF")
    peer_versions = {p: "latest" for p in pc["papers"]}
    if args.limit:
        ret_versions = dict(sorted(ret_versions.items())[: args.limit])
        sens_versions = dict(sorted(sens_versions.items())[: args.limit])
        peer_versions = dict(sorted(peer_versions.items())[: args.limit])
    assert not (set(ret_versions) | set(sens_versions)) & c_int, "C-INT paper in RQ1 add-on"

    ret150 = rr.group_items(rr.load_cohort("C-RET-150"))
    papers150 = sorted(ret150)[: args.limit] if args.limit else sorted(ret150)
    down_versions = {p: ret150[p][0]["pdf_version"] for p in papers150}
    reservoir_todo = sorted({(p, v, rr.pdf_path("C-RET", p, v))
                             for p, v in {**sens_versions, **ret_versions, **down_versions}.items()})
    run_extraction("reservoir", reservoir_todo)
    run_extraction("peerqa", sorted((p, "latest", rr.pdf_path("PEERQA-PDF", p)) for p in peer_versions))

    res_cache = {**base.load_cache("reservoir"), **load("reservoir")}
    peer_cache = {**base.load_cache("peerqa"), **load("peerqa")}

    primary_rows = recall_rows(ret_versions, ret_evidence, res_cache)
    sens_rows = recall_rows(sens_versions, sens_evidence, res_cache)
    primary = rr.compare(primary_rows, "pymupdf_layout", "grobid", "evidence_recall")
    sensitivity = rr.compare(sens_rows, "pymupdf_layout", "grobid", "evidence_recall")

    # Secondary: heading F1 and latency, same definitions as the frozen RQ1-v2
    secondary = {}
    for ex in ARMS:
        f1s, ms_page, fails, errors = [], [], 0, []
        for pid, ver in ret_versions.items():
            c = res_cache.get((pid, ver, ex))
            if not c or not c.get("ok"):
                fails += 1
                errors.append({"paper_id": pid, "error": (c or {}).get("error", "missing")})
                continue
            gold = {rq1.normalize_heading_title(s["section_name"]) for s in train[pid]["full_text"]
                    if s.get("section_name") and rq1.normalize_heading_title(s["section_name"])}
            pred = {rq1.normalize_heading_title(h) for h in c["headings"] if rq1.normalize_heading_title(h)}
            if gold and pred:
                m = len(gold & pred)
                p_, r_ = m / len(pred), m / len(gold)
                f1s.append(2 * p_ * r_ / (p_ + r_) if p_ + r_ else 0.0)
            else:
                f1s.append(1.0 if not gold and not pred else 0.0)
            ms_page.append(1000 * c["elapsed_sec"] / max(1, c["page_count"]))
        secondary[ex] = {"heading_f1_mean": round(float(np.mean(f1s)), 4) if f1s else None,
                         "ms_per_page_p50": round(float(np.percentile(ms_page, 50)), 1) if ms_page else None,
                         "ms_per_page_mean": round(float(np.mean(ms_page)), 1) if ms_page else None,
                         "failures": fails, "failure_list": errors}
    secondary["pymupdf_layout"]["memory"] = json.load(open(base.CACHE / "reservoir" / "latest" / "pymupdf_layout.memory.json"))
    mem_file = CACHE / "reservoir" / "grobid.memory.json"
    secondary["grobid"]["memory"] = json.load(open(mem_file)) if mem_file.exists() else None
    secondary["grobid"]["latency_note"] = ("client wall time of one HTTP request to the Docker/WSL2 container, "
                                           "one request at a time; pymupdf_layout is in-process. Not a like-for-like speed comparison.")

    # Secondary: downstream CEC/nDCG on C-RET-150 (same pipeline as the frozen RQ1-v2 downstream step)
    down_rows, down_missing = [], {ex: [] for ex in ARMS}
    for pid in papers150:
        items = ret150[pid]
        qv = rp.cached_embed(base.E5, [it["question"] for it in items], True, f"cret_{pid}")
        per_q = [{"paper_id": pid, "question_id": it["question_id"]} for it in items]
        for ex in ARMS:
            c = res_cache.get((pid, items[0]["pdf_version"], ex))
            units = rp.build_units(base.sections_of(c), "hierarchical", pid) if c and c.get("ok") else []
            if not units:
                down_missing[ex].append(pid)
                for rec in per_q:
                    rec[ex] = {"cec_0.5": 0, "ndcg10": 0.0}
                continue
            texts = [u["text"] for u in units]
            um = rp.cached_embed(base.E5, texts, False, f"rq1v2_{pid}_{ex}")
            cand = rp.candidate_units_for_relevance(units, "hierarchical")
            for rec, it, q in zip(per_q, items, qv):
                ctx = rp.assemble(rp.rank("dense", um @ q, texts, it["question"]), units, "hierarchical")
                rec[ex] = rp.question_metrics(ctx, cand, it["retrieval_evidence"])
        down_rows += per_q

    # Descriptive: PeerQA-PDF
    pev = {}
    for it in pc["items"]:
        pev.setdefault(it["paper_id"], [])
        pev[it["paper_id"]] += [e for e in it["retrieval_evidence"] if e not in pev[it["paper_id"]]]
    prow = recall_rows(peer_versions, pev, peer_cache)

    half = round((primary["ci95"][1] - primary["ci95"][0]) / 2, 4)
    meets = primary["diff"] >= 0.03 and primary["ci95"][0] > 0
    summary = {
        "experiment": "RQ1-v2-GROBID-ADDON", "cohort": "C-RET", "role": "SELECTION (add-on; not eligible for adoption)",
        "grobid": {"server_version": version, "image": image, "endpoint": "/api/processFulltextDocument",
                   "params": {"teiCoordinates": ["p", "head"]}, "timeout_s": TIMEOUT_S, "concurrency": 1},
        "papers": len(primary_rows),
        "means": rr.arm_means(primary_rows, ARMS, ["evidence_recall", "ok"]),
        "primary_evidence_recall": {**primary, "ci95_half_width": half, "adjustment": "none (separate add-on test)"},
        "would_meet_frozen_switch_rule": meets,
        "sensitivity_all_opened_papers": {"papers": len(sens_rows), "means": rr.arm_means(sens_rows, ARMS, ["evidence_recall"]),
                                          "comparison": sensitivity},
        "secondary": secondary,
        "downstream_c_ret_150": {"questions": len(down_rows), "papers_without_units_scored_0": down_missing, "means": rr.arm_means(down_rows, ARMS, ["cec_0.5", "ndcg10"]),
                                 "cec_0.5": rr.compare(down_rows, "pymupdf_layout", "grobid", "cec_0.5"),
                                 "ndcg10": rr.compare(down_rows, "pymupdf_layout", "grobid", "ndcg10")},
        "peerqa_descriptive": {"papers": len(prow), "means": rr.arm_means(prow, ARMS, ["evidence_recall", "ok"])},
        "decision": "pymupdf_layout stays (GROBID is an add-on and cannot be adopted in this run)",
        "interpretation_rule": "if would_meet_frozen_switch_rule is true, report GROBID as a lead for future work, not a winner",
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper (one value per paper)"},
    }
    rr.write_outputs(OUT if not args.limit else OUT / f"smoke_{args.limit}", primary_rows, summary)
    print(json.dumps({k: summary[k] for k in ("papers", "means", "primary_evidence_recall", "would_meet_frozen_switch_rule")}, indent=1))


if __name__ == "__main__":
    main()
