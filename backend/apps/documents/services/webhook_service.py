import threading
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def trigger_rag_ingestion(document_id: int, file_path: str, title: str, owner_id: int) -> None:
    """
    Non-blocking notification to start chunking and vector embedding locally and via webhook.
    Runs in a background daemon thread so PDF uploads never block the request cycle.
    """
    def _ingest() -> None:
        # 1. Local RAG index build
        try:
            from .rag_service import get_or_create_rag
            logger.info(f"Background indexing started for document {document_id}")
            get_or_create_rag(document_id, file_path)
            logger.info(f"Background indexing completed for document {document_id}")
        except Exception as e:
            logger.warning(f"Background RAG ingestion failed for document {document_id}: {e}")

        # 2. Webhook notification (if microservice is listening)
        webhook_url = getattr(settings, 'RAG_WEBHOOK_URL', 'http://localhost:8001/webhook/rag/ingest')
        payload = {
            'document_id': document_id,
            'file_path': file_path,
            'title': title,
            'owner_id': owner_id,
        }
        try:
            requests.post(webhook_url, json=payload, timeout=3)
        except Exception:
            pass

    thread = threading.Thread(target=_ingest, daemon=True)
    thread.start()
