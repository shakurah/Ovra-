import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import log_api_request, log_api_response, log_error

logger = logging.getLogger("ovra.middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses with detailed information.
    """
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each HTTP request and log relevant information.
        """
        start_time = time.time()
        
        # Extract request information
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        content_type = request.headers.get("content-type", "")
        request_size = request.headers.get("content-length", "0")
        
        # Get user ID if available (from JWT token or session)
        user_id = await self.get_user_id(request)
        
        # Log incoming request
        if self.log_requests:
            log_api_request(
                endpoint=str(request.url.path),
                method=request.method,
                user_id=user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                content_type=content_type,
                request_size=request_size,
                query_params=str(request.query_params) if request.query_params else None
            )
        
        # Log request body for POST/PUT/PATCH requests (excluding sensitive data)
        await self.log_request_body(request)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log response
            if self.log_responses:
                response_size = response.headers.get("content-length", "unknown")
                log_api_response(
                    endpoint=str(request.url.path),
                    method=request.method,
                    status_code=response.status_code,
                    response_time_ms=process_time,
                    user_id=user_id,
                    response_size=response_size,
                    content_type=response.headers.get("content-type", "")
                )
            
            # Add response time to headers
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log errors
            process_time = (time.time() - start_time) * 1000
            log_error(
                error=e,
                context=f"Request processing {request.method} {request.url.path}",
                user_id=user_id,
                ip_address=client_ip,
                response_time_ms=process_time
            )
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request headers."""
        # Check for forwarded headers first (for proxy/load balancer setups)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    async def get_user_id(self, request: Request) -> str:
        """Extract user ID from request (JWT token, session, etc.)."""
        try:
            # Check if user is available in request state (set by auth middleware)
            if hasattr(request.state, "user") and request.state.user:
                return str(request.state.user.id)
            
            # Try to extract from Authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # In a real implementation, you'd decode the JWT token here
                # For now, just indicate that auth header is present
                return "authenticated_user"
            
            return "anonymous"
            
        except Exception as e:
            logger.warning(f"Could not extract user ID: {e}")
            return "unknown"
    
    async def log_request_body(self, request: Request):
        """Log request body for relevant methods, excluding sensitive data."""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read the request body
                body = await request.body()
                if body:
                    content_type = request.headers.get("content-type", "")
                    
                    if "application/json" in content_type:
                        try:
                            body_json = json.loads(body.decode("utf-8"))
                            # Filter out sensitive fields
                            filtered_body = self.filter_sensitive_data(body_json)
                            logger.info(f"Request body for {request.method} {request.url.path}: {json.dumps(filtered_body, indent=2)}")
                        except json.JSONDecodeError:
                            logger.info(f"Request body for {request.method} {request.url.path}: <invalid JSON>")
                    else:
                        # For non-JSON content, just log the size
                        logger.info(f"Request body for {request.method} {request.url.path}: <{len(body)} bytes of {content_type}>")
                        
            except Exception as e:
                logger.warning(f"Could not log request body: {e}")
    
    def filter_sensitive_data(self, data):
        """Remove sensitive information from request body before logging."""
        if isinstance(data, dict):
            sensitive_fields = {
                "password", "confirm_password", "old_password", "new_password",
                "token", "access_token", "refresh_token", "api_key", "secret",
                "credit_card", "ssn", "social_security"
            }
            
            filtered = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in sensitive_fields):
                    filtered[key] = "***FILTERED***"
                elif isinstance(value, (dict, list)):
                    filtered[key] = self.filter_sensitive_data(value)
                else:
                    filtered[key] = value
            return filtered
        elif isinstance(data, list):
            return [self.filter_sensitive_data(item) for item in data]
        else:
            return data