"""
WebSocket routing for the chat app.
"""
from django.urls import path
from apps.chat import consumers

websocket_urlpatterns = [
    # WebSocket endpoint for streaming chat responses
    path('ws/chat/', consumers.ChatConsumer.as_asgi()),
] 