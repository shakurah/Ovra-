from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    PLAN_CHOICES = (
        ("free", "Free"),
        ("pro", "Pro"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    plan = models.CharField(max_length=10, choices=PLAN_CHOICES, default="free")

    def __str__(self):
        return f"{self.user.username} ({self.plan})"



