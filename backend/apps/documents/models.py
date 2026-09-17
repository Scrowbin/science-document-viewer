from django.db import models
from django.conf import settings
from ..collections_app.models import Collection

# Shared permission level choices — mirrors CollectionShare.PERMISSION_CHOICES.
# Intentionally kept identical: VIEW < COMMENT < EDIT hierarchy.
PERMISSION_CHOICES = (
    ('VIEW', 'View Only'),
    ('COMMENT', 'Comment / Annotate'),
    ('EDIT', 'Full Edit'),
)

class Author(models.Model):
    first_name = models.CharField(max_length=150, blank=True, default='')
    last_name = models.CharField(max_length=150)

    class Meta:
        db_table = 'authors'

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'tags'

    def __str__(self):
        return self.name

class Domain(models.Model):
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'domains'

    def __str__(self):
        return self.name

class Document(models.Model):
    RAG_STATUS_CHOICES = (
        ('PENDING', 'Pending Ingestion'),
        ('INDEXING', 'Indexing in Progress'),
        ('INDEXED', 'Indexed Successfully'),
        ('FAILED', 'Indexing Failed'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_documents'
    )
    primary_collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_documents'
    )
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=255, blank=True, default='')
    item_type = models.CharField(max_length=100, default='journalArticle')
    repository = models.CharField(max_length=255, blank=True, default='')
    archive_id = models.CharField(max_length=100, blank=True, default='')
    doi = models.CharField(max_length=255, blank=True, default='', db_index=True)
    url = models.URLField(max_length=1000, blank=True, default='')
    genre = models.CharField(max_length=100, blank=True, default='')
    date = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=50, blank=True, default='English')
    license = models.CharField(max_length=100, blank=True, default='')
    version = models.CharField(max_length=50, blank=True, default='1.0')
    citation_key = models.CharField(max_length=100, blank=True, default='')
    loc_in_archive = models.CharField(max_length=255, blank=True, default='')

    # Physical File storage
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)

    # RAG Status
    rag_status = models.CharField(max_length=50, choices=RAG_STATUS_CHOICES, default='PENDING')

    # Flags & Timestamps
    extra = models.TextField(blank=True, default='')
    in_trash = models.BooleanField(default=False)
    is_publication = models.BooleanField(default=False)
    is_duplicate = models.BooleanField(default=False)
    last_read = models.DateTimeField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Many-to-Many Relationships through junction tables
    authors = models.ManyToManyField(Author, through='DocumentAuthor', related_name='documents')
    tags = models.ManyToManyField(Tag, through='DocumentTag', related_name='documents')
    domains = models.ManyToManyField(Domain, through='DocumentDomain', related_name='documents')
    collections = models.ManyToManyField(Collection, through='DocumentCollection', related_name='documents')

    class Meta:
        db_table = 'documents'
        ordering = ['-date_modified']

    def __str__(self):
        return self.title

class DocumentAuthor(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    author_order = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = 'document_authors'
        unique_together = ('document', 'author')
        ordering = ['author_order']

class DocumentTag(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        db_table = 'document_tags'
        unique_together = ('document', 'tag')

class DocumentDomain(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)

    class Meta:
        db_table = 'document_domains'
        unique_together = ('document', 'domain')

class DocumentCollection(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)

    class Meta:
        db_table = 'document_collections'
        unique_together = ('document', 'collection')

class Annotation(models.Model):
    TYPE_CHOICES = (
        ('highlight', 'Highlight'),
        ('note', 'Sticky Note'),
        ('underline', 'Underline'),
    )

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='annotations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='annotations')
    page_number = models.PositiveIntegerField(default=1)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='highlight')
    color = models.CharField(max_length=50, default='#ffeb3b')
    rects = models.JSONField(default=list, blank=True)
    selected_text = models.TextField(blank=True, default='')
    comment = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'annotations'
        ordering = ['page_number', 'created_at']

class Note(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_notes')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notes'
        ordering = ['-updated_at']

class DocumentShare(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shares')
    shared_with_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shared_documents')
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='VIEW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_shares'
        unique_together = ('document', 'shared_with_user')

class RelatedDocument(models.Model):
    document_1 = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='related_from')
    document_2 = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='related_to')
    relation_type = models.CharField(max_length=50, default='manual')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'related_documents'
        unique_together = ('document_1', 'document_2')
