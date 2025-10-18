# billing/views.py
import stripe
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import SubscriptionPlan, UserSubscription, PaymentRecord
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction


stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
@require_POST
def create_checkout_session(request):
    data = json.loads(request.body.decode("utf-8") or "{}")
    plan_slug = data.get("plan")
    try:
        plan = SubscriptionPlan.objects.get(slug=plan_slug)
    except SubscriptionPlan.DoesNotExist:
        return HttpResponseBadRequest("Invalid plan")

    # Create / reuse stripe customer
    user_sub, _ = UserSubscription.objects.get_or_create(user=request.user)
    if not user_sub.stripe_customer_id:
        customer = stripe.Customer.create(email=request.user.email, name=request.user.get_full_name() or request.user.username)
        user_sub.stripe_customer_id = customer["id"]
        user_sub.save()

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=user_sub.stripe_customer_id,
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            success_url=settings.FRONTEND_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.FRONTEND_CANCEL_URL,
        )
        return JsonResponse({"url": checkout_session.url})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
# billing/views.py (continued)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Handle relevant events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        # Attach subscription id to user if possible
        customer_id = session.get("customer")
        # Optionally fetch customer email & inspect subscription via stripe API
        try:
            with transaction.atomic():
                user_sub = UserSubscription.objects.filter(stripe_customer_id=customer_id).first()
                if user_sub:
                    # Get the subscription object
                    # The session for subscription will include subscription id in session["subscription"]
                    user_sub.stripe_subscription_id = session.get("subscription")
                    # mark active; find plan via price id from subscription
                    user_sub.active = True
                    # fetch subscription to get period end
                    if user_sub.stripe_subscription_id:
                        sub = stripe.Subscription.retrieve(user_sub.stripe_subscription_id)
                        user_sub.current_period_end = timezone.datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
                        # find price id on subscription -> map to plan
                        price_id = sub["items"]["data"][0]["price"]["id"]
                        plan = SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()
                        if plan:
                            user_sub.plan = plan
                    user_sub.save()
        except Exception as e:
            # log, but continue
            print("Webhook error:", e)

    # subscription.updated, invoice.paid, customer.subscription.deleted, invoice.payment_failed etc.
    if event["type"] in ("invoice.paid", "customer.subscription.created", "customer.subscription.updated"):
        # If invoice paid (first invoice), allocate credits for the plan
        obj = event["data"]["object"]
        # find customer
        customer_id = obj.get("customer")
        user_sub = UserSubscription.objects.filter(stripe_customer_id=customer_id).first()
        if user_sub and user_sub.plan:
            # allocate credits (synchronous or background)
            allocate_credits_for_user(user_sub.user.id, user_sub.plan.monthly_credits)
    if event["type"] == "invoice.payment_failed":
        # suspend user subscription or notify
        pass

    # store event for audit
    PaymentRecord.objects.create(
        user = User.objects.filter(email=event.get("data", {}).get("object", {}).get("customer_email") or "").first() or None,
        stripe_event_id = event["id"],
        stripe_charge_id = event["data"]["object"].get("charge"),
        amount = int(event["data"]["object"].get("amount_paid", 0)),
        currency = event["data"]["object"].get("currency", "eur"),
        success = True,
        raw_event = event
    )

    return HttpResponse(status=200)
