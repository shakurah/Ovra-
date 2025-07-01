"""
Custom exception handling for the Ovra AI Tax Assistant API.
"""
import uuid
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import IntegrityError


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses.
    
    Format:
    {
        "detail": "Human-readable message",
        "code": "UPPER_SNAKE_CASE_CODE"
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get or generate request ID
    request = context.get('request')
    request_id = None
    if request:
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
    
    if response is not None:
        # Customize the response data
        custom_response_data = {
            'detail': 'An error occurred',
            'code': 'UNKNOWN_ERROR'
        }
        
        # Map different exception types to codes
        if hasattr(exc, 'default_code'):
            code_mapping = {
                'authentication_failed': 'AUTH_FAILED',
                'not_authenticated': 'NOT_AUTHENTICATED',
                'permission_denied': 'PERMISSION_DENIED',
                'not_found': 'NOT_FOUND',
                'method_not_allowed': 'METHOD_NOT_ALLOWED',
                'unsupported_media_type': 'UNSUPPORTED_MEDIA_TYPE',
                'throttled': 'RATE_LIMIT_EXCEEDED',
                'validation_error': 'VALIDATION_ERROR',
                'parse_error': 'PARSE_ERROR',
            }
            custom_response_data['code'] = code_mapping.get(
                exc.default_code, 
                exc.default_code.upper().replace(' ', '_')
            )
        
        # Extract detail message
        if hasattr(response.data, 'get'):
            detail = response.data.get('detail')
            if detail:
                custom_response_data['detail'] = str(detail)
            elif isinstance(response.data, dict):
                # For validation errors, combine field errors
                errors = []
                for field, messages in response.data.items():
                    if isinstance(messages, list):
                        errors.extend([f"{field}: {msg}" for msg in messages])
                    else:
                        errors.append(f"{field}: {messages}")
                custom_response_data['detail'] = '; '.join(errors)
                custom_response_data['code'] = 'VALIDATION_ERROR'
        elif isinstance(response.data, list) and response.data:
            custom_response_data['detail'] = str(response.data[0])
        
        response.data = custom_response_data
        
        # Add request ID header
        if request_id:
            response['X-Request-ID'] = request_id
    
    # Handle non-DRF exceptions
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        data = {
            'detail': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }
        
        if isinstance(exc, ValidationError):
            status_code = status.HTTP_400_BAD_REQUEST
            data = {
                'detail': str(exc),
                'code': 'VALIDATION_ERROR'
            }
        elif isinstance(exc, IntegrityError):
            status_code = status.HTTP_400_BAD_REQUEST
            data = {
                'detail': 'Database integrity error',
                'code': 'INTEGRITY_ERROR'
            }
        
        response = Response(data, status=status_code)
        if request_id:
            response['X-Request-ID'] = request_id
    
    return response


class OvraAPIException(Exception):
    """Base exception for Ovra-specific errors."""
    default_detail = 'An error occurred'
    default_code = 'OVRA_ERROR'
    
    def __init__(self, detail=None, code=None):
        self.detail = detail or self.default_detail
        self.code = code or self.default_code
        super().__init__(self.detail)


class OpenAIException(OvraAPIException):
    """Exception for OpenAI API errors."""
    default_detail = 'OpenAI service error'
    default_code = 'OPENAI_ERROR'


class VectorStoreException(OvraAPIException):
    """Exception for vector store errors."""
    default_detail = 'Vector store error'
    default_code = 'VECTOR_STORE_ERROR'


class BOESyncException(OvraAPIException):
    """Exception for BOE synchronization errors."""
    default_detail = 'BOE synchronization error'
    default_code = 'BOE_SYNC_ERROR' 