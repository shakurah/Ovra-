from django.contrib import admin
from django.db import models
from .models import LegalDocument, DocumentChunk, EmbeddingSearchLog, CaptureLog


@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'document_type', 'total_pages', 'total_chunks', 'processed_at', 'created_at']
    list_filter = ['document_type', 'processed_at', 'created_at']
    search_fields = ['title', 'filename', 'document_type']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'content_preview', 'token_count', 'created_at']
    list_filter = ['document__document_type', 'embedding_model', 'created_at']
    search_fields = ['content', 'document__title']
    readonly_fields = ['id', 'content_hash', 'created_at', 'updated_at']
    ordering = ['document', 'chunk_index']

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(EmbeddingSearchLog)
class EmbeddingSearchLogAdmin(admin.ModelAdmin):
    list_display = ['query_preview', 'results_count', 'similarity_threshold', 'execution_time_ms', 'created_at']
    list_filter = ['results_count', 'similarity_threshold', 'created_at']
    search_fields = ['query']
    readonly_fields = ['id', 'created_at']
    ordering = ['-created_at']

    def query_preview(self, obj):
        return obj.query[:50] + "..." if len(obj.query) > 50 else obj.query
    query_preview.short_description = 'Query Preview'


@admin.register(CaptureLog)
class CaptureLogAdmin(admin.ModelAdmin):
    """Admin configuration for CaptureLog model."""
    
    list_display = [
        'capture_date', 'status', 'documents_found', 'documents_processed', 
        'embeddings_created', 'duration_display', 'started_at'
    ]
    list_filter = ['status', 'capture_date', 'started_at']
    search_fields = ['capture_date', 'error_message']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'duration_display'
    ]
    ordering = ['-capture_date', '-started_at']
    date_hierarchy = 'capture_date'
    
    fieldsets = (
        ('Capture Information', {
            'fields': ('id', 'capture_date', 'status', 'retry_count')
        }),
        ('Statistics', {
            'fields': (
                'documents_found', 'documents_downloaded', 'documents_processed',
                'embeddings_created', 'api_items_processed', 'pdf_files_processed'
            )
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_display')
        }),
        ('Error Handling', {
            'fields': ('error_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['retry_failed_captures']
    
    def duration_display(self, obj):
        """Display the duration of the capture process."""
        if obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return str(duration)
        return "In progress"
    duration_display.short_description = 'Duration'
    
    def retry_failed_captures(self, request, queryset):
        """Action to retry failed capture processes."""
        failed_captures = queryset.filter(status='failed')
        count = failed_captures.count()
        if count > 0:
            # Reset status to allow retry
            failed_captures.update(status='running', retry_count=models.F('retry_count') + 1)
            self.message_user(request, f'{count} failed captures marked for retry.')
        else:
            self.message_user(request, 'No failed captures selected.')
    retry_failed_captures.short_description = 'Retry failed captures'
