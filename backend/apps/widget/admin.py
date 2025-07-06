from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import UserEngagement


@admin.register(UserEngagement)
class UserEngagementAdmin(admin.ModelAdmin):
    """Admin configuration for UserEngagement model."""
    
    # Fields to display in the list view
    list_display = (
        'email', 'source_website', 'total_questions', 
        'privacy_accepted', 'terms_accepted', 'created_at'
    )
    
    # Fields to filter by
    list_filter = (
        'is_active', 'privacy_accepted', 'terms_accepted', 
        'created_at', 'source_website'
    )
    
    # Fields to search by
    search_fields = ('email',)
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Read-only fields
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'first_interaction', 
        'last_interaction', 'total_questions'
    )
    
    # Fields layout
    fieldsets = (
        (_('User Information'), {
            'fields': ('id', 'email', 'source_website')
        }),
        (_('Consent'), {
            'fields': ('privacy_accepted', 'terms_accepted', 'accepted_at')
        }),
        (_('Engagement Metrics'), {
            'fields': (
                'first_interaction', 'last_interaction', 
                'total_questions', 'is_active'
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    # Custom actions
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'