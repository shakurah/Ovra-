"""
RAG App API Views

This module contains API views for the RAG (Retrieval-Augmented Generation) system,
including daily BOE capture management, document processing, and embedding operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_ratelimit.decorators import ratelimit

from apps.common.responses import APIResponse
from apps.rag_app.models import CaptureLog, LegalDocument, DocumentChunk
from apps.rag_app.services.daily_capture_service import DailyBOECaptureService
from apps.rag_app.services.boe_service import BOEAPIService

logger = logging.getLogger(__name__)


class DailyCaptureView(APIView):
    """
    API view for managing daily BOE capture operations.
    
    Endpoints:
    - GET: Get capture configuration and status
    - POST: Trigger manual capture or setup scheduling
    - PUT: Update capture settings
    - DELETE: Stop scheduled captures
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='30/m', method='GET'), name='dispatch')
    def get(self, request):
        """Get daily capture status and configuration."""
        try:
            service = DailyBOECaptureService()
            status = service.get_capture_status()
            
            return APIResponse.success(
                data=status,
                message="Daily capture status retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error getting capture status: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="Failed to get capture status")
    
    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'), name='dispatch')
    def post(self, request):
        """Trigger manual capture or setup scheduling."""
        try:
            action = request.data.get('action', 'trigger')
            
            service = DailyBOECaptureService()
            
            if action == 'trigger':
                # Manual trigger
                date = request.data.get('date')  # Optional specific date
                result = service.trigger_manual_capture(date)
                
                if result['success']:
                    return APIResponse.success(
                        data=result,
                        message="Manual capture triggered successfully"
                    )
                else:
                    return APIResponse.error(
                        message=result.get('error', 'Failed to trigger capture'),
                        error_code='CAPTURE_TRIGGER_FAILED'
                    )
            
            elif action == 'schedule':
                # Setup daily scheduling
                capture_time = request.data.get('time', '08:00')
                result = service.setup_daily_schedule(capture_time)
                
                if result['success']:
                    return APIResponse.success(
                        data=result,
                        message="Daily capture scheduled successfully"
                    )
                else:
                    return APIResponse.error(
                        message=result.get('error', 'Failed to setup schedule'),
                        error_code='SCHEDULE_SETUP_FAILED'
                    )
            
            else:
                return APIResponse.validation_error(
                    errors={'action': ['Invalid action. Use "trigger" or "schedule"']},
                    message="Invalid action specified"
                )
                
        except Exception as e:
            logger.error(f"Error in daily capture POST: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="Failed to process capture request")
    
    @method_decorator(ratelimit(key='user', rate='5/m', method='DELETE'), name='dispatch')
    def delete(self, request):
        """Stop scheduled daily captures."""
        try:
            service = DailyBOECaptureService()
            result = service.stop_scheduled_capture()
            
            if result['success']:
                return APIResponse.success(
                    data=result,
                    message="Daily capture schedule stopped successfully"
                )
            else:
                return APIResponse.error(
                    message=result.get('error', 'Failed to stop schedule'),
                    error_code='SCHEDULE_STOP_FAILED'
                )
                
        except Exception as e:
            logger.error(f"Error stopping capture schedule: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="Failed to stop capture schedule")


class CaptureStatusView(APIView):
    """
    API view for getting detailed capture status and statistics.
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    @method_decorator(ratelimit(key='user', rate='60/m', method='GET'), name='dispatch')
    def get(self, request):
        """Get detailed capture status and statistics."""
        try:
            # Get recent capture logs
            recent_logs = CaptureLog.objects.filter(
                capture_date__gte=timezone.now().date() - timedelta(days=30)
            ).order_by('-capture_date')[:20]
            
            # Get summary statistics
            total_documents = LegalDocument.objects.count()
            boe_documents = LegalDocument.objects.filter(
                document_type__in=['BOE_Daily_Update', 'BOE_Summary']
            ).count()
            total_chunks = DocumentChunk.objects.count()
            
            # Calculate capture statistics
            successful_captures = recent_logs.filter(status='completed').count()
            failed_captures = recent_logs.filter(status='failed').count()
            
            status_data = {
                'summary': {
                    'total_documents': total_documents,
                    'boe_documents': boe_documents,
                    'total_chunks': total_chunks,
                    'last_capture': recent_logs.first().capture_date if recent_logs else None,
                },
                'recent_captures': {
                    'successful': successful_captures,
                    'failed': failed_captures,
                    'success_rate': (successful_captures / len(recent_logs) * 100) if recent_logs else 0
                },
                'recent_logs': [
                    {
                        'id': str(log.id),
                        'capture_date': log.capture_date.strftime('%Y-%m-%d'),
                        'status': log.status,
                        'documents_found': log.documents_found,
                        'documents_processed': log.documents_processed,
                        'embeddings_created': log.embeddings_created,
                        'started_at': log.started_at.isoformat(),
                        'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                        'duration': str(log.duration) if log.duration else None,
                        'error_message': log.error_message
                    }
                    for log in recent_logs
                ]
            }
            
            return APIResponse.success(
                data=status_data,
                message="Capture status retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error getting capture status: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="Failed to get capture status")


class CaptureLogsView(APIView):
    """
    API view for managing capture logs.
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='30/m', method='GET'), name='dispatch')
    def get(self, request):
        """Get capture logs with filtering and pagination."""
        try:
            # Get query parameters
            days = int(request.query_params.get('days', 30))
            status = request.query_params.get('status')
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            # Build query
            queryset = CaptureLog.objects.filter(
                capture_date__gte=timezone.now().date() - timedelta(days=days)
            )
            
            if status:
                queryset = queryset.filter(status=status)
            
            # Get total count
            total_count = queryset.count()
            
            # Apply pagination
            logs = queryset[offset:offset + limit]
            
            logs_data = {
                'total_count': total_count,
                'logs': [
                    {
                        'id': str(log.id),
                        'capture_date': log.capture_date.strftime('%Y-%m-%d'),
                        'status': log.status,
                        'documents_found': log.documents_found,
                        'documents_downloaded': log.documents_downloaded,
                        'documents_processed': log.documents_processed,
                        'embeddings_created': log.embeddings_created,
                        'started_at': log.started_at.isoformat(),
                        'completed_at': log.completed_at.isoformat() if log.completed_at else None,
                        'duration': str(log.duration) if log.duration else None,
                        'error_message': log.error_message,
                        'retry_count': log.retry_count
                    }
                    for log in logs
                ]
            }
            
            return APIResponse.success(
                data=logs_data,
                message="Capture logs retrieved successfully"
            )
            
        except ValueError as e:
            return APIResponse.validation_error(
                errors={'query_params': [str(e)]},
                message="Invalid query parameters"
            )
        except Exception as e:
            logger.error(f"Error getting capture logs: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="Failed to get capture logs")


class BOETestView(APIView):
    """
    API view for testing BOE API integration.
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(ratelimit(key='user', rate='10/m', method='POST'), name='dispatch')
    def post(self, request):
        """Test BOE API integration."""
        try:
            date = request.data.get('date')
            days_back = int(request.data.get('days_back', 3))
            
            service = BOEAPIService()
            
            # Test basic API connectivity
            summary = service.get_daily_summary(date)
            
            if not summary:
                return APIResponse.error(
                    message="Failed to connect to BOE API",
                    error_code='BOE_API_CONNECTION_FAILED'
                )
            
            # Test tax-related content search
            tax_items = service.search_tax_related_content(date)
            
            # Test recent updates
            recent_items = service.get_recent_tax_updates(days_back)
            
            test_results = {
                'api_connectivity': True,
                'summary_available': summary is not None,
                'tax_items_found': len(tax_items),
                'recent_updates_found': len(recent_items),
                'test_date': date or datetime.now().strftime('%Y%m%d'),
                'sample_items': [
                    {
                        'id': item.get('id'),
                        'title': item.get('title', '')[:100],
                        'department': item.get('department', ''),
                        'date': item.get('date')
                    }
                    for item in tax_items[:3]  # First 3 items
                ]
            }
            
            return APIResponse.success(
                data=test_results,
                message="BOE API test completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error testing BOE API: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="BOE API test failed")


class DocumentStatsView(APIView):
    """
    API view for getting document and embedding statistics.
    """
    
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    @method_decorator(ratelimit(key='user', rate='30/m', method='GET'), name='dispatch')
    def get(self, request):
        """Get document and embedding statistics."""
        try:
            # Document statistics
            total_documents = LegalDocument.objects.count()
            boe_summaries = LegalDocument.objects.filter(document_type='BOE_Summary').count()
            boe_daily_updates = LegalDocument.objects.filter(document_type='BOE_Daily_Update').count()
            processed_documents = LegalDocument.objects.filter(processed_at__isnull=False).count()
            
            # Chunk statistics
            total_chunks = DocumentChunk.objects.count()
            chunks_with_embeddings = DocumentChunk.objects.filter(embedding_vector__isnull=False).count()
            
            # Recent activity
            recent_documents = LegalDocument.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            recent_chunks = DocumentChunk.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            stats_data = {
                'documents': {
                    'total': total_documents,
                    'boe_summaries': boe_summaries,
                    'boe_daily_updates': boe_daily_updates,
                    'processed': processed_documents,
                    'processing_rate': (processed_documents / total_documents * 100) if total_documents > 0 else 0,
                    'recent_week': recent_documents
                },
                'chunks': {
                    'total': total_chunks,
                    'with_embeddings': chunks_with_embeddings,
                    'embedding_rate': (chunks_with_embeddings / total_chunks * 100) if total_chunks > 0 else 0,
                    'recent_week': recent_chunks
                },
                'summary': {
                    'total_processed_documents': processed_documents,
                    'total_searchable_chunks': chunks_with_embeddings,
                    'system_health': 'healthy' if processed_documents > 0 and chunks_with_embeddings > 0 else 'initializing'
                }
            }
            
            return APIResponse.success(
                data=stats_data,
                message="Document statistics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}", exc_info=True)
            return APIResponse.server_error(message="Failed to get document statistics")