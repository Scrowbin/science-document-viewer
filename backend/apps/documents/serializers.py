from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Author, Tag, Domain, Document, DocumentAuthor,
    Annotation, Note, DocumentShare, RelatedDocument
)

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'first_name', 'last_name')

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('id', 'name')

class AnnotationSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Annotation
        fields = (
            'id', 'document', 'user', 'username', 'page_number',
            'type', 'color', 'rects', 'selected_text', 'comment',
            'created_at', 'updated_at'
        )
        read_only_fields = ('document', 'user', 'created_at', 'updated_at')

class NoteSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Note
        fields = ('id', 'user', 'username', 'document', 'title', 'content', 'created_at', 'updated_at')
        read_only_fields = ('user', 'created_at', 'updated_at')

class DocumentShareSerializer(serializers.ModelSerializer):
    shared_with_email = serializers.EmailField(write_only=True, required=False)
    shared_with_username = serializers.ReadOnlyField(source='shared_with_user.username')
    shared_with_email_display = serializers.ReadOnlyField(source='shared_with_user.email')

    class Meta:
        model = DocumentShare
        fields = (
            'id', 'document', 'shared_with_user', 'shared_with_email',
            'shared_with_username', 'shared_with_email_display',
            'permission', 'created_at'
        )
        read_only_fields = ('document', 'shared_with_user', 'created_at')

    def create(self, validated_data):
        email = validated_data.pop('shared_with_email', None)
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError({"email": "User with this email not found."})
            validated_data['shared_with_user'] = user
        return super().create(validated_data)

class RelatedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatedDocument
        fields = ('id', 'document_1', 'document_2', 'relation_type', 'created_at')

class FileUrlMixin:
    """Provides a consistent get_file_url method for document serializers."""

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None


class DocumentListSerializer(FileUrlMixin, serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    primary_collection_name = serializers.ReadOnlyField(source='primary_collection.name')
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'title', 'short_title', 'item_type', 'repository',
            'doi', 'url', 'date', 'authors', 'tags', 'primary_collection',
            'primary_collection_name', 'file_url', 'file_size', 'rag_status',
            'in_trash', 'is_publication', 'is_duplicate', 'last_read',
            'date_added', 'date_modified'
        )

    def get_authors(self, obj):
        return [str(a) for a in obj.authors.all()]

class DocumentDetailSerializer(FileUrlMixin, serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    domains = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    primary_collection_name = serializers.ReadOnlyField(source='primary_collection.name')
    file_url = serializers.SerializerMethodField()
    owner_username = serializers.ReadOnlyField(source='owner.username')
    user_permission = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'owner', 'owner_username', 'user_permission',
            'title', 'short_title', 'item_type', 'repository', 'archive_id',
            'doi', 'url', 'genre', 'date', 'language', 'license', 'version',
            'citation_key', 'loc_in_archive', 'file_url', 'file_size',
            'rag_status', 'extra', 'in_trash', 'is_publication', 'is_duplicate',
            'last_read', 'primary_collection', 'primary_collection_name',
            'authors', 'tags', 'domains', 'date_added', 'date_modified'
        )

    def get_authors(self, obj):
        return [
            {'first_name': a.first_name, 'last_name': a.last_name, 'full_name': str(a)}
            for a in obj.authors.all()
        ]

    def get_user_permission(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return 'NONE'
        if obj.owner == request.user:
            return 'OWNER'
        share = obj.shares.filter(shared_with_user=request.user).first()
        if share:
            return share.permission
        if obj.primary_collection:
            col_share = obj.primary_collection.shares.filter(shared_with_user=request.user).first()
            if col_share:
                return col_share.permission
        return 'NONE'

class DocumentCreateUpdateSerializer(serializers.ModelSerializer):
    author_names = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    tag_names = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    domain_names = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    class Meta:
        model = Document
        fields = (
            'id', 'title', 'short_title', 'item_type', 'repository', 'archive_id',
            'doi', 'url', 'genre', 'date', 'language', 'license', 'version',
            'citation_key', 'loc_in_archive', 'file', 'primary_collection',
            'extra', 'in_trash', 'is_publication', 'is_duplicate', 'last_read',
            'author_names', 'tag_names', 'domain_names'
        )

    def create(self, validated_data):
        author_names = validated_data.pop('author_names', [])
        tag_names = validated_data.pop('tag_names', [])
        domain_names = validated_data.pop('domain_names', [])

        uploaded_file = validated_data.get('file')
        if uploaded_file:
            validated_data['file_size'] = uploaded_file.size

        document = Document.objects.create(**validated_data)
        self._set_m2m(document, author_names, tag_names, domain_names)
        return document

    def update(self, instance, validated_data):
        author_names = validated_data.pop('author_names', None)
        tag_names = validated_data.pop('tag_names', None)
        domain_names = validated_data.pop('domain_names', None)

        uploaded_file = validated_data.get('file')
        if uploaded_file:
            validated_data['file_size'] = uploaded_file.size

        document = super().update(instance, validated_data)

        if author_names is not None or tag_names is not None or domain_names is not None:
            self._set_m2m(
                document,
                author_names if author_names is not None else [],
                tag_names if tag_names is not None else [],
                domain_names if domain_names is not None else [],
                is_update=True
            )
        return document

    def _set_m2m(self, document, author_names, tag_names, domain_names, is_update=False):
        # Authors: global Zotero-style registry — same (first_name, last_name) pair is
        # intentionally shared across documents, matching Zotero's Author entity model.
        if author_names:
            if is_update:
                document.documentauthor_set.all().delete()
            for idx, name in enumerate(author_names, start=1):
                parts = name.strip().rsplit(' ', 1)
                first_name = parts[0] if len(parts) > 1 else ''
                last_name = parts[1] if len(parts) > 1 else parts[0]
                author, _ = Author.objects.get_or_create(first_name=first_name, last_name=last_name)
                DocumentAuthor.objects.create(document=document, author=author, author_order=idx)

        if tag_names:
            if is_update:
                document.tags.clear()
            for name in tag_names:
                clean_name = name.strip()
                if clean_name:
                    tag, _ = Tag.objects.get_or_create(name=clean_name)
                    document.tags.add(tag)

        if domain_names:
            if is_update:
                document.domains.clear()
            for name in domain_names:
                clean_name = name.strip()
                if clean_name:
                    domain, _ = Domain.objects.get_or_create(name=clean_name)
                    document.domains.add(domain)
