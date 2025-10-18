from celery import shared_task
from django.contrib.auth import get_user_model

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
