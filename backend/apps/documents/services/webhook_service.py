import logging
import os
import threading
from typing import Dict, Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Track active background ingestion threads for lifecycle coordination and deterministic tests
_active_ingest_threads: Dict[int, threading.Thread] = {}


def get_ingest_thread(document_id: int) -> Optional[threading.Thread]:
    """Returns the background ingestion thread for a document if currently active."""
    return _active_ingest_threads.get(document_id)


def join_all_ingest_threads(timeout: float = 10.0) -> None:
    """Waits for all active background ingestion threads to complete and cleans up."""
    for doc_id, thread in list(_active_ingest_threads.items()):
        if thread.is_alive():
            thread.join(timeout=timeout)
    _active_ingest_threads.clear()


def trigger_rag_ingestion(
    document_id: int,
    file_path: str,
    title: str = "",
    owner_id: Optional[int] = None,
    sync: bool = False,
) -> Optional[threading.Thread]:
    """
    Triggers the RAG ingestion pipeline:
      1. Sets document rag_status = 'INDEXING'.
      2. Extracts layout sections, chunks (hierarchical: child ~200 tokens, overlap 40, parent_text),
         embeds with intfloat/e5-small-v2 (384-dim), and writes points & payloads to Qdrant
         (persistent local mode at media/qdrant_db/ or configured storage path).
      3. On success, sets rag_status = 'INDEXED'.
      4. On any exception, sets rag_status = 'FAILED' and logs the error with traceback.
      5. Optionally fires webhook notification.

    Runs in a background daemon thread by default; runs synchronously if sync=True (useful in tests).
    """
    def _ingest() -> None:
        from django.db import connections
        from ..models import Document as DocModel
        from .rag_service import ingest_document

        try:
            # 1. Transition to INDEXING
            try:
                DocModel.objects.filter(id=document_id).update(rag_status="INDEXING")
                logger.info("Background indexing started for document %s (status=INDEXING)", document_id)
            except Exception as e:
                logger.error("Failed to set rag_status=INDEXING for document %s: %s", document_id, e)

            # 2. Extract, chunk, embed, and index into Qdrant
            try:
                if not file_path or not os.path.exists(file_path):
                    raise FileNotFoundError(f"Document file path not found or inaccessible: {file_path}")

                indexed_count, rag = ingest_document(document_id, file_path)
                if rag is None or indexed_count <= 0:
                    raise RuntimeError(
                        f"Background ingestion produced 0 chunks for document {document_id} from {file_path}"
                    )

                DocModel.objects.filter(id=document_id).update(rag_status="INDEXED")
                logger.info(
                    "Background indexing succeeded for document %s (%d chunks, status=INDEXED)",
                    document_id, indexed_count
                )
            except Exception as e:
                logger.error(
                    "Background RAG ingestion failed for document %s: %s",
                    document_id, e, exc_info=True
                )
                try:
                    DocModel.objects.filter(id=document_id).update(rag_status="FAILED")
                except Exception as db_err:
                    logger.error(
                        "Failed to record rag_status=FAILED for document %s: %s",
                        document_id, db_err
                    )

            # 3. Webhook notification (if microservice is listening)
            webhook_url = getattr(settings, "RAG_WEBHOOK_URL", "http://localhost:8001/webhook/rag/ingest")
            payload = {
                "document_id": document_id,
                "file_path": file_path,
                "title": title,
                "owner_id": owner_id,
            }
            try:
                requests.post(webhook_url, json=payload, timeout=3)
            except Exception:
                pass
        finally:
            if not sync:
                from django.db import connection
                connection.close()

    if sync:
        _ingest()
        return None

    thread = threading.Thread(
        target=_ingest,
        daemon=True,
        name=f"rag-ingest-{document_id}",
    )
    _active_ingest_threads[document_id] = thread
    thread.start()
    return thread

