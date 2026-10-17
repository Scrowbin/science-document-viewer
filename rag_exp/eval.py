from chunking import fixed_size_chunker, recursive_chunker, semantic_chunker
from langchain_huggingface import HuggingFaceEmbeddings
import ir_datasets
from ranx import Qrels, Run, compare, evaluate
import numpy as np

dataset = ir_datasets.load("beir/fiqa/test")
pubmed_dataset = ir_datasets.load("cord19/trec-covid")

EMBEDDING_MODEL = "ibm-granite/granite-embedding-125m-english"
embed_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


specs = [(200, 50), (400, 100), (800, 100), (800, 200), (1200, 200)]
# ( chunksize, chunk_overlap )
XML_FILE_DIR = "../xml_store/test_doc_no_metadata.grobid.tei.xml"
with open(XML_FILE_DIR, "r") as f:
    file = f.read()
# %%
fixed_size = fixed_size_chunker(file)
fixed_size[3]
# %%
recurv = recursive_chunker(file)
recurv[1]
# %%
sem = semantic_chunker(file, embeddings=embed_model)


# %%
docs = list(dataset.docs_iter())
queries = list(dataset.queries_iter())
qrels_dict = {}


for qrel in dataset.qrels_iter():
    if qrel.query_id in [q.query_id for q in queries]:
        if qrel.query_id not in qrels_dict:
            qrels_dict[qrel.query_id] = {}
        qrels_dict[qrel.query_id][qrel.doc_id] = qrel.relevance

qrels = Qrels(qrels_dict)


def evaluate_chunk_strategy(chunk_fn):
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
run_fixed = evaluate_chunk_strategy(fixed_size_chunker)
# run_paragraph = evaluate_chunk_strategy(chunk_by_paragraph)

# %%
# 5. Evaluate and Compare with ranx
metrics = ["precision@5", "recall@5", "f1@5", "ndcg@5"]

print("--- Fixed Chunking Results ---")
print(evaluate(qrels, run_fixed, metrics))

print("\n--- Paragraph Chunking Results ---")
# print(evaluate(qrels, run_paragraph, metrics))
#
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
# testing things out
chunk_corpus = []
chunk_map = []  # Maps chunk_index -> parent_doc_id

# Chunk all documents
for doc in docs:
    chunks = fixed_size_chunker(doc.text, benchmark=True)
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
