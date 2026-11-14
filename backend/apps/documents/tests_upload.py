"""
Tests for document create/update input cleaning and atomicity (DocumentCreateUpdateSerializer)
and for the test-run settings isolation (MEDIA_ROOT / QDRANT_STORAGE_PATH in a temp dir).

Complements UploadTitleTests.test_upload_with_overlong_extracted_names_succeeds and
DocumentUpdateRuleTests in tests_app.py; reuses their fixtures.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Author, Document, DocumentAuthor, Domain, Tag
from .serializers import DocumentCreateUpdateSerializer
from .tests_app import PDF_BYTES, User, _MediaTestCase

clean = DocumentCreateUpdateSerializer._clean_names

FIRST_MAX = Author._meta.get_field("first_name").max_length   # 150
LAST_MAX = Author._meta.get_field("last_name").max_length     # 150
TAG_MAX = Tag._meta.get_field("name").max_length              # 100
DOMAIN_MAX = Domain._meta.get_field("name").max_length        # 150


def _media_files(root):
    """Relative paths of every file under root (empty set when root does not exist)."""
    found = set()
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            found.add(os.path.relpath(os.path.join(dirpath, f), root))
    return found


def _norm(path):
    return os.path.normcase(os.path.realpath(str(path)))


def _is_under(path, root):
    path, root = _norm(path), _norm(root)
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # different drives on Windows
        return False


# ---------------------------------------------------------------------------
# _clean_names unit cases
# ---------------------------------------------------------------------------

class CleanNamesTests(SimpleTestCase):
    def test_whitespace_collapsed_and_trimmed(self):
        self.assertEqual(clean(["  Deep \n\t Learning  ", "a b"], 100), ["Deep Learning", "a b"])

    def test_blank_and_whitespace_only_dropped(self):
        self.assertEqual(clean(["", "   ", "\n\t", "OCR"], 100), ["OCR"])
        self.assertEqual(clean([], 100), [])
        self.assertEqual(clean(None, 100), [])

    def test_dedupe_is_exact_and_case_sensitive(self):
        # Exact duplicates (after whitespace collapse) are dropped; different case is kept.
        # This matches the database: Tag.name is unique case-sensitively on PostgreSQL, so
        # "OCR" and "ocr" are two distinct tags and no IntegrityError can occur.
        self.assertEqual(clean(["OCR", " OCR ", "O C R", "ocr", "OCR"], 100), ["OCR", "O C R", "ocr"])

    def test_order_preserved(self):
        self.assertEqual(clean(["c", "a", "b", "a", "c"], 100), ["c", "a", "b"])

    def test_truncation_exactly_at_max_length(self):
        self.assertEqual(clean(["x" * 100], 100), ["x" * 100])
        self.assertEqual(clean(["x" * 101], 100), ["x" * 100])
        self.assertEqual(clean(["x" * 99], 100), ["x" * 99])

    def test_truncation_happens_after_collapse_and_trailing_space_stripped(self):
        # 99 chars + many spaces + more text: collapse first, cut at 100 lands on the space.
        name = "a" * 99 + "      " + "tail"
        self.assertEqual(clean([name], 100), ["a" * 99])

    def test_names_equal_after_truncation_are_deduplicated(self):
        self.assertEqual(clean(["x" * 120, "x" * 110, "x" * 100], 100), ["x" * 100])

    def test_vietnamese_unicode(self):
        names = ["Nguyễn Văn An", "Trần  Thị\nBích Ngọc", "Nguyễn Văn An", "Xử lý ngôn ngữ tự nhiên"]
        self.assertEqual(clean(names, 100), ["Nguyễn Văn An", "Trần Thị Bích Ngọc", "Xử lý ngôn ngữ tự nhiên"])
        # Truncation counts characters, not bytes.
        self.assertEqual(clean(["ễ" * 150], 100), ["ễ" * 100])

    def test_non_string_values_are_stringified(self):
        self.assertEqual(clean([2024, 1.5], 100), ["2024", "1.5"])


class AuthorNameValidationTests(SimpleTestCase):
    def _v(self, names):
        return DocumentCreateUpdateSerializer().validate_author_names(names)

    def test_single_long_token_becomes_capped_last_name(self):
        self.assertEqual(self._v(["B" * 400]), ["B" * LAST_MAX])

    def test_long_first_and_last_both_capped(self):
        # The whole name is first cut to 300 chars (= 150 + 150), then each part to its column.
        (out,) = self._v(["A" * 200 + " " + "B" * 200])
        first, last = out.rsplit(" ", 1)
        self.assertEqual(first, "A" * FIRST_MAX)
        self.assertEqual(last, "B" * 99)  # only 99 B's survive the 300-char cut
        (out,) = self._v(["Al " + "B" * 200])
        self.assertEqual(out, "Al " + "B" * LAST_MAX)

    def test_particles_stay_in_first_name(self):
        # The last word is the last name; particles ("van", "de la") go to the first name.
        self.assertEqual(self._v(["Ludwig van Beethoven", "Juan de la Cruz"]),
                         ["Ludwig van Beethoven", "Juan de la Cruz"])


# ---------------------------------------------------------------------------
# API: create / update cleaning
# ---------------------------------------------------------------------------

class DocumentNameFieldsApiTests(_MediaTestCase):
    def _create(self, **extra):
        payload = {"title": "Clean Names Paper"}
        payload.update(extra)
        return self.client.post("/api/v1/documents/", payload, format="json")

    def _authors(self, doc_id):
        return list(
            DocumentAuthor.objects.filter(document_id=doc_id).order_by("author_order")
            .values_list("author__first_name", "author__last_name")
        )

    def test_author_split_and_order_preserved_on_create_and_update(self):
        resp = self._create(author_names=["Zoe Zimmer", "Ludwig van Beethoven", "Plato", "Nguyễn Văn An"])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        doc_id = resp.data["id"]
        self.assertEqual(self._authors(doc_id), [
            ("Zoe", "Zimmer"), ("Ludwig van", "Beethoven"), ("", "Plato"), ("Nguyễn Văn", "An"),
        ])
        self.assertEqual([a["full_name"] for a in resp.data["authors"]][0], str(Author.objects.get(last_name="Zimmer")))

        resp = self.client.patch(f"/api/v1/documents/{doc_id}/",
                                 {"author_names": ["Plato", "Ada Lovelace", "Zoe Zimmer"]}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(self._authors(doc_id), [("", "Plato"), ("Ada", "Lovelace"), ("Zoe", "Zimmer")])

    def test_long_author_parts_capped_in_database(self):
        resp = self._create(author_names=["C" * 500, "A" * 200 + " " + "B" * 99, "Al " + "D" * 200])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(self._authors(resp.data["id"]), [
            ("", "C" * LAST_MAX), ("A" * FIRST_MAX, "B" * 99), ("Al", "D" * LAST_MAX),
        ])

    def test_authors_identical_after_capping_do_not_500(self):
        # Regression (was a bug; serializers.py validate_author_names, ~line 217-225): dedupe runs in
        # _clean_names *before* the first/last name parts are capped, so two different long
        # names that become identical after capping both survive. _set_m2m then resolves both
        # to the same Author and DocumentAuthor's unique_together(document, author) raises
        # IntegrityError -> HTTP 500 (same class of failure the change was meant to remove).
        resp = self._create(author_names=["A" * 200 + " Smith", "A" * 180 + " Smith"])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(self._authors(resp.data["id"])), 1)

    def test_capped_first_name_has_no_trailing_space(self):
        # Regression (was a minor bug; serializers.py validate_author_names, ~line 222): the first-name part is
        # cut at 150 chars without .strip(), so a cut that lands on a space stores
        # first_name with a trailing space (e.g. "xxx...x ").
        resp = self._create(author_names=["x" * 149 + " Middle Last"])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        ((first, last),) = self._authors(resp.data["id"])
        self.assertEqual(last, "Last")
        self.assertEqual(first, first.strip())

    def test_tag_and_domain_caps_apply_on_patch(self):
        doc = Document.objects.create(owner=self.owner, title="Patch me")
        resp = self.client.patch(f"/api/v1/documents/{doc.id}/", {
            "tag_names": ["t" * 300, "Ok\ntag", "Ok tag"],
            "domain_names": ["d" * 300, "  "],
        }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(sorted(doc.tags.values_list("name", flat=True)), sorted(["t" * TAG_MAX, "Ok tag"]))
        self.assertEqual(list(doc.domains.values_list("name", flat=True)), ["d" * DOMAIN_MAX])

    def test_tags_exactly_at_limit_kept_unchanged(self):
        resp = self._create(tag_names=["t" * TAG_MAX], domain_names=["d" * DOMAIN_MAX])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        doc = Document.objects.get(id=resp.data["id"])
        self.assertEqual(list(doc.tags.values_list("name", flat=True)), ["t" * TAG_MAX])
        self.assertEqual(list(doc.domains.values_list("name", flat=True)), ["d" * DOMAIN_MAX])

    def test_case_variants_become_distinct_tags(self):
        resp = self._create(tag_names=["OCR", "ocr"])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(sorted(resp.data["tags"]), ["OCR", "ocr"])

    def test_empty_list_and_blank_only_list_clear_on_patch(self):
        resp = self._create(author_names=["Ada Lovelace"], tag_names=["a", "b"], domain_names=["CS"])
        doc_id = resp.data["id"]
        url = f"/api/v1/documents/{doc_id}/"
        # Blank-only lists clean to [] and clear the relation (not a 400).
        resp = self.client.patch(url, {"tag_names": ["", "  ", "\n"], "domain_names": []}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.tags.count(), 0)
        self.assertEqual(doc.domains.count(), 0)
        self.assertEqual(doc.authors.count(), 1)  # field not sent -> untouched
        resp = self.client.patch(url, {"author_names": []}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(doc.authors.count(), 0)

    def test_patch_without_name_fields_leaves_relations(self):
        resp = self._create(author_names=["Ada Lovelace"], tag_names=["keep"])
        doc_id = resp.data["id"]
        resp = self.client.patch(f"/api/v1/documents/{doc_id}/", {"title": "Renamed"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        self.assertEqual(resp.data["tags"], ["keep"])
        self.assertEqual(len(resp.data["authors"]), 1)

    def test_multipart_repeated_keys_with_blanks(self):
        resp = self.client.post("/api/v1/documents/", {
            "title": "Multipart names",
            "author_names": ["Ada Lovelace", "", "Alan Turing"],
            "tag_names": ["", "x" * 150],
            "file": SimpleUploadedFile("names.pdf", PDF_BYTES, content_type="application/pdf"),
        }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(self._authors(resp.data["id"]), [("Ada", "Lovelace"), ("Alan", "Turing")])
        self.assertEqual(resp.data["tags"], ["x" * TAG_MAX])


class DocumentNameFieldsInvalidInputTests(_MediaTestCase):
    def _post(self, **fields):
        return self.client.post("/api/v1/documents/", {"title": "Bad input", **fields}, format="json")

    def test_non_list_is_400_with_field_message(self):
        for field in ("author_names", "tag_names", "domain_names"):
            for bad in ("OCR", {"a": 1}, 5):
                resp = self._post(**{field: bad})
                self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, (field, bad))
                self.assertIn(field, resp.data)
                self.assertIn("list", str(resp.data[field]).lower())
        self.assertEqual(Document.objects.count(), 0)

    def test_non_string_items_are_400_with_field_message(self):
        for bad in ([{"name": "x"}], [["nested"]], [True], [None]):
            resp = self._post(tag_names=bad)
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST, bad)
            self.assertIn("tag_names", resp.data)
        self.assertEqual(Document.objects.count(), 0)

    def test_numeric_items_are_accepted_as_strings(self):
        resp = self._post(tag_names=[2024, "2024"])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(resp.data["tags"], ["2024"])

    def test_null_list_is_400(self):
        resp = self._post(author_names=None)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("author_names", resp.data)

    def test_large_list_has_no_cap_but_is_deduplicated(self):
        # There is no list-length cap on these fields; a large, repetitive list is accepted
        # and collapsed to its distinct values.
        resp = self._post(tag_names=["dup"] * 2000 + [f"t{i}" for i in range(50)])
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(len(resp.data["tags"]), 51)


# ---------------------------------------------------------------------------
# Atomicity of create / update
# ---------------------------------------------------------------------------

class DocumentSaveAtomicityTests(_MediaTestCase):
    def setUp(self):
        super().setUp()
        # A failure inside the view must come back as a 500 response, not a raised exception.
        self.client.raise_request_exception = False

    def _failing_author_lookup(self):
        return patch.object(Author.objects, "get_or_create", side_effect=RuntimeError("boom"))

    def test_create_failure_leaves_no_document_row(self):
        with self._failing_author_lookup():
            resp = self.client.post("/api/v1/documents/", {
                "title": "Will fail", "author_names": ["Ada Lovelace"], "tag_names": ["new-tag"],
            }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(Document.objects.filter(title="Will fail").exists())
        self.assertEqual(DocumentAuthor.objects.count(), 0)
        self.assertFalse(Tag.objects.filter(name="new-tag").exists())
        self.trigger.assert_not_called()

    def test_create_failure_leaves_no_file_on_disk(self):
        # Regression (was a bug; serializers.py create, ~line 268-270): transaction.atomic() rolls back the
        # Document row, but FileField.pre_save has already written the PDF to MEDIA_ROOT
        # during Document.objects.create(); nothing deletes it on rollback, so an orphan
        # file stays in media/documents/ (no row references it any more).
        before = _media_files(settings.MEDIA_ROOT)
        with self._failing_author_lookup():
            resp = self.client.post("/api/v1/documents/", {
                "title": "Will fail with file",
                "author_names": ["Ada Lovelace"],
                "file": SimpleUploadedFile("orphan.pdf", PDF_BYTES, content_type="application/pdf"),
            }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(Document.objects.filter(title="Will fail with file").exists())
        self.assertEqual(_media_files(settings.MEDIA_ROOT), before)

    def test_update_failure_keeps_old_values(self):
        resp = self.client.post("/api/v1/documents/", {
            "title": "Original", "author_names": ["Ada Lovelace"], "tag_names": ["old"],
        }, format="json")
        doc_id = resp.data["id"]
        with self._failing_author_lookup():
            resp = self.client.patch(f"/api/v1/documents/{doc_id}/", {
                "title": "Changed", "author_names": ["Alan Turing"], "tag_names": ["new"],
            }, format="json")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.title, "Original")
        self.assertEqual([str(a) for a in doc.authors.all()], [str(Author.objects.get(last_name="Lovelace"))])
        self.assertEqual(list(doc.tags.values_list("name", flat=True)), ["old"])

    def test_update_failure_with_new_file_keeps_old_file_reference(self):
        doc = self._doc_with_file(title="Has file", name="keep.pdf")
        old_name, old_path = doc.file.name, doc.file.path
        with self._failing_author_lookup():
            resp = self.client.patch(f"/api/v1/documents/{doc.id}/", {
                "author_names": ["Alan Turing"],
                "file": SimpleUploadedFile("replacement.pdf", PDF_BYTES + b" v2", content_type="application/pdf"),
            }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        doc.refresh_from_db()
        self.assertEqual(doc.file.name, old_name)
        self.assertTrue(os.path.exists(old_path))
        self.trigger.assert_not_called()

    def test_update_failure_leaves_no_replacement_file_on_disk(self):
        # Regression (was a bug; serializers.py update, ~line 282-292): same as create - the replacement PDF is
        # written to MEDIA_ROOT by instance.save() inside the atomic block and is not removed
        # when the transaction rolls back.
        doc = self._doc_with_file(title="Has file", name="keep.pdf")
        before = _media_files(settings.MEDIA_ROOT)
        with self._failing_author_lookup():
            resp = self.client.patch(f"/api/v1/documents/{doc.id}/", {
                "author_names": ["Alan Turing"],
                "file": SimpleUploadedFile("replacement.pdf", PDF_BYTES + b" v2", content_type="application/pdf"),
            }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(_media_files(settings.MEDIA_ROOT), before)


# ---------------------------------------------------------------------------
# Test-run settings isolation (core/settings.py, `manage.py test` branch)
# ---------------------------------------------------------------------------

class TestSettingsIsolationTests(TestCase):
    def test_storage_paths_are_in_temp_dir_not_project_media(self):
        tmp = tempfile.gettempdir()
        real_media = os.path.join(settings.BASE_DIR, "media")
        for name in ("MEDIA_ROOT", "QDRANT_STORAGE_PATH"):
            value = getattr(settings, name)
            self.assertTrue(_is_under(value, tmp), f"{name}={value} not under {tmp}")
            self.assertFalse(_is_under(value, real_media), f"{name}={value} is under {real_media}")

    def test_online_metadata_lookup_disabled(self):
        self.assertIs(settings.METADATA_ONLINE_LOOKUP, False)

    def test_upload_without_override_writes_under_temp_media_root(self):
        # No override_settings here: exercises the MEDIA_ROOT that settings.py chose for tests.
        user = User.objects.create_user(username="iso_user", email="iso@univ.edu", password="pw123456")
        client = APIClient()
        client.force_authenticate(user=user)
        with patch("apps.documents.views.trigger_rag_ingestion"):
            resp = client.post("/api/v1/documents/", {
                "title": "Isolation Check Paper",
                "author_names": ["Ada Lovelace"],
                "file": SimpleUploadedFile("isolation.pdf", PDF_BYTES, content_type="application/pdf"),
            }, format="multipart")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        path = Document.objects.get(id=resp.data["id"]).file.path
        try:
            self.assertTrue(os.path.exists(path))
            self.assertTrue(_is_under(path, settings.MEDIA_ROOT))
            self.assertTrue(_is_under(path, tempfile.gettempdir()))
            self.assertFalse(_is_under(path, os.path.join(settings.BASE_DIR, "media")))
        finally:
            if os.path.exists(path):
                os.remove(path)
