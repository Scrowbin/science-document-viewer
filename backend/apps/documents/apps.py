import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


# Production WSGI/ASGI servers whose worker processes serve requests.
_WEB_SERVER_PROGRAMS = ("gunicorn", "uvicorn", "daphne", "hypercorn", "waitress-serve")


def _should_run_startup_recovery(argv=None, environ=None) -> bool:
    """
    Only recover in the process that actually serves requests:
      - never during tests, migrations or any management command other than runserver;
      - under runserver's autoreloader, only in the child (RUN_MAIN == 'true');
      - with `runserver --noreload`, in the single process;
      - under a known WSGI/ASGI server (gunicorn, uvicorn, daphne, hypercorn, waitress-serve).
    Anything else (evaluation scripts calling django.setup(), pytest, notebooks) does not
    recover, so it never starts background ingestion. RAG_STARTUP_RECOVERY=1 forces it on
    (e.g. for a server launched another way), RAG_STARTUP_RECOVERY=0 forces it off.
    """
    argv = sys.argv if argv is None else argv
    environ = os.environ if environ is None else environ

    override = environ.get("RAG_STARTUP_RECOVERY", "").strip().lower()
    if override in ("0", "false", "no"):
        return False
    if "test" in argv:
        return False
    if override in ("1", "true", "yes"):
        return True
    program = os.path.basename(argv[0]) if argv else ""
    if program.lower().endswith(".exe"):
        program = program[:-4]
    if program in ("manage.py", "django-admin", "django-admin.py") or program.startswith("django-admin"):
        if len(argv) < 2 or argv[1] != "runserver":
            return False
        if "--noreload" in argv:
            return True
        return environ.get("RUN_MAIN") == "true"
    return program in _WEB_SERVER_PROGRAMS


def recover_stuck_documents() -> int:
    """
    Re-enqueues documents whose ingestion did not finish: INDEXING (crash/restart
    mid-ingestion) is reset to PENDING, and PENDING documents with a file (queued in memory
    when the process stopped) are queued again. Returns the number enqueued.
    Never raises (the database may not exist yet or be unreachable).
    """
    try:
        from .models import Document
        from .services.webhook_service import trigger_rag_ingestion

        pending = list(Document.objects.filter(rag_status="PENDING").exclude(file="").exclude(file__isnull=True))
        stuck = list(Document.objects.filter(rag_status="INDEXING")) + pending
        enqueued = 0
        for doc in stuck:
            if doc.rag_status != "PENDING":
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
                "Startup recovery: %d unfinished document(s) (%d PENDING), re-enqueued %d.",
                len(stuck), len(pending), enqueued,
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
