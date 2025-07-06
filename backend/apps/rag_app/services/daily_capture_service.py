"""
Daily BOE Capture Service

This service handles the automation and scheduling of daily BOE captures.
It integrates with Django-Q2 for background task processing and provides
status tracking for the capture process.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django_q.tasks import async_task, schedule
from django_q.models import Schedule

from apps.rag_app.models import LegalDocument, CaptureLog
from apps.common.responses import APIResponse

logger = logging.getLogger(__name__)


class DailyBOECaptureService:
    """
    Service for managing daily BOE capture automation.
    
    Handles:
    - Scheduling daily captures
    - Monitoring capture status
    - Error handling and recovery
    - Progress tracking
    """
    
    TASK_NAME = 'daily_boe_capture'
    SCHEDULE_NAME = 'daily_boe_capture_schedule'
    
    def __init__(self):
        self.capture_time = getattr(settings, 'BOE_CAPTURE_TIME', '08:00')
        self.max_retries = getattr(settings, 'BOE_CAPTURE_MAX_RETRIES', 3)
        self.retry_delay = getattr(settings, 'BOE_CAPTURE_RETRY_DELAY', 30)  # minutes
    
    def setup_daily_schedule(self, capture_time: str = None) -> Dict[str, Any]:
        """
        Set up the daily capture schedule.
        
        Args:
            capture_time: Time in HH:MM format (24-hour)
            
        Returns:
            Dictionary with schedule setup result
        """
        try:
            if capture_time:
                self.capture_time = capture_time
            
            # Remove existing schedule if it exists
            Schedule.objects.filter(name=self.SCHEDULE_NAME).delete()
            
            # Create new schedule
            schedule(
                'apps.rag_app.services.daily_capture_service.run_daily_capture',
                name=self.SCHEDULE_NAME,
                schedule_type=Schedule.DAILY,
                next_run=self._get_next_run_time()
            )
            
            logger.info(f'Daily BOE capture scheduled for {self.capture_time}')
            
            return {
                'success': True,
                'message': f'Daily capture scheduled for {self.capture_time}',
                'schedule_name': self.SCHEDULE_NAME,
                'next_run': self._get_next_run_time()
            }
            
        except Exception as e:
            logger.error(f'Error setting up daily schedule: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_next_run_time(self) -> datetime:
        """Calculate next run time based on capture time."""
        now = timezone.now()
        
        # Parse capture time
        hour, minute = map(int, self.capture_time.split(':'))
        
        # Set next run time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If time has passed today, schedule for tomorrow
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def run_daily_capture(self, date: str = None, retry_count: int = 0) -> Dict[str, Any]:
        """
        Execute the daily capture process.
        
        Args:
            date: Specific date to capture (YYYY-MM-DD format)
            retry_count: Current retry attempt
            
        Returns:
            Dictionary with capture results
        """
        capture_date = date or timezone.now().strftime('%Y-%m-%d')
        
        try:
            # Log capture start
            capture_log = self._log_capture_start(capture_date)
            
            # Run the management command
            result = self._execute_capture_command(capture_date)
            
            # Log success
            self._log_capture_success(capture_log, result)
            
            return {
                'success': True,
                'date': capture_date,
                'stats': result,
                'message': 'Daily capture completed successfully'
            }
            
        except Exception as e:
            logger.error(f'Error in daily capture for {capture_date}: {e}')
            
            # Log failure
            self._log_capture_failure(capture_log if 'capture_log' in locals() else None, str(e))
            
            # Retry logic
            if retry_count < self.max_retries:
                logger.info(f'Retrying daily capture in {self.retry_delay} minutes (attempt {retry_count + 1}/{self.max_retries})')
                
                # Schedule retry
                async_task(
                    'apps.rag_app.services.daily_capture_service.run_daily_capture',
                    date,
                    retry_count + 1,
                    timeout=3600,  # 1 hour timeout
                    eta=timezone.now() + timedelta(minutes=self.retry_delay)
                )
                
                return {
                    'success': False,
                    'error': str(e),
                    'retry_scheduled': True,
                    'retry_count': retry_count + 1
                }
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'max_retries_reached': True
                }
    
    def _execute_capture_command(self, date: str) -> Dict[str, Any]:
        """Execute the daily capture management command."""
        try:
            # Capture stdout to get statistics
            from io import StringIO
            import sys
            
            old_stdout = sys.stdout
            sys.stdout = buffer = StringIO()
            
            # Run the command
            call_command('daily_boe_capture', date=date, verbosity=0)
            
            # Restore stdout
            sys.stdout = old_stdout
            
            # Parse results from command output
            # This is a simplified version - in production you might want more sophisticated parsing
            return {
                'documents_processed': 0,  # Would be parsed from command output
                'embeddings_created': 0,
                'execution_time': timezone.now()
            }
            
        except Exception as e:
            logger.error(f'Error executing capture command: {e}')
            raise
    
    def _log_capture_start(self, date: str) -> 'CaptureLog':
        """Log the start of a capture process."""
        try:
            return CaptureLog.objects.create(
                capture_date=datetime.strptime(date, '%Y-%m-%d').date(),
                status='running',
                started_at=timezone.now()
            )
        except Exception as e:
            logger.error(f'Error logging capture start: {e}')
            raise
    
    def _log_capture_success(self, capture_log: 'CaptureLog', result: Dict[str, Any]):
        """Log successful capture completion."""
        try:
            if capture_log:
                capture_log.status = 'completed'
                capture_log.completed_at = timezone.now()
                capture_log.documents_processed = result.get('documents_processed', 0)
                capture_log.embeddings_created = result.get('embeddings_created', 0)
                capture_log.save()
        except Exception as e:
            logger.error(f'Error logging capture success: {e}')
    
    def _log_capture_failure(self, capture_log: Optional['CaptureLog'], error: str):
        """Log failed capture attempt."""
        try:
            if capture_log:
                capture_log.status = 'failed'
                capture_log.error_message = error
                capture_log.completed_at = timezone.now()
                capture_log.save()
        except Exception as e:
            logger.error(f'Error logging capture failure: {e}')
    
    def get_capture_status(self) -> Dict[str, Any]:
        """Get current capture status and statistics."""
        try:
            # Get recent capture logs
            recent_logs = CaptureLog.objects.filter(
                capture_date__gte=timezone.now().date() - timedelta(days=7)
            ).order_by('-capture_date')
            
            # Get schedule info
            schedule_info = Schedule.objects.filter(name=self.SCHEDULE_NAME).first()
            
            # Calculate statistics
            total_captures = recent_logs.count()
            successful_captures = recent_logs.filter(status='completed').count()
            failed_captures = recent_logs.filter(status='failed').count()
            
            return {
                'is_scheduled': schedule_info is not None,
                'next_run': schedule_info.next_run if schedule_info else None,
                'last_capture': recent_logs.first().capture_date if recent_logs else None,
                'recent_stats': {
                    'total_captures': total_captures,
                    'successful_captures': successful_captures,
                    'failed_captures': failed_captures,
                    'success_rate': (successful_captures / total_captures * 100) if total_captures > 0 else 0
                },
                'recent_logs': [
                    {
                        'date': log.capture_date.strftime('%Y-%m-%d'),
                        'status': log.status,
                        'documents_processed': log.documents_processed,
                        'embeddings_created': log.embeddings_created,
                        'started_at': log.started_at,
                        'completed_at': log.completed_at,
                        'error_message': log.error_message
                    }
                    for log in recent_logs[:10]  # Last 10 logs
                ]
            }
            
        except Exception as e:
            logger.error(f'Error getting capture status: {e}')
            return {
                'error': str(e),
                'is_scheduled': False
            }
    
    def trigger_manual_capture(self, date: str = None) -> Dict[str, Any]:
        """
        Trigger a manual capture process.
        
        Args:
            date: Specific date to capture (YYYY-MM-DD format)
            
        Returns:
            Dictionary with task result
        """
        try:
            capture_date = date or timezone.now().strftime('%Y-%m-%d')
            
            # Queue the capture task
            task_id = async_task(
                'apps.rag_app.services.daily_capture_service.run_daily_capture',
                capture_date,
                0,  # retry_count
                timeout=3600,  # 1 hour timeout
                task_name=f'manual_capture_{capture_date}'
            )
            
            return {
                'success': True,
                'task_id': task_id,
                'date': capture_date,
                'message': f'Manual capture queued for {capture_date}'
            }
            
        except Exception as e:
            logger.error(f'Error triggering manual capture: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_scheduled_capture(self) -> Dict[str, Any]:
        """Stop the scheduled daily capture."""
        try:
            deleted_count = Schedule.objects.filter(name=self.SCHEDULE_NAME).delete()[0]
            
            if deleted_count > 0:
                logger.info('Daily BOE capture schedule stopped')
                return {
                    'success': True,
                    'message': 'Daily capture schedule stopped'
                }
            else:
                return {
                    'success': True,
                    'message': 'No active schedule found'
                }
                
        except Exception as e:
            logger.error(f'Error stopping scheduled capture: {e}')
            return {
                'success': False,
                'error': str(e)
            }


# Function to be called by Django-Q2
def run_daily_capture(date: str = None, retry_count: int = 0) -> Dict[str, Any]:
    """
    Django-Q2 task function for daily BOE capture.
    
    Args:
        date: Specific date to capture (YYYY-MM-DD format)
        retry_count: Current retry attempt
        
    Returns:
        Dictionary with capture results
    """
    service = DailyBOECaptureService()
    return service.run_daily_capture(date, retry_count)