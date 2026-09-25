# Comprehensive Project Audit & Midterm Scope Reduction Report

---

> **Project Title:** Development of a Scientific Research Document Management System with an AI Assistant Using Retrieval-Augmented Generation (RAG)  
> **Audit Milestone:** Week 1 (~14 days before Midterm Defense & Live Demo)  
> **Report Objectives:** Audit codebase status, uncover technical debt and scope creep, eliminate non-essential distractions, and formulate a **lean 14-day action plan** to deliver a verified End-to-End RAG workflow for the academic evaluation committee.

---

# 1. Project Context & Core Identity

The formally registered academic objectives of this capstone project comprise:
* Developing a web-based scientific document management platform (PDF upload, storage, 22 metadata fields, Crossref DOI metadata auto-fetching).
* Library workspace organization: hierarchical folder collections (nested trees), multi-category tags, and dynamic table filtering.
* Desktop-grade interactive PDF reader (PDF.js canvas) with text-layer selection, multi-color highlighting, and sticky notes.
* **Building a robust RAG (Retrieval-Augmented Generation) pipeline** operating over the user's uploaded scientific PDF repository.
* **Empirical evaluation of RAG methodologies** (chunking granularity, embedding models, retrieval accuracy, latency).
* **AI Research Assistant Panel** providing: grounded document Q&A, structured 1-click summarization, and interactive citation badges.

> [!IMPORTANT]
> ### CORE IDENTITY DEFINITION
> **"A web application for scientific research document management integrating an AI assistant for grounded Q&A and summarization powered by RAG across the user's document library."**  
> Every feature that does not directly support demonstrating this core proposition during the Midterm Demo must be **FROZEN**, **SIMPLIFIED**, or **DEFERRED** to the final graduation phase.

---

# 2. Comprehensive Codebase Status Audit

Direct technical inspection of repository files, databases, and dependencies at `c:\DACNTT`:

```text
c:\DACNTT/
├── ARCHITECTURE.md          # Modular Monolith specs, 15-table ERD, 22 REST endpoints, Qdrant schema
├── AGENTS.md                # Single source of truth & roadmap tracker for autonomous agents
├── additional docs/         # App_db.sql (PostgreSQL 15-table schema), funcs.txt, use_case_for_now.png
├── backend/
│   ├── apps/
│   │   ├── users/           # Custom User model, SimpleJWT lifecycle, blacklist logout, test suite
│   │   ├── collections_app/ # Single-query hierarchical tree builder (O(N)), sharing permissions
│   │   └── documents/       # Document CRUD, 22 metadata fields, Crossref DOI service, annotations, notes
│   ├── core/                # Django 5.x root settings, URL router, SimpleJWT configuration
│   ├── requirements.txt     # django, djangorestframework, psycopg2, pymupdf, langchain, qdrant-client
│   └── bruno_collection/    # Bruno REST API test collection (Auth, Collections, Documents, Metadata)
├── frontend/
│   ├── src/
│   │   ├── components/      # TabBar, LeftSidebar, MainToolbar, DocumentTable, MetadataPanel, PdfViewer
│   │   ├── pages/           # HomePage (~290 lines orchestrator), LoginPage, RegisterPage
│   │   ├── hooks/           # useDocuments, useCollections, useDoiModal, useKeyboardShortcuts
│   │   ├── api/             # Axios client with 401 refresh queue, documentsApi, collectionsApi, annotationsApi
│   │   └── index.css        # Vanilla CSS Modules design tokens (no Tailwind CSS)
│   └── package.json         # React 19 + TypeScript + Vite + PDF.js canvas
└── scripts/
    └── start-all.mjs        # Unified runner launching PostgreSQL, Django (8000), and Vite (5173) concurrently
```

### A. Completion Categorization by Functional Area

1. **Implemented & Production-Ready:**
   * **Authentication & Session:** Registration, dual-token JWT login, automatic token rotation via Axios interceptors on 401 responses, server-side token blacklist logout (`/api/v1/auth/logout/`), and `ProtectedRoute` route guards.
   * **Library & Document Management:** Full document CRUD over 22 metadata fields, advanced filtering by collections/tags/trash, multi-channel document assignment (drag-and-drop, right-click context menu, MetadataPanel dropdown).
   * **Crossref DOI Metadata Automation:** `crossref_service.py` fetches and cleans journal metadata from Crossref REST API, normalizes author lists into typed arrays (`string[]`), and auto-populates modal forms.
   * **Hierarchical Collections Tree:** Single-query O(N) tree builder with `Count('primary_documents')` aggregation avoiding N+1 database queries.
   * **Interactive PDF.js Viewer:** High-fidelity canvas rendering, native TextLayer for text selection, multi-color highlighting, draggable sticky notes with boundary clamping, custom right-click context menu, and REST annotation persistence.
   * **Automated Test Suites:** 19/19 backend tests passing (`apps.documents.tests`, `apps.users.tests`), frontend ESLint passing with 0 errors, and Vite TypeScript build passing with code 0.

2. **Implemented but Incomplete:**
   * **Full-Text & Semantic Search:** Currently limited to SQL `icontains` filters on title, author, DOI, and tags; deep vector semantic search is pending.
   * **Collaborative Sharing Dialog:** Database models and permission enforcement (`document_shares`, `collection_shares`, `VIEW`, `COMMENT`, `EDIT`) are active in DRF, but the frontend lacks an interactive modal dialog.

3. **Previously Mocked / Stubbed:**
   * **RAG Trigger Webhook:** `trigger_rag_ingestion` in `backend/apps/documents/services/webhook_service.py` was merely an asynchronous thread sending an HTTP POST to a dummy port (`http://localhost:8001`) with an empty `except: pass` block.

4. **Documented but Unimplemented:**
   * **RAG Core Pipeline:** Layout-aware text extraction, text chunking, vector embedding generation, Qdrant vector indexing, scoped retrieval, prompt assembly, and local LLM response streaming.
   * **AI Assistant UI:** Slide-out chat panel component, message bubbles, streaming state, and source page grounding badges.
   * **Empirical Evaluation Benchmark:** Evaluation dataset, ground-truth questions, and performance comparison script.

5. **Identified Scope Creep (Distractions to Drop):**
   * Non-essential tasks in prior backlogs: Arbitrary file upload (`.docx`, `.xlsx`, `.epub`), User Profile/PFP avatar uploader, and BibTeX/RIS multi-format citation export parsers.

### B. Current End-to-End Pipeline Connectivity

```text
[User]
   ↓ (100% OPERATIONAL)
[Login / JWT Session]
   ↓ (100% OPERATIONAL)
[Library Table & 22 Metadata Fields]
   ↓ (100% OPERATIONAL)
[PDF Upload / Crossref DOI Lookup]
   ↓ (100% OPERATIONAL)
[PDF.js Canvas Reading & Annotations]
   ↓ 
[RAG Ingestion Trigger]  ──► [PREVIOUS GAP: Embedded service layer now specified]
   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
   • Layout-Aware PDF Extraction: [NEXT UP: PyMuPDF with sort=True]
   • Text Chunking Strategy:       [NEXT UP: RecursiveSplitter 900/150]
   • Local Dense Embeddings:       [NEXT UP: all-MiniLM-L6-v2 384-dim]
   • Vector Storage (Qdrant):      [NEXT UP: Local Embedded media/qdrant_db/]
   • Grounded LLM Response:        [NEXT UP: Ollama llama3.2:3b]
   • Frontend AI Chat Panel:       [NEXT UP: React <AiChatPanel>]
```

### C. Visual Progress Audit

```text
Authentication & Security   ██████████  100% (JWT, Token Blacklist, Role Guards)
Document Management & CRUD  █████████░   90% (22 Fields, M2M Collections & Tags)
PDF Reader & Annotations    █████████░   90% (Canvas, TextLayer, Notes, Highlights)
Metadata DOI Automation     ████████░░   80% (Crossref live, ISBN/arXiv disabled)
RAG Document Ingestion      █░░░░░░░░░   10% (Webhook stub replaced with service spec)
Vector Storage & Indexing   ░░░░░░░░░░    0% (Queued for execution)
Retrieval & Similarity      ░░░░░░░░░░    0% (Queued for execution)
AI Assistant UI / Chatbot   ░░░░░░░░░░    0% (Queued for execution)
RAG Performance Evaluation  ░░░░░░░░░░    0% (Queued for execution)
```

> [!CAUTION]
> ### 🚨 PRIMARY RISK IDENTIFIED FOR MIDTERM DEFENSE
> The document management and PDF viewer components are built to commercial desktop standards. However, **THE SECOND HALF AND CORE THEME OF THE THESIS ("AI Assistant Using RAG") HAS 0% RUNNING CODE**.  
> If engineering effort is dissipated on visual tweaks or extraneous features (avatar upload, citation parsers), the project will fail the midterm evaluation for lack of demonstrable RAG capabilities.

---

# 3. Granular Feature Evaluation & Disposition

Every feature is evaluated against 4 decision categories:
1. **KEEP NOW:** Mandatory for the live Midterm Demo.
2. **SIMPLIFY:** Retain a streamlined, local-first implementation to minimize delivery risk.
3. **DEFER:** Postpone to the post-midterm final thesis phase.
4. **REMOVE:** Drop permanently as scope creep.

---

## 3.1. Authentication & User Management

### 1. Authentication Service (Registration, Login, JWT Lifecycle)
* **Status:** 100% complete (SimpleJWT, refresh queue, blacklist logout).
* **Thesis Relevance:** Enables isolated user library namespaces.
* **Midterm Value:** High (proves system security and multi-user isolation).
* **Recommendation:** **KEEP NOW (FREEZE CODE)**.

### 2. Account Profile Management (Avatar Upload, Password Change - BACKLOG-3)
* **Status:** Unimplemented (`/auth/me/` endpoint exists).
* **Thesis Relevance:** Zero. Academic evaluation focuses on RAG performance, not avatar forms.
* **Recommendation:** **DEFER**.

### 3. Third-Party OAuth2 (Google / GitHub SSO)
* **Status:** Previously deferred in `AGENTS.md`.
* **Recommendation:** **DEFER**.

### 4. Google Drive-Style Collaboration UI
* **Status:** Database models and DRF API complete; frontend share dialog missing.
* **Recommendation:** **DEFER (RETAIN BACKEND, DO NOT BUILD SHARE UI IN THE NEXT 14 DAYS)**.

---

## 3.2. Document & Library Management

### 5. Document Management (CRUD, Collections Tree, Tags, 22 Metadata Fields)
* **Status:** 100% complete (drag-and-drop, in-place edit, table sorting).
* **Recommendation:** **KEEP NOW (FREEZE AS-IS)**.

### 6. PDF Physical File Upload & Validation
* **Status:** Complete with `%PDF-` magic byte inspection, 50MB limit, Django media storage.
* **Recommendation:** **KEEP NOW**.

### 7. Automated DOI Metadata Extraction (Crossref)
* **Status:** Complete with live preview modal (`DoiModal`).
* **Recommendation:** **KEEP NOW**.

### 8. arXiv and ISBN (OpenLibrary) Metadata Fetching
* **Status:** Toolbar buttons disabled. Crossref sufficiently proves automated metadata retrieval.
* **Recommendation:** **DEFER (LEAVE BUTTONS DISABLED)**.

### 9. Multi-Format Uploads (.docx, .epub, .xlsx - BACKLOG-1)
* **Status:** Queued in backlog.
* **Risk:** Severe distraction requiring multiple document parsers (`python-docx`, epub readers), breaking PDF.js canvas consistency.
* **Recommendation:** **REMOVE / DROP**. Focus 100% on scientific PDF documents.

### 10. PDF.js Viewer & In-Canvas Annotation System
* **Status:** 100% complete (TextLayer highlighting, draggable sticky notes, context menus).
* **Recommendation:** **KEEP NOW (FREEZE CODE)**.

---

## 3.3. Citations & Writing Features

### 11. Multi-Format Citation Generator (IEEE, APA, Harvard, BibTeX, RIS - BACKLOG-4)
* **Status:** Unimplemented.
* **Recommendation:** **DEFER**.

### 12. Integrated Rich Text / Markdown Writing Editor
* **Status:** Unimplemented.
* **Risk:** Textbook scope creep converting a research viewer into a subpar Overleaf clone.
* **Recommendation:** **REMOVE / DROP PERMANENTLY**.

### 13. Auto-Insert Citations While Writing
* **Recommendation:** **REMOVE / DROP PERMANENTLY**.

---

## 3.4. External Web & Metadata Scraping

### 14. Web Connector Extension (Zotero Browser Plugin Clone)
* **Recommendation:** **DEFER**.

### 15. AI Agent for Missing Metadata Discrepancy Reconciliation
* **Recommendation:** **REMOVE / DROP**. Users can directly edit 22 metadata fields on the UI.

### 16. Web Search Agent (Live Internet Search inside Chat)
* **Risk:** Distorts thesis scope. The objective is RAG **over the user's uploaded scientific document collection**, not general web search.
* **Recommendation:** **REMOVE / DROP**.

---

## 3.5. Architecture & Infrastructure

### 17. Independent FastAPI Microservice Container
* **Status:** Specified in initial Week 1 docs; zero code implemented.
* **Evaluation:** Running two backend servers introduces cross-origin CORS issues, dual JWT authentication, and network failure points during live evaluation.
* **Recommendation:** **SIMPLIFY RADICALLY:** Embed RAG pipeline directly into Django (`backend/apps/documents/services/rag_service.py`), leveraging shared virtual environments, ORM models, and local disk paths.

### 18. Message Brokers & gRPC (RabbitMQ, Kafka, Celery + Redis)
* **Evaluation:** Unnecessary architectural overengineering for a single-user evaluation workstation.
* **Recommendation:** **REMOVE / DROP**. Use synchronous indexing or standard Python `threading.Thread`.

### 19. Dedicated Qdrant Server Container (Docker)
* **Evaluation:** Running Docker on Windows during a live academic presentation creates networking and resource risks.
* **Recommendation:** **SIMPLIFY:** Use **Qdrant Embedded** via `qdrant-client` path storage (`QdrantClient(path="media/qdrant_db")`). Zero network ports, zero Docker overhead, fully persistent on disk.

### 20. CI/CD & Kubernetes Deployment
* **Recommendation:** **DEFER**. `scripts/start-all.mjs` executes PostgreSQL, Django, and Vite seamlessly with `npm start`.

---

## 3.6. Core RAG & AI Pipeline (SOLE FOCUS OF NEXT 14 DAYS)

### 21. Layout-Aware PDF Text Extraction
* **Recommendation:** **KEEP NOW**. Use **`PyMuPDF` (`fitz`)** with coordinate-based block ordering (`sort=True`) to maintain natural academic two-column reading order.

### 22. Text Chunking Strategy
* **Recommendation:** **KEEP NOW**. Implement `RecursiveCharacterTextSplitter` (chunk size: 900, overlap: 150).

### 23. Dense Embeddings & Vector Storage
* **Recommendation:** **KEEP NOW**. Use `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors, lightweight CPU inference) stored in local `Qdrant Embedded`.

### 24. Scoped Vector Retrieval
* **Recommendation:** **KEEP NOW**. Filter retrieval strictly by active document: `filter={"must": [{"key": "doc_id", "match": {"value": active_doc_id}}]}` returning Top-4 chunks with page metadata.

### 25. Document Q&A AI Assistant
* **Recommendation:** **KEEP NOW**. Deliver a slide-out `<AiChatPanel>` beside the PDF viewer: User asks question $\rightarrow$ context retrieved $\rightarrow$ local Ollama (`llama3.2:3b`) generates answer with `[Page X]` citations.

### 26. 1-Click Paper Summarization
* **Recommendation:** **KEEP NOW**. Deliver a one-click button generating a structured 3-part summary (Objective, Methodology, Key Findings).

### 27. Multi-Paper Literature Review Synthesis
* **Recommendation:** **DEFER**.

---

## 3.7. Empirical Research & Evaluation

### 28. Midterm RAG Evaluation Benchmark
* **Thesis Requirement:** The thesis specification explicitly mandates "Evaluation of RAG methods." Presenting only a UI without benchmark metrics will invite criticism from the academic committee.
* **Recommendation:** **KEEP BUT SIMPLIFY**:
  - Curate 15 ground-truth questions across 3 representative scientific papers.
  - Run quantitative comparison: Measure **Latency (seconds)** and **Retrieval Hit Rate @ 3 (%)** between Chunk Size 500 vs Chunk Size 1000.
  - Package findings into a comparative results table.

---

# 4. Scope Allocation Matrix

| Feature | Current Status | Thesis Relevance | Demo Value | Complexity | Decision | Technical Rationale |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **PDF Extraction (`PyMuPDF` sort=True)** | Unimplemented | Critical | Mandatory | Low | **KEEP NOW** | Preserves academic multi-column reading order |
| **Text Chunking (RecursiveSplitter)** | Unimplemented | Critical | Mandatory | Low | **KEEP NOW** | Creates grounded context for LLM |
| **Dense Embeddings & Vector DB** | Unimplemented | Critical | Mandatory | Medium | **KEEP NOW** | Core of RAG architecture (`all-MiniLM-L6-v2` + Qdrant) |
| **Document Q&A AI Assistant** | Unimplemented | Critical | Mandatory | Medium | **KEEP NOW** | Core deliverable fulfilling registered project title |
| **1-Click Paper Summarization** | Unimplemented | High | High | Low | **KEEP NOW** | High demonstration impact for academic committee |
| **Interactive [Page X] Citations** | Unimplemented | High | High | Low | **KEEP NOW** | Visual proof that responses originate from retrieved context |
| **Midterm Evaluation Benchmark** | Unimplemented | Mandatory | High | Low | **SIMPLIFY** | 15-question benchmark across 3 sample papers |
| **Document CRUD & 22 Metadata** | 100% Complete | Core | High | Complete | **KEEP NOW** | Retain intact; provides document library base |
| **DOI Lookup (Crossref)** | 100% Complete | High | High | Complete | **KEEP NOW** | Demonstrates automated data entry |
| **PDF.js Viewer & Annotations** | 100% Complete | High | High | Complete | **KEEP NOW** | Commercial-grade reading interface |
| **FastAPI Microservice for RAG** | Documented only | Secondary | Negative | Very High | **SIMPLIFY** | Embed into Django to eliminate multi-service networking failures |
| **Qdrant Vector Server (Docker)** | Unimplemented | Medium | Low | High | **SIMPLIFY** | Use local file-based Qdrant Embedded (`media/qdrant_db/`) |
| **Google Drive Sharing UI** | Backend complete | Secondary | Low | Medium | **DEFER** | Avoid wasting time on sharing modal when demoing single-user flow |
| **Profile Page / Avatar PFP** | Unimplemented | Irrelevant | Zero | Low | **DEFER** | Complete scope creep |
| **Arbitrary Uploads (.docx, .xlsx)**| Unimplemented | Very Low | Zero | Medium | **REMOVE** | Academic research focuses on PDF format |
| **BibTeX / RIS Citation Export** | Unimplemented | Medium | Low | High | **DEFER** | Postpone to final thesis phase |
| **Rich Text / Markdown Editor** | Conceptual | Irrelevant | Zero | Very High | **REMOVE** | Eliminates risk of turning viewer into a document editor |
| **Web Search Agent (Google/Bing)** | Unimplemented | Off-target | Low | Very High | **REMOVE** | Thesis requires RAG over the user's library, not web scraping |
| **Literature Review Synthesis** | Conceptual | High | Low | Very High | **DEFER** | Multi-hop reasoning too complex for 2-week window |
| **Docker Compose / Cloud Deploy** | Unimplemented | Very Low | Zero | High | **DEFER** | Local execution via `npm start` is 100% reliable |

---

# 5. Midterm Minimum Viable Product (MVP) & Demo Script

## 5.1. Midterm MVP Feature Boundary

The deliverables for the Midterm Evaluation comprise:
1. **User Authentication:** Single-user researcher login via active JWT credentials.
2. **Scientific Library Management:**
   - Document table displaying title, authors, publication date, and metadata fields.
   - 1-Click DOI import auto-fetching metadata via Crossref.
   - Physical PDF upload with magic byte integrity validation.
   - Hierarchical collection folders and tag classification.
3. **Reading & Annotation:**
   - High-fidelity PDF.js reading canvas.
   - Text selection highlighting and draggable sticky notes.
4. **AI Research Assistant (Embedded RAG):**
   - Automated layout-aware extraction, chunking, and embedding on PDF upload.
   - Slide-out `<AiChatPanel>` beside the active PDF reader.
   - Grounded Q&A answering methodology, findings, and dataset inquiries.
   - Transparent citations with clickable `[Page X]` navigation badges.
   - 1-Click structured summarization.
5. **Empirical Evaluation Data:**
   - Quantitative table measuring retrieval hit rate and latency across chunk sizes.

---

## 5.2. Live Demo Script (7 - 10 Minutes)

```text
STEP 1: Authentication & Workspace Overview
  • Log in to the system.
  • Display the 3-column workspace: Collections tree on the left, scientific papers in the center, 
    and 22 metadata fields in the right panel.

STEP 2: Automated Ingestion via DOI & PDF Upload
  • Click "+ Add from DOI" and input a well-known paper (e.g., Attention Is All You Need: 10.48550/arXiv.1706.03762).
  • Verify instant auto-population of Title, Authors (Vaswani et al.), Year, and Journal.
  • Upload the PDF. System updates status to "Indexed" in local Qdrant.

STEP 3: Academic Reading & In-Canvas Annotation
  • Double-click the paper to open the PDF viewer tab.
  • Highlight a conclusion passage in yellow and attach a sticky note on the canvas.

STEP 4: Capstone Highlight — Grounded RAG Assistant
  • Open the "AI Assistant" slide-out panel next to the PDF canvas.
  • Submit an academic query: "What limitation of RNNs does the Multi-Head Attention mechanism resolve?"
  • AI generates a precise response synthesized from extracted paper chunks.
  • The response cites [Page 3, Paragraph 2]. Clicking the badge scrolls the PDF viewer directly to Page 3!

STEP 5: 1-Click Paper Summarization
  • Click "Summarize Document".
  • AI delivers a 3-part structured breakdown: Problem Statement, Proposed Architecture, and Experimental Results.

STEP 6: Technical Evaluation Benchmark Presentation
  • Present the empirical evaluation slide: Comparative table demonstrating Chunk Size 500 vs 1000 on 
    Retrieval Hit Rate @ 3 and inference latency.
```

---

# 6. Architectural Overengineering Audit (Direct Answers)

1. **Are microservices being used where a modular monolith suffices?**  
   * **Answer:** YES. Initial documentation proposed a separate FastAPI microservice. Consolidating into a **Modular Monolith** (Django managing both REST endpoints and RAG services in-process) is 5x faster to implement and eliminates cross-service networking bugs.
2. **Are gRPC or message brokers truly necessary?**  
   * **Answer:** NO. Synchronous execution or Python standard `threading.Thread` is completely adequate for a single-user evaluation workstation.
3. **Is infrastructure being built before validating the RAG loop?**  
   * **Answer:** YES. 15 relational tables, SQL indexes, and 19 tests were completed, but the RAG loop had zero lines of operational code. This audit permanently re-balances priorities.
4. **Are abstract layers introducing drag without demo utility?**  
   * **Answer:** The asynchronous webhook dispatcher (`webhook_service.py`) introduced needless complexity. Replacing it with direct in-process service invocations simplifies execution.
5. **Can external services be simplified?**  
   * **Answer:** Dedicated Dockerized Qdrant containers are replaced with **Qdrant Embedded** (`media/qdrant_db/`), running in-process via `qdrant-client` path storage.
6. **Can the system be demonstrated with 1 backend and 1 database?**  
   * **Answer:** ABSOLUTELY. The demo topology is: **1 Django Backend (Port 8000) + 1 PostgreSQL Database (Port 5432) + 1 Embedded Vector Store + 1 React Frontend (Port 5173)**.
7. **Which architectural decisions should be preserved?**  
   * **Answer:** Retain the 15-table PostgreSQL schema, the 22 metadata fields, SimpleJWT authentication, and the React 3-column + PDF.js canvas viewer.
8. **Which decisions are safely deferred?**  
   * **Answer:** Microservice decomposition, Docker Compose clusters, arbitrary file format parsers, collaborative sharing UI, and web search agents.

---

# 7. 14-Day Sprint Schedule

```text
WEEK 1: RAG PIPELINE IMPLEMENTATION & SYSTEM INTEGRATION
├── Days 1 - 2: Core RAG Services in Backend:
│               • Implement `apps/documents/services/rag_service.py`
│               • PyMuPDF text extraction (`sort=True`) + RecursiveCharacterTextSplitter (900/150)
│               • all-MiniLM-L6-v2 dense embeddings + Qdrant Embedded indexing
├── Days 3 - 4: Django REST API Actions:
│               • `POST /api/v1/documents/{id}/chat/` (Scoped retrieval + Ollama llama3.2:3b)
│               • `POST /api/v1/documents/{id}/summarize/` (1-Click summary action)
│               • `POST /api/v1/documents/{id}/reindex/` (Manual re-indexing)
├── Days 5 - 6: Frontend AI Assistant Interface:
│               • Implement `<AiChatPanel>` slide-out panel adjacent to `<PdfViewer>`
│               • Render chat bubbles, loading skeletons, and interactive `[Page X]` source badges
├── Day 7:      Automated Pipeline Integration:
│               • Auto-trigger vector indexing on document PDF upload; update `rag_status` to 'INDEXED'

WEEK 2: EMPIRICAL BENCHMARK, DRY RUN & FINAL REHEARSAL
├── Days 8 - 9:   Execute Empirical RAG Benchmark:
│                 • Evaluate 15 questions across 3 representative papers
│                 • Measure Retrieval Hit Rate @ 3 and Latency comparing chunk sizes 500 vs 1000
├── Days 10 - 11: End-to-End System Polish:
│                 • Populate library with 3 - 5 compelling sample research papers
│                 • Verify error states, offline fallbacks, and toast notifications
├── Day 12:       Prepare Midterm Presentation Slides & Architecture Summary
├── Day 13:       End-to-End Dry Run:
│                 • Rehearse full demo script from login to citation navigation; verify zero network dependencies
├── Day 14:       MIDTERM LIVE DEMONSTRATION & DEFENSE
```

---

# 8. Operational Directives for Midterm Preparation

1. **What must the team start IMMEDIATELY?**  
   > Implement `rag_service.py` in the backend and `<AiChatPanel>` in the frontend. All non-RAG development is halted.
2. **What must remain FROZEN as-is?**  
   > Freeze the library workspace, 22 metadata fields, 3-column layout, and PDF.js annotation tools. Do not alter working CSS or add new buttons.
3. **What is DEFERRED to the final thesis?**  
   > Google Drive sharing dialog, BibTeX/RIS parsers, user profile avatar editor, and arXiv/ISBN integrations.
4. **What is DROPPED permanently?**  
   > Multi-format uploads (`.docx`, `.xlsx`), integrated rich-text editor, web search agents, and separate microservice containers.
5. **What is the minimum convincing demo?**  
   > **Log in $\rightarrow$ View paper library $\rightarrow$ Import paper via DOI $\rightarrow$ Open PDF viewer $\rightarrow$ Open AI Chat panel $\rightarrow$ Submit technical query $\rightarrow$ Receive accurate answer citing `[Page X]` $\rightarrow$ Click badge to navigate directly to page.**
