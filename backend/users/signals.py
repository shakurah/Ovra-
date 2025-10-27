# users/signals.py
from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)
User = get_user_model()
DEFAULT_START_CREDITS = getattr(settings, "DEFAULT_START_CREDITS", 5)

@receiver(post_save, sender=User)
def ensure_userprofile(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        with transaction.atomic():
            UserProfile.objects.get_or_create(user=instance, defaults={"credits": DEFAULT_START_CREDITS})
    except IntegrityError:
        logger.exception("UserProfile get_or_create IntegrityError for user=%s — ignoring duplicate", instance.id)