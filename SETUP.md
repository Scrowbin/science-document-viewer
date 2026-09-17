# Hướng Dẫn Cài Đặt và Khởi Chạy Dự Án (Setup & Installation Guide)

Tài liệu này hướng dẫn chi tiết cách cài đặt và chạy toàn bộ hệ thống **Scientific Document Manager** (bao gồm cả Backend Django REST Framework và Frontend React) khi bạn clone/pull mã nguồn từ GitHub về máy mới.

---

## 1. Yêu Cầu Phần Mềm Cần Cài Đặt Sẵn (Prerequisites)

Trước khi tiến hành cài đặt dự án, máy tính của bạn cần được cài đặt các công cụ sau:

| Công cụ | Phiên bản khuyến nghị | Ghi chú & Liên kết tải |
| :--- | :--- | :--- |
| **Python** | `3.11.x` hoặc `3.12.x` | [Tải Python cho Windows](https://www.python.org/downloads/windows/)<br>⚠️ **Bắt buộc:** Tích chọn ô **"Add python.exe to PATH"** trong quá trình cài đặt. |
| **Node.js** | `v18.x` hoặc `v20.x LTS` (kèm `npm`) | [Tải Node.js](https://nodejs.org/) để chạy và build Frontend React. |
| **PostgreSQL** | `16.x` | [Tải PostgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (đi kèm `pgAdmin 4`) hoặc chạy qua Docker. |
| **Git** | Bản mới nhất | [Tải Git](https://git-scm.com/downloads) để clone và quản lý mã nguồn. |
| **Bruno** hoặc **Postman** *(Tùy chọn)* | Mới nhất | [Tải Bruno](https://www.usebruno.com/downloads) để chạy test bộ sưu tập API có sẵn tại `backend/bruno_collection`. |
| **Docker Desktop** *(Tùy chọn)* | Mới nhất | [Tải Docker Desktop](https://www.docker.com/products/docker-desktop/) (khuyến nghị nếu muốn chạy PostgreSQL hoặc Qdrant Vector DB trong container). |

---

## 2. Hướng Dẫn Cài Đặt Backend (Django REST Framework)

### Bước 2.1: Tạo Cơ sở dữ liệu PostgreSQL
Mở `pgAdmin 4` hoặc terminal `psql`, tạo một cơ sở dữ liệu mới cho dự án:
```sql
CREATE DATABASE scientific_library_db;
```

### Bước 2.2: Khởi tạo Virtual Environment và Cài đặt Thư viện
Mở terminal (PowerShell hoặc CMD) tại thư mục gốc của dự án:
```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Tạo môi trường ảo Python
python -m venv venv

# 3. Kích hoạt môi trường ảo:
# Trên Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# (Nếu gặp lỗi Execution Policy trên PowerShell, chạy: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
# Hoặc trên Windows (CMD):
.\venv\Scripts\activate.bat
# Trên macOS / Linux:
source venv/bin/activate

# 4. Cài đặt các phụ thuộc từ requirements.txt
pip install -r requirements.txt
```

### Bước 2.3: Thiết lập biến môi trường `.env`
Do file `.env` chứa thông tin nhạy cảm và được chặn bởi `.gitignore`, bạn cần tạo file `.env` từ file mẫu `.env.example`:
```bash
# Trên Windows (PowerShell):
Copy-Item .env.example .env

# Trên macOS / Linux:
cp .env.example .env
```
Mở file `backend/.env` và cập nhật các thông số cho phù hợp với máy của bạn (đặc biệt là mật khẩu `DB_PASSWORD` của PostgreSQL):
```env
# Django Configuration
SECRET_KEY=django-insecure-scientific-doc-manager-secret-key-2026-prod-ready
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL 16)
DB_NAME=scientific_library_db
DB_USER=postgres
DB_PASSWORD=mật_khẩu_postgres_của_bạn
DB_HOST=localhost
DB_PORT=5432

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# RAG Service Webhook URL
RAG_WEBHOOK_URL=http://localhost:8001/webhook/rag/ingest
```

### Bước 2.4: Thực thi Migrations & Tạo Superuser
```bash
# Áp dụng các migration tạo 15 bảng cơ sở dữ liệu
python manage.py migrate

# (Tùy chọn) Tạo tài khoản quản trị Admin
python manage.py createsuperuser
```

### Bước 2.5: Kiểm tra và Khởi chạy Backend Server
```bash
# Chạy bộ kiểm thử tự động (6 tests)
python manage.py test apps.documents.tests

# Khởi động máy chủ backend
python manage.py runserver
```
Backend API sẽ hoạt động tại: **`http://127.0.0.1:8000/`**  
Trang quản trị Django Admin: **`http://127.0.0.1:8000/admin/`**

---

## 3. Hướng Dẫn Cài Đặt Frontend (React + TypeScript + Vite)

Mở một cửa sổ terminal **mới**:

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt các gói phụ thuộc (node_modules)
npm install

# 3. Khởi chạy máy chủ phát triển (Dev Server)
npm run dev
```

Giao diện Web sẽ hoạt động tại: **`http://localhost:5173/`**

---

## 4. Cấu Hình Trình Soạn Thảo / IDE (VS Code & Antigravity IDE)

Để đảm bảo Language Server và Linter phân giải đường dẫn chính xác (không bị báo lỗi giả *`Cannot find module apps...`*):

1. **Luôn mở thư mục gốc của repository (`DACNTT`)** trong IDE thay vì mở riêng lẻ thư mục con.
2. Dự án đã được thiết lập sẵn các file cấu hình sau trong mã nguồn:
   - [`.vscode/settings.json`](file:///c:/DACNTT/.vscode/settings.json): Khai báo `backend` là `extraPaths` và tự động chọn Python Virtual Environment tại `backend/venv`.
   - [`pyrightconfig.json`](file:///c:/DACNTT/pyrightconfig.json): Khai báo `backend` cho Pyright / Pylance.
3. Trong VS Code, bạn chỉ cần nhấn `Ctrl + Shift + P` -> chọn **"Python: Select Interpreter"** -> chọn Python trong `backend/venv/Scripts/python.exe`.

---

## 5. Xử Lý Các Sự Cố Thường Gặp (Troubleshooting)

### 1. Lỗi `ModuleNotFoundError: No module named 'psycopg2'`
- **Nguyên nhân:** Chưa cài đặt thư viện kết nối PostgreSQL hoặc chưa kích hoạt môi trường ảo.
- **Khắc phục:** Đảm bảo đã chạy `.\venv\Scripts\activate` và chạy lệnh:
  ```bash
  pip install psycopg2-binary
  ```

### 2. Lỗi `django.db.utils.OperationalError: connection to server at "localhost", port 5432 failed`
- **Nguyên nhân:** Dịch vụ PostgreSQL chưa được bật hoặc thông tin đăng nhập trong file `backend/.env` không chính xác.
- **Khắc phục:** 
  - Mở `Services` (trên Windows) tìm `postgresql-x64-16` và chọn **Start**.
  - Kiểm tra lại `DB_USER` và `DB_PASSWORD` trong file `backend/.env`.

### 3. Lỗi PowerShell không cho kích hoạt venv (`running scripts is disabled on this system`)
- **Khắc phục:** Mở PowerShell với quyền Administrator hoặc chạy lệnh sau trong phiên làm việc hiện tại:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\Activate.ps1
  ```

### 4. Lỗi import `Cannot find module apps.documents.models` trong editor
- **Khắc phục:** Đảm bảo thư mục mở trong IDE là thư mục gốc của repo (`DACNTT`) để file `.vscode/settings.json` và `pyrightconfig.json` có hiệu lực.
