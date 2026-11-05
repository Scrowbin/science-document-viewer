import logging
import os
import tempfile
import threading
from collections import OrderedDict
from typing import Any, Dict, List
from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.throttling import ScopedRateThrottle
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Document,
    DocumentAuthor,
    Tag,
    Domain,
    Annotation,
    Note,
    DocumentShare,
    RelatedDocument,
)
from ..collections_app.models import Collection
from .serializers import (
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentCreateUpdateSerializer,
    TagSerializer,
    DomainSerializer,
    AnnotationSerializer,
    NoteSerializer,
    DocumentShareSerializer,
)
from .permissions import (
    IsOwnerOrCollaborator,
    can_file_into_collection,
    has_document_permission,
    visible_documents_q,
)
from .services.crossref_service import fetch_metadata_from_doi
from .services.webhook_service import trigger_rag_ingestion
from .services.pdf_metadata_service import (
    apply_pdf_metadata_to_document,
    extract_metadata_from_pdf,
    is_raw_title,
)
from .services.chunking_utils import chunk_sections, extract_sections_from_pdf
from .services.chunkers import chunk_hierarchical
from .services.rag_service import (
    query_document,
    summarize_document,
    reindex_document,
    delete_document_qdrant_data,
    evict_rag_instance,
)

logger = logging.getLogger(__name__)

MAX_QUESTION_LENGTH = 2000
REINDEX_STRATEGIES = ("hierarchical", "section_overlap")
CHUNK_INSPECT_STRATEGIES = ("section", "section_token", "section_overlap", "hierarchical")
HIERARCHICAL_CHILD_TOKENS = 200
HIERARCHICAL_CHILD_OVERLAP = 40
CHUNK_INSPECT_MAX_TOKENS = 4000
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # FR-02
METADATA_PREVIEW_MAX_PAGES = 5  # title/authors/DOI/abstract live on the first pages
MAX_DOI_LENGTH = 255
RAG_STATUS_MAX_IDS = 100

# Fields only the document owner may change through PUT/PATCH (an EDIT share may edit metadata).
# Moving a document into another collection could expose it through that collection's shares.
OWNER_ONLY_FIELDS = ("primary_collection", "in_trash", "is_duplicate", "file")

# Bulk action -> minimum permission, mirroring the single-document actions in permissions.py.
BULK_ACTIONS = {
    "move": "OWNER",
    "remove_from_collection": "OWNER",
    "add_tag": "EDIT",
    "trash": "OWNER",
    "restore": "OWNER",
    "delete": "OWNER",
}
BULK_MAX_IDS = 500


def _parse_int(value, name):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError({name: "Must be an integer."})


def _schedule_ingestion(doc):
    """Marks a document PENDING and hands it to the background ingestion queue."""
    if not doc.file:
        return None
    if doc.rag_status != "PENDING":
        doc.rag_status = "PENDING"
        doc.save(update_fields=["rag_status"])
    return trigger_rag_ingestion(
        document_id=doc.id,
        file_path=doc.file.path,
        title=doc.title,
        owner_id=doc.owner_id,
        sync=getattr(settings, "RAG_INGESTION_SYNC", False),
    )


def _indexing_conflict_response():
    return Response(
        {"code": "indexing", "detail": "Document is still being indexed."},
        status=status.HTTP_409_CONFLICT,
    )


def _not_ready_response(doc):
    """409 while the document is being indexed or still waiting in the ingestion queue, so a
    chat/summary request never runs a full ingestion synchronously. None when ready."""
    if doc.rag_status == "INDEXING":
        return _indexing_conflict_response()
    if doc.rag_status == "PENDING" and doc.file:
        return Response(
            {"code": "indexing", "detail": "Document is waiting to be indexed. Try again shortly."},
            status=status.HTTP_409_CONFLICT,
        )
    return None


def _remove_file_if_unreferenced(file_name, exclude_id=None):
    """Deletes a stored PDF unless another Document still references it
    (duplicates created before files were copied share one file)."""
    if not file_name:
        return
    others = Document.objects.filter(file=file_name)
    if exclude_id is not None:
        others = others.exclude(id=exclude_id)
    if others.exists():
        return
    try:
        Document._meta.get_field("file").storage.delete(file_name)
    except Exception as e:
        logger.warning("Failed to remove physical file %r: %s", file_name, e)


def _delete_document_permanently(instance):
    """
    Permanent delete implementation matching thesis specification:
      1. Deletes that document's points in Qdrant (child vectors in doc_{id} and companion doc_{id}_parents)
      2. Evicts cached in-memory _rag_instances[doc_id]
      3. Deletes physical file in media/documents/ (unless another document still references it)
      4. Deletes PostgreSQL row (CASCADE to all relational tables)
    Shared by DELETE /documents/{id}/ and the bulk "delete" action.
    """
    doc_id = instance.id
    file_path = instance.file.path if instance.file else None

    # 1. Delete Qdrant vectors and companion parent collection
    try:
        delete_document_qdrant_data(doc_id)
    except Exception as e:
        logger.warning("Failed to delete Qdrant points for doc %s: %s", doc_id, e)

    # 2. Evict in-memory RAG instance
    try:
        evict_rag_instance(doc_id)
    except Exception as e:
        logger.warning("Failed to evict RAG instance for doc %s: %s", doc_id, e)

    # 3. Delete physical file in media/documents/, unless another document still
    #    references it (duplicates created before files were copied share one file)
    still_referenced = bool(instance.file) and Document.objects.filter(
        file=instance.file.name
    ).exclude(id=doc_id).exists()
    if file_path and not still_referenced and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning("Failed to remove physical file %s: %s", file_path, e)

    # 4. Delete PostgreSQL row (CASCADE)
    instance.delete()


def _owner_only_changes(instance, validated_data):
    """Names of OWNER_ONLY_FIELDS whose submitted value differs from the stored one."""
    changed = []
    for field in OWNER_ONLY_FIELDS:
        if field not in validated_data:
            continue
        new = validated_data[field]
        if field == "file":
            if new or bool(instance.file):
                changed.append(field)
        elif field == "primary_collection":
            if (new.id if new is not None else None) != instance.primary_collection_id:
                changed.append(field)
        elif new != getattr(instance, field):
            changed.append(field)
    return changed


def _truncate(value, field_name):
    max_length = Document._meta.get_field(field_name).max_length
    return value[:max_length] if value else value


# Small in-process LRU of extracted PDF sections for the chunk inspector, keyed by
# (document id, file name, size, mtime) so a replaced file is never served stale.
_SECTIONS_CACHE: "OrderedDict[tuple, List[Dict[str, Any]]]" = OrderedDict()
_SECTIONS_CACHE_SIZE = 8
_SECTIONS_CACHE_LOCK = threading.Lock()


def _cached_sections(doc):
    path = doc.file.path
    stat = os.stat(path)
    key = (doc.id, doc.file.name, stat.st_size, stat.st_mtime_ns)
    with _SECTIONS_CACHE_LOCK:
        if key in _SECTIONS_CACHE:
            _SECTIONS_CACHE.move_to_end(key)
            return _SECTIONS_CACHE[key]
    sections = extract_sections_from_pdf(path)
    with _SECTIONS_CACHE_LOCK:
        _SECTIONS_CACHE[key] = sections
        _SECTIONS_CACHE.move_to_end(key)
        while len(_SECTIONS_CACHE) > _SECTIONS_CACHE_SIZE:
            _SECTIONS_CACHE.popitem(last=False)
    return sections


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrCollaborator)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    # Set per action (chat/summarize use the 'chat' scope); declared so @action may override it.
    throttle_scope = None
    # Disable DRF's global PageNumberPagination for this endpoint.
    # The frontend loads the full document library and performs client-side
    # filtering/sorting. This is correct for the current documented UI behavior.
    # Re-evaluate when document collections become large or pagination/infinite
    # scrolling is introduced in the frontend.
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer
        if self.action in ("create", "update", "partial_update"):
            return DocumentCreateUpdateSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Document.objects.filter(visible_documents_q(user)).distinct()

        # Query Filters
        in_trash = self.request.query_params.get("in_trash")
        if in_trash is not None:
            queryset = queryset.filter(in_trash=in_trash.lower() in ("true", "1"))
        elif self.action == "list":
            # The list excludes Trash unless explicitly asked. Detail actions must still find
            # trashed documents (restore via toggle-trash, permanent delete from Trash).
            queryset = queryset.filter(in_trash=False)

        collection_id = self.request.query_params.get("collection_id")
        if collection_id:
            collection_id = _parse_int(collection_id, "collection_id")
            queryset = queryset.filter(
                Q(primary_collection_id=collection_id)
                | Q(collections__id=collection_id)
            )

        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(short_title__icontains=search)
                | Q(doi__icontains=search)
                | Q(authors__last_name__icontains=search)
                | Q(authors__first_name__icontains=search)
                | Q(tags__name__icontains=search)
            )

        section = self.request.query_params.get("section")
        if section == "recent":
            queryset = queryset.filter(last_read__isnull=False).order_by("-last_read")
        elif section == "publications":
            queryset = queryset.filter(is_publication=True)
        elif section == "duplicates":
            queryset = queryset.filter(is_duplicate=True)
        elif section == "unfiled":
            queryset = queryset.filter(primary_collection__isnull=True)

        queryset = queryset.select_related("owner", "primary_collection").prefetch_related("authors", "tags")
        if self.action != "list":  # only the detail serializer renders domains
            queryset = queryset.prefetch_related("domains")
        return queryset

    def perform_create(self, serializer):
        doc = serializer.save(owner=self.request.user)
        # If file was uploaded:
        if doc.file:
            # 1. Extract academic metadata (arXiv ID, DOI, or layout heuristic) only when the
            #    client did not already send previewed/confirmed metadata. The upload modal runs
            #    /metadata/extract-pdf/ first, so a second synchronous extraction is wasted work
            #    and could overwrite what the user confirmed.
            sent_authors = bool(serializer.validated_data.get("author_names"))
            if not sent_authors and is_raw_title(doc.title, doc.file.name):
                try:
                    apply_pdf_metadata_to_document(doc)
                except Exception as e:
                    logger.warning("PDF metadata extraction failed: %s", e)

            # 2. Trigger RAG background ingestion
            _schedule_ingestion(doc)

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance.owner_id != self.request.user.id:
            changed = _owner_only_changes(instance, serializer.validated_data)
            if changed:
                raise PermissionDenied(f"Only the document owner can change: {', '.join(changed)}.")

        old_file_name = instance.file.name if instance.file else ""
        doc = serializer.save()
        new_file_name = doc.file.name if doc.file else ""
        if "file" not in serializer.validated_data or new_file_name == old_file_name:
            return

        # The old PDF is no longer used by this document: drop it from disk unless shared.
        _remove_file_if_unreferenced(old_file_name, exclude_id=doc.id)
        try:
            evict_rag_instance(doc.id)
        except Exception as e:
            logger.warning("Failed to evict RAG instance for doc %s: %s", doc.id, e)

        if doc.file:
            # A new PDF replaces the old one: drop the stale in-memory index and re-ingest
            doc.file_size = doc.file.size
            doc.rag_status = "PENDING"
            doc.save(update_fields=["file_size", "rag_status"])
            _schedule_ingestion(doc)
        else:
            # The PDF was removed: its vectors describe a file that no longer exists
            try:
                delete_document_qdrant_data(doc.id)
            except Exception as e:
                logger.warning("Failed to delete Qdrant points for doc %s: %s", doc.id, e)
            doc.file_size = None
            doc.save(update_fields=["file_size"])

    def perform_destroy(self, instance):
        _delete_document_permanently(instance)

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        """
        Apply one action to many documents in a single request.

        Body: {"action": "move" | "remove_from_collection" | "trash" | "restore" | "delete" | "add_tag",
               "ids": [int, ...], "collection_id": int (move), "tag": str (add_tag)}
        Response 200: {"action", "succeeded": [id, ...], "failed": [{"id", "reason", "detail"}, ...]}
        Permissions follow the single-document actions: add_tag needs EDIT (like PATCH of tags);
        move / remove (changing primary_collection), trash / restore / delete are owner-only.
        """
        data = request.data if isinstance(request.data, dict) else {}
        action_name = data.get("action")
        if action_name not in BULK_ACTIONS:
            return Response(
                {"detail": f"action must be one of: {', '.join(sorted(BULK_ACTIONS))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_ids = data.get("ids")
        if not isinstance(raw_ids, list) or not raw_ids:
            return Response({"detail": "ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)
        if len(raw_ids) > BULK_MAX_IDS:
            return Response(
                {"detail": f"At most {BULK_MAX_IDS} documents per request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ids = list(dict.fromkeys(int(i) for i in raw_ids))
        except (TypeError, ValueError):
            return Response({"detail": "ids must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        collection = None
        if action_name == "move":
            try:
                collection = Collection.objects.get(id=int(data.get("collection_id")))
            except (TypeError, ValueError, Collection.DoesNotExist):
                return Response(
                    {"detail": "collection_id is not a valid collection."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not can_file_into_collection(request.user, collection):
                return Response(
                    {"detail": "You cannot add documents to this collection."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        tag = None
        if action_name == "add_tag":
            tag_name = data.get("tag")
            tag_name = tag_name.strip() if isinstance(tag_name, str) else ""
            if not tag_name or len(tag_name) > 100:
                return Response({"detail": "tag must be 1-100 characters."}, status=status.HTTP_400_BAD_REQUEST)
            tag, _ = Tag.objects.get_or_create(name=tag_name)

        user = request.user
        visible = {
            d.id: d
            for d in Document.objects.filter(
                visible_documents_q(user),
                id__in=ids,
            ).distinct().select_related("primary_collection")
        }
        required = BULK_ACTIONS[action_name]

        succeeded, failed = [], []
        for doc_id in ids:
            doc = visible.get(doc_id)
            if doc is None:
                failed.append({"id": doc_id, "reason": "not_found", "detail": "Document not found."})
                continue
            if not has_document_permission(user, doc, required):
                failed.append({"id": doc_id, "reason": "permission_denied", "detail": "Permission denied."})
                continue
            try:
                if action_name == "move":
                    if doc.primary_collection_id != collection.id:
                        doc.primary_collection = collection
                        doc.save(update_fields=["primary_collection", "date_modified"])
                elif action_name == "remove_from_collection":
                    if doc.primary_collection_id is not None:
                        doc.primary_collection = None
                        doc.save(update_fields=["primary_collection", "date_modified"])
                elif action_name in ("trash", "restore"):
                    target = action_name == "trash"
                    if doc.in_trash != target:
                        doc.in_trash = target
                        doc.save(update_fields=["in_trash"])
                elif action_name == "add_tag":
                    doc.tags.add(tag)
                elif action_name == "delete":
                    _delete_document_permanently(doc)
            except Exception as e:  # one bad document must not abort the rest of the batch
                logger.warning("Bulk %s failed for doc %s: %s", action_name, doc_id, e)
                failed.append({"id": doc_id, "reason": "error", "detail": "The action failed on the server."})
                continue
            succeeded.append(doc_id)

        return Response({"action": action_name, "succeeded": succeeded, "failed": failed})

    @action(detail=False, methods=["get"], url_path="rag-status")
    def rag_status(self, request):
        """
        Batched indexing status for polling: GET /documents/rag-status/?ids=1,2,3
        -> [{"id", "rag_status"}] for the requested documents the user can access
        (inaccessible or unknown ids are simply omitted). At most RAG_STATUS_MAX_IDS ids.
        """
        raw = request.query_params.get("ids", "")
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if not parts:
            return Response({"detail": "ids is required (comma-separated integers)."}, status=status.HTTP_400_BAD_REQUEST)
        if len(parts) > RAG_STATUS_MAX_IDS:
            return Response(
                {"detail": f"At most {RAG_STATUS_MAX_IDS} ids per request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            ids = list(dict.fromkeys(int(p) for p in parts))
        except ValueError:
            return Response({"detail": "ids must be integers."}, status=status.HTTP_400_BAD_REQUEST)
        rows = (
            Document.objects.filter(visible_documents_q(request.user), id__in=ids)
            .distinct()
            .order_by("id")
            .values("id", "rag_status")
        )
        return Response(list(rows))

    @action(detail=True, methods=["get"], url_path="file", url_name="file")
    def file_download(self, request, pk=None):
        """Serves the PDF behind the same permission check as the document (VIEW or higher)."""
        doc = self.get_object()
        if not doc.file:
            raise Http404("This document has no PDF file.")
        try:
            handle = doc.file.open("rb")
        except (FileNotFoundError, OSError):
            raise Http404("The PDF file is missing.")
        return FileResponse(
            handle,
            content_type="application/pdf",
            as_attachment=False,
            filename=os.path.basename(doc.file.name),
        )

    @action(detail=True, methods=["post"], url_path="toggle-trash")
    def toggle_trash(self, request, pk=None):
        doc = self.get_object()
        doc.in_trash = not doc.in_trash
        doc.save(update_fields=["in_trash"])
        return Response({"id": doc.id, "in_trash": doc.in_trash})

    @action(detail=True, methods=["post"], url_path="toggle-read")
    def toggle_read(self, request, pk=None):
        doc = self.get_object()
        doc.last_read = None if doc.last_read else timezone.now()
        doc.save(update_fields=["last_read"])
        return Response({"id": doc.id, "last_read": doc.last_read})

    @action(detail=True, methods=["post"], url_path="duplicate")
    def duplicate(self, request, pk=None):
        original = self.get_object()
        copy_file = bool(original.file) and os.path.exists(original.file.path)
        with transaction.atomic():
            clone = Document.objects.create(
                owner=request.user,
                primary_collection=original.primary_collection,
                title=_truncate(f"{original.title} (Copy)", "title"),
                short_title=_truncate(f"{original.short_title or original.title} (Copy)", "short_title"),
                item_type=original.item_type,
                repository=original.repository,
                archive_id=original.archive_id,
                doi=original.doi,
                url=original.url,
                genre=original.genre,
                date=original.date,
                language=original.language,
                license=original.license,
                version=original.version,
                citation_key=_truncate(f"{original.citation_key}_copy", "citation_key") if original.citation_key else "",
                loc_in_archive=original.loc_in_archive,
                file_size=original.file_size if copy_file else None,
                is_duplicate=True,
                last_read=timezone.now(),
            )
            # Give the copy its own physical file so deleting either document keeps the other's PDF
            if copy_file:
                with original.file.open("rb") as src:
                    clone.file.save(os.path.basename(original.file.name), ContentFile(src.read()), save=True)
            DocumentAuthor.objects.bulk_create(
                DocumentAuthor(document=clone, author_id=da.author_id, author_order=da.author_order)
                for da in original.documentauthor_set.all()
            )
            clone.tags.add(*original.tags.all())
            clone.domains.add(*original.domains.all())

        # The copy has its own file and its own (empty) index: ingest it like a fresh upload
        if clone.file:
            _schedule_ingestion(clone)

        return Response(
            DocumentDetailSerializer(clone, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    # RAG Grounded Q&A and Summarization
    @action(detail=True, methods=["post"], url_path="chat",
            throttle_classes=[ScopedRateThrottle], throttle_scope="chat")
    def chat(self, request, pk=None):
        doc = self.get_object()
        not_ready = _not_ready_response(doc)
        if not_ready is not None:
            return not_ready

        raw_question = request.data.get("question")
        question = raw_question.strip() if isinstance(raw_question, str) else ""
        if not question:
            return Response(
                {"code": "question_required", "detail": "Question field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(question) > MAX_QUESTION_LENGTH:
            return Response(
                {
                    "code": "question_too_long",
                    "detail": f"Question must be at most {MAX_QUESTION_LENGTH} characters.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_path = doc.file.path if doc.file else ""
        try:
            res = query_document(doc.id, file_path, question, doc.title)
        except Exception:
            logger.exception("RAG query failed for document %s", doc.id)
            return Response(
                {"code": "rag_error", "detail": "The assistant could not answer this question."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(res)

    @action(detail=True, methods=["post"], url_path="summarize",
            throttle_classes=[ScopedRateThrottle], throttle_scope="chat")
    def summarize(self, request, pk=None):
        doc = self.get_object()
        not_ready = _not_ready_response(doc)
        if not_ready is not None:
            return not_ready

        file_path = doc.file.path if doc.file else ""
        try:
            res = summarize_document(doc.id, file_path, doc.title)
        except Exception:
            logger.exception("RAG summarization failed for document %s", doc.id)
            return Response(
                {"code": "rag_error", "detail": "The assistant could not summarize this document."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(res)

    @action(detail=True, methods=["post"], url_path="reindex")
    def reindex(self, request, pk=None):
        """
        Without a strategy: re-ingest with the production strategy on the background queue
        (202, status PENDING). With a strategy override (comparison/inspection use): run
        synchronously and report the chunk count, as before.
        """
        doc = self.get_object()
        strategy = request.data.get("strategy") or request.query_params.get("strategy")
        # Validate BEFORE touching any cache or index (reindex_document evicts the cache first)
        if strategy is not None and strategy not in REINDEX_STRATEGIES:
            return Response(
                {
                    "code": "invalid_strategy",
                    "detail": f"strategy must be one of: {', '.join(REINDEX_STRATEGIES)}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not doc.file or not os.path.exists(doc.file.path):
            return Response(
                {"code": "no_file", "detail": "This document has no PDF file to index."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if strategy is None:
            if doc.rag_status == "INDEXING":
                return _indexing_conflict_response()
            try:
                evict_rag_instance(doc.id)
            except Exception as e:
                logger.warning("Failed to evict RAG instance for doc %s: %s", doc.id, e)
            _schedule_ingestion(doc)  # sets PENDING; the worker moves it to INDEXING -> INDEXED/FAILED
            return Response(
                {"status": "PENDING", "strategy": getattr(settings, "CHUNKING_STRATEGY", "hierarchical")},
                status=status.HTTP_202_ACCEPTED,
            )

        Document.objects.filter(id=doc.id).update(rag_status="INDEXING")
        try:
            rag = reindex_document(doc.id, doc.file.path, strategy=strategy)
            chunk_count = len(getattr(rag, "documents", None) or []) if rag is not None else 0
            if chunk_count <= 0:
                raise RuntimeError(f"Re-indexing produced no chunks for document {doc.id}")
        except Exception:
            logger.exception("Re-indexing failed for document %s (strategy=%s)", doc.id, strategy)
            Document.objects.filter(id=doc.id).update(rag_status="FAILED")
            return Response(
                {"status": "FAILED", "code": "reindex_failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        Document.objects.filter(id=doc.id).update(rag_status="INDEXED")
        return Response({"status": "INDEXED", "chunks": chunk_count, "strategy": strategy})

    # Google Drive-style shares
    @action(detail=True, methods=["get", "post"], url_path="shares")
    def shares(self, request, pk=None):
        doc = self.get_object()
        if doc.owner != request.user:
            return Response(
                {"detail": "Only document owner can manage shares."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            shares = doc.shares.select_related("shared_with_user")
            return Response(DocumentShareSerializer(shares, many=True).data)

        serializer = DocumentShareSerializer(data=request.data, context={"owner_id": doc.owner_id})
        serializer.is_valid(raise_exception=True)
        serializer.save(document=doc)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if serializer.created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["delete"], url_path="shares/(?P<share_id>[^/.]+)")
    def delete_share(self, request, pk=None, share_id=None):
        doc = self.get_object()
        if doc.owner != request.user:
            return Response(
                {"detail": "Only document owner can revoke shares."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            share = doc.shares.get(id=int(share_id))
        except (ValueError, TypeError, DocumentShare.DoesNotExist):
            return Response(
                {"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND
            )
        share.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PDF Annotations on this document
    @action(detail=True, methods=["get", "post"], url_path="annotations")
    def annotations(self, request, pk=None):
        doc = self.get_object()
        if request.method == "GET":
            page = request.query_params.get("page")
            annos = doc.annotations.select_related("user")
            if page:
                annos = annos.filter(page_number=_parse_int(page, "page"))
            return Response(AnnotationSerializer(annos, many=True).data)

        serializer = AnnotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=doc, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Related items
    @action(detail=True, methods=["get", "post"], url_path="related")
    def related(self, request, pk=None):
        doc = self.get_object()
        if request.method == "GET":
            # Use DB-side union for efficiency
            related_from = RelatedDocument.objects.filter(document_1=doc).values_list(
                "document_2_id", flat=True
            )
            related_to = RelatedDocument.objects.filter(document_2=doc).values_list(
                "document_1_id", flat=True
            )
            all_related_ids = related_from.union(related_to)
            # Only list related documents the requester can open themselves: the owner may
            # have linked one of their private papers to a document they shared.
            related_docs = (
                Document.objects.filter(visible_documents_q(request.user), id__in=all_related_ids)
                .distinct()
                .select_related("primary_collection")
                .prefetch_related("authors", "tags")
            )
            return Response(
                DocumentListSerializer(
                    related_docs, many=True, context={"request": request}
                ).data
            )

        target_id = request.data.get("related_document_id")
        if target_id in (None, ""):
            return Response(
                {"detail": "related_document_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target_id = _parse_int(target_id, "related_document_id")
        if target_id == doc.id:
            return Response(
                {"detail": "A document cannot be related to itself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation_type = request.data.get("relation_type", "manual")
        max_type_len = RelatedDocument._meta.get_field("relation_type").max_length
        if not isinstance(relation_type, str) or not relation_type.strip() or len(relation_type) > max_type_len:
            return Response(
                {"detail": f"relation_type must be a string of 1-{max_type_len} characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_doc = Document.objects.get(id=target_id)
            # Do not reveal or link documents the requester cannot see
            if not has_document_permission(request.user, target_doc, "VIEW"):
                raise Document.DoesNotExist
        except Document.DoesNotExist:
            return Response(
                {"detail": "Target document does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        relation, _ = RelatedDocument.objects.get_or_create(
            document_1=doc,
            document_2=target_doc,
            defaults={"relation_type": relation_type.strip()},
        )
        return Response(
            {"status": "linked", "id": relation.id}, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['get'], url_path='chunks')
    def chunks(self, request, pk=None):
        """
        Inspect document chunks under a specified chunking strategy.
        Supports query params:
          - strategy: 'section' | 'section_token' | 'section_overlap' | 'hierarchical'
            (default: 'section_overlap')
          - max_tokens: int 1-4000 (default: 400; ignored for 'hierarchical', which uses 200-token children)
          - overlap: int, 0 <= overlap < max_tokens (default: 80; ignored for 'hierarchical',
            which uses a 40-token child overlap)
        For 'hierarchical', the response also carries `parents`: each parent section with its
        children grouped under it (`parent_text` is sent once per parent, not per child).
        Extracted sections are cached per file version, so switching strategies is cheap.
        """
        doc = self.get_object()
        strategy = request.query_params.get('strategy', 'section_overlap')
        if strategy not in CHUNK_INSPECT_STRATEGIES:
            return Response(
                {
                    "code": "invalid_strategy",
                    "detail": f"strategy must be one of: {', '.join(CHUNK_INSPECT_STRATEGIES)}.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if strategy == 'hierarchical':
            return self._hierarchical_chunks_response(doc)
        try:
            max_tokens = int(request.query_params.get('max_tokens', 400))
        except (ValueError, TypeError):
            max_tokens = 400

        try:
            overlap = int(request.query_params.get('overlap', 80))
        except (ValueError, TypeError):
            overlap = 80

        bad_overlap = strategy == 'section_overlap' and not 0 <= overlap < max_tokens
        if not 1 <= max_tokens <= CHUNK_INSPECT_MAX_TOKENS or bad_overlap:
            return Response(
                {
                    "code": "invalid_parameters",
                    "detail": f"max_tokens must be 1-{CHUNK_INSPECT_MAX_TOKENS} and 0 <= overlap < max_tokens.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        sections = self._sections_for(doc)
        if sections is None:
            return Response(
                {"code": "chunking_failed", "detail": "Failed to extract document chunks."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        chunks_data = chunk_sections(sections, strategy=strategy, max_tokens=max_tokens, overlap=overlap)

        avg_tokens = (
            round(sum(c['token_count'] for c in chunks_data) / max(1, len(chunks_data)), 1)
            if chunks_data else 0
        )

        return Response({
            "document_id": str(doc.id),
            "document_title": doc.title,
            "strategy": strategy,
            "max_tokens": max_tokens,
            "overlap": overlap if strategy == 'section_overlap' else 0,
            "total_chunks": len(chunks_data),
            "avg_tokens_per_chunk": avg_tokens,
            "chunks": chunks_data
        })

    def _sections_for(self, doc):
        """Sections of the document's PDF (cached), a single-section fallback for documents
        without a file, or None when extraction fails."""
        if not doc.file or not os.path.exists(doc.file.path):
            content = doc.extra or doc.title or "No document file content available."
            return [{"title": "Abstract", "page_start": 1, "page_end": 1, "text": content}]
        try:
            return _cached_sections(doc)
        except Exception as e:
            logger.exception("Error extracting sections from document %s: %s", doc.id, e)
            return None

    def _hierarchical_chunks_response(self, doc):
        """Small-to-Big inspection: child chunks (as indexed) plus their grouping under parent sections."""
        sections = self._sections_for(doc)
        if sections is None:
            return Response(
                {"code": "chunking_failed", "detail": "Failed to extract document chunks."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        children = chunk_hierarchical(
            sections,
            child_max_tokens=HIERARCHICAL_CHILD_TOKENS,
            child_overlap=HIERARCHICAL_CHILD_OVERLAP,
            paper_id=f"doc_{doc.id}",
        )

        parents: List[Dict[str, Any]] = []
        by_parent: Dict[Any, Dict[str, Any]] = {}
        slim_children: List[Dict[str, Any]] = []
        for child in children:
            p_id = child.get("parent_id")
            group = by_parent.get(p_id)
            if group is None:
                group = {
                    "parent_id": p_id,
                    "section": child.get("section", ""),
                    "page": child.get("page", 1),
                    "parent_tokens": child.get("parent_tokens", 0),
                    "parent_text": child.get("parent_text", ""),
                    "child_ids": [],
                }
                by_parent[p_id] = group
                parents.append(group)
            group["child_ids"].append(child.get("chunk_id"))
            # parent_text is sent once per parent (in `parents`), not repeated on every child
            slim_children.append({k: v for k, v in child.items() if k != "parent_text"})
        for group in parents:
            group["child_count"] = len(group["child_ids"])

        avg_tokens = (
            round(sum(c.get("token_count", 0) for c in children) / len(children), 1) if children else 0
        )
        return Response({
            "document_id": str(doc.id),
            "document_title": doc.title,
            "strategy": "hierarchical",
            "max_tokens": HIERARCHICAL_CHILD_TOKENS,
            "overlap": HIERARCHICAL_CHILD_OVERLAP,
            "total_chunks": len(children),
            "total_parents": len(parents),
            "avg_tokens_per_chunk": avg_tokens,
            "chunks": slim_children,
            "parents": parents,
        })



class MetadataLookupView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        doi = request.data.get("doi")
        if not doi or not isinstance(doi, str) or not doi.strip():
            return Response(
                {"detail": "DOI string is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(doi) > MAX_DOI_LENGTH:
            return Response(
                {"detail": f"DOI must be at most {MAX_DOI_LENGTH} characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            metadata = fetch_metadata_from_doi(doi)
        except Exception:
            logger.exception("DOI lookup failed for %r", doi)
            metadata = None
        if not metadata:
            return Response(
                {"detail": "Could not fetch metadata for the provided DOI."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(metadata)


def _first_pages_copy(src_path, max_pages):
    """Path of a temporary PDF holding only the first `max_pages` pages of src_path, or None
    when the file is short enough (or cannot be opened; the extractor then reports failure)."""
    try:
        import pymupdf
        with pymupdf.open(src_path) as pdf:
            if pdf.page_count <= max_pages:
                return None
            with pymupdf.open() as head:
                head.insert_pdf(pdf, from_page=0, to_page=max_pages - 1)
                fd, head_path = tempfile.mkstemp(suffix=".pdf")
                os.close(fd)
                head.save(head_path)
                return head_path
    except Exception as e:
        logger.warning("[PDF-EXTRACT] Could not cut the PDF to its first pages: %s", e)
        return None


class PdfMetadataExtractView(views.APIView):
    """
    Extracts metadata from an uploaded PDF without saving to the database.
    Allows the frontend to display a preview pane matching metadata_extract_usecase.png.
    Only the first METADATA_PREVIEW_MAX_PAGES pages are parsed.
    """

    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "extract"

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            logger.warning(
                "[PDF-EXTRACT] [ERROR] No 'file' field in request.FILES. Received keys: %r",
                list(request.FILES.keys()),
            )
            return Response(
                {"detail": "PDF file is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            "[PDF-EXTRACT] [IN] Received file: %r (%s bytes)",
            uploaded_file.name,
            uploaded_file.size,
        )
        if uploaded_file.size > MAX_UPLOAD_BYTES:
            return Response(
                {"detail": "File size exceeds maximum allowed limit (50 MB)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate magic byte
        pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
        chunk = uploaded_file.read(1024)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(pos)
        if not chunk.startswith(b"%PDF-") and b"%PDF-" not in chunk[:1024]:
            logger.warning(
                "[PDF-EXTRACT] [ERROR] Magic byte validation failed. Chunk preview: %r",
                chunk[:32],
            )
            return Response(
                {"detail": "Uploaded file is not a valid PDF document."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            for c in uploaded_file.chunks():
                tmp.write(c)
            tmp_path = tmp.name

        head_path = None
        try:
            head_path = _first_pages_copy(tmp_path, METADATA_PREVIEW_MAX_PAGES)
            logger.info("[PDF-EXTRACT] [RUN] Running extraction pipeline...")
            metadata = extract_metadata_from_pdf(head_path or tmp_path)
            logger.info(
                "[PDF-EXTRACT] [DONE] Pipeline finished. Title: %r, Authors: %r",
                metadata.get("title"),
                metadata.get("authors"),
            )
        except Exception as e:
            logger.exception(
                "[PDF-EXTRACT] [FAIL] Exception during extract_metadata_from_pdf: %s", e
            )
            metadata = None
        finally:
            for path in (tmp_path, head_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError as e:
                        logger.warning("[PDF-EXTRACT] Could not remove temp file: %s", e)

        if not metadata:
            logger.warning(
                "[PDF-EXTRACT] [EMPTY] No metadata returned from extraction pipeline (HTTP 404)."
            )
            return Response(
                {"detail": "Could not extract metadata from the provided PDF."},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info(
            "[PDF-EXTRACT] [OK] Returning HTTP 200 with extracted metadata for %r",
            metadata.get("title"),
        )
        return Response(metadata)


class AnnotationViewSet(viewsets.ModelViewSet):
    """
    /annotations/: list/retrieve the user's own annotations and those on documents they own.
    Create needs COMMENT or higher on the document. Edit: the author only, while they still
    hold COMMENT or higher. Delete: the author or the document owner.
    """

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.filter(
            Q(user=self.request.user) | Q(document__owner=self.request.user)
        ).select_related("user", "document")

    def create(self, request, *args, **kwargs):
        raw_doc = request.data.get("document") if hasattr(request.data, "get") else None
        if raw_doc in (None, ""):
            raise ValidationError({"document": "This field is required."})
        doc_id = _parse_int(raw_doc, "document")
        doc = get_object_or_404(
            Document.objects.filter(visible_documents_q(request.user)).distinct(), id=doc_id
        )
        if not has_document_permission(request.user, doc, "COMMENT"):
            raise PermissionDenied("Annotating this document requires COMMENT permission.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=doc, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        anno = serializer.instance
        if anno.user_id != self.request.user.id:
            raise PermissionDenied("Only the author can edit this annotation.")
        if not has_document_permission(self.request.user, anno.document, "COMMENT"):
            raise PermissionDenied("Editing annotations requires COMMENT permission on the document.")
        serializer.save()

    def perform_destroy(self, instance):
        user_id = self.request.user.id
        if instance.user_id != user_id and instance.document.owner_id != user_id:
            raise PermissionDenied("Only the author or the document owner can delete this annotation.")
        instance.delete()


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NoteSerializer

    def get_queryset(self):
        qs = Note.objects.filter(user=self.request.user).select_related("user")
        doc_id = self.request.query_params.get("document_id")
        if doc_id:
            qs = qs.filter(document_id=_parse_int(doc_id, "document_id"))
        return qs

    def _check_document_access(self, serializer):
        doc = serializer.validated_data.get("document")
        if doc is not None and not has_document_permission(self.request.user, doc, "VIEW"):
            raise PermissionDenied("You do not have access to this document.")

    def perform_create(self, serializer):
        self._check_document_access(serializer)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        self._check_document_access(serializer)
        serializer.save()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Tags attached to at least one document the user can access (tags are global rows,
    so listing them all would reveal other users' private tagging)."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer

    def get_queryset(self):
        visible_ids = Document.objects.filter(visible_documents_q(self.request.user)).values("id")
        return Tag.objects.filter(documents__id__in=visible_ids).distinct().order_by("name")


class SharedWithMeView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        shared_docs = (
            Document.objects.filter(
                Q(shares__shared_with_user=user)
                | Q(primary_collection__shares__shared_with_user=user)
            )
            .exclude(owner=user)
            .distinct()
            .select_related("owner", "primary_collection")
            .prefetch_related("authors", "tags")
        )

        return Response(
            DocumentListSerializer(
                shared_docs, many=True, context={"request": request}
            ).data
        )
