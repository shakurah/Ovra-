from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model."""

    # Fields to display in the user list
    list_display = (
        'email', 'full_name', 'profession', 'subscription_type',
        'trial_queries_used', 'is_verified', 'is_active', 'created_at'
    )

    # Fields to filter by in the admin sidebar
    list_filter = (
        'subscription_type', 'is_verified', 'is_active', 'is_staff',
        'preferred_language', 'created_at'
    )

    # Fields to search by
    search_fields = ('email', 'full_name', 'profession', 'company_name')

    # Default ordering
    ordering = ('-created_at',)

    # Fields to display in the user detail form
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('full_name', 'profile_picture', 'phone_number', 'profession', 'company_name')
        }),
        (_('Preferences'), {
            'fields': ('preferred_language',)
        }),
        (_('Subscription & Usage'), {
            'fields': ('subscription_type', 'trial_queries_used', 'trial_queries_limit')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions'),
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
    actions = ['verify_users', 'reset_trial_queries']

    def verify_users(self, request, queryset):
        """Mark selected users as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users marked as verified.')
    verify_users.short_description = _('Mark selected users as verified')

    def reset_trial_queries(self, request, queryset):
        """Reset trial queries for selected users."""
        updated = queryset.update(trial_queries_used=0)
        self.message_user(request, f'Trial queries reset for {updated} users.')
    reset_trial_queries.short_description = _('Reset trial queries for selected users')
