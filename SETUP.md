# Setup & Installation Guide

This guide provides comprehensive instructions for installing, configuring, and running the **Scientific Document Manager** (Django REST Framework backend + React 19 frontend + Local RAG pipeline) on a new workstation.

---

## 1. Prerequisites

Before installing the project, ensure your workstation has the following prerequisites:

| Tool | Recommended Version | Download & Setup Notes |
| :--- | :--- | :--- |
| **Python** | `3.11.x` or `3.12.x` | [Download Python for Windows](https://www.python.org/downloads/windows/)<br>⚠️ **Mandatory:** Check the box **"Add python.exe to PATH"** during installation. |
| **Node.js** | `v18.x` or `v20.x LTS` (with `npm`) | [Download Node.js](https://nodejs.org/) to run and build the React frontend. |
| **PostgreSQL** | `16.x` | [Download PostgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) (includes `pgAdmin 4`) or run via Docker. |
| **Git** | Latest | [Download Git](https://git-scm.com/downloads) for version control. |
| **Ollama** | Latest | [Download Ollama](https://ollama.com/) to serve local LLMs (`llama3.2:3b`) on `http://localhost:11434`. |
| **Bruno** / **Postman** *(Optional)* | Latest | [Download Bruno](https://www.usebruno.com/downloads) to run the prebuilt API collection at `backend/bruno_collection`. |

---

## 2. Backend Setup (Django 5 REST Framework)

### Step 2.1: Create PostgreSQL Database
Open `pgAdmin 4` or your terminal `psql` shell and create a database:
```sql
CREATE DATABASE scientific_library_db;
```

### Step 2.2: Initialize Virtual Environment & Install Dependencies
Open a terminal in the root repository directory:
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create Python virtual environment
python -m venv venv

# 3. Activate virtual environment:
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# (If script execution is disabled, run: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate

# 4. Install backend dependencies (including PyMuPDF, LangChain, Qdrant)
pip install -r requirements.txt
```

### Step 2.3: Configure Environment Variables (`.env`)
Create your `.env` file from `.env.example`:
```bash
# On Windows (PowerShell):
Copy-Item .env.example .env

# On macOS / Linux:
cp .env.example .env
```

Open `backend/.env` and configure your credentials (especially PostgreSQL `DB_PASSWORD`):
```env
# Django Configuration
SECRET_KEY=django-insecure-scientific-doc-manager-secret-key-2026-prod-ready
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (PostgreSQL 16)
DB_NAME=scientific_library_db
DB_USER=postgres
DB_PASSWORD=your_actual_postgres_password
DB_HOST=localhost
DB_PORT=5432

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Local LLM & RAG Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
EMBEDDING_MODEL=all-MiniLM-L6-v2
QDRANT_STORAGE_PATH=media/qdrant_db
```

### Step 2.4: Execute Migrations & Create Superuser
```bash
# Apply database migrations (creates 15 relational tables)
python manage.py migrate

# (Optional) Create superuser for Django Admin
python manage.py createsuperuser
```

### Step 2.5: Verify & Run Backend Server
```bash
# Run automated test suites (19 tests)
python manage.py test apps.documents.tests apps.users.tests

# Start Django development server
python manage.py runserver
```
Backend API will be accessible at: **`http://127.0.0.1:8000/`**  
Django Admin dashboard: **`http://127.0.0.1:8000/admin/`**

---

## 3. Local AI Setup (Ollama & Model Download)

Ensure Ollama is running in the background:
```bash
# Pull the required lightweight model (Llama 3.2 3B)
ollama pull llama3.2:3b

# Verify Ollama server responds
curl http://localhost:11434/v1/models
```

---

## 4. Frontend Setup (React 19 + TypeScript + Vite)

Open a **new** terminal window:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Verify TypeScript build
npm run build

# 4. Start Vite development server
npm run dev
```

The Web UI will be live at: **`http://localhost:5173/`**

---

## 5. Running the Complete System (One Command)

From the project root:
```bash
npm start
```
This runs both Django backend and React Vite dev server concurrently via `scripts/start-all.mjs`.

---

## 6. IDE Configuration (VS Code & Antigravity IDE)

To ensure language servers, linters, and imports resolve cleanly:

1. **Always open the root directory (`DACNTT`)** in your editor.
2. The repository includes:
   - [`.vscode/settings.json`](file:///c:/DACNTT/.vscode/settings.json): Designates `backend` as an `extraPath` and automatically binds `backend/venv`.
   - [`pyrightconfig.json`](file:///c:/DACNTT/pyrightconfig.json): Configures root and backend search paths for Pyright/Pylance.
3. In VS Code, press `Ctrl + Shift + P` -> **"Python: Select Interpreter"** -> choose `backend/venv/Scripts/python.exe`.

---

## 7. Troubleshooting

### 1. `ModuleNotFoundError: No module named 'psycopg2'`
- **Cause:** PostgreSQL driver not installed or virtual environment not activated.
- **Resolution:** Activate `backend/venv` and run `pip install psycopg2-binary`.

### 2. `django.db.utils.OperationalError: connection to server at "localhost", port 5432 failed`
- **Cause:** PostgreSQL service not running or invalid credentials in `.env`.
- **Resolution:** Start the PostgreSQL service in Windows Services (`postgresql-x64-16`) and check `DB_PASSWORD` in `backend/.env`.

### 3. PowerShell execution policy error (`running scripts is disabled`)
- **Resolution:** Run PowerShell as Administrator or execute in the current session:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\Activate.ps1
  ```

### 4. Ollama connection refused (`Failed to connect to localhost:11434`)
- **Resolution:** Launch the Ollama desktop app or run `ollama serve` in a terminal.
