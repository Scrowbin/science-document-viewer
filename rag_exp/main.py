from chunking import fixed_size_chunker, recursive_chunker, semantic_chunker
from eval import dataset_passthrough, evaluate_chunk_strategy, qasper_passthrough
from ranx import compare, evaluate
from langchain_huggingface import HuggingFaceEmbeddings

# import ir_datasets
EMBEDDING_MODEL = "ibm-granite/granite-embedding-125m-english"
embed_model = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL, encode_kwargs={"batch_size": 128}
)
dataset = "beir/fiqa/test"
# pubmed_dataset = "cord19/trec-covid"

# docs, qrels, queries = dataset_passthrough(pubmed_dataset)

docs, qrels, queries = qasper_passthrough()
run_fixed = evaluate_chunk_strategy(fixed_size_chunker, docs, queries, embed_model)

metrics = ["precision@5", "recall@5", "f1@5", "ndcg@5"]

print("--- Fixed Chunking Results ---")
print(evaluate(qrels, run_fixed, metrics))
