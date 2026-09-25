from django.db import models


class Document(models.Model):
    title = models.CharField(max_length=255, null=True, blank=True)
    short_title = models.CharField(max_length=255, null=True, blank=True)
    item_type = models.CharField(max_length=255, null=True, blank=True)
    repository = models.CharField(max_length=255, null=True, blank=True)
    archive_id = models.CharField(max_length=255, null=True, blank=True)
    doi = models.CharField(max_length=255, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    genre = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)
    license = models.CharField(max_length=255, null=True, blank=True)
    version = models.CharField(max_length=255, null=True, blank=True)
    citation_key = models.CharField(max_length=255, null=True, blank=True)
    loc_in_archive = models.CharField(max_length=255, null=True, blank=True)
    date_added = models.DateTimeField(null=True, blank=True)
    extra = models.TextField(null=True, blank=True)
    date_modified = models.DateTimeField(null=True, blank=True)

    authors = models.ManyToManyField(
        "Author",
        through="DocumentAuthor",
        related_name="documents",
    )

    tags = models.ManyToManyField(
        "Tag",
        through="DocumentTag",
        related_name="documents",
    )

    domains = models.ManyToManyField(
        "Domain",
        through="DocumentDomain",
        related_name="documents",
    )

    groups = models.ManyToManyField(
        "DocumentGroup",
        through="DocumentGroupMember",
        related_name="documents",
    )

    def __str__(self):
        return self.title or f"Document {self.id}"


class Author(models.Model):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


class DocumentAuthor(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
    )
    author_order = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "author"],
                name="unique_document_author",
            )
        ]
        ordering = ["author_order"]


class Tag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class DocumentTag(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "tag"],
                name="unique_document_tag",
            )
        ]


class Domain(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class DocumentDomain(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
    )
    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "domain"],
                name="unique_document_domain",
            )
        ]


class DocumentGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    color = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class DocumentGroupMember(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
    )
    group = models.ForeignKey(
        DocumentGroup,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "group"],
                name="unique_document_group_member",
            )
        ]
