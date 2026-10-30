# ResearchQA Full Dataset — Paper-Level Citation Retrieval Report

> **Generated:** `2026-10-30T04:23:16.843235 UTC`  
> **Dataset:** `realliyifei/ResearchQA` (real HuggingFace data)  
> **Task:** Given a research query, retrieve the cited paper(s) from the rubric

> [!NOTE]
> ResearchQA contains rubric-based evaluation criteria, not verbatim evidence passages.
> Ground-truth = papers cited in rubric items (type=Citation). Corpus = stub entries
> (title + metadata) for each unique cited paper. This evaluates whether lexical/
> semantic matching on paper titles is sufficient to retrieve the right paper given
> the query — a necessary but not sufficient condition for full RAG retrieval.

---

## 1. Overall Results

| Strategy | Paper Recall@5 | Paper Recall@10 | Paper Recall@20 | Full Coverage@10 | Citation Hit@5 | nDCG@10 | MRR@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `bm25` | 0.6680 | 0.7298 | 0.7783 | 0.6846 | 0.7199 | 0.6140 | 0.6093 |
| `dense` | 0.6661 | 0.7260 | 0.7797 | 0.6826 | 0.7192 | 0.6104 | 0.6041 |
| `hybrid_rrf` | 0.6719 | 0.7295 | 0.7792 | 0.6860 | 0.7239 | 0.6171 | 0.6132 |

---

## 2. Split Breakdown

### `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6463 | 0.7069 | 0.6578 | 0.7056 | 0.5844 |
| test | 1126 | 0.6753 | 0.7374 | 0.6936 | 0.7247 | 0.6239 |

### `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.7056 | 0.6578 | 0.6950 | 0.5798 |
| test | 1126 | 0.6769 | 0.7328 | 0.6909 | 0.7274 | 0.6206 |

### `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6446 | 0.7082 | 0.6605 | 0.7029 | 0.5885 |
| test | 1126 | 0.6810 | 0.7367 | 0.6945 | 0.7309 | 0.6266 |

---

## 3. Methodology Notes

- **Corpus limitation:** Only paper title + metadata available (no full text).
  Retrieval is title-matching, not passage retrieval. Results represent an upper-bound
  estimate of what title-level lexical retrieval can achieve.
- **Ground truth:** Rubric items with `type=Citation` and non-null `citation_metadata`.
  Queries with zero citation rubric items are excluded (no retrievable ground truth).
- **BM25:** Okapi BM25 (k₁=1.5, b=0.75) with regex tokenisation.
- **Dense:** TF-IDF cosine similarity (no GPU required).
- **Hybrid RRF:** Reciprocal Rank Fusion of BM25 + TF-IDF (k=60).
