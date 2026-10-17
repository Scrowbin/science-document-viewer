from exp import fixed_size_chunk
from rag import RAG

with open(
    "/home/oracle/Downloads/output_dir/test_doc_no_metadata.grobid.tei.xml", "r"
) as f:
    doc = f.read()
chunk_a = fixed_size_chunk(doc)

# %%
rag = RAG(chunk_a)
results = rag.embed_and_rerank(
    query="How does the proposed model improve VQA performance?",
    retrieve_k=20,
    rerank_k=5,
)

for doc, score in results:
    print(score)
    print(doc.metadata)
    print(doc.page_content)
    print("---")

# %%
with open("/home/oracle/Downloads/output_dir/attention.pdf.tei.xml", "r") as f:
    sec_doc = f.read()
chunk_b = fixed_size_chunk(sec_doc)
retrieve = RAG(chunk_b)
# %%
results = retrieve.embed_and_rerank(
    query="What were once state of the art approaches to sequence modeling",
    retrieve_k=100,
    rerank_k=5,
)

for doc, score in results:
    print(score)
    print(doc.metadata)
    print(doc.page_content)
    print("---")
# %%
results = retrieve.hybrid_search_embed_and_rerank(
    query="What were once state of the art approaches to sequence modeling",
    retrieve_k=100,
    rerank_k=5,
)

for doc, score in results:
    print(score)
    print(doc.metadata)
    print(doc.page_content)
    print("---")
