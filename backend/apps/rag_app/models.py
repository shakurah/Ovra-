from django.db import models
from pgvector.django import VectorField
import uuid


class LegalDocument(models.Model):
    """
    Model to store legal documents and their metadata.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1000)
    document_type = models.CharField(max_length=100, help_text="Type of legal document (e.g., 'VAT Law', 'IRPF Law')")
    total_pages = models.IntegerField(null=True, blank=True)
    total_chunks = models.IntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'legal_documents'
        ordering = ['title']

    def __str__(self):
        return f"{self.title} ({self.filename})"


class DocumentChunk(models.Model):
    """
    Model to store document chunks with their embeddings and metadata.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(LegalDocument, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField(help_text="Sequential index of this chunk within the document")
    content = models.TextField(help_text="The actual text content of this chunk")
    content_hash = models.CharField(max_length=64, help_text="SHA-256 hash of content for deduplication")

    # Metadata
    page_numbers = models.JSONField(default=list, help_text="Page numbers this chunk spans")
    start_char = models.IntegerField(null=True, blank=True, help_text="Starting character position in document")
    end_char = models.IntegerField(null=True, blank=True, help_text="Ending character position in document")

    # Embedding data
    embedding_vector = VectorField(dimensions=1536, null=True, blank=True, help_text="Vector embedding of the content")
    embedding_model = models.CharField(max_length=100, default="text-embedding-3-small")

    # Processing metadata
    token_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_chunks'
        ordering = ['document', 'chunk_index']
        indexes = [
            models.Index(fields=['document', 'chunk_index']),
            models.Index(fields=['content_hash']),
        ]

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"


class EmbeddingSearchLog(models.Model):
    """
    Model to log embedding searches for analytics and debugging.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query = models.TextField(help_text="The search query")
    query_embedding = VectorField(dimensions=1536, null=True, blank=True)
    results_count = models.IntegerField(default=0)
    similarity_threshold = models.FloatField(null=True, blank=True)
    execution_time_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'embedding_search_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Search: {self.query[:50]}... ({self.results_count} results)"
