# ResearchQA Method B: Multi-Paper Citation Graph Retrieval Report

*Generated on: 2026-10-30 11:00:05*
- **Strategy:** `hybrid_rrf`
- **Dense Encoder:** `intfloat/e5-small-v2`
- **Total Multi-Paper Queries:** `4`
- **Total Corpus Chunks:** `33`

---

## 1. Executive Summary & Cross-Document Citation Scorecard

| Evaluation Metric | Top-5 | Top-10 | Top-20 (Candidate Ceiling) |
| :--- | :---: | :---: | :---: |
| **Paper Recall@k** (Fraction of target citations captured) | **62.5%** | **87.5%** | **100.0%** |
| **Full Coverage@k** (ALL target papers captured) | **25.0%** | **75.0%** | **100.0%** |
| **Citation Hit@k** (At least 1 target paper captured) | **100.0%** | **100.0%** | **100.0%** |

- **Mean nDCG@10:** `0.5109`
- **Mean MRR@10:** `0.4583`

---

## 2. Per-Query Breakdown & Citation Completeness

| Query ID | Target Citations | Recall@5 | Recall@10 | Recall@20 | Full Coverage@10 | nDCG@10 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `RQA_CS_001` | P_ATTN_VASWANI, P_FLASH_DAO | 50% | 100% | 100% | 🟢 Yes | 0.4963 |
| `RQA_CS_002` | P_ROPE_SU, P_ATTN_VASWANI | 50% | 50% | 100% | 🔴 No | 0.4725 |
| `RQA_BIO_001` | P_ALPHAFOLD_JUMPER, P_ESM_RIVES | 100% | 100% | 100% | 🟢 Yes | 0.5286 |
| `RQA_SYS_001` | P_PAXOS_LAMPORT, P_RAFT_ONGARO | 50% | 100% | 100% | 🟢 Yes | 0.5461 |

---

## 3. Methodological Insights for RAG Pipeline

1. **Multi-Paper Candidate Expansion:** In single-paper RAG, Top-4 chunks often suffice to capture an answer.
   However, in scholarly synthesis (ResearchQA Method B), queries require synthesizing claims across **2 to 3 distinct primary papers**.
   Expanding the candidate pool to Top-20 increases Paper Recall from 62.5% to 100.0%.
2. **Hybrid RRF Complementarity:** Pure dense semantic matching captures conceptual themes, whereas BM25 ensures exact author/method acronyms (e.g. *RoPE*, *FlashAttention*, *AlphaFold2*) are promoted into the context assembly window.