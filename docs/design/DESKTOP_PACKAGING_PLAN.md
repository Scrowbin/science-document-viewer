# Desktop packaging plan: light installer, models downloaded on first run

**Goal.** A user downloads one Windows installer, runs it, and gets a desktop app ("Scientific Document Manager"). It needs no separate installs: no Python and no PostgreSQL. The installer stays small: the heavy parts (the LLM runtime and the models) are **downloaded once on first run** by a setup screen inside the app. After that one-time setup the app works offline.

**Status.** Planned. Today the app runs from source (`npm start`: Vite dev server, Django on :8000, a local PostgreSQL and a separately installed Ollama).

---

## 1. What ships in the installer and what is downloaded

| Part | Today | Packaged app |
|---|---|---|
| Window / UI | React app in a browser (Vite dev server) | **In installer.** A **Tauri 2** desktop window (WebView2) showing the built React app (`frontend/dist`) |
| Backend | `python manage.py runserver` from `backend/venv` | **In installer.** Django frozen with **PyInstaller** (one-folder build), started by the app as a background process ("sidecar") on a free localhost port |
| Database | PostgreSQL 16 server | **In installer.** A **SQLite** file in the user's data folder. The models use no PostgreSQL-only features (checked), so only `DATABASES` changes, via an env switch |
| PDF files, vector store | `backend/media/`, embedded Qdrant (`media/qdrant_db/`) | Same code, stored under `%APPDATA%\ScientificDocManager\` |
| LLM runtime | Ollama installed by the user | **Downloaded on first run.** If Ollama is already installed, the app uses it. Otherwise the setup screen downloads the official Ollama Windows build into the app's data folder and runs it as a sidecar on a private port |
| LLM weights | `ollama pull llama3.2:3b` by hand | **Downloaded on first run** through Ollama's own pull API (`/api/pull`, ~2 GB), with progress shown |
| Embedding model | `intfloat/e5-small-v2` downloaded by Sentence-Transformers on first use | **Downloaded on first run** (~130 MB) into the data folder. Afterwards `HF_HUB_OFFLINE=1`, so it never contacts the network again |
| Installer | – | Tauri's bundler builds an **NSIS `.exe` installer** (MSI optional) |

**Expected sizes:**
- **Installer:** about **1 GB**, mostly PyTorch CPU and the Python libraries in the frozen backend; the app itself is under 100 MB.
- **First-run download:** about **2.2 GB** (llama3.2:3b, e5, and the Ollama runtime if missing).

## 2. How it starts (runtime flow)

**First run:**
1. **Data folder.** The app creates `%APPDATA%\ScientificDocManager\`: SQLite database, `media/`, Qdrant data, `models/`, logs.
2. **Setup screen.** It checks what is missing and downloads it, with progress bars and the size of each item:
   - the Ollama runtime, unless already installed;
   - `llama3.2:3b` via Ollama;
   - the e5 embedding model.

   It needs an internet connection only this once. Downloads resume if interrupted, and the screen has a "Retry" button.
3. **Check.** It verifies each part (Ollama answers `/api/tags` and lists the model; the e5 folder loads) and records that setup is complete.

**Every run:**
1. Tauri shows a splash screen and starts the **Ollama sidecar** (or connects to an existing Ollama) and the **Django sidecar**. Django gets env vars for the data folder, port, `OLLAMA_BASE_URL`, `HF_HUB_OFFLINE=1` and `DEBUG=False`, runs `migrate`, then serves the API.
2. The window loads the React app, which calls the local Django port; the port is passed at runtime instead of the hard-coded `localhost:8000`.
3. On close, Tauri stops the sidecars it started.

Single-user desktop: on first run the app creates one local account and logs in automatically, so the login screen is skipped. Sharing features stay in the code but are hidden in desktop mode.

## 3. Work items

| # | Task | Notes | Effort |
|---|---|---|---|
| 1 | **Settings for desktop mode** | Env switch for SQLite, a data folder path, `DEBUG=False`, an allowed origin for the Tauri window, a port from env, a model folder from env | 0.5 day |
| 2 | **Frontend API URL at runtime** | Read the backend port from Tauri (or a `config.json`) instead of `VITE_API_URL`; build `frontend/dist` | 0.5 day |
| 3 | **Freeze Django with PyInstaller** | Collect hidden imports (Django apps, DRF, PyMuPDF, sentence-transformers, qdrant-client, rank-bm25); startup script runs `migrate` then `waitress`/`uvicorn` instead of `runserver` | 1.5–2 days (most of the risk is here) |
| 4 | **First-run setup screen** | Detect existing Ollama; download the Ollama runtime if missing; `ollama pull llama3.2:3b` with progress; download e5 into the data folder; resume and retry; mark setup done | 1–1.5 days |
| 5 | **Tauri shell** | `tauri init`; Ollama and backend sidecars; health checks; splash and error screen; stop sidecars on exit | 1.5 days |
| 6 | **Desktop single-user mode** | Auto-create and log in a local user; hide sharing UI | 0.5 day |
| 7 | **Installer** | Tauri NSIS bundle; app name, icon, version; on uninstall, ask whether to keep user data and downloaded models | 0.5 day |
| 8 | **Test on a clean Windows machine/VM** | Install; first-run download (also with a broken connection mid-download); add a PDF, index it, ask a question, summarise; restart with the network off; uninstall | 1 day |
| 9 | **Docs and licences** | User guide (install, one-time ~2.2 GB download, minimum 16 GB RAM, first-start time). Licence notices for the components the app installs: Llama 3.2 Community Licence ("Built with Llama"), Ollama (MIT), e5 (MIT), PyMuPDF (AGPL; see risks) | 0.5 day |

**Total: about 7.5–8.5 working days for one person.**

## 4. Risks and decisions

- **First run needs internet.** The ~2.2 GB download must finish before the AI assistant works. The library and PDF reader can work during the download; the assistant shows "setting up" until it finishes.
- **Download sources can change** (Ollama release URLs, model registry). Pin versions (Ollama release, model tag, e5 revision), and keep the URLs in one config file so they're easy to update.
- **PyTorch size.** The code already has a FastEmbed (ONNX) path. Switching the embedder to ONNX could cut the installer by up to ~1 GB, but it changes the embedding runtime the evaluation used, so only do this with a parity check (same rankings on a sample).
- **Memory.** llama3.2:3b with long contexts needs ~5–7 GB (measured). State a minimum of 16 GB RAM, and show a warning on machines with less.
- **Speed.** ~30 s per answer on CPU with long contexts (measured). Show streaming or progress in the chat panel so the app doesn't look frozen.
- **PyMuPDF licence (AGPL).** Distributing a binary that bundles PyMuPDF means the app's source must be available under AGPL-compatible terms. That is fine for a public student project; otherwise a commercial PyMuPDF licence is needed.
- **Code signing.** Without a certificate, Windows SmartScreen warns on install. That's acceptable for a thesis demo; mention it in the user guide.
- **Antivirus false positives** on PyInstaller executables are common. Test on the target machine, and use one-folder builds rather than one-file.

## 5. Order and timing

Do this **after the combination experiment's full run**, because both compete for the same machine and for time. Order:
1. settings and frontend URL (1, 2);
2. PyInstaller backend (3), with the RAG pipeline tested from the frozen build;
3. Tauri shell and first-run setup (5, 4);
4. single-user mode and installer (6, 7);
5. clean-machine test and docs (8, 9).
