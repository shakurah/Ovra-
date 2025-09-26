# metrics/admin.py
from django.contrib import admin
from .models import MetricLog

@admin.register(MetricLog)
class MetricLogAdmin(admin.ModelAdmin):
    list_display = ("metric_type", "value", "timestamp")
    list_filter = ("metric_type", "timestamp")
    search_fields = ("metric_type",)
