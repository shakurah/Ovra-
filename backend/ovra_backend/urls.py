from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView
)
from users.views import RegisterView, logout_view, me_view, forgot_password_view, reset_password_view


urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth endpoints
    
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name="token_refresh"),  # alias
    path('api/v1/auth/token/verify', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v1/auth/logout/', logout_view, name='logout'),
    path('api/v1/auth/register', RegisterView.as_view(), name='register'),
    path('api/v1/auth/me', me_view, name='me'),

    
    path('api/v1/forgot-password/', forgot_password_view, name='forgot-password'),
    
    path('api/v1/reset-password/<uuid:token>/', reset_password_view, name='reset-password-uuid'),
    
    path('api/v1/reset-password/<str:token>/', reset_password_view, name='reset-password-str'),
    
    re_path(r'^api/v1/reset-password/(?P<token>.+)/$', reset_password_view, name='reset-password-any'),

    path("api/v1/auth", include("users.urls")),  
    path("api/v1/", include("chat.urls")),
    path("metrics/", include("metrics.urls")),
    path("api/v1/billing/", include("billing.urls")),
    # single, correct include for agent endpoints (versioned)
    path("api/v1/agent/", include("apps.agent.urls")),
]
