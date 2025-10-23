from django.urls import path
from . import views

# This file initializes the agent module.

urlpatterns = [
    path("reason/", views.reason_cycle, name="agent-reason-cycle"),
]