"""
Background RAG ingestion queue.

All ingestion jobs go through ONE module-level queue served by ONE lazily started
daemon worker thread, so documents are indexed strictly one at a time (the embedding
model and the embedded Qdrant store are not safe to hammer with parallel writers).

Status transitions per job: PENDING -> INDEXING -> INDEXED | FAILED.
"""
import logging
import os
import queue
import threading
from typing import Dict, List, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class IngestJob:
    """A queued ingestion request. Exposes a Thread-like join()/is_alive() for callers and tests."""

    def __init__(self, document_id: int, file_path: str, title: str = "", owner_id: Optional[int] = None):
        self.document_id = document_id
        self.file_path = file_path
        self.title = title
        self.owner_id = owner_id
        self._done = threading.Event()

    def join(self, timeout: Optional[float] = None) -> None:
        self._done.wait(timeout)

    def is_alive(self) -> bool:
        return not self._done.is_set()

    def mark_done(self) -> None:
        self._done.set()

    def __repr__(self) -> str:
        return f"IngestJob(document_id={self.document_id})"


_job_queue: "queue.Queue[IngestJob]" = queue.Queue()
_worker_thread: Optional[threading.Thread] = None
_worker_lock = threading.Lock()
# Jobs that are queued or running, keyed by document id. Entries are removed when a job finishes.
_active_jobs: Dict[int, IngestJob] = {}
_active_lock = threading.Lock()


def get_ingest_thread(document_id: int) -> Optional[IngestJob]:
    """Returns the queued/running ingestion job for a document, or None if none is pending."""
    with _active_lock:
        return _active_jobs.get(document_id)


def get_active_jobs() -> List[IngestJob]:
    with _active_lock:
        return list(_active_jobs.values())


def join_all_ingest_threads(timeout: float = 10.0) -> None:
    """Waits (up to `timeout` per job) for every queued or running ingestion job to finish."""
    for job in get_active_jobs():
        if job.is_alive():
            job.join(timeout=timeout)


def _notify_webhook(document_id: int, file_path: str, title: str, owner_id: Optional[int]) -> None:
    """POSTs to an external webhook only when settings.RAG_WEBHOOK_URL is explicitly configured."""
    webhook_url = getattr(settings, "RAG_WEBHOOK_URL", None)
    if not webhook_url:
        return
    payload = {
        "document_id": document_id,
        "file_path": file_path,
        "title": title,
        "owner_id": owner_id,
    }
    try:
        requests.post(webhook_url, json=payload, timeout=3)
    except Exception as e:
        logger.warning("RAG webhook POST to %s failed for document %s: %s", webhook_url, document_id, e)


def run_ingestion(document_id: int, file_path: str, title: str = "", owner_id: Optional[int] = None) -> bool:
    """
    Runs one ingestion synchronously in the calling thread:
      INDEXING -> chunk, embed, write to Qdrant -> INDEXED (or FAILED on any error).
    Returns True on success.
    """
    from ..models import Document as DocModel
    from .rag_service import ingest_document

    try:
        DocModel.objects.filter(id=document_id).update(rag_status="INDEXING")
        logger.info("Background indexing started for document %s (status=INDEXING)", document_id)
    except Exception as e:
        logger.error("Failed to set rag_status=INDEXING for document %s: %s", document_id, e)

    success = False
    try:
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file path not found or inaccessible: {file_path}")

        indexed_count, rag = ingest_document(document_id, file_path)
        if rag is None or indexed_count <= 0:
            raise RuntimeError(
                f"Background ingestion produced 0 chunks for document {document_id} from {file_path}"
            )

        DocModel.objects.filter(id=document_id).update(rag_status="INDEXED")
        success = True
        logger.info(
            "Background indexing succeeded for document %s (%d chunks, status=INDEXED)",
            document_id, indexed_count,
        )
    except Exception as e:
        logger.error("Background RAG ingestion failed for document %s: %s", document_id, e, exc_info=True)
        try:
            DocModel.objects.filter(id=document_id).update(rag_status="FAILED")
        except Exception as db_err:
            logger.error("Failed to record rag_status=FAILED for document %s: %s", document_id, db_err)

    _notify_webhook(document_id, file_path, title, owner_id)
    return success


def process_job(job: IngestJob) -> None:
    """Processes a single job and always releases it (marks done, drops it from the active map)."""
    try:
        run_ingestion(job.document_id, job.file_path, job.title, job.owner_id)
    except Exception:
        logger.exception("Unexpected error while processing ingestion job for document %s", job.document_id)
    finally:
        with _active_lock:
            if _active_jobs.get(job.document_id) is job:
                del _active_jobs[job.document_id]
        job.mark_done()


def drain_queue(max_jobs: Optional[int] = None) -> int:
    """
    Processes queued jobs one at a time in the calling thread until the queue is empty
    (or `max_jobs` were processed). Used by the worker loop's logic and by unit tests.
    Returns the number of jobs processed.
    """
    processed = 0
    while max_jobs is None or processed < max_jobs:
        try:
            job = _job_queue.get_nowait()
        except queue.Empty:
            break
        try:
            process_job(job)
        finally:
            _job_queue.task_done()
        processed += 1
    return processed


def _worker_loop() -> None:
    from django.db import connection

    while True:
        job = _job_queue.get()
        try:
            process_job(job)
        finally:
            _job_queue.task_done()
            try:
                connection.close()
            except Exception:
                pass


def _ensure_worker() -> None:
    global _worker_thread
    with _worker_lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(target=_worker_loop, daemon=True, name="rag-ingest-worker")
            _worker_thread.start()


def enqueue_ingestion(
    document_id: int,
    file_path: str,
    title: str = "",
    owner_id: Optional[int] = None,
    start_worker: bool = True,
) -> IngestJob:
    """Adds a job to the single ingestion queue (starting the worker lazily) and returns it."""
    job = IngestJob(document_id, file_path, title, owner_id)
    with _active_lock:
        _active_jobs[document_id] = job
    _job_queue.put(job)
    if start_worker:
        _ensure_worker()
    return job


def trigger_rag_ingestion(
    document_id: int,
    file_path: str,
    title: str = "",
    owner_id: Optional[int] = None,
    sync: bool = False,
) -> Optional[IngestJob]:
    """
    Triggers the RAG ingestion pipeline for a document.
    Default: enqueues a job on the single background worker and returns the IngestJob handle.
    sync=True: runs the ingestion inline in the caller (useful in tests) and returns None.
    """
    if sync:
        run_ingestion(document_id, file_path, title, owner_id)
        return None
    return enqueue_ingestion(document_id, file_path, title, owner_id)
