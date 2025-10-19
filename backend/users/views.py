import uuid
import json
import datetime
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import logout
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .models import PasswordResetToken

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        user = instance
        refresh = RefreshToken.for_user(user)
 
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
            'id': instance.id,
            'email': instance.email,
            'firstName': instance.first_name,
            'lastName': instance.last_name
        } 
    })

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(username=email, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'firstName': user.first_name,
                'lastName': user.last_name
            }
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        # Blacklist the refresh token
        refresh_token = request.data.get("refresh")
        if refresh_token:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({
        "id": user.id,
        "email": user.email,
        "firstName": user.first_name,
        "lastName": user.last_name,
    })

@csrf_exempt
def forgot_password_view(request):
    """
    Accepts POST { "email": "..." }.
    If the email exists, create a time-limited token and send reset link.
    Always return a generic success message to avoid account enumeration.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    email = (data.get('email') or '').strip()
    if not email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    # Look up user (case-insensitive)
    user = User.objects.filter(email__iexact=email).first()

    # Always respond with a generic message to prevent user enumeration.
    generic_response = {'message': 'If an account with that email exists, a reset link has been sent.'}

    if not user:
        return JsonResponse(generic_response, status=200)

    # Remove any previous tokens for this user
    PasswordResetToken.objects.filter(user=user).delete()

    # Create a new token (UUID4). Use created_at on the model to enforce expiry.
    token = str(uuid.uuid4())
    PasswordResetToken.objects.create(user=user, token=token)

    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password/{token}"

    # Send email (fail_silently=False so exceptions are surfaced)
    try:
        send_mail(
            subject="Password Reset Request",
            message=f"Hi {user.get_full_name() or user.username},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 1 hour.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        # Log or handle email sending failure; still return generic response
        # Optionally: logger.exception("Failed to send reset email")
        return JsonResponse(generic_response, status=200)

    return JsonResponse(generic_response, status=200)


@csrf_exempt
def reset_password_view(request, token):
    """
    Accepts POST { "new_password": "..." }.
    Validates token expiry, sets new password, and deletes the token.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_password = data.get('new_password') or ''
    if not new_password or len(new_password) < 8:
        return JsonResponse({'error': 'Password must be at least 8 characters long.'}, status=400)

    try:
        reset_entry = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return JsonResponse({'error': 'Invalid or expired token'}, status=400)

    # Expire after 1 hour (uses created_at on model)
    created_at = reset_entry.created_at
    if timezone.now() - created_at > datetime.timedelta(hours=1):
        reset_entry.delete()
        return JsonResponse({'error': 'Token expired. Please request a new one.'}, status=400)

    user = reset_entry.user
    user.password = make_password(new_password)
    user.save()

    # Remove token after successful reset
    reset_entry.delete()

    return JsonResponse({'message': 'Password reset successful! You can now log in.'})
