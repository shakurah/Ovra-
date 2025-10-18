# billing/urls.py
from django.urls import path
from .views import create_checkout_session, stripe_webhook

urlpatterns = [
    path("create-checkout/", create_checkout_session, name="create_checkout"),
    path("webhook/", stripe_webhook, name="stripe_webhook"),
]
