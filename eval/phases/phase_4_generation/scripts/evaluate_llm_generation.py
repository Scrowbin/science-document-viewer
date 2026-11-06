#!/usr/bin/env python3
"""
Phase 4: LLM (answer generation) evaluation, run on Kaggle with Ollama.

Questions (same cohorts as Phases 2-3):
  C-RET       QASPER, 335 papers / 567 questions; references rebuilt from the official QASPER JSON with
              is_atomic_eligible (an annotator gave an answer AND text evidence); answer type extractive /
              abstractive / boolean
  PEERQA-PDF  PeerQA, the questions with an author-written free-form answer (answer_free_form)

Two context conditions:
  gold        the evidence passages of the question (retrieval_evidence): generation only
  retrieved   the context the app would build: ranking with a Phase 3 pipeline (--pipeline embedder:arm),
              hierarchical chunks expanded to parent sections, <= 5 units, <= 1,600 estimated tokens
              (eval_common.reval_pipeline.assemble, same rules as production). No similarity gate: the app's
              0.80 cutoff is calibrated for e5 only.
The gap gold - retrieved shows how much answer quality is lost to retrieval.

LLMs (Ollama, the quantized models the app would run): llama3.2:3b (app default), qwen2.5:1.5b, phi4-mini,
qwen3:4b (thinking off), gemma3:4b. Prompt = production rag_service.build_answer_prompt with the same refusal
sentence. Options: temperature 0, num_ctx 4096, num_predict 256, seed 42.

Metrics (descriptive, no statistical tests):
  token_f1          max over references (QASPER evaluator convention); refusals score 0
  refusal           the answer contains the prompt's refusal sentence
  containment       share of informative answer tokens found in the context (lexical proxy, NOT faithfulness)
  boolean_correct   yes/no questions: first yes/no in the answer equals the gold majority
  latency           wall time per answer, tokens/s (device recorded; Kaggle GPU is not the app's CPU)

LLM-as-judge (--judge): Gemini (default gemini-2.5-flash, Google Gemini API; key from the environment variable
GEMINI_API, read from .env) gives each answer one of the 6 human-check labels. The judge is used only for this
evaluation, never by the application. A model name without the "gemini" prefix is run through Ollama instead
(SUPPORTED, MISSING_INFO - PARTIAL, MISSING_INFO - UNJUSTIFIED_REFUSAL, REFUSAL_VALID, UNSUPPORTED,
CONTRADICTED), judging only against the context given to the model. --judge-validate first runs the judge on the
100 answers already labelled by a human (generation human checks, rounds 1-2) and reports the share of answers
where the judge gives the same label as the human (and a confusion table); only then should judge labels be reported.

Outputs: eval/phases/phase_4_generation/artifacts/
  <cohort>/<condition>/per_query.jsonl   one row per (model, question); resumable
  <cohort>/<condition>/summary.json, REPORT.md
  <cohort>/retrieved_contexts_<pipeline>.jsonl
  judge_validation.json, <cohort>/<condition>/judge.jsonl
  summary.json                           all cohorts/conditions + gold-retrieved gaps

Usage (Kaggle, after `ollama serve &`):
  python .../evaluate_llm_generation.py --condition gold
  python .../evaluate_llm_generation.py --condition retrieved --pipeline qwen:convex+bgem3
  python .../evaluate_llm_generation.py --judge-validate
  python .../evaluate_llm_generation.py --judge
  smoke test: --cohort C-RET --limit 3 --models llama3.2:3b
"""

import argparse
import csv
import importlib.util
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import requests

ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / "eval" / "phases" / "phase_4_generation" / "artifacts"
P9 = ROOT / "eval" / "phases" / "phase_9_generation"
P3_PATH = ROOT / "eval" / "phases" / "phase_3_hybrid_reranking" / "scripts" / "evaluate_hybrid_reranking.py"
OLLAMA = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

MODELS = ["llama3.2:3b", "qwen2.5:1.5b", "phi4-mini", "qwen3:4b", "gemma3:4b"]
THINKING_MODELS = ("qwen3",)  # sent think=false
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-2.5-flash")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEN_OPTIONS = {"temperature": 0, "num_ctx": 4096, "num_predict": 256, "seed": 42}
JUDGE_OPTIONS = {"temperature": 0, "num_ctx": 8192, "num_predict": 200, "seed": 42}
COHORTS = ["C-RET", "PEERQA-PDF"]
BUDGET, MAX_UNITS = 1600, 5
LABELS = ["SUPPORTED", "MISSING_INFO - PARTIAL", "MISSING_INFO - UNJUSTIFIED_REFUSAL", "REFUSAL_VALID",
          "UNSUPPORTED", "CONTRADICTED"]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Phase 3 module: sets up Django and gives Phase 2 helpers (sections, units, ranking, rerankers)
p3 = _load("phase3_hybrid_reranking", P3_PATH)
p2, rp, rr = p3.p2, p3.rp, p3.rr
gen9 = _load("phase9_generation", P9 / "scripts" / "evaluate_generation.py")              # F1, containment
man9 = _load("phase9_manifest", P9 / "scripts" / "generate_sample_manifest_250.py")       # is_atomic_eligible
from apps.documents.services.rag_service import build_answer_prompt  # noqa: E402
from langchain_core.documents import Document  # noqa: E402

REFUSAL = gen9.REFUSAL_MESSAGE


# ----------------------------------------------------------------------------- Ollama
def ollama_ready(model: str) -> None:
    tags = requests.get(f"{OLLAMA}/api/tags", timeout=10).json().get("models", [])
    names = {m["name"] for m in tags} | {m["name"].split(":latest")[0] for m in tags}
    if model not in names:
        print(f"  pulling {model} ...", flush=True)
        r = requests.post(f"{OLLAMA}/api/pull", json={"model": model, "stream": False}, timeout=3600)
        r.raise_for_status()


def ollama_unload(model: str) -> None:
    try:
        requests.post(f"{OLLAMA}/api/generate", json={"model": model, "keep_alive": 0}, timeout=60)
    except requests.RequestException:
        pass


def ollama_generate(model: str, prompt: str, options: Dict[str, Any], fmt: Optional[str] = None,
                    timeout: int = 300, tries: int = 3) -> Dict[str, Any]:
    body: Dict[str, Any] = {"model": model, "prompt": prompt, "stream": False, "options": options,
                            "keep_alive": "30m"}
    if any(model.startswith(t) for t in THINKING_MODELS):
        body["think"] = False
    if fmt:
        body["format"] = fmt
    last = None
    for attempt in range(tries):
        try:
            t0 = time.perf_counter()
            r = requests.post(f"{OLLAMA}/api/generate", json=body, timeout=timeout)
            r.raise_for_status()
            d = r.json()
            ec, ed = d.get("eval_count") or 0, d.get("eval_duration") or 0
            return {"text": (d.get("response") or "").strip(), "wall_s": round(time.perf_counter() - t0, 3),
                    "eval_count": ec, "prompt_eval_count": d.get("prompt_eval_count"),
                    "tokens_per_s": round(ec / (ed / 1e9), 2) if ed else None, "error": None}
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
            time.sleep(5 * (attempt + 1))
    return {"text": "", "wall_s": None, "eval_count": 0, "prompt_eval_count": None, "tokens_per_s": None,
            "error": last}


# ----------------------------------------------------------------------------- questions
def load_questions(cohort: str, limit: Optional[int]) -> List[Dict[str, Any]]:
    groups = rr.group_items(rr.load_cohort(cohort))
    papers = sorted(groups)[:limit] if limit else sorted(groups)
    out, skipped = [], Counter()
    for pid in papers:
        title = ""
        qas: Dict[str, Any] = {}
        if cohort != "PEERQA-PDF":
            for split in ("train", "dev", "test"):
                pdata = p2._load_qasper_split(split).get(pid)
                if pdata:
                    title = pdata.get("title", "")
                    qas = {qa["question_id"]: qa for qa in pdata.get("qas", [])}
                    break
        for i, it in enumerate(groups[pid]):
            qid = p2.make_qid(pid, i, it)
            if cohort == "PEERQA-PDF":
                ans = (it.get("answer_free_form") or "").strip()
                if not ans:
                    skipped["no_free_form_answer"] += 1
                    continue
                refs = [{"answer": ans, "type": "abstractive"}]
            else:
                qa = qas.get(it.get("question_id"))
                if not qa:
                    skipped["question_not_in_qasper_json"] += 1
                    continue
                ok, refs, _ = man9.is_atomic_eligible(qa)
                if not ok:
                    skipped["no_answer_with_evidence"] += 1
                    continue
            types = Counter(r["type"] for r in refs)
            yn = [r["answer"] for r in refs if r["type"] == "boolean"]
            out.append({"cohort": cohort, "paper_id": pid, "question_id": qid, "question": it["question"],
                        "title": title, "refs": refs, "answer_type": types.most_common(1)[0][0],
                        "gold_yes_no": Counter(yn).most_common(1)[0][0] if yn else None,
                        "evidence": [e for e in it.get("retrieval_evidence", []) if isinstance(e, str) and e.strip()]})
    print(f"{cohort}: {len(out)} questions with references (skipped {dict(skipped)})", flush=True)
    return out


# ----------------------------------------------------------------------------- contexts
def gold_context(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{"text": e, "page": "n/a", "section": "Evidence"} for e in q["evidence"]]


def retrieval_order(pipeline: str, units: List[Dict[str, Any]], um: Optional[np.ndarray],
                    qv: Optional[np.ndarray], question: str, qkey: str, rerankers: Dict[str, Any]) -> List[int]:
    emb, arm = pipeline.split(":", 1) if ":" in pipeline else ("-", pipeline)
    texts = [u["text"] for u in units]
    if arm == "bm25":
        return [int(i) for i in np.argsort(-rp.bm25_scores(texts, question, "regex"), kind="stable")]
    base, _, rer = arm.partition("+")
    dense = um @ qv
    if base == "dense":
        order = [int(i) for i in np.argsort(-dense, kind="stable")]
    elif base == "rrf":
        order = rp.rrf(dense, rp.bm25_scores(texts, question, "regex"))
    elif base == "convex":
        order = rp.convex(dense, rp.bm25_scores(texts, question, "regex"))
    else:
        raise ValueError(f"unknown arm {arm!r}")
    if rer:
        order, _ = rerankers[rer].rerank(qkey, question, order, texts)
    return order


def build_retrieved_contexts(cohort: str, qs: List[Dict[str, Any]], pipeline: str) -> Dict[str, List[Dict[str, Any]]]:
    path = ART / cohort.lower().replace("-", "_") / f"retrieved_contexts_{pipeline.replace(':', '_').replace('+', '_')}.jsonl"
    cached: Dict[str, List[Dict[str, Any]]] = {}
    if path.exists():
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            cached[f"{r['paper_id']}|{r['question_id']}"] = r["docs"]
    todo = [q for q in qs if f"{q['paper_id']}|{q['question_id']}" not in cached]
    if not todo:
        return cached
    emb = pipeline.split(":", 1)[0] if ":" in pipeline else None
    model_name = p2.MODEL_MAP[emb] if emb and emb != "-" else None
    rer_label = pipeline.split("+", 1)[1] if "+" in pipeline else None
    rerankers = {rer_label: p3.Reranker(rer_label, p3.RERANKERS[rer_label])} if rer_label else {}
    tag = cohort.lower().replace("-", "_")
    path.parent.mkdir(parents=True, exist_ok=True)
    by_paper: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for q in todo:
        by_paper[q["paper_id"]].append(q)
    with open(path, "a", encoding="utf-8") as f:
        for pid, pqs in by_paper.items():
            secs, _ = p2.load_sections_for_cohort(cohort, pid)
            units = p2.build_units_by_strategy(secs, "hierarchical", pid) if secs else []
            if not units:
                for q in pqs:
                    cached[f"{pid}|{q['question_id']}"] = []
                continue
            um = qvs = None
            if model_name:
                texts = [u["text"] for u in units]
                h = p2.hashlib.md5("\x00".join(texts).encode()).hexdigest()[:8]
                um = p2.normalize_l2(rp.cached_embed(model_name, texts, False, f"{tag}_{p2.safe_pid(pid)}_hierarchical_{emb}_{h}"))
                qvs = p2.normalize_l2(rp.embed(model_name, [q["question"] for q in pqs], True))
            for j, q in enumerate(pqs):
                order = retrieval_order(pipeline, units, um, None if qvs is None else qvs[j], q["question"],
                                        f"{pid}|{q['question_id']}", rerankers)
                ctx = rp.assemble(order, units, "hierarchical", budget=BUDGET, max_units=MAX_UNITS)
                first = {}
                for u in units:
                    first.setdefault(u.get("parent_id"), u)
                docs = [{"text": c["text"], "tokens": c["tokens"], "unit_id": c["unit_id"],
                         "page": first.get(c["unit_id"], {}).get("page_start", "n/a"),
                         "section": first.get(c["unit_id"], {}).get("section", "")} for c in ctx]
                cached[f"{pid}|{q['question_id']}"] = docs
                f.write(json.dumps({"paper_id": pid, "question_id": q["question_id"], "pipeline": pipeline,
                                    "docs": docs}) + "\n")
    if model_name:
        rp._MODELS.pop(model_name, None)
    return cached


# ----------------------------------------------------------------------------- generation
def is_refusal(text: str) -> bool:
    t = text.lower()
    return REFUSAL.lower() in t or "does not contain sufficient" in t


def score(q: Dict[str, Any], answer: str, context_text: str) -> Dict[str, Any]:
    ref = is_refusal(answer)
    if ref or not answer:
        f1, ptype = 0.0, q["answer_type"]
        cont = 0.0
    else:
        f1, _, _, ptype = gen9.score_prediction_max_annotator(answer, q["refs"])
        cont = gen9.compute_context_containment_proxy(answer, context_text)
    bc = None
    if q["gold_yes_no"] is not None and q["answer_type"] == "boolean":
        import re
        m = re.search(r"\b(yes|no)\b", answer.lower())
        bc = bool(m and not ref and m.group(1).capitalize() == q["gold_yes_no"])
    return {"token_f1": round(f1, 4), "refusal": ref, "containment": round(cont, 4), "boolean_correct": bc,
            "best_ref_type": ptype}


def run_generation(cohort: str, condition: str, pipeline: Optional[str], models: List[str],
                   limit: Optional[int]) -> Dict[str, Any]:
    qs = load_questions(cohort, limit)
    out_dir = ART / cohort.lower().replace("-", "_") / (condition if condition == "gold"
                                                       else f"retrieved_{pipeline.replace(':', '_').replace('+', '_')}")
    if limit:
        out_dir = out_dir.with_name(out_dir.name + f"_smoke_{limit}")
    out_dir.mkdir(parents=True, exist_ok=True)
    contexts = ({f"{q['paper_id']}|{q['question_id']}": gold_context(q) for q in qs} if condition == "gold"
                else build_retrieved_contexts(cohort, qs, pipeline))
    pq = out_dir / "per_query.jsonl"
    done = set()
    if pq.exists():
        for line in open(pq, encoding="utf-8"):
            r = json.loads(line)
            done.add((r["model"], r["paper_id"], r["question_id"]))
    with open(pq, "a", encoding="utf-8") as f:
        for model in models:
            todo = [q for q in qs if (model, q["paper_id"], q["question_id"]) not in done]
            if not todo:
                print(f"  {model}: complete", flush=True)
                continue
            ollama_ready(model)
            ollama_generate(model, "Say OK.", GEN_OPTIONS)  # load the model; excluded from latency
            print(f"  {model}: {len(todo)} questions [{cohort} / {out_dir.name}]", flush=True)
            for n, q in enumerate(todo, 1):
                docs = contexts.get(f"{q['paper_id']}|{q['question_id']}", [])
                lc_docs = [Document(page_content=d["text"], metadata={"page": d.get("page", "n/a"),
                                                                      "section": d.get("section") or "Main"})
                           for d in docs]
                prompt = build_answer_prompt(q["question"], q["title"], lc_docs, REFUSAL)
                res = ollama_generate(model, prompt, GEN_OPTIONS)
                ctx_text = "\n\n".join(d["text"] for d in docs)
                row = {"cohort": cohort, "condition": condition, "pipeline": pipeline, "model": model,
                       "paper_id": q["paper_id"], "question_id": q["question_id"], "answer_type": q["answer_type"],
                       "question": q["question"], "answer": res["text"], "error": res["error"],
                       "context_units": len(docs), "context_tokens": sum(d.get("tokens", 0) for d in docs),
                       "wall_s": res["wall_s"], "tokens_per_s": res["tokens_per_s"],
                       "prompt_eval_count": res["prompt_eval_count"], **score(q, res["text"], ctx_text)}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                if n % 25 == 0:
                    f.flush()
                    print(f"    {n}/{len(todo)}", flush=True)
            f.flush()
            ollama_unload(model)
    summary = summarise_dir(out_dir, models)
    return summary


def summarise_dir(out_dir: Path, models: List[str]) -> Dict[str, Any]:
    rows = [json.loads(line) for line in open(out_dir / "per_query.jsonl", encoding="utf-8")]
    judge = {}
    jp = out_dir / "judge.jsonl"
    if jp.exists():
        for line in open(jp, encoding="utf-8"):
            j = json.loads(line)
            judge[(j["model"], j["paper_id"], j["question_id"])] = j["label"]
    res: Dict[str, Any] = {"dir": out_dir.name, "models": {}}
    for m in models:
        rs = [r for r in rows if r["model"] == m]
        if not rs:
            continue
        lat = [r["wall_s"] for r in rs if r["wall_s"] is not None]
        tps = [r["tokens_per_s"] for r in rs if r["tokens_per_s"]]
        bc = [r["boolean_correct"] for r in rs if r["boolean_correct"] is not None]
        d = {"n": len(rs), "token_f1": round(float(np.mean([r["token_f1"] for r in rs])), 4),
             "refusal_rate": round(float(np.mean([r["refusal"] for r in rs])), 4),
             "containment": round(float(np.mean([r["containment"] for r in rs if not r["refusal"]] or [0])), 4),
             "boolean_accuracy": f"{sum(bc)}/{len(bc)}" if bc else None,
             "errors": sum(1 for r in rs if r["error"]),
             "latency_s_p50": round(float(np.percentile(lat, 50)), 2) if lat else None,
             "latency_s_p95": round(float(np.percentile(lat, 95)), 2) if lat else None,
             "tokens_per_s_p50": round(float(np.percentile(tps, 50)), 1) if tps else None,
             "by_type": {}}
        for t in ("extractive", "abstractive", "boolean"):
            rt = [r for r in rs if r["answer_type"] == t]
            if rt:
                d["by_type"][t] = {"n": len(rt), "token_f1": round(float(np.mean([r["token_f1"] for r in rt])), 4),
                                   "refusal_rate": round(float(np.mean([r["refusal"] for r in rt])), 4)}
        jl = [judge[(m, r["paper_id"], r["question_id"])] for r in rs if (m, r["paper_id"], r["question_id"]) in judge]
        if jl:
            d["judge_labels"] = dict(Counter(jl))
            d["judge_n"] = len(jl)
        res["models"][m] = d
    (out_dir / "summary.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    L = [f"# Phase 4: LLM evaluation ({out_dir.parent.name} / {out_dir.name})", "",
         "| Model | n | Token F1 | Refusal | Containment (non-refusals) | Yes/No correct | p50 s | p95 s | tok/s |",
         "|---|---|---|---|---|---|---|---|---|"]
    for m, d in res["models"].items():
        L.append(f"| {m} | {d['n']} | {d['token_f1']:.4f} | {d['refusal_rate']:.3f} | {d['containment']:.3f} | "
                 f"{d['boolean_accuracy'] or '–'} | {d['latency_s_p50']} | {d['latency_s_p95']} | {d['tokens_per_s_p50']} |")
    if any("judge_labels" in d for d in res["models"].values()):
        L += ["", "## Judge labels", "", "| Model | " + " | ".join(LABELS) + " |", "|---|" + "---|" * len(LABELS)]
        for m, d in res["models"].items():
            jl = d.get("judge_labels", {})
            L.append(f"| {m} | " + " | ".join(str(jl.get(lb, 0)) for lb in LABELS) + " |")
    (out_dir / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return res


# ----------------------------------------------------------------------------- judge
JUDGE_PROMPT = """You are checking whether an AI answer is grounded in a context taken from a scientific paper.
Judge ONLY against the context below. Do not use outside knowledge.

Labels (if several apply, use the first in this order):
CONTRADICTED: at least one claim in the answer conflicts with the context.
UNSUPPORTED: at least one substantive claim is not stated in or implied by the context (but does not contradict it).
MISSING_INFO - UNJUSTIFIED_REFUSAL: the answer refuses or says the information is missing, but the context does contain the answer.
MISSING_INFO - PARTIAL: grounded, but leaves out a key part of the answer that the context contains.
REFUSAL_VALID: the answer refuses and the context really does not contain the answer.
SUPPORTED: every substantive claim is stated in or follows from the context.

Context:
<<<
{context}
>>>

Question: {question}

Answer to check:
<<<
{answer}
>>>

Reply with JSON only: {{"label": "<one of the six labels>", "reason": "<one sentence>"}}"""


def load_env() -> None:
    """Read GEMINI_API from .env files: repo root, then backend/ (Django already loads backend/.env), then cwd."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env in (ROOT / ".env", ROOT / "backend" / ".env", Path.cwd() / ".env"):
        if env.exists():
            load_dotenv(env, override=False)


def is_gemini(model: str) -> bool:
    return model.lower().startswith("gemini")


def gemini_generate(model: str, prompt: str, tries: int = 6) -> Dict[str, Any]:
    """Gemini API generateContent with JSON output; retries with backoff on 429/5xx (free-tier rate limits)."""
    key = os.environ.get("GEMINI_API")
    if not key:
        raise SystemExit("GEMINI_API is not set: put GEMINI_API=<key> in .env (repo root or backend/) "
                         "or in the environment (Kaggle: Secrets).")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    delay, last = 5.0, None
    for _ in range(tries):
        try:
            t0 = time.perf_counter()
            r = requests.post(GEMINI_URL.format(model=model), json=body, timeout=120,
                              headers={"x-goog-api-key": key, "Content-Type": "application/json"})
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(delay)
                delay = min(delay * 2, 120)
                continue
            r.raise_for_status()
            d = r.json()
            cand = (d.get("candidates") or [{}])[0]
            text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", [])).strip()
            return {"text": text, "wall_s": round(time.perf_counter() - t0, 3),
                    "error": None if text else f"empty response ({cand.get('finishReason')})"}
        except requests.RequestException as e:
            last = f"{type(e).__name__}: {str(e).split('?')[0]}"  # never echo the key
            time.sleep(delay)
            delay = min(delay * 2, 120)
    return {"text": "", "wall_s": None, "error": last}


ALIASES = {"PARTIAL": "MISSING_INFO - PARTIAL", "UNJUSTIFIED_REFUSAL": "MISSING_INFO - UNJUSTIFIED_REFUSAL"}


def normalise_label(raw: Any) -> str:
    label = " ".join(str(raw).strip().upper().replace("–", "-").replace("_-_", " - ").split())
    label = label.replace("MISSING_INFO-", "MISSING_INFO - ").replace("MISSING_INFO_", "MISSING_INFO - ")
    if label in LABELS:
        return label
    for lb in sorted(LABELS, key=len, reverse=True):  # longest first: UNSUPPORTED before SUPPORTED
        if lb in label:
            return lb
    for short, lb in sorted(ALIASES.items(), key=lambda kv: -len(kv[0])):
        if short in label:
            return lb
    return "INVALID"


def judge_one(judge_model: str, context: str, question: str, answer: str) -> Tuple[str, str]:
    prompt = JUDGE_PROMPT.format(context=context[:24000], question=question, answer=answer or "(empty answer)")
    res = gemini_generate(judge_model, prompt) if is_gemini(judge_model) else \
        ollama_generate(judge_model, prompt, JUDGE_OPTIONS, fmt="json")
    try:
        d = json.loads(res["text"])
        if isinstance(d, list):
            d = d[0] if d else {}
        return normalise_label(d.get("label", "")), str(d.get("reason", ""))[:300]
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "INVALID", res["text"][:200] or (res["error"] or "")


def judge_ready(judge_model: str) -> None:
    if is_gemini(judge_model):
        load_env()
        if not os.environ.get("GEMINI_API"):
            raise SystemExit("GEMINI_API is not set: put GEMINI_API=<key> in .env (repo root or backend/).")
    else:
        ollama_ready(judge_model)


def collapse(label: str) -> str:
    if label in ("SUPPORTED", "MISSING_INFO - PARTIAL"):
        return "grounded"
    if label in ("UNSUPPORTED", "CONTRADICTED"):
        return "not_grounded"
    if label in ("REFUSAL_VALID", "MISSING_INFO - UNJUSTIFIED_REFUSAL"):
        return "refusal"
    return label


def human_labelled_answers() -> List[Dict[str, Any]]:
    """The 100 human-labelled answers (generation human checks round 1: 60, round 2: 40; final labels)."""
    hf = P9 / "artifacts" / "human_faithfulness_review"
    t1 = {(r["question_id"], r["model_answer"].strip()): r
          for r in csv.DictReader(open(hf / "faithfulness_annotation_template_60a.csv", encoding="utf-8-sig"))}
    out = []
    for line in open(hf / "correction" / "faithfulness_annotations_unblinded_corrected.jsonl", encoding="utf-8"):
        r = json.loads(line)
        t = t1.get((r["question_id"], (r["answer"] or "").strip()))
        if t:
            out.append({"round": 1, "id": r["review_id"], "model": r["actual_model"], "question": t["question_text"],
                        "context": t["context_text"], "answer": t["model_answer"], "human": r["final_primary_label"]})
    mp = json.load(open(hf / "extra_models" / "restricted_model_label_mapping.json", encoding="utf-8"))
    who = {(m["review_item_id"], m["blind_label"]): m["actual_model"] for m in mp["mapping"]}
    for r in csv.DictReader(open(hf / "extra_models" / "annotation_template_40a.csv", encoding="utf-8-sig")):
        out.append({"round": 2, "id": f"{r['review_item_id']}/{r['blind_label']}",
                    "model": who.get((r["review_item_id"], r["blind_label"])), "question": r["question_text"],
                    "context": r["context_text"], "answer": r["model_answer"], "human": r["primary_label"].strip()})
    return out


def judge_validate(judge_model: str, limit: Optional[int]) -> Dict[str, Any]:
    items = human_labelled_answers()[:limit] if limit else human_labelled_answers()
    judge_ready(judge_model)
    rows = []
    for it in items:
        label, reason = judge_one(judge_model, it["context"], it["question"], it["answer"])
        rows.append({**{k: it[k] for k in ("round", "id", "model", "human")}, "judge": label, "reason": reason})
    h, j = [r["human"] for r in rows], [r["judge"] for r in rows]
    hc, jc = [collapse(x) for x in h], [collapse(x) for x in j]
    conf: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for a, b in zip(h, j):
        conf[a][b] += 1
    res = {"judge_model": judge_model, "n": len(rows),
           "agreement_6_labels": round(sum(a == b for a, b in zip(h, j)) / len(rows), 4),
           "agreement_3_classes": round(sum(a == b for a, b in zip(hc, jc)) / len(rows), 4),
           "classes_3": "grounded = SUPPORTED/PARTIAL; not_grounded = UNSUPPORTED/CONTRADICTED; "
                        "refusal = REFUSAL_VALID/UNJUSTIFIED_REFUSAL",
           "confusion_human_rows_judge_cols": {k: dict(v) for k, v in conf.items()},
           "invalid_outputs": j.count("INVALID"), "rows": rows}
    ART.mkdir(parents=True, exist_ok=True)
    name = "judge_validation.json" if not limit else f"judge_validation_smoke_{limit}.json"
    (ART / name).write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Judge {judge_model} vs human on {len(rows)} answers: 6-label agreement {res['agreement_6_labels']} "
          f"3-class agreement {res['agreement_3_classes']} "
          f"invalid {res['invalid_outputs']}", flush=True)
    return res


def judge_runs(judge_model: str, models: List[str]) -> None:
    judge_ready(judge_model)
    for pq in sorted(ART.glob("*/*/per_query.jsonl")):
        if "_smoke_" in pq.parent.name:
            continue
        jp = pq.parent / "judge.jsonl"
        done = set()
        if jp.exists():
            done = {(j["model"], j["paper_id"], j["question_id"]) for j in map(json.loads, open(jp, encoding="utf-8"))}
        rows = [json.loads(line) for line in open(pq, encoding="utf-8")]
        todo = [r for r in rows if (r["model"], r["paper_id"], r["question_id"]) not in done and r["model"] in models]
        if not todo:
            continue
        cohort = rows[0]["cohort"]
        qs = {q["question_id"]: q for q in load_questions(cohort, None)}
        ctxs = ({k: v for k, v in ((f"{q['paper_id']}|{q['question_id']}", gold_context(q)) for q in qs.values())}
                if rows[0]["condition"] == "gold" else build_retrieved_contexts(cohort, list(qs.values()), rows[0]["pipeline"]))
        print(f"Judging {len(todo)} answers in {pq.parent}", flush=True)
        with open(jp, "a", encoding="utf-8") as f:
            for n, r in enumerate(todo, 1):
                ctx = "\n\n".join(d["text"] for d in ctxs.get(f"{r['paper_id']}|{r['question_id']}", []))
                label, reason = judge_one(judge_model, ctx, r["question"], r["answer"])
                f.write(json.dumps({"model": r["model"], "paper_id": r["paper_id"], "question_id": r["question_id"],
                                    "label": label, "reason": reason, "judge_model": judge_model}) + "\n")
                if n % 50 == 0:
                    f.flush()
                    print(f"    {n}/{len(todo)}", flush=True)
        summarise_dir(pq.parent, MODELS)


def combined_summary() -> None:
    out: Dict[str, Any] = {}
    for s in sorted(ART.glob("*/*/summary.json")):
        if "_smoke_" in s.parent.name:
            continue
        out.setdefault(s.parent.parent.name, {})[s.parent.name] = json.load(open(s, encoding="utf-8"))["models"]
    for cohort, conds in out.items():
        gold = conds.get("gold", {})
        for cond, models in list(conds.items()):
            if cond.startswith("retrieved") and gold:
                conds[f"gap_gold_minus_{cond}"] = {
                    m: {"token_f1": round(gold[m]["token_f1"] - d["token_f1"], 4),
                        "refusal_rate": round(gold[m]["refusal_rate"] - d["refusal_rate"], 4)}
                    for m, d in models.items() if m in gold}
    ART.mkdir(parents=True, exist_ok=True)
    (ART / "summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 4 LLM evaluation (Ollama)")
    ap.add_argument("--cohort", choices=COHORTS + ["all"], default="all")
    ap.add_argument("--condition", choices=["gold", "retrieved"])
    ap.add_argument("--pipeline", help="Phase 3 arm for --condition retrieved, e.g. qwen:convex+bgem3, e5:dense, bm25")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--limit", type=int, help="papers per cohort (smoke test)")
    ap.add_argument("--judge", action="store_true", help="label all generated answers with the judge model")
    ap.add_argument("--judge-validate", action="store_true", help="run the judge on the 100 human-labelled answers")
    ap.add_argument("--judge-model", default=JUDGE_MODEL,
                    help="gemini-* uses the Gemini API (key GEMINI_API in .env); any other name runs through Ollama")
    a = ap.parse_args()
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    if a.judge_validate:
        judge_validate(a.judge_model, a.limit)
    if a.condition:
        if a.condition == "retrieved" and not a.pipeline:
            ap.error("--condition retrieved needs --pipeline (choose it from the Phase 3 results)")
        for c in (COHORTS if a.cohort == "all" else [a.cohort]):
            run_generation(c, a.condition, a.pipeline, models, a.limit)
    if a.judge:
        judge_runs(a.judge_model, models)
    if not (a.judge_validate or a.condition or a.judge):
        ap.error("nothing to do: give --condition, --judge-validate and/or --judge")
    combined_summary()


if __name__ == "__main__":
    main()
