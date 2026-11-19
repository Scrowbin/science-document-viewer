"""Small follow-up probe: does gemma3:4b refuse because of the strict refusal instruction?

Setup (approved by the user on 2026-11-19, not part of the main Phase 4 run):
- 50 C-RET gold-context questions, sampled with seed 42 and stratified by answer type in the
  proportions of the full 567 (30 extractive, 12 abstractive, 8 boolean).
- gemma3:4b via local Ollama (CPU), same generation options as Phase 4 (temperature 0, seed 42).
- Two prompts, identical except for the refusal instruction:
    production : rag_service.build_answer_prompt (as in Phase 4)
    soft       : allows paraphrase and short yes/no inference; refuse only if nothing relevant
- The production arm is also compared with the Kaggle GPU answers to check the local rerun.

Output: eval/phases/phase_4_generation/artifacts/gemma_refusal_probe/{per_query.jsonl, summary.json}
Run:    backend/venv/Scripts/python.exe eval/phases/phase_4_generation/scripts/gemma_refusal_probe.py
"""
import importlib.util
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("p4", HERE / "evaluate_llm_generation.py")
p4 = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0]]
spec.loader.exec_module(p4)

MODEL = "gemma3:4b"
SEED = 42
PER_TYPE = {"extractive": 30, "abstractive": 12, "boolean": 8}
OUT = p4.ART / "gemma_refusal_probe"
KAGGLE = p4.ART / "c_ret" / "gold" / "per_query.jsonl"


def soft_prompt(question, doc_title, docs, refusal_message):
    context_str = "\n\n".join(
        f"--- Snippet (Page {d.metadata.get('page', 1)}, Section: {d.metadata.get('section', 'Main')}) ---\n{d.page_content}"
        for d in docs
    )
    return (
        f'You are a precise academic research assistant reading "{doc_title or "the document"}".\n'
        f"Use the provided context below to answer the user's question clearly and accurately.\n"
        f"Respond in the same language as the user's question.\n"
        f"The context may state the answer in different words than the question. For yes/no questions, "
        f"answer Yes or No when the context supports it, even if it does not say so literally.\n"
        f"Only if the context contains nothing relevant to the question, state: '{refusal_message}'\n"
        f"Do NOT add facts that are not in the context.\n\n"
        f"Context:\n{context_str}\n\nQuestion: {question}\n\nAnswer:"
    )


PROMPTS = {"production": p4.build_answer_prompt, "soft": soft_prompt}


def main():
    qs = p4.load_questions("C-RET", None)
    rng = random.Random(SEED)
    sample = []
    for t, n in PER_TYPE.items():
        pool = sorted((q for q in qs if q["answer_type"] == t), key=lambda q: (q["paper_id"], q["question_id"]))
        sample += rng.sample(pool, n)
    kaggle = {}
    for line in open(KAGGLE, encoding="utf-8"):
        r = json.loads(line)
        if r["model"] == MODEL:
            kaggle[(r["paper_id"], r["question_id"])] = r

    OUT.mkdir(parents=True, exist_ok=True)
    pq = OUT / "per_query.jsonl"
    done = set()
    if pq.exists():
        done = {(r["prompt"], r["paper_id"], r["question_id"]) for r in map(json.loads, open(pq, encoding="utf-8"))}
    p4.ollama_ready(MODEL)
    p4.ollama_generate(MODEL, "Say OK.", p4.GEN_OPTIONS)
    with open(pq, "a", encoding="utf-8") as f:
        for name, build in PROMPTS.items():
            for n, q in enumerate(sample, 1):
                if (name, q["paper_id"], q["question_id"]) in done:
                    continue
                docs = [p4.Document(page_content=d["text"], metadata={"page": d["page"], "section": d["section"]})
                        for d in p4.gold_context(q)]
                res = p4.ollama_generate(MODEL, build(q["question"], q["title"], docs, p4.REFUSAL), p4.GEN_OPTIONS)
                ctx = "\n\n".join(d.page_content for d in docs)
                k = kaggle.get((q["paper_id"], q["question_id"]), {})
                row = {"prompt": name, "model": MODEL, "paper_id": q["paper_id"], "question_id": q["question_id"],
                       "answer_type": q["answer_type"], "question": q["question"], "answer": res["text"],
                       "error": res["error"], "wall_s": res["wall_s"],
                       "kaggle_answer": k.get("answer"), "kaggle_refusal": k.get("refusal"),
                       **p4.score(q, res["text"], ctx)}
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                print(f"{name} {n}/{len(sample)} refusal={row['refusal']}", flush=True)
    p4.ollama_unload(MODEL)

    rows = [json.loads(l) for l in open(pq, encoding="utf-8")]
    summ = {"model": MODEL, "seed": SEED, "per_type": PER_TYPE, "n_questions": len(sample), "arms": {}}
    for name in PROMPTS:
        rs = [r for r in rows if r["prompt"] == name]
        by = defaultdict(list)
        for r in rs:
            by[r["answer_type"]].append(r)
        bools = [r for r in rs if r["boolean_correct"] is not None]
        summ["arms"][name] = {
            "n": len(rs),
            "refusal_rate": round(sum(r["refusal"] for r in rs) / len(rs), 3),
            "refusal_by_type": {t: round(sum(r["refusal"] for r in v) / len(v), 3) for t, v in by.items()},
            "token_f1_mean": round(sum(r["token_f1"] for r in rs) / len(rs), 4),
            "containment_mean": round(sum(r["containment"] for r in rs) / len(rs), 4),
            "boolean_accuracy": round(sum(r["boolean_correct"] for r in bools) / len(bools), 3) if bools else None,
        }
    prod = [r for r in rows if r["prompt"] == "production" and r["kaggle_refusal"] is not None]
    summ["production_vs_kaggle_refusal_agreement"] = round(
        sum(r["refusal"] == r["kaggle_refusal"] for r in prod) / len(prod), 3) if prod else None
    summ["kaggle_refusal_rate_same_50"] = round(sum(r["kaggle_refusal"] for r in prod) / len(prod), 3) if prod else None
    json.dump(summ, open(OUT / "summary.json", "w", encoding="utf-8"), indent=2)
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
