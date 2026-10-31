#!/usr/bin/env python3
"""
Cross-RQ dataset audit (RQ1-RQ5): cohort ID sets, overlap matrix, dataset ledger, checks.

Read-only with respect to the project: it only reads existing artifacts and writes to
reports/audit/. No network, no model loading, no inference. Deterministic: IDs are
sorted and no timestamps are written, so two runs produce byte-identical outputs.

Outputs (reports/audit/):
  cross_rq_audit_checks.json     PASS / FAIL / INFO checks with values
  cross_rq_audit_ids.json        full paper / question ID lists per cohort and overlap
  CROSS_RQ_DATASET_LEDGER.csv    one row per cohort
  CROSS_RQ_OVERLAP_MATRIX.csv    pairwise paper / question intersections (detection only)

Run:  backend/venv/Scripts/python.exe reports/audit/scripts/cross_rq_audit.py
"""

import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports" / "audit"

P_OFFICIAL = ROOT / "eval" / "data" / "qasper_official"
P_PREP = ROOT / "eval" / "prepared"
P_RESULTS = ROOT / "eval" / "results"
P_RQ4 = ROOT / "eval" / "phases" / "phase_6_hybrid_retrieval" / "artifacts"
P_RQ5 = ROOT / "eval" / "phases" / "phase_9_generation" / "artifacts"
P_REVIEW = P_RQ5 / "human_faithfulness_review"
REGISTRY = ROOT / "eval" / "experiment_provenance_registry.json"
THESIS = ROOT / "DU_AN_CNTT_TOAN_VAN.md"

RQ1_TS = "20261024_000639"
RQ2_TS = "20261024_013443"
RQ5_MODELS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"]

CHECKS: List[Dict[str, Any]] = []


def rel(p):
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(p):
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def check(cid, rq, status, summary, **values):
    CHECKS.append({"id": cid, "rq": rq, "status": status, "summary": summary, "values": values})


def norm_text(s):
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# 1. Official QASPER v0.3
# ---------------------------------------------------------------------------
official = {s: load_json(P_OFFICIAL / f"qasper-{s}-v0.3.json") for s in ("train", "dev", "test")}
paper_split = {pid: s for s, d in official.items() for pid in d}
q_paper = {}  # QASPER question hash -> paper
for s, d in official.items():
    for pid, pdata in d.items():
        for qa in pdata.get("qas", []):
            q_paper[qa["question_id"]] = pid
q_split = {qid: paper_split[pid] for qid, pid in q_paper.items()}

check("QASPER-01", "all", "INFO", "Official QASPER v0.3 split sizes",
      papers={s: len(d) for s, d in official.items()},
      questions={s: sum(len(p.get("qas", [])) for p in d.values()) for s, d in official.items()},
      paper_ids_disjoint=len(set(official["train"]) & set(official["dev"])) + len(set(official["train"]) & set(official["test"])) + len(set(official["dev"]) & set(official["test"])) == 0)


def rq4_included(qa):
    """Inclusion rule of evaluate_full_qasper_rq4_hybrid.load_official_qasper_corpus."""
    for ans in qa.get("answers", []):
        a = ans.get("answer", {})
        if not a.get("unanswerable", False):
            if any((not ev.startswith("FLOAT SELECTED")) and ev.strip() for ev in a.get("evidence", [])):
                return True
    return False


def has_text_sections(pdata):
    return any("\n\n".join(sec.get("paragraphs", [])).strip() for sec in pdata.get("full_text", []))


# ---------------------------------------------------------------------------
# 2. Cohorts
# ---------------------------------------------------------------------------
cohorts: Dict[str, Dict[str, Any]] = {}


def add_cohort(name, papers, questions, membership, sources, q_namespace="qasper_hash", **extra):
    cohorts[name] = {
        "papers": set(papers),
        "questions": set(questions),
        "membership": membership,
        "sources": sources,
        "q_namespace": q_namespace,
        **extra,
    }


for s in ("train", "dev", "test"):
    add_cohort(f"QASPER-{s.upper()}", official[s].keys(),
               [qa["question_id"] for p in official[s].values() for qa in p.get("qas", [])],
               "recorded", [rel(P_OFFICIAL / f"qasper-{s}-v0.3.json")])

# In-house prepared files (in-house IDs Q_QASP_xxx are mapped to QASPER hashes via original_id)
qs_pilot = load_json(P_PREP / "qasper_sampled.json")          # 250 q / pilot sample
qs_exp = load_json(P_PREP / "expanded_qasper_sampled.json")   # 487 q
inhouse_pilot = {q["id"]: q["original_id"] for q in qs_pilot}
inhouse_exp = {q["id"]: q["original_id"] for q in qs_exp}
shared_inhouse = sorted(set(inhouse_pilot) & set(inhouse_exp))
collide = [i for i in shared_inhouse if inhouse_pilot[i] != inhouse_exp[i]]
check("IDS-01", "RQ1-RQ3", "INFO" if collide else "PASS",
      "In-house query IDs (Q_QASP_xxx) are reused across qasper_sampled.json and expanded_qasper_sampled.json "
      "for different QASPER questions; cross-file joins must use original_id",
      shared_inhouse_ids=len(shared_inhouse), same_id_different_question=len(collide),
      examples=collide[:10])

split48 = load_json(P_PREP / "dev_held_out_split.json")
exp160 = load_json(P_PREP / "expanded_held_out_split.json")
dev48 = set(split48["dev_papers"])
ho48 = set(split48["held_out_papers"])
ho160 = set(exp160["held_out_papers"])

add_cohort("PILOT-SAMPLE-96P", {q["paper_arxiv_id"] for q in qs_pilot}, [q["original_id"] for q in qs_pilot],
           "recorded", [rel(P_PREP / "qasper_sampled.json")])

# --- RQ1 / RQ2 (directly recorded per-query JSONL, written by the same runs) ---
rq1_json = load_json(P_RESULTS / f"rq1_extraction_{RQ1_TS}.json")
rq2_json = load_json(P_RESULTS / f"rq2_chunking_{RQ2_TS}.json")
rq1_rows = load_jsonl(P_RESULTS / f"rq1_extraction_queries_{RQ1_TS}.jsonl")
rq2_rows = load_jsonl(P_RESULTS / f"rq2_chunking_queries_{RQ2_TS}.jsonl")


def map_inhouse(ids):
    mapped = {inhouse_pilot.get(i) for i in ids}
    return {m for m in mapped if m}, sorted(i for i in ids if i not in inhouse_pilot)


rq1_papers = {r["paper_arxiv_id"] for r in rq1_rows}
rq1_qin = {r["query_id"] for r in rq1_rows}
rq1_q, rq1_unmapped = map_inhouse(rq1_qin)
rq2_papers = {r["paper_arxiv_id"] for r in rq2_rows}
rq2_qin = {r["query_id"] for r in rq2_rows}
rq2_q, rq2_unmapped = map_inhouse(rq2_qin)
add_cohort("RQ1-47P", rq1_papers, rq1_q, "recorded",
           [rel(P_RESULTS / f"rq1_extraction_queries_{RQ1_TS}.jsonl"), rel(P_RESULTS / f"rq1_extraction_{RQ1_TS}.json")])
add_cohort("RQ2-47P", rq2_papers, rq2_q, "recorded",
           [rel(P_RESULTS / f"rq2_chunking_queries_{RQ2_TS}.jsonl"), rel(P_RESULTS / f"rq2_chunking_{RQ2_TS}.json")])

# Four lines of corroborating evidence for the historical RQ1/RQ2 cohort
pdf_dirs = [ROOT / "eval" / "pdfs" / "dev", ROOT / "eval" / "data" / "pdfs", ROOT / "sample__papers"]
available = {}
for aid in split48["dev_papers"]:
    for d in pdf_dirs:
        cand = d / f"{aid}.pdf"
        if cand.exists() and cand.stat().st_size > 10000:
            available[aid] = cand
            break
loader_today = [aid for aid in split48["dev_papers"] if aid in available]


def ts_of(path):
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y%m%d_%H%M%S")


pdf_mtimes = {aid: ts_of(p) for aid, p in available.items()}
pdfs_newer_than_rq1 = sorted(a for a, t in pdf_mtimes.items() if t > RQ1_TS)
reg = load_json(REGISTRY)
reg_exp = reg["registered_experiments"]
reg_rq1 = set(reg_exp["EXP-RQ1-EXTRACTION"].get("paper_ids", []))
reg_rq2 = set(reg_exp["EXP-RQ2-CHUNKING"].get("paper_ids", []))
missing_pdf = sorted(dev48 - set(available))
rq12_agree = (set(loader_today) == rq1_papers == rq2_papers == reg_rq1 == reg_rq2)
check("RQ12-01", "RQ1/RQ2", "PASS" if rq12_agree and not rq1_unmapped and not rq2_unmapped else "INFO",
      "RQ1/RQ2 cohort: per-query JSONL written by the same runs (recorded) vs loader-today, PDF mtimes, registry",
      result_timestamps={"rq1": RQ1_TS, "rq2": RQ2_TS},
      papers_evaluated_metadata={"rq1": rq1_json["metadata"]["papers_evaluated"], "rq2": rq2_json["metadata"]["papers_evaluated"]},
      jsonl_mtime={"rq1": ts_of(P_RESULTS / f"rq1_extraction_queries_{RQ1_TS}.jsonl"),
                   "rq2": ts_of(P_RESULTS / f"rq2_chunking_queries_{RQ2_TS}.jsonl")},
      rq1_jsonl_papers=len(rq1_papers), rq1_jsonl_queries=len(rq1_qin),
      rq2_jsonl_papers=len(rq2_papers), rq2_jsonl_queries=len(rq2_qin),
      rq1_equals_rq2_papers=rq1_papers == rq2_papers, rq1_equals_rq2_queries=rq1_qin == rq2_qin,
      inhouse_dev_papers=len(dev48), pdfs_available_today=len(available), loader_today_selects=len(loader_today),
      loader_today_equals_recorded=set(loader_today) == rq1_papers,
      dev48_without_pdf=missing_pdf,
      pdfs_with_mtime_after_rq1_run=len(pdfs_newer_than_rq1),
      registry_rq1_equals_recorded=reg_rq1 == rq1_papers, registry_rq2_equals_recorded=reg_rq2 == rq2_papers,
      unmapped_inhouse_query_ids=rq1_unmapped + rq2_unmapped,
      note="The JSONL files carry per-query paper IDs written by the runs themselves, so membership is recorded. "
           "PDF mtimes only show the files present today are not newer than the run; they do not prove byte identity.")

# RQ1 / RQ2 numerical reproduction of headline means from per-query rows
rq1_mean = {}
for eng in sorted({r["engine"] for r in rq1_rows}):
    v = [r["ndcg10"] for r in rq1_rows if r["engine"] == eng]
    rq1_mean[eng] = round(sum(v) / len(v), 4)
check("RQ1-01", "RQ1", "INFO", "RQ1 per-engine query-weighted mean nDCG@10 recomputed from per-query JSONL (compare with Table 5.x)",
      mean_ndcg10_from_jsonl=rq1_mean,
      queries_per_engine=dict(Counter(r["engine"] for r in rq1_rows)),
      queries_with_Rq_zero_per_engine={e: sum(1 for r in rq1_rows if r["engine"] == e and r["R_q"] == 0) for e in sorted(rq1_mean)},
      engines_evaluated=sorted(rq1_mean))

rq2_stats = {}
for st in sorted({r["strategy"] for r in rq2_rows}):
    rows = [r for r in rq2_rows if r["strategy"] == st]
    rq2_stats[st] = {
        "n": len(rows),
        "mean_ndcg10": round(sum(r["ndcg10"] for r in rows) / len(rows), 4),
        "mean_ndcg4": round(sum(r["ndcg4"] for r in rows) / len(rows), 4),
        "mean_recall20": round(sum(r["recall20"] for r in rows) / len(rows), 4),
        "budget_covered_rate": round(sum(r["budget_covered"] for r in rows) / len(rows), 4),
        "queries_Rq_zero": sum(1 for r in rows if r["R_q"] == 0),
        "mean_Rq": round(sum(r["R_q"] for r in rows) / len(rows), 3),
        "tau": sorted({r["tau"] for r in rows}),
    }
check("RQ2-01", "RQ2", "INFO",
      "RQ2 per-strategy means from per-query JSONL. nDCG/Recall are over the full unbudgeted ranked list; "
      "budget_covered is the only budget-aware field (evidence in units accumulated until >= 1,600 tokens, "
      "the crossing unit included). R_q is counted in each strategy's own units.",
      per_strategy=rq2_stats)
rq_zero_any = {}
for r in rq2_rows:
    rq_zero_any.setdefault(r["query_id"], {})[r["strategy"]] = r["R_q"]
unit_dependent = sorted(q for q, d in rq_zero_any.items() if min(d.values()) == 0 and max(d.values()) > 0)
check("RQ2-02", "RQ2", "INFO",
      "Queries whose relevance set is empty under some chunking strategies but non-empty under others "
      "(ground truth depends on unit size)",
      count=len(unit_dependent), of_queries=len(rq_zero_any), examples=unit_dependent[:10])

# --- RQ3 (reconstructed from the loader in run_thesis_embedding_benchmark.py) ---
qasper_corpus = load_json(P_PREP / "qasper_corpus.json")
exp_corpus = load_json(P_PREP / "expanded_corpus.json")
exp_chunks = load_json(ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts" / "expanded_160_chunks.json")
chunk_papers_ho = Counter(c["chunk_id"].rsplit("_c_", 1)[0] for c in exp_chunks)

dev_q = [q for q in qs_pilot if q["paper_arxiv_id"] in dev48 and q.get("question_type") != "unanswerable"]
ho_q = [q for q in qs_exp if q["paper_arxiv_id"] in ho160 and q.get("question_type") != "unanswerable"]
dev_has_text = {p for p in dev48 if any((s.get("text") or "").strip() for s in qasper_corpus.get(p, {}).get("sections", []))}
ho_has_text = {p for p in ho160 if any((s.get("text") or "").strip() for s in exp_corpus.get(p, {}).get("sections", []))}
dev_q_valid = [q for q in dev_q if q["paper_arxiv_id"] in dev_has_text]
ho_q_valid = [q for q in ho_q if q["paper_arxiv_id"] in ho_has_text]
rq3_dev_papers = {q["paper_arxiv_id"] for q in dev_q_valid}
rq3_ho_papers = {q["paper_arxiv_id"] for q in ho_q_valid}
rq3_papers = rq3_dev_papers | rq3_ho_papers
rq3_q = {q["original_id"] for q in dev_q_valid} | {q["original_id"] for q in ho_q_valid}
ho_zero_q = sorted(ho160 - rq3_ho_papers)
add_cohort("RQ3-DEV-48P", rq3_dev_papers, {q["original_id"] for q in dev_q_valid}, "reconstructed",
           [rel(P_PREP / "dev_held_out_split.json"), rel(P_PREP / "qasper_sampled.json"), "backend/scripts/run_thesis_embedding_benchmark.py:196-287"])
add_cohort("RQ3-HELDOUT-160P", ho160, {q["original_id"] for q in ho_q_valid}, "reconstructed",
           [rel(P_PREP / "expanded_held_out_split.json"), rel(P_PREP / "expanded_qasper_sampled.json")])
add_cohort("RQ3-207P", rq3_papers, rq3_q, "reconstructed",
           ["union of RQ3-DEV-48P and RQ3-HELDOUT-160P after the loader's 0-chunk filter"])
add_cohort("INHOUSE-HELDOUT-48P", ho48,
           [inhouse_pilot[i] for i in split48["held_out_query_ids"] if i in inhouse_pilot], "recorded",
           [rel(P_PREP / "dev_held_out_split.json")], note="first 48-paper held-out cohort; frozen_cohort_1 of the 160")

# Containment-threshold (tau) labelling sets: 80 calibration + 35 fresh pairs (34 after sanitising)
tau_cal = load_json(P_PREP / "containment_label_queue_labeled.json")
tau_fresh = load_json(P_PREP / "new_containment_validation_queue.json")
tau_items = tau_cal + tau_fresh
add_cohort("TAU-LABELS-115PAIRS", {i["aid"] for i in tau_items}, {inhouse_pilot[i["qid"]] for i in tau_items if i["qid"] in inhouse_pilot},
           "recorded", [rel(P_PREP / "containment_label_queue_labeled.json"), rel(P_PREP / "new_containment_validation_queue.json"),
                        rel(P_PREP / "containment_validation_metrics.json")])
tau_metrics = load_json(P_PREP / "containment_validation_metrics.json")
check("TAU-01", "RQ1-RQ4", "INFO", "Relevance-threshold labels: cohort and validation precision (stored metrics)",
      calibration_pairs=len(tau_cal), fresh_pairs=len(tau_fresh),
      calibration_papers=len({i["aid"] for i in tau_cal}), fresh_papers=len({i["aid"] for i in tau_fresh}),
      papers_in_inhouse_dev48=len({i["aid"] for i in tau_items} & dev48),
      fresh_sanitized_n34={t: tau_metrics["fresh_validation_sanitized_n34"][t] for t in ("0.50", "0.55")},
      calibration_n80={t: tau_metrics["calibration_n80"][t] for t in ("0.50", "0.55")})

rq3_bench = load_json(P_RESULTS / "thesis_embedding_benchmark.json")
rq3_types = Counter(m["type"] for m in rq3_bench["models"])
check("RQ3-01", "RQ3", "PASS" if (not (dev48 & ho160) and len(rq3_papers) == rq3_bench["metadata"]["corpus"]["active_papers"]
                                  and len(dev_q_valid) + len(ho_q_valid) == rq3_bench["metadata"]["corpus"]["total_queries"]) else "FAIL",
      "RQ3 corpus reconstructed by ID from the loader inputs",
      dev48_heldout160_disjoint=not (dev48 & ho160),
      dev_papers=len(rq3_dev_papers), dev_queries=len(dev_q_valid),
      heldout_manifest_papers=len(ho160), heldout_papers_with_queries=len(rq3_ho_papers),
      heldout_papers_without_scored_queries=ho_zero_q,
      heldout_queries=len(ho_q_valid), total_papers=len(rq3_papers), total_queries=len(rq3_q),
      artifact_corpus=rq3_bench["metadata"]["corpus"],
      unique_question_hashes=len(rq3_q), query_rows=len(dev_q_valid) + len(ho_q_valid),
      heldout_chunks_in_expanded_160_chunks=len(exp_chunks),
      heldout_papers_with_chunks_file=len(chunk_papers_ho),
      dev_chunks="not recomputed (needs the Django chunker); docstring/thesis value 1,099",
      inhouse_heldout48_subset_of_160=ho48 <= ho160,
      official_split_of_rq3_papers=dict(Counter(paper_split.get(p, "non_qasper") for p in rq3_papers)),
      official_split_dev48=dict(Counter(paper_split.get(p) for p in rq3_dev_papers)),
      official_split_heldout=dict(Counter(paper_split.get(p) for p in rq3_ho_papers)))
check("RQ3-02", "RQ3", "INFO", "RQ3 evaluated methods in thesis_embedding_benchmark.json",
      entries=len(rq3_bench["models"]), by_type=dict(rq3_types),
      names=[m["short_name"] for m in rq3_bench["models"]],
      per_model_n_queries="not recorded per model; only metadata.corpus.total_queries; the script scores every model on the same valid_queries list")
reg3 = reg_exp["EXP-RQ3-EMBEDDING-UNIFIED"]
reg3_p, reg3_q = set(reg3.get("paper_ids", [])), set(reg3.get("question_ids", []))
reg3_q_mapped = {inhouse_pilot.get(q) or inhouse_exp.get(q) or q for q in reg3_q}
check("RQ3-03", "RQ3", "INFO" if reg3_p >= rq3_papers else "FAIL",
      "Registry EXP-RQ3 entry vs reconstructed RQ3 cohort",
      registry_papers=len(reg3_p), registry_questions=len(reg3_q),
      registry_papers_not_in_rq3=sorted(reg3_p - rq3_papers), rq3_papers_not_in_registry=sorted(rq3_papers - reg3_p),
      rq3_questions_not_in_registry=len(rq3_q - reg3_q_mapped))

# E5 selection history (stored artifacts, dates from their own metadata)
p3 = ROOT / "eval" / "phases" / "phase_3_embedding" / "artifacts"
hist = {}
for name in ["part2_dev_candidates_results.json", "held_out_final_benchmark_results.json", "expanded_160_papers_benchmark_results.json"]:
    d = load_json(p3 / name)
    hist[name] = {"dataset": d.get("dataset", "Dev 48 papers (part2 candidates)"),
                  "models": d.get("models") or [c.get("model_name") for c in d.get("candidates", []) if isinstance(c, dict)]}
check("RQ3-04", "RQ3", "INFO",
      "E5 selection history: E5 was compared against MiniLM/BGE on the in-house Dev 48, the held-out 48 and the "
      "160-paper held-out cohort before the unified 207-paper RQ3 benchmark pooled the same papers",
      prior_artifacts=hist, rq3_benchmark_date=rq3_bench["metadata"]["date"],
      heldout160_papers_in_rq3=len(ho160 & rq3_papers), dev48_papers_in_rq3=len(dev48 & rq3_papers))

# --- RQ4 ---
rq4 = {}
for split in ("dev", "test"):
    rows = load_jsonl(P_RQ4 / "rq4p_production_fusion" / f"{split}_per_query.jsonl")
    rq4[split] = rows
    papers = {r["paper_arxiv_id"] for r in rows}
    qids = [r["query_id"] for r in rows]
    add_cohort(f"RQ4-{split.upper()}", papers, qids, "recorded",
               [rel(P_RQ4 / "rq4p_production_fusion" / f"{split}_per_query.jsonl"),
                rel(P_RQ4 / f"rq4_qasper_{split}_hierarchical_benchmark.json")],
               note="per-query IDs from the E1 run, whose reproduction gate matched RQ4 to 4 decimals")
    # Independent recount with the RQ4 inclusion rule on the official split
    indep_q = {qa["question_id"] for pid, p in official[split].items() if has_text_sections(p)
               for qa in p.get("qas", []) if rq4_included(qa)}
    per_paper = Counter(r["paper_arxiv_id"] for r in rows)
    all_zero = sorted(r["query_id"] for r in rows
                      if all(r[a]["ndcg10"] == 0 and r[a]["recall20"] == 0 for a in ("dense", "bm25_bench", "rrf_bench", "convex_bench", "bm25_prod", "rrf_prod", "convex_prod")))
    meta = load_json(P_RQ4 / f"rq4_qasper_{split}_hierarchical_benchmark.json")["metadata"]
    check(f"RQ4-{split.upper()}-01", "RQ4",
          "PASS" if (len(qids) == len(set(qids)) == meta["total_queries"] and set(qids) == indep_q
                     and all(paper_split.get(p) == split for p in papers) and all(q_paper.get(q) == r["paper_arxiv_id"] for q, r in zip(qids, rows))) else "FAIL",
          f"RQ4 {split}: per-query IDs vs independent recount of the RQ4 inclusion rule on qasper-{split}-v0.3.json",
          per_query_rows=len(qids), unique_queries=len(set(qids)), papers=len(papers),
          artifact_total_queries=meta["total_queries"], artifact_total_papers=meta["total_papers"],
          independent_recount_queries=len(indep_q), sets_equal=set(qids) == indep_q,
          all_papers_in_declared_split=all(paper_split.get(p) == split for p in papers),
          all_questions_belong_to_recorded_paper=all(q_paper.get(q) == r["paper_arxiv_id"] for q, r in zip(qids, rows)),
          split_papers=len(official[split]), split_papers_without_included_queries=sorted(set(official[split]) - papers),
          queries_per_paper_max=max(per_paper.values()), queries_per_paper_min=min(per_paper.values()),
          queries_per_paper_mean=round(len(qids) / len(papers), 2),
          queries_per_paper_distribution=dict(sorted(Counter(per_paper.values()).items())),
          papers_at_max=sorted(p for p, n in per_paper.items() if n == max(per_paper.values())),
          queries_scoring_zero_in_every_arm=len(all_zero),
          note="R_q is not stored per query, so the 2 Dev queries with no relevant parent cannot be identified by ID "
               "from this file; they are a subset of queries_scoring_zero_in_every_arm" if split == "dev" else "")

# Appendix E reported questions-per-paper (read mechanically from the thesis line)
appx_line = next((ln for ln in THESIS.read_text(encoding="utf-8").splitlines() if "Phân bố câu hỏi/bài" in ln), "")
appx_max = re.findall(r"Max\s*=\s*(\d+)", appx_line)
check("RQ4-03", "RQ4", "FAIL" if appx_max and int(appx_max[0]) != max(Counter(r["paper_arxiv_id"] for r in rq4["dev"]).values()) else "PASS",
      "Appendix E questions-per-paper maximum vs per-query records",
      appendix_e_max_dev_test=[int(x) for x in appx_max],
      records_max_dev=max(Counter(r["paper_arxiv_id"] for r in rq4["dev"]).values()),
      records_max_test=max(Counter(r["paper_arxiv_id"] for r in rq4["test"]).values()))

# --- RQ5 ---
man = load_json(P_RQ5 / "eval_sample_manifest_500q.json")
items = man["selected_eval_items"]
reserve = man["manifest_metadata"]["standby_queue"]
reserve_p = {r["paper_arxiv_id"] for r in reserve}
reserve_q = {q["question_id"] for r in reserve for q in r.get("preselected_questions", [])}
excl = man["exclusion_manifest"]["exclusion_codes_paper_level"]
residual_p = set(excl["RESIDUAL_UNSELECTED_CANDIDATE_PAPERS"]["paper_ids"])
prim_p = {i["paper_arxiv_id"] for i in items}
prim_q = [i["question_id"] for i in items]
add_cohort("RQ5-PRIMARY-250P", prim_p, prim_q, "recorded", [rel(P_RQ5 / "eval_sample_manifest_500q.json")])
add_cohort("RQ5-RESERVE-50P", reserve_p, reserve_q, "recorded", [rel(P_RQ5 / "eval_sample_manifest_500q.json") + " manifest_metadata.standby_queue"],
           note="never evaluated (replacement_log empty)")
add_cohort("RQ5-RESIDUAL-187P", residual_p, [], "recorded", [rel(P_RQ5 / "eval_sample_manifest_500q.json") + " exclusion_manifest"],
           note="eligible candidates not drawn; never evaluated")

per_paper5 = Counter(i["paper_arxiv_id"] for i in items)
bad_ev = [i["question_id"] for i in items if not i.get("ground_truth_evidence")
          or any((e or "").startswith("FLOAT SELECTED") or not (e or "").strip() for e in i["ground_truth_evidence"])]
bad_ref = [i["question_id"] for i in items if not i.get("ground_truth_references")]
not_train = sorted(p for p in prim_p | reserve_p | residual_p if paper_split.get(p) != "train")
q_mismatch = [i["question_id"] for i in items if q_paper.get(i["question_id"]) != i["paper_arxiv_id"]]
check("RQ5-01", "RQ5",
      "PASS" if (len(prim_q) == len(set(prim_q)) == 500 and len(prim_p) == 250 and set(per_paper5.values()) == {2}
                 and not bad_ev and not bad_ref and not not_train and not q_mismatch
                 and not (prim_p & reserve_p) and not (prim_p & residual_p) and not (reserve_p & residual_p)) else "FAIL",
      "RQ5 manifest structure and eligibility",
      items=len(items), unique_questions=len(set(prim_q)), papers=len(prim_p),
      questions_per_paper=dict(Counter(per_paper5.values())),
      items_with_empty_or_float_evidence=bad_ev, items_without_references=bad_ref,
      papers_not_in_official_train=not_train, questions_not_belonging_to_paper=q_mismatch,
      reserve_papers=len(reserve_p), residual_papers=len(residual_p),
      primary_reserve_overlap=len(prim_p & reserve_p), primary_residual_overlap=len(prim_p & residual_p),
      reserve_residual_overlap=len(reserve_p & residual_p),
      replacement_log=man["manifest_metadata"]["replacement_log"],
      question_types=dict(Counter(i["question_type"] for i in items)),
      paper_level_exclusions={k: v["count"] for k, v in excl.items()},
      question_level_exclusions={k: (v["count"] if isinstance(v, dict) else v) for k, v in man["exclusion_manifest"]["exclusion_codes_question_level"].items()})

# Stored generations cover exactly the manifest, for every model
bench5 = load_json(P_RQ5 / "rq5_llm_generation_benchmark_500q.json")
recs = bench5["detailed_records"]
cover = {m: (sorted(r["question_id"] for r in recs[m]) == sorted(prim_q), len(recs[m]),
             sum(1 for r in recs[m] if r.get("error"))) for m in RQ5_MODELS}
check("RQ5-02", "RQ5", "PASS" if all(v[0] for v in cover.values()) else "FAIL",
      "Stored generations: each model has one record per manifest question",
      per_model={m: {"matches_manifest": v[0], "records": v[1], "records_with_error": v[2]} for m, v in cover.items()},
      generation_settings=bench5["metadata"].get("generation_settings"))

# Boolean gold coverage (coverage only; no accuracy computed here)
bool_items = [i for i in items if i["question_type"] == "boolean"]
bool_with_ref = [i for i in bool_items if any(r.get("type") == "boolean" for r in i["ground_truth_references"])]
bool_conflict = [i["question_id"] for i in bool_items
                 if len({r["answer"] for r in i["ground_truth_references"] if r.get("type") == "boolean"}) > 1]
mixed = [i["question_id"] for i in items if len({r.get("type") for r in i["ground_truth_references"]}) > 1]
check("RQ5-03", "RQ5", "INFO", "Boolean gold-label coverage in the 500-question manifest (coverage only)",
      boolean_items=len(bool_items), boolean_items_with_yes_no_reference=len(bool_with_ref),
      boolean_items_with_conflicting_yes_no_annotators=len(bool_conflict), conflicting_ids=bool_conflict,
      items_with_mixed_reference_types=len(mixed), mixed_type_ids=mixed,
      yes_no_distribution=dict(Counter(r["answer"] for i in bool_items for r in i["ground_truth_references"] if r.get("type") == "boolean")))

# Human-review subset
corr_rows = list(csv.DictReader(open(P_REVIEW / "correction" / "faithfulness_annotations_unblinded_corrected.csv", encoding="utf-8")))
hr_q = sorted({r["question_id"] for r in corr_rows})
hr_idx = sorted({int(r["manifest_item_index"]) for r in corr_rows})
samp = load_json(P_REVIEW / "sampling_and_integrity_manifest.json")
add_cohort("RQ5-HUMAN-REVIEW-20Q", {r["paper_arxiv_id"] for r in corr_rows}, hr_q, "recorded",
           [rel(P_REVIEW / "correction" / "faithfulness_annotations_unblinded_corrected.csv"), rel(P_REVIEW / "sampling_and_integrity_manifest.json")])
idx_to_q = {i["item_index"]: i["question_id"] for i in items}
check("RQ5-04", "RQ5",
      "PASS" if (len(hr_q) == 20 and set(hr_q) <= set(prim_q) and hr_idx == list(range(1, 501, 25))
                 and all(idx_to_q[int(r["manifest_item_index"])] == r["question_id"] for r in corr_rows)) else "FAIL",
      "Human-review subset is the stride-25 sample of the primary manifest",
      questions=len(hr_q), answers=len(corr_rows), subset_of_primary=set(hr_q) <= set(prim_q),
      manifest_indices=hr_idx, sampling_manifest_indices=samp["sampling_parameters"]["one_based_manifest_item_indices"])

# Corrected mapping vs stored outputs and the signed sheet (read-only, three-way)
LABELS = ["SUPPORTED", "REFUSAL_VALID", "MISSING_INFO - PARTIAL", "MISSING_INFO - UNJUSTIFIED_REFUSAL", "UNSUPPORTED", "CONTRADICTED"]


def canon_label(s):
    s = s.strip()
    return {"MISSING_INFO - PARTIAL": "PARTIAL", "MISSING_INFO - UNJUSTIFIED_REFUSAL": "UNJUSTIFIED_REFUSAL"}.get(s, s)


sheet = {}
text = (P_RQ5 / "review_and_signed.md").read_text(encoding="utf-8")
for m in re.finditer(r"^##### \[(REV-\d+)\] (Model_\w+):\s*\n(.*?)(?=^##### \[|^### REV-|\Z)", text, re.S | re.M):
    rev, blind, body = m.group(1), m.group(2), m.group(3)
    ans_lines, label = [], None
    for ln in body.splitlines():
        if ln.startswith("- **Primary Label:**"):
            for lab in LABELS:
                if f"[X] {lab}" in ln or f"[x] {lab}" in ln:
                    label = canon_label(lab)
            break
        if ln.startswith(">"):
            ans_lines.append(ln[1:].strip())
    sheet[(rev, blind)] = {"answer": norm_text(" ".join(ans_lines)), "label": label}

stored = {(r["question_id"], m): norm_text(r["prediction"]) for m in RQ5_MODELS for r in recs[m]}
outcome = Counter()
detail = []
groups = {}
for r in corr_rows:
    qid, model, ans = r["question_id"], r["actual_model"], norm_text(r["answer"])
    same = sorted(m for m in RQ5_MODELS if stored.get((qid, m)) == ans)
    s = sheet.get((r["review_id"], r["blind_label_in_signed_sheet"]))
    stored_ok = stored.get((qid, model)) == ans
    sheet_ok = bool(s) and s["answer"] == ans and s["label"] == canon_label(r["original_primary_label"])
    kind = "unmatched" if not stored_ok else ("unique" if len(same) == 1 else "ambiguous_identical_text")
    outcome[kind] += 1
    if not sheet_ok:
        outcome["sheet_mismatch"] += 1
    if kind == "ambiguous_identical_text":
        groups.setdefault((qid, ans), []).append((r["original_primary_label"], r["final_primary_label"]))
    detail.append({"review_id": r["review_id"], "model": model, "match": kind, "models_with_identical_text": same,
                   "signed_sheet_answer_and_label_agree": sheet_ok})
amb_label_conflict = [list(k) for k, v in groups.items() if len(set(v)) > 1]
check("RQ5-05", "RQ5",
      "PASS" if outcome["unmatched"] == 0 and outcome["sheet_mismatch"] == 0 and not amb_label_conflict else "FAIL",
      "Corrected human-review attribution re-verified against stored generations and the signed sheet "
      "(NFKC + whitespace normalisation; question ID + model + answer text)",
      rows=len(corr_rows), signed_sheet_entries_parsed=len(sheet), outcome=dict(outcome),
      ambiguous_groups=len(groups), ambiguous_groups_with_differing_labels=amb_label_conflict,
      final_label_by_model={m: dict(Counter(canon_label(r["final_primary_label"]) for r in corr_rows if r["actual_model"] == m)) for m in RQ5_MODELS},
      adjudicated_changes=sum(1 for r in corr_rows if canon_label(r["final_primary_label"]) != canon_label(r["original_primary_label"])),
      rows_detail=detail)

# Reproduction of thesis-reported RQ5 numbers from stored records (no new statistics)
def pct(values, q):
    v = sorted(values)
    k = (len(v) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return round(sxy / (sxx * syy) ** 0.5, 3) if sxx and syy else None


table56 = {}
for m in RQ5_MODELS:
    rs = recs[m]
    table56[m] = {
        "token_f1": round(sum(r["token_f1"] for r in rs) / len(rs), 4),
        "refusals": sum(1 for r in rs if r["is_refusal"]),
        "containment_mean": round(sum(r["automated_containment_proxy"] for r in rs) / len(rs), 4),
        "latency_p50_s": round(pct([r["latency_s"] for r in rs], 0.5), 2),
        "f1_by_manifest_type": {t: round(sum(r["token_f1"] for r in rs if r["question_type"] == t) / max(1, sum(1 for r in rs if r["question_type"] == t)), 4)
                                for t in ("extractive", "abstractive", "boolean")},
    }
both = [q for q in prim_q if not next(r for r in recs["llama3.2:3b"] if r["question_id"] == q)["is_refusal"]
        and not next(r for r in recs["qwen2.5:0.5b"] if r["question_id"] == q)["is_refusal"]]
f1_of = {(m, r["question_id"]): r["token_f1"] for m in RQ5_MODELS for r in recs[m]}
sup = [1 if canon_label(r["final_primary_label"]) == "SUPPORTED" else 0 for r in corr_rows]
grounded = [1 if canon_label(r["final_primary_label"]) in ("SUPPORTED", "REFUSAL_VALID") else 0 for r in corr_rows]
halluc = [1 if canon_label(r["final_primary_label"]) in ("UNSUPPORTED", "CONTRADICTED") else 0 for r in corr_rows]
f1v = [float(r["token_f1"]) for r in corr_rows]
cpv = [float(r["automated_containment_proxy"]) for r in corr_rows]
refusal_labels = {m: sum(1 for r in corr_rows if r["actual_model"] == m and canon_label(r["final_primary_label"]) in ("REFUSAL_VALID", "UNJUSTIFIED_REFUSAL")) for m in RQ5_MODELS}
refusal_detector = {m: sum(1 for r in corr_rows if r["actual_model"] == m and r["is_refusal"] == "True") for m in RQ5_MODELS}
check("RQ5-07", "RQ5", "INFO", "Thesis RQ5 numbers recomputed from stored records (Table 5.6, 244-question figure, §5.6.5)",
      table_5_6=table56,
      answered_by_both_3b_and_qwen=len(both),
      mean_f1_on_both={"llama3.2:3b": round(sum(f1_of[("llama3.2:3b", q)] for q in both) / len(both), 4),
                       "qwen2.5:0.5b": round(sum(f1_of[("qwen2.5:0.5b", q)] for q in both) / len(both), 4)},
      pearson_supported_vs_f1=pearson(sup, f1v), pearson_supported_vs_containment=pearson(sup, cpv),
      pearson_grounded_vs_f1=pearson(grounded, f1v), pearson_grounded_vs_containment=pearson(grounded, cpv),
      pearson_unsupported_or_contradicted_vs_containment=pearson(halluc, cpv),
      review_refusal_labels_vs_detector={"labels": refusal_labels, "detector": refusal_detector},
      attribution_changed=dict(Counter(r["attribution_changed"] for r in corr_rows)))

# --- RQ5 pilot (non-QASPER seed papers) ---
seed = load_json(ROOT / "backend" / "data" / "eval_benchmark_seed.json")
pilot = load_json(P_RQ5 / "rq5_llm_generation_benchmark.json")
pilot_ids = {r["id"] for r in pilot["llama3.2:3b"]["records"]}
seed_map = {q["id"]: q["paper_arxiv_id"] for q in seed}
pilot_p = {seed_map[i] for i in pilot_ids if i in seed_map}
add_cohort("RQ5-PILOT-16Q", pilot_p, pilot_ids, "recorded",
           [rel(P_RQ5 / "rq5_llm_generation_benchmark.json"), "backend/data/eval_benchmark_seed.json"], q_namespace="seed_ids")
check("RQ5-06", "RQ5", "INFO", "Pilot seed papers: official QASPER split membership as found",
      questions=len(pilot_ids), papers=sorted(pilot_p),
      split_membership={p: paper_split.get(p, "not in QASPER v0.3") for p in sorted(pilot_p)})

# --- Train residual: two definitions ---
train = set(official["train"])
evented = {pid for pid, v in reg["paper_index"].items() if v.get("exposure_events")}
all_cohort_papers = set().union(*(c["papers"] for n, c in cohorts.items() if not n.startswith("QASPER-")
                                  and n not in ("RQ5-RESERVE-50P", "RQ5-RESIDUAL-187P")))
def_a = train - prim_p - reserve_p
def_b = train - all_cohort_papers - evented
legacy_true = {pid for pid, v in reg["paper_index"].items() if v.get("is_unexposed_to_repository_experiments")}
add_cohort("TRAIN-UNUSED-DEF-B", def_b, [], "reconstructed", ["official Train minus every audited cohort and every registry event"])

# --- Revalidation cohorts (2026-10-30), if built ---
REVAL_DIR = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "revalidation"
NEVER_EVALUATED = ("TRAIN-UNUSED-DEF-B", "RQ5-RESERVE-50P", "RQ5-RESIDUAL-187P")  # sampling pools, no outputs
historical = [n for n in cohorts if not n.startswith("QASPER-") and n not in NEVER_EVALUATED]
new_names = []
for name in ("C-INT", "C-RET", "C-RET-150", "PEERQA-PDF", "PEERQA-TEXT"):
    p = REVAL_DIR / f"cohort_{name}.json"
    if p.exists():
        c = load_json(p)
        add_cohort(f"REVAL-{name}", c["papers"], [i["question_id"] for i in c["items"]], "recorded", [rel(p)],
                   q_namespace="peerqa" if name.startswith("PEERQA") else "qasper_hash")
        new_names.append(f"REVAL-{name}")
if new_names:
    clash = {f"{n} & {h}": (len(cohorts[n]["papers"] & cohorts[h]["papers"]), len(cohorts[n]["questions"] & cohorts[h]["questions"]))
             for n in new_names for h in historical}
    clash = {k: v for k, v in clash.items() if v != (0, 0)}
    internal = len(cohorts["REVAL-C-INT"]["papers"] & cohorts["REVAL-C-RET"]["papers"]) if "REVAL-C-INT" in cohorts else None
    check("REVAL-01", "revalidation", "PASS" if not clash and not internal else "FAIL",
          "Revalidation cohorts vs every historical cohort (paper and question overlap must be zero); C-INT vs C-RET disjoint",
          cohorts={n: {"papers": len(cohorts[n]["papers"]), "questions": len(cohorts[n]["questions"])} for n in new_names},
          nonzero_overlaps_with_historical=clash, c_int_c_ret_paper_overlap=internal,
          info_overlap_with_never_evaluated_rq5_pools={f"{n} & {h}": len(cohorts[n]["papers"] & cohorts[h]["papers"])
                                                       for n in new_names for h in ("RQ5-RESERVE-50P", "RQ5-RESIDUAL-187P")},
          all_qasper_new_papers_in_train=all(paper_split.get(p) == "train" for n in new_names if not n.startswith("REVAL-PEERQA")
                                             for p in cohorts[n]["papers"]))
check("RES-01", "RQ5", "INFO",
      "Train residual under two definitions (527 treated as a hypothesis)",
      train_papers=len(train),
      def_a_train_outside_rq5_primary_and_reserve=len(def_a),
      def_b_train_with_no_event_and_in_no_audited_cohort=len(def_b),
      def_a_minus_def_b=len(def_a - def_b),
      breakdown_of_difference={
          "rq3_train_papers": len((def_a - def_b) & rq3_papers),
          "other": sorted((def_a - def_b) - rq3_papers)[:20]},
      def_b_composition={"residual_candidates_187": len(def_b & residual_p),
                         "single_eligible_226": len(def_b & set(excl["EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS"]["paper_ids"])),
                         "zero_eligible_64": len(def_b & set(excl["EXCL_ZERO_ELIGIBLE_QUESTIONS"]["paper_ids"]))},
      reserve_papers_have_registry_events=len(reserve_p & evented),
      def_b_papers_with_legacy_flag_true=len(def_b & legacy_true),
      train_papers_missing_from_registry=sorted(train - set(reg["paper_index"]))[:20])

# --- Registry consistency ---
ev_counter = Counter(e["experiment_id"] for v in reg["paper_index"].values() for e in v.get("exposure_events", []))
rq5_events = {pid for pid, v in reg["paper_index"].items() if any(e["experiment_id"] == "EXP-RQ5-MAIN-SAMPLED" for e in v.get("exposure_events", []))}
rq5_hr_events = {pid for pid, v in reg["paper_index"].items() if any(e.get("role") == "HUMAN_FAITHFULNESS_REVIEW" for e in v.get("exposure_events", []))}
stale = sorted(p for p in rq5_events if reg["paper_index"][p].get("is_unexposed_to_repository_experiments"))
check("REG-01", "all", "PASS" if rq5_events == prim_p and rq5_hr_events == cohorts["RQ5-HUMAN-REVIEW-20Q"]["papers"] else "FAIL",
      "Registry exposure events vs primary cohorts (E0 verification)",
      events_by_experiment=dict(sorted(ev_counter.items())),
      rq5_event_papers_equal_primary=rq5_events == prim_p,
      human_review_event_papers_equal_review_subset=rq5_hr_events == cohorts["RQ5-HUMAN-REVIEW-20Q"]["papers"],
      papers_with_events_but_legacy_flag_true=len(stale),
      registry_papers_per_experiment={k: len(v.get("paper_ids", [])) for k, v in reg_exp.items()},
      registry_questions_per_experiment={k: len(v.get("question_ids", [])) for k, v in reg_exp.items()},
      rq4_dev_event_papers_equal_records=({p for p, v in reg["paper_index"].items() if any(e["experiment_id"] == "EXP-RQ4-HYBRID-DEV" for e in v["exposure_events"])} == cohorts["RQ4-DEV"]["papers"]),
      rq4_test_event_papers_equal_records=({p for p, v in reg["paper_index"].items() if any(e["experiment_id"] == "EXP-RQ4-HYBRID-TEST" for e in v["exposure_events"])} == cohorts["RQ4-TEST"]["papers"]))

consumers = []
for p in sorted((ROOT / "eval").rglob("*.py")) + sorted((ROOT / "backend" / "scripts").rglob("*.py")):
    if "venv" in p.parts or "__pycache__" in p.parts:
        continue
    for n, ln in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if "is_unexposed_to_repository_experiments" in ln:
            consumers.append(f"{rel(p)}:{n}")
check("REG-02", "all", "INFO",
      "Code that reads or writes the legacy flag is_unexposed_to_repository_experiments",
      occurrences=consumers,
      note="check_experiment_overlap.py treats a paper as unexposed only if it has no events AND the flag is true, "
           "so a recorded event always wins; a paper with no events and flag false is reported exposed (conservative)")

# ---------------------------------------------------------------------------
# 3. Overlap matrix (detection only, no leakage labels)
# ---------------------------------------------------------------------------
names = sorted(cohorts)
overlap_rows = []
overlap_ids = {}
for a, b in combinations(names, 2):
    ca, cb = cohorts[a], cohorts[b]
    pi = sorted(ca["papers"] & cb["papers"])
    same_ns = ca["q_namespace"] == cb["q_namespace"] and ca["questions"] and cb["questions"]
    qi = sorted(ca["questions"] & cb["questions"]) if same_ns else None
    overlap_rows.append({
        "cohort_a": a, "cohort_b": b,
        "papers_a": len(ca["papers"]), "papers_b": len(cb["papers"]), "paper_overlap": len(pi),
        "questions_a": len(ca["questions"]), "questions_b": len(cb["questions"]),
        "question_overlap": len(qi) if qi is not None else "n/a",
        "membership_a": ca["membership"], "membership_b": cb["membership"],
        "example_paper_ids": " ".join(pi[:20]),
        "example_question_ids": " ".join(qi[:20]) if qi else "",
    })
    if pi or qi:
        overlap_ids[f"{a} & {b}"] = {"papers": pi, "questions": qi or []}

# ---------------------------------------------------------------------------
# 4. Ledger (counts from this script; qualitative fields from code reading)
# ---------------------------------------------------------------------------
LEDGER_TEXT = {
    "QASPER-TRAIN": dict(source="AllenAI QASPER v0.3 official release", inclusion="all papers in release", split="official train (paper level)",
                         seed="n/a", unit="n/a", ground_truth="QASPER crowd annotations (answers + evidence)",
                         usage="RQ3 (111 papers), RQ5 sample (250), reserve/residual pools", claims="§5.1 EDA; §5.4; §5.6"),
    "QASPER-DEV": dict(source="AllenAI QASPER v0.3 official release", inclusion="all papers in release", split="official dev (paper level)",
                       seed="n/a", unit="n/a", ground_truth="QASPER crowd annotations", usage="RQ1-RQ3 in-house cohorts; RQ4 Dev (configuration/diagnostics); E1",
                       claims="§5.1 EDA; §5.2-§5.5"),
    "QASPER-TEST": dict(source="AllenAI QASPER v0.3 official release", inclusion="all papers in release", split="official test (paper level)",
                        seed="n/a", unit="n/a", ground_truth="QASPER crowd annotations", usage="RQ4 Test (final evaluation), then E1 (post-selection diagnostic)",
                        claims="§5.5; Appendix E"),
    "PILOT-SAMPLE-96P": dict(source="eval/prepared, seeded sample of QASPER Dev (prepare_qasper.py)", inclusion="250 sampled questions incl. unanswerable",
                             split="all official Dev", seed="42 (sample_ids.json)", unit="question", ground_truth="QASPER evidence; tau containment",
                             usage="source pool for in-house Dev 48 / held-out 48; EDA pilot", claims="§5.1 (pilot EDA)"),
    "RQ1-47P": dict(source="QASPER Dev papers with arXiv PDFs", inclusion="in-house dev_papers (48) with a PDF > 10 kB on disk; unanswerable questions dropped",
                    split="official dev; in-house 'Dev' partition", seed="42", unit="paper (extraction metrics); query nested in paper (nDCG)",
                    ground_truth="QASPER JSON full text (headings/paragraphs) as extraction reference; evidence containment tau=0.50 for nDCG",
                    usage="configuration selection (extractor default)", claims="§5.2, Table 5.2; abstract; Ch.6"),
    "RQ2-47P": dict(source="same cohort as RQ1 (PDF -> pymupdf_layout sections)", inclusion="as RQ1",
                    split="official dev; in-house 'Dev' partition", seed="42", unit="query nested in paper; bootstrap resamples papers",
                    ground_truth="evidence containment tau=0.50 per strategy's own unit (sensitivity 0.30)",
                    usage="configuration selection (chunker default)", claims="§5.3, Table 5.3; abstract; Ch.6"),
    "RQ3-DEV-48P": dict(source="in-house Dev partition (dev_held_out_split.json) on QASPER JSON text", inclusion="non-unanswerable; paper has text",
                        split="official dev", seed="42", unit="query nested in paper", ground_truth="containment tau*=0.55",
                        usage="earlier model screening (part2) and part of the RQ3 207 corpus", claims="§5.4"),
    "RQ3-HELDOUT-160P": dict(source="expanded_held_out_split.json (48 first held-out + 112 Train papers)", inclusion="non-unanswerable; paper has text (1 paper has no scored query)",
                             split="mixed official dev/train", seed="42", unit="query nested in paper", ground_truth="containment tau*=0.55",
                             usage="earlier E5 vs BGE/MiniLM confirmation (expanded_160 benchmark) and part of the RQ3 207 corpus", claims="§5.4"),
    "RQ3-207P": dict(source="union of RQ3 Dev 48 and held-out 159 on QASPER JSON text (not PDF extraction)", inclusion="as parts",
                     split="official dev + train, 0 test", seed="42", unit="query nested in paper; paper-cluster bootstrap B=2000",
                     ground_truth="containment tau*=0.55 (fresh-set precision 58.3%, n=34)", usage="final RQ3 ranking (same papers as earlier selection rounds)",
                     claims="§5.4, Tables 5.4-5.5; abstract; Ch.6"),
    "INHOUSE-HELDOUT-48P": dict(source="dev_held_out_split.json held_out_papers", inclusion="as RQ3", split="official dev",
                                seed="42", unit="query nested in paper", ground_truth="containment tau*=0.55",
                                usage="early 'pre-registered' held-out E5 check; frozen_cohort_1 of the 160", claims="none directly"),
    "RQ4-DEV": dict(source="QASPER v0.3 dev full_text JSON", inclusion=">=1 non-unanswerable annotation with non-FLOAT text evidence; paper has >=1 chunk",
                    split="official dev", seed="42", unit="query nested in paper; paper-cluster bootstrap B=2000",
                    ground_truth="containment tau=0.50 over unique parent sections; R_q floored at 1",
                    usage="configuration check (descriptive); E1 direction check and alpha sweep", claims="§5.5; Appendix E"),
    "RQ4-TEST": dict(source="QASPER v0.3 test full_text JSON", inclusion="as RQ4 Dev", split="official test", seed="42",
                     unit="query nested in paper; paper-cluster bootstrap B=2000, Holm m=3",
                     ground_truth="containment tau=0.50 over parents", usage="RQ4 final evaluation; reused by E1 (post-selection)", claims="§5.5, Table 5.5; Appendix E; abstract"),
    "RQ5-PRIMARY-250P": dict(source="QASPER v0.3 train, papers unused by RQ1-RQ4 at sampling time", inclusion="atomic joint grounding: one annotation with usable answer AND non-FLOAT text evidence; paper needs >=2 eligible",
                             split="official train", seed="42 (per-paper sub-seeds)", unit="question nested in paper; paper-level paired t (df=249) + Holm; bootstrap B=2000",
                             ground_truth="QASPER reference answers (max over annotators); gold evidence given as context", usage="final evaluation of 3 SLMs (generator only)",
                             claims="§5.6, Tables 5.6-5.7; abstract; Ch.6"),
    "RQ5-RESERVE-50P": dict(source="manifest standby queue", inclusion="as primary", split="official train", seed="42", unit="n/a",
                            ground_truth="n/a", usage="never used (replacement_log empty)", claims="none"),
    "RQ5-RESIDUAL-187P": dict(source="manifest exclusion list", inclusion="eligible (>=2) but not drawn", split="official train", seed="42",
                              unit="n/a", ground_truth="n/a", usage="never used", claims="none"),
    "RQ5-HUMAN-REVIEW-20Q": dict(source="stride-25 subset of RQ5 primary", inclusion="items 1,26,...,476", split="official train", seed="42 (blinding)",
                                 unit="answer (60) nested in question (20); single reviewer", ground_truth="one human reviewer, 6-label rubric; adjudicated; attribution corrected 2026-10-29",
                                 usage="exploratory faithfulness audit", claims="§5.6.x human audit; Ch.6"),
    "RQ5-PILOT-16Q": dict(source="backend/data/eval_benchmark_seed.json (hand-written questions on 4 famous papers)", inclusion="all 16",
                          split="not QASPER", seed="n/a", unit="question", ground_truth="hand-written answers/quotes",
                          usage="harness smoke test (preliminary)", claims="should not support any thesis claim"),
    "TAU-LABELS-115PAIRS": dict(source="(question, chunk) pairs from the in-house Dev 48, hand-labelled relevant / not relevant",
                                inclusion="80 calibration pairs + 35 fresh pairs (34 after sanitising)", split="official dev",
                                seed="not recorded", unit="pair", ground_truth="single labeller (no agreement statistic recorded)",
                                usage="choice of tau*=0.55 (RQ3) and tau=0.50 (RQ1/RQ2/RQ4)", claims="§3.x relevance definition; §5.2-§5.5"),
    "TRAIN-UNUSED-DEF-B": dict(source="derived", inclusion="official Train with no registry event and in no audited cohort", split="official train",
                               seed="n/a", unit="n/a", ground_truth="n/a", usage="available for a future fresh sample", claims="none"),
}

ledger_rows = []
for n in names:
    c = cohorts[n]
    t = LEDGER_TEXT.get(n, {})
    extra = {}
    if n == "RQ3-207P":
        extra = {"chunks": "5,207 claimed (4,108 held-out verified in expanded_160_chunks.json; 1,099 dev not recomputed)"}
    elif n == "RQ3-HELDOUT-160P":
        extra = {"chunks": str(len(exp_chunks))}
    elif n.startswith("RQ4-"):
        extra = {"chunks": str(load_json(P_RQ4 / f"rq4_qasper_{n[4:].lower()}_hierarchical_benchmark.json")["metadata"]["total_chunks"]) + " (artifact metadata)"}
    elif n in ("RQ1-47P", "RQ2-47P"):
        extra = {"chunks": "per strategy (RQ2 artifact)" if n == "RQ2-47P" else "n/a"}
    ledger_rows.append({
        "cohort": n,
        "dataset_source": t.get("source", ""),
        "artifacts": "; ".join(c["sources"]),
        "membership_status": c["membership"],
        "papers": len(c["papers"]),
        "questions": len(c["questions"]) if c["questions"] else "not recorded",
        "question_id_namespace": c["q_namespace"],
        "official_split_composition": " ".join(f"{k}:{v}" for k, v in sorted(Counter(paper_split.get(p, "non_qasper") for p in c["papers"]).items())),
        "chunks": extra.get("chunks", "n/a"),
        "inclusion_exclusion": t.get("inclusion", "unknown"),
        "split_and_unit": t.get("split", "unknown"),
        "seed_sampling": t.get("seed", "unknown"),
        "evaluation_and_resampling_unit": t.get("unit", "unknown"),
        "ground_truth": t.get("ground_truth", "unknown"),
        "usage": t.get("usage", "unknown"),
        "dependent_claims": t.get("claims", "unknown"),
        "note": c.get("note", ""),
    })

# ---------------------------------------------------------------------------
# 5. Write outputs (sorted, no timestamps)
# ---------------------------------------------------------------------------
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "cross_rq_audit_checks.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump({"checks": CHECKS,
               "summary": dict(Counter(c["status"] for c in CHECKS))}, f, indent=2, ensure_ascii=False, sort_keys=True)
with open(OUT / "cross_rq_audit_ids.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump({"cohorts": {n: {"membership": c["membership"], "sources": c["sources"], "q_namespace": c["q_namespace"],
                               "papers": sorted(c["papers"]), "questions": sorted(c["questions"])} for n, c in sorted(cohorts.items())},
               "overlaps": overlap_ids,
               "train_residual": {"def_a": sorted(def_a), "def_b": sorted(def_b)}},
              f, indent=1, ensure_ascii=False, sort_keys=True)
for fname, rows in (("CROSS_RQ_DATASET_LEDGER.csv", ledger_rows), ("CROSS_RQ_OVERLAP_MATRIX.csv", overlap_rows)):
    with open(OUT / fname, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

print(f"checks: {dict(Counter(c['status'] for c in CHECKS))}; cohorts: {len(cohorts)}; overlap pairs: {len(overlap_rows)}")
for c in CHECKS:
    print(f"  [{c['status']}] {c['id']}: {c['summary'][:110]}")
