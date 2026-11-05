"""
Application-layer tests for the RAG HTTP contract, ingestion queue, metadata handling and
startup recovery. Everything that would load an embedding model or call Ollama is mocked.

Run with:  python manage.py test apps.documents.tests_app
"""
import os
import queue
import tempfile
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .apps import _should_run_startup_recovery, recover_stuck_documents
from .models import Annotation, Document, DocumentShare
from .services import webhook_service
from .services.pdf_metadata_service import apply_pdf_metadata_to_document, is_raw_title

User = get_user_model()

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


class _MediaTestCase(TestCase):
    """Isolates uploaded files in a temporary MEDIA_ROOT and mocks background ingestion."""

    def setUp(self):
        self._media = tempfile.TemporaryDirectory()
        self._override = override_settings(MEDIA_ROOT=self._media.name)
        self._override.enable()
        self.trigger_patch = patch("apps.documents.views.trigger_rag_ingestion")
        self.trigger = self.trigger_patch.start()
        self.client = APIClient()
        self.owner = User.objects.create_user(username="app_owner", email="o@univ.edu", password="pw123456")
        self.client.force_authenticate(user=self.owner)

    def tearDown(self):
        self.trigger_patch.stop()
        self._override.disable()
        self._media.cleanup()
        super().tearDown()

    def _doc_with_file(self, title="Paper", rag_status="INDEXED", name="paper.pdf"):
        doc = Document.objects.create(owner=self.owner, title=title, rag_status=rag_status)
        doc.file.save(name, SimpleUploadedFile(name, PDF_BYTES), save=True)
        return doc


class ChatSummarizeContractTests(_MediaTestCase):
    def setUp(self):
        super().setUp()
        self.doc = self._doc_with_file()

    def _chat(self, payload):
        return self.client.post(f"/api/v1/documents/{self.doc.id}/chat/", payload, format="json")

    def _summarize(self):
        return self.client.post(f"/api/v1/documents/{self.doc.id}/summarize/", {}, format="json")

    def test_409_while_indexing(self):
        Document.objects.filter(id=self.doc.id).update(rag_status="INDEXING")
        with patch("apps.documents.views.query_document") as q, \
             patch("apps.documents.views.summarize_document") as s:
            for resp in (self._chat({"question": "What is it?"}), self._summarize()):
                self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
                self.assertEqual(resp.data, {"code": "indexing", "detail": "Document is still being indexed."})
            q.assert_not_called()
            s.assert_not_called()

    def test_question_required(self):
        with patch("apps.documents.views.query_document") as q:
            for payload in ({}, {"question": ""}, {"question": "   "}, {"question": 42}):
                resp = self._chat(payload)
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, payload)
                self.assertEqual(resp.data["code"], "question_required")
            q.assert_not_called()

    def test_question_too_long(self):
        with patch("apps.documents.views.query_document") as q:
            resp = self._chat({"question": "x" * 2001})
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(resp.data["code"], "question_too_long")
            q.assert_not_called()

            q.return_value = {"answer": "ok", "sources": []}
            self.assertEqual(self._chat({"question": "x" * 2000}).status_code, status.HTTP_200_OK)

    def test_success_passes_through_unchanged(self):
        answer = {"answer": "A", "sources": [{"page": 2}], "model": "llama3.2:3b", "extra": 1}
        summary = {"summary": "S", "sources": []}
        with patch("apps.documents.views.query_document", return_value=answer) as q, \
             patch("apps.documents.views.summarize_document", return_value=summary):
            resp = self._chat({"question": "  What?  "})
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(resp.data, answer)
            self.assertEqual(q.call_args.args[2], "What?")
            resp = self._summarize()
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(resp.data, summary)

    def test_rag_exception_returns_structured_500(self):
        with patch("apps.documents.views.query_document", side_effect=RuntimeError("qdrant locked")), \
             patch("apps.documents.views.summarize_document", side_effect=RuntimeError("ollama down")), \
             self.assertLogs("apps.documents.views", level="ERROR"):
            for resp in (self._chat({"question": "What?"}), self._summarize()):
                self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
                self.assertEqual(resp.data["code"], "rag_error")
                self.assertTrue(resp.data["detail"])
                self.assertNotIn("qdrant", resp.data["detail"])

    def test_viewer_can_still_chat_outsider_cannot(self):
        viewer = User.objects.create_user(username="app_viewer", email="app_viewer@univ.edu", password="pw123456")
        outsider = User.objects.create_user(username="app_outsider", email="app_outsider@univ.edu", password="pw123456")
        DocumentShare.objects.create(document=self.doc, shared_with_user=viewer, permission="VIEW")
        with patch("apps.documents.views.query_document", return_value={"answer": "ok"}):
            self.client.force_authenticate(user=viewer)
            self.assertEqual(self._chat({"question": "Q"}).status_code, status.HTTP_200_OK)
            self.client.force_authenticate(user=outsider)
            self.assertEqual(self._chat({"question": "Q"}).status_code, status.HTTP_404_NOT_FOUND)


class ReindexContractTests(_MediaTestCase):
    def _reindex(self, doc, payload=None):
        return self.client.post(f"/api/v1/documents/{doc.id}/reindex/", payload or {}, format="json")

    def test_invalid_strategy_rejected_before_cache_eviction(self):
        doc = self._doc_with_file()
        with patch("apps.documents.views.evict_rag_instance") as view_evict, \
             patch("apps.documents.services.rag_service.evict_rag_instance") as svc_evict, \
             patch("apps.documents.views.reindex_document") as reindex:
            resp = self._reindex(doc, {"strategy": "semantic"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["code"], "invalid_strategy")
        view_evict.assert_not_called()
        svc_evict.assert_not_called()
        reindex.assert_not_called()
        doc.refresh_from_db()
        self.assertEqual(doc.rag_status, "INDEXED")

    def test_no_file(self):
        doc = Document.objects.create(owner=self.owner, title="Metadata only")
        with patch("apps.documents.views.reindex_document") as reindex:
            resp = self._reindex(doc)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data["code"], "no_file")
        reindex.assert_not_called()

    def test_success_sets_indexed_and_reports_chunks(self):
        doc = self._doc_with_file(rag_status="FAILED")
        seen_status = []

        def fake_reindex(doc_id, file_path, strategy=None):
            seen_status.append(Document.objects.get(id=doc_id).rag_status)
            return SimpleNamespace(documents=[object()] * 7)

        with patch("apps.documents.views.reindex_document", side_effect=fake_reindex) as reindex:
            resp = self._reindex(doc, {"strategy": "section_overlap"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "INDEXED")
        self.assertEqual(resp.data["chunks"], 7)
        self.assertEqual(seen_status, ["INDEXING"])
        self.assertEqual(reindex.call_args.kwargs["strategy"], "section_overlap")
        doc.refresh_from_db()
        self.assertEqual(doc.rag_status, "INDEXED")

    def test_failure_sets_failed(self):
        doc = self._doc_with_file()
        for outcome in ({"return_value": None}, {"side_effect": RuntimeError("boom")}):
            with patch("apps.documents.views.reindex_document", **outcome), \
                 self.assertLogs("apps.documents.views", level="ERROR"):
                resp = self._reindex(doc, {"strategy": "hierarchical"})
            self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(resp.data, {"status": "FAILED", "code": "reindex_failed"})
            doc.refresh_from_db()
            self.assertEqual(doc.rag_status, "FAILED")


class IngestionTriggerTests(_MediaTestCase):
    def test_duplicate_triggers_ingestion_for_clone(self):
        doc = self._doc_with_file()
        resp = self.client.post(f"/api/v1/documents/{doc.id}/duplicate/")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        clone = Document.objects.get(id=resp.data["id"])
        self.assertEqual(clone.rag_status, "PENDING")
        self.trigger.assert_called_once()
        kwargs = self.trigger.call_args.kwargs
        self.assertEqual(kwargs["document_id"], clone.id)
        self.assertEqual(kwargs["file_path"], clone.file.path)

    def test_duplicate_without_file_does_not_trigger(self):
        doc = Document.objects.create(owner=self.owner, title="No PDF")
        resp = self.client.post(f"/api/v1/documents/{doc.id}/duplicate/")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.trigger.assert_not_called()

    def test_file_replacement_resets_pending_and_reingests(self):
        doc = self._doc_with_file()
        with patch("apps.documents.views.evict_rag_instance") as evict:
            resp = self.client.patch(
                f"/api/v1/documents/{doc.id}/",
                {"file": SimpleUploadedFile("v2.pdf", PDF_BYTES + b" v2", content_type="application/pdf")},
                format="multipart",
            )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.rag_status, "PENDING")
        evict.assert_called_once_with(doc.id)
        self.trigger.assert_called_once()
        self.assertEqual(self.trigger.call_args.kwargs["file_path"], doc.file.path)

    def test_metadata_edit_does_not_reingest(self):
        doc = self._doc_with_file()
        resp = self.client.patch(f"/api/v1/documents/{doc.id}/", {"title": "Renamed"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.trigger.assert_not_called()
        doc.refresh_from_db()
        self.assertEqual(doc.rag_status, "INDEXED")


class UploadTitleTests(_MediaTestCase):
    EXTRACTED = {"title": "Extracted From PDF", "authors": ["Ada Lovelace"]}

    def test_confirmed_title_is_not_overwritten(self):
        doc = self._doc_with_file(title="Title The User Confirmed", name="scan_0042.pdf")
        with patch("apps.documents.services.pdf_metadata_service.extract_metadata_from_pdf",
                   return_value=dict(self.EXTRACTED)):
            apply_pdf_metadata_to_document(doc)
        doc.refresh_from_db()
        self.assertEqual(doc.title, "Title The User Confirmed")

    def test_raw_filename_title_is_replaced(self):
        doc = self._doc_with_file(title="scan_0042", name="scan_0042.pdf")
        with patch("apps.documents.services.pdf_metadata_service.extract_metadata_from_pdf",
                   return_value=dict(self.EXTRACTED)):
            apply_pdf_metadata_to_document(doc)
        doc.refresh_from_db()
        self.assertEqual(doc.title, "Extracted From PDF")

    def test_is_raw_title(self):
        self.assertTrue(is_raw_title("", "documents/x.pdf"))
        self.assertTrue(is_raw_title("1706.03762v7", None))
        self.assertTrue(is_raw_title("Untitled Document", None))
        self.assertTrue(is_raw_title("my_paper", "documents/my_paper.pdf"))
        self.assertTrue(is_raw_title("my_paper.pdf", "documents/my_paper_AbC1234.pdf"))
        self.assertFalse(is_raw_title("Deep", "documents/Deep_learning.pdf"))
        self.assertFalse(is_raw_title("Attention Is All You Need", "documents/1706.03762v7.pdf"))

    def test_upload_with_previewed_metadata_skips_second_extraction(self):
        with patch("apps.documents.views.apply_pdf_metadata_to_document") as apply_meta:
            resp = self.client.post("/api/v1/documents/", {
                "title": "Confirmed In Upload Modal",
                "author_names": ["Ada Lovelace"],
                "file": SimpleUploadedFile("upload.pdf", PDF_BYTES, content_type="application/pdf"),
            }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        apply_meta.assert_not_called()
        self.trigger.assert_called_once()
        self.assertEqual(Document.objects.get(id=resp.data["id"]).title, "Confirmed In Upload Modal")

    def test_upload_without_metadata_still_extracts(self):
        with patch("apps.documents.views.apply_pdf_metadata_to_document") as apply_meta:
            resp = self.client.post("/api/v1/documents/", {
                "title": "raw_upload",
                "file": SimpleUploadedFile("raw_upload.pdf", PDF_BYTES, content_type="application/pdf"),
            }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        apply_meta.assert_called_once()
        self.trigger.assert_called_once()


class HierarchicalChunksTests(_MediaTestCase):
    def test_hierarchical_chunks_grouped_by_parent(self):
        doc = self._doc_with_file()
        sections = [
            {"title": "1. Introduction", "page_start": 1, "page_end": 1,
             "text": "Short introduction about retrieval augmented generation."},
            {"title": "2. Method", "page_start": 2, "page_end": 3,
             "text": " ".join(f"word{i}" for i in range(400))},
        ]
        with patch("apps.documents.views.extract_sections_from_pdf", return_value=sections) as extract:
            resp = self.client.get(f"/api/v1/documents/{doc.id}/chunks/?strategy=hierarchical")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        extract.assert_called_once_with(doc.file.path)
        data = resp.data
        self.assertEqual(data["strategy"], "hierarchical")
        self.assertEqual(data["total_parents"], 2)
        parents = data["parents"]
        self.assertEqual([p["section"] for p in parents], ["1. Introduction", "2. Method"])
        self.assertEqual(parents[0]["child_count"], 1)
        self.assertGreater(parents[1]["child_count"], 1)
        self.assertEqual(sum(p["child_count"] for p in parents), data["total_chunks"])
        self.assertEqual(len(data["chunks"]), data["total_chunks"])
        ids_by_parent = {p["parent_id"]: set(p["child_ids"]) for p in parents}
        for chunk in data["chunks"]:
            self.assertIn(chunk["chunk_id"], ids_by_parent[chunk["parent_id"]])
            self.assertNotIn("parent_text", chunk)  # sent once per parent instead
        self.assertTrue(all(p["parent_text"] for p in parents))

        # Sections are cached per file version: a second request does not re-extract.
        with patch("apps.documents.views.extract_sections_from_pdf", return_value=sections) as extract:
            resp = self.client.get(f"/api/v1/documents/{doc.id}/chunks/?strategy=section_overlap")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        extract.assert_not_called()

    def test_existing_strategies_still_work_and_unknown_rejected(self):
        doc = Document.objects.create(owner=self.owner, title="T", extra="Some abstract text " * 30)
        for strategy in ("section", "section_token", "section_overlap"):
            resp = self.client.get(f"/api/v1/documents/{doc.id}/chunks/?strategy={strategy}")
            self.assertEqual(resp.status_code, status.HTTP_200_OK, strategy)
            self.assertEqual(resp.data["strategy"], strategy)
            self.assertGreater(resp.data["total_chunks"], 0)
        resp = self.client.get(f"/api/v1/documents/{doc.id}/chunks/?strategy=bogus")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class IngestionQueueTests(TestCase):
    def setUp(self):
        # Fresh queue/registry so nothing leaks between tests; no worker thread is started.
        self._q = patch.object(webhook_service, "_job_queue", queue.Queue())
        self._a = patch.object(webhook_service, "_active_jobs", {})
        self._q.start()
        self._a.start()

    def tearDown(self):
        self._q.stop()
        self._a.stop()
        super().tearDown()

    def test_jobs_processed_sequentially_and_released(self):
        events = []
        running = {"n": 0, "max": 0}
        lock = threading.Lock()

        def fake_run(document_id, file_path, title="", owner_id=None):
            with lock:
                running["n"] += 1
                running["max"] = max(running["max"], running["n"])
            events.append(("start", document_id))
            events.append(("end", document_id))
            with lock:
                running["n"] -= 1
            return True

        with patch.object(webhook_service, "run_ingestion", side_effect=fake_run), \
             patch.object(webhook_service, "_ensure_worker") as ensure_worker:
            jobs = [webhook_service.enqueue_ingestion(i, f"/tmp/{i}.pdf", start_worker=False) for i in (1, 2, 3)]
            ensure_worker.assert_not_called()
            self.assertIs(webhook_service.get_ingest_thread(2), jobs[1])
            self.assertTrue(all(j.is_alive() for j in jobs))

            processed = webhook_service.drain_queue()

        self.assertEqual(processed, 3)
        self.assertEqual(events, [("start", 1), ("end", 1), ("start", 2), ("end", 2), ("start", 3), ("end", 3)])
        self.assertEqual(running["max"], 1)
        self.assertTrue(all(not j.is_alive() for j in jobs))
        self.assertIsNone(webhook_service.get_ingest_thread(1))
        self.assertEqual(webhook_service.get_active_jobs(), [])

    def test_failing_job_does_not_block_the_queue(self):
        calls = []

        def fake_run(document_id, *args, **kwargs):
            calls.append(document_id)
            if document_id == 1:
                raise RuntimeError("unexpected")
            return True

        with patch.object(webhook_service, "run_ingestion", side_effect=fake_run), \
             self.assertLogs("apps.documents.services.webhook_service", level="ERROR"):
            webhook_service.enqueue_ingestion(1, "a", start_worker=False)
            webhook_service.enqueue_ingestion(2, "b", start_worker=False)
            self.assertEqual(webhook_service.drain_queue(), 2)
        self.assertEqual(calls, [1, 2])
        self.assertEqual(webhook_service.get_active_jobs(), [])


class RunIngestionTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="ingest_owner", email="ingest_owner@univ.edu", password="pw123456")
        self.doc = Document.objects.create(owner=self.owner, title="Ingest Me")
        fd, self.path = tempfile.mkstemp(suffix=".pdf")
        os.write(fd, PDF_BYTES)
        os.close(fd)

    def tearDown(self):
        os.remove(self.path)
        super().tearDown()

    def _run(self, ingest_result=(5, object())):
        seen = []

        def fake_ingest(doc_id, file_path, strategy=None):
            seen.append(Document.objects.get(id=doc_id).rag_status)
            return ingest_result

        with patch("apps.documents.services.rag_service.ingest_document", side_effect=fake_ingest), \
             patch.object(webhook_service.requests, "post") as post:
            ok = webhook_service.run_ingestion(self.doc.id, self.path, "Ingest Me", self.owner.id)
        self.doc.refresh_from_db()
        return ok, seen, post

    @override_settings()
    def test_webhook_not_posted_when_url_unset(self):
        from django.conf import settings
        if hasattr(settings, "RAG_WEBHOOK_URL"):
            del settings.RAG_WEBHOOK_URL
        ok, seen, post = self._run()
        self.assertTrue(ok)
        self.assertEqual(seen, ["INDEXING"])
        self.assertEqual(self.doc.rag_status, "INDEXED")
        post.assert_not_called()

    @override_settings(RAG_WEBHOOK_URL="http://hooks.local/rag")
    def test_webhook_posted_when_url_set(self):
        ok, _, post = self._run()
        self.assertTrue(ok)
        post.assert_called_once()
        self.assertEqual(post.call_args.args[0], "http://hooks.local/rag")

    def test_zero_chunks_sets_failed(self):
        with self.assertLogs("apps.documents.services.webhook_service", level="ERROR"):
            ok, _, _ = self._run(ingest_result=(0, None))
        self.assertFalse(ok)
        self.assertEqual(self.doc.rag_status, "FAILED")


class StartupRecoveryTests(TestCase):
    def test_guard(self):
        runserver = ["manage.py", "runserver"]
        self.assertFalse(_should_run_startup_recovery(["manage.py", "test"], {}))
        self.assertFalse(_should_run_startup_recovery(["manage.py", "migrate"], {"RUN_MAIN": "true"}))
        self.assertFalse(_should_run_startup_recovery(["manage.py", "reindex_documents", "--all"], {}))
        self.assertFalse(_should_run_startup_recovery(runserver, {}))  # autoreloader parent
        self.assertTrue(_should_run_startup_recovery(runserver, {"RUN_MAIN": "true"}))
        self.assertTrue(_should_run_startup_recovery(runserver + ["--noreload"], {}))
        # Evaluation scripts / pytest call django.setup() and must never start ingestion.
        self.assertFalse(_should_run_startup_recovery(["eval/phases/phase_12_combination/scripts/run.py"], {}))
        self.assertFalse(_should_run_startup_recovery(["pytest"], {}))
        self.assertTrue(_should_run_startup_recovery(["/usr/bin/gunicorn", "core.wsgi"], {}))
        self.assertTrue(_should_run_startup_recovery(["serve.py"], {"RAG_STARTUP_RECOVERY": "1"}))
        self.assertFalse(_should_run_startup_recovery(runserver + ["--noreload"], {"RAG_STARTUP_RECOVERY": "0"}))

    def test_stuck_documents_reset_and_enqueued(self):
        owner = User.objects.create_user(username="recover_owner", email="recover_owner@univ.edu", password="pw123456")
        stuck = Document.objects.create(owner=owner, title="Stuck", rag_status="INDEXING", file="documents/stuck.pdf")
        stuck_no_file = Document.objects.create(owner=owner, title="Stuck no file", rag_status="INDEXING")
        done = Document.objects.create(owner=owner, title="Done", rag_status="INDEXED", file="documents/done.pdf")
        queued = Document.objects.create(owner=owner, title="Queued", rag_status="PENDING", file="documents/queued.pdf")
        queued_no_file = Document.objects.create(owner=owner, title="Metadata only", rag_status="PENDING")
        with patch("apps.documents.services.webhook_service.trigger_rag_ingestion") as trigger:
            self.assertEqual(recover_stuck_documents(), 2)
        self.assertEqual(
            sorted(c.kwargs["document_id"] for c in trigger.call_args_list), sorted([stuck.id, queued.id])
        )
        for doc, expected in ((stuck, "PENDING"), (stuck_no_file, "PENDING"), (done, "INDEXED"),
                              (queued, "PENDING"), (queued_no_file, "PENDING")):
            doc.refresh_from_db()
            self.assertEqual(doc.rag_status, expected)

    def test_recovery_never_raises(self):
        with patch("apps.documents.models.Document.objects") as objects:
            objects.filter.side_effect = RuntimeError("database not ready")
            self.assertEqual(recover_stuck_documents(), 0)


class ReindexCommandTests(TestCase):
    def test_single_indexing_pass(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with override_settings(MEDIA_ROOT=tmp.name):
            owner = User.objects.create_user(username="cmd_owner", email="cmd_owner@univ.edu", password="pw123456")
            doc = Document.objects.create(owner=owner, title="Cmd Paper", rag_status="FAILED")
            doc.file.save("cmd.pdf", SimpleUploadedFile("cmd.pdf", PDF_BYTES), save=True)

            service = MagicMock()
            service.client.collection_exists.return_value = True
            service.client.count.return_value = SimpleNamespace(count=2)
            with patch("apps.documents.management.commands.reindex_documents.RagService") as rag_cls, \
                 patch("apps.documents.management.commands.reindex_documents.reindex_document",
                       return_value=SimpleNamespace(documents=[1, 2, 3, 4])) as reindex:
                rag_cls.get_instance.return_value = service
                call_command("reindex_documents", f"--doc-id={doc.id}", "--strategy=hierarchical", stdout=MagicMock())

            reindex.assert_called_once_with(doc.id, doc.file.path, strategy="hierarchical")
            service.index_chunks.assert_not_called()
            doc.refresh_from_db()
            self.assertEqual(doc.rag_status, "INDEXED")


class BulkDocumentActionTests(_MediaTestCase):
    """POST /api/v1/documents/bulk/ applies one action to many documents with per-document checks."""

    URL = "/api/v1/documents/bulk/"

    def setUp(self):
        super().setUp()
        from ..collections_app.models import Collection, CollectionShare
        self.Collection = Collection
        self.CollectionShare = CollectionShare
        self.other = User.objects.create_user(username="bulk_other", email="x@univ.edu", password="pw123456")
        self.parent = Collection.objects.create(owner=self.owner, name="Parent")
        self.child = Collection.objects.create(owner=self.owner, name="Child", parent=self.parent)
        self.mine = [Document.objects.create(owner=self.owner, title=f"Mine {i}") for i in range(3)]
        self.foreign = Document.objects.create(owner=self.other, title="Not shared")
        self.shared_edit = Document.objects.create(owner=self.other, title="Shared EDIT")
        DocumentShare.objects.create(document=self.shared_edit, shared_with_user=self.owner, permission="EDIT")
        self.shared_view = Document.objects.create(owner=self.other, title="Shared VIEW")
        DocumentShare.objects.create(document=self.shared_view, shared_with_user=self.owner, permission="VIEW")

    def _bulk(self, payload):
        return self.client.post(self.URL, payload, format="json")

    def _failed_reasons(self, resp):
        return {f["id"]: f["reason"] for f in resp.data["failed"]}

    def test_move_into_nested_collection_with_partial_failures(self):
        ids = [d.id for d in self.mine] + [self.foreign.id, self.shared_edit.id, self.shared_view.id]
        resp = self._bulk({"action": "move", "ids": ids, "collection_id": self.child.id})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Changing a document's collection is owner-only (it could expose the document
        # through the target collection's shares), so the EDIT share is refused too.
        self.assertEqual(sorted(resp.data["succeeded"]), sorted(d.id for d in self.mine))
        self.assertEqual(
            self._failed_reasons(resp),
            {
                self.foreign.id: "not_found",
                self.shared_edit.id: "permission_denied",
                self.shared_view.id: "permission_denied",
            },
        )
        for d in self.mine:
            d.refresh_from_db()
            self.assertEqual(d.primary_collection_id, self.child.id)
        self.shared_view.refresh_from_db()
        self.assertIsNone(self.shared_view.primary_collection_id)

    def test_move_into_someone_elses_collection_is_forbidden(self):
        theirs = self.Collection.objects.create(owner=self.other, name="Theirs")
        resp = self._bulk({"action": "move", "ids": [self.mine[0].id], "collection_id": theirs.id})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.mine[0].refresh_from_db()
        self.assertIsNone(self.mine[0].primary_collection_id)

        # An EDIT share on the collection allows filing into it.
        self.CollectionShare.objects.create(collection=theirs, shared_with_user=self.owner, permission="EDIT")
        resp = self._bulk({"action": "move", "ids": [self.mine[0].id], "collection_id": theirs.id})
        self.assertEqual(resp.data["succeeded"], [self.mine[0].id])

    def test_patch_cannot_file_into_someone_elses_collection(self):
        theirs = self.Collection.objects.create(owner=self.other, name="Theirs")
        url = f"/api/v1/documents/{self.mine[0].id}/"
        resp = self.client.patch(url, {"primary_collection": theirs.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        resp = self.client.patch(url, {"primary_collection": self.child.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["primary_collection"], self.child.id)

    def test_remove_from_collection(self):
        Document.objects.filter(id__in=[d.id for d in self.mine]).update(primary_collection=self.child)
        resp = self._bulk({"action": "remove_from_collection", "ids": [d.id for d in self.mine]})
        self.assertEqual(len(resp.data["succeeded"]), 3)
        self.assertFalse(Document.objects.filter(primary_collection__isnull=False, owner=self.owner).exists())

    def test_trash_and_restore_are_owner_only(self):
        ids = [self.mine[0].id, self.mine[1].id, self.shared_edit.id]
        resp = self._bulk({"action": "trash", "ids": ids})
        self.assertEqual(sorted(resp.data["succeeded"]), sorted(ids[:2]))
        self.assertEqual(self._failed_reasons(resp), {self.shared_edit.id: "permission_denied"})
        self.assertEqual(Document.objects.filter(in_trash=True).count(), 2)

        resp = self._bulk({"action": "restore", "ids": ids[:2]})
        self.assertEqual(sorted(resp.data["succeeded"]), sorted(ids[:2]))
        self.assertFalse(Document.objects.filter(in_trash=True).exists())

    def test_add_tag(self):
        resp = self._bulk({"action": "add_tag", "ids": [self.mine[0].id, self.shared_view.id], "tag": " review "})
        self.assertEqual(resp.data["succeeded"], [self.mine[0].id])
        self.assertEqual(list(self.mine[0].tags.values_list("name", flat=True)), ["review"])
        self.assertEqual(self._bulk({"action": "add_tag", "ids": [self.mine[0].id], "tag": "  "}).status_code, 400)

    def test_delete_uses_full_cleanup(self):
        doc = self._doc_with_file(title="With file")
        path = doc.file.path
        self.assertTrue(os.path.exists(path))
        ids = [doc.id, self.mine[0].id, self.shared_edit.id]
        with patch("apps.documents.views.delete_document_qdrant_data") as qdrant_delete, \
             patch("apps.documents.views.evict_rag_instance") as evict:
            resp = self._bulk({"action": "delete", "ids": ids})
        self.assertEqual(sorted(resp.data["succeeded"]), sorted([doc.id, self.mine[0].id]))
        self.assertEqual(self._failed_reasons(resp), {self.shared_edit.id: "permission_denied"})
        self.assertEqual(sorted(c.args[0] for c in qdrant_delete.call_args_list), sorted([doc.id, self.mine[0].id]))
        self.assertEqual(evict.call_count, 2)
        self.assertFalse(os.path.exists(path))
        self.assertFalse(Document.objects.filter(id__in=[doc.id, self.mine[0].id]).exists())
        self.assertTrue(Document.objects.filter(id=self.shared_edit.id).exists())

    def test_invalid_requests(self):
        for payload in (
            {"action": "explode", "ids": [self.mine[0].id]},
            {"action": "trash", "ids": []},
            {"action": "trash", "ids": "1,2"},
            {"action": "trash", "ids": ["abc"]},
            {"action": "move", "ids": [self.mine[0].id]},
            {"action": "move", "ids": [self.mine[0].id], "collection_id": 999999},
        ):
            self.assertEqual(self._bulk(payload).status_code, status.HTTP_400_BAD_REQUEST, payload)

    def test_tree_counts_are_direct_and_exclude_trash(self):
        # Two shares on the collection used to multiply the count through the join.
        self.CollectionShare.objects.create(collection=self.child, shared_with_user=self.other, permission="VIEW")
        third = User.objects.create_user(username="bulk_third", email="t@univ.edu", password="pw123456")
        self.CollectionShare.objects.create(collection=self.child, shared_with_user=third, permission="VIEW")
        Document.objects.filter(id__in=[self.mine[0].id, self.mine[1].id]).update(primary_collection=self.child)
        Document.objects.filter(id=self.mine[2].id).update(primary_collection=self.child, in_trash=True)
        resp = self.client.get("/api/v1/collections/tree/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        parent = next(n for n in resp.data if n["id"] == self.parent.id)
        self.assertEqual(parent["document_count"], 0)
        self.assertEqual(parent["children"][0]["id"], self.child.id)
        self.assertEqual(parent["children"][0]["document_count"], 2)


# ---------------------------------------------------------------------------
# Regression tests for the backend bug-fix / security / performance pass (2026-11)
# ---------------------------------------------------------------------------

class _SharedFixture(_MediaTestCase):
    """Owner + viewer/commenter/editor shares on one document, plus an outsider."""

    def setUp(self):
        super().setUp()
        from ..collections_app.models import Collection, CollectionShare
        self.Collection = Collection
        self.CollectionShare = CollectionShare
        self.viewer = User.objects.create_user(username="fx_viewer", email="fx_viewer@univ.edu", password="pw123456")
        self.commenter = User.objects.create_user(username="fx_commenter", email="fx_commenter@univ.edu", password="pw123456")
        self.editor = User.objects.create_user(username="fx_editor", email="fx_editor@univ.edu", password="pw123456")
        self.outsider = User.objects.create_user(username="fx_outsider", email="fx_outsider@univ.edu", password="pw123456")
        self.doc = self._doc_with_file(title="Shared paper")
        for user, perm in ((self.viewer, "VIEW"), (self.commenter, "COMMENT"), (self.editor, "EDIT")):
            DocumentShare.objects.create(document=self.doc, shared_with_user=user, permission=perm)

    def _as(self, user):
        self.client.force_authenticate(user=user)
        return self.client


class CollectionPermissionTests(_SharedFixture):
    def setUp(self):
        super().setUp()
        self.col = self.Collection.objects.create(owner=self.owner, name="Owned")
        for user, perm in ((self.viewer, "VIEW"), (self.editor, "EDIT")):
            self.CollectionShare.objects.create(collection=self.col, shared_with_user=user, permission=perm)
        self.url = f"/api/v1/collections/{self.col.id}/"

    def test_shared_users_cannot_rename_move_or_delete(self):
        other = self.Collection.objects.create(owner=self.editor, name="Editor collection")
        for user in (self.viewer, self.editor):
            c = self._as(user)
            self.assertEqual(c.get(self.url).status_code, status.HTTP_200_OK)
            self.assertEqual(c.patch(self.url, {"name": "Hacked"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(c.put(self.url, {"name": "Hacked"}, format="json").status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(c.delete(self.url).status_code, status.HTTP_403_FORBIDDEN)
            self.assertEqual(c.get(f"{self.url}shares/").status_code, status.HTTP_403_FORBIDDEN)
        resp = self._as(self.editor).patch(self.url, {"parent": other.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.col.refresh_from_db()
        self.assertEqual(self.col.name, "Owned")
        self.assertIsNone(self.col.parent_id)

        c = self._as(self.owner)
        self.assertEqual(c.patch(self.url, {"name": "Renamed"}, format="json").status_code, status.HTTP_200_OK)
        self.assertEqual(c.delete(self.url).status_code, status.HTTP_204_NO_CONTENT)

    def test_parent_must_be_usable_and_not_a_cycle(self):
        child = self.Collection.objects.create(owner=self.owner, name="Child", parent=self.col)
        grandchild = self.Collection.objects.create(owner=self.owner, name="Grandchild", parent=child)
        foreign = self.Collection.objects.create(owner=self.outsider, name="Private")
        c = self._as(self.owner)
        for parent in (self.col, child, grandchild):
            resp = c.patch(self.url, {"parent": parent.id}, format="json")
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, parent.name)
        self.assertEqual(c.post("/api/v1/collections/", {"name": "Sneaky", "parent": foreign.id}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        # An EDIT share on the parent allows a subcollection under it; a VIEW share does not.
        self.assertEqual(self._as(self.editor).post("/api/v1/collections/", {"name": "Sub", "parent": self.col.id},
                                                    format="json").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self._as(self.viewer).post("/api/v1/collections/", {"name": "Sub", "parent": self.col.id},
                                                    format="json").status_code, status.HTTP_400_BAD_REQUEST)
        # Moving a collection under an unrelated collection of one's own still works.
        sibling = self.Collection.objects.create(owner=self.owner, name="Sibling")
        self.assertEqual(self._as(self.owner).patch(f"/api/v1/collections/{child.id}/", {"parent": sibling.id},
                                                    format="json").status_code, status.HTTP_200_OK)


class ShareCreationTests(_SharedFixture):
    def test_document_share_validation_and_upsert(self):
        url = f"/api/v1/documents/{self.doc.id}/shares/"
        c = self._as(self.owner)
        self.assertEqual(c.post(url, {"permission": "VIEW"}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(c.post(url, {"shared_with_email": self.owner.email}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(c.post(url, {"shared_with_email": "nobody@univ.edu"}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(c.post(url, {"shared_with_email": self.outsider.email, "permission": "ADMIN"},
                                format="json").status_code, status.HTTP_400_BAD_REQUEST)
        resp = c.post(url, {"shared_with_email": self.outsider.email.upper(), "permission": "VIEW"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # Sharing again changes the level instead of crashing on the unique constraint.
        resp = c.post(url, {"shared_with_email": self.outsider.email, "permission": "EDIT"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(DocumentShare.objects.get(document=self.doc, shared_with_user=self.outsider).permission, "EDIT")
        self.assertEqual(c.delete(f"{url}abc/").status_code, status.HTTP_404_NOT_FOUND)

    def test_collection_share_validation_and_upsert(self):
        col = self.Collection.objects.create(owner=self.owner, name="C")
        url = f"/api/v1/collections/{col.id}/shares/"
        c = self._as(self.owner)
        self.assertEqual(c.post(url, {}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(c.post(url, {"shared_with_email": self.owner.email}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(c.post(url, {"shared_with_email": self.viewer.email}, format="json").status_code,
                         status.HTTP_201_CREATED)
        self.assertEqual(c.post(url, {"shared_with_email": self.viewer.email, "permission": "COMMENT"},
                                format="json").status_code, status.HTTP_200_OK)
        self.assertEqual(self.CollectionShare.objects.get(collection=col).permission, "COMMENT")
        self.assertEqual(c.delete(f"{url}abc/").status_code, status.HTTP_404_NOT_FOUND)


class DocumentUpdateRuleTests(_SharedFixture):
    def test_trashed_document_can_be_restored_and_deleted(self):
        Document.objects.filter(id=self.doc.id).update(in_trash=True)
        resp = self.client.post(f"/api/v1/documents/{self.doc.id}/toggle-trash/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(resp.data["in_trash"])
        Document.objects.filter(id=self.doc.id).update(in_trash=True)
        self.assertEqual(self.client.get("/api/v1/documents/").data, [])  # the list still hides Trash
        with patch("apps.documents.views.delete_document_qdrant_data"), patch("apps.documents.views.evict_rag_instance"):
            self.assertEqual(self.client.delete(f"/api/v1/documents/{self.doc.id}/").status_code,
                             status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=self.doc.id).exists())

    def test_edit_share_cannot_change_owner_only_fields(self):
        mine = self.Collection.objects.create(owner=self.editor, name="Editor own")
        url = f"/api/v1/documents/{self.doc.id}/"
        c = self._as(self.editor)
        for payload in ({"in_trash": True}, {"is_duplicate": True}, {"primary_collection": mine.id}):
            self.assertEqual(c.patch(url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN, payload)
        resp = c.patch(url, {"file": SimpleUploadedFile("x.pdf", PDF_BYTES, content_type="application/pdf")},
                       format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        # Unchanged values (a client re-sending the whole form) and plain metadata are fine.
        resp = c.patch(url, {"title": "Edited", "in_trash": False, "primary_collection": None}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.title, "Edited")
        self.assertFalse(self.doc.in_trash)
        self.trigger.assert_not_called()
        # The owner may change them.
        self.assertEqual(self._as(self.owner).patch(url, {"is_duplicate": True}, format="json").status_code,
                         status.HTTP_200_OK)

    def test_replacing_pdf_removes_old_file(self):
        old_path = self.doc.file.path
        with patch("apps.documents.views.evict_rag_instance"):
            resp = self.client.patch(
                f"/api/v1/documents/{self.doc.id}/",
                {"file": SimpleUploadedFile("v2.pdf", PDF_BYTES + b" v2", content_type="application/pdf")},
                format="multipart",
            )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.doc.refresh_from_db()
        self.assertTrue(os.path.exists(self.doc.file.path))
        self.assertFalse(os.path.exists(old_path))

    def test_non_numeric_query_params_are_400(self):
        self.assertEqual(self.client.get("/api/v1/documents/?collection_id=abc").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get(f"/api/v1/documents/{self.doc.id}/annotations/?page=x").status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.get("/api/v1/notes/?document_id=x").status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_long_fields_missing_file_and_author_order(self):
        from .models import Author, DocumentAuthor
        doc = Document.objects.create(owner=self.owner, title="T" * 500, short_title="S" * 255, citation_key="k" * 100)
        doc.file.name = "documents/missing.pdf"
        doc.save()
        for order, last in ((1, "Zed"), (2, "Alpha")):
            DocumentAuthor.objects.create(document=doc, author=Author.objects.create(last_name=last), author_order=order)
        resp = self.client.post(f"/api/v1/documents/{doc.id}/duplicate/")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        clone = Document.objects.get(id=resp.data["id"])
        self.assertEqual(len(clone.title), 500)
        self.assertEqual(len(clone.citation_key), 100)
        self.assertFalse(clone.file)
        self.assertEqual(
            list(clone.documentauthor_set.order_by("author_order").values_list("author__last_name", flat=True)),
            ["Zed", "Alpha"],
        )
        self.trigger.assert_not_called()


class RelatedAndChunksTests(_SharedFixture):
    def test_related_hides_inaccessible_and_validates_input(self):
        private = Document.objects.create(owner=self.owner, title="Owner private paper")
        url = f"/api/v1/documents/{self.doc.id}/related/"
        c = self._as(self.owner)
        self.assertEqual(c.post(url, {"related_document_id": private.id}, format="json").status_code, status.HTTP_201_CREATED)
        self.assertEqual([d["id"] for d in c.get(url).data], [private.id])
        # The viewer can open the shared document but not the owner's private one.
        self.assertEqual(self._as(self.viewer).get(url).data, [])

        c = self._as(self.owner)
        self.assertEqual(c.post(url, {"related_document_id": self.doc.id}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        self.assertEqual(c.post(url, {"related_document_id": "abc"}, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        other = Document.objects.create(owner=self.owner, title="Other")
        self.assertEqual(c.post(url, {"related_document_id": other.id, "relation_type": "x" * 51},
                                format="json").status_code, status.HTTP_400_BAD_REQUEST)

    def test_chunk_parameters_validated(self):
        doc = Document.objects.create(owner=self.owner, title="T", extra="Some abstract text " * 30)
        base = f"/api/v1/documents/{doc.id}/chunks/?strategy=section_overlap"
        for params in ("&max_tokens=0", "&max_tokens=100000", "&max_tokens=50&overlap=50", "&overlap=-1"):
            resp = self.client.get(base + params)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, params)
        self.assertEqual(self.client.get(base + "&max_tokens=20&overlap=5").status_code, status.HTTP_200_OK)


class AnnotationRouterTests(_SharedFixture):
    PAYLOAD = {"page_number": 1, "type": "highlight", "color": "#ffeb3b", "rects": [], "selected_text": "x"}

    def test_create_via_router_requires_comment(self):
        url = "/api/v1/annotations/"
        payload = dict(self.PAYLOAD, document=self.doc.id)
        self.assertEqual(self._as(self.viewer).post(url, payload, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self._as(self.outsider).post(url, payload, format="json").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self._as(self.commenter).post(url, self.PAYLOAD, format="json").status_code,
                         status.HTTP_400_BAD_REQUEST)
        resp = self._as(self.commenter).post(url, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        anno = Annotation.objects.get(id=resp.data["id"])
        self.assertEqual((anno.document_id, anno.user_id), (self.doc.id, self.commenter.id))

    def test_edit_author_only_delete_author_or_owner(self):
        anno = Annotation.objects.create(document=self.doc, user=self.commenter, comment="mine")
        url = f"/api/v1/annotations/{anno.id}/"
        # The document owner sees it but cannot edit someone else's annotation.
        self.assertEqual(self._as(self.owner).patch(url, {"comment": "owner edit"}, format="json").status_code,
                         status.HTTP_403_FORBIDDEN)
        self.assertEqual(self._as(self.commenter).patch(url, {"comment": "edited"}, format="json").status_code,
                         status.HTTP_200_OK)
        # After the share is downgraded to VIEW, the author can no longer edit.
        DocumentShare.objects.filter(document=self.doc, shared_with_user=self.commenter).update(permission="VIEW")
        self.assertEqual(self._as(self.commenter).patch(url, {"comment": "again"}, format="json").status_code,
                         status.HTTP_403_FORBIDDEN)
        anno.refresh_from_db()
        self.assertEqual(anno.comment, "edited")
        # The document owner may delete (moderation).
        self.assertEqual(self._as(self.owner).delete(url).status_code, status.HTTP_204_NO_CONTENT)
        # Another collaborator cannot even see someone else's annotation through the router.
        other = Annotation.objects.create(document=self.doc, user=self.commenter)
        self.assertEqual(self._as(self.editor).delete(f"/api/v1/annotations/{other.id}/").status_code,
                         status.HTTP_404_NOT_FOUND)
        self.assertEqual(self._as(self.commenter).delete(f"/api/v1/annotations/{other.id}/").status_code,
                         status.HTTP_204_NO_CONTENT)


class TagVisibilityTests(_SharedFixture):
    def test_tags_limited_to_accessible_documents(self):
        from .models import Tag
        self.doc.tags.add(Tag.objects.create(name="shared-tag"))
        secret = Document.objects.create(owner=self.outsider, title="Secret")
        secret.tags.add(Tag.objects.create(name="secret-project"))

        def names(user):
            data = self._as(user).get("/api/v1/tags/").data
            rows = data["results"] if isinstance(data, dict) else data
            return {t["name"] for t in rows}

        self.assertEqual(names(self.viewer), {"shared-tag"})
        self.assertIn("secret-project", names(self.outsider))
        self.assertNotIn("secret-project", names(self.owner))


class ProtectedFileTests(_SharedFixture):
    def test_file_endpoint_permissions(self):
        url = f"/api/v1/documents/{self.doc.id}/file/"
        resp = self._as(self.owner).get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp["Content-Disposition"].startswith("inline"))
        # Consume the stream (the test client then closes it safely; an explicit close()
        # would fire request_finished and close the test DB connection).
        self.assertEqual(b"".join(resp.streaming_content), PDF_BYTES)
        resp = self._as(self.viewer).get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(resp.streaming_content), PDF_BYTES)
        self.assertEqual(self._as(self.outsider).get(url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(APIClient().get(url).status_code, status.HTTP_401_UNAUTHORIZED)

        no_file = Document.objects.create(owner=self.owner, title="Metadata only")
        self.assertEqual(self._as(self.owner).get(f"/api/v1/documents/{no_file.id}/file/").status_code,
                         status.HTTP_404_NOT_FOUND)

    def test_file_url_points_to_api_and_media_not_routed(self):
        from django.urls import Resolver404, resolve
        resp = self._as(self.owner).get(f"/api/v1/documents/{self.doc.id}/")
        self.assertTrue(resp.data["file_url"].endswith(f"/api/v1/documents/{self.doc.id}/file/"))
        listed = self.client.get("/api/v1/documents/").data
        self.assertTrue(listed[0]["file_url"].endswith(f"/api/v1/documents/{self.doc.id}/file/"))
        with self.assertRaises(Resolver404):
            resolve(f"/media/{self.doc.file.name}")
        self.assertEqual(self.client.get(f"/media/{self.doc.file.name}").status_code, status.HTTP_404_NOT_FOUND)


class RagStatusAndReadinessTests(_SharedFixture):
    def test_batched_rag_status(self):
        secret = Document.objects.create(owner=self.outsider, title="Secret", rag_status="FAILED")
        url = "/api/v1/documents/rag-status/"
        resp = self._as(self.viewer).get(f"{url}?ids={self.doc.id},{secret.id},999999")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [{"id": self.doc.id, "rag_status": "INDEXED"}])
        for query in ("", "?ids=", "?ids=1,x", "?ids=" + ",".join(str(i) for i in range(101))):
            self.assertEqual(self.client.get(url + query).status_code, status.HTTP_400_BAD_REQUEST, query)

    def test_chat_and_summary_409_while_pending_with_file(self):
        Document.objects.filter(id=self.doc.id).update(rag_status="PENDING")
        with patch("apps.documents.views.query_document") as q, patch("apps.documents.views.summarize_document") as s:
            r1 = self.client.post(f"/api/v1/documents/{self.doc.id}/chat/", {"question": "Q?"}, format="json")
            r2 = self.client.post(f"/api/v1/documents/{self.doc.id}/summarize/", {}, format="json")
        for resp in (r1, r2):
            self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
            self.assertEqual(resp.data["code"], "indexing")
        q.assert_not_called()
        s.assert_not_called()

    def test_default_reindex_is_queued(self):
        url = f"/api/v1/documents/{self.doc.id}/reindex/"
        with patch("apps.documents.views.reindex_document") as reindex, \
             patch("apps.documents.views.evict_rag_instance") as evict:
            resp = self.client.post(url, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(resp.data["status"], "PENDING")
        reindex.assert_not_called()
        evict.assert_called_once_with(self.doc.id)
        self.trigger.assert_called_once()
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.rag_status, "PENDING")

        Document.objects.filter(id=self.doc.id).update(rag_status="INDEXING")
        self.assertEqual(self.client.post(url, {}, format="json").status_code, status.HTTP_409_CONFLICT)

    def test_chat_is_throttled(self):
        from django.core.cache import cache
        from rest_framework.throttling import ScopedRateThrottle
        cache.clear()
        self.addCleanup(cache.clear)
        with patch.object(ScopedRateThrottle, "THROTTLE_RATES", {"chat": "2/min"}), \
             patch("apps.documents.views.query_document", return_value={"answer": "ok"}):
            codes = [
                self.client.post(f"/api/v1/documents/{self.doc.id}/chat/", {"question": "Q?"}, format="json").status_code
                for _ in range(3)
            ]
        self.assertEqual(codes, [200, 200, 429])


class MetadataEndpointTests(_MediaTestCase):
    def test_metadata_endpoints_require_authentication(self):
        anon = APIClient()
        self.assertEqual(anon.post("/api/v1/metadata/lookup-doi/", {"doi": "10.1/x"}, format="json").status_code,
                         status.HTTP_401_UNAUTHORIZED)
        upload = SimpleUploadedFile("p.pdf", PDF_BYTES, content_type="application/pdf")
        self.assertEqual(anon.post("/api/v1/metadata/extract-pdf/", {"file": upload}, format="multipart").status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_doi_must_be_a_short_string(self):
        with patch("apps.documents.views.fetch_metadata_from_doi") as fetch:
            for doi in (42, ["10.1/x"], "x" * 300):
                resp = self.client.post("/api/v1/metadata/lookup-doi/", {"doi": doi}, format="json")
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, doi)
            fetch.assert_not_called()

    def test_extract_size_cap_and_first_pages_only(self):
        import pymupdf
        upload = SimpleUploadedFile("p.pdf", PDF_BYTES, content_type="application/pdf")
        with patch("apps.documents.views.MAX_UPLOAD_BYTES", 10):
            resp = self.client.post("/api/v1/metadata/extract-pdf/", {"file": upload}, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        pdf = pymupdf.open()
        for _ in range(12):
            pdf.new_page()
        data = pdf.tobytes()
        pdf.close()
        seen = {}

        def fake_extract(path):
            with pymupdf.open(path) as d:
                seen["pages"] = d.page_count
            return {"title": "T", "authors": []}

        with patch("apps.documents.views.extract_metadata_from_pdf", side_effect=fake_extract):
            resp = self.client.post("/api/v1/metadata/extract-pdf/",
                                    {"file": SimpleUploadedFile("long.pdf", data, content_type="application/pdf")},
                                    format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(seen["pages"], 5)
