import logging
from rest_framework import viewsets, permissions, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Q
from django.utils import timezone
from .models import Document, Tag, Domain, Annotation, Note, DocumentShare, RelatedDocument
from .serializers import (
    DocumentListSerializer, DocumentDetailSerializer, DocumentCreateUpdateSerializer,
    TagSerializer, DomainSerializer, AnnotationSerializer, NoteSerializer,
    DocumentShareSerializer
)
from .permissions import IsOwnerOrCollaborator
from .services.crossref_service import fetch_metadata_from_doi
from .services.webhook_service import trigger_rag_ingestion
from .services.pdf_metadata_service import apply_pdf_metadata_to_document

logger = logging.getLogger(__name__)

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
        if self.action == 'list':
            return DocumentListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return DocumentCreateUpdateSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Document.objects.filter(
            Q(owner=user) |
            Q(shares__shared_with_user=user) |
            Q(primary_collection__shares__shared_with_user=user)
        ).distinct()

        # Query Filters
        in_trash = self.request.query_params.get('in_trash')
        if in_trash is not None:
            queryset = queryset.filter(in_trash=in_trash.lower() in ('true', '1'))
        else:
            # Default exclude trash unless explicitly asked
            queryset = queryset.filter(in_trash=False)

        collection_id = self.request.query_params.get('collection_id')
        if collection_id:
            queryset = queryset.filter(
                Q(primary_collection_id=collection_id) | Q(collections__id=collection_id)
            )

        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__name__iexact=tag)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(short_title__icontains=search) |
                Q(doi__icontains=search) |
                Q(authors__last_name__icontains=search) |
                Q(authors__first_name__icontains=search) |
                Q(tags__name__icontains=search)
            )

        section = self.request.query_params.get('section')
        if section == 'recent':
            queryset = queryset.filter(last_read__isnull=False).order_by('-last_read')
        elif section == 'publications':
            queryset = queryset.filter(is_publication=True)
        elif section == 'duplicates':
            queryset = queryset.filter(is_duplicate=True)
        elif section == 'unfiled':
            queryset = queryset.filter(primary_collection__isnull=True)

        return queryset.select_related('owner', 'primary_collection').prefetch_related(
            'authors', 'tags', 'domains'
        )

    def perform_create(self, serializer):
        doc = serializer.save(owner=self.request.user)
        # If file was uploaded:
        if doc.file:
            # 1. Automatically extract academic metadata (arXiv ID, DOI, or layout heuristic)
            try:
                apply_pdf_metadata_to_document(doc)
            except Exception as e:
                logger.warning("PDF metadata extraction failed: %s", e)

            # 2. Trigger RAG background ingestion
            trigger_rag_ingestion(
                document_id=doc.id,
                file_path=doc.file.path,
                title=doc.title,
                owner_id=doc.owner_id
            )

    @action(detail=True, methods=['post'], url_path='toggle-trash')
    def toggle_trash(self, request, pk=None):
        doc = self.get_object()
        doc.in_trash = not doc.in_trash
        doc.save(update_fields=['in_trash'])
        return Response({'id': doc.id, 'in_trash': doc.in_trash})

    @action(detail=True, methods=['post'], url_path='toggle-read')
    def toggle_read(self, request, pk=None):
        doc = self.get_object()
        doc.last_read = None if doc.last_read else timezone.now()
        doc.save(update_fields=['last_read'])
        return Response({'id': doc.id, 'last_read': doc.last_read})

    @action(detail=True, methods=['post'], url_path='duplicate')
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
            file=original.file,
            file_size=original.file_size,
            is_duplicate=True,
            last_read=timezone.now(),
        )
        for author in original.authors.all():
            clone.authors.add(author)
        for tag in original.tags.all():
            clone.tags.add(tag)
        for domain in original.domains.all():
            clone.domains.add(domain)

        return Response(DocumentDetailSerializer(clone, context={'request': request}).data, status=status.HTTP_201_CREATED)

    # Google Drive-style shares
    @action(detail=True, methods=['get', 'post'], url_path='shares')
    def shares(self, request, pk=None):
        doc = self.get_object()
        if doc.owner != request.user:
            return Response({"detail": "Only document owner can manage shares."}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            shares = doc.shares.all()
            return Response(DocumentShareSerializer(shares, many=True).data)

        serializer = DocumentShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='shares/(?P<share_id>[^/.]+)')
    def delete_share(self, request, pk=None, share_id=None):
        doc = self.get_object()
        if doc.owner != request.user:
            return Response({"detail": "Only document owner can revoke shares."}, status=status.HTTP_403_FORBIDDEN)
        try:
            share = doc.shares.get(id=share_id)
            share.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except DocumentShare.DoesNotExist:
            return Response({"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND)

    # PDF Annotations on this document
    @action(detail=True, methods=['get', 'post'], url_path='annotations')
    def annotations(self, request, pk=None):
        doc = self.get_object()
        if request.method == 'GET':
            page = request.query_params.get('page')
            annos = doc.annotations.all()
            if page:
                annos = annos.filter(page_number=page)
            return Response(AnnotationSerializer(annos, many=True).data)

        serializer = AnnotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(document=doc, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Related items
    @action(detail=True, methods=['get', 'post'], url_path='related')
    def related(self, request, pk=None):
        doc = self.get_object()
        if request.method == 'GET':
            # Use DB-side union for efficiency
            related_from = RelatedDocument.objects.filter(document_1=doc).values_list('document_2_id', flat=True)
            related_to = RelatedDocument.objects.filter(document_2=doc).values_list('document_1_id', flat=True)
            all_related_ids = related_from.union(related_to)
            related_docs = Document.objects.filter(id__in=all_related_ids)
            return Response(DocumentListSerializer(related_docs, many=True, context={'request': request}).data)

        target_id = request.data.get('related_document_id')
        if not target_id:
            return Response({"detail": "related_document_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_doc = Document.objects.get(id=target_id)
        except Document.DoesNotExist:
            return Response({"detail": "Target document does not exist."}, status=status.HTTP_404_NOT_FOUND)

        relation, _ = RelatedDocument.objects.get_or_create(
            document_1=doc,
            document_2=target_doc,
            defaults={'relation_type': request.data.get('relation_type', 'manual')}
        )
        return Response({"status": "linked", "id": relation.id}, status=status.HTTP_201_CREATED)


class MetadataLookupView(views.APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        doi = request.data.get('doi')
        if not doi:
            return Response({"detail": "DOI string is required."}, status=status.HTTP_400_BAD_REQUEST)

        metadata = fetch_metadata_from_doi(doi)
        if not metadata:
            return Response({"detail": "Could not fetch metadata for the provided DOI."}, status=status.HTTP_404_NOT_FOUND)

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
        doc_id = self.request.query_params.get('document_id')
        if doc_id:
            qs = qs.filter(document_id=doc_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TagSerializer
    queryset = Tag.objects.all().order_by('name')


class SharedWithMeView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user
        shared_docs = Document.objects.filter(
            Q(shares__shared_with_user=user) |
            Q(primary_collection__shares__shared_with_user=user)
        ).exclude(owner=user).distinct()

        return Response(DocumentListSerializer(shared_docs, many=True, context={'request': request}).data)
