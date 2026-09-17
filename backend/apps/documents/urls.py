from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet, MetadataLookupView,
    NoteViewSet, TagViewSet, SharedWithMeView
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('metadata/lookup-doi/', MetadataLookupView.as_view(), name='metadata_lookup_doi'),
    path('shares/shared-with-me/', SharedWithMeView.as_view(), name='shared_with_me'),
    path('', include(router.urls)),
]
