from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ChatLog(models.Model):
    conversation_id = models.CharField(max_length=100, blank=True, null=True)
    user_message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) 
    response_text = models.TextField(blank=True, null=True)
    response_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    validations = models.JSONField(blank=True, null=True, default=list)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"ChatLog {self.id} - {self.conversation_id or 'no convo id'}"