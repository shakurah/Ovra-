from django.db import models
from django.conf import settings
from pgvector.django import VectorField
import uuid

class SemanticCacheEntry(models.Model):
    """
    Stores a query/response pair plus a pgvector embedding and metadata.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    conversation_id = models.UUIDField(null=True, blank=True)
    query_text = models.TextField()
    response_text = models.TextField()
    # use 'dimensions' keyword accepted by pgvector.django
    embedding = VectorField(dimensions=1536, null=True, blank=True)  # adjust dimensions to your embedder
    fingerprint = models.CharField(max_length=64, db_index=True)
    tokens = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=100, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation_id"]),
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["fingerprint"]),
        ]

    def __str__(self):
        return f"SemanticCacheEntry({self.id}, conv={self.conversation_id})"
