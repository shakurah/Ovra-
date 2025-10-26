# billing/views.py
import json
import logging
import stripe
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import JsonResponse, HttpResponse
from django.conf import settings

from rest_framework.response import Response
from .models import Subscription
from django.utils import timezone

logger = logging.getLogger(__name__)
stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", None)

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    # DRF has already authenticated the request; use request.user
    user = request.user

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
        price_id = data.get("price_id")
        amount = data.get("amount")        # expected in cents (int)
        currency = (data.get("currency") or "eur").lower()
        description = data.get("description") or f"Purchase by user {user.id}"
        success_url = data.get("success_url")
        cancel_url = data.get("cancel_url")

        if not success_url or not cancel_url:
            return JsonResponse({"error": "success_url and cancel_url required"}, status=400)

        # create or reuse a Stripe Customer
        stripe_customer_id = None
        if hasattr(user, "stripe_customer_id") and getattr(user, "stripe_customer_id"):
            stripe_customer_id = user.stripe_customer_id
        else:
            try:
                cust = stripe.Customer.create(email=getattr(user, "email", None), metadata={"user_id": user.id})
                stripe_customer_id = cust.id
                # try to persist on user model if field exists
                try:
                    setattr(user, "stripe_customer_id", stripe_customer_id)
                    user.save(update_fields=["stripe_customer_id"])
                except Exception:
                    # ignore if user model doesn't have field or cannot be saved
                    pass
            except stripe.error.PermissionError as e:
                logger.exception("Stripe permission error creating customer")
                return JsonResponse({"error": "Stripe permission error: check API key permissions"}, status=403)

        # build line_items: use price_id if valid, otherwise create a Stripe Price
        line_items = None
        if price_id and str(price_id).startswith("price_"):
            line_items = [{"price": price_id, "quantity": 1}]
        elif amount:
            # create a product then a price for the requested amount
            product = stripe.Product.create(name=description[:120])
            price = stripe.Price.create(unit_amount=int(amount), currency=currency, product=product.id)
            line_items = [{"price": price.id, "quantity": 1}]
        else:
            return JsonResponse({"error": "missing price_id or amount"}, status=400)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=line_items,
            success_url=success_url,
            cancel_url=cancel_url,
            customer=stripe_customer_id,
        )

        return JsonResponse({"id": session.id, "url": getattr(session, "url", None) or session.get("url")})
    except stripe._error.StripeError as e:
        logger.exception("Stripe error creating checkout session")
        return JsonResponse({"error": str(e)}, status=402)
    except Exception as e:
        logger.exception("create_checkout_session failed")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret) if webhook_secret else stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        logger.exception("Invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.exception("Invalid signature")
        return HttpResponse(status=400)

    # Handle relevant events
    try:
        typ = event['type']
        data = event['data']['object']
        logger.debug("stripe webhook event: %s", typ)

        if typ == 'checkout.session.completed':
            # create subscription record after Checkout completes
            customer_id = data.get('customer')
            session_id = data.get('id')
            metadata = data.get('metadata') or {}
            user_id = metadata.get('user_id')
            # fetch subscription created by Stripe Checkout (requires retrieving session)
            try:
                sess = stripe.checkout.Session.retrieve(session_id, expand=['subscription'])
                subscription_obj = sess.get('subscription')
                if subscription_obj:
                    stripe_sub_id = subscription_obj['id']
                    tier_price = metadata.get('tier_price')
                    # map price -> tier name or store price id as metadata
                    # attach to our Subscription model
                    sub = None
                    if user_id:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        try:
                            user = User.objects.get(pk=int(user_id))
                            sub, _ = Subscription.objects.get_or_create(user=user)
                        except Exception:
                            user = None
                    if sub:
                        sub.stripe_subscription_id = stripe_sub_id
                        sub.stripe_customer_id = customer_id
                        sub.status = subscription_obj.get('status', 'active')
                        # set period end if present
                        period_end = subscription_obj.get('current_period_end')
                        if period_end:
                            sub.current_period_end = timezone.datetime.fromtimestamp(period_end, tz=timezone.utc)
                        # credits allocation will be handled on invoice.paid / via task
                        sub.save()
            except Exception:
                logger.exception("Failed handling checkout.session.completed")

        elif typ in ('invoice.paid'):
            # allocate credits for the subscription owner
            try:
                customer_id = data.get('customer')
                # find subscription by stripe_customer_id / stripe_subscription_id
                sub = Subscription.objects.filter(stripe_customer_id=customer_id).first()
                if not sub and data.get('subscription'):
                    sub = Subscription.objects.filter(stripe_subscription_id=data.get('subscription')).first()
                if sub:
                    # determine credits based on tier mapping (configure below)
                    tier_to_credits = {'basic': 10, 'plus': 30, 'advanced': 100}
                    credits = tier_to_credits.get(sub.tier, 0)
                    sub.credits = (sub.credits or 0) + credits
                    sub.status = 'active'
                    sub.save()
                    logger.info("Allocated %d credits to %s", credits, sub.user_id)
            except Exception:
                logger.exception("invoice.paid handling failed")

        elif typ in ('invoice.payment_failed',):
            try:
                customer_id = data.get('customer')
                sub = Subscription.objects.filter(stripe_customer_id=customer_id).first()
                if sub:
                    sub.status = 'past_due'
                    sub.save()
            except Exception:
                logger.exception("payment_failed handling failed")

        elif typ in ('customer.subscription.updated', 'customer.subscription.deleted'):
            try:
                stripe_sub = data
                # find subscription by stripe_subscription_id
                sub = Subscription.objects.filter(stripe_subscription_id=stripe_sub.get('id')).first()
                if sub:
                    sub.status = stripe_sub.get('status', sub.status)
                    period_end = stripe_sub.get('current_period_end')
                    if period_end:
                        sub.current_period_end = timezone.datetime.fromtimestamp(period_end, tz=timezone.utc)
                    sub.save()
            except Exception:
                logger.exception("subscription update/delete handling failed")

    except Exception:
        logger.exception("Unhandled webhook processing error")

    return HttpResponse(status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_checkout_session(request):
    """
    GET ?session_id=...  -> returns whether session succeeded and subscription/payment info.
    """
    session_id = request.query_params.get('session_id')
    if not session_id:
        return Response({'error': 'missing session_id'}, status=400)
    try:
        sess = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent', 'subscription'])
        # Example payload you can return:
        result = {
            'id': sess.id,
            'payment_status': sess.payment_status,
            'status': sess.status,
            'subscription': None,
        }
        if sess.get('subscription'):
            sub = stripe.Subscription.retrieve(sess['subscription'])
            result['subscription'] = {
                'id': sub.id,
                'status': sub.status,
                'current_period_end': sub.current_period_end,
            }
        return Response(result)
    except Exception as e:
        logger.exception("verify_checkout_session failed")
        return Response({'error': str(e)}, status=500)
