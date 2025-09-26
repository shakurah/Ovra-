from django.urls import path
from .views import metrics_dashboard

urlpatterns = [
    path("dashboard/", metrics_dashboard, name="metrics_dashboard"),
]