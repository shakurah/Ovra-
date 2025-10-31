from django.db import models
from django.utils import timezone

class PipelineExecution(models.Model):
    """Records of pipeline executions"""
    
    task_id = models.CharField(max_length=36, primary_key=True)
    user_id = models.CharField(max_length=36, null=True, blank=True)
    
    query = models.TextField()
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    final_stage = models.CharField(
        max_length=20,
        choices=[
            ('comprehend', 'Comprehend'),
            ('detect', 'Detect'),
            ('verify', 'Verify'),
            ('reason', 'Reason'),
            ('respond', 'Respond'),
            ('register', 'Register')
        ]
    )
    
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    verification_status = models.BooleanField(default=False)
    reliability_score = models.FloatField(default=0.0)
    
    metadata = models.JSONField(default=dict)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'started_at']),
            models.Index(fields=['success', 'final_stage']),
        ]
    
    def __str__(self):
        return f"Pipeline Execution {self.task_id}"

class StageExecution(models.Model):
    """Details of individual stage executions"""
    
    pipeline = models.ForeignKey(PipelineExecution, on_delete=models.CASCADE)
    stage = models.CharField(
        max_length=20,
        choices=[
            ('comprehend', 'Comprehend'),
            ('detect', 'Detect'),
            ('verify', 'Verify'),
            ('reason', 'Reason'),
            ('respond', 'Respond'),
            ('register', 'Register')
        ]
    )
    
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    success = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    
    class Meta:
        indexes = [
            models.Index(fields=['pipeline', 'stage']),
            models.Index(fields=['success']),
        ]
        unique_together = ['pipeline', 'stage']
    
    def __str__(self):
        return f"{self.stage} for Pipeline {self.pipeline.task_id}"

class SystemMetrics(models.Model):
    """System-wide performance metrics"""
    
    timestamp = models.DateTimeField(default=timezone.now)
    period = models.CharField(
        max_length=20,
        choices=[
            ('minute', 'Per Minute'),
            ('hour', 'Hourly'),
            ('day', 'Daily')
        ]
    )
    
    total_executions = models.IntegerField(default=0)
    successful_executions = models.IntegerField(default=0)
    failed_executions = models.IntegerField(default=0)
    
    average_execution_time = models.FloatField(default=0.0)
    average_reliability_score = models.FloatField(default=0.0)
    
    verification_success_rate = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)
    
    class Meta:
        indexes = [
            models.Index(fields=['timestamp', 'period']),
        ]
        unique_together = ['timestamp', 'period']
    
    def __str__(self):
        return f"Metrics for {self.period} at {self.timestamp}"