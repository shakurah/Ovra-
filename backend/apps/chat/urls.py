"""
URL configuration for the chat app.
"""
from django.urls import path, include
from apps.chat.views import (
    ChatAPIView, ChatStreamAPIView, ChatSessionListView, ChatSessionDetailView,
    ChatHistoryView, UpdateChatRatingView
)

app_name = 'chat'

urlpatterns = [
    # Main chat endpoint
    path('', ChatAPIView.as_view(), name='chat'),

    # Streaming chat endpoint
    path('stream/', ChatStreamAPIView.as_view(), name='chat-stream'),

    # Session management
    path('sessions/', ChatSessionListView.as_view(), name='session-list'),
    path('sessions/<uuid:id>/', ChatSessionDetailView.as_view(), name='session-detail'),

    # Chat history
    path('history/', ChatHistoryView.as_view(), name='history'),

    # Rating
    path('<uuid:chat_id>/rate/', UpdateChatRatingView.as_view(), name='rate-chat'),
]