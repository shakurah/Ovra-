import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


class ChatSession(models.Model):
    """
    Model for grouping related chat messages into sessions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='chat_sessions',
        null=True,
        blank=True
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Auto-generated or user-defined session title"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Chat Session'
        verbose_name_plural = 'Chat Sessions'
    
    def __str__(self):
        return f"Session {self.id} - {self.title or 'Untitled'}"


class ChatLog(models.Model):
    """
    Model for storing individual chat messages and responses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    question = models.TextField(
        help_text="User's question in Spanish"
    )
    answer = models.TextField(
        help_text="AI-generated response with citations"
    )
    citations = models.JSONField(
        default=list,
        help_text="List of legal article citations used in the answer"
    )
    duration_ms = models.IntegerField(
        help_text="Response generation time in milliseconds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Additional tracking fields
    model_used = models.CharField(
        max_length=50,
        default='gpt-4o',
        help_text="OpenAI model used for generation"
    )
    retrieved_articles = models.JSONField(
        default=list,
        help_text="List of article IDs retrieved from vector search"
    )
    user_rating = models.IntegerField(
        null=True,
        blank=True,
        help_text="User satisfaction rating (1-5)"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['session', 'created_at']),
        ]
        verbose_name = 'Chat Log'
        verbose_name_plural = 'Chat Logs'
    
    def __str__(self):
        return f"Chat {self.id} - {self.created_at}"


class CostMetric(models.Model):
    """
    Model for tracking OpenAI API usage costs per chat interaction.
    """
    chat_log = models.OneToOneField(
        ChatLog,
        on_delete=models.CASCADE,
        related_name='cost_metric'
    )
    prompt_tokens = models.IntegerField(
        help_text="Number of tokens in the prompt"
    )
    completion_tokens = models.IntegerField(
        help_text="Number of tokens in the completion"
    )
    embedding_tokens = models.IntegerField(
        default=0,
        help_text="Number of tokens used for embeddings"
    )
    cost_eur = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        help_text="Total cost in EUR"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Breakdown by operation
    prompt_cost_eur = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        help_text="Cost of prompt tokens in EUR"
    )
    completion_cost_eur = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        help_text="Cost of completion tokens in EUR"
    )
    embedding_cost_eur = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        help_text="Cost of embedding tokens in EUR"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['cost_eur']),
        ]
        verbose_name = 'Cost Metric'
        verbose_name_plural = 'Cost Metrics'
    
    def __str__(self):
        return f"Cost for Chat {self.chat_log_id} - €{self.cost_eur}"
    
    @property
    def total_tokens(self):
        """Calculate total tokens used."""
        return self.prompt_tokens + self.completion_tokens + self.embedding_tokens
