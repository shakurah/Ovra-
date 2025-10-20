from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Subscription
import logging

logger = logging.getLogger(__name__)

@shared_task
def allocate_credits_for_user_task(user_id: int, credits: int):
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        profile.credits = (profile.credits or 0) + credits
        profile.save()
    except Exception as e:
        print("allocate credits failed:", e)

@shared_task
def allocate_monthly_credits():
    tier_map = {'basic': 10, 'plus': 30, 'advanced': 100}
    subs = Subscription.objects.filter(status='active')
    for s in subs:
        credits = tier_map.get(s.tier, 0)
        s.credits = (s.credits or 0) + credits
        s.save()
        logger.info("Allocated %d credits to user %s", credits, s.user_id)
