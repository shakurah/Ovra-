# billing/views.py
import stripe
import json
import logging
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Subscription
from django.utils import timezone

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_checkout_session(request):
    """
    Frontend posts { price_id } or { tier } and success/cancel urls.
    Returns Stripe Checkout session url.
    """
    data = request.data or {}
    price_id = data.get('price_id')
    success_url = data.get('success_url') or data.get('return_url') or settings.FRONTEND_SUCCESS_URL
    cancel_url = data.get('cancel_url') or settings.FRONTEND_CANCEL_URL

    # create/get customer
    user = request.user
    sub, _ = Subscription.objects.get_or_create(user=user)
    try:
        if not sub.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
            sub.stripe_customer_id = customer['id']
            sub.save()
        else:
            customer = stripe.Customer.retrieve(sub.stripe_customer_id)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            customer=customer['id'],
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            metadata={'user_id': str(user.id), 'tier_price': price_id},
        )
        return Response({'url': session.url, 'id': session.id})
    except Exception as e:
        logger.exception("create_checkout_session failed")
        return Response({'error': str(e)}, status=500)


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

        elif typ in ('invoice.paid',):
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
