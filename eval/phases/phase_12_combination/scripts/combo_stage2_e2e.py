#!/usr/bin/env python3
"""
COMBO stage 2: end-to-end pipeline x LLM selection on C-RET-150 questions
(registered: reports/revalidation/protocol/combo_test.json "stage2").

  --draw            draw and freeze the 120 stage-2 questions (seed 42; one atomically eligible question
                    per paper, 120 papers). Run once, before any stage-2 output; the file is hashed into the registry.
  (default)         run the selection: shortlist pipelines (stage-1 + semantic add-on combined shortlist) x LLMs.
  --limit N         smoke test on the first N questions (output under smoke_N/, no decision).

Per (pipeline, question): the same context construction as stage 1 (sections -> chunker -> embedder -> ranking ->
production assembly). Gate: production rule (max dense cosine of the matched units in the context, rrf modes count
units outside the dense top-50 as 0), with the stage-1 calibrated threshold for the pipeline. Gated questions are
refusals without generation. Otherwise the production prompt (rag_service.build_answer_prompt; Snippet page/section
from the unit metadata, as production) is sent to Ollama with the production payload (temperature 0, no other
options, timeout OLLAMA_TIMEOUT). A timeout is a generation failure (scored 0, counted).
Scoring: max-over-annotator Token F1; any refusal = 0. Boolean accuracy; refusal rates; context tokens; latency
(retrieval rank+assemble, generation wall time, end-to-end = both plus the embedder's stage-1 query latency P50).
Dedup: an identical (LLM, prompt) is generated once and reused (temperature 0); reuse is recorded.
Successive halving: phase A = first 40 questions for every pair; then a pair stops if the 95% paper-cluster CI of its
F1 difference to the best pair is entirely below 0 (production pair never stops); phase B = the remaining questions
for the surviving pairs. Each LLM is loaded once per phase (all models unloaded first).
Decision (all 120 questions, survivors vs production pair, Holm): adopt if diff >= +0.03, CI lower > 0, Holm p < 0.05
and end-to-end P50 <= 1.5x production; several pass -> highest F1; else production stays.

Output: eval/phases/phase_12_combination/artifacts/stage2/[smoke_N/]
"""

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_1_extraction" / "scripts"))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))

ART = ROOT / "eval" / "phases" / "phase_12_combination" / "artifacts"
STAGE1 = ART / "stage1" / "summary.json"
STAGE1B = ART / "stage1b_semantic" / "summary.json"  # semantic add-on (combo_semantic_addon.json)
SEMANTIC_UNITS = ART / "stage1b_semantic" / "units"
QUESTIONS = ART / "stage2" / "questions.json"
TRAIN = ROOT / "eval" / "data" / "qasper_official" / "qasper-train-v0.3.json"
LLMS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b", "qwen2.5:1.5b", "phi4-mini"]
PRODUCTION_PIPELINE = "pymupdf_layout|hierarchical|e5|dense"
PRODUCTION_LLM = "llama3.2:3b"
N_QUESTIONS, PHASE_A, SEED = 120, 40, 42
REFUSAL = "The document does not contain sufficient relevant information to answer this question."
URL = "http://localhost:11434"


def pair(p, m):
    return f"{p} || {m}"


# ----------------------------------------------------------------------------- question draw
def draw():
    from eval_common import reval_runner as rr
    from generate_sample_manifest_250 import is_atomic_eligible
    if QUESTIONS.exists():
        raise SystemExit(f"{QUESTIONS} already exists (frozen); refusing to redraw")
    train = json.load(open(TRAIN, encoding="utf-8"))
    groups = rr.group_items(rr.load_cohort("C-RET-150"))
    eligible = {}
    for pid, items in sorted(groups.items()):
        qas = {qa["question_id"]: qa for qa in train[pid]["qas"]}
        ok = []
        for it in items:
            good, refs, ev = is_atomic_eligible(qas[it["question_id"]])
            if good:
                ok.append({**it, "references": refs, "gold_evidence": ev, "question_type": refs[0]["type"],
                           "paper_title": train[pid]["title"]})
        if ok:
            eligible[pid] = sorted(ok, key=lambda x: x["question_id"])
    rng = random.Random(SEED)
    papers = sorted(eligible)
    chosen = sorted(rng.sample(papers, min(N_QUESTIONS, len(papers))))
    items = [rng.choice(eligible[p]) for p in chosen]
    rng.shuffle(items)  # fixed processing order; phase A = the first 40
    doc = {"rule": "C-RET-150 papers with >= 1 atomically eligible question (is_atomic_eligible); seed 42; "
                   "min(120, eligible) papers; one eligible question each; order shuffled with the same seed",
           "eligible_papers": len(papers), "n": len(items),
           "question_types": dict(Counter(i["question_type"] for i in items)), "items": items}
    QUESTIONS.parent.mkdir(parents=True, exist_ok=True)
    QUESTIONS.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"drew {len(items)} questions from {len(papers)} eligible papers; sha256 "
          f"{hashlib.sha256(QUESTIONS.read_bytes()).hexdigest()}")


# ----------------------------------------------------------------------------- contexts
def build_contexts(items, pipelines):
    """{(pipeline, question_id): {'docs': [...], 'gate_score', 'context_tokens', 'n_units', 'retrieve_s'}}"""
    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    import numpy as np
    import rq1v2_extractors as rq1
    import combo_stage1_grid as s1
    from apps.documents.services.chunking_utils import extract_sections_from_pdf
    cache = rq1.load_cache("reservoir")
    out = {}
    by_paper = {}
    for it in items:
        by_paper.setdefault(it["paper_arxiv_id"], []).append(it)
    for pl in pipelines:
        ex, ch, em, mode = pl.split("|")
        model = s1.EMBEDDERS[em]
        for pid, its in by_paper.items():
            version = its[0]["pdf_version"]
            if ex == "pymupdf_layout":
                sections = extract_sections_from_pdf(str(rr.pdf_path("C-RET", pid, version)))
            else:
                c = cache.get((pid, version, ex))
                sections = rq1.sections_of(c) if c and c.get("ok") else []
            if ch.startswith("semantic_"):  # chunked once by the add-on (e5 split points); identical units
                cached = json.loads((SEMANTIC_UNITS / f"{pid}.json").read_text(encoding="utf-8"))
                units = cached["units"].get(ch) or []
            else:
                units = rp.build_units(sections, ch, pid) if sections else []
            if not units:
                for it in its:
                    out[(pl, it["question_id"])] = {"docs": [], "gate_score": 0.0, "context_tokens": 0, "n_units": 0, "retrieve_s": 0.0}
                continue
            texts = [u["text"] for u in units]
            tag = (f"cret_{pid}_{ch}" if ex == "pymupdf_layout"
                   else (f"rq1v2_{pid}_{ex}" if ch == "hierarchical" else f"grid_{pid}_{ex}_{ch}"))
            um = rp.cached_embed(model, texts, False, tag)
            qv = rp.cached_embed(model, [it["question"] for it in its], True, f"cret_{pid}_s2")
            for it, q in zip(its, qv):
                t = time.perf_counter()
                dense = um @ q
                ranked = rp.rank(mode, dense, texts, it["question"])
                ctx = rp.assemble(ranked, units, ch)
                retrieve_s = time.perf_counter() - t
                idx = s1.context_indices(ranked, units, ch, len(ctx))
                top50 = set(int(i) for i in np.argsort(dense)[::-1][:rp.RETRIEVE_K])
                gs = max(((float(dense[i]) if (mode not in ("rrf_prod", "rrf_fix") or i in top50) else 0.0) for i in idx),
                         default=0.0)
                docs = [{"text": c["text"], "page": units[i].get("page", 1),
                         "section": units[i].get("section", "Main"), "tokens": c["tokens"]} for c, i in zip(ctx, idx)]
                out[(pl, it["question_id"])] = {"docs": docs, "gate_score": gs, "n_units": len(ctx),
                                                "context_tokens": sum(c["tokens"] for c in ctx), "retrieve_s": retrieve_s}
        print(f"contexts ready: {pl}", flush=True)
    return out


# ----------------------------------------------------------------------------- generation
def generate(model, prompt, timeout_s):
    import requests
    t = time.perf_counter()
    try:
        r = requests.post(f"{URL}/api/generate", json={"model": model, "prompt": prompt, "stream": False,
                                                       "options": {"temperature": 0}}, timeout=(3.0, timeout_s))
        r.raise_for_status()
        d = r.json()
        return {"response": (d.get("response") or "").strip(), "wall_s": time.perf_counter() - t,
                "eval_count": d.get("eval_count"), "eval_s": (d.get("eval_duration") or 0) / 1e9,
                "prompt_eval_count": d.get("prompt_eval_count"), "error": None}
    except Exception as e:  # production treats any failure as "no answer"
        return {"response": "", "wall_s": time.perf_counter() - t, "error": f"{type(e).__name__}: {e}"[:200]}


def is_refusal(text):
    t = (text or "").lower()
    return REFUSAL.lower() in t or "does not contain sufficient" in t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draw", action="store_true")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.draw:
        draw()
        return

    from eval_common import reval_pipeline as rp
    from eval_common import reval_runner as rr
    rp.setup_django()
    from django.conf import settings
    from langchain_core.documents import Document
    from apps.documents.services.rag_service import build_answer_prompt
    from evaluate_rq5_llm_generation import score_prediction_max_annotator
    from rq5_reanalysis import wilson, yes_no
    from rq5_resource_profile import TreeSampler, unload_all

    s1 = json.load(open(STAGE1, encoding="utf-8"))
    if STAGE1B.exists():  # registered add-on: stage-1 shortlist + top 2 semantic cells
        s1b = json.load(open(STAGE1B, encoding="utf-8"))
        pipelines, gates = s1b["combined_shortlist"], s1b["combined_gate_thresholds"]
    elif a.limit:
        pipelines, gates = s1["shortlist"], s1["gate_thresholds"]
    else:
        raise SystemExit(f"{STAGE1B} missing: the semantic add-on must finish before stage 2 (combo_semantic_addon.json)")
    q_latency = {em: v["query_latency_ms"]["p50"] / 1000 for em, v in s1["efficiency"].items()}
    assert PRODUCTION_PIPELINE in pipelines
    qd = json.load(open(QUESTIONS, encoding="utf-8"))
    items = qd["items"][: a.limit] if a.limit else qd["items"]
    out = ART / "stage2" / (f"smoke_{a.limit}" if a.limit else "")
    out.mkdir(parents=True, exist_ok=True)
    timeout_s = float(getattr(settings, "OLLAMA_TIMEOUT", 60))

    print(f"{len(pipelines)} pipelines x {len(LLMS)} LLMs, {len(items)} questions", flush=True)
    ctxs = build_contexts(items, pipelines)

    ckpt = out / "checkpoint.jsonl"
    done, gen_cache = {}, {}
    if ckpt.exists():
        for line in open(ckpt, encoding="utf-8"):
            r = json.loads(line)
            done[(r["pair"], r["question_id"])] = r
            if r.get("prompt_sha") and not r.get("dedup_reused") and not r.get("gated"):
                gen_cache[(r["llm"], r["prompt_sha"])] = r
    resources = {}

    def run_phase(name, qs, pairs):
        by_llm = {}
        for p in pairs:
            by_llm.setdefault(p.split(" || ")[1], []).append(p)
        with open(ckpt, "a", encoding="utf-8") as f:
            for llm in LLMS:
                todo = [(p, it) for p in by_llm.get(llm, []) for it in qs if (p, it["question_id"]) not in done]
                if not todo:
                    continue
                unload_all()
                time.sleep(3)
                sampler = TreeSampler()
                for k, (p, it) in enumerate(todo, 1):
                    pl = p.split(" || ")[0]
                    c = ctxs[(pl, it["question_id"])]
                    em = pl.split("|")[2]
                    rec = {"pair": p, "pipeline": pl, "llm": llm, "paper_id": it["paper_arxiv_id"],
                           "question_id": it["question_id"], "question_type": it["question_type"], "phase": name,
                           "gate_score": round(c["gate_score"], 5), "context_tokens": c["context_tokens"],
                           "n_units": c["n_units"], "retrieve_s": round(c["retrieve_s"], 5)}
                    if not c["docs"] or c["gate_score"] < gates[pl]:
                        rec.update({"gated": True, "prediction": REFUSAL, "refusal": True, "generation_failed": False,
                                    "generate_s": 0.0})
                    else:
                        docs = [Document(page_content=d["text"], metadata={"page": d["page"], "section": d["section"]})
                                for d in c["docs"]]
                        prompt = build_answer_prompt(it["question"], it.get("paper_title", ""), docs, REFUSAL)
                        sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                        hit = gen_cache.get((llm, sha))
                        if hit:
                            g = {"response": hit["prediction"], "wall_s": hit["generate_s"], "error": hit.get("error"),
                                 "eval_count": hit.get("eval_count"), "eval_s": hit.get("eval_s")}
                        else:
                            g = generate(llm, prompt, timeout_s)
                        rec.update({"gated": False, "prompt_sha": sha, "dedup_reused": bool(hit),
                                    "prediction": g["response"], "generation_failed": bool(g["error"]),
                                    "error": g["error"], "generate_s": round(g["wall_s"], 3),
                                    "eval_count": g.get("eval_count"), "eval_s": g.get("eval_s"),
                                    "refusal": is_refusal(g["response"])})
                        if not hit:
                            gen_cache[(llm, sha)] = rec
                    rec["end_to_end_s"] = round(q_latency.get(em, 0) + rec["retrieve_s"] + rec["generate_s"], 3)
                    rec["token_f1"] = 0.0 if (rec["refusal"] or rec["generation_failed"]) else \
                        round(score_prediction_max_annotator(rec["prediction"], it["references"])[0], 4)
                    if it["question_type"] == "boolean":
                        gold = Counter(r["answer"] for r in it["references"] if r.get("type") == "boolean").most_common(1)
                        if gold:
                            rec["boolean_correct"] = int((None if rec["refusal"] else yes_no(rec["prediction"])) == gold[0][0])
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    f.flush()
                    done[(p, it["question_id"])] = rec
                    if k % 50 == 0:
                        print(f"[{name}] {llm}: {k}/{len(todo)}", flush=True)
                resources[f"{name}|{llm}"] = sampler.stop()
                print(f"[{name}] {llm} done {resources[f'{name}|{llm}']}", flush=True)
        unload_all()

    def rows_for(pairs, qs):
        rows = []
        for it in qs:
            r = {"paper_id": it["paper_arxiv_id"], "question_id": it["question_id"]}
            for p in pairs:
                d = done[(p, it["question_id"])]
                r[p] = {"token_f1": d["token_f1"], "refusal": int(d["refusal"]), "end_to_end_s": d["end_to_end_s"]}
            rows.append(r)
        return rows

    all_pairs = [pair(p, m) for p in pipelines for m in LLMS]
    prod = pair(PRODUCTION_PIPELINE, PRODUCTION_LLM)
    qa_, qb = items[:PHASE_A], items[PHASE_A:]
    run_phase("A", qa_, all_pairs)

    rows_a = rows_for(all_pairs, qa_)
    means_a = {p: sum(r[p]["token_f1"] for r in rows_a) / len(rows_a) for p in all_pairs}
    best = max(all_pairs, key=lambda p: means_a[p])
    stopped, halving = [], []
    for p in all_pairs:
        if p in (best, prod) or a.limit:
            continue
        cmp = rr.compare(rows_a, best, p, "token_f1")
        halving.append(cmp)
        if cmp["ci95"][1] < 0:
            stopped.append(p)
    survivors = [p for p in all_pairs if p not in stopped]
    if qb:
        run_phase("B", qb, survivors)

    rows = rows_for(survivors, items)
    means = {p: round(sum(r[p]["token_f1"] for r in rows) / len(rows), 4) for p in survivors}
    fam = rr.family(rows, [(p, prod) for p in survivors if p != prod], "token_f1") if len(survivors) > 1 else []
    p50 = {p: sorted(r[p]["end_to_end_s"] for r in rows)[len(rows) // 2] for p in survivors}
    eligible = [c for c in fam if c["diff"] >= 0.03 and c["ci95"][0] > 0 and c["p_holm"] < 0.05
                and p50[c["comparison"].split(" - ")[0]] <= 1.5 * p50[prod]]
    winner = max(eligible, key=lambda c: means[c["comparison"].split(" - ")[0]])["comparison"].split(" - ")[0] \
        if eligible else prod

    per_pair = {}
    for p in all_pairs:
        recs = [done[(p, it["question_id"])] for it in items if (p, it["question_id"]) in done]
        boo = [r["boolean_correct"] for r in recs if r.get("boolean_correct") is not None]
        e2e = sorted(r["end_to_end_s"] for r in recs)
        per_pair[p] = {
            "n": len(recs), "token_f1": round(sum(r["token_f1"] for r in recs) / max(1, len(recs)), 4),
            "refusal_rate": round(sum(r["refusal"] for r in recs) / max(1, len(recs)), 4),
            "gate_refusals": sum(r.get("gated", False) for r in recs),
            "generation_failures": sum(r.get("generation_failed", False) for r in recs),
            "dedup_reused": sum(r.get("dedup_reused", False) for r in recs),
            "boolean_accuracy": {"n": len(boo), "correct": sum(boo), "wilson95": wilson(sum(boo), len(boo))},
            "context_tokens_mean": round(sum(r["context_tokens"] for r in recs) / max(1, len(recs)), 1),
            "end_to_end_s_p50": e2e[len(e2e) // 2] if e2e else None,
            "end_to_end_s_p95": e2e[min(len(e2e) - 1, int(0.95 * len(e2e)))] if e2e else None,
            "stopped_after_phase_A": p in stopped,
        }
    summary = {
        "experiment": "COMBO-STAGE2", "smoke": bool(a.limit), "questions": len(items), "pipelines": pipelines,
        "llms": LLMS, "gate_thresholds": gates, "production_pair": prod,
        "phase_A": {"questions": len(qa_), "best_pair": best, "halving_comparisons": halving, "stopped": stopped},
        "per_pair": per_pair, "final_means_token_f1": means, "family_vs_production": fam,
        "end_to_end_p50": p50, "decision_rule": "adopt if diff >= +0.03, CI lower > 0, Holm p < 0.05, P50 <= 1.5x production",
        "winner": None if a.limit else winner, "resources": resources,
        "bootstrap": {"B": rr.B, "seed": rr.SEED, "unit": "paper"},
    }
    rr.write_outputs(out, rows, summary)
    print(json.dumps({"winner": summary["winner"], "stopped": len(stopped), "survivors": len(survivors)}, indent=1))


if __name__ == "__main__":
    main()
