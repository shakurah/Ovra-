"""
Serializers for the chat application.
"""
from rest_framework import serializers
from apps.chat.models import ChatLog, ChatSession, CostMetric
from apps.common.serializers import BaseModelSerializer, UUIDPrimaryKeySerializer, TimestampSerializer


class ChatRequestSerializer(serializers.Serializer):
    """
    Serializer for chat request input.
    """
    question = serializers.CharField(
        required=True,
        min_length=3,
        max_length=2000,
        help_text="User's question in Spanish about tax law"
    )
    session_id = serializers.UUIDField(
        required=False,
        help_text="Optional session ID to continue a conversation"
    )
    law_filter = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Optional filter for specific law (e.g., 'Ley del IVA')"
    )
    stream = serializers.BooleanField(
        default=False,
        help_text="Whether to stream the response"
    )
    
    def validate_question(self, value):
        """Validate the question field."""
        # Remove extra whitespace
        value = ' '.join(value.split())
        
        # Check if question is too short after cleanup
        if len(value) < 3:
            raise serializers.ValidationError(
                "Question is too short. Please provide more details."
            )
        
        return value


class CitationSerializer(serializers.Serializer):
    """
    Serializer for legal article citations.
    """
    article_num = serializers.CharField()
    law = serializers.CharField()
    excerpt = serializers.CharField()
    relevance_score = serializers.FloatField(required=False)
    source = serializers.CharField(required=False)


class ChatResponseSerializer(serializers.Serializer):
    """
    Serializer for chat response output.
    """
    id = serializers.UUIDField()
    question = serializers.CharField()
    answer = serializers.CharField()
    citations = CitationSerializer(many=True)
    session_id = serializers.UUIDField(required=False)
    created_at = serializers.DateTimeField()
    duration_ms = serializers.IntegerField()
    model_used = serializers.CharField()


class ChatSessionSerializer(BaseModelSerializer, UUIDPrimaryKeySerializer, TimestampSerializer):
    """
    Serializer for chat sessions.
    """
    message_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'created_at', 'updated_at', 
            'is_active', 'message_count', 'last_message_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        """Get the number of messages in the session."""
        return obj.messages.count()
    
    def get_last_message_at(self, obj):
        """Get the timestamp of the last message."""
        last_message = obj.messages.order_by('-created_at').first()
        return last_message.created_at if last_message else None


class ChatLogSerializer(BaseModelSerializer, UUIDPrimaryKeySerializer):
    """
    Serializer for chat logs.
    """
    cost_metric = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatLog
        fields = [
            'id', 'session', 'question', 'answer', 'citations',
            'duration_ms', 'created_at', 'model_used', 
            'retrieved_articles', 'user_rating', 'cost_metric'
        ]
        read_only_fields = [
            'id', 'created_at', 'duration_ms', 
            'model_used', 'retrieved_articles'
        ]
    
    def get_cost_metric(self, obj):
        """Get cost metrics for the chat."""
        try:
            cost = obj.cost_metric
            return {
                'prompt_tokens': cost.prompt_tokens,
                'completion_tokens': cost.completion_tokens,
                'total_tokens': cost.total_tokens,
                'cost_eur': float(cost.cost_eur)
            }
        except CostMetric.DoesNotExist:
            return None


class ChatStatsSerializer(serializers.Serializer):
    """
    Serializer for chat statistics.
    """
    total_chats = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    avg_response_time_ms = serializers.FloatField()
    total_cost_eur = serializers.DecimalField(max_digits=10, decimal_places=6)
    period = serializers.CharField()
    
    # Breakdown by model
    model_usage = serializers.DictField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # Daily stats
    daily_stats = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


class RatingUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating chat rating.
    """
    rating = serializers.IntegerField(min_value=1, max_value=5)
    feedback = serializers.CharField(required=False, allow_blank=True, max_length=1000) 