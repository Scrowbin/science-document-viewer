import threading
import requests
from django.conf import settings

def trigger_rag_ingestion(document_id: int, file_path: str, title: str, owner_id: int) -> None:
    """
    Non-blocking notification to RAG microservice to start chunking and embedding.
    Runs in a background daemon thread so PDF uploads never block the request cycle.
    Fails gracefully if RAG service is not reachable.
    """
    webhook_url = getattr(settings, 'RAG_WEBHOOK_URL', 'http://localhost:8001/webhook/rag/ingest')
    payload = {
        'document_id': document_id,
        'file_path': file_path,
        'title': title,
        'owner_id': owner_id,
    }

    def _send() -> None:
        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception:
            pass  # Non-blocking: RAG pipeline can be offline during core backend dev

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
