"""
Common serializers for the Ovra AI Tax Assistant.
"""
from rest_framework import serializers
from typing import Any, Dict, List, Optional


class BaseResponseSerializer(serializers.Serializer):
    """
    Base serializer for all API responses.
    """
    code = serializers.IntegerField(read_only=True)
    is_success = serializers.BooleanField(read_only=True)
    message = serializers.CharField(read_only=True)
    data = serializers.JSONField(read_only=True, required=False)
    error_code = serializers.CharField(read_only=True, required=False)
    

class PaginationSerializer(serializers.Serializer):
    """
    Serializer for pagination metadata.
    """
    total = serializers.IntegerField(read_only=True)
    page = serializers.IntegerField(read_only=True)
    page_size = serializers.IntegerField(read_only=True)
    total_pages = serializers.IntegerField(read_only=True)
    has_next = serializers.BooleanField(read_only=True)
    has_previous = serializers.BooleanField(read_only=True)


class PaginatedResponseSerializer(BaseResponseSerializer):
    """
    Serializer for paginated API responses.
    """
    class DataSerializer(serializers.Serializer):
        items = serializers.ListField(read_only=True)
        pagination = PaginationSerializer(read_only=True)
    
    data = DataSerializer(read_only=True)


class ErrorDetailSerializer(serializers.Serializer):
    """
    Serializer for detailed error information.
    """
    field = serializers.CharField(required=False)
    message = serializers.CharField()
    code = serializers.CharField(required=False)


class ValidationErrorSerializer(BaseResponseSerializer):
    """
    Serializer for validation error responses.
    """
    class DataSerializer(serializers.Serializer):
        errors = serializers.DictField(
            child=serializers.ListField(child=serializers.CharField()),
            required=False
        )
    
    data = DataSerializer(read_only=True)


class TimestampSerializer(serializers.Serializer):
    """
    Common serializer for timestamp fields.
    """
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UUIDPrimaryKeySerializer(serializers.Serializer):
    """
    Common serializer for UUID primary key.
    """
    id = serializers.UUIDField(read_only=True)


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base model serializer with common functionality.
    """
    
    def to_representation(self, instance):
        """
        Convert model instance to dictionary representation.
        Handles common transformations.
        """
        data = super().to_representation(instance)
        
        # Remove None values if configured
        if getattr(self.Meta, 'remove_none_values', False):
            data = {k: v for k, v in data.items() if v is not None}
            
        return data
    
    class Meta:
        abstract = True
        remove_none_values = False 