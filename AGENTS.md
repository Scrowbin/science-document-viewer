# AGENTS.md — Instructions for AI agents

Guide for AI agents working on the **Scientific Document Manager** (a Zotero-style reference manager with a local RAG assistant). This is an undergraduate graduation project; keep the work at that scope.

## Agent directives
1. Check the real state first: read the files you will touch, and run the checks relevant
   to what you changed (e.g. backend tests for backend code, `npm run build` for frontend code).
2. Keep this file short and generic. Record finished work in a short "Current status"
   section (no result numbers); history lives in git, results in `eval/README.md`.
3. Monorepo layout: `backend/` (Django 5 + DRF), `frontend/` (React 19 + TS + Vite, CSS Modules,
   no Tailwind), `eval/` (experiments), `archive/` (superseded material, not used by active code).
4. Keep the production application unchanged unless a specific bug requires a fix.
5. Prioritise finishing experiments, explaining findings and the thesis over repository tidiness.

## Evaluation methodology (undergraduate scope)
1. Prefer simple, deterministic procedures. Preserve experiment scripts, settings and raw
   per-query results so each result can be reproduced.
2. Evaluate one component at a time with the others at the documented baseline (the
   production setting, listed in `eval/README.md`); then compare the selected methods together
   in the final combination experiment (two methods for each of four components, 16 pipelines).
3. Report descriptive evaluation results: metric means, differences between methods, and
   computational costs (latency, throughput, memory).
4. Choose methods using results, cost and theory together; for each component write what
   theory predicted, what the experiment showed, and a supported explanation if they differ.
   If something cannot be explained, say so.
5. Name each result's dataset and setup; do not present results from different setups as
   directly comparable; do not call reused data an independent test; do not report anything
   as done that was not run. Token F1 is not factual correctness; the containment proxy and
   CEC are not semantic faithfulness.
6. Investigate surprising results when they could indicate a bug or change a conclusion;
   do not rerun experiments only because a result is unexpected. Substantial reruns, dataset
   reductions or setting changes need the user's approval and must be documented.
7. Name experiments, files and variables after the pipeline component, not numbered research
   questions.
8. Embedding models must get their required prefixes (`MODEL_PREFIX_SPECS` in `rag_service.py`)
   in both production and evaluation.
9. `eval/README.md` is the single methodology and results document.

---

## 1. System architecture

```
Client (frontend/)    React 19 + TypeScript + Vite
                      Zotero 3-column layout (LeftSidebar, DocumentTable, MetadataPanel),
                      PDF.js viewer with annotations, AI assistant panel (Q&A, summary,
                      page citations), browser-style tabs, keyboard shortcuts
        |  REST / JWT
        v
Backend (backend/)    Django 5 + DRF + SimpleJWT, PostgreSQL 16
                      Service layer in apps/documents/services/ (Crossref DOI, RAG)
                      Drive-style sharing (owner, VIEW, COMMENT, EDIT)
                      PDF files in media/documents/ (magic-byte checked)
        |  in-process call
        v
RAG pipeline          PyMuPDF layout-aware section extraction -> hierarchical (small-to-big)
(apps/documents/)     chunking -> intfloat/e5-small-v2 embeddings (with prefixes) ->
                      embedded Qdrant (child vectors + vectorless parent collection) ->
                      dense retrieval by default (RAG_RETRIEVAL_MODE=dense; rrf_legacy optional)
                      -> parent expansion within a token budget -> Ollama llama3.2:3b
```

Production settings live in `backend/core/settings.py` and `backend/.env` (see `SETUP.md`).

---

## 2. Frontend rules (`frontend/`)

### 2.1 Stack and hard constraints
* React 19 function components + TypeScript, bundled with Vite.
* Styling: **CSS Modules** (`*.module.css`) plus the design tokens in `index.css`.
* 🚫 **Do not use Tailwind CSS.**
* Icons: `react-icons`.
* State: React state and custom hooks; no Redux.

### 2.2 Structure
```text
frontend/src/
├── api/              # Typed Axios client (JWT interceptors, token refresh) and REST services
├── context/          # AuthContext
├── types/index.ts    # Shared TypeScript interfaces
├── constants/        # metadataConfig.ts (data-driven metadata fields)
├── hooks/            # useKeyboardShortcuts, useDocuments, useDocumentSelection, useCollections,
│                     # useChatSession, useRagStatusPolling, useDoiModal, useAuth, useTagTooltip
├── utils/            # documentFilters, collections, citationGeometry, format
├── components/       # TabBar, LeftSidebar, MainToolbar, DocumentTable, MetadataPanel, PdfViewer,
│                     # AiChatPanel, BulkActions, UploadModal, DoiModal, ChunkInspectorModal,
│                     # CreateCollectionModal, UserMenu, common/
├── pages/HomePage/   # Orchestration only
├── App.tsx, App.module.css, index.css
```

### 2.3 Behaviours to preserve
1. Zotero 3-column layout: collapsible left sidebar (library items, collections tree, tags),
   center toolbar + document table, resizable right metadata panel (min 320px).
2. Data-driven metadata: render fields from `metadataConfig.ts`; never hardcode rows.
3. Keyboard shortcuts centralised in `useKeyboardShortcuts.ts` (`Ctrl/Cmd+1..9` tabs,
   `Ctrl/Cmd+F` search, `Delete` delete selection); never fire while editing text inputs.
4. Table sorting via one generic `SortState` (first click ascending, second descending).

---

## 3. Backend rules (`backend/`)

### 3.1 Stack
Django 5 + DRF + `djangorestframework-simplejwt`, PostgreSQL 16 (`psycopg2-binary`),
Python 3.11/3.12 in `backend/venv`, configuration in `backend/.env` (`python-dotenv`).

### 3.2 Structure
```text
backend/
├── core/                 # settings, urls, wsgi/asgi
├── apps/
│   ├── users/            # custom User, JWT auth, logout blacklist
│   ├── collections_app/  # hierarchical collections and shares
│   └── documents/        # documents, metadata, annotations, notes, RAG
│       ├── services/     # crossref_service, rag_service, chunkers, query_processing, ...
│       ├── permissions.py
│       └── tests.py, tests_app.py
└── scripts/eval_common/  # shared evaluation code (metrics, pipeline, relevance)
```

### 3.3 Import convention
Inside an app (e.g. `apps/documents/`) use **relative imports** for sibling modules
(`from .models import Document`, `from ..collections_app.models import Collection`).
`from apps.documents...` inside the app confuses language servers. `.vscode/settings.json`,
`pyrightconfig.json` and `pyrefly.toml` add `backend`, `backend/scripts` and `eval` to the
search path; the root `.venv` junction points to `backend/venv`.

### 3.4 Database
Never edit tables by hand: change `models.py`, then `python manage.py makemigrations` and
`python manage.py migrate`.

---

## 4. Validation commands

```powershell
# backend/ (venv active)
python manage.py check
python manage.py test apps.documents.tests apps.documents.tests_app apps.users.tests

# frontend/
npm run lint
npm run build
```

Evaluation scripts live under `eval/phases/phase_<n>_<component>/scripts/`; shared code
under `backend/scripts/eval_common/` has unit tests runnable with `pytest`.

---

## 5. Current status
* Application: library management, PDF viewer with annotations, sharing, bulk actions and the
  RAG assistant are implemented. Serving PDFs behind permission checks (MinIO, presigned
  URLs) is planned after the evaluation work (`docs/design/FILE_STORAGE_PLAN.md`).
* Evaluation: component experiments for extraction, chunking, embedding, retrieval and
  generation are complete; the 16-configuration combination experiment is being prepared.
  See `eval/README.md`.
