from django.db import models
from pgvector.django import VectorField
import uuid
from django.utils import timezone


class LegalDocument(models.Model):
    """
    Model to store legal documents and their metadata.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500)
    filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=1000)
    document_type = models.CharField(max_length=100, help_text="Type of legal document (e.g., 'VAT Law', 'IRPF Law')")

    # Enhanced metadata for BOE documents
    document_name = models.CharField(max_length=500, null=True, blank=True, help_text="Official document name")
    publication_date = models.DateField(null=True, blank=True, help_text="Official publication date")
    boe_number = models.CharField(max_length=50, null=True, blank=True, help_text="BOE number (e.g., BOE-A-2023-12345)")
    boe_id = models.CharField(max_length=100, null=True, blank=True, unique=True, help_text="BOE document ID for API items")
    boe_section = models.CharField(max_length=100, null=True, blank=True, help_text="BOE section (e.g., 'I. Disposiciones generales')")
    department = models.CharField(max_length=200, null=True, blank=True, help_text="Department that issued the document")
    section = models.CharField(max_length=200, null=True, blank=True, help_text="BOE section name")
    issuing_authority = models.CharField(max_length=300, null=True, blank=True, help_text="Authority that issued the document")
    metadata = models.JSONField(null=True, blank=True, help_text="Additional metadata for API items")
    legal_status = models.CharField(max_length=50, default='active', choices=[
        ('active', 'Active'),
        ('modified', 'Modified'),
        ('repealed', 'Repealed'),
        ('superseded', 'Superseded'),
        ('unknown', 'Unknown')
    ], help_text="Current legal status of the document")
    effective_date = models.DateField(null=True, blank=True, help_text="Date when the law/regulation became effective")

    # Document processing metadata
    total_pages = models.IntegerField(null=True, blank=True)
    total_chunks = models.IntegerField(default=0)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'legal_documents'
        ordering = ['-publication_date', 'title']
        indexes = [
            models.Index(fields=['document_type', 'publication_date']),
            models.Index(fields=['boe_number']),
            models.Index(fields=['legal_status', 'publication_date']),
            models.Index(fields=['publication_date']),
        ]

    def __str__(self):
        if self.publication_date:
            return f"{self.title} ({self.publication_date})"
        return f"{self.title} ({self.filename})"

    @property
    def is_recent(self):
        """Check if document is from the last 3 years"""
        if not self.publication_date:
            return False
        from datetime import date, timedelta
        three_years_ago = date.today() - timedelta(days=3*365)
        return self.publication_date >= three_years_ago

    @property
    def formatted_reference(self):
        """Get formatted legal reference for citations"""
        if self.boe_number and self.publication_date:
            return f"{self.boe_number} ({self.publication_date.strftime('%d/%m/%Y')})"
        elif self.publication_date:
            return f"BOE {self.publication_date.strftime('%d/%m/%Y')}"
        return self.filename


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


class CaptureLog(models.Model):
    """
    Model to log daily BOE capture processes for monitoring and debugging.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capture_date = models.DateField(help_text="Date of the BOE capture")
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='running')
    
    # Capture statistics
    documents_found = models.IntegerField(default=0, help_text="Number of documents found from API")
    documents_downloaded = models.IntegerField(default=0, help_text="Number of documents downloaded")
    documents_processed = models.IntegerField(default=0, help_text="Number of documents processed")
    embeddings_created = models.IntegerField(default=0, help_text="Number of embeddings created")
    
    # Timing information
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    
    # Processing metadata
    api_items_processed = models.IntegerField(default=0, help_text="Number of API items processed")
    pdf_files_processed = models.IntegerField(default=0, help_text="Number of PDF files processed")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'capture_logs'
        ordering = ['-capture_date', '-started_at']
        indexes = [
            models.Index(fields=['capture_date']),
            models.Index(fields=['status', 'capture_date']),
            models.Index(fields=['started_at']),
        ]
        unique_together = ['capture_date', 'started_at']
    
    def __str__(self):
        return f"Capture {self.capture_date} - {self.status}"
    
    @property
    def duration(self):
        """Calculate the duration of the capture process."""
        if self.completed_at:
            return self.completed_at - self.started_at
        return None
