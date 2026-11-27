# Demo checklist

## 15 minutes before

1. Close anything using the app's database or index. Do not run `reindex_documents` or evaluation scripts while the backend is up.
2. On Kaggle, open `demo/kaggle_llm_server.ipynb` and check:
   - **Accelerator** is GPU and **Internet** is on.
   - Secrets `NGROK_AUTHTOKEN`, `NGROK_DOMAIN` and `OLLAMA_API_KEY` are attached.
   - Secret `OLLAMA_MODEL` is `qwen3:4b-instruct-2507-q4_K_M`. Without it the notebook uses `llama3.2:3b`.
3. Click **Save Version → Save & Run All**. Startup can take about 10 minutes.
4. Wait for the log to show `no key  -> 401` and `with key-> 200 ['qwen3:4b-instruct-2507-q4_K_M']`.
5. Start local Ollama as the backup and run `ollama list`. It must include `llama3.2:3b`.
6. From the repo root, run `npm start`. Do not use `npm run dev`, which restarts the backend when files change.
7. In `backend/` with the venv active, run `python manage.py ollama_status`. It must say `configured model ... available`. This checks Kaggle only, not the local backup.
8. Open `http://localhost:5173`, not a LAN address. If Vite reports another port because 5173 is busy, close the other app and restart so the API allows the origin.
9. Sign in and ask one warm-up question on any paper. The answer must be labelled **(Remote GPU)**.
10. If *Attention Is All You Need* is already in the library, delete it from Library and Trash so the upload looks clean.
11. **Sign Out** and reload the page, so the demo starts at the login screen.

## Demo script

| Step | Action | Expect |
|---|---|---|
| Log in | Sign in | Library opens |
| Upload | **Add → Upload PDF File**, choose `sample_documents/attention.pdf` | Preview shows the title, 8 authors and the year |
| Import | **Confirm & Import to Library** | PDF opens in its own tab |
| Navigate | Next page, type `3` in the page box and press **Enter**, zoom in, **Width** | Page and zoom update |
| Find | `Ctrl+F`, search `Scaled Dot-Product`, `Esc` | Match is marked, then cleared |
| Annotate | Click the **Notes** tab, select a sentence, choose a highlight colour | Highlight appears on the page and under **Notes** |
| AI panel | Open **AI Assistant**, wait for **Indexed** | Input unlocks |
| Ask 1 | `How many parallel attention heads were used?` | 8; passage on page 5 |
| Ask 2 | `What BLEU score did the model achieve on English-to-German translation?` | 28.4; first chip is the abstract on page 1, the results passage is on page 8 |
| Ask 3 | `What hardware was the model trained on?` | 8 NVIDIA P100 GPUs; passage on page 7 |
| Citation | Click the first page chip under the answer | PDF scrolls to the highlighted passage |
| Refusal | `What is the population of Vietnam?` | "No answer found in this paper" |

Ask only these questions on stage. Answers normally take about 2 seconds on the Kaggle GPU.

## If something goes wrong

| Symptom | Action |
|---|---|
| Answer says **(Local RAG)** | Kaggle or the tunnel dropped. Keep going; answers take about 30 s on CPU. A hung tunnel can add up to 40 s per question first. Restart Kaggle afterwards. |
| Answer shows excerpts only | Neither model replied. Show the citations, then check Kaggle and Ollama. |
| Status stuck on Queued or Indexing | Indexing takes about 2 minutes for the Attention paper on CPU (4–5 minutes for long papers), so upload it before the talk or talk through the wait. If it never moves, restart the backend; indexing resumes on startup. |
| `ollama_status` says the model is not available | Make the Kaggle secret `OLLAMA_MODEL` and `OLLAMA_MODEL` in `backend/.env` match, then restart. If it shows `has: []`, also check that `OLLAMA_API_KEY` is the same in both places. |
| ngrok "endpoint already online" | Cancel the old Kaggle run, or stop the endpoint in the ngrok dashboard. |

## Known limitations to state if asked

- Questions are best asked in English. Vietnamese questions on an English paper are often refused because they fall below the relevance threshold.
- The assistant can refuse a question the paper does answer, when retrieval misses the passage.
- Answers can add detail or lose a qualifier, so the highlighted source remains the reference.
- Highlights show the retrieved passage that best matches the answer. The supporting sentence can still be nearby or on another page.
- Scanned PDFs with no text can be read but not indexed for AI answers.
- With Kaggle, the question, the document title, section names and retrieved excerpts leave the machine, so demo with public papers only.

## Afterwards

Cancel the Kaggle run so it stops using the weekly GPU quota.
