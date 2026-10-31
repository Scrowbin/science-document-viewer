# Project Documentation (`docs/`)

This directory holds the system architecture diagrams, use-case figures and design notes for the Scientific Document Manager. The complete thesis is [`../DU_AN_CNTT_TOAN_VAN.md`](../DU_AN_CNTT_TOAN_VAN.md); the evaluation methodology and results are in [`../eval/README.md`](../eval/README.md).

---

## 1. Architecture & Design Diagrams

* **`diagrams/`**: Mermaid / PlantUML sources (system architecture, ERD, ingestion and Q&A sequences, use case, user workflow).
* **`accounts.drawio`**: Relational user model & authentication sequence diagram.
* **`metadata_extract_usecase.png`**, **`use_case_for_now.png`**: Use case flows (PDF metadata extraction, overall system).

## 2. Design Notes

* **`design/FILE_STORAGE_PLAN.md`**: Planned move of PDF storage behind permission checks (after the evaluation work).
* **`metadata_extract.txt`**: Notes on the PDF metadata extraction flow.
