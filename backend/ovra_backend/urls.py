from django.urls import path, include
from django.contrib import admin
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from users.views import RegisterView, logout_view, me_view

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth endpoints
    #path('api/v1/auth/login', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view()),  # alias
    path('api/v1/auth/token/verify', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/auth/logout/', logout_view, name='logout'),
    path('api/v1/auth/register', RegisterView.as_view(), name='register'),
    path('api/v1/auth/me', me_view, name='me'),
    path("api/v1/auth", include("users.urls")),  # Include user app URLs
    # App routes
    path("api/v1/", include("chat.urls")),
    path("metrics/", include("metrics.urls")),
]
