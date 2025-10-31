from django.db import models
from django.utils import timezone

class TestCase(models.Model):
    """Stored test cases for regression testing"""
    
    id = models.CharField(max_length=36, primary_key=True)
    query = models.TextField()
    expected_response = models.TextField()
    tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(default=timezone.now)
    last_run = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['last_run']),
        ]
    
    def __str__(self):
        return f"Test Case {self.id}"

class TestExecution(models.Model):
    """Records of test case executions"""
    
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    actual_response = models.TextField()
    similarity_score = models.FloatField()
    passed = models.BooleanField()
    execution_time = models.FloatField()  # in seconds
    
    timestamp = models.DateTimeField(default=timezone.now)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['test_case', 'timestamp']),
            models.Index(fields=['passed']),
        ]
    
    def __str__(self):
        return f"Execution {self.id} for Test Case {self.test_case.id}"

class RegressionIssue(models.Model):
    """Tracked regression issues"""
    
    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE)
    first_detected = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('investigating', 'Under Investigation'),
            ('fixed', 'Fixed'),
            ('wontfix', 'Won\'t Fix')
        ],
        default='open'
    )
    
    description = models.TextField()
    resolution_notes = models.TextField(null=True, blank=True)
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ],
        default='medium'
    )
    
    occurrences = models.IntegerField(default=1)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['first_detected']),
        ]
    
    def __str__(self):
        return f"Regression Issue {self.id} for Test Case {self.test_case.id}"