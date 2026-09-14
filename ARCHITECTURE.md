# Tài Liệu Thiết Kế Kiến Trúc Hệ Thống (Architecture Design Document)

## 1. Tổng quan kiến trúc hệ thống

Hệ thống quản lý tài liệu khoa học được tổ chức theo mô hình kiến trúc phân tán hướng dịch vụ (Service-Oriented Architecture), chia làm **3 thành phần chính**:

```
+-------------------------------------------------------------+
|               Frontend (React.js + TypeScript)              |
|   - Quản lý tài liệu & Thư viện (Zotero-style UI)           |
|   - Trình đọc & chú thích PDF (PDF.js / pdfAnnotate)        |
|   - Ghi chú, tags, quản lý metadata                         |
|   - Giao diện trò chuyện tương tác với AI                   |
+------------------------------+------------------------------+
                               |
               +---------------+---------------+
               | HTTP / REST                   | HTTP / Stream
               v                               v
+-------------------------------+  +--------------------------+
|  Backend API (Django REST)    |  | RAG Pipeline (FastAPI)   |
|  - Nghiệp vụ & Xác thực       |  | - Microservice riêng     |
|  - CRUD Tài liệu, Tag, Ghi chú|  | - Chunking & Embedding   |
|  - Tích hợp DOI (Crossref)    |  | - LangChain RAG Chains   |
|  - Upload / Download tệp      |  | - Truy xuất vector & LLM |
+---------------+---------------+  +------------+-------------+
                |                               |
                | ORM                           | Vector Search
                v                               v
+-------------------------------+  +--------------------------+
|  PostgreSQL Database          |  |  Vector DB (Qdrant)      |
|  - Metadata & Tài liệu        |  |  - Document Chunk Vectors|
|  - Users, Collections, Tags   |  |  - Semantic Search Index |
+-------------------------------+  +--------------------------+
```

---

## 2. Công nghệ chi tiết

### 2.1. Website quản lý tài liệu

| Thành phần | Công nghệ / Thư viện | Lý do lựa chọn & Vai trò |
| :--- | :--- | :--- |
| **Backend API** | **Django REST Framework (Python)** | Framework quen thuộc, tốc độ phát triển nhanh, tích hợp sẵn hệ thống Admin trực quan, ORM mạnh mẽ, bảo mật cao và hỗ trợ đầy đủ Authentication/Authorization. |
| **Frontend** | **React.js + TypeScript** | Hệ sinh thái phong phú, linh hoạt, khả năng mở rộng cao (modular architecture), dễ dàng quản lý state phức tạp và tích hợp các thư viện đọc PDF/annotation. |
| **PDF Viewer & Annotation** | **PDF.js** hoặc **pdfAnnotate** | Giải pháp open-source chuẩn công nghiệp, hiển thị PDF chính xác trên trình duyệt và cho phép tạo ghi chú (notes), tô sáng (highlight), vẽ chú thích trực tiếp trên trang tài liệu. |
| **DOI Metadata Integration**| **Crossref REST API** / **DataCite API** | Tự động hóa trích xuất metadata (Tiêu đề, Tác giả, Tạp chí, Năm xuất bản, Tóm tắt) từ mã số DOI mà không cần khóa truy cập API (no API key required), tiết kiệm thời gian nhập liệu thủ công. |

### 2.2. RAG Pipeline (Retrieval-Augmented Generation)

| Thành phần | Công nghệ / Thư viện | Vai trò trong hệ thống |
| :--- | :--- | :--- |
| **Microservice Framework** | **FastAPI (Python)** | Xây dựng API phi đồng bộ (async), tốc độ phản hồi cực nhanh, hỗ trợ Server-Sent Events (SSE) / WebSockets cho phản hồi chat streaming thời gian thực. |
| **RAG Orchestration** | **LangChain** | Quản lý quy trình chunking tài liệu, kết nối Embedding models, xây dựng Retrieval QA chains và prompt engineering. |
| **Vector Database** | **Qdrant** | Lưu trữ vector embedding cho từng đoạn (chunk) của bài báo khoa học; hỗ trợ lọc metadata (payload filter theo `doc_id`, `collection_id`) kết hợp tìm kiếm ngữ nghĩa tương đồng (cosine similarity). |

### 2.3. Cơ sở dữ liệu & Lưu trữ

1. **PostgreSQL**:
   - Lưu trữ thông tin tài khoản người dùng và phân quyền.
   - Quản lý cấu trúc phân cấp: thư viện (`Library`), bộ sưu tập (`Collections`), thư mục (`Folders`).
   - Quản lý metadata chi tiết của tài liệu (DOI, Title, Authors, Journal, Year, Abstract, URL, File Path).
   - Quản lý các nhãn (`Tags`), ghi chú (`Notes`) và các điểm highlight trên PDF.

2. **Qdrant (Vector Database)**:
   - Lưu trữ các vector đặc trưng kích thước lớn (ví dụ: OpenAI `text-embedding-3-small`, bge-m3, hoặc các mô hình mã nguồn mở khác).
   - Mỗi vector điểm (point) gắn kèm payload: `doc_id`, `chunk_index`, `page_number`, `text_content`.

---

## 3. Luồng dữ liệu chính (Core Data Flows)

### 3.1. Luồng tải lên tài liệu & Trích xuất Metadata qua DOI
1. Người dùng tải tệp PDF lên qua **Frontend**.
2. **Frontend** gửi tệp và mã DOI (nếu có) đến **Django Backend**.
3. Nếu có DOI (hoặc trích xuất được DOI từ PDF), **Backend** gọi **Crossref REST API** hoặc **DataCite API** để lấy thông tin metadata chuẩn xác.
4. **Backend** lưu tệp PDF vào storage, ghi nhận thông tin tài liệu vào **PostgreSQL**.
5. **Backend** phát tín hiệu / gọi nội bộ sang **RAG Pipeline (FastAPI)** để tiến hành lập chỉ mục (index).

### 3.2. Luồng Ingestion & Indexing cho RAG
1. **RAG Pipeline** nhận yêu cầu index một tài liệu (`document_id`, `file_path`).
2. Trích xuất text từ PDF và phân đoạn nội dung (**Chunking** sử dụng `RecursiveCharacterTextSplitter`).
3. Tạo vector nhúng (**Embeddings**) cho từng chunk.
4. Lưu toàn bộ vectors kèm payload metadata vào **Qdrant Vector Database**.

### 3.3. Luồng Trò chuyện & Hỏi đáp AI (Chat with Document)
1. Người dùng đặt câu hỏi trên giao diện **Frontend** (trong ngữ cảnh 1 tài liệu hoặc cả bộ sưu tập).
2. **Frontend** gửi yêu cầu chat đến **RAG Pipeline (FastAPI)**.
3. **RAG Pipeline** vector hóa câu hỏi của người dùng và thực hiện tìm kiếm tương đồng trên **Qdrant** (lọc theo phạm vi tài liệu).
4. Các đoạn trích dẫn liên quan nhất (relevant contexts) được đưa vào Prompt kết hợp cùng câu hỏi.
5. Mô hình ngôn ngữ (**LLM**) sinh câu trả lời và stream từng token về giao diện **Frontend**.
