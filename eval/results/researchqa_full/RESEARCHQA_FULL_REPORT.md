# ResearchQA Full Dataset — Paper-Level Citation Retrieval Report

> **Generated:** `2026-10-30T07:34:24.820597+00:00 UTC`  
> **Dataset:** `realliyifei/ResearchQA` (real HuggingFace data)  
> **Task:** Given a research query, retrieve the cited paper(s) from the rubric  
> **Chunking Source:** `backend/apps/documents/services/chunkers.py`

> [!NOTE]
> ResearchQA contains rubric-based evaluation criteria, not verbatim evidence passages.
> Ground-truth = papers cited in rubric items (type=Citation). Corpus = stub entries
> (title + metadata) for each unique cited paper, chunked using production chunkers.
> This evaluates whether lexical/semantic matching on chunks is sufficient to retrieve
> the right paper given the query under various chunking strategies.

---

## 1. Overall Results Across Chunking and Retrieval Strategies

| Chunk Strategy | Retrieval Strategy | Chunks | Paper Recall@5 | Paper Recall@10 | Paper Recall@20 | Full Coverage@10 | Citation Hit@5 | nDCG@10 | MRR@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `fixed_size` | `bm25` | 1625 | 0.6721 | 0.7288 | 0.7727 | 0.6866 | 0.7265 | 0.6180 | 0.6154 |
| `fixed_size` | `dense` | 1625 | 0.6616 | 0.7194 | 0.7694 | 0.6740 | 0.7146 | 0.6114 | 0.6089 |
| `fixed_size` | `hybrid_rrf` | 1625 | 0.6744 | 0.7297 | 0.7706 | 0.6873 | 0.7272 | 0.6202 | 0.6181 |
| `fixed_size_overlap` | `bm25` | 1625 | 0.6721 | 0.7288 | 0.7727 | 0.6866 | 0.7265 | 0.6180 | 0.6154 |
| `fixed_size_overlap` | `dense` | 1625 | 0.6616 | 0.7194 | 0.7694 | 0.6740 | 0.7146 | 0.6114 | 0.6089 |
| `fixed_size_overlap` | `hybrid_rrf` | 1625 | 0.6744 | 0.7297 | 0.7706 | 0.6873 | 0.7272 | 0.6202 | 0.6181 |
| `hierarchical` | `bm25` | 3250 | 0.6680 | 0.7298 | 0.7783 | 0.6846 | 0.7199 | 0.6140 | 0.6093 |
| `hierarchical` | `dense` | 3250 | 0.6661 | 0.7260 | 0.7797 | 0.6826 | 0.7192 | 0.6104 | 0.6041 |
| `hierarchical` | `hybrid_rrf` | 3250 | 0.6719 | 0.7295 | 0.7792 | 0.6860 | 0.7239 | 0.6171 | 0.6132 |
| `section` | `bm25` | 3250 | 0.6680 | 0.7298 | 0.7783 | 0.6846 | 0.7199 | 0.6140 | 0.6093 |
| `section` | `dense` | 3250 | 0.6661 | 0.7260 | 0.7797 | 0.6826 | 0.7192 | 0.6104 | 0.6041 |
| `section` | `hybrid_rrf` | 3250 | 0.6719 | 0.7295 | 0.7792 | 0.6860 | 0.7239 | 0.6171 | 0.6132 |
| `section_token` | `bm25` | 3250 | 0.6680 | 0.7298 | 0.7783 | 0.6846 | 0.7199 | 0.6140 | 0.6093 |
| `section_token` | `dense` | 3250 | 0.6661 | 0.7260 | 0.7797 | 0.6826 | 0.7192 | 0.6104 | 0.6041 |
| `section_token` | `hybrid_rrf` | 3250 | 0.6719 | 0.7295 | 0.7792 | 0.6860 | 0.7239 | 0.6171 | 0.6132 |
| `section_overlap` | `bm25` | 3250 | 0.6680 | 0.7298 | 0.7783 | 0.6846 | 0.7199 | 0.6140 | 0.6093 |
| `section_overlap` | `dense` | 3250 | 0.6661 | 0.7260 | 0.7797 | 0.6826 | 0.7192 | 0.6104 | 0.6041 |
| `section_overlap` | `hybrid_rrf` | 3250 | 0.6719 | 0.7295 | 0.7792 | 0.6860 | 0.7239 | 0.6171 | 0.6132 |

---

## 2. Split Breakdown

### Chunk: `fixed_size` | Retrieval: `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6494 | 0.7082 | 0.6631 | 0.7082 | 0.5920 |
| test | 1126 | 0.6797 | 0.7356 | 0.6945 | 0.7327 | 0.6267 |

### Chunk: `fixed_size` | Retrieval: `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.6976 | 0.6499 | 0.6897 | 0.5858 |
| test | 1126 | 0.6708 | 0.7268 | 0.6821 | 0.7229 | 0.6199 |

### Chunk: `fixed_size` | Retrieval: `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6512 | 0.7109 | 0.6658 | 0.7056 | 0.5951 |
| test | 1126 | 0.6822 | 0.7359 | 0.6945 | 0.7345 | 0.6286 |

### Chunk: `fixed_size_overlap` | Retrieval: `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6494 | 0.7082 | 0.6631 | 0.7082 | 0.5920 |
| test | 1126 | 0.6797 | 0.7356 | 0.6945 | 0.7327 | 0.6267 |

### Chunk: `fixed_size_overlap` | Retrieval: `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.6976 | 0.6499 | 0.6897 | 0.5858 |
| test | 1126 | 0.6708 | 0.7268 | 0.6821 | 0.7229 | 0.6199 |

### Chunk: `fixed_size_overlap` | Retrieval: `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6512 | 0.7109 | 0.6658 | 0.7056 | 0.5951 |
| test | 1126 | 0.6822 | 0.7359 | 0.6945 | 0.7345 | 0.6286 |

### Chunk: `hierarchical` | Retrieval: `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6463 | 0.7069 | 0.6578 | 0.7056 | 0.5844 |
| test | 1126 | 0.6753 | 0.7374 | 0.6936 | 0.7247 | 0.6239 |

### Chunk: `hierarchical` | Retrieval: `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.7056 | 0.6578 | 0.6950 | 0.5798 |
| test | 1126 | 0.6769 | 0.7328 | 0.6909 | 0.7274 | 0.6206 |

### Chunk: `hierarchical` | Retrieval: `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6446 | 0.7082 | 0.6605 | 0.7029 | 0.5885 |
| test | 1126 | 0.6810 | 0.7367 | 0.6945 | 0.7309 | 0.6266 |

### Chunk: `section` | Retrieval: `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6463 | 0.7069 | 0.6578 | 0.7056 | 0.5844 |
| test | 1126 | 0.6753 | 0.7374 | 0.6936 | 0.7247 | 0.6239 |

### Chunk: `section` | Retrieval: `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.7056 | 0.6578 | 0.6950 | 0.5798 |
| test | 1126 | 0.6769 | 0.7328 | 0.6909 | 0.7274 | 0.6206 |

### Chunk: `section` | Retrieval: `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6446 | 0.7082 | 0.6605 | 0.7029 | 0.5885 |
| test | 1126 | 0.6810 | 0.7367 | 0.6945 | 0.7309 | 0.6266 |

### Chunk: `section_token` | Retrieval: `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6463 | 0.7069 | 0.6578 | 0.7056 | 0.5844 |
| test | 1126 | 0.6753 | 0.7374 | 0.6936 | 0.7247 | 0.6239 |

### Chunk: `section_token` | Retrieval: `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.7056 | 0.6578 | 0.6950 | 0.5798 |
| test | 1126 | 0.6769 | 0.7328 | 0.6909 | 0.7274 | 0.6206 |

### Chunk: `section_token` | Retrieval: `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6446 | 0.7082 | 0.6605 | 0.7029 | 0.5885 |
| test | 1126 | 0.6810 | 0.7367 | 0.6945 | 0.7309 | 0.6266 |

### Chunk: `section_overlap` | Retrieval: `bm25`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6463 | 0.7069 | 0.6578 | 0.7056 | 0.5844 |
| test | 1126 | 0.6753 | 0.7374 | 0.6936 | 0.7247 | 0.6239 |

### Chunk: `section_overlap` | Retrieval: `dense`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6340 | 0.7056 | 0.6578 | 0.6950 | 0.5798 |
| test | 1126 | 0.6769 | 0.7328 | 0.6909 | 0.7274 | 0.6206 |

### Chunk: `section_overlap` | Retrieval: `hybrid_rrf`

| Split | n | Recall@5 | Recall@10 | Full Coverage@10 | Citation Hit@5 | nDCG@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| test_mini | 377 | 0.6446 | 0.7082 | 0.6605 | 0.7029 | 0.5885 |
| test | 1126 | 0.6810 | 0.7367 | 0.6945 | 0.7309 | 0.6266 |

---

## 3. Methodology Notes

- **Chunking Strategies from `chunkers.py`:**
  - `fixed_size`: Fixed token window across the full document text without overlap.
  - `fixed_size_overlap`: Sliding token window with overlap (400 max tokens, 80 overlap).
  - `hierarchical`: Multi-level chunking with parent sections and child windows (200 tokens, 40 overlap).
  - `section`: One chunk per document section.
  - `section_token`: Section-aware chunking with token budget constraint.
  - `section_overlap`: Section-aware sliding window with overlap (production default).
- **Ground truth:** Rubric items with `type=Citation` and non-null `citation_metadata`.
  Queries with zero citation rubric items are excluded (no retrievable ground truth).
- **BM25:** Okapi BM25 (k₁=1.5, b=0.75) with regex tokenisation.
- **Dense:** TF-IDF cosine similarity (no GPU required).
- **Hybrid RRF:** Reciprocal Rank Fusion of BM25 + TF-IDF (k=60).
