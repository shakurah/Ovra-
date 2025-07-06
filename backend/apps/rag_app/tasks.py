"""
Django Q scheduled tasks for RAG app.
"""
from django.core.management import call_command
from django_q.tasks import schedule, Schedule
from django_q.models import Schedule as ScheduleModel
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def daily_boe_capture_task():
    """
    Daily task to capture BOE updates.
    This function is called by Django Q scheduler.
    """
    try:
        logger.info("Starting daily BOE capture task")
        
        # Call the management command for daily capture
        call_command('daily_boe_capture', '--days-back=1')
        
        logger.info("Daily BOE capture task completed successfully")
        return {"status": "success", "message": "Daily BOE capture completed"}
        
    except Exception as e:
        logger.error(f"Daily BOE capture task failed: {e}")
        return {"status": "error", "message": str(e)}


def setup_daily_boe_schedule():
    """
    Set up the daily BOE capture schedule.
    Call this function to initialize the scheduled task.
    """
    # Check if schedule already exists
    existing_schedule = ScheduleModel.objects.filter(
        name='daily_boe_capture'
    ).first()
    
    if existing_schedule:
        logger.info("Daily BOE capture schedule already exists")
        return existing_schedule
    
    # Create new schedule for end of day (11:30 PM)
    from django.utils import timezone as django_timezone
    schedule_time = django_timezone.now().replace(hour=23, minute=30, second=0, microsecond=0)
    if schedule_time <= django_timezone.now():
        # If 11:30 PM today has passed, schedule for tomorrow
        schedule_time += timedelta(days=1)
    
    scheduled_task = schedule(
        'apps.rag_app.tasks.daily_boe_capture_task',
        name='daily_boe_capture',
        schedule_type=Schedule.DAILY,
        next_run=schedule_time,
        repeats=-1  # Repeat indefinitely
    )
    
    logger.info(f"Daily BOE capture scheduled for {schedule_time}")
    return scheduled_task


def manual_boe_capture_task(days_back=1):
    """
    Manual BOE capture task that can be triggered via API.
    """
    try:
        logger.info(f"Starting manual BOE capture for {days_back} days back")
        
        # Call the management command
        call_command('daily_boe_capture', f'--days-back={days_back}')
        
        logger.info("Manual BOE capture completed successfully")
        return {"status": "success", "message": f"Manual BOE capture completed for {days_back} days"}
        
    except Exception as e:
        logger.error(f"Manual BOE capture failed: {e}")
        return {"status": "error", "message": str(e)}


def get_schedule_status():
    """
    Get the status of the daily BOE capture schedule.
    """
    try:
        schedule_obj = ScheduleModel.objects.filter(
            name='daily_boe_capture'
        ).first()
        
        if not schedule_obj:
            return {
                "status": "not_scheduled",
                "message": "Daily BOE capture is not scheduled"
            }
        
        # Get the last run time safely
        last_run = None
        try:
            if hasattr(schedule_obj, 'last_run') and schedule_obj.last_run:
                if callable(schedule_obj.last_run):
                    last_run = schedule_obj.last_run()
                else:
                    last_run = schedule_obj.last_run
        except:
            last_run = None
            
        return {
            "status": "active" if schedule_obj.next_run else "inactive",
            "next_run": schedule_obj.next_run.isoformat() if schedule_obj.next_run else None,
            "last_run": last_run.isoformat() if last_run else None,
            "schedule_type": schedule_obj.schedule_type,
            "repeats": schedule_obj.repeats,
            "task": schedule_obj.func
        }
        
    except Exception as e:
        logger.error(f"Error checking schedule status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def remove_daily_boe_schedule():
    """
    Remove the daily BOE capture schedule.
    """
    try:
        deleted_count = ScheduleModel.objects.filter(
            name='daily_boe_capture'
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info("Daily BOE capture schedule removed")
            return {"status": "success", "message": "Schedule removed"}
        else:
            return {"status": "not_found", "message": "No schedule found to remove"}
            
    except Exception as e:
        logger.error(f"Error removing schedule: {e}")
        return {"status": "error", "message": str(e)}