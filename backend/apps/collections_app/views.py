from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Collection, CollectionShare
from .serializers import CollectionSerializer, CollectionTreeSerializer, CollectionShareSerializer

class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        # Return collections owned by user or shared with user
        return Collection.objects.filter(
            Q(owner=user) | Q(shares__shared_with_user=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """Return root collections with nested children for the current user."""
        user = request.user
        root_collections = Collection.objects.filter(
            Q(owner=user) | Q(shares__shared_with_user=user),
            parent__isnull=True
        ).distinct()
        serializer = CollectionTreeSerializer(root_collections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='shares')
    def shares(self, request, pk=None):
        collection = self.get_object()
        if collection.owner != request.user:
            return Response({"detail": "Only the collection owner can manage shares."}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            shares = collection.shares.all()
            serializer = CollectionShareSerializer(shares, many=True)
            return Response(serializer.data)

        serializer = CollectionShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(collection=collection)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path='shares/(?P<share_id>[^/.]+)')
    def delete_share(self, request, pk=None, share_id=None):
        collection = self.get_object()
        if collection.owner != request.user:
            return Response({"detail": "Only the collection owner can revoke shares."}, status=status.HTTP_403_FORBIDDEN)
        try:
            share = collection.shares.get(id=share_id)
            share.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except CollectionShare.DoesNotExist:
            return Response({"detail": "Share not found."}, status=status.HTTP_404_NOT_FOUND)
