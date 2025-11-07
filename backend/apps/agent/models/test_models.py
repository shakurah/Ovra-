"""
Test Case and Result Models for Regression Testing
"""

# prevent pytest test collection of model classes in this module
__test__ = False

from django.db import models
from django.utils import timezone

class TestCaseModel(models.Model):
    """Persistent storage for regression test cases"""
    
    test_id = models.CharField(max_length=255, unique=True)
    query = models.TextField()
    expected_response = models.TextField()
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    last_run = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['test_id']),
            models.Index(fields=['created_at'])
        ]
        app_label = "agent"

class TestResultModel(models.Model):
    """Persistent storage for test execution results"""
    
    test_case_id = models.CharField(max_length=255)
    actual_response = models.TextField()
    similarity_score = models.FloatField()
    passed = models.BooleanField()
    execution_time = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['test_case_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['passed'])
        ]
        app_label = "agent"