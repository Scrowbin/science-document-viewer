from chunking import fixed_size_chunker, recursive_chunker, semantic_chunker
from datasets import load_dataset
from ir_datasets import load
from ranx import Qrels, Run, compare, evaluate
import numpy as np

# %%


def dataset_passthrough(dataset_name):
    dataset = load(dataset_name)
    docs = list(dataset.docs_iter())
    queries = list(dataset.queries_iter())
    qrels_dict = {}

    for qrel in dataset.qrels_iter():
        if qrel.query_id in [q.query_id for q in queries]:
            if qrel.query_id not in qrels_dict:
                qrels_dict[qrel.query_id] = {}
            qrels_dict[qrel.query_id][qrel.doc_id] = qrel.relevance

    qrels = Qrels(qrels_dict)
    return docs, qrels, queries


def evaluate_chunk_strategy(chunk_fn, docs, queries, embed_model):
    chunk_corpus = []
    chunk_map = []  # Maps chunk_index -> parent_doc_id

    # Chunk all documents
    for doc in docs:
        chunks = chunk_fn(doc.text, benchmark=True)
        for c in chunks:
            chunk_corpus.append(c.page_content)
            chunk_map.append(doc.doc_id)

    # Encode chunks
    chunk_embeddings = np.array(embed_model.embed_documents(chunk_corpus))
    # Run retrieval for each query
    run_dict = {}
    for q in queries:
        query_emb = np.array(embed_model.embed_query(q.text))
        # Cosine Similarity
        scores = query_emb @ chunk_embeddings.T

        # Retrieve Top-10 Chunks
        top_k_idx = np.argsort(scores)[::-1][:10]

        run_dict[q.query_id] = {}
        for idx in top_k_idx:
            parent_doc_id = chunk_map[idx]
            score = float(scores[idx])

            # Map back to Parent Doc ID for ranx ground truth matching
            # Keep the highest chunk score if multiple chunks come from the same document
            if (
                parent_doc_id not in run_dict[q.query_id]
                or score > run_dict[q.query_id][parent_doc_id]
            ):
                run_dict[q.query_id][parent_doc_id] = score

    return Run(run_dict)


# 4. Generate Runs
# docs, qrels, queries = dataset_passthrough("beir/fiqa/test")
# run_fixed = evaluate_chunk_strategy(fixed_size_chunker, docs, queries)

# %%
# 5. Evaluate and Compare with ranx
# metrics = ["precision@5", "recall@5", "f1@5", "ndcg@5"]

# print("--- Fixed Chunking Results ---")
# print(evaluate(qrels, run_fixed, metrics))

# # Compare statistically (t-test / norm difference)
# report = compare(
#     qrels=qrels,
#     runs=[run_fixed, run_paragraph],
#     metrics=metrics,
#     max_p=0.05,  # Statistical significance cutoff
# )
# print("\n--- Comparison Report ---")
# print(report)
#


# %%
def qasper_passthrough(split="validation"):
    """
    Loads Qasper from Hugging Face and parses it into docs, queries, and qrels for ranx.

    docs: Dummy objects with .doc_id and .text (full paragraph text or section text)
    queries: Dummy objects with .query_id and .text
    qrels: ranx.Qrels object mapping query_id -> doc_id -> relevance
    """
    ds = load_dataset("allenai/qasper", split=split)

    docs_dict = {}
    queries = []
    qrels_dict = {}

    class Doc:
        def __init__(self, doc_id, text):
            self.doc_id = doc_id
            self.text = text

    class Query:
        def __init__(self, query_id, text):
            self.query_id = query_id
            self.text = text

    for paper in ds:
        paper_id = paper["id"]
        full_text = paper["full_text"]

        # 1. Reconstruct paragraphs as individual retrieved documents
        # Document ID schema: {paper_id}_p_{section_idx}_{paragraph_idx}
        paragraph_map = {}
        for sec_idx, (sec_name, paragraphs) in enumerate(
            zip(full_text["section_name"], full_text["paragraphs"])
        ):
            for p_idx, p_text in enumerate(paragraphs):
                p_id = f"{paper_id}_s{sec_idx}_p{p_idx}"
                # Format: "Section Title: Paragraph Text"
                doc_content = f"{sec_name}: {p_text}" if sec_name else p_text
                docs_dict[p_id] = Doc(p_id, doc_content)
                paragraph_map[(sec_name, p_idx)] = p_id

        # 2. Extract Questions and Evidence Annotations (qrels)
        qas = paper["qas"]
        for q_idx, q_id in enumerate(qas["question_id"]):
            q_text = qas["question"][q_idx]
            queries.append(Query(q_id, q_text))

            # Extract supporting evidence paragraphs across annotators
            relevant_docs = set()
            answers = qas["answers"][q_idx]["answer"]

            for ans in answers:
                if ans.get("unanswerable", False):
                    continue

                # Check for annotated evidence paragraphs
                evidence_list = ans.get("evidence", [])
                for ev in evidence_list:
                    # Match evidence string back to created paragraph IDs
                    for p_id, doc_obj in docs_dict.items():
                        if p_id.startswith(paper_id) and ev in doc_obj.text:
                            relevant_docs.add(p_id)

            if relevant_docs:
                qrels_dict[q_id] = {p_id: 1 for p_id in relevant_docs}

    docs = list(docs_dict.values())
    qrels = Qrels(qrels_dict)

    # Filter queries to only those with valid qrels (ground truth answers)
    queries = [q for q in queries if q.query_id in qrels_dict]

    return docs, qrels, queries
