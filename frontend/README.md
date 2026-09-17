# Frontend — Scientific Document Manager

Giao diện người dùng cho ứng dụng Quản lý Tài liệu Khoa học (lấy cảm hứng từ Zotero), được xây dựng bằng **React.js + TypeScript + Vite**.

Ứng dụng kết nối với:
- **Backend API (Django REST Framework)**: Quản lý nghiệp vụ, metadata, DOI, lưu trữ tệp tin.
- **RAG Pipeline (FastAPI + LangChain)**: Chat AI, truy vấn ngữ nghĩa tài liệu qua Qdrant Vector DB.

---

## Công nghệ sử dụng trong Frontend

- **Framework**: React 19 + TypeScript
- **Bundler**: Vite
- **Styling**: CSS Modules + Global CSS Tokens (Không dùng Tailwind CSS)
- **PDF Viewer & Annotation**: PDF.js / pdfAnnotate
- **Icons**: `react-icons`

---

## Cấu trúc thư mục

```text
frontend/src/
├── components/
│   ├── TabBar/           # Browser-style tab navigation (Ctrl/Cmd + 1..9)
│   ├── LeftSidebar/      # Library, Collections, Tags with resizer & tooltips
│   ├── MainToolbar/      # Search bar (Ctrl/Cmd + F), Add document, View controls
│   ├── DocumentTable/    # Sortable document list with status indicators
│   ├── MetadataPanel/    # Resizable right sidebar with in-place field editing
│   ├── PdfViewer/        # Integrated PDF viewer with annotation support
│   └── common/           # Reusable components (Tooltip, Resizer, Dropdown, Modal)
├── types/                # Core TypeScript interfaces (Document, Collection, Tag, Tab)
├── data/                 # Mock datasets and initial state
├── App.tsx               # Root component & keyboard shortcuts handler
└── index.css             # Theme variables & CSS reset
```

---

## Hướng dẫn cài đặt & Khởi chạy

```bash
# Cài đặt dependencies
npm install

# Khởi chạy development server
npm run dev

# Kiểm tra lint
npm run lint

# Build production bundle
npm run build
```

Xem tài liệu kiến trúc toàn diện tại [README.md](../README.md) và [ARCHITECTURE.md](../ARCHITECTURE.md).
