"""Main URL Configuration."""
from django.contrib import admin
from django.urls import path, include

# MEDIA is deliberately not served: PDFs are only reachable through the permission-checked
# GET /api/v1/documents/{id}/file/ endpoint, and media/ also holds the Qdrant store.
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/collections/', include('apps.collections_app.urls')),
    path('api/v1/', include('apps.documents.urls')),
]
