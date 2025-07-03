from django.contrib import admin
from .models import LegalDocument, DocumentChunk, EmbeddingSearchLog


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
