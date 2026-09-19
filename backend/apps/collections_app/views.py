from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Collection, CollectionShare
from .serializers import CollectionSerializer, CollectionTreeSerializer, CollectionShareSerializer

class CollectionViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        # Return collections owned by user or shared with user, annotated with document count
        return Collection.objects.filter(
            Q(owner=user) | Q(shares__shared_with_user=user)
        ).distinct().annotate(doc_count=Count('primary_documents'))

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """
        Return all collections structured into a nested tree for the current user.
        Executes in a single SQL query using in-memory dictionary-based tree building,
        preventing N+1 queries regardless of tree depth.
        """
        user = request.user
        collections = Collection.objects.filter(
            Q(owner=user) | Q(shares__shared_with_user=user)
        ).distinct().annotate(doc_count=Count('primary_documents'))

        nodes = {}
        for c in collections:
            nodes[c.id] = {
                'id': c.id,
                'name': c.name,
                'color': c.color,
                'parent': c.parent_id,
                'document_count': getattr(c, 'doc_count', 0),
                'children': [],
            }

        root_nodes = []
        for c in collections:
            node = nodes[c.id]
            if c.parent_id and c.parent_id in nodes:
                nodes[c.parent_id]['children'].append(node)
            else:
                root_nodes.append(node)

        return Response(root_nodes)

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
