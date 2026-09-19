from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Collection, CollectionShare

User = get_user_model()

class CollectionShareSerializer(serializers.ModelSerializer):
    shared_with_email = serializers.EmailField(write_only=True, required=False)
    shared_with_username = serializers.ReadOnlyField(source='shared_with_user.username')
    shared_with_email_display = serializers.ReadOnlyField(source='shared_with_user.email')

    class Meta:
        model = CollectionShare
        fields = ('id', 'collection', 'shared_with_user', 'shared_with_email', 'shared_with_username', 'shared_with_email_display', 'permission', 'created_at')
        read_only_fields = ('collection', 'shared_with_user', 'created_at')

    def create(self, validated_data):
        email = validated_data.pop('shared_with_email', None)
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError({"email": "User with this email not found."})
            validated_data['shared_with_user'] = user
        return super().create(validated_data)

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
