# RAG service review (findings only, fixes deferred)

**Status (2026-11-06):** review only. `backend/apps/documents/services/` was **not changed**, because the combination experiment imports this code (`backend/scripts/eval_common/`, `eval/phases/*`). Apply the fixes below **after the combination run is finished**, then re-run the backend tests and `pytest backend/scripts/eval_common`.

Line numbers refer to the code as of this review.

## A. Safe fixes (no effect on retrieval, chunking, prompt or generation output)

| # | Where | Problem | Fix |
|---|---|---|---|
| A1 | `rag_service.py:164-186` `RagService.embedder` | Lazy init is not thread-safe: `_embedder` is published before `_is_st_model=True`; two threads can load the model twice or call `.embed()` on a SentenceTransformer | Lock + double check; set the flag before publishing |
| A2 | `rag_service.py:729-747` `get_embedding_model` | No lock; if e5 fails it silently falls back to all-MiniLM-L6-v2 (same 384 dims, different vector space: silently wrong results), then returns `None` | Lock; raise `RuntimeError` like `RagService.embedder`; reuse that single instance |
| A3 | `rag_service.py:1004-1007` `evict_rag_instance` | Check-then-delete can raise `KeyError` under concurrency | `_rag_instances.pop(doc_id, None)` |
| A4 | `rag_service.py:1150-1204` `ingest_document` | The worker and a request thread can rebuild the same document's collections at the same time | Module-level `RLock` around the index-write section |
| A5 | `rag_service.py:1267-1288` `_generate_with_ollama` | Non-200 responses are not logged; a trailing `/` in the base URL gives `//api/generate`; no `keep_alive`/`num_predict`/streaming | Log status, strip slash, check JSON type. Later: `keep_alive`, `num_predict` (~400), streaming with cancel on client disconnect |
| A6 | `chunking_utils.py:222-252, 398-504`; `pdf_metadata_service.py:96-99` | PDF opened with PyMuPDF is not closed on exceptions (file handle leak; on Windows blocks deleting the PDF) | `try/finally` close |
| A7 | `webhook_service.run_ingestion` | A document deleted while queued/indexing is re-indexed and its Qdrant collections re-created (orphans) | Skip if the row is gone; after ingestion, delete Qdrant data and evict if the row was deleted meanwhile |
| A8 | `crossref_service.py:106, 154` | Raw DOI inserted into the URL path (`?`, `#`, `../` can rewrite the request; host is fixed, so not SSRF) | Reject non-strings; `urllib.parse.quote(doi, safe='/')`; require the DOI pattern |
| A9 | `crossref_service.py:113-118, 182-186, 221` | OpenAlex `primary_location: null`/`author: null` raises; Crossref `date-parts [[null]]` gives year "None"; the shared demo dict is returned (mutable) | Null-safe access; skip null dates; return a copy |
| A10 | `rag_service.py:157, 907-918` | One local-mode `QdrantClient` shared by the worker (which drops/recreates collections) and request threads, with no lock; errors fall into a fallback that loads a second model | Module-level `RLock` around client calls |
| A11 | `rag_service.py:726, 806, 859` | `_rag_instances` grows forever; a BM25 index is built even in `dense` mode; dense queries fetch all child payloads | Small LRU (~10 docs); build BM25 lazily; limit `retrieve_k` |
| A12 | `crossref_service.py:160, 215` | Crossref then OpenAlex sequentially, 6 s each (up to 12 s) | Run in parallel or shorten timeouts |
| A13 | `query_document` (`rag_service.py:1307-1402`) | The low-similarity refusal returns no `refused` flag; the timeout fallback has no `degraded` flag (the frontend has to guess from the model name); the model label says "Grounded Hybrid RAG" although the default is dense; `top_k=5` is hard-coded | Add `refused`/`degraded` flags and a setting for `top_k`; fix the label |
| A14 | `rag_service.py:1291-1304, 1396, 1454-1474` | Prompt injection: PDF text and the user-chosen title go into the prompt without delimiters; fallback answers paste raw PDF text into Markdown | Wrap snippets in clear delimiters and tell the model to treat them as data. (The frontend no longer renders Markdown images, which removes the main exfiltration path.) |
| A15 | `question_guard.py:70-77` | A flagged word is allowed if it appears anywhere in the PDF, so the PDF author can switch the guard off; trivial spelling tricks pass | Document it as a best-effort content filter (it guards no secrets: the LLM never sees any) |

## B. Issues that would change experiment outputs (do not fix during the evaluation)

| # | Where | Problem | Effect |
|---|---|---|---|
| B1 | `chunkers.py` (fixed) | **Fixed 2026-11-06 with the user's approval.** `chunk_fixed_size`, `chunk_fixed_size_overlap` and `chunk_semantic` read `start_page` while sections carry `page_start`, so every chunk got page 1 | Each chunk now gets the start page of the section where it begins. Chunk texts, ids and token counts are byte-identical to before (checked against the previous code); no experiment metric uses chunk pages. Regression test: `WholeDocumentChunkerPageTests`. |
| B2 | `chunkers.py:311-342` `chunk_hierarchical` | Can emit a redundant last child fully inside the previous window (e.g. 270-word section: [120,270) then [240,270)) | Duplicate units in the candidate pool; changes rankings slightly. Fix only together with a re-run. |
| B3 | `chunkers.py:18-21` vs `chunking_utils.py:363-368` | Two `estimate_tokens` disagree on empty text (1 vs 0) | Negligible; unify later |
| B4 | `chunkers.py:164` `chunk_semantic` | Hard-codes the e5 `passage: ` prefix regardless of the embedder (AGENTS.md directive 8) | Only the semantic-chunking extension; note in the thesis if relevant |
| B5 | `chunking_utils.py:276-309` | Hierarchical branch returns `[]` without trying the GROBID/page fallbacks | Only for PDFs without text; same result in practice |
| B6 | `rag_service.py:925-927` (`rrf_legacy` only) | BM25 may give NaN when all child texts are empty | Not on the default path; unverified |

## C. Server smoothness items that need `services/` (deferred)
- No streaming (`stream: False`): the user waits ~30 s on a spinner; Stop does not cancel the Ollama call, so the next question waits behind it (A5).
- First chat pays the model and Qdrant start-up cost; Qdrant local mode loads every collection, and many `doc_*` collections on disk have no database row (add a cleanup command and a warm-up step; the warm-up must not run in evaluation scripts).
- Re-index with a strategy override still runs inside the request (`trigger_rag_ingestion` has no strategy parameter).

Not in `services/`, recommended without code changes:
- set `OLLAMA_KEEP_ALIVE=1h` in Ollama's environment so the model is not unloaded after 5 idle minutes;
- run `runserver 8000 --noreload` when not editing backend code (the reloader restarts the process on every save and drops the in-memory indexing queue).
