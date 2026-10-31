#!/usr/bin/env python3
"""
Draw the 300 questions on which all 16 combination configurations generate answers.

Rule (seed 42): 100 questions from each QASPER split (train, dev, test) of the combination set; at most one
question per paper; within each split, the number of questions per answer type (extractive / abstractive /
boolean, the answer type of the first gold reference) is proportional to that split's distribution
(largest-remainder rounding). Retrieval metrics are still computed on the whole combination set.
The sample is not representative of all QASPER questions; it is a fixed, reproducible subset.

Output: eval/phases/phase_0_baseline/artifacts/generation_sample.json
Usage:  backend/venv/Scripts/python.exe eval/phases/phase_0_baseline/scripts/sample_generation_questions.py
"""

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "eval" / "phases" / "phase_9_generation" / "scripts"))
from generate_sample_manifest_250 import is_atomic_eligible  # noqa: E402

DATASET = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "combination_set.json"
OUT = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "generation_sample.json"
PER_SPLIT, SEED = 100, 42


def quotas(counts, total):
    """Largest-remainder allocation of `total` proportional to `counts`."""
    n = sum(counts.values())
    raw = {k: total * v / n for k, v in counts.items()}
    q = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: (raw[k] - q[k], k), reverse=True)[: total - sum(q.values())]:
        q[k] += 1
    return q


def main():
    ds = json.load(open(DATASET, encoding="utf-8"))
    data = {}
    for s in ("train", "dev", "test"):
        data.update(json.load(open(ROOT / "eval" / "data" / "qasper_official" / f"qasper-{s}-v0.3.json", encoding="utf-8")))
    qtype = {}
    for pid, p in ds["papers"].items():
        qas = {qa["question_id"]: qa for qa in data[pid]["qas"]}
        for qid in p["questions"]:
            qtype[qid] = is_atomic_eligible(qas[qid])[1][0]["type"]

    rng = random.Random(SEED)
    chosen, report = [], {}
    for split in ("train", "dev", "test"):
        qids = sorted(q for q, v in ds["questions"].items() if v["split"] == split)
        counts = Counter(qtype[q] for q in qids)
        quota = quotas(counts, PER_SPLIT)
        pool = defaultdict(list)
        for q in qids:
            pool[qtype[q]].append(q)
        for t in pool:
            rng.shuffle(pool[t])
        used_papers, picked = set(), Counter()
        # fill the rarest type first, so its one-question-per-paper constraint is met before common types use up papers
        for t in sorted(quota, key=lambda t: counts[t]):
            for q in pool[t]:
                if picked[t] >= quota[t]:
                    break
                pid = ds["questions"][q]["paper_id"]
                if pid in used_papers:
                    continue
                used_papers.add(pid)
                picked[t] += 1
                chosen.append({"question_id": q, "paper_id": pid, "split": split, "answer_type": t})
        report[split] = {"population_by_type": dict(counts), "quota": quota, "selected": dict(picked),
                         "papers": len(used_papers)}
    out = {"rule": "100 questions per split (train, dev, test) of the combination set; at most one per paper; "
                   "answer types proportional within each split (largest remainder); seed 42",
           "seed": SEED, "source": str(DATASET.relative_to(ROOT)).replace("\\", "/"), "n": len(chosen),
           "by_split": report, "questions": chosen,
           "note": "Fixed reproducible subset; not representative of all QASPER questions."}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({"n": len(chosen), "by_split": report}, indent=1))


if __name__ == "__main__":
    main()
