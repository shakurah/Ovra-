from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    # Fields to display in the user list
    list_display = (
        'email', 'full_name', 'is_active', 'created_at'
    )

    # Fields to filter by in the admin sidebar
    list_filter = (
        'is_active', 'is_staff', 'preferred_language', 'created_at'
    )

    # Fields to search by
    search_fields = ('email', 'full_name')

    # Default ordering
    ordering = ('-created_at',)

    # Fields to display in the user detail form
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('full_name', 'profile_picture')
        }),
        (_('Preferences'), {
            'fields': ('preferred_language',)
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'last_login_ip')
        }),
    )

    # Fields to display when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )

    # Read-only fields
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')

    # Custom actions
    actions = []
