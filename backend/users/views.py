import uuid
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
from django.utils.timezone import now, timedelta
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from .models import PasswordResetToken
import json
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
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    data = json.loads(request.body)
    email = data.get('email')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    # Delete old tokens for the same user
    PasswordResetToken.objects.filter(user=user).delete()

    token = str(uuid.uuid4())
    PasswordResetToken.objects.create(user=user, token=token)

    reset_link = f"{request.scheme}://{request.get_host()}/reset-password/{token}/"

    send_mail(
        subject="Password Reset Request",
        message=f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 1 hour.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return JsonResponse({'message': 'Password reset email sent successfully.'})


def reset_password_view(request, token):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    data = json.loads(request.body)
    new_password = data.get('new_password')

    try:
        reset_entry = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return JsonResponse({'error': 'Invalid or expired token'}, status=400)

    # Optional: expire after 1 hour
    if now() - reset_entry.created_at > timedelta(hours=1):
        reset_entry.delete()
        return JsonResponse({'error': 'Token expired. Please request a new one.'}, status=400)

    user = reset_entry.user
    user.password = make_password(new_password)
    user.save()

    reset_entry.delete()  # remove used token

    return JsonResponse({'message': 'Password reset successful! You can now log in.'})
