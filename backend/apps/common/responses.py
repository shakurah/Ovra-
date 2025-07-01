"""
Generic response utilities for consistent API responses.
"""
from typing import Any, Optional, Dict, List, Union
from rest_framework.response import Response
from rest_framework import status as http_status


class APIResponse:
    """
    Generic API response class for consistent response structure.
    
    All API responses will follow this format:
    {
        "code": 200,
        "is_success": true,
        "message": "Success message",
        "data": {...}
    }
    """
    
    @staticmethod
    def success(
        data: Optional[Union[Dict, List, Any]] = None,
        message: str = "Request successful",
        status: int = http_status.HTTP_200_OK,
        **kwargs
    ) -> Response:
        """
        Create a successful API response.
        
        Args:
            data: The response data (can be dict, list, or any serializable object)
            message: Success message
            status: HTTP status code
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object
        """
        response_data = {
            "code": status,
            "is_success": True,
            "message": message,
            "data": data or {}
        }
        
        # Add any additional kwargs to the response
        response_data.update(kwargs)
        
        return Response(response_data, status=status)
    
    @staticmethod
    def error(
        message: str = "An error occurred",
        data: Optional[Union[Dict, List, Any]] = None,
        status: int = http_status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        **kwargs
    ) -> Response:
        """
        Create an error API response.
        
        Args:
            message: Error message
            data: Additional error data (optional)
            status: HTTP status code
            error_code: Specific error code for client handling
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object
        """
        response_data = {
            "code": status,
            "is_success": False,
            "message": message,
            "data": data or {}
        }
        
        if error_code:
            response_data["error_code"] = error_code
            
        # Add any additional kwargs to the response
        response_data.update(kwargs)
        
        return Response(response_data, status=status)
    
    @staticmethod
    def created(
        data: Optional[Union[Dict, List, Any]] = None,
        message: str = "Resource created successfully",
        **kwargs
    ) -> Response:
        """
        Create a response for successful resource creation.
        
        Args:
            data: The created resource data
            message: Success message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 201 status
        """
        return APIResponse.success(
            data=data,
            message=message,
            status=http_status.HTTP_201_CREATED,
            **kwargs
        )
    
    @staticmethod
    def deleted(
        message: str = "Resource deleted successfully",
        **kwargs
    ) -> Response:
        """
        Create a response for successful resource deletion.
        
        Args:
            message: Success message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 204 status
        """
        return APIResponse.success(
            data=None,
            message=message,
            status=http_status.HTTP_204_NO_CONTENT,
            **kwargs
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        **kwargs
    ) -> Response:
        """
        Create a response for resource not found.
        
        Args:
            message: Error message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 404 status
        """
        return APIResponse.error(
            message=message,
            status=http_status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            **kwargs
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Unauthorized access",
        **kwargs
    ) -> Response:
        """
        Create a response for unauthorized access.
        
        Args:
            message: Error message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 401 status
        """
        return APIResponse.error(
            message=message,
            status=http_status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            **kwargs
        )
    
    @staticmethod
    def forbidden(
        message: str = "Access forbidden",
        **kwargs
    ) -> Response:
        """
        Create a response for forbidden access.
        
        Args:
            message: Error message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 403 status
        """
        return APIResponse.error(
            message=message,
            status=http_status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            **kwargs
        )
    
    @staticmethod
    def validation_error(
        errors: Union[Dict, List, str],
        message: str = "Validation failed",
        **kwargs
    ) -> Response:
        """
        Create a response for validation errors.
        
        Args:
            errors: Validation errors (can be dict, list, or string)
            message: Error message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 422 status
        """
        return APIResponse.error(
            message=message,
            data={"errors": errors} if not isinstance(errors, dict) else errors,
            status=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            **kwargs
        )
    
    @staticmethod
    def server_error(
        message: str = "Internal server error",
        **kwargs
    ) -> Response:
        """
        Create a response for server errors.
        
        Args:
            message: Error message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with 500 status
        """
        return APIResponse.error(
            message=message,
            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="SERVER_ERROR",
            **kwargs
        )
    
    @staticmethod
    def paginated(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        message: str = "Data retrieved successfully",
        **kwargs
    ) -> Response:
        """
        Create a paginated response.
        
        Args:
            data: List of items for current page
            total: Total number of items
            page: Current page number
            page_size: Items per page
            message: Success message
            **kwargs: Additional response parameters
            
        Returns:
            DRF Response object with pagination metadata
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        
        pagination_data = {
            "items": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }
        
        return APIResponse.success(
            data=pagination_data,
            message=message,
            **kwargs
        ) 