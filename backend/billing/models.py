from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

class SubscriptionPlan(models.Model):
    # Define your plan catalog here or sync with Stripe product IDs
    slug = models.SlugField(unique=True)            # e.g. basic, plus, pro
    name = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=200, blank=True, null=True)  # Stripe Price ID
    monthly_credits = models.IntegerField(default=0)  # credits allocated each billing period
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=200, blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PaymentRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_event_id = models.CharField(max_length=200, unique=True)
    stripe_charge_id = models.CharField(max_length=200, blank=True, null=True)
    amount = models.IntegerField()  # cents
    currency = models.CharField(max_length=10, default='eur')
    success = models.BooleanField(default=False)
    raw_event = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

class Subscription(models.Model):
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    tier = models.CharField(max_length=32, choices=TIER_CHOICES, default='basic')
    status = models.CharField(max_length=64, default='inactive')
    current_period_end = models.DateTimeField(blank=True, null=True)
    credits = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} {self.tier} {self.status}"
