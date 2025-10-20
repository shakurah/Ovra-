from django.urls import path
from .views import chat_api, chat_history

urlpatterns = [
    path("chat/stream/", chat_api, name="chat_api"),
    path("chat/sessions/", chat_history, name="chat_history"),
    path("chat/sessions/<str:conversation_id>/", chat_history, name="chat_history_detail"),
]
