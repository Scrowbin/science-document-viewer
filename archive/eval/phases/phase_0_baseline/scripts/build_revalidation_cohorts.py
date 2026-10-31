#!/usr/bin/env python3
"""
Builds and registers the revalidation cohorts (Phase B2). Seed 42. Run after version_check_extract.py.

Population: QASPER v0.3 Train papers with NO exposure event in the provenance registry (read from
exposure_events, not the legacy is_unexposed flag) whose PDF passed the version check.

  C-INT      100 papers with >= 2 atomically eligible questions (RQ5 rule); 2 questions per paper.
             Role: CONFIRMATION (RQ6 only). Drawn first so that nothing else touches it.
  C-RET      every other kept paper with >= 1 retrieval-eligible question (RQ4 rule); all such questions.
             Role: SELECTION (RQ1-RQ4 winners chosen here with pre-declared rules).
  C-RET-150  seeded 150-paper subset of C-RET (RQ3 embedding shortlist).
  PEERQA     PeerQA papers that passed the version check; answerable questions with evidence.
             Role: DESCRIPTIVE external check (RQ1, RQ4, RQ6).

Writes eval/phases/phase_0_baseline/artifacts/revalidation/cohort_<name>.json (with SHA-256 of the
membership) and appends (never overwrites) entries to eval/experiment_provenance_registry.json.
"""

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "revalidation"
REGISTRY = ROOT / "eval" / "experiment_provenance_registry.json"
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))
from eval_common.revalidation import peerqa_evidence, qasper_text_evidence  # noqa: E402
from generate_sample_manifest_250 import is_atomic_eligible  # noqa: E402

SEED = 42
N_INT = 100
M_INT = 2
N_RET150 = 150


def membership_hash(papers, questions):
    payload = json.dumps({"papers": sorted(papers), "questions": sorted(questions)}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_cohort(name, role, papers, items, extra):
    qids = [it["question_id"] for it in items]
    doc = {"cohort": name, "role": role, "seed": SEED, "n_papers": len(papers), "n_questions": len(qids),
           "membership_sha256": membership_hash(papers, qids), **extra,
           "papers": sorted(papers), "items": items}
    ART.mkdir(parents=True, exist_ok=True)
    (ART / f"cohort_{name}.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--register", action="store_true", help="append cohorts to the provenance registry")
    args = ap.parse_args()

    reg = json.load(open(REGISTRY, encoding="utf-8"))
    train = json.load(open(ROOT / "eval/data/qasper_official/qasper-train-v0.3.json", encoding="utf-8"))
    vc = json.load(open(ART / "version_check_reservoir.json", encoding="utf-8"))["papers"]

    kept = sorted(p for p, d in vc.items() if d["kept"]
                  and not reg["paper_index"].get(p, {}).get("exposure_events"))
    retr, atomic = {}, {}
    for p in kept:
        retr[p] = [qa for qa in train[p]["qas"] if qasper_text_evidence(qa)]
        atomic[p] = [qa for qa in train[p]["qas"] if is_atomic_eligible(qa)[0]]

    rng = random.Random(SEED)
    int_pool = sorted(p for p in kept if len(atomic[p]) >= M_INT)
    c_int = sorted(rng.sample(int_pool, min(N_INT, len(int_pool))))
    int_items = []
    for p in c_int:
        prng = random.Random(f"{SEED}-{p}")
        for qa in sorted(prng.sample(sorted(atomic[p], key=lambda q: q["question_id"]), M_INT), key=lambda q: q["question_id"]):
            _, refs, ev = is_atomic_eligible(qa)
            int_items.append({"paper_arxiv_id": p, "question_id": qa["question_id"], "question": qa["question"],
                              "pdf_version": vc[p]["version"], "references": refs,
                              "question_type": refs[0]["type"], "gold_evidence": ev,
                              "retrieval_evidence": qasper_text_evidence(qa)})

    c_ret = sorted(p for p in kept if p not in c_int and retr[p])
    ret_items = [{"paper_arxiv_id": p, "question_id": qa["question_id"], "question": qa["question"],
                  "pdf_version": vc[p]["version"], "retrieval_evidence": qasper_text_evidence(qa)}
                 for p in c_ret for qa in retr[p]]
    c_ret150 = sorted(random.Random(f"{SEED}-ret150").sample(c_ret, min(N_RET150, len(c_ret))))
    ret150_items = [it for it in ret_items if it["paper_arxiv_id"] in set(c_ret150)]

    common = {"population": "QASPER v0.3 Train, no registry exposure event, PDF kept by version check",
              "version_check": "eval/phases/phase_0_baseline/artifacts/revalidation/version_check_reservoir.json",
              "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    docs = {
        "C-INT": write_cohort("C-INT", "CONFIRMATION (RQ6 only; never used for tuning)", c_int, int_items,
                              {**common, "rule": f"{N_INT} papers with >= {M_INT} atomically eligible questions; {M_INT} per paper"}),
        "C-RET": write_cohort("C-RET", "SELECTION (RQ1-RQ4)", c_ret, ret_items,
                              {**common, "rule": "all remaining kept papers; all retrieval-eligible questions"}),
        "C-RET-150": write_cohort("C-RET-150", "SELECTION (RQ3 shortlist)", c_ret150, ret150_items,
                                  {**common, "rule": f"seeded {N_RET150}-paper subset of C-RET"}),
    }

    # PeerQA (descriptive). OpenReview PDFs could not be obtained (human challenge on all automated access;
    # manual browser download also failed), so: PEERQA-PDF = papers with an obtainable PDF (EGU) that pass the
    # version check; PEERQA-TEXT = papers whose text ships in papers.jsonl (no PDF; retrieval check only).
    qa = [json.loads(line) for line in open(ROOT / "eval/data/peerqa/raw/qa.jsonl", encoding="utf-8")]
    eligible = [q for q in qa if q.get("answerable") is True and peerqa_evidence(q)]
    peer_meta = {"license": "CC BY-NC-SA 4.0 (README in peerqa-data-v1.0.zip); non-commercial research use",
                 "population": "PeerQA v1.0; answerable (authors' label) with evidence sentences"}

    def peer_items(papers):
        return [{"paper_id": q["paper_id"], "question_id": q["question_id"], "question": q["question"],
                 "answer_free_form": q.get("answer_free_form"), "retrieval_evidence": peerqa_evidence(q)}
                for q in eligible if q["paper_id"] in papers]

    peer_vc_path = ART / "version_check_peerqa.json"
    if peer_vc_path.exists():
        pk = {p for p, d in json.load(open(peer_vc_path, encoding="utf-8"))["papers"].items() if d["kept"]}
        items = peer_items(pk)
        docs["PEERQA-PDF"] = write_cohort("PEERQA-PDF", "DESCRIPTIVE external check (RQ1, RQ4, RQ6)",
                                          sorted({i["paper_id"] for i in items}), items, peer_meta)
    text_papers = {json.loads(line)["paper_id"] for line in open(ROOT / "eval/data/peerqa/raw/papers.jsonl", encoding="utf-8")}
    items = peer_items(text_papers)
    docs["PEERQA-TEXT"] = write_cohort("PEERQA-TEXT", "DESCRIPTIVE external retrieval check on shipped text (RQ4)",
                                       sorted({i["paper_id"] for i in items}), items,
                                       {**peer_meta, "text_source": "papers.jsonl (GROBID text shipped by the authors; no PDF extraction)"})

    overlap = {f"{a} & {b}": len(set(docs[a]["papers"]) & set(docs[b]["papers"]))
               for a, b in (("C-INT", "C-RET"), ("C-INT", "C-RET-150"))}
    summary = {k: {"papers": v["n_papers"], "questions": v["n_questions"], "sha256": v["membership_sha256"]}
               for k, v in docs.items()}
    print(json.dumps({"cohorts": summary, "overlap": overlap,
                      "c_int_question_types": {t: sum(1 for i in int_items if i["question_type"] == t)
                                               for t in ("extractive", "abstractive", "boolean")}}, indent=1))

    if args.register:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        exps = {
            "EXP-REVAL-SELECTION-CRET": ("C-RET", "SELECTION", "RQ1-RQ4 revalidation (one component varied at a time)"),
            "EXP-REVAL-RQ6-CINT": ("C-INT", "CONFIRMATION", "RQ6 integrated end-to-end evaluation"),
        }
        if "PEERQA-PDF" in docs:
            exps["EXP-REVAL-PEERQA-PDF"] = ("PEERQA-PDF", "DESCRIPTIVE", "External descriptive check on PeerQA PDFs (RQ1, RQ4, RQ6)")
        exps["EXP-REVAL-PEERQA-TEXT"] = ("PEERQA-TEXT", "DESCRIPTIVE", "External descriptive retrieval check on PeerQA shipped text (RQ4)")
        for exp_id, (cohort, role, purpose) in exps.items():
            d = docs[cohort]
            reg["registered_experiments"][exp_id] = {
                "experiment_id": exp_id, "phase": "REVALIDATION", "experiment_name": purpose,
                "date": now[:10], "status": "REGISTERED_PLANNED", "dataset_name": d.get("population"),
                "source_manifest": f"eval/phases/phase_0_baseline/artifacts/revalidation/cohort_{cohort}.json",
                "membership_sha256": d["membership_sha256"], "paper_count": d["n_papers"],
                "question_count": d["n_questions"], "paper_ids": d["papers"],
                "question_ids": [i["question_id"] for i in d["items"]], "evaluation_purpose": role,
            }
        for cohort, exp_id, role in (("C-RET", "EXP-REVAL-SELECTION-CRET", "SELECTION_RQ1_RQ4"),
                                     ("C-INT", "EXP-REVAL-RQ6-CINT", "CONFIRMATION_RQ6")):
            for p in docs[cohort]["papers"]:
                reg["paper_index"][p].setdefault("exposure_events", []).append({
                    "experiment_id": exp_id, "phase": "REVALIDATION", "role": role, "outputs_inspected": False,
                    "influenced_decision": "planned", "classification": "PLANNED_REGISTERED", "recorded_on": now})
        reg.setdefault("audit_corrections", []).append({
            "date": now[:10], "experiment_id": "EXP-REVALIDATION-COHORTS",
            "note": "Revalidation cohorts registered before any scoring (append-only). " + json.dumps(summary)})
        REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        print("registry updated")


if __name__ == "__main__":
    main()
