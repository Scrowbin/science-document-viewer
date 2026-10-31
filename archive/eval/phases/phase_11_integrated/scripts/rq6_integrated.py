#!/usr/bin/env python3
"""
RQ6: integrated end-to-end evaluation through the production code path (pre-registered template:
reports/revalidation/protocol/rq5_rq6.json "RQ6_template"; filled config: reports/revalidation/protocol/rq6_config.json,
hashed into the registry before this runs).

Per paper: apps.documents.services.rag_service.ingest_document (temporary Qdrant path) once per distinct
(extractor, chunker, embedder). Per question and condition: rag_service.query_document (hybrid_search(mode) ->
0.80 dense gate -> production prompt -> Ollama, temperature 0). GOLD: gold evidence through the same production
prompt (build_answer_prompt), no gate.

Startup check (aborts on mismatch): the config file's SHA-256 equals the hash recorded in the registry, and the
live Django settings equal the config's NEW system (retrieval mode, chunker, embedder, gate, temperature, model).

Scoring: max-over-annotator Token F1 (QASPER) or Token F1 vs the free-form answer (PeerQA); any refusal (gate or
model) scores 0. Also: Boolean accuracy, gate vs model refusals, CEC@0.5 of the retrieved context, context tokens,
per-stage latency (ingest, retrieve, generate, end-to-end), Python and Ollama-tree memory, failure counts
(Ollama returned nothing -> production's snippet fallback answer; scored as returned and flagged).

Usage:
  python rq6_integrated.py --cohort C-INT                    (confirmatory run; once)
  python rq6_integrated.py --cohort PEERQA-PDF               (descriptive secondary)
  python rq6_integrated.py --cohort C-RET --limit 2          (smoke test; never C-INT)
Output: eval/phases/phase_11_integrated/artifacts/rq6_<cohort>[/smoke_N]/  (resumable checkpoint.jsonl)
"""

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))
from eval_common import reval_pipeline as rp  # noqa: E402
from eval_common import reval_runner as rr  # noqa: E402

rp.setup_django()
from django.conf import settings  # noqa: E402

from eval_common.revalidation import context_evidence_coverage  # noqa: E402
from evaluate_rq5_llm_generation import compute_token_f1, score_prediction_max_annotator  # noqa: E402
from rq5_reanalysis import wilson, yes_no  # noqa: E402
from rq5_resource_profile import TreeSampler, unload_all  # noqa: E402

CONFIG = ROOT / "reports" / "revalidation" / "protocol" / "rq6_config.json"
REGISTRY = ROOT / "eval" / "experiment_provenance_registry.json"
ART = ROOT / "eval" / "phases" / "phase_11_integrated" / "artifacts"
QDRANT_DIR = ROOT / "eval" / "data" / "revalidation_cache" / "rq6_qdrant"
QASPER_TRAIN = ROOT / "eval" / "data" / "qasper_official" / "qasper-train-v0.3.json"
DOC_ID_BASE = 9_100_000  # far above any app document id; ingestion never writes to the database
REFUSAL = "The document does not contain sufficient relevant information to answer this question."


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_config(cfg):
    """Config hash must equal the latest registry record; live settings must equal the NEW system."""
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    rel = str(CONFIG.relative_to(ROOT)).replace("\\", "/")
    recorded = [v["files"][rel] for v in reg["registered_experiments"]["EXP-REVALIDATION-PROTOCOL"]["versions"]
                if rel in v["files"]]
    if not recorded or recorded[-1] != sha256(CONFIG):
        raise SystemExit(f"ABORT: {rel} hash does not match the registry record")
    new = cfg["systems"]["NEW"]
    live = {
        "retrieval_mode": settings.RAG_RETRIEVAL_MODE,
        "chunker": settings.CHUNKING_STRATEGY,
        "embedder": settings.EMBEDDING_MODEL,
        "gate_min_dense_score": settings.RAG_MIN_SIMILARITY_SCORE,
        "temperature": settings.OLLAMA_TEMPERATURE,
        "default_llm": settings.OLLAMA_MODEL,
        "ollama_timeout_s": settings.OLLAMA_TIMEOUT,
        "context_budget_tokens": getattr(settings, "RAG_CONTEXT_BUDGET", 1600),
        "max_parent_tokens": getattr(settings, "RAG_MAX_PARENT_TOKENS", 800),
    }
    diff = {k: (live[k], new[k]) for k in live if live[k] != new.get(k)}
    if diff:
        raise SystemExit(f"ABORT: production settings differ from rq6_config NEW: {diff}")
    return live


def load_items(cohort, limit):
    c = rr.load_cohort(cohort)
    groups = rr.group_items(c)
    pids = list(groups)[:limit] if limit else list(groups)
    titles = {}
    if cohort != "PEERQA-PDF":
        train = json.load(open(QASPER_TRAIN, encoding="utf-8"))
        titles = {p: train[p]["title"] for p in pids if p in train}
    return c, [(p, groups[p]) for p in pids], titles


def references(cohort, it):
    if cohort == "PEERQA-PDF":
        # Author-written answer; 107 of the 288 PeerQA questions have none (scored only in the sensitivity check)
        return [{"answer": it["answer_free_form"], "type": "free_form"}] if it.get("answer_free_form") else []
    return it["references"]


def peerqa_augmented():
    """PeerQA's released generated answers (qa-augmented-answers.jsonl), one per question; sensitivity only."""
    path = ROOT / "eval" / "data" / "peerqa" / "raw" / "qa-augmented-answers.jsonl"
    return {r["question_id"]: r["augmented_answer_free_form"]
            for r in (json.loads(line) for line in open(path, encoding="utf-8"))}


def gold_docs(cohort, it):
    from langchain_core.documents import Document
    ev = it["retrieval_evidence"] if cohort == "PEERQA-PDF" else it["gold_evidence"]
    return [Document(page_content=e, metadata={}) for e in ev]


def is_refusal(text):
    t = (text or "").lower()
    return REFUSAL.lower() in t or "does not contain sufficient" in t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True, choices=["C-INT", "PEERQA-PDF", "C-RET"])
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.cohort == "C-RET" and not a.limit:
        raise SystemExit("C-RET is only for smoke tests (--limit)")
    if a.cohort == "C-INT" and a.limit:
        raise SystemExit("no smoke tests on C-INT")

    cfg = json.load(open(CONFIG, encoding="utf-8"))
    live = verify_config(cfg)
    conditions = cfg["conditions"]["PEERQA-PDF" if a.cohort == "PEERQA-PDF" else "C-INT"]
    out = ART / f"rq6_{a.cohort}" / (f"smoke_{a.limit}" if a.limit else "")
    out.mkdir(parents=True, exist_ok=True)

    # Temporary Qdrant store for this run (production code, separate path)
    settings.QDRANT_STORAGE_PATH = str(QDRANT_DIR / (a.cohort + (f"_smoke{a.limit}" if a.limit else "")))
    from apps.documents.services import rag_service as rs
    rs.RagService.reset_instance()
    rs._rag_instances.clear()

    # Instrument production functions (timing + captured context); behaviour unchanged
    stage: dict = {}
    orig_search, orig_gen = rs.DocumentRAG.hybrid_search, rs._generate_with_ollama

    def timed_search(self, query, top_k=5, mode=None):
        t = time.perf_counter()
        res = orig_search(self, query, top_k=top_k, mode=mode)
        stage["retrieve_s"] = time.perf_counter() - t
        stage["context"] = [d for d, _ in res]
        return res

    def timed_gen(prompt, model_name, ollama_url):
        t = time.perf_counter()
        ans = orig_gen(prompt, model_name, ollama_url)
        stage["generate_s"] = time.perf_counter() - t
        stage["generated"] = ans is not None
        return ans

    rs.DocumentRAG.hybrid_search, rs._generate_with_ollama = timed_search, timed_gen

    cohort, papers, titles = load_items(a.cohort, a.limit)
    augmented = peerqa_augmented() if a.cohort == "PEERQA-PDF" else {}
    systems = cfg["systems"]
    ckpt = out / "checkpoint.jsonl"
    done = {}
    if ckpt.exists():
        for line in open(ckpt, encoding="utf-8"):
            r = json.loads(line)
            done[(r["condition"], r["question_id"])] = r

    py_mem = rr.MemorySampler()
    py_mem.__enter__()

    # 1. Ingestion: once per paper per distinct pipeline (extractor, chunker, embedder)
    pipelines = sorted({(s["chunker"], s["embedder"]) for s in systems.values()})
    if len(pipelines) != 1 or pipelines[0][1] != settings.EMBEDDING_MODEL:
        raise SystemExit(f"harness supports one shared ingestion pipeline with the production embedder; got {pipelines}")
    chunker = pipelines[0][0]
    doc_ids, ingest = {}, {}
    for n, (pid, its) in enumerate(papers):
        doc_id = DOC_ID_BASE + n
        doc_ids[pid] = doc_id
        pdf = str(rr.pdf_path(a.cohort, pid, its[0].get("pdf_version", "latest")))
        t = time.perf_counter()
        try:
            count, rag = rs.ingest_document(doc_id, pdf, strategy=chunker)
            ingest[pid] = {"ok": rag is not None, "points": count, "ingest_s": round(time.perf_counter() - t, 2)}
        except Exception as e:  # recorded, never dropped
            ingest[pid] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300], "ingest_s": round(time.perf_counter() - t, 2)}
        if (n + 1) % 10 == 0:
            print(f"ingested {n + 1}/{len(papers)}", flush=True)
    pdf_version = {it["question_id"]: it.get("pdf_version", "latest") for _, its in papers for it in its}

    # 2. Generation: per model, per condition, fresh model load (unload_all) and one pass
    resources = {}
    by_model = {}
    for cond in conditions:
        by_model.setdefault(cond["llm"], []).append(cond)
    with open(ckpt, "a", encoding="utf-8") as f:
        for llm, conds in by_model.items():
            for cond in conds:
                name = cond["name"]
                todo = [(p, it) for p, its in papers for it in its if (name, it["question_id"]) not in done]
                if not todo:
                    continue
                unload_all()
                time.sleep(3)
                sampler = TreeSampler()
                for k, (pid, it) in enumerate(todo, 1):
                    stage.clear()
                    t0 = time.perf_counter()
                    sys_cfg = systems.get(cond["system"])
                    if cond["system"] == "GOLD":
                        docs = gold_docs(a.cohort, it)
                        prompt = rs.build_answer_prompt(it["question"], titles.get(pid, ""), docs, REFUSAL)
                        ans = rs._generate_with_ollama(prompt, llm, settings.OLLAMA_BASE_URL)
                        result = {"answer": ans or "", "sources": [{"gold": True}] if ans else []}
                        gate = False
                        failed = ans is None
                        ctx_docs = docs
                    else:
                        if not ingest[pid]["ok"]:
                            rec = {"condition": name, "question_id": it["question_id"], "paper_id": pid,
                                   "error": "ingestion failed", "token_f1": 0.0, "refusal": True}
                            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            done[(name, it["question_id"])] = rec
                            continue
                        settings.RAG_RETRIEVAL_MODE = sys_cfg["retrieval_mode"]
                        settings.OLLAMA_MODEL = llm
                        result = rs.query_document(doc_ids[pid], "", it["question"], titles.get(pid, ""))
                        settings.RAG_RETRIEVAL_MODE = live["retrieval_mode"]
                        settings.OLLAMA_MODEL = live["default_llm"]
                        gate = "generated" not in stage
                        failed = (not gate) and not stage.get("generated")
                        ctx_docs = stage.get("context", [])
                    ans = result["answer"]
                    refused = gate or is_refusal(ans)
                    refs = references(a.cohort, it)
                    f1_aug = None
                    if a.cohort == "PEERQA-PDF":
                        f1 = None if not refs else (0.0 if refused else compute_token_f1(ans, refs[0]["answer"])[2])
                        aug = augmented.get(it["question_id"])
                        f1_aug = None if not aug else (0.0 if refused else compute_token_f1(ans, aug)[2])
                    elif refused:
                        f1 = 0.0
                    else:
                        f1 = score_prediction_max_annotator(ans, refs)[0]
                    ev = it["retrieval_evidence"]
                    ctx_text = "\n\n".join(d.page_content for d in ctx_docs)
                    rec = {
                        "condition": name, "system": cond["system"], "llm": llm, "paper_id": pid,
                        "question_id": it["question_id"], "question_type": it.get("question_type", "free_form"),
                        "prediction": ans, "token_f1": None if f1 is None else round(f1, 4),
                        "token_f1_augmented_ref": None if f1_aug is None else round(f1_aug, 4),
                        "refusal": refused, "gate_refusal": gate,
                        "model_refusal": refused and not gate, "generation_failed": failed,
                        "cec_0.5": context_evidence_coverage(ctx_text, ev, tau=0.5) if ctx_docs else 0,
                        "context_tokens": sum(int(d.metadata.get("token_count") or rp_tokens(d.page_content)) for d in ctx_docs),
                        "n_context_units": len(ctx_docs),
                        "retrieve_s": round(stage.get("retrieve_s", 0.0), 4),
                        "generate_s": round(stage.get("generate_s", 0.0), 3),
                        "end_to_end_s": round(time.perf_counter() - t0, 3),
                        "pdf_version": pdf_version.get(it["question_id"]),
                        "context_text": ctx_text,  # what the LLM was given (for the human review sheets)
                    }
                    bool_refs = [r["answer"] for r in refs if r.get("type") == "boolean"]
                    if rec["question_type"] == "boolean" and bool_refs:
                        gold = Counter(bool_refs).most_common(1)[0][0]
                        rec["boolean_correct"] = int((None if refused else yes_no(ans)) == gold)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    done[(name, it["question_id"])] = rec
                    if k % 25 == 0:
                        print(f"{name}: {k}/{len(todo)}", flush=True)
                resources[name] = sampler.stop()
                print(name, "done", resources[name], flush=True)
    unload_all()
    py_mem.__exit__()

    # 3. Summary
    names = [c["name"] for c in conditions]
    rows = []
    for pid, its in papers:
        for it in its:
            row = {"paper_id": pid, "question_id": it["question_id"], "question_type": it.get("question_type")}
            for nme in names:
                r = done.get((nme, it["question_id"]))
                if r is None:
                    break
                row[nme] = {"token_f1": r["token_f1"], "token_f1_augmented_ref": r.get("token_f1_augmented_ref"),
                            "refusal": int(r["refusal"]), "gate_refusal": int(r.get("gate_refusal", False)),
                            "cec_0.5": r.get("cec_0.5", 0), "context_tokens": r.get("context_tokens", 0),
                            "boolean_correct": r.get("boolean_correct")}
            else:
                rows.append(row)
    # Rows scored on the primary reference (all of C-INT; PeerQA: only questions with an author answer)
    all_rows = rows
    rows = [r for r in all_rows if all(r[n]["token_f1"] is not None for n in names)]
    aug_rows = [{**r, **{n: {**r[n], "token_f1": r[n]["token_f1_augmented_ref"]} for n in names}}
                for r in all_rows if all(r[n].get("token_f1_augmented_ref") is not None for n in names)]
    per_cond = {}
    for nme in names:
        recs = [done[(nme, r["question_id"])] for r in rows]
        e2e = sorted(r.get("end_to_end_s", 0) for r in recs if r.get("end_to_end_s"))
        gen = sorted(r["generate_s"] for r in recs if r.get("generate_s"))
        ret = sorted(r["retrieve_s"] for r in recs if r.get("retrieve_s"))
        boo = [r["boolean_correct"] for r in recs if r.get("boolean_correct") is not None]

        def pct(xs, q):
            return round(xs[min(len(xs) - 1, int(q * len(xs)))], 3) if xs else None
        per_cond[nme] = {
            "n": len(recs), "token_f1": round(sum(r["token_f1"] for r in recs) / max(1, len(recs)), 4),
            "refusal_rate": round(sum(bool(r["refusal"]) for r in recs) / max(1, len(recs)), 4),
            "gate_refusals": sum(bool(r.get("gate_refusal")) for r in recs),
            "model_refusals": sum(bool(r.get("model_refusal")) for r in recs),
            "generation_failures": sum(bool(r.get("generation_failed")) for r in recs),
            "other_errors": sum(1 for r in recs if r.get("error")),
            "cec_0.5": round(sum(r.get("cec_0.5", 0) for r in recs) / max(1, len(recs)), 4),
            "context_tokens_mean": round(sum(r.get("context_tokens", 0) for r in recs) / max(1, len(recs)), 1),
            "boolean_accuracy": {"n": len(boo), "correct": sum(boo), "wilson95": wilson(sum(boo), len(boo))},
            "latency_s": {"retrieve_p50": pct(ret, 0.5), "retrieve_p95": pct(ret, 0.95), "generate_p50": pct(gen, 0.5),
                          "generate_p95": pct(gen, 0.95), "end_to_end_p50": pct(e2e, 0.5), "end_to_end_p95": pct(e2e, 0.95)},
            "ollama_memory": resources.get(nme),
        }
    fam = cfg["primary_family"][a.cohort if a.cohort == "PEERQA-PDF" else "C-INT"]
    summary = {
        "experiment": "RQ6", "cohort": a.cohort, "smoke": bool(a.limit), "config_sha256": sha256(CONFIG),
        "live_settings": live, "papers": len(papers), "questions": len(rows),
        "ingestion": {"papers_ok": sum(v["ok"] for v in ingest.values()), "papers_failed": [p for p, v in ingest.items() if not v["ok"]],
                      "ingest_s_p50": sorted(v["ingest_s"] for v in ingest.values())[len(ingest) // 2] if ingest else None},
        "conditions": per_cond,
        "primary_family_token_f1": rr.family(rows, fam, "token_f1") if rows and fam else [],
        "secondary_answered_by_both": [
            {**rr.compare([r for r in rows if not r[c][ "refusal"] and not r[b]["refusal"]], b, c, "token_f1"),
             "n_questions": sum(1 for r in rows if not r[c]["refusal"] and not r[b]["refusal"]),
             "note": "selection-affected"} for c, b in fam] if rows and fam else [],
        "descriptive_pairs": [rr.compare(rows, b, c, "token_f1") for c, b in cfg.get("descriptive_pairs", {}).get(
            "PEERQA-PDF" if a.cohort == "PEERQA-PDF" else "C-INT", [])] if rows else [],
        "questions_all": len(all_rows),
        "sensitivity_augmented_reference": {
            "note": "PeerQA only: Token F1 against PeerQA's released generated answers, all questions; LLM-written references",
            "questions": len(aug_rows),
            "means": {n: round(sum(r[n]["token_f1"] for r in aug_rows) / max(1, len(aug_rows)), 4) for n in names},
            "pairs": [rr.compare(aug_rows, b, c, "token_f1") for c, b in fam] if aug_rows and fam else [],
        } if a.cohort == "PEERQA-PDF" else None,
        "python_memory": py_mem.report(),
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper"},
    }
    rr.write_outputs(out, all_rows, summary)
    (out / "ingestion.json").write_text(json.dumps(ingest, indent=1), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("papers", "questions", "primary_family_token_f1")}, indent=1))


def rp_tokens(text):
    from apps.documents.services.chunkers import estimate_tokens
    return estimate_tokens(text)


if __name__ == "__main__":
    main()
