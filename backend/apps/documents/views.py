import logging
import os
import tempfile
from typing import Any, Dict, List
from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone
from .models import (
    Document,
    Tag,
    Domain,
    Annotation,
    Note,
    DocumentShare,
    RelatedDocument,
)
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
from .permissions import IsOwnerOrCollaborator, has_document_permission
from .services.crossref_service import fetch_metadata_from_doi
from .services.webhook_service import trigger_rag_ingestion
from .services.pdf_metadata_service import (
    apply_pdf_metadata_to_document,
    extract_metadata_from_pdf,
    is_raw_title,
)
from .services.chunking_utils import chunk_document_pdf, chunk_sections, extract_sections_from_pdf
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


class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrCollaborator)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
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
        queryset = Document.objects.filter(
            Q(owner=user)
            | Q(shares__shared_with_user=user)
            | Q(primary_collection__shares__shared_with_user=user)
        ).distinct()

        # Query Filters
        in_trash = self.request.query_params.get("in_trash")
        if in_trash is not None:
            queryset = queryset.filter(in_trash=in_trash.lower() in ("true", "1"))
        else:
            # Default exclude trash unless explicitly asked
            queryset = queryset.filter(in_trash=False)

        collection_id = self.request.query_params.get("collection_id")
        if collection_id:
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

        return queryset.select_related("owner", "primary_collection").prefetch_related(
            "authors", "tags", "domains"
        )

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
        old_file_name = serializer.instance.file.name if serializer.instance.file else ""
        doc = serializer.save()
        new_file_name = doc.file.name if doc.file else ""
        if "file" in serializer.validated_data and doc.file and new_file_name != old_file_name:
            # A new PDF replaces the old one: drop the stale in-memory index and re-ingest
            try:
                evict_rag_instance(doc.id)
            except Exception as e:
                logger.warning("Failed to evict RAG instance for doc %s: %s", doc.id, e)
            doc.file_size = doc.file.size
            doc.rag_status = "PENDING"
            doc.save(update_fields=["file_size", "rag_status"])
            _schedule_ingestion(doc)

    def perform_destroy(self, instance):
        """
        Permanent delete implementation matching thesis specification:
          1. Deletes physical file in media/documents/
          2. Deletes that document's points in Qdrant (child vectors in doc_{id} and companion doc_{id}_parents)
          3. Evicts cached in-memory _rag_instances[doc_id]
          4. Deletes PostgreSQL row (CASCADE to all relational tables)
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
        super().perform_destroy(instance)

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
        clone = Document.objects.create(
            owner=request.user,
            primary_collection=original.primary_collection,
            title=f"{original.title} (Copy)",
            short_title=f"{original.short_title or original.title} (Copy)",
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
            citation_key=f"{original.citation_key}_copy",
            loc_in_archive=original.loc_in_archive,
            file_size=original.file_size,
            is_duplicate=True,
            last_read=timezone.now(),
        )
        # Give the copy its own physical file so deleting either document keeps the other's PDF
        if original.file:
            with original.file.open("rb") as src:
                clone.file.save(os.path.basename(original.file.name), ContentFile(src.read()), save=True)
        for author in original.authors.all():
            clone.authors.add(author)
        for tag in original.tags.all():
            clone.tags.add(tag)
        for domain in original.domains.all():
            clone.domains.add(domain)

        # The copy has its own file and its own (empty) index: ingest it like a fresh upload
        if clone.file:
            _schedule_ingestion(clone)

        return Response(
            DocumentDetailSerializer(clone, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    # RAG Grounded Q&A and Summarization
    @action(detail=True, methods=["post"], url_path="chat")
    def chat(self, request, pk=None):
        doc = self.get_object()
        if doc.rag_status == "INDEXING":
            return _indexing_conflict_response()

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

    @action(detail=True, methods=["post"], url_path="summarize")
    def summarize(self, request, pk=None):
        doc = self.get_object()
        if doc.rag_status == "INDEXING":
            return _indexing_conflict_response()

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

        active_strategy = strategy or getattr(settings, "CHUNKING_STRATEGY", "hierarchical")
        Document.objects.filter(id=doc.id).update(rag_status="INDEXING")
        try:
            rag = reindex_document(doc.id, doc.file.path, strategy=strategy)
            chunk_count = len(getattr(rag, "documents", None) or []) if rag is not None else 0
            if chunk_count <= 0:
                raise RuntimeError(f"Re-indexing produced no chunks for document {doc.id}")
        except Exception:
            logger.exception("Re-indexing failed for document %s (strategy=%s)", doc.id, active_strategy)
            Document.objects.filter(id=doc.id).update(rag_status="FAILED")
            return Response(
                {"status": "FAILED", "code": "reindex_failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        Document.objects.filter(id=doc.id).update(rag_status="INDEXED")
        return Response({"status": "INDEXED", "chunks": chunk_count, "strategy": active_strategy})

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
            shares = doc.shares.all()
            return Response(DocumentShareSerializer(shares, many=True).data)

        serializer = DocumentShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path="shares/(?P<share_id>[^/.]+)")
    def delete_share(self, request, pk=None, share_id=None):
        doc = self.get_object()
        if doc.owner != request.user:
            return Response(
                {"detail": "Only document owner can revoke shares."},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            share = doc.shares.get(id=share_id)
            share.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DocumentShare.DoesNotExist:
            return Response(
                {"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND
            )

    # PDF Annotations on this document
    @action(detail=True, methods=["get", "post"], url_path="annotations")
    def annotations(self, request, pk=None):
        doc = self.get_object()
        if request.method == "GET":
            page = request.query_params.get("page")
            annos = doc.annotations.all()
            if page:
                annos = annos.filter(page_number=page)
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
            related_docs = Document.objects.filter(id__in=all_related_ids)
            return Response(
                DocumentListSerializer(
                    related_docs, many=True, context={"request": request}
                ).data
            )

        target_id = request.data.get("related_document_id")
        if not target_id:
            return Response(
                {"detail": "related_document_id is required."},
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
            defaults={"relation_type": request.data.get("relation_type", "manual")},
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
          - max_tokens: int (default: 400; ignored for 'hierarchical', which uses 200-token children)
          - overlap: int (default: 80; ignored for 'hierarchical', which uses a 40-token child overlap)
        For 'hierarchical', the response also carries `parents`: each parent section with its
        children grouped under it (`parent_text` is sent once per parent, not per child).
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

        if not doc.file or not os.path.exists(doc.file.path):
            content = doc.extra or doc.title or "No document file content available."
            sections = [{"title": "Abstract", "page_start": 1, "page_end": 1, "text": content}]
            chunks_data = chunk_sections(sections, strategy=strategy, max_tokens=max_tokens, overlap=overlap)
        else:
            try:
                chunks_data = chunk_document_pdf(
                    doc.file.path,
                    strategy=strategy,
                    max_tokens=max_tokens,
                    overlap=overlap
                )
            except Exception as e:
                logger.exception("Error extracting chunks from document %s: %s", doc.id, e)
                return Response(
                    {"detail": f"Failed to extract document chunks: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

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

    def _hierarchical_chunks_response(self, doc):
        """Small-to-Big inspection: child chunks (as indexed) plus their grouping under parent sections."""
        if not doc.file or not os.path.exists(doc.file.path):
            content = doc.extra or doc.title or "No document file content available."
            sections = [{"title": "Abstract", "page_start": 1, "page_end": 1, "text": content}]
        else:
            try:
                sections = extract_sections_from_pdf(doc.file.path)
            except Exception as e:
                logger.exception("Error extracting sections from document %s: %s", doc.id, e)
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
            "chunks": children,
            "parents": parents,
        })



class MetadataLookupView(views.APIView):
    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        doi = request.data.get("doi")
        if not doi:
            return Response(
                {"detail": "DOI string is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        metadata = fetch_metadata_from_doi(doi)
        if not metadata:
            return Response(
                {"detail": "Could not fetch metadata for the provided DOI."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(metadata)


class PdfMetadataExtractView(views.APIView):
    """
    Extracts metadata from an uploaded PDF without saving to the database.
    Allows the frontend to display a preview pane matching metadata_extract_usecase.png.
    """

    authentication_classes = ()
    permission_classes = (permissions.AllowAny,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            logger.warning(
                "[PDF-EXTRACT] [ERROR] No 'file' field in request.FILES. Received keys: %s",
                list(request.FILES.keys()),
            )
            return Response(
                {"detail": "PDF file is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(
            "[PDF-EXTRACT] [IN] Received file: %s (%s bytes)",
            uploaded_file.name,
            uploaded_file.size,
        )

        # Validate magic byte
        pos = uploaded_file.tell() if hasattr(uploaded_file, "tell") else 0
        chunk = uploaded_file.read(1024)
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(pos)
        if not chunk.startswith(b"%PDF-") and b"%PDF-" not in chunk[:1024]:
            logger.warning(
                "[PDF-EXTRACT] [ERROR] Magic byte validation failed. Chunk preview: %s",
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

        try:
            logger.info(
                "[PDF-EXTRACT] [RUN] Running extraction pipeline on temp file %s...",
                tmp_path,
            )
            metadata = extract_metadata_from_pdf(tmp_path)
            logger.info(
                "[PDF-EXTRACT] [DONE] Pipeline finished. Title: %s, Authors: %s",
                metadata.get("title"),
                metadata.get("authors"),
            )
        except Exception as e:
            logger.exception(
                "[PDF-EXTRACT] [FAIL] Exception during extract_metadata_from_pdf: %s", e
            )
            metadata = None
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        if not metadata:
            logger.warning(
                "[PDF-EXTRACT] [EMPTY] No metadata returned from extraction pipeline (HTTP 404)."
            )
            return Response(
                {"detail": "Could not extract metadata from the provided PDF."},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info(
            "[PDF-EXTRACT] [OK] Returning HTTP 200 with extracted metadata for '%s'",
            metadata.get("title"),
        )
        return Response(metadata)


class AnnotationViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        return Annotation.objects.filter(
            Q(user=self.request.user) | Q(document__owner=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NoteSerializer

    def get_queryset(self):
        qs = Note.objects.filter(user=self.request.user)
        doc_id = self.request.query_params.get("document_id")
        if doc_id:
            qs = qs.filter(document_id=doc_id)
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
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by("name")


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
        )

        return Response(
            DocumentListSerializer(
                shared_docs, many=True, context={"request": request}
            ).data
        )
