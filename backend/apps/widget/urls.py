from django.urls import path
from .views import (
    WidgetRegisterView,
    WidgetChatView,
    WidgetFeedbackView
)

app_name = 'widget'

urlpatterns = [
    # Widget endpoints
    path('register/', WidgetRegisterView.as_view(), name='widget-register'),
    path('chat/', WidgetChatView.as_view(), name='widget-chat'),
    path('feedback/', WidgetFeedbackView.as_view(), name='widget-feedback'),
]