# Frontend — Scientific Document Manager

User interface for the Scientific Document Management application (inspired by Zotero), built with **React 19 + TypeScript + Vite**.

The application connects to:
- **Backend API (Django 5 REST Framework)**: Business logic, metadata management, DOI lookup, PDF file storage, and relational library management.
- **Embedded RAG Pipeline**: Local semantic search, in-document Q&A with page grounding badges (`[Page X]`), and 1-click summarization via local vector database (Qdrant Embedded) and local LLM (Ollama `llama3.2:3b`).

---

## Frontend Tech Stack

- **Framework**: React 19 + TypeScript
- **Bundler**: Vite
- **Styling**: CSS Modules + Global CSS Variables & Design Tokens (Tailwind CSS strictly prohibited)
- **PDF Viewer & Annotation**: PDF.js (Canvas rendering, TextLayer, Smooth Zoom, Highlighting, Draggable Sticky Notes)
- **Icons**: `react-icons` (FontAwesome / Lucide icons)
- **HTTP Client**: Axios with automatic JWT interceptors and 401 token refresh queue

---

## Directory Structure

```text
frontend/src/
├── api/                         # Typed Axios client & REST services
│   ├── client.ts                # Axios instance with JWT interceptors & token refresh
│   ├── authApi.ts               # Login, register, me endpoints
│   ├── documentsApi.ts          # Document CRUD, PDF multipart upload, DOI lookup
│   ├── annotationsApi.ts        # In-canvas annotations REST integration
│   ├── collectionsApi.ts        # Collections tree CRUD
│   └── index.ts                 # Central API exports
├── components/
│   ├── TabBar/                  # Browser-style tab navigation (Ctrl/Cmd + 1..9)
│   ├── LeftSidebar/             # Library tree, Collections, Tags with resizer & tooltips
│   ├── MainToolbar/             # Search bar (Ctrl/Cmd + F), Add document dropdown
│   ├── DocumentTable/           # Sortable document table with active column indicators
│   ├── MetadataPanel/           # Resizable right sidebar with in-place editing of 22 fields
│   ├── PdfViewer/               # Integrated PDF.js canvas viewer, TextLayer, In-canvas notes
│   ├── AiChatPanel/             # Slide-out AI assistant: Q&A, 1-Click summary, [Page X] navigation
│   ├── DoiModal/                # DOI lookup & metadata preview modal
│   ├── UserMenu/                # User avatar dropdown & API status indicator
│   └── common/                  # Reusable Tooltip, Resizer, Dropdown, Modal components
├── context/                     # React Contexts (AuthContext.tsx with JWT session)
├── hooks/                       # Custom hooks (useKeyboardShortcuts, useDocuments, useCollections, useDoiModal)
├── utils/                       # Pure utility functions (documentFilters, pdfGenerator)
├── types/index.ts               # Core shared TypeScript interfaces
├── constants/metadataConfig.ts  # Data-driven configuration for 22 metadata fields
├── data/                        # Mock data & sample PDF binary fallback
├── App.tsx                      # Root shell & keyboard shortcuts coordinator
├── App.module.css               # Main 3-column layout grid
└── index.css                    # Design tokens (colors, fonts, light/dark themes)
```

---

## Installation & Development

```bash
# Install dependencies
npm install

# Start Vite development server
npm run dev

# Run TypeScript & ESLint check
npm run lint

# Build production bundle
npm run build
```

See comprehensive architecture documentation at [README.md](../README.md) and [ARCHITECTURE.md](../ARCHITECTURE.md).
