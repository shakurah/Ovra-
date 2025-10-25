from django.urls import path
from .views import chat_api, chat_history, chat_health

urlpatterns = [
    path("chat/stream/", chat_api, name="chat_api"),
    path("chat/sessions/", chat_history, name="chat_history"),
    path("chat/sessions/<str:conversation_id>/", chat_history, name="chat_history_detail"),
    path("chat/_chat_health/", chat_health, name="chat_health")
]
