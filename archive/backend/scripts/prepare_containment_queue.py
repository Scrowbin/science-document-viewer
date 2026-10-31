import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

from apps.documents.services.chunking_utils import chunk_sections
from scripts.evaluate_retrieval import tokenize

benchmark_path = os.path.join(ROOT_DIR, "eval", "prepared", "qasper_sampled.json")
corpus_path = os.path.join(ROOT_DIR, "eval", "prepared", "qasper_corpus.json")

with open(benchmark_path, "r", encoding="utf-8") as f:
    queries = json.load(f)
with open(corpus_path, "r", encoding="utf-8") as f:
    corpus_dict = json.load(f)

# Balanced split
papers = defaultdict(list)
for q in queries:
    papers[q["paper_arxiv_id"]].append(q)

unans_papers = sorted([
    aid
    for aid, qlist in papers.items()
    if any(q.get("question_type") == "unanswerable" for q in qlist)
])
ans_papers = sorted([aid for aid, qlist in papers.items() if aid not in unans_papers])

rng = random.Random(42)
rng.shuffle(unans_papers)
rng.shuffle(ans_papers)

dev_papers = set(unans_papers[:4] + ans_papers[:44])
held_out_papers = set(unans_papers[4:] + ans_papers[44:])

dev_queries = [
    q
    for q in queries
    if q["paper_arxiv_id"] in dev_papers and q.get("question_type") != "unanswerable"
]

dev_chunks = []
for aid in dev_papers:
    p_data = corpus_dict.get(aid, {})
    secs = p_data.get("sections", [])
    c_list = chunk_sections(secs, strategy="section_overlap", max_tokens=350, overlap=70)
    for c in c_list:
        c["paper_arxiv_id"] = aid
        dev_chunks.append(c)

borderline = []
high_cov = []
low_cov = []

for q in dev_queries:
    aid = q["paper_arxiv_id"]
    ev_ref = q.get("verbatim_evidence_quote") or " ".join(q.get("evidence_list") or [])
    ev_toks = set(tokenize(ev_ref))
    if not ev_toks:
        continue
    paper_chunks = [c for c in dev_chunks if c["paper_arxiv_id"] == aid]
    for c in paper_chunks:
        c_toks = set(tokenize(c.get("text", "")))
        if not c_toks:
            continue
        inter = len(ev_toks & c_toks)
        cov_ev = inter / len(ev_toks)
        cov_chunk = inter / len(c_toks) if len(c_toks) >= 20 else 0.0
        score = max(cov_ev, cov_chunk)

        rec = {
            "qid": q.get("id"),
            "question": q.get("question"),
            "aid": aid,
            "ev_ref": ev_ref,
            "section": c.get("section", ""),
            "chunk_text": c.get("text", ""),
            "score": round(score, 3),
            "cov_ev": round(cov_ev, 3),
            "cov_chunk": round(cov_chunk, 3),
            "inter": inter,
            "len_ev": len(ev_toks),
            "len_c": len(c_toks),
        }
        if 0.35 <= score <= 0.65:
            borderline.append(rec)
        elif score >= 0.70:
            high_cov.append(rec)
        elif 0.08 <= score <= 0.30:
            low_cov.append(rec)

rng_sample = random.Random(123)
sample_border = rng_sample.sample(borderline, min(30, len(borderline)))
sample_high = rng_sample.sample(high_cov, min(25, len(high_cov)))
sample_low = rng_sample.sample(low_cov, min(25, len(low_cov)))

final_sample = sample_border + sample_high + sample_low
rng_sample.shuffle(final_sample)

print(
    f"Sampled {len(final_sample)} pairs: {len(sample_border)} borderline, {len(sample_high)} high, {len(sample_low)} low."
)

out_path = os.path.join(ROOT_DIR, "eval", "prepared", "CONTAINMENT_LABEL_QUEUE.md")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("# Evidence-to-Chunk Containment Hand-Labeling Queue (Dev Papers)\n\n")
    f.write("**Instructions for Human Evaluator:**\n")
    f.write(
        "For each pair below, read the Question, Gold Evidence passage, and Candidate Chunk text.\n"
    )
    f.write(
        "Judge whether the candidate chunk contains the evidence required to answer the question or substantially covers the gold passage.\n"
    )
    f.write(
        "- Write `1` in `User Label: [ ]` if **Relevant** (contains the evidence / answers the question).\n"
    )
    f.write(
        "- Write `0` in `User Label: [ ]` if **Not Relevant** (incidental term overlap, wrong section, or insufficient context).\n\n"
    )
    f.write("---\n\n")

    for idx, item in enumerate(final_sample, 1):
        f.write(
            f"### Pair {idx:02d} / {len(final_sample):02d} [{item['qid']}] (Paper: `{item['aid']}`)\n\n"
        )
        f.write(f"**Question:** {item['question']}\n\n")
        f.write(f"**Gold Evidence:**\n> \"{item['ev_ref'][:400]}\"\n\n")
        f.write(
            f"**Candidate Chunk (Section: *{item['section']}*):**\n> \"{item['chunk_text'][:450]}...\"\n\n"
        )
        f.write(
            f"*Matcher Metrics:* Coverage(Evidence in Chunk) = `{item['cov_ev']}`, Coverage(Chunk in Evidence) = `{item['cov_chunk']}` -> **Max Score = `{item['score']}`**\n\n"
        )
        f.write("**User Label (1 = Relevant, 0 = Not Relevant):** `[ ]`\n\n")
        f.write("---\n\n")

json_out = os.path.join(ROOT_DIR, "eval", "prepared", "containment_label_queue.json")
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(final_sample, f, indent=2)

# Also save dev/held-out split definition so it is 100% frozen and reproducible
split_out = os.path.join(ROOT_DIR, "eval", "prepared", "dev_held_out_split.json")
with open(split_out, "w", encoding="utf-8") as f:
    json.dump(
        {
            "seed": 42,
            "dev_papers": sorted(list(dev_papers)),
            "held_out_papers": sorted(list(held_out_papers)),
            "dev_query_ids": [q["id"] for q in dev_queries],
            "held_out_query_ids": [
                q["id"] for q in queries if q["paper_arxiv_id"] in held_out_papers
            ],
            "unanswerable_dev": [
                q["id"]
                for q in queries
                if q["paper_arxiv_id"] in dev_papers
                and q.get("question_type") == "unanswerable"
            ],
            "unanswerable_held_out": [
                q["id"]
                for q in queries
                if q["paper_arxiv_id"] in held_out_papers
                and q.get("question_type") == "unanswerable"
            ],
        },
        f,
        indent=2,
    )

print(f"Wrote markdown queue to {out_path}")
print(f"Wrote JSON queue to {json_out}")
print(f"Wrote split definition to {split_out}")
