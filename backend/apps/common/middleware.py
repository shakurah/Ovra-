"""
Common middleware for the Ovra AI Tax Assistant.
"""
import uuid
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from apps.common.responses import APIResponse

logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware to add a unique request ID to each request and response.
    """
    
    def process_request(self, request):
        """Add request ID to the request object."""
        request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))
        request.request_id = request_id
        request.META['X-Request-ID'] = request_id
        return None
    
    def process_response(self, request, response):
        """Add request ID to the response headers."""
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log request and response details.
    """
    
    def process_request(self, request):
        """Log incoming request details."""
        request.start_time = time.time()
        
        logger.info(
            "Request started",
            extra={
                'request_id': getattr(request, 'request_id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'user': str(request.user) if hasattr(request, 'user') else 'anonymous',
                'ip': self.get_client_ip(request),
            }
        )
        return None
    
    def process_response(self, request, response):
        """Log response details."""
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000  # Convert to ms
            
            logger.info(
                "Request completed",
                extra={
                    'request_id': getattr(request, 'request_id', 'unknown'),
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration, 2),
                }
            )
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware to handle unexpected errors and return consistent error responses.
    """
    
    def process_exception(self, request, exception):
        """Handle exceptions and return consistent error responses."""
        logger.error(
            f"Unhandled exception: {str(exception)}",
            exc_info=True,
            extra={
                'request_id': getattr(request, 'request_id', 'unknown'),
                'method': request.method,
                'path': request.path,
            }
        )
        
        # Don't handle exceptions in DEBUG mode
        from django.conf import settings
        if settings.DEBUG:
            return None
            
        # Return a generic error response
        return APIResponse.server_error(
            message="An unexpected error occurred. Please try again later.",
            request_id=getattr(request, 'request_id', 'unknown')
        )


class CORSMiddleware(MiddlewareMixin):
    """
    Additional CORS handling middleware for specific needs.
    Note: This supplements django-cors-headers, not replaces it.
    """
    
    def process_response(self, request, response):
        """Add additional CORS headers if needed."""
        # Add timing header for performance monitoring
        if hasattr(request, 'start_time'):
            duration = (time.time() - request.start_time) * 1000
            response['X-Response-Time'] = f"{duration:.2f}ms"
            
        return response 