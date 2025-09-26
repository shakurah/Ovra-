# metrics/models.py
from django.db import models
from django.utils import timezone

class MetricLog(models.Model):
    METRIC_CHOICES = [
        ("accuracy", "Accuracy"),
        ("latency", "Latency"),
        ("usage", "Usage"),
    ]

    metric_type = models.CharField(max_length=20, choices=METRIC_CHOICES)
    value = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.metric_type} - {self.value} ({self.timestamp})"
