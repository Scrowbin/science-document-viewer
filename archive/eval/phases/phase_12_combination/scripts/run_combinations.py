#!/usr/bin/env python3
"""
Combination experiment: 16 complete RAG pipelines on the QASPER combination set.

Design: the extractor is fixed to pymupdf_layout; two methods for each of four components
  chunker   : hierarchical (children 200 / overlap 40, parent expansion) | fixed_size (400)
  embedder  : intfloat/e5-small-v2 | nomic-ai/modernbert-embed-base
  retrieval : dense | hybrid (convex: 0.7 * minmax(dense) + 0.3 * minmax(BM25, regex tokens), all chunks of the paper;
              alpha checked by phase_6_hybrid_retrieval/scripts/tune_hybrid_alpha.py on Train papers only)
  LLM       : llama3.2:3b | qwen2.5:1.5b
-> 8 retrieval pipelines x 2 LLMs = 16 configurations. Settings are those of the component experiments and the
stage-1 grid (eval_common.reval_pipeline): production section extraction, 1,600-token budget, <= 5 units,
parents over 800 tokens windowed to +-200 words, refusal gate calibrated per pipeline (GATES).

Two phases, so the embedder and the LLM are never in memory together:
  1 retrieval  : per embedder, per paper -> retrieval_per_query.jsonl and contexts.jsonl (exact LLM contexts)
  2 generation : per LLM, per retrieval pipeline -> generation_per_query.jsonl
Both phases resume from their JSONL files. Results are descriptive (means, rates, latency, memory).

Usage (backend venv):
  python run_combinations.py --list          print the 16 configurations and their parameters
  python run_combinations.py --limit 3       smoke test: first 3 questions through all 16 configurations
  python run_combinations.py --profile       ~10 papers of mixed size: per-stage time and memory + full-run estimate
  python run_combinations.py [--retrieval-scope all|sample]
                                             full run: generation (16 configurations) on the 300 questions of
                                             generation_sample.json; retrieval metrics on every question of
                                             combination_set.json (all, default) or of the 300 sampled papers (sample).
                                             Resumable: rerunning the same command continues from the JSONL files.
Output: eval/phases/phase_12_combination/artifacts/combinations/[smoke_N/|profile/]
"""

import argparse
import gc
import hashlib
import json
import random
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend" / "scripts"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))

DATASET = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "combination_set.json"
GEN_SAMPLE = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "generation_sample.json"  # 300 questions
QASPER = ROOT / "eval" / "data" / "qasper_official"
OUT = ROOT / "eval" / "phases" / "phase_12_combination" / "artifacts" / "combinations"
URL = "http://localhost:11434"
REFUSAL = "The document does not contain sufficient relevant information to answer this question."
SEED = 42

CHUNKERS = {"HIER": "hierarchical", "FIXED": "fixed_size"}
EMBEDDERS = {"E5": "intfloat/e5-small-v2", "MBERT": "nomic-ai/modernbert-embed-base"}
EMBEDDER_REVISION = {"intfloat/e5-small-v2": "ffb93f3bd4047442299a41ebb6fa998a38507c52",
                     "nomic-ai/modernbert-embed-base": "d556a88e332558790b210f7bdbe87da2fa94a8d8"}
RETRIEVAL = {"DENSE": "dense", "HYBRID": "convex_fix"}
LLMS = {"LLAMA3B": "llama3.2:3b", "QWEN15B": "qwen2.5:1.5b"}
GEN_OPTIONS = {"temperature": 0, "num_ctx": 4096}
# Ollama's prompt cache grows with every new prompt (llama3.2:3b reached ~6 GB and forced paging in the profile run);
# unloading the model every UNLOAD_EVERY generated answers resets it. Memory handling only, not a generation setting.
UNLOAD_EVERY = 25   # production payload; answers are short, no num_predict cap

# Refusal gate: max dense cosine of the context units below this -> refuse without calling the LLM.
# e5 hierarchical dense = production 0.80; the others are the stage-1 grid calibration (same gate-refusal rate as
# production, 2.4% of 249 questions; eval/phases/phase_12_combination/artifacts/stage1/per_query.jsonl).
GATES = {"HIER_E5_DENSE": 0.80, "HIER_E5_HYBRID": 0.79494, "HIER_MBERT_DENSE": 0.30715, "HIER_MBERT_HYBRID": 0.3035,
         "FIXED_E5_DENSE": 0.79252, "FIXED_E5_HYBRID": 0.79252, "FIXED_MBERT_DENSE": 0.2615,
         "FIXED_MBERT_HYBRID": 0.2615}


def retrieval_pipelines():
    return [f"{c}_{e}_{r}" for c in CHUNKERS for e in EMBEDDERS for r in RETRIEVAL]


def configs():
    return [f"{p}_{m}" for p in retrieval_pipelines() for m in LLMS]


def pipeline_params(pid):
    c, e, r = pid.split("_")
    from apps.documents.services.rag_service import get_model_prefix
    from eval_common import reval_pipeline as rp
    model = EMBEDDERS[e]
    chunker = ({"name": "hierarchical", "child_max_tokens": 200, "child_overlap": 40, "parent_expansion": True,
                "parent_window": f"parents > {rp.MAX_PARENT_TOKENS} tokens -> +-{rp.PAD_WORDS} words around the child"}
               if c == "HIER" else {"name": "fixed_size", "max_tokens": 400})
    retrieval = ({"name": "dense", "similarity": "cosine (L2-normalised dot product)"} if r == "DENSE" else
                 {"name": "hybrid_convex", "alpha_dense": rp.CONVEX_ALPHA, "bm25": "BM25Okapi, regex tokens, 39 stopwords",
                  "normalisation": "per-query min-max over all chunks of the paper"})
    return {"extractor": "pymupdf_layout (apps.documents.services.chunking_utils.extract_sections_from_pdf)",
            "chunker": {**chunker, "token_estimate": "ceil(words * 1.33)"},
            "embedder": {"model": model, "revision": EMBEDDER_REVISION[model],
                         "query_prefix": get_model_prefix(model, is_query=True),
                         "passage_prefix": get_model_prefix(model, is_query=False)},
            "retrieval": retrieval,
            "context": {"budget_tokens": 1600, "max_units": 5, "assembly": "rank order, stop before exceeding budget"},
            "gate_threshold": GATES[pid]}


def config_params(cid):
    pid, m = cid.rsplit("_", 1)
    return {**pipeline_params(pid), "llm": {"model": LLMS[m], "options": GEN_OPTIONS,
                                             "prompt": "apps.documents.services.rag_service.build_answer_prompt"}}


# ----------------------------------------------------------------------------- data
def load_items(limit=None, papers_subset=None):
    ds = json.load(open(DATASET, encoding="utf-8"))
    from eval_common.revalidation import qasper_text_evidence
    from generate_sample_manifest_250 import is_atomic_eligible
    data = {}
    for s in ("train", "dev", "test"):
        data.update(json.load(open(QASPER / f"qasper-{s}-v0.3.json", encoding="utf-8")))
    items = []
    for pid in sorted(ds["papers"]):
        if papers_subset is not None and pid not in papers_subset:
            continue
        p = ds["papers"][pid]
        qas = {qa["question_id"]: qa for qa in data[pid]["qas"]}
        for qid in sorted(p["questions"]):
            qa = qas[qid]
            _, refs, _ = is_atomic_eligible(qa)
            items.append({"paper_id": pid, "split": p["split"], "pdf": str(ROOT / p["pdf"]), "question_id": qid,
                          "question": qa["question"], "paper_title": data[pid]["title"], "references": refs,
                          "question_type": refs[0]["type"], "evidence": qasper_text_evidence(qa)})
    return items[:limit] if limit else items


def read_jsonl(path):
    return [json.loads(line) for line in open(path, encoding="utf-8")] if path.exists() else []


# ----------------------------------------------------------------------------- resources
class SystemSampler:
    """Every 0.5 s: Python working set, Ollama process tree working set, system available memory, pagefile use."""

    def __init__(self):
        import psutil
        self.psutil, self.me = psutil, psutil.Process()
        self.base_swap = psutil.swap_memory().used
        self.peak_py = self.peak_ol = 0
        self.min_avail = psutil.virtual_memory().available
        self.max_swap_growth = 0
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def _ollama_rss(self):
        total, seen = 0, set()
        for p in self.psutil.process_iter(["name"]):
            if (p.info["name"] or "").lower() != "ollama.exe":
                continue
            try:
                for q in [p] + p.children(recursive=True):
                    if q.pid not in seen:
                        seen.add(q.pid)
                        total += q.memory_info().rss
            except self.psutil.Error:
                pass
        return total

    def _run(self):
        while not self._stop.is_set():
            self.peak_py = max(self.peak_py, self.me.memory_info().rss)
            self.peak_ol = max(self.peak_ol, self._ollama_rss())
            self.min_avail = min(self.min_avail, self.psutil.virtual_memory().available)
            self.max_swap_growth = max(self.max_swap_growth, self.psutil.swap_memory().used - self.base_swap)
            time.sleep(0.5)

    def stop(self):
        self._stop.set()
        mb = lambda x: round(x / 2**20, 1)  # noqa: E731
        return {"python_peak_mb": mb(self.peak_py), "ollama_peak_mb": mb(self.peak_ol),
                "system_min_available_mb": mb(self.min_avail), "pagefile_growth_max_mb": mb(self.max_swap_growth)}


# ----------------------------------------------------------------------------- phase 1: retrieval
def run_retrieval(items, out, timings):
    from eval_common import reval_pipeline as rp
    from eval_common.relevance import is_chunk_hit
    from apps.documents.services.chunking_utils import extract_sections_from_pdf
    import combo_stage1_grid as s1
    import numpy as np

    ret_path, ctx_path = out / "retrieval_per_query.jsonl", out / "contexts.jsonl"
    done = {(r["retrieval_pipeline"], r["question_id"]) for r in read_jsonl(ret_path)}
    by_paper = defaultdict(list)
    for it in items:
        by_paper[it["paper_id"]].append(it)
    resources = {}
    with open(ret_path, "a", encoding="utf-8") as fr, open(ctx_path, "a", encoding="utf-8") as fc:
        for e, model in EMBEDDERS.items():
            todo = [p for p in by_paper if any((f"{c}_{e}_{r}", it["question_id"]) not in done
                                               for c in CHUNKERS for r in RETRIEVAL for it in by_paper[p])]
            if not todo:
                continue
            sampler = SystemSampler()
            t = time.perf_counter()
            rp.get_model(model)
            timings["model_load_s"][e] = round(time.perf_counter() - t, 2)
            for n, pid in enumerate(todo, 1):
                its = by_paper[pid]
                t = time.perf_counter()
                sections = extract_sections_from_pdf(its[0]["pdf"])
                timings["extract_s"].append(time.perf_counter() - t)
                t = time.perf_counter()
                qv = rp.cached_embed(model, [it["question"] for it in its], True, f"combo_{pid}")
                timings["query_embed_s"][e].append((time.perf_counter() - t) / len(its))
                for c, ch in CHUNKERS.items():
                    units = rp.build_units(sections, ch, pid) if sections else []
                    texts = [u["text"] for u in units]
                    um, cand = None, []
                    if units:
                        cache_dir = rp.EMB_CACHE / model.replace("/", "__") / "p"
                        h = hashlib.sha256(("\x1f".join(texts)).encode("utf-8")).hexdigest()[:16]
                        cached = (cache_dir / f"cret_{pid}_{ch}_{h}.npy").exists()
                        t = time.perf_counter()
                        um = rp.cached_embed(model, texts, False, f"cret_{pid}_{ch}")
                        dt = time.perf_counter() - t
                        if not cached:
                            timings["index_s_per_chunk"][e].append(dt / len(texts))
                        timings["chunks_per_paper"][c].append(len(texts))
                        cand = rp.candidate_units_for_relevance(units, ch)
                    for r, mode in RETRIEVAL.items():
                        pl = f"{c}_{e}_{r}"
                        for it, q in zip(its, qv):
                            if (pl, it["question_id"]) in done:
                                continue
                            rec = {"retrieval_pipeline": pl, "question_id": it["question_id"], "paper_id": pid}
                            if not units or um is None:
                                rec.update(ndcg10=0.0, mrr10=0.0, **{"cec_0.5": 0, "cec_0.3": 0, "cec_0.7": 0},
                                           context_tokens=0, n_units=0, gate_score=0.0, retrieve_ms=0.0, no_units=True)
                                docs = []
                            else:
                                t = time.perf_counter()
                                dense = um @ q
                                ranked = rp.rank(mode, dense, texts, it["question"])
                                ctx = rp.assemble(ranked, units, ch)
                                retrieve_ms = (time.perf_counter() - t) * 1000
                                idx = s1.context_indices(ranked, units, ch, len(ctx))
                                m = rp.question_metrics(ctx, cand, it["evidence"])
                                rel = [1 if is_chunk_hit({"text": x["text"]}, "", "", it["evidence"], tau=0.50) else 0
                                       for x in ctx]
                                mrr = next((1.0 / (i + 1) for i, v in enumerate(rel[:10]) if v), 0.0)
                                gs = max((float(dense[i]) for i in idx), default=0.0)
                                rec.update(ndcg10=round(m["ndcg10"], 5), mrr10=round(mrr, 5),
                                           **{k: m[k] for k in ("cec_0.3", "cec_0.5", "cec_0.7")},
                                           context_tokens=m["context_tokens"], n_units=m["n_units"],
                                           gate_score=round(gs, 5), retrieve_ms=round(retrieve_ms, 3),
                                           ranked_unit_ids=[x["unit_id"] for x in ctx])
                                timings["retrieve_ms"][pl].append(retrieve_ms)
                                docs = [{"text": x["text"], "page": units[i].get("page", 1),
                                         "section": units[i].get("section", "Main"), "tokens": x["tokens"]}
                                        for x, i in zip(ctx, idx)]
                            fr.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            fc.write(json.dumps({"retrieval_pipeline": pl, "question_id": it["question_id"],
                                                 "gate_score": rec["gate_score"], "docs": docs}, ensure_ascii=False) + "\n")
                fr.flush()
                fc.flush()
                if n % 10 == 0 or n == len(todo):
                    print(f"[retrieval {e}] {n}/{len(todo)} papers", flush=True)
            resources[f"retrieval_{e}"] = sampler.stop()
            rp._MODELS.clear()
            gc.collect()
    return resources


# ----------------------------------------------------------------------------- phase 2: generation
def generate(model, prompt, timeout_s):
    import requests
    t = time.perf_counter()
    try:
        r = requests.post(f"{URL}/api/generate", json={"model": model, "prompt": prompt, "stream": False,
                                                       "options": GEN_OPTIONS}, timeout=(3.0, timeout_s))
        r.raise_for_status()
        d = r.json()
        return {"response": (d.get("response") or "").strip(), "wall_s": time.perf_counter() - t,
                "eval_count": d.get("eval_count"), "error": None}
    except Exception as e:  # production treats any failure as "no answer"
        return {"response": "", "wall_s": time.perf_counter() - t, "error": f"{type(e).__name__}: {e}"[:200]}


def is_refusal(text):
    t = (text or "").lower()
    return REFUSAL.lower() in t or "does not contain sufficient" in t


def run_generation(items, out, timings):
    from django.conf import settings
    from langchain_core.documents import Document
    from apps.documents.services.rag_service import build_answer_prompt
    from evaluate_generation import compute_context_containment_proxy, score_prediction_max_annotator
    from generation_reanalysis import yes_no
    from profile_generation_resources import unload_all

    timeout_s = float(getattr(settings, "OLLAMA_TIMEOUT", 60))
    ctxs = {(r["retrieval_pipeline"], r["question_id"]): r for r in read_jsonl(out / "contexts.jsonl")}
    gen_path = out / "generation_per_query.jsonl"
    prior = read_jsonl(gen_path)
    done = {(r["config"], r["question_id"]) for r in prior}
    gen_cache = {(r["llm"], r["prompt_sha"]): r for r in prior if r.get("prompt_sha") and not r.get("reused")}
    resources = {}
    with open(gen_path, "a", encoding="utf-8") as f:
        for m, llm in LLMS.items():
            todo = [(pl, it) for pl in retrieval_pipelines() for it in items if (f"{pl}_{m}", it["question_id"]) not in done]
            if not todo:
                continue
            unload_all()
            sampler = SystemSampler()
            t = time.perf_counter()
            generate(llm, "Hello", timeout_s)  # cold load, timed separately
            timings["llm_load_s"][m] = round(time.perf_counter() - t, 2)
            n_generated = 0
            for k, (pl, it) in enumerate(todo, 1):
                c = ctxs[(pl, it["question_id"])]
                rec = {"config": f"{pl}_{m}", "retrieval_pipeline": pl, "llm": llm, "question_id": it["question_id"],
                       "paper_id": it["paper_id"], "split": it["split"], "question_type": it["question_type"]}
                context_text = "\n\n".join(d["text"] for d in c["docs"])
                if not c["docs"] or c["gate_score"] < GATES[pl]:
                    rec.update(gated=True, prediction=REFUSAL, refusal=True, generation_failed=False, generate_s=0.0)
                else:
                    docs = [Document(page_content=d["text"], metadata={"page": d["page"], "section": d["section"]})
                            for d in c["docs"]]
                    prompt = build_answer_prompt(it["question"], it["paper_title"], docs, REFUSAL)
                    sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                    hit = gen_cache.get((llm, sha))
                    g = ({"response": hit["prediction"], "wall_s": hit["generate_s"], "error": hit.get("error")}
                         if hit else generate(llm, prompt, timeout_s))
                    rec.update(gated=False, prompt_sha=sha, reused=bool(hit), prediction=g["response"],
                               generation_failed=bool(g["error"]), error=g["error"], generate_s=round(g["wall_s"], 3),
                               refusal=is_refusal(g["response"]))
                    if not hit:
                        gen_cache[(llm, sha)] = rec
                        n_generated += 1
                        if n_generated % UNLOAD_EVERY == 0:
                            unload_all()
                        timings["generate_s"][m].append(g["wall_s"])
                failed = rec["refusal"] or rec["generation_failed"]
                rec["token_f1"] = 0.0 if failed else round(score_prediction_max_annotator(rec["prediction"], it["references"])[0], 4)
                rec["containment_proxy"] = 0.0 if failed else round(compute_context_containment_proxy(rec["prediction"], context_text), 4)
                if it["question_type"] == "boolean":
                    gold = Counter(x["answer"] for x in it["references"] if x.get("type") == "boolean").most_common(1)
                    if gold:
                        rec["boolean_correct"] = int((None if rec["refusal"] else yes_no(rec["prediction"])) == gold[0][0])
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                if k % 100 == 0:
                    print(f"[generation {m}] {k}/{len(todo)}", flush=True)
            resources[f"generation_{m}"] = sampler.stop()
    unload_all()
    return resources


# ----------------------------------------------------------------------------- summary
def pct(xs, q):
    xs = sorted(xs)
    return round(xs[min(len(xs) - 1, int(q * len(xs)))], 3) if xs else None


def summarise(out, items, resources, extra, gen_items=None):
    import csv
    qids = {it["question_id"] for it in items}
    # Reported per QASPER split: Train papers were used to select methods and check alpha (current experiments);
    # Dev papers were used in the first-round (v1) experiments; Test papers were never used to choose a method.
    group = {it["question_id"]: it["split"] for it in items}

    def split_mean(rs, key):
        out = {}
        for g in ("train", "dev", "test"):
            sub = [r[key] for r in rs if group.get(r["question_id"]) == g]
            out[g] = round(sum(sub) / len(sub), 4) if sub else None
        return out
    ret = [r for r in read_jsonl(out / "retrieval_per_query.jsonl") if r["question_id"] in qids]
    gen_items = gen_items if gen_items is not None else items
    gen_qids = {it["question_id"] for it in gen_items}
    gen = [r for r in read_jsonl(out / "generation_per_query.jsonl") if r["question_id"] in gen_qids]

    def type_mean(rs, key):
        out = {}
        for t in ("extractive", "abstractive", "boolean"):
            sub = [r[key] for r in rs if r.get("question_type") == t]
            out[t] = round(sum(sub) / len(sub), 4) if sub else None
        return out
    rrows = []
    for pl in retrieval_pipelines():
        rs = [r for r in ret if r["retrieval_pipeline"] == pl]
        n = max(1, len(rs))
        rrows.append({"retrieval_pipeline": pl, "n_questions": len(rs),
                      "ndcg10": round(sum(r["ndcg10"] for r in rs) / n, 4), "mrr10": round(sum(r["mrr10"] for r in rs) / n, 4),
                      "cec_0.5": round(sum(r["cec_0.5"] for r in rs) / n, 4),
                      "context_tokens": round(sum(r["context_tokens"] for r in rs) / n, 1),
                      "n_units": round(sum(r["n_units"] for r in rs) / n, 2),
                      "gate_refusal_rate": round(sum(r["gate_score"] < GATES[pl] or r.get("no_units", False) for r in rs) / n, 4),
                      "retrieve_ms_p50": pct([r["retrieve_ms"] for r in rs], 0.5),
                      **{f"ndcg10_{g}": v for g, v in split_mean(rs, "ndcg10").items()},
                      **{f"cec_0.5_{g}": v for g, v in split_mean(rs, "cec_0.5").items()}})
    cec = {(r["retrieval_pipeline"], r["question_id"]): r["cec_0.5"] for r in ret}
    prod = {r["question_id"]: r["token_f1"] for r in gen if r["config"] == "HIER_E5_DENSE_LLAMA3B"}

    def by_evidence(gs, key):
        """Mean of key where the context contains the evidence (CEC=1) and where it does not (CEC=0)."""
        out = {}
        for v in (1, 0):
            sub = [r[key] for r in gs if cec.get((r["retrieval_pipeline"], r["question_id"])) == v]
            out["ctx_has_evidence" if v else "ctx_lacks_evidence"] = (round(sum(sub) / len(sub), 4) if sub else None, len(sub))
        return out

    grows = []
    for cid in configs():
        gs = [r for r in gen if r["config"] == cid]
        n = max(1, len(gs))
        boo = [r["boolean_correct"] for r in gs if "boolean_correct" in r]
        gtimes = [r["generate_s"] for r in gs if not r["gated"]]
        grows.append({"config": cid, "retrieval_pipeline": cid.rsplit("_", 1)[0], "llm": LLMS[cid.rsplit("_", 1)[1]],
                      "n_questions": len(gs), "token_f1": round(sum(r["token_f1"] for r in gs) / n, 4),
                      "refusal_rate": round(sum(r["refusal"] for r in gs) / n, 4),
                      "gate_refusals": sum(r["gated"] for r in gs),
                      "llm_refusals": sum(r["refusal"] and not r["gated"] for r in gs),
                      "generation_failures": sum(r["generation_failed"] for r in gs),
                      "containment_proxy": round(sum(r["containment_proxy"] for r in gs) / n, 4),
                      "boolean_correct": f"{sum(boo)}/{len(boo)}",
                      "generate_s_p50": pct(gtimes, 0.5), "generate_s_p95": pct(gtimes, 0.95),
                      **{f"token_f1_{g}": v for g, v in split_mean(gs, "token_f1").items()},
                      **{f"refusal_rate_{g}": v for g, v in split_mean(gs, "refusal").items()},
                      **{f"token_f1_{t}": v for t, v in type_mean(gs, "token_f1").items()},
                      **{f"refusal_rate_{t}": v for t, v in type_mean(gs, "refusal").items()},
                      # refusals are justified when the retrieved context lacks the evidence (all questions are answerable)
                      **{f"refusal_rate_{k}": v[0] for k, v in by_evidence(gs, "refusal").items()},
                      **{f"token_f1_{k}": v[0] for k, v in by_evidence(gs, "token_f1").items()},
                      "n_ctx_has_evidence": by_evidence(gs, "refusal")["ctx_has_evidence"][1],
                      # per-question comparison with the production configuration (Token F1)
                      "vs_production_better": sum(r["token_f1"] > prod[r["question_id"]] for r in gs if r["question_id"] in prod),
                      "vs_production_worse": sum(r["token_f1"] < prod[r["question_id"]] for r in gs if r["question_id"] in prod)})
    for name, rows in (("retrieval.csv", rrows), ("generation.csv", grows)):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    summary = {"experiment": "combination (16 configurations)", "dataset": str(DATASET.relative_to(ROOT)).replace("\\", "/"),
               "papers": len({it["paper_id"] for it in items}), "questions": len(items),
               "questions_by_split": dict(Counter(it["split"] for it in items)),
               "generation_questions": len(gen_items),
               "generation_questions_by_split": dict(Counter(it["split"] for it in gen_items)),
               "generation_questions_by_type": dict(Counter(it["question_type"] for it in gen_items)),
               "configs": {cid: config_params(cid) for cid in configs()},
               "retrieval": rrows, "generation": grows, "resources": resources, **extra}
    (out / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    return summary


# ----------------------------------------------------------------------------- profile helpers
def profile_papers(n=10):
    """10 papers spread over document length (word-count quartiles), seed 42, at least 2 uncached if available."""
    ds = json.load(open(DATASET, encoding="utf-8"))
    from eval_common import reval_pipeline as rp
    words = {}
    for pid, p in ds["papers"].items():
        f = ROOT / "eval" / "data" / "revalidation_cache" / "extract" / p["extraction_cache"]
        words.setdefault(str(f), None)
    lengths = {}
    for f in words:
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r["paper_id"] in ds["papers"]:
                lengths[r["paper_id"]] = len((r.get("full_text") or "").split())
    order = sorted(lengths, key=lambda p: lengths[p])
    rng = random.Random(SEED)
    quart = [order[i * len(order) // 4:(i + 1) * len(order) // 4] for i in range(4)]
    chosen = [order[-1]]                                       # the longest paper
    for i, qpapers in enumerate(quart):
        k = 3 if i in (1, 2) else 2
        chosen += rng.sample([p for p in qpapers if p not in chosen], k)
    chosen = chosen[:n]
    mb = rp.EMB_CACHE / EMBEDDERS["MBERT"].replace("/", "__") / "p"
    uncached = [p for p in chosen if not list(mb.glob(f"cret_{p}_hierarchical_*.npy"))]
    return chosen, {p: lengths[p] for p in chosen}, uncached


def estimate(items_all, timings):
    """Full-run estimate from the profile's per-stage timings and the manifest's cache state."""
    from eval_common import reval_pipeline as rp
    ds = json.load(open(DATASET, encoding="utf-8"))
    papers = list(ds["papers"])
    mean = lambda xs: sum(xs) / len(xs) if xs else 0.0  # noqa: E731
    est: Dict[str, Any] = {"papers": len(papers), "questions": len(items_all)}
    secs = {"extraction": mean(timings["extract_s"]) * len(papers) * len(EMBEDDERS)}
    for e, model in EMBEDDERS.items():
        d = rp.EMB_CACHE / model.replace("/", "__") / "p"
        for c, ch in CHUNKERS.items():
            missing = sum(1 for p in papers if not list(d.glob(f"cret_{p}_{ch}_*.npy")))
            chunks = mean(timings["chunks_per_paper"][c]) * missing
            secs[f"indexing_{e}_{c}"] = chunks * mean(timings["index_s_per_chunk"][e])
            est[f"papers_to_index_{e}_{c}"] = missing
    secs["retrieval"] = len(items_all) * sum(mean(v) for v in timings["retrieve_ms"].values()) / 1000
    for m in LLMS:
        n_gen = len(json.load(open(GEN_SAMPLE, encoding="utf-8"))["questions"])
        secs[f"generation_{m}"] = n_gen * len(retrieval_pipelines()) * mean(timings["generate_s"][m]) * (1 - 0.024)
    est["seconds_by_stage"] = {k: round(v) for k, v in secs.items()}
    est["total_hours"] = round(sum(secs.values()) / 3600, 1)
    est["note"] = ("generation time assumes no prompt reuse and the profile's mean time per answer; gate refusals "
                   "(~2.4%) skip generation")
    return est


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--retrieval-scope", choices=["all", "sample"], default="all",
                    help="all: retrieval metrics on every question of the combination set (~43 h in total); "
                         "sample: only on the questions of the 300 sampled papers (~32 h). Generation always uses the 300.")
    a = ap.parse_args()

    from eval_common import reval_pipeline as rp
    rp.setup_django()
    if a.list:
        for cid in configs():
            print(cid)
        print(f"{len(configs())} configurations ({len(set(configs()))} distinct), "
              f"{len(retrieval_pipelines())} retrieval pipelines")
        print(json.dumps({p: pipeline_params(p) for p in retrieval_pipelines()}, indent=1))
        return

    timings: Dict[str, Any] = {"model_load_s": {}, "llm_load_s": {}, "extract_s": [], "query_embed_s": defaultdict(list),
               "index_s_per_chunk": defaultdict(list), "chunks_per_paper": defaultdict(list),
               "retrieve_ms": defaultdict(list), "generate_s": defaultdict(list)}
    extra: Dict[str, Any] = {}
    if a.profile:
        papers, lengths, uncached = profile_papers()
        items = load_items(papers_subset=set(papers))
        out = OUT / "profile"
        extra["profile_papers"] = {"papers": lengths, "uncached_modernbert": uncached}
    elif a.limit:
        items = load_items(limit=a.limit)
        out = OUT / f"smoke_{a.limit}"
    else:
        gen = json.load(open(GEN_SAMPLE, encoding="utf-8"))["questions"]
        sample = {q["question_id"] for q in gen}
        items = load_items() if a.retrieval_scope == "all" else load_items(papers_subset={q["paper_id"] for q in gen})
        extra["retrieval_scope"] = a.retrieval_scope
        gen_items = [it for it in items if it["question_id"] in sample]
        assert len(gen_items) == len(sample), "generation sample not contained in the combination set"
        out = OUT
    if a.profile or a.limit:
        gen_items = items
    out.mkdir(parents=True, exist_ok=True)
    print(f"{len(configs())} configurations, {len(items)} questions, "
          f"{len({it['paper_id'] for it in items})} papers -> {out}", flush=True)

    from profile_generation_resources import unload_all
    unload_all()  # no LLM may stay resident while the embedder runs (memory)
    t0 = time.perf_counter()
    resources = run_retrieval(items, out, timings)
    t1 = time.perf_counter()
    resources.update(run_generation(gen_items, out, timings))
    t2 = time.perf_counter()
    extra["elapsed_s"] = {"retrieval": round(t1 - t0, 1), "generation": round(t2 - t1, 1)}
    if a.profile:
        mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
        extra["profile_timings"] = {
            "model_load_s": timings["model_load_s"], "llm_load_s": timings["llm_load_s"],
            "extract_s_per_paper": mean(timings["extract_s"]),
            "index_s_per_uncached_chunk": {e: mean(v) for e, v in timings["index_s_per_chunk"].items()},
            "chunks_per_paper": {c: mean(v) for c, v in timings["chunks_per_paper"].items()},
            "retrieve_ms_per_query": {p: mean(v) for p, v in timings["retrieve_ms"].items()},
            "generate_s_per_answer": {m: mean(v) for m, v in timings["generate_s"].items()}}
        extra["full_run_estimate"] = estimate(load_items(), timings)
    s = summarise(out, items, resources, extra, gen_items)
    print(json.dumps({"retrieval": s["retrieval"], "generation": [
        {k: g[k] for k in ("config", "n_questions", "token_f1", "refusal_rate")} for g in s["generation"]],
        "resources": resources, **{k: v for k, v in extra.items() if k != "profile_papers"}}, indent=1))


if __name__ == "__main__":
    main()
