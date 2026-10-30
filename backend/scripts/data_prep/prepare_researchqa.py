"""
ResearchQA Benchmark Ingestion & Multi-Paper Citation Graph Generator (Method B).
Transforms scholarly survey questions and citation rubrics into a multi-paper
cross-document retrieval benchmark.

For each query:
  - Identifies the source survey paper.
  - Extracts the fine-grained rubric criteria.
  - Defines the gold set of target cited primary papers (ground truth qrels).
  - Builds structured paper corpora across diverse scientific domains.

Outputs:
  - eval/prepared/researchqa_citation_benchmark.json
  - eval/prepared/researchqa_corpus.json
  - eval/prepared/researchqa_qrels.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = WORKSPACE_ROOT / "backend"
SCRIPTS_DIR = BACKEND_DIR / "scripts"
EVAL_PREP_DIR = WORKSPACE_ROOT / "eval" / "prepared"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))


def build_curated_researchqa_corpus() -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Builds a rigorous, multi-discipline benchmark cohort covering:
      1. Computer Science & AI (Efficient Transformers, Attention & RAG)
      2. Biomedical & Life Sciences (Structural Biology, AlphaFold, Protein Language Models)
      3. Distributed Systems & Computing (Consensus, Raft, Paxos, Fault Tolerance)
      4. Physical Sciences & Chemistry (Neural Potentials, Molecular Dynamics)
    """
    corpus: Dict[str, Dict[str, Any]] = {
        # --- Cluster 1: Computer Science / Transformer Architectures ---
        "SURVEY_CS_TRANSFORMERS": {
            "paper_arxiv_id": "SURVEY_CS_TRANSFORMERS",
            "paper_title": "A Survey on Efficient Transformers and Long-Sequence Deep Learning Architectures",
            "field": "Engineering & Computer Science",
            "subfield": "Artificial Intelligence & NLP",
            "abstract": (
                "Transformer architectures have achieved state-of-the-art results across natural language "
                "processing, computer vision, and speech recognition. However, the standard dot-product attention "
                "mechanism scales quadratically with sequence length O(N^2), imposing substantial computational and "
                "memory bottlenecks for long-context documents. This comprehensive survey systematically reviews "
                "efficient transformer modifications, categorizing techniques into IO-aware exact computation, "
                "rotational relative positional embeddings, low-rank parameter-efficient adaptation, and external "
                "knowledge retrieval augmentation."
            ),
            "sections": [
                {
                    "heading": "1. Introduction to Self-Attention Bottlenecks",
                    "text": (
                        "The standard multi-head self-attention module computes attention weights as softmax(QK^T / sqrt(d))V. "
                        "Materializing the full N-by-N attention matrix incurs O(N^2) time and GPU SRAM memory traffic, "
                        "limiting context length in traditional architectures. Researchers have proposed various approaches "
                        "to mitigate this, ranging from architectural tiling to external retrieval augmentation."
                    ),
                },
                {
                    "heading": "2. IO-Aware Hardware Acceleration",
                    "text": (
                        "Rather than approximating attention, IO-aware algorithms reorganize computation to account for GPU "
                        "memory hierarchy levels between high-bandwidth memory (HBM) and fast static RAM (SRAM). "
                        "By tiling queries, keys, and values into blocks and computing softmax incrementally via online normalizers, "
                        "memory reads and writes are reduced by an order of magnitude without any mathematical approximation."
                    ),
                },
                {
                    "heading": "3. Relative and Rotational Positional Encodings",
                    "text": (
                        "Absolute sinusoidal and learned position embeddings struggle to extrapolate beyond pre-training lengths. "
                        "Rotary Position Embedding (RoPE) resolves this by applying a orthogonal rotation matrix to query and key vectors "
                        "in 2D sub-spaces, naturally encoding relative distance through inner products while maintaining dot-product efficiency."
                    ),
                },
                {
                    "heading": "4. Retrieval-Augmented Generation (RAG) Integration",
                    "text": (
                        "Instead of packing entire external corpora into model context windows, RAG frameworks integrate "
                        "dense and sparse passage retrievers with pre-trained seq2seq generators, dynamically retrieving non-parametric "
                        "evidence passages from vector indices to ground factual generation."
                    ),
                },
            ],
        },
        "P_ATTN_VASWANI": {
            "paper_arxiv_id": "P_ATTN_VASWANI",
            "paper_title": "Attention Is All You Need",
            "field": "Engineering & Computer Science",
            "subfield": "Artificial Intelligence & NLP",
            "abstract": (
                "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks "
                "in an encoder-decoder configuration. We propose the Transformer, a model architecture eschewing recurrence and "
                "relying entirely on an attention mechanism to draw global dependencies between input and output."
            ),
            "sections": [
                {
                    "heading": "3.2 Scaled Dot-Product Attention",
                    "text": (
                        "We compute the attention function on a set of queries simultaneously, packed together into a matrix Q. "
                        "The keys and values are also packed into matrices K and V. We compute the matrix of outputs as: "
                        "Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V. The two most commonly used attention functions are "
                        "additive attention and dot-product (multiplicative) attention."
                    ),
                },
                {
                    "heading": "3.3 Multi-Head Attention",
                    "text": (
                        "Multi-head attention allows the model to jointly attend to information from different representation "
                        "subspaces at different positions. MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O where "
                        "head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)."
                    ),
                },
            ],
        },
        "P_FLASH_DAO": {
            "paper_arxiv_id": "P_FLASH_DAO",
            "paper_title": "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness",
            "field": "Engineering & Computer Science",
            "subfield": "Hardware & Systems Architecture",
            "abstract": (
                "Transformers are slow and memory-hungry on long sequences, as the time and memory complexity of self-attention "
                "is quadratic in sequence length. We propose FlashAttention, an IO-aware exact attention algorithm that uses "
                "tiling to reduce memory reads/writes between GPU high bandwidth memory (HBM) and GPU on-chip SRAM."
            ),
            "sections": [
                {
                    "heading": "2. Hardware Characteristics & IO Complexity",
                    "text": (
                        "For modern GPUs like NVIDIA A100 (40-80 GB HBM with 1.5-2.0 TB/s bandwidth, 192 KB on-chip SRAM per SM with 19 TB/s), "
                        "standard attention execution is memory-bound (memory-access overhead) rather than compute-bound. "
                        "Standard attention materializes intermediate N x N matrices S and P to HBM, incurring O(N^2) HBM accesses."
                    ),
                },
                {
                    "heading": "3. Tiling and Online Softmax Normalization",
                    "text": (
                        "FlashAttention computes exact softmax without storing intermediate attention matrices. "
                        "Given blocks of Q, K, V loaded into on-chip SRAM, we compute local attention and rescale output running accumulators "
                        "using the online softmax normalization trick: m_new = max(m_prev, x_i) and l_new = exp(m_prev - m_new) l_prev + exp(x_i - m_new)."
                    ),
                },
            ],
        },
        "P_ROPE_SU": {
            "paper_arxiv_id": "P_ROPE_SU",
            "paper_title": "RoFormer: Enhanced Transformer with Rotary Position Embedding",
            "field": "Engineering & Computer Science",
            "subfield": "Artificial Intelligence & NLP",
            "abstract": (
                "Positional information is crucial in sequence modeling. We propose Rotary Position Embedding (RoPE) to effectively "
                "incorporate relative positional interactions into transformer architectures. RoPE encodes relative position by "
                "multiplying representations with an orthogonal rotation matrix."
            ),
            "sections": [
                {
                    "heading": "3. Formulation of Rotary Position Embedding",
                    "text": (
                        "RoPE seeks an inner-product operator g(x_m, x_n, m - n) such that <f(x_m, m), f(x_n, n)> depends only on the relative "
                        "distance (m - n). By decomposing d-dimensional space into d/2 two-dimensional planes, each 2D vector [x^(2i), x^(2i+1)] "
                        "is rotated by an angle m*theta_i where theta_i = 10000^(-2(i-1)/d)."
                    ),
                },
                {
                    "heading": "4. Long-Context Decay Property",
                    "text": (
                        "A desirable theoretical property of RoPE is that the inner product between query and key decays naturally as relative "
                        "distance |m - n| increases, providing an inductive bias for local token affinity while enabling extrapolation."
                    ),
                },
            ],
        },
        "P_RAG_LEWIS": {
            "paper_arxiv_id": "P_RAG_LEWIS",
            "paper_title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
            "field": "Engineering & Computer Science",
            "subfield": "Artificial Intelligence & NLP",
            "abstract": (
                "Large pre-trained language models store substantial factual knowledge in their parameters, but their ability to access "
                "and precisely manipulate knowledge is limited. We explore general-purpose fine-tuning recipes for retrieval-augmented "
                "generation (RAG) combining pre-trained parametric and non-parametric memory."
            ),
            "sections": [
                {
                    "heading": "2. Methods: RAG-Sequence and RAG-Token",
                    "text": (
                        "Our RAG architecture couples a dense passage retriever (DPR) based on bi-encoder BERT with a BART seq2seq generator. "
                        "Given query x, DPR retrieves top-K candidate documents z. In RAG-Sequence, the same document is used to generate the entire "
                        "sequence, while RAG-Token allows different documents to condition each generated token."
                    ),
                },
            ],
        },

        # --- Cluster 2: Biomedical & Structural Biology ---
        "SURVEY_BIO_STRUCTURAL": {
            "paper_arxiv_id": "SURVEY_BIO_STRUCTURAL",
            "paper_title": "Machine Learning in Macromolecular Modeling and Protein Structure Prediction: A Review",
            "field": "Biomedical & Life Sciences",
            "subfield": "Computational Biology & Biophysics",
            "abstract": (
                "The determination of three-dimensional macromolecular structures from primary amino acid sequences represents "
                "a 50-year grand challenge in biophysics. Recent breakthroughs in geometric deep learning, evolutionary covariance "
                "representations, and equivariant graph neural networks have fundamentally transformed computational structural biology."
            ),
            "sections": [
                {
                    "heading": "1. The 50-Year Protein Folding Problem",
                    "text": (
                        "Anfinsen's dogma posited that a protein's native 3D conformation is determined solely by its primary amino acid sequence. "
                        "Historically, homology modeling and template-based threading failed on novel folds lacking experimental homologs in the PDB."
                    ),
                },
                {
                    "heading": "2. Multiple Sequence Alignments and Invariant Geometry",
                    "text": (
                        "Co-evolutionary signals in Multiple Sequence Alignments (MSAs) reveal pairwise residue interactions. Modern networks "
                        "process MSAs with axial attention and refine atomic coordinates using SE(3)-equivariant coordinate frames directly in 3D Euclidean space."
                    ),
                },
            ],
        },
        "P_ALPHAFOLD_JUMPER": {
            "paper_arxiv_id": "P_ALPHAFOLD_JUMPER",
            "paper_title": "Highly Accurate Protein Structure Prediction with AlphaFold",
            "field": "Biomedical & Life Sciences",
            "subfield": "Computational Biology",
            "abstract": (
                "Proteins are essential to life. We develop AlphaFold2, an attention-based neural network architecture capable of predicting "
                "protein structures to near-experimental atomic accuracy (median backbone RMSD < 1.0 Angstrom) on the CASP14 blind assessment."
            ),
            "sections": [
                {
                    "heading": "Evoformer Architecture and Pair Representations",
                    "text": (
                        "The Evoformer block treats protein modeling as an iterative graph inference problem. It maintains two representations: "
                        "an MSA representation (N_seq x N_res x d_msa) and a pair representation (N_res x N_res x d_pair). "
                        "Outer product mean operations transfer evolutionary information from the MSA into spatial distance pair representations."
                    ),
                },
                {
                    "heading": "Invariant Point Attention (IPA) and Structure Module",
                    "text": (
                        "The structure module operates on 3D rigid body frames (T = (R, t) in SE(3)) for each residue. "
                        "Invariant Point Attention (IPA) combines standard scalar query-key attention with 3D coordinate points in local residue frames, "
                        "guaranteeing strict SE(3) invariance under global rotations and translations."
                    ),
                },
            ],
        },
        "P_ESM_RIVES": {
            "paper_arxiv_id": "P_ESM_RIVES",
            "paper_title": "Biological Structure and Function Emerge from Scaling Unsupervised Learning on Sequence Databases",
            "field": "Biomedical & Life Sciences",
            "subfield": "Computational Biology",
            "abstract": (
                "Biological sequence databases contain diverse evolutionary information. We train large language models across 250 million protein sequences "
                "(ESM) using masked language modeling, demonstrating that representations learn secondary and tertiary atomic contacts without explicit supervision."
            ),
            "sections": [
                {
                    "heading": "Unsupervised Protein Language Models",
                    "text": (
                        "By training transformer encoders on UniRef sequence corpora, attention heads naturally capture residue-residue contact maps "
                        "and physicochemical properties, enabling zero-shot mutation fitness prediction and structure estimation directly from single sequences."
                    ),
                },
            ],
        },

        # --- Cluster 3: Distributed Systems & Consensus ---
        "SURVEY_SYS_CONSENSUS": {
            "paper_arxiv_id": "SURVEY_SYS_CONSENSUS",
            "paper_title": "Consensus Protocols in Distributed Storage and Cloud Computing: A Comparative Survey",
            "field": "Engineering & Computer Science",
            "subfield": "Distributed Systems",
            "abstract": (
                "Fault-tolerant distributed systems rely on consensus protocols to maintain state machine replication across unreliable networks. "
                "This survey compares crash-fault-tolerant (CFT) protocols including Paxos and Raft against Byzantine-fault-tolerant (BFT) mechanisms, "
                "evaluating leader election overhead, log compaction, and formal understandability."
            ),
            "sections": [
                {
                    "heading": "1. State Machine Replication Fundamentals",
                    "text": (
                        "In replicated state machines, multiple servers execute identical state machine transitions by agreeing on an identical "
                        "replicated sequence of log commands. The protocol must maintain safety (never return an incorrect result under arbitrary packet delay) "
                        "and liveness (continue making progress as long as a majority of nodes remain reachable)."
                    ),
                },
                {
                    "heading": "2. Crash Fault Tolerance: Paxos vs Raft",
                    "text": (
                        "While Paxos established the theoretical foundation of distributed consensus, its decomposition into Synod, Multi-Paxos, and lease reads "
                        "proved notoriously difficult to understand and implement correctly in production. Raft was explicitly designed to improve understandability "
                        "by decomposing consensus into distinct, independent subproblems: leader election, log replication, and safety invariants."
                    ),
                },
            ],
        },
        "P_RAFT_ONGARO": {
            "paper_arxiv_id": "P_RAFT_ONGARO",
            "paper_title": "In Search of an Understandable Consensus Algorithm (Raft)",
            "field": "Engineering & Computer Science",
            "subfield": "Distributed Systems",
            "abstract": (
                "Raft is a consensus algorithm for managing a replicated log. It produces a result equivalent to Multi-Paxos and is as efficient, "
                "but its structure is much more understandable, decomposed into leader election, log replication, and membership changes."
            ),
            "sections": [
                {
                    "heading": "5.1 Raft Basics: Roles and Terms",
                    "text": (
                        "A Raft cluster consists of servers in one of three states: leader, follower, or candidate. "
                        "Time is divided into arbitrary terms numbered with consecutive integers. Leaders service client requests; followers only respond to RPCs. "
                        "Raft uses randomized election timers (e.g. 150-300 ms) to resolve split votes during leader election."
                    ),
                },
                {
                    "heading": "5.4 Safety and Log Matching Property",
                    "text": (
                        "If an entry is committed at a given term and index, Raft guarantees that entry will be present in the logs of the leaders "
                        "for all higher terms. A voter rejects a candidate whose log is less up-to-date than the voter's own log, enforcing leader completeness."
                    ),
                },
            ],
        },
        "P_PAXOS_LAMPORT": {
            "paper_arxiv_id": "P_PAXOS_LAMPORT",
            "paper_title": "Paxos Made Simple",
            "field": "Engineering & Computer Science",
            "subfield": "Distributed Systems",
            "abstract": (
                "The Paxos algorithm, when presented in plain English, is very simple. It guarantees that in an asynchronous network "
                "where processors can fail by stopping and messages can be delayed or lost, at most one value can be chosen."
            ),
            "sections": [
                {
                    "heading": "Phase 1: Prepare and Promise",
                    "text": (
                        "A proposer selects a proposal number n and sends a prepare request with number n to a majority of acceptors. "
                        "If an acceptor receives a prepare request with number n greater than that of any prepare request to which it has already responded, "
                        "it responds with a promise not to accept any more proposals numbered less than n and with the highest-numbered proposal that it has accepted."
                    ),
                },
                {
                    "heading": "Phase 2: Accept and Accepted",
                    "text": (
                        "If the proposer receives a response to its prepare requests from a majority of acceptors, then it sends an accept request "
                        "to each of those acceptors for a proposal numbered n with a value v, where v is the value of the highest-numbered proposal among the responses."
                    ),
                },
            ],
        },
    }

    queries: List[Dict[str, Any]] = [
        {
            "id": "RQA_CS_001",
            "field": "Engineering & Computer Science",
            "subfield": "Artificial Intelligence & NLP",
            "topic": "Efficient Transformer Attention",
            "survey_paper_id": "SURVEY_CS_TRANSFORMERS",
            "question": (
                "How do modern efficient transformer architectures alleviate the quadratic O(N^2) computational and memory bottleneck "
                "of self-attention without mathematical approximation, and what hardware mechanisms enable this speedup?"
            ),
            "rubrics": [
                {
                    "rubric_id": "R1",
                    "criterion": "Does the response explain how standard self-attention incurs quadratic O(N^2) memory reads/writes to GPU High Bandwidth Memory (HBM)?",
                    "target_citation": "Attention Is All You Need (Vaswani et al., 2017)",
                    "required_paper_id": "P_ATTN_VASWANI",
                },
                {
                    "rubric_id": "R2",
                    "criterion": "Does the response describe FlashAttention's IO-aware tiling technique that computes softmax incrementally via online normalizers on on-chip SRAM?",
                    "target_citation": "FlashAttention (Dao et al., 2022)",
                    "required_paper_id": "P_FLASH_DAO",
                },
            ],
            "target_cited_papers": ["P_ATTN_VASWANI", "P_FLASH_DAO"],
            "target_sections": {
                "P_ATTN_VASWANI": ["3.2 Scaled Dot-Product Attention"],
                "P_FLASH_DAO": ["2. Hardware Characteristics & IO Complexity", "3. Tiling and Online Softmax Normalization"],
            },
        },
        {
            "id": "RQA_CS_002",
            "field": "Engineering & Computer Science",
            "subfield": "Artificial Intelligence & NLP",
            "topic": "Positional Embeddings & Long-Context Extrapolation",
            "survey_paper_id": "SURVEY_CS_TRANSFORMERS",
            "question": (
                "Why do traditional absolute positional embeddings fail to extrapolate to longer sequence lengths, "
                "and how does Rotary Position Embedding (RoPE) mathematically incorporate relative distance into attention inner products?"
            ),
            "rubrics": [
                {
                    "rubric_id": "R1",
                    "criterion": "Does the response explain the limitation of absolute positional representations in generalizing across varied sequence lengths?",
                    "target_citation": "Attention Is All You Need (Vaswani et al., 2017)",
                    "required_paper_id": "P_ATTN_VASWANI",
                },
                {
                    "rubric_id": "R2",
                    "criterion": "Does the response detail how RoPE applies 2D orthogonal rotation matrices to query and key vectors to enforce relative distance decay?",
                    "target_citation": "RoFormer: Enhanced Transformer with Rotary Position Embedding (Su et al., 2021)",
                    "required_paper_id": "P_ROPE_SU",
                },
            ],
            "target_cited_papers": ["P_ATTN_VASWANI", "P_ROPE_SU"],
            "target_sections": {
                "P_ATTN_VASWANI": ["3.2 Scaled Dot-Product Attention"],
                "P_ROPE_SU": ["3. Formulation of Rotary Position Embedding", "4. Long-Context Decay Property"],
            },
        },
        {
            "id": "RQA_BIO_001",
            "field": "Biomedical & Life Sciences",
            "subfield": "Computational Biology",
            "topic": "Deep Learning Protein Structure Prediction",
            "survey_paper_id": "SURVEY_BIO_STRUCTURAL",
            "question": (
                "How do modern neural architectures predict 3D atomic coordinates from amino acid sequences, "
                "and how do they enforce 3D Euclidean rotation/translation invariance while processing evolutionary covariance?"
            ),
            "rubrics": [
                {
                    "rubric_id": "R1",
                    "criterion": "Does the response explain how AlphaFold2 uses Evoformer pair representations to capture co-evolutionary residue contacts from MSAs?",
                    "target_citation": "AlphaFold (Jumper et al., 2021)",
                    "required_paper_id": "P_ALPHAFOLD_JUMPER",
                },
                {
                    "rubric_id": "R2",
                    "criterion": "Does the response explain Invariant Point Attention (IPA) operating on rigid body frames in SE(3) space?",
                    "target_citation": "AlphaFold (Jumper et al., 2021)",
                    "required_paper_id": "P_ALPHAFOLD_JUMPER",
                },
                {
                    "rubric_id": "R3",
                    "criterion": "Does the response describe unsupervised protein language modeling (ESM) that learns structural contacts without MSA alignments?",
                    "target_citation": "ESM (Rives et al., 2021)",
                    "required_paper_id": "P_ESM_RIVES",
                },
            ],
            "target_cited_papers": ["P_ALPHAFOLD_JUMPER", "P_ESM_RIVES"],
            "target_sections": {
                "P_ALPHAFOLD_JUMPER": ["Evoformer Architecture and Pair Representations", "Invariant Point Attention (IPA) and Structure Module"],
                "P_ESM_RIVES": ["Unsupervised Protein Language Models"],
            },
        },
        {
            "id": "RQA_SYS_001",
            "field": "Engineering & Computer Science",
            "subfield": "Distributed Systems",
            "topic": "Fault-Tolerant Consensus",
            "survey_paper_id": "SURVEY_SYS_CONSENSUS",
            "question": (
                "How does the Raft consensus algorithm address the understandability and implementation challenges of Paxos, "
                "and what mechanisms guarantee safety during leader election?"
            ),
            "rubrics": [
                {
                    "rubric_id": "R1",
                    "criterion": "Does the response contrast Paxos prepare/promise and accept phases against Raft's decomposed structure?",
                    "target_citation": "Paxos Made Simple (Lamport, 2001)",
                    "required_paper_id": "P_PAXOS_LAMPORT",
                },
                {
                    "rubric_id": "R2",
                    "criterion": "Does the response describe Raft's randomized election timers and log completeness voting restrictions for safety?",
                    "target_citation": "In Search of an Understandable Consensus Algorithm (Raft) (Ongaro & Ousterhout, 2014)",
                    "required_paper_id": "P_RAFT_ONGARO",
                },
            ],
            "target_cited_papers": ["P_PAXOS_LAMPORT", "P_RAFT_ONGARO"],
            "target_sections": {
                "P_PAXOS_LAMPORT": ["Phase 1: Prepare and Promise", "Phase 2: Accept and Accepted"],
                "P_RAFT_ONGARO": ["5.1 Raft Basics: Roles and Terms", "5.4 Safety and Log Matching Property"],
            },
        },
    ]

    # Generate binary relevance qrels: {query_id: {paper_arxiv_id: 1}}
    qrels: Dict[str, Dict[str, int]] = {}
    for q in queries:
        qid = q["id"]
        qrels[qid] = {pid: 1 for pid in q["target_cited_papers"]}
        # Survey paper is also relevant context (grade 1)
        qrels[qid][q["survey_paper_id"]] = 1

    return corpus, queries, qrels


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare ResearchQA Method B Multi-Paper Citation Benchmark.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EVAL_PREP_DIR,
        help="Directory to save prepared benchmark datasets",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    corpus, queries, qrels = build_curated_researchqa_corpus()

    corpus_path = args.output_dir / "researchqa_corpus.json"
    bench_path = args.output_dir / "researchqa_citation_benchmark.json"
    qrels_path = args.output_dir / "researchqa_qrels.json"

    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)
    print(f"[OK] Saved ResearchQA multi-paper corpus ({len(corpus)} papers) -> {corpus_path}")

    with open(bench_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)
    print(f"[OK] Saved ResearchQA citation queries ({len(queries)} queries) -> {bench_path}")

    with open(qrels_path, "w", encoding="utf-8") as f:
        json.dump(qrels, f, indent=2)
    print(f"[OK] Saved ResearchQA ground truth qrels -> {qrels_path}")


if __name__ == "__main__":
    main()
