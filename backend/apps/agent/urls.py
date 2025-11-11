from django.urls import path
from . import views

urlpatterns = [
    path("reason/", views.reason_cycle, name="agent-reason-cycle"),
    path("validations/<str:resp_id>/", views.validation_result, name="validation_result"),
    path("validations/stream/<str:resp_id>/", views.validation_stream, name="validation_stream"),
]