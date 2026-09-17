from django.db import models
from django.conf import settings

class Collection(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=50, blank=True, null=True, default='#3b82f6')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collections'
        ordering = ['name']

    def __str__(self):
        return self.name

class CollectionShare(models.Model):
    PERMISSION_CHOICES = (
        ('VIEW', 'View Only'),
        ('COMMENT', 'Comment'),
        ('EDIT', 'Edit'),
    )

    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    shared_with_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_collections'
    )
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='VIEW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'collection_shares'
        unique_together = ('collection', 'shared_with_user')

    def __str__(self):
        return f"{self.collection.name} shared with {self.shared_with_user.username} ({self.permission})"
