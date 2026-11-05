from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Collection, CollectionShare

User = get_user_model()


class ShareCreateMixin:
    """
    Shared create logic for document and collection shares.
    - `shared_with_email` is required and resolved case-insensitively.
    - The owner (context['owner_id']) cannot share with themselves.
    - Sharing again with the same user updates the permission instead of failing on the
      unique constraint; `self.created` tells the view whether a share was created.
    Subclasses set `target_field` ('document' or 'collection').
    """

    target_field = ''

    def validate(self, attrs):
        if self.instance is None and not attrs.get('shared_with_email'):
            raise serializers.ValidationError({'shared_with_email': 'This field is required.'})
        return attrs

    def create(self, validated_data):
        email = validated_data.pop('shared_with_email')
        candidates = list(User.objects.filter(email__iexact=email)[:2])
        user = next((u for u in candidates if u.email == email), None)
        if user is None and len(candidates) == 1:
            user = candidates[0]
        if user is None:
            raise serializers.ValidationError({'shared_with_email': 'User with this email not found.'})
        if user.id == self.context.get('owner_id'):
            raise serializers.ValidationError({'shared_with_email': 'You cannot share with yourself.'})

        target = validated_data.pop(self.target_field)
        share, created = self.Meta.model.objects.update_or_create(
            **{self.target_field: target, 'shared_with_user': user},
            defaults={'permission': validated_data.get('permission', 'VIEW')},
        )
        self.created = created
        return share


class CollectionShareSerializer(ShareCreateMixin, serializers.ModelSerializer):
    target_field = 'collection'
    shared_with_email = serializers.EmailField(write_only=True, required=False)
    shared_with_username = serializers.ReadOnlyField(source='shared_with_user.username')
    shared_with_email_display = serializers.ReadOnlyField(source='shared_with_user.email')

    class Meta:
        model = CollectionShare
        fields = ('id', 'collection', 'shared_with_user', 'shared_with_email', 'shared_with_username', 'shared_with_email_display', 'permission', 'created_at')
        read_only_fields = ('collection', 'shared_with_user', 'created_at')


class CollectionSerializer(serializers.ModelSerializer):
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ('id', 'owner', 'parent', 'name', 'color', 'document_count', 'created_at')
        read_only_fields = ('owner', 'created_at')

    def get_document_count(self, obj):
        if hasattr(obj, 'doc_count'):
            return obj.doc_count
        return obj.primary_documents.count()

    def validate_parent(self, value):
        """The parent must be a collection the user owns or holds an EDIT share on, and must
        not be the collection itself or one of its descendants (a cycle hides the subtree)."""
        if value is None:
            return value
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if self.instance is not None and self.instance.parent_id == value.id:
            return value
        can_use = user is not None and (
            value.owner_id == user.id
            or value.shares.filter(shared_with_user=user, permission='EDIT').exists()
        )
        if not can_use:
            raise serializers.ValidationError('You cannot add a collection under this collection.')
        if self.instance is not None:
            node, seen = value, set()
            while node is not None and node.id not in seen:
                if node.id == self.instance.id:
                    raise serializers.ValidationError('A collection cannot be moved into itself or its subcollections.')
                seen.add(node.id)
                node = node.parent
        return value


class CollectionTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = ('id', 'name', 'color', 'parent', 'document_count', 'children')

    def get_children(self, obj):
        children = obj.children.all()
        return CollectionTreeSerializer(children, many=True).data

    def get_document_count(self, obj):
        return obj.primary_documents.count()
