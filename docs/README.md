# Project Documentation (`docs/`)

This directory holds the system architecture diagrams, use-case figures and design notes for the Scientific Document Manager. The complete thesis is [`../DU_AN_CNTT_TOAN_VAN.md`](../DU_AN_CNTT_TOAN_VAN.md); the evaluation methodology and results are in [`../eval/README.md`](../eval/README.md).

---

## 1. Architecture & Design Diagrams

* **`diagrams/`**: Mermaid / PlantUML sources (system architecture, ERD, ingestion and Q&A sequences, use case, user workflow).
* **`accounts.drawio`**: Relational user model & authentication sequence diagram.
* **`metadata_extract_usecase.png`**, **`use_case_for_now.png`**: Use case flows (PDF metadata extraction, overall system).

## 2. Design Notes

* **`design/RAG_SERVICE_REVIEW.md`**: Review of `services/` (bugs, thread safety, security, performance); fixes deferred until the combination run ends.
* **`design/CONTEXT_RETRY_PLAN.md`**: Planned FR-16: fetch the next-ranked sections when the model refuses (`strict`/`once`/`loop`); not implemented.
* **`design/DEPLOYMENT_PLAN.md`**: Deferred until after the graduation project: desktop client + one project-hosted server (backend, storage, Ollama); lists why it does not scale.
* **`design/FILE_STORAGE_PLAN.md`**: Planned move of PDF storage behind permission checks (after the evaluation work).
* **`metadata_extract.txt`**: Notes on the PDF metadata extraction flow.
