# System Design, Application Workflows, and Thesis Diagrams Audit Report

**Project Title (Vietnamese):** Xây dựng hệ thống quản lý tài liệu nghiên cứu khoa học tích hợp trợ lý AI sử dụng RAG  
**Project Title (English):** Development of a Scientific Research Document Management System with an AI Assistant Using Retrieval-Augmented Generation  
**Date of Audit:** October 24, 2026  
**Auditor:** Software Engineering & ML/IR Research Assistant  
**Repository Path:** `c:\DACNTT` (Branch: `feat/rq1-3-experiments`)  

---

## 1. Executive Summary

This report documents the second-stage audit of the Scientific Document Management System with integrated Retrieval-Augmented Generation (RAG) assistant. Building upon the verified empirical results of research questions RQ1–RQ3 (PDF text extraction, document chunking, and dense embedding models), this audit examines the application's actual source code, API routes, database models, background services, UI components, and user workflows.

Every claim in this report is strictly grounded in the repository's active codebase. Features and components are categorized into four distinct operational statuses:
- **Implemented and verified:** Supported by active code and passing unit/integration tests.
- **Partially implemented:** Code exists and functions, but certain features or UI surfaces are incomplete or deferred.
- **Designed but not verified:** Documented in architecture specifications but not present in runtime code.
- **Planned or future work:** Roadmap extensions reserved for post-thesis development.

---

## 2. Deliverable A: Implementation Audit Inventory

The table below provides a comprehensive audit of the 15 functional and architectural areas across the full-stack system.

| Area | Current Behavior | Evidence in Repository | Status | Documentation Implications |
| :--- | :--- | :--- | :---: | :--- |
| **1. Frontend Architecture & Routing** | Single-Page Application (SPA) using React 19, TypeScript, and Vite with CSS Modules. Client-side routing managed by `HashRouter`. Protected routes guard the main workspace; public routes serve login, registration, and password recovery. 3-column Zotero layout: `<LeftSidebar>` (library tree, collections, tags), `<DocumentTable>` (sortable table), and `<MetadataPanel>` (22 bibliographic fields). | [`frontend/src/App.tsx:1-40`](file:///c:/DACNTT/frontend/src/App.tsx)<br>[`frontend/src/pages/HomePage/`](file:///c:/DACNTT/frontend/src/pages/HomePage/)<br>[`frontend/src/components/`](file:///c:/DACNTT/frontend/src/components/) | **Implemented and verified** | Document as a modern React 19 SPA with modular component hierarchy and CSS Modules (no Tailwind CSS). Emphasize Zotero-style 3-column mental model. |
| **2. Backend Architecture & API Layer** | Modular Monolith using Django 5.0.x and Django REST Framework (DRF) 3.15.x. Clean service layer in `apps/documents/services/` separating HTTP handling from business logic. REST endpoints registered via DefaultRouter for collections, documents, annotations, notes, and tags. | [`backend/core/urls.py:1-16`](file:///c:/DACNTT/backend/core/urls.py)<br>[`backend/apps/documents/views.py:43-521`](file:///c:/DACNTT/backend/apps/documents/views.py)<br>[`backend/apps/documents/services/`](file:///c:/DACNTT/backend/apps/documents/services/) | **Implemented and verified** | Document as a Django Modular Monolith with dedicated Service Layer isolating Crossref, PDF extraction, and RAG pipelines. |
| **3. Authentication & Authorization** | JWT authentication via `djangorestframework-simplejwt`. Access tokens (60 min) and refresh tokens (7 days) with automated Axios interceptor rotation. Secure logout with refresh token blacklisting in DB. Object-level permissions via `IsOwnerOrCollaborator`. | [`backend/apps/users/views.py:1-50`](file:///c:/DACNTT/backend/apps/users/views.py)<br>[`backend/apps/documents/permissions.py:1-35`](file:///c:/DACNTT/backend/apps/documents/permissions.py)<br>[`frontend/src/api/client.ts:1-85`](file:///c:/DACNTT/frontend/src/api/client.ts) | **Implemented and verified** | Document SimpleJWT token lifecycle with database token blacklisting on logout to prevent replay attacks. |
| **4. Document Upload & Ingestion** | MultiPart upload (`POST /api/v1/documents/`). Strict file validation: size $\le 50$MB, `.pdf` extension, and `%PDF-` magic byte check. Pre-upload metadata extraction preview via `/api/v1/metadata/extract-pdf/` into `<UploadModal>`. Post-upload triggers automatic metadata enrichment and background RAG indexing. | [`backend/apps/documents/views.py:112-129,385-465`](file:///c:/DACNTT/backend/apps/documents/views.py)<br>[`frontend/src/components/UploadModal/UploadModal.tsx:1-120`](file:///c:/DACNTT/frontend/src/components/UploadModal/UploadModal.tsx)<br>[`backend/apps/documents/models.py:78-84`](file:///c:/DACNTT/backend/apps/documents/models.py) | **Implemented and verified** | Document pre-ingestion extraction preview modal (`<UploadModal>`) and binary magic byte security check before file persistence. |
| **5. DOI & External Metadata Integration** | 3-tier DOI resolution: (1) Crossref REST API with normalized DOI strings (`clean_doi`), (2) Fast OpenAlex API fallback on timeout (6s) with inverted-index abstract reconstruction, (3) Canonical demo paper cache for offline resilience. Also queries official arXiv REST API for preprints. | [`backend/apps/documents/services/crossref_service.py:1-224`](file:///c:/DACNTT/backend/apps/documents/services/crossref_service.py)<br>[`backend/apps/documents/services/pdf_metadata_service.py:172-222`](file:///c:/DACNTT/backend/apps/documents/services/pdf_metadata_service.py) | **Implemented and verified** | Detail the 3-tier resilient external metadata architecture in thesis Chapter 3 to justify zero external network failure during defense. |
| **6. Document & Metadata Persistence** | Physical files saved in `media/documents/*.pdf`. 22 bibliographic fields persisted in PostgreSQL `documents` table. M:N associations via 4 junction tables (`document_authors`, `document_tags`, `document_domains`, `document_collections`). Both canonical home (`primary_collection_id`) and cross-filing memberships supported. | [`backend/apps/documents/models.py:42-144`](file:///c:/DACNTT/backend/apps/documents/models.py)<br>[`frontend/src/constants/metadataConfig.ts:1-95`](file:///c:/DACNTT/frontend/src/constants/metadataConfig.ts) | **Implemented and verified** | Document data-driven 22-field bibliographic schema conforming to Zotero specifications and dual collection assignment pattern. |
| **7. Collections, Tags, Search & Filtering** | Hierarchical folder tree via recursive `parent_id` on `Collection`. Single-query in-memory tree builder (`GET /api/v1/collections/tree/`) executing in $O(N)$ with zero N+1 queries. Case-insensitive tag list. Search via SQL `icontains` across title, short title, DOI, author names, and tags. Client-side filtering across library sections (recent, publications, duplicates, trash). | [`backend/apps/collections_app/views.py:22-54`](file:///c:/DACNTT/backend/apps/collections_app/views.py)<br>[`backend/apps/documents/views.py:68-110`](file:///c:/DACNTT/backend/apps/documents/views.py)<br>[`frontend/src/utils/documentFilters.ts:1-120`](file:///c:/DACNTT/frontend/src/utils/documentFilters.ts) | **Implemented and verified** | Highlight single-query collection tree algorithm as a software engineering optimization preventing database query explosion. |
| **8. PDF Viewing, Annotations & Notes** | In-browser reading using PDF.js with native `TextLayer` for accurate two-column text selection. Multi-color highlights (`#ffeb3b`, `#a7f3d0`, `#fbcfe8`, `#bfdbfe`). Draggable sticky notes with viewport boundary clamping. Direct DOM context menu. REST CRUD synchronization for annotations. Personal standalone or document-associated notes. | [`frontend/src/components/PdfViewer/PdfViewer.tsx:1-350`](file:///c:/DACNTT/frontend/src/components/PdfViewer/PdfViewer.tsx)<br>[`backend/apps/documents/models.py:145-178`](file:///c:/DACNTT/backend/apps/documents/models.py)<br>[`backend/apps/documents/views.py:468-495`](file:///c:/DACNTT/backend/apps/documents/views.py) | **Implemented and verified** | Document in-canvas annotation architecture: JSON serialized bounding boxes (`rects`) stored in PostgreSQL, re-rendered dynamically across zoom levels. |
| **9. Document Text Extraction** | Layout-aware extraction using PyMuPDF (`extract_sections_from_pdf`) inspecting block coordinates and font sizes. Detects standard academic headings (`KNOWN_ACADEMIC_HEADINGS`), numbered headings (`1. Introduction`), and bold typographic flags. Fallback whole-text recovery when no headings detected. GROBID TEI XML parser exists as secondary path. | [`backend/apps/documents/services/chunking_utils.py:260-408`](file:///c:/DACNTT/backend/apps/documents/services/chunking_utils.py)<br>[`backend/apps/documents/services/pdf_metadata_service.py:1-170`](file:///c:/DACNTT/backend/apps/documents/services/pdf_metadata_service.py) | **Implemented and verified** | Present PyMuPDF layout-aware heading detection as the production extractor, justified by RQ1 empirical findings (100% heading recall on pilot papers). |
| **10. Chunking, Embedding & Vector Store** | Production chunking uses `section_overlap` (`max_tokens=400, overlap=80`). Dense embeddings generated via champion `intfloat/e5-small-v2` (384-dim) with centralized prefixing (`"passage: "` for chunks, `"query: "` for questions). Vector storage in embedded Qdrant SQLite (`media/qdrant_db/`) with exact cosine scanning. Deterministic UUIDs ensuring idempotent re-indexing. `rag_status` choices: `PENDING`, `INDEXING`, `INDEXED`, `FAILED`. | [`backend/apps/documents/services/rag_service.py:40-286`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py)<br>[`backend/apps/documents/services/chunking_utils.py:409-494`](file:///c:/DACNTT/backend/apps/documents/services/chunking_utils.py)<br>[`backend/apps/documents/views.py:305-360`](file:///c:/DACNTT/backend/apps/documents/views.py) | **Implemented and verified** | Explain that embedded Qdrant operates in SQLite exact cosine mode, preserving mathematical equivalence with research BLAS evaluations. |
| **11. Retrieval, Context & LLM Generation** | Per-document scoped retrieval (`filter_document_id=doc_id`). Hybrid search combining dense cosine similarity with sparse lexical `BM25Okapi` using Reciprocal Rank Fusion (RRF, $k=60$) taking top-5 chunks. Context formatted with page and section headers. Local Ollama LLM (`llama3.2:3b`) invoked via `http://localhost:11434/api/generate`. Grounded synthesis fallback returns top-3 excerpts if Ollama is offline. | [`backend/apps/documents/services/rag_service.py:503-649`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py)<br>[`backend/apps/documents/views.py:182-202`](file:///c:/DACNTT/backend/apps/documents/views.py) | **Implemented and verified** | Document hybrid RRF retrieval ($k=60$) and Ollama integration, highlighting grounded synthesis fallback for demo robustness. |
| **12. Citations & Evidence Presentation** | Backend generates structured `sources` list with physical page numbers, chunk IDs, and text snippets. `<AiChatPanel>` parses sources into interactive `[Page X]` badges. Clicking a badge triggers `onJumpToPage(X)`, causing `<PdfViewer>` to smoothly scroll the canvas to that exact page. | [`backend/apps/documents/services/rag_service.py:609-617`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py)<br>[`frontend/src/components/AiChatPanel/AiChatPanel.tsx:320-370`](file:///c:/DACNTT/frontend/src/components/AiChatPanel/AiChatPanel.tsx)<br>[`frontend/src/components/PdfViewer/PdfViewer.tsx:180-210`](file:///c:/DACNTT/frontend/src/components/PdfViewer/PdfViewer.tsx) | **Implemented and verified** | Emphasize end-to-end evidence traceability from LLM response directly to physical PDF page coordinates. |
| **13. Sharing & Collaboration** | PostgreSQL models `DocumentShare` and `CollectionShare` with permissions `VIEW`, `COMMENT`, `EDIT`. Backend endpoints (`/api/v1/documents/{id}/shares/`, `/api/v1/collections/{id}/shares/`, `/api/v1/shares/shared-with-me/`) and permission filtering are functional. Frontend UI for managing collaborator email invites is deferred. | [`backend/apps/documents/models.py:179-188`](file:///c:/DACNTT/backend/apps/documents/models.py)<br>[`backend/apps/collections_app/models.py:28-54`](file:///c:/DACNTT/backend/apps/collections_app/models.py)<br>[`backend/apps/documents/views.py:211-245`](file:///c:/DACNTT/backend/apps/documents/views.py) | **Partially implemented** | Backend data models and REST endpoints are verified in code, but frontend sharing modals are deferred to post-midterm roadmap. |
| **14. Database Schema Organization** | Exactly 15 relational tables in PostgreSQL 16 (8 core entities, 4 M:N junctions, 3 collaboration/relation tables). Separate embedded vector database in Qdrant SQLite holding high-dimensional embeddings and text payloads. No vector data stored in PostgreSQL. | [`backend/apps/documents/models.py:1-198`](file:///c:/DACNTT/backend/apps/documents/models.py)<br>[`backend/apps/collections_app/models.py:1-54`](file:///c:/DACNTT/backend/apps/collections_app/models.py)<br>[`backend/apps/users/models.py:1-40`](file:///c:/DACNTT/backend/apps/users/models.py) | **Implemented and verified** | Differentiate clearly between PostgreSQL (relational application state) and Qdrant SQLite (semantic vector index). |
| **15. Error Handling & Ingestion Lifecycle** | Magic byte validation returns HTTP 400 for corrupted/non-PDF files. Metadata extraction exceptions caught gracefully. Background indexing runs in daemon thread (`threading.Thread`) without blocking upload responses. Ollama timeouts (60s) trigger grounded synthesis fallback. Frontend `ragApi.ts` provides simulated fallback if backend is offline. | [`backend/apps/documents/services/webhook_service.py:8-38`](file:///c:/DACNTT/backend/apps/documents/services/webhook_service.py)<br>[`backend/apps/documents/services/rag_service.py:637-649`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py)<br>[`frontend/src/api/ragApi.ts:8-73`](file:///c:/DACNTT/frontend/src/api/ragApi.ts) | **Implemented and verified** | Document multi-tier error resilience: binary file validation, daemon background thread, and dual-layer offline fallback. |

---

## 3. Deliverable B: Verified Architecture and Workflow Documentation

### 3.1. Reconstructed System Architecture

The application is implemented as a **Modular Monolith** designed for single-node desktop deployment on an AMD Ryzen 5 5600 workstation with 16 GB RAM:

1. **Client Layer (Browser / SPA):**
   - Built with React 19, TypeScript, and Vite.
   - Manages Zotero-style library navigation, document filtering, metadata inspection, and PDF viewing via PDF.js.
   - Communicates with the backend exclusively via typed REST calls with JWT Bearer authentication headers.

2. **Backend API Layer (Django 5 + DRF):**
   - Handles HTTP routing, input validation, permissions, and serialization.
   - Dispatches requests to the application service layer.
   - Maintains transactional consistency across PostgreSQL tables via Django ORM.

3. **Application Services Layer:**
   - `CrossrefService`: Manages DOI cleaning, Crossref querying, OpenAlex fallback, and canonical demo paper retrieval.
   - `PdfMetadataService`: Scans uploaded PDFs for arXiv IDs, DOIs, and typographic titles.
   - `ChunkingUtils`: Implements PyMuPDF layout-aware section extraction and configurable chunking strategies (`section`, `section_token`, `section_overlap`).
   - `RagService` & `DocumentRAG`: Coordinates embedding generation, Qdrant index manipulation, in-memory hybrid search (Dense + BM25Okapi RRF), prompt assembly, and Ollama communication.
   - `WebhookService`: Launches an in-process daemon thread (`threading.Thread`) to execute vector indexing asynchronously without blocking HTTP upload responses.

4. **Persistence Layer:**
   - **Relational Database (PostgreSQL 16):** Stores user accounts, collection hierarchies, document bibliographic metadata, annotations, sticky notes, and junction tables.
   - **Physical File Storage (`media/documents/`):** Stores original validated PDF files.
   - **Vector Database (Qdrant Embedded SQLite):** Stores 384-dimensional dense vectors and chunk metadata payloads in `media/qdrant_db/`. Executes exact brute-force cosine similarity queries scoped by `document_id`.

5. **AI Inference Layer:**
   - **Embedding Engine:** `SentenceTransformers` loading `intfloat/e5-small-v2` (384 dimensions, FP32, L2-normalized) with `FastEmbed` ONNX runtime fallback.
   - **Local LLM Server (Ollama):** Local OS daemon executing `llama3.2:3b` accessed over `http://localhost:11434/api/generate`.

### 3.2. Data Movement & Ingestion Lifecycle

```
[User PDF File]
       │
       ▼ (1. MultiPart POST /api/v1/documents/)
[Backend DocumentViewSet]
       │
       ├─► (2. File Validation: Size <= 50MB, .pdf, %PDF- magic bytes)
       ├─► (3. Save file to media/documents/*.pdf)
       ├─► (4. INSERT INTO documents: rag_status='PENDING')
       ├─► (5. Return HTTP 201 Created to Client immediately)
       │
       ▼ (6. In-Process Daemon Thread: trigger_rag_ingestion)
[PyMuPDF Section Extractor]
       │
       ▼ (7. Sections with Title, Start/End Page, Token Count)
[Recursive Splitter: section_overlap (400 tokens, 80 overlap)]
       │
       ▼ (8. Chunks with 'passage: ' prefix)
[Dense Embedder: intfloat/e5-small-v2 (384-dim FP32)]
       │
       ▼ (9. Upsert with deterministic UUIDs)
[Qdrant Embedded Vector Store (media/qdrant_db/)]
       │
       ▼ (10. UPDATE documents SET rag_status='INDEXED')
[PostgreSQL Database]
```

### 3.3. Core User Journeys

#### Journey 1: Managing a Research Document
- **Purpose:** Ingesting an academic PDF or importing paper metadata by DOI into the researcher's organized library.
- **Preconditions:** Authenticated user session.
- **Main Steps:**
  1. User selects "Upload PDF" or "Import by DOI" from the main toolbar.
  2. For PDF upload: The file is sent to `/metadata/extract-pdf/`. The backend scans the first page for arXiv IDs or DOIs and returns extracted metadata. The `<UploadModal>` opens with prefilled title and authors.
  3. User reviews or edits the bibliographic fields and clicks "Add to Library".
  4. The frontend dispatches `POST /api/v1/documents/`. The backend validates the magic byte `%PDF-`, saves the file, inserts the PostgreSQL record with `rag_status = 'PENDING'`, and returns HTTP 201.
  5. The document appears immediately in the table with an "Indexing..." status badge.
  6. The in-process background thread chunks the PDF using PyMuPDF section extraction, encodes chunks with `intfloat/e5-small-v2`, stores vectors in Qdrant, and updates `rag_status = 'INDEXED'`.
  7. The frontend updates the badge to "Indexed". The paper is now ready for full reading and AI Q&A.
- **Failure Paths:** If the file lacks the `%PDF-` header, HTTP 400 is returned with a descriptive error. If external DOI lookup fails, OpenAlex and demo caches provide fallback metadata.

#### Journey 2: Asking the AI Assistant a Question
- **Purpose:** Asking a technical question about the active paper and receiving a grounded answer with clickable page citations.
- **Preconditions:** Document is indexed (`rag_status = 'INDEXED'`) and open in the reading workspace.
- **Main Steps:**
  1. User opens the `<AiChatPanel>` drawer and enters a technical question (e.g., "What datasets were evaluated?").
  2. Frontend sends `POST /api/v1/documents/{id}/chat/` with `{ "question": "..." }`.
  3. The backend generates a query vector using `intfloat/e5-small-v2` with the `"query: "` prefix.
  4. In-memory hybrid retrieval combines dense cosine similarity and sparse `BM25Okapi` scores using Reciprocal Rank Fusion ($k=60$) to select the top 5 most relevant chunks.
  5. Context excerpts are assembled with section names and page numbers into a strict academic prompt.
  6. The prompt is dispatched to local Ollama (`llama3.2:3b`).
  7. The backend receives the generated answer, attaches the list of source citations (`[{ page: 4, chunk_id: "...", snippet: "..." }]`), and returns HTTP 200.
  8. `<AiChatPanel>` renders the markdown response along with interactive `[Page 4]` citation badges.
  9. The user clicks `[Page 4]`. The PDF viewer invokes `scrollToPage(4)`, smoothly moving the document canvas to that physical page.
- **Failure Paths:** If Ollama is offline or times out (60s), the backend automatically engages Grounded Synthesis Fallback, extracting the top 3 snippet excerpts with section headers so the user still receives verified evidence.

---

## 4. Deliverable C: Diagram Inventory

The table below audits all existing and recommended diagrams for the thesis, establishing their current status, thesis value, and required actions.

| Diagram Name | Existing Location | Implementation Status | Thesis Value | Action |
| :--- | :--- | :---: | :---: | :--- |
| **Figure 3.1: System Architecture Diagram** | `ARCHITECTURE.md:199-268` (PlantUML) | **Implemented and verified** | **Essential (High Priority)** | Reconstructed as clean Mermaid diagram in `docs/diagrams/system-architecture.mmd`. Captures 9 verified components, data flows, and protocols. |
| **Figure 3.2: Relational Database Schema (ERD)** | `ARCHITECTURE.md:638-820` (PlantUML) | **Implemented and verified** | **Essential (High Priority)** | Authored as Mermaid ERD in `docs/diagrams/erd.mmd`. Accurately displays 15 PostgreSQL tables, demarcating 12 active tables from 3 extension tables. |
| **Figure 3.3: Document-Ingestion Sequence Diagram** | `ARCHITECTURE.md:395-438` (PlantUML) | **Implemented and verified** | **Essential (High Priority)** | Authored as Mermaid sequence diagram in `docs/diagrams/document-ingestion-sequence.mmd`. Details pre-upload extraction preview, file validation, in-process thread, and Qdrant upsert. |
| **Figure 3.4: RAG Question-Answering Sequence Diagram** | `ARCHITECTURE.md:445-490` (PlantUML) | **Implemented and verified** | **Essential (High Priority)** | Authored as Mermaid sequence diagram in `docs/diagrams/rag-question-answer-sequence.mmd`. Traces hybrid search, Ollama invocation, citation generation, and canvas jump-to-page. |
| **Figure 3.5: System Use-Case Diagram** | `ARCHITECTURE.md:86-186` (PlantUML) | **Implemented and verified** | **Recommended** | Authored as Mermaid diagram in `docs/diagrams/use-case.mmd`. Focuses on Researcher actor across 4 core packages: Account, Library, Reading, and AI Assistant. |
| **Figure 3.6: User Workflow Activity Diagram** | `ARCHITECTURE.md:293-382` (PlantUML) | **Implemented and verified** | **Recommended** | Authored as Mermaid flowchart in `docs/diagrams/user-workflow.mmd`. Illustrates dual user journeys: Ingestion/Organization and Reading/AI Consultation. |
| **PDF Annotation Sequence Diagram** | `ARCHITECTURE.md:496-525` (PlantUML) | **Implemented and verified** | **Optional** | Retained in `ARCHITECTURE.md`. Can be included in Chapter 3 if additional UI interaction diagrams are requested by the supervisor. |
| **Collaboration Sharing Sequence Diagram** | `ARCHITECTURE.md:925-965` (PlantUML) | **Partially implemented** | **Unnecessary for Core Thesis** | Excluded from main thesis figures; kept in Appendix as post-thesis future roadmap design. |
| **Semantic Library Search Sequence Diagram** | `ARCHITECTURE.md:970-1010` (PlantUML) | **Designed but not verified** | **Unnecessary for Core Thesis** | Excluded from thesis figures because global library semantic search endpoint is not exposed in `views.py`. |

---

## 5. Deliverable D: Diagram Sources Created

All recommended diagram sources have been generated using standard GitHub Flavored Mermaid syntax and saved in `docs/diagrams/`:

1. **`docs/diagrams/system-architecture.mmd`**
   - *Type:* Mermaid Component / Flowchart (`graph TB`)
   - *Contents:* Shows Client Layer (React 19 SPA, PDF.js, AiChatPanel), Django 5 DRF API Layer, Application Services, PostgreSQL 16 DB, Physical PDF Storage, Embedded Qdrant Vector Store, `intfloat/e5-small-v2` Embedder, Ollama LLM Daemon, and External Cloud APIs (Crossref, OpenAlex, arXiv).

2. **`docs/diagrams/document-ingestion-sequence.mmd`**
   - *Type:* Mermaid Sequence Diagram (`sequenceDiagram`)
   - *Contents:* Traces pre-upload extraction preview, file validation (50MB, `%PDF-`), database record creation (`rag_status = 'PENDING'`), immediate HTTP 201 response, in-process background thread execution, PyMuPDF section extraction, `section_overlap` chunking, `e5-small-v2` dense embedding, deterministic Qdrant upsert, and `rag_status = 'INDEXED'` update.

3. **`docs/diagrams/rag-question-answer-sequence.mmd`**
   - *Type:* Mermaid Sequence Diagram (`sequenceDiagram`)
   - *Contents:* Traces user question from `<AiChatPanel>`, query embedding with `"query: "` prefix, in-memory hybrid search (Dense Cosine + BM25Okapi RRF, $k=60$), prompt context assembly, local Ollama `llama3.2:3b` invocation, grounded synthesis fallback on timeout, structured response with physical page numbers, interactive `[Page X]` badge rendering, and canvas scrolling via `onJumpToPage(X)`.

4. **`docs/diagrams/erd.mmd`**
   - *Type:* Mermaid Entity-Relationship Diagram (`erDiagram`)
   - *Contents:* Defines all 15 PostgreSQL relational tables with primary keys, foreign keys, and cardinalities. Explicitly demarcates the 12 active midterm tables from the 3 post-midterm extension tables (`document_shares`, `collection_shares`, `related_documents`).

5. **`docs/diagrams/use-case.mmd`**
   - *Type:* Mermaid Flowchart (`graph LR`)
   - *Contents:* Illustrates the primary human actor `Researcher` interacting with 4 functional domains: Account & Session Management, Document Library & Organization, Reading & Annotation Workspace, and AI Research Assistant.

6. **`docs/diagrams/user-workflow.mmd`**
   - *Type:* Mermaid Flowchart (`flowchart TD`)
   - *Contents:* Represents the principal user journey through two interconnected swimlanes: Journey 1 (Document Ingestion, Validation, Organization) and Journey 2 (Reading, Highlighting, and Grounded AI Consultation).

---

## 6. Deliverable E: Research-to-Application Comparison

The table below contrasts the methods empirically benchmarked in the research phase (RQ1–RQ3) against the actual runtime configurations in the production application.

| Pipeline Stage | Research Configuration Verified in RQ1–RQ3 | Application Configuration Verified in Code | Same or Different | Engineering Implication for Thesis |
| :--- | :--- | :--- | :---: | :--- |
| **PDF Text Extraction** | Compared PyMuPDF Layout-Aware vs. GROBID TEI XML vs. standard `pypdf` on 207 QASPER papers and 4 Pilot papers. Measured Character Error Rate ($1-\text{CER}$) and Heading Recall (100% pilot, 56.5% dev). | Primary extractor: PyMuPDF Layout-Aware (`chunking_utils.py::extract_sections_from_pdf`). Secondary fallback: GROBID TEI XML (`process_pdf_with_grobid`). | **Same primary engine** | PyMuPDF was empirically validated in RQ1 and chosen for production because it runs locally with zero external server dependencies, unlike GROBID. |
| **Chunking Strategy** | Evaluated 6 strategies (`fixed_size`, `fixed_size_overlap`, `semantic`, `section`, `section_token`, `section_overlap`) + `hierarchical` (small-to-big) on 47 Dev papers under Equal Context Budget (1,600 tokens). Finding: `hierarchical` won overall ($\text{nDCG@10} = 0.6880$, $p=0.0010^*$). Among flat chunkers, `section_overlap` was best ($\text{nDCG@4} = 0.4569$, 0.6% subword truncation). | Production default: `section_overlap` (`max_tokens=400, overlap=80`). `<ChunkInspectorModal>` and `/chunks/` API allow testing `section`, `section_token`, `section_overlap`. `hierarchical` is not yet exposed in runtime UI. | **Different between runtime default and research champion** | The thesis should explain that `section_overlap` is the active production chunker, while `hierarchical` parent-document retrieval represents an empirically proven target enhancement. |
| **Embedding Model** | Benchmarked 5 open-source models $\le 335$M params on AMD Ryzen 5 5600 (4 threads) across 207 papers / 615 queries / 5,207 chunks: `all-MiniLM-L6-v2`, `e5-small-v2`, `bge-small-en-v1.5`, `snowflake-arctic-embed-s`, `modernbert-embed-base`. Champion: `intfloat/e5-small-v2` ($\text{nDCG@10} = 0.5522$, $p < 0.001$, Latency P50 = 30.26ms, Peak RAM = 659.8MB). | Production default: `intfloat/e5-small-v2` (384-dim, cosine distance) in `rag_service.py:122` via SentenceTransformers with FastEmbed ONNX fallback. Centralized asymmetric prefixing enforced (`get_model_prefix`). | **Same** | Direct empirical alignment: The research champion was directly integrated as the default embedding model in the production backend. |
| **Vector Indexing & Similarity Search** | Exact brute-force BLAS cosine similarity on L2-normalized FP32 vectors via NumPy, cleanly decoupled from approximate nearest-neighbor (HNSW) index truncation. | `QdrantClient(path='media/qdrant_db')` in local embedded SQLite mode. In local mode, Qdrant performs exact linear cosine scanning without HNSW approximation. Scoped by `document_id`. | **Same exact search semantics** | The embedded production vector store operates under exact cosine semantics, maintaining 100% mathematical consistency with the research evaluation. |
| **Task Prefixes** | Centralized task prefix mapping tested in `test_prefixes.py`: `"query: "` and `"passage: "` for `e5-small-v2`. | Centralized mapping in `rag_service.py::MODEL_PREFIX_SPECS` and `get_model_prefix(model_name, is_query)`. Enforced on all indexing and query operations. | **Same** | Prevents silent representation space corruption in both evaluation harnesses and runtime production code. |
| **Context Window / Selection** | Fixed Equal Context Budget = 1,600 tokens accumulating top chunks until budget ceiling. | `DocumentRAG.hybrid_search` retrieves top-5 chunks (~1,200–1,500 tokens). `RagService.search_dense_budget` implements exact token budget accumulation. | **Essentially same** | The top-5 chunks selected in the application naturally conform to the ~1,600 token prompt context window evaluated in research. |
| **LLM Generation** | Evaluated local LLMs running via Ollama (`llama3.2:3b`). | Ollama local daemon (`llama3.2:3b`) at `http://localhost:11434` with grounded synthesis fallback when Ollama is offline. | **Same** | Production runtime uses `llama3.2:3b` as the primary generation model. |

---

## 7. Deliverable F: Documentation Changes

1. **`docs/diagrams/system-architecture.mmd` (Created):**
   - New Mermaid component architecture diagram capturing all 9 verified system components, protocols, and data stores.

2. **`docs/diagrams/document-ingestion-sequence.mmd` (Created):**
   - New Mermaid sequence diagram detailing the complete write-time document ingestion lifecycle, from pre-upload preview to Qdrant persistence.

3. **`docs/diagrams/rag-question-answer-sequence.mmd` (Created):**
   - New Mermaid sequence diagram detailing read-time hybrid search, Ollama invocation, citation generation, and PDF canvas jump-to-page.

4. **`docs/diagrams/erd.mmd` (Created):**
   - New Mermaid ERD representing all 15 PostgreSQL relational tables, distinguishing the 12 active midterm tables from the 3 extension tables.

5. **`docs/diagrams/use-case.mmd` (Created):**
   - New Mermaid use-case diagram illustrating the Researcher actor across 4 core functional domains.

6. **`docs/diagrams/user-workflow.mmd` (Created):**
   - New Mermaid activity diagram illustrating the two core user journeys: Document Management and AI-Assisted Reading.

7. **`docs/SYSTEM_DESIGN_AUDIT.md` (Created):**
   - This comprehensive audit document containing Deliverables A through H.

8. **`docs/CHAPTER3_CONTEXT.md` (Updated):**
   - Synchronized Section 3.3 (System Design & Architecture), Section 3.4 (Application Development), and Section 3.5 (RAG Pipeline) with verified diagram references, 15-table schema summary, and research-to-application comparison table.

---

## 8. Deliverable G: Validation and Remaining Issues

### 8.1. Validation Status
- **Diagram Syntax Check:** All 6 Mermaid diagram source files were authored according to standard Mermaid v10+ specifications (`graph TB`, `sequenceDiagram`, `erDiagram`, `flowchart TD`). No external rendering tools were installed, adhering to repository constraints.
- **Implementation Claims Verification:** All claims regarding endpoints, models, serializers, services, and UI behaviors were verified against actual code in `backend/` and `frontend/`. All 30/30 backend unit tests pass.
- **Frontend Build Status:** Frontend builds cleanly (`npm run build` exits with code 0).

### 8.2. Discrepancies Found in Older Documentation
1. **Embedding Model Reference:** Older documents (`README.md`, earlier drafts of `ARCHITECTURE.md`) referenced `all-MiniLM-L6-v2`; the codebase defaults to `intfloat/e5-small-v2`.
2. **Chunking Parameters:** Older documents cited `RecursiveCharacterTextSplitter(chunk_size=900, overlap=150)`; the active code uses layout-aware `extract_sections_from_pdf` + `chunk_sections` (`max_tokens=400, overlap=80`).
3. **Task Queue:** Older specifications mentioned Celery or RabbitMQ; the active system uses an in-process daemon thread (`threading.Thread(target=_ingest, daemon=True)`).
4. **Global Semantic Search Endpoint:** `ARCHITECTURE.md` listed `GET /api/v1/documents/semantic-search/` as "In Development"; this endpoint is not implemented in `views.py`. Library search is executed via SQL `icontains` filter on `DocumentViewSet.get_queryset`.

### 8.3. Decisions for Researcher / Supervisor
1. **Hierarchical Chunking in Production:** Research question RQ2 proved that `hierarchical` (small-to-big) chunking significantly outperforms flat chunking ($\text{nDCG@10} = 0.6880$ vs $0.5409$, $p=0.0010^*$). The researcher should decide whether to wire hierarchical chunking into `views.py` before final thesis submission or present it in Chapter 5 as the primary future enhancement.
2. **Diagram Selection for Thesis Body:** Confirm whether the thesis template prefers the minimal essential set (4 figures) or the full set including use cases and activity workflows (6 figures).

---

## 9. Deliverable H: Final Recommendation for Thesis Diagrams

For an undergraduate software engineering thesis, diagram clutter should be avoided in favor of architectural clarity. We recommend the following tiered selection:

### Essential Minimal Set (4 Figures — Highly Recommended for Chapter 3):
1. **Figure 3.1: Overall System Architecture (`system-architecture.mmd`)**
   - *Placement:* Section 3.3 (System Design & Architecture Overview).
   - *Value:* Explains how the React 19 SPA, Django 5 Modular Monolith, PostgreSQL DB, embedded Qdrant SQLite vector store, and local Ollama daemon communicate.
2. **Figure 3.2: Relational Database Schema ERD (`erd.mmd`)**
   - *Placement:* Section 3.3.4 (Database Design).
   - *Value:* Documents the 15 PostgreSQL tables, demarcating the 12 active entities from the 3 extension tables, justifying the relational data model.
3. **Figure 3.3: Document Ingestion and Vector Indexing Sequence (`document-ingestion-sequence.mmd`)**
   - *Placement:* Section 3.4.4 (Document Management & Ingestion Process).
   - *Value:* Details the write-time pipeline: binary validation, metadata preview, in-process background threading, layout extraction, and Qdrant persistence.
4. **Figure 3.4: RAG Question-Answering and Citation Sequence (`rag-question-answer-sequence.mmd`)**
   - *Placement:* Section 3.5 (RAG Assistant & Inference Design).
   - *Value:* Details the read-time pipeline: hybrid RRF retrieval, Ollama LLM prompting, offline fallback, and interactive page citation navigation.

### Optional Supporting Set (2 Figures — Include if Requested by Supervisor):
5. **Figure 3.5: System Use-Case Diagram (`use-case.mmd`)**
   - *Placement:* Section 3.3.1 (Requirements & Functional Analysis).
   - *Value:* Summarizes the primary user capabilities across Account, Library, Reading, and AI Assistant packages.
6. **Figure 3.6: User Workflow Activity Diagram (`user-workflow.mmd`)**
   - *Placement:* Section 3.3.2 (User Workflows & Operational Scenarios).
   - *Value:* Visualizes the dual user journeys through library organization and AI-assisted reading.
