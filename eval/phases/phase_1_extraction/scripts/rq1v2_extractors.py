#!/usr/bin/env python3
"""
RQ1-v2: PDF extractors on fresh papers (pre-registered: reports/revalidation/protocol/rq1_rq4.json "RQ1-v2").

Uses the extraction cache written by eval/phases/phase_0_baseline/scripts/version_check_extract.py
(each extractor ran in its own subprocess; latency per paper and working-set increase recorded there).

Primary (C-RET, selection): evidence recall = share of a paper's evidence paragraphs found (>= 0.80
content-word containment) in the extractor's full text; one value per paper. Family: each challenger vs
pymupdf_layout (Holm m=4), SESOI 0.03.
Sensitivity: the same on ALL opened reservoir papers except C-INT (i.e. before the version-check exclusion).
Secondary: heading F1 vs QASPER section names (RQ1 definition), ms/page, failure rate, working-set increase,
downstream CEC@0.5 on C-RET-150 (each extractor's sections -> hierarchical -> e5 dense -> production context;
extractors without headings get one section per page, as production's page fallback).
Descriptive: PeerQA evidence recall.

Usage: python rq1v2_extractors.py [--limit N]
Output: eval/phases/phase_1_extraction/artifacts/rq1v2/
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
import numpy as np  # noqa: E402
from eval_common.revalidation import evidence_match_rate  # noqa: E402

CACHE = ROOT / "eval" / "data" / "revalidation_cache" / "extract"
EXTRACTORS = ["pymupdf_layout", "pymupdf_plain", "pypdf", "pdfminer.six", "pdfplumber"]
INCUMBENT = "pymupdf_layout"
OUT = ROOT / "eval" / "phases" / "phase_1_extraction" / "artifacts" / "rq1v2"
E5 = "intfloat/e5-small-v2"


def load_cache(set_name):
    out = {}
    for version in ("latest", "v1"):
        for ex in EXTRACTORS:
            p = CACHE / set_name / version / f"{ex}.jsonl"
            if p.exists():
                for line in open(p, encoding="utf-8"):
                    r = json.loads(line)
                    out[(r["paper_id"], version, ex)] = r
    return out


def sections_of(rec):
    if rec.get("has_headings"):
        return [{"title": b["heading"] or "Section", "text": b["text"], "page": b["page"]} for b in rec["blocks"] if b["text"].strip()]
    pages = {}
    for b in rec["blocks"]:
        pages.setdefault(b["page"], []).append(b["text"])
    return [{"title": f"Page {p}", "text": "\n\n".join(t), "page": p} for p, t in sorted(pages.items())]


def recall_rows(paper_versions, evidence, cache):
    rows = []
    for pid, version in paper_versions.items():
        ev = evidence.get(pid, [])
        if not ev:
            continue
        rec = {"paper_id": pid, "question_id": pid}
        for ex in EXTRACTORS:
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
    from eval_common.revalidation import qasper_text_evidence

    vc = json.load(open(rr.COHORT_DIR / "version_check_reservoir.json", encoding="utf-8"))["papers"]
    c_int = set(rr.load_cohort("C-INT")["papers"])
    c_ret = rr.load_cohort("C-RET")
    train = json.load(open(ROOT / "eval/data/qasper_official/qasper-train-v0.3.json", encoding="utf-8"))
    cache = load_cache("reservoir")

    ret_versions = {it["paper_arxiv_id"]: it["pdf_version"] for it in c_ret["items"]}
    ret_evidence = {}
    for it in c_ret["items"]:
        ret_evidence.setdefault(it["paper_arxiv_id"], [])
        ret_evidence[it["paper_arxiv_id"]] += [e for e in it["retrieval_evidence"] if e not in ret_evidence[it["paper_arxiv_id"]]]
    sens_versions = {p: d.get("version", "latest") for p, d in vc.items() if d["reason"] != "no_usable_pdf" and p not in c_int}
    sens_evidence = {p: list(dict.fromkeys(e for qa in train[p]["qas"] for e in qasper_text_evidence(qa))) for p in sens_versions}
    if args.limit:
        ret_versions = dict(sorted(ret_versions.items())[: args.limit])
        sens_versions = dict(sorted(sens_versions.items())[: args.limit])

    primary_rows = recall_rows(ret_versions, ret_evidence, cache)
    sens_rows = recall_rows(sens_versions, sens_evidence, cache)
    pairs = [(ex, INCUMBENT) for ex in EXTRACTORS if ex != INCUMBENT]
    primary = rr.family(primary_rows, pairs, "evidence_recall")
    sensitivity = rr.family(sens_rows, pairs, "evidence_recall")

    # Secondary: heading F1, latency, failures, memory
    secondary = {}
    for ex in EXTRACTORS:
        f1s, ms_page, fails = [], [], 0
        for pid, version in ret_versions.items():
            c = cache.get((pid, version, ex))
            if not c or not c.get("ok"):
                fails += 1
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
        mem = json.load(open(CACHE / "reservoir" / "latest" / f"{ex}.memory.json"))
        secondary[ex] = {"heading_f1_mean": round(float(np.mean(f1s)), 4) if f1s else None,
                         "ms_per_page_p50": round(float(np.percentile(ms_page, 50)), 1) if ms_page else None,
                         "ms_per_page_mean": round(float(np.mean(ms_page)), 1) if ms_page else None,
                         "failures": fails, "memory": mem}

    # Secondary: downstream CEC on C-RET-150
    ret150 = rr.group_items(rr.load_cohort("C-RET-150"))
    papers150 = sorted(ret150)[: args.limit] if args.limit else sorted(ret150)
    down_rows = []
    for pid in papers150:
        items = ret150[pid]
        qv = rp.cached_embed(E5, [it["question"] for it in items], True, f"cret_{pid}")
        per_q = [{"paper_id": pid, "question_id": it["question_id"]} for it in items]
        for ex in EXTRACTORS:
            c = cache.get((pid, items[0]["pdf_version"], ex))
            units = rp.build_units(sections_of(c), "hierarchical", pid) if c and c.get("ok") else []
            if not units:
                for rec in per_q:
                    rec[ex] = {"cec_0.5": 0, "ndcg10": 0.0}
                continue
            texts = [u["text"] for u in units]
            um = rp.cached_embed(E5, texts, False, f"rq1v2_{pid}_{ex}")
            cand = rp.candidate_units_for_relevance(units, "hierarchical")
            for rec, it, q in zip(per_q, items, qv):
                ctx = rp.assemble(rp.rank("dense", um @ q, texts, it["question"]), units, "hierarchical")
                rec[ex] = rp.question_metrics(ctx, cand, it["retrieval_evidence"])
        down_rows += per_q

    # Descriptive: PeerQA
    peer = {}
    if (rr.COHORT_DIR / "cohort_PEERQA-PDF.json").exists():
        pc = rr.load_cohort("PEERQA-PDF")
        pev = {}
        for it in pc["items"]:
            pev.setdefault(it["paper_id"], [])
            pev[it["paper_id"]] += [e for e in it["retrieval_evidence"] if e not in pev[it["paper_id"]]]
        prow = recall_rows({p: "latest" for p in pc["papers"]}, pev, load_cache("peerqa"))
        peer = {"papers": len(prow), "means": rr.arm_means(prow, EXTRACTORS, ["evidence_recall", "ok"])}

    winners = [r for r in primary if r["diff"] >= 0.03 and r["ci95"][0] > 0]
    summary = {
        "experiment": "RQ1-v2", "cohort": "C-RET", "role": "SELECTION", "papers": len(primary_rows),
        "means": rr.arm_means(primary_rows, EXTRACTORS, ["evidence_recall", "ok"]),
        "primary_family_evidence_recall": primary,
        "sensitivity_all_opened_papers": {"papers": len(sens_rows), "means": rr.arm_means(sens_rows, EXTRACTORS, ["evidence_recall"]), "family": sensitivity},
        "secondary": secondary,
        "downstream_c_ret_150": {"questions": len(down_rows), "means": rr.arm_means(down_rows, EXTRACTORS, ["cec_0.5", "ndcg10"]),
                                 "family_cec_0.5": rr.family(down_rows, pairs, "cec_0.5")},
        "peerqa_descriptive": peer,
        "decision_rule": "switch only if a challenger beats pymupdf_layout by >= 0.03 evidence recall with CI lower bound > 0",
        "decision": (max(winners, key=lambda r: r["diff"])["comparison"].split(" - ")[0] if winners else "keep pymupdf_layout"),
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper (one value per paper)"},
    }
    rr.write_outputs(OUT if not args.limit else OUT / f"smoke_{args.limit}", primary_rows, summary)
    print({k: summary[k] for k in ("papers", "decision")})


if __name__ == "__main__":
    main()
