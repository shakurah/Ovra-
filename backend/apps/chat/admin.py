from django.contrib import admin
from apps.chat.models import ChatSession, ChatLog, CostMetric


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['title', 'user__username', 'user__email']
    date_hierarchy = 'created_at'
    ordering = ['-updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'question_preview', 'created_at', 'duration_ms', 'user_rating']
    list_filter = ['created_at', 'model_used', 'user_rating']
    search_fields = ['question', 'answer']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'duration_ms', 'retrieved_articles', 'citations']
    
    def question_preview(self, obj):
        """Show first 50 characters of the question."""
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'


@admin.register(CostMetric)
class CostMetricAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat_log', 'total_tokens', 'cost_eur', 'created_at']
    list_filter = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'total_tokens']
    
    def total_tokens(self, obj):
        """Calculate total tokens."""
        return obj.total_tokens
    total_tokens.short_description = 'Total Tokens'
