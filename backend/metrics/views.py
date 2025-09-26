# metrics/views.py
from django.shortcuts import render
from django.db.models import Avg, Max, Min, Count
from .models import MetricLog

def metrics_dashboard(request):
    accuracy_avg = MetricLog.objects.filter(metric_type="accuracy").aggregate(Avg("value"))["value__avg"]
    latency_avg = MetricLog.objects.filter(metric_type="latency").aggregate(Avg("value"))["value__avg"]
    usage_count = MetricLog.objects.filter(metric_type="usage").count()

    context = {
        "accuracy_avg": accuracy_avg or 0,
        "latency_avg": latency_avg or 0,
        "usage_count": usage_count,
    }
    return render(request, "metrics/dashboard.html", context)
