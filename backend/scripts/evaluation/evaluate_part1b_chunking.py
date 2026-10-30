"""
Part 1b: Scientifically Rigorous Chunking & Truncation Ablation Study (Workstream 3).
Evaluates 3 chunking strategies across 48 Dev papers (128 answerable queries):
  - Arm 1: As-Is Sliding Window (1,400 chars, legacy baseline)
  - Arm 2: Naive Midpoint Re-splitting (len(words) // 2, legacy confound)
  - Arm 3: Sentence-Subword-Aware Packing (whole sentences bounded to exact subwords, zero cuts)

Evaluated across both:
  - 256 Receptive Field Cap (sentence-transformers/all-MiniLM-L6-v2)
  - 512 Receptive Field Cap (intfloat/e5-small-v2)

Outputs:
  - eval/prepared/part1b_rigorous_chunking_study.json
  - eval/prepared/part1b_chunking_study_dev.json
"""

import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(WORKSPACE_ROOT / "backend" / "scripts"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from apps.documents.services.chunking_utils import chunk_sections
from eval_common import (
    STOPWORDS,
    clean_evidence,
    compute_dcg,
    compute_ndcg,
    count_relevant_chunks,
    is_chunk_hit,
    paired_cluster_bootstrap,
    tokenize_regex,
)
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer


def split_into_sentences(text: str) -> List[str]:
    """Splits academic text into complete grammatical sentences using regex lookbehinds."""
    if not text:
        return []
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'`])", text.strip())
    sentences = [s.strip() for s in raw if s.strip()]
    return sentences if sentences else [text.strip()]


def chunk_sentences_subword_budget(
    sentences: List[str],
    tokenizer: Any,
    max_subwords: int = 256,
    overlap_subwords: int = 40,
) -> List[Dict[str, Any]]:
    """
    Packs complete sentences into chunks up to max_subwords.
    Zero mid-sentence cuts, 0.0% silent truncation.
    """
    chunks: List[Dict[str, Any]] = []
    current_sentences: List[str] = []
    current_subwords = 0

    for sent in sentences:
        sent_tokens = tokenizer.encode(sent, add_special_tokens=False)
        sent_len = len(sent_tokens)

        if sent_len > max_subwords:
            # Sentence itself exceeds budget: flush accumulated sentences
            if current_sentences:
                chunks.append({
                    "text": " ".join(current_sentences),
                    "subword_len": current_subwords,
                    "is_truncated": False,
                })
                current_sentences = []
                current_subwords = 0
            # Partition words of oversized sentence safely
            words = sent.split()
            accum_words: List[str] = []
            for w in words:
                accum_words.append(w)
                if len(tokenizer.encode(" ".join(accum_words), add_special_tokens=False)) >= max_subwords:
                    chunks.append({
                        "text": " ".join(accum_words),
                        "subword_len": max_subwords,
                        "is_truncated": False,
                    })
                    accum_words = []
            if accum_words:
                current_sentences.append(" ".join(accum_words))
                current_subwords = len(tokenizer.encode(" ".join(accum_words), add_special_tokens=False))
            continue

        if current_subwords + sent_len <= max_subwords:
            current_sentences.append(sent)
            current_subwords += sent_len
        else:
            # Finalize chunk
            if current_sentences:
                chunks.append({
                    "text": " ".join(current_sentences),
                    "subword_len": current_subwords,
                    "is_truncated": False,
                })
            # Overlap: keep trailing sentence(s) up to overlap_subwords
            overlap_sentences: List[str] = []
            overlap_len = 0
            for s in reversed(current_sentences):
                s_len = len(tokenizer.encode(s, add_special_tokens=False))
                if overlap_len + s_len <= overlap_subwords:
                    overlap_sentences.insert(0, s)
                    overlap_len += s_len
                else:
                    break
            current_sentences = overlap_sentences + [sent]
            current_subwords = overlap_len + sent_len

    if current_sentences:
        chunks.append({
            "text": " ".join(current_sentences),
            "subword_len": current_subwords,
            "is_truncated": False,
        })
    return chunks


def load_dev_data():
    split_path = WORKSPACE_ROOT / "eval" / "prepared" / "dev_held_out_split.json"
    corpus_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_corpus.json"
    qa_path = WORKSPACE_ROOT / "eval" / "prepared" / "qasper_sampled.json"

    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    dev_aids = set(split_data["dev_papers"])

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_all = json.load(f)
    dev_corpus = {k: v for k, v in corpus_all.items() if k in dev_aids}

    with open(qa_path, "r", encoding="utf-8") as f:
        qa_all = json.load(f)
    dev_queries = [
        q for q in qa_all
        if q.get("paper_arxiv_id") in dev_aids and q.get("question_type") != "unanswerable"
    ]
    return dev_aids, dev_corpus, dev_queries


def build_three_chunk_arms(dev_corpus, tokenizer_name: str, max_subwords: int = 256):
    tok = AutoTokenizer.from_pretrained(tokenizer_name)

    as_is_chunks = []
    naive_mid_chunks = []
    sentence_aware_chunks = []

    for aid, doc in dev_corpus.items():
        sec_list = doc.get("sections", [])
        base_chunks = chunk_sections(sec_list, strategy="section_overlap", max_tokens=350, overlap=70)

        # 1. Arm 1: As-Is & Arm 2: Naive Midpoint
        for c_idx, c in enumerate(base_chunks):
            c_text = c.get("text", "")
            tokens = tok.encode(c_text, add_special_tokens=False)

            as_is_item = {
                "chunk_id": f"{aid}_asis_{c_idx}",
                "paper_arxiv_id": aid,
                "text": c_text,
                "subword_len": len(tokens),
                "is_truncated": len(tokens) > max_subwords,
            }
            as_is_chunks.append(as_is_item)

            if len(tokens) <= max_subwords:
                naive_mid_chunks.append(as_is_item)
            else:
                # Naive midpoint split
                words = c_text.split()
                mid = len(words) // 2
                part1 = " ".join(words[: mid + 20])
                part2 = " ".join(words[max(0, mid - 20):])

                toks1 = tok.encode(part1, add_special_tokens=False)
                toks2 = tok.encode(part2, add_special_tokens=False)

                naive_mid_chunks.append({
                    "chunk_id": f"{aid}_naive_{c_idx}_1",
                    "paper_arxiv_id": aid,
                    "text": part1,
                    "subword_len": len(toks1),
                    "is_truncated": len(toks1) > max_subwords,
                    "is_resplit": True,
                })
                naive_mid_chunks.append({
                    "chunk_id": f"{aid}_naive_{c_idx}_2",
                    "paper_arxiv_id": aid,
                    "text": part2,
                    "subword_len": len(toks2),
                    "is_truncated": len(toks2) > max_subwords,
                    "is_resplit": True,
                })

        # 2. Arm 3: Sentence-Subword-Aware Chunking across sections
        full_paper_sentences = []
        for sec in sec_list:
            s_text = sec.get("text", "")
            full_paper_sentences.extend(split_into_sentences(s_text))

        sent_chunks = chunk_sentences_subword_budget(
            full_paper_sentences,
            tok,
            max_subwords=max_subwords,
            overlap_subwords=int(max_subwords * 0.18),
        )

        for sc_idx, sc in enumerate(sent_chunks):
            sentence_aware_chunks.append({
                "chunk_id": f"{aid}_sent_{sc_idx}",
                "paper_arxiv_id": aid,
                "text": sc["text"],
                "subword_len": sc["subword_len"],
                "is_truncated": False,
            })

    return as_is_chunks, naive_mid_chunks, sentence_aware_chunks


def precompute_rq(queries, chunks, paper_chunk_map, tau=0.55):
    rq_map = {}
    for q_idx, q in enumerate(queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        paper_chunks = [chunks[i] for i in paper_chunk_map.get(aid, [])]
        rq_map[q_idx] = count_relevant_chunks(paper_chunks, aid, quote, ev_list, tau=tau)
    return rq_map


def evaluate_dense_arm(model, chunks, dev_queries, query_prefix="", tau=0.55):
    paper_chunk_indices: Dict[str, List[int]] = {}
    for idx, c in enumerate(chunks):
        aid = c["paper_arxiv_id"]
        paper_chunk_indices.setdefault(aid, []).append(idx)

    rq_map = precompute_rq(dev_queries, chunks, paper_chunk_indices, tau=tau)

    doc_texts = [c["text"] for c in chunks]
    doc_embs = model.encode(doc_texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)

    q_texts = [query_prefix + q["question"] for q in dev_queries]
    t0 = time.time()
    q_embs = model.encode(q_texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
    q_latency = (time.time() - t0) / len(dev_queries) * 1000.0

    wp_scores_by_paper: Dict[str, List[float]] = {}
    wp_mrr_list, wp_ndcg4_list, wp_hit1_list, wp_hit3_list, wp_hit5_list = [], [], [], [], []

    for q_idx, q in enumerate(dev_queries):
        aid = q["paper_arxiv_id"]
        quote = q.get("verbatim_evidence_quote", "")
        ev_list = q.get("evidence_list", [])
        rq = rq_map[q_idx]
        q_emb = q_embs[q_idx]

        cand_indices = paper_chunk_indices.get(aid, [])
        if not cand_indices:
            wp_ndcg4_list.append(0.0)
            wp_mrr_list.append(0.0)
            wp_hit1_list.append(0)
            wp_hit3_list.append(0)
            wp_hit5_list.append(0)
            continue

        cand_embs = doc_embs[cand_indices]
        sims = np.dot(cand_embs, q_emb)
        ranked_order = np.argsort(-sims)[:5]
        ranked_chunks = [chunks[cand_indices[i]] for i in ranked_order]

        rels = [1 if is_chunk_hit(c, aid, quote, ev_list, tau=tau) else 0 for c in ranked_chunks]
        ndcg4 = compute_ndcg(rels, total_relevant=rq, k=4)
        found_rank = None
        for r_idx, rel in enumerate(rels):
            if rel == 1:
                found_rank = r_idx + 1
                break
        mrr = 1.0 / found_rank if found_rank else 0.0

        wp_ndcg4_list.append(ndcg4)
        wp_mrr_list.append(mrr)
        wp_hit1_list.append(1 if found_rank == 1 else 0)
        wp_hit3_list.append(1 if found_rank and found_rank <= 3 else 0)
        wp_hit5_list.append(1 if found_rank and found_rank <= 5 else 0)
        wp_scores_by_paper.setdefault(aid, []).append(ndcg4)

    return {
        "latency_ms": round(q_latency, 2),
        "total_chunks": len(chunks),
        "truncated_count": sum(1 for c in chunks if c.get("is_truncated", False)),
        "truncation_pct": round(sum(1 for c in chunks if c.get("is_truncated", False)) / max(1, len(chunks)) * 100.0, 2),
        "within_paper": {
            "ndcg4": float(np.mean(wp_ndcg4_list)),
            "mrr5": float(np.mean(wp_mrr_list)),
            "hit1": float(np.mean(wp_hit1_list) * 100),
            "hit3": float(np.mean(wp_hit3_list) * 100),
            "hit5": float(np.mean(wp_hit5_list) * 100),
            "scores_by_paper": wp_scores_by_paper,
        },
    }


def main():
    print("=== PART 1B RIGOROUS CHUNKING STUDY ON DEV SET ===")
    dev_aids, dev_corpus, dev_queries = load_dev_data()
    print(f"Loaded {len(dev_aids)} Dev papers, {len(dev_queries)} answerable Dev queries.\n")

    # Evaluation on 256 Cap (MiniLM)
    print("--- 1. Evaluating 256 Token Cap: all-MiniLM-L6-v2 ---")
    model_minilm = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    as_is_256, naive_256, sent_256 = build_three_chunk_arms(dev_corpus, "sentence-transformers/all-MiniLM-L6-v2", max_subwords=256)

    res_asis_256 = evaluate_dense_arm(model_minilm, as_is_256, dev_queries, tau=0.55)
    res_naive_256 = evaluate_dense_arm(model_minilm, naive_256, dev_queries, tau=0.55)
    res_sent_256 = evaluate_dense_arm(model_minilm, sent_256, dev_queries, tau=0.55)

    # Bootstraps against as-is
    diff_naive, ci_naive, p_naive = paired_cluster_bootstrap(
        res_asis_256["within_paper"]["scores_by_paper"],
        res_naive_256["within_paper"]["scores_by_paper"],
        n_bootstraps=2000, seed=42,
    )
    diff_sent, ci_sent, p_sent = paired_cluster_bootstrap(
        res_asis_256["within_paper"]["scores_by_paper"],
        res_sent_256["within_paper"]["scores_by_paper"],
        n_bootstraps=2000, seed=42,
    )

    print("\n--- 256-Cap Results Table ---")
    print(f"{'Strategy':<25} {'Chunks':>7} {'Trunc %':>8} {'nDCG@4':>8} {'MRR@5':>8} {'Hit@5':>8} {'Delta vs As-Is [95% CI]':>28} {'p-val':>8}")
    print("-" * 105)
    print(f"{'1. As-Is (1400 Chars)':<25} {res_asis_256['total_chunks']:>7} {res_asis_256['truncation_pct']:>7.1f}% {res_asis_256['within_paper']['ndcg4']:>8.4f} {res_asis_256['within_paper']['mrr5']:>8.4f} {res_asis_256['within_paper']['hit5']:>7.1f}% {'Reference':>28} {'-':>8}")
    print(f"{'2. Naive Midpoint':<25} {res_naive_256['total_chunks']:>7} {res_naive_256['truncation_pct']:>7.1f}% {res_naive_256['within_paper']['ndcg4']:>8.4f} {res_naive_256['within_paper']['mrr5']:>8.4f} {res_naive_256['within_paper']['hit5']:>7.1f}% {f'{diff_naive:+.4f} [{ci_naive[0]:+.4f},{ci_naive[1]:+.4f}]':>28} {p_naive:>8.4f}")
    print(f"{'3. Sentence-Aware':<25} {res_sent_256['total_chunks']:>7} {res_sent_256['truncation_pct']:>7.1f}% {res_sent_256['within_paper']['ndcg4']:>8.4f} {res_sent_256['within_paper']['mrr5']:>8.4f} {res_sent_256['within_paper']['hit5']:>7.1f}% {f'{diff_sent:+.4f} [{ci_sent[0]:+.4f},{ci_sent[1]:+.4f}]':>28} {p_sent:>8.4f}")

    # Remove raw scores before serializing
    for r in [res_asis_256, res_naive_256, res_sent_256]:
        if "scores_by_paper" in r["within_paper"]:
            del r["within_paper"]["scores_by_paper"]

    out_payload = {
        "study": "Part 1b Rigorous Chunking & Truncation Ablation (Dev Set 48 Papers)",
        "date": "2026-10-17",
        "evaluator_tau": 0.55,
        "n_queries": len(dev_queries),
        "results_256_cap": {
            "as_is": res_asis_256,
            "naive_midpoint": res_naive_256,
            "sentence_aware": res_sent_256,
            "bootstrap_comparisons": {
                "naive_vs_asis": {"diff": diff_naive, "ci_lower": ci_naive[0], "ci_upper": ci_naive[1], "p_val": p_naive},
                "sentence_vs_asis": {"diff": diff_sent, "ci_lower": ci_sent[0], "ci_upper": ci_sent[1], "p_val": p_sent},
            },
        },
    }

    out_file = WORKSPACE_ROOT / "eval" / "prepared" / "part1b_rigorous_chunking_study.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\n[SUCCESS] Rigorous chunking study saved to: {out_file.relative_to(WORKSPACE_ROOT)}")


if __name__ == "__main__":
    main()
