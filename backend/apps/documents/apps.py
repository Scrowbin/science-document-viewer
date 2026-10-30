import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def _should_run_startup_recovery(argv=None, environ=None) -> bool:
    """
    Only recover in the process that actually serves requests:
      - never during tests, migrations or any management command other than runserver;
      - under runserver's autoreloader, only in the child (RUN_MAIN == 'true');
      - with `runserver --noreload`, in the single process.
    Non-manage.py launches (e.g. a WSGI/ASGI server) are allowed.
    """
    argv = sys.argv if argv is None else argv
    environ = os.environ if environ is None else environ

    if "test" in argv:
        return False
    program = os.path.basename(argv[0]) if argv else ""
    if program in ("manage.py", "django-admin", "django-admin.py") or program.startswith("django-admin"):
        if len(argv) < 2 or argv[1] != "runserver":
            return False
        if "--noreload" in argv:
            return True
        return environ.get("RUN_MAIN") == "true"
    return True


def recover_stuck_documents() -> int:
    """
    Resets documents left in INDEXING (by a crash/restart mid-ingestion) to PENDING and
    re-enqueues them on the background ingestion worker. Returns the number enqueued.
    Never raises (the database may not exist yet or be unreachable).
    """
    try:
        from .models import Document
        from .services.webhook_service import trigger_rag_ingestion

        stuck = list(Document.objects.filter(rag_status="INDEXING"))
        enqueued = 0
        for doc in stuck:
            Document.objects.filter(id=doc.id).update(rag_status="PENDING")
            if not doc.file:
                continue
            try:
                file_path = doc.file.path
            except Exception:
                continue
            trigger_rag_ingestion(
                document_id=doc.id,
                file_path=file_path,
                title=doc.title,
                owner_id=doc.owner_id,
            )
            enqueued += 1
        if stuck:
            logger.info(
                "Startup recovery: reset %d document(s) stuck in INDEXING, re-enqueued %d.",
                len(stuck), enqueued,
            )
        return enqueued
    except Exception as e:
        logger.warning("Startup recovery of stuck RAG ingestions skipped: %s", e)
        return 0


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'

    def ready(self):
        if not _should_run_startup_recovery():
            return
        # Run off the startup path: Django discourages DB queries inside ready(),
        # and the DB might not be reachable yet. Failures are logged, never raised.
        import threading

        def _recover():
            try:
                recover_stuck_documents()
            finally:
                try:
                    from django.db import connection
                    connection.close()
                except Exception:
                    pass

        threading.Thread(target=_recover, daemon=True, name="rag-startup-recovery").start()
