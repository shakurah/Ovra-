from django.contrib import admin
from apps.legal.models import LegalArticle


@admin.register(LegalArticle)
class LegalArticleAdmin(admin.ModelAdmin):
    list_display = ['law', 'article_num', 'title_preview', 'is_active', 'sync_ts']
    list_filter = ['law', 'is_active', 'sync_ts', 'last_modified']
    search_fields = ['law', 'article_num', 'title', 'text']
    date_hierarchy = 'sync_ts'
    ordering = ['law', 'article_num']
    readonly_fields = ['id', 'sync_ts']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('law', 'article_num', 'title', 'is_active')
        }),
        ('Content', {
            'fields': ('text', 'source_url')
        }),
        ('Metadata', {
            'fields': ('id', 'sync_ts', 'last_modified'),
            'classes': ('collapse',)
        })
    )
    
    def title_preview(self, obj):
        """Show first 60 characters of the title."""
        if obj.title:
            return obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
        return '-'
    title_preview.short_description = 'Title'
