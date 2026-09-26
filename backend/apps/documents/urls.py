from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet, MetadataLookupView, PdfMetadataExtractView,
    AnnotationViewSet, NoteViewSet, TagViewSet, SharedWithMeView
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'annotations', AnnotationViewSet, basename='annotation')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('metadata/lookup-doi/', MetadataLookupView.as_view(), name='metadata_lookup_doi'),
    path('metadata/extract-pdf/', PdfMetadataExtractView.as_view(), name='metadata_extract_pdf'),
    path('shares/shared-with-me/', SharedWithMeView.as_view(), name='shared_with_me'),
    path('', include(router.urls)),
]
