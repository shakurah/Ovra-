from django.urls import path
from .views import chat_api

urlpatterns = [
    path("chat/stream/", chat_api, name="chat_api"),
]
