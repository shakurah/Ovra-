from rest_framework import serializers
from apps.widget.models import UserEngagement
from apps.chat.models import ChatLog, ChatSession
from django.utils import timezone


class WidgetUserSerializer(serializers.ModelSerializer):
    """Serializer for widget user engagement."""
    
    class Meta:
        model = UserEngagement
        fields = [
            'email', 'privacy_accepted', 'terms_accepted',
            'source_website'
        ]
        read_only_fields = ['source_website']
    
    def validate(self, attrs):
        """Ensure privacy and terms are accepted."""
        if not attrs.get('privacy_accepted') or not attrs.get('terms_accepted'):
            raise serializers.ValidationError(
                "You must accept the privacy policy and terms of service to continue."
            )
        return attrs
    
    def create(self, validated_data):
        """Create or update user engagement record."""
        email = validated_data['email']
        validated_data['accepted_at'] = timezone.now()
        
        # Get or create the user engagement record
        user_engagement, created = UserEngagement.objects.update_or_create(
            email=email,
            defaults=validated_data
        )
        
        return user_engagement


class WidgetChatRequestSerializer(serializers.Serializer):
    """Serializer for widget chat requests."""
    
    email = serializers.EmailField(required=True)
    question = serializers.CharField(
        min_length=3,
        max_length=2000,
        trim_whitespace=True
    )
    session_id = serializers.UUIDField(required=False, allow_null=True)
    source_website = serializers.URLField(required=False, allow_blank=True)
    
    def validate_question(self, value):
        """Validate the question."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Please enter a valid question (minimum 3 characters)."
            )
        return value.strip()


class WidgetChatResponseSerializer(serializers.Serializer):
    """Serializer for widget chat responses."""
    
    answer = serializers.CharField()
    citations = serializers.JSONField(default=list)
    session_id = serializers.UUIDField()
    chat_id = serializers.UUIDField()
    duration_ms = serializers.IntegerField()


class WidgetFeedbackSerializer(serializers.Serializer):
    """Serializer for widget feedback."""
    
    chat_id = serializers.UUIDField()
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    helpful = serializers.BooleanField(required=False)
    
    def validate(self, attrs):
        """Ensure at least one feedback type is provided."""
        if 'rating' not in attrs and 'helpful' not in attrs:
            raise serializers.ValidationError(
                "Please provide either a rating or helpful feedback."
            )
        return attrs