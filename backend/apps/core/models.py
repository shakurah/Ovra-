from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """
    Custom User model for Ovra AI Tax Assistant.

    Extends Django's AbstractUser to include additional fields
    for profile management and user preferences.
    """

    # Remove username field and use email as the unique identifier
    username = None
    email = models.EmailField(_('email address'), unique=True)

    # User profile fields
    full_name = models.CharField(_('full name'), max_length=150, blank=True)
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text=_('Upload a profile picture (optional)')
    )

    # User preferences and metadata
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    profession = models.CharField(
        _('profession'),
        max_length=100,
        blank=True,
        help_text=_('e.g., Artist, Cultural Professional, Freelancer')
    )
    company_name = models.CharField(_('company name'), max_length=200, blank=True)

    # Account settings
    is_verified = models.BooleanField(_('email verified'), default=False)
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=[('es', 'Español'), ('en', 'English')],
        default='es'
    )

    # Subscription and usage tracking
    subscription_type = models.CharField(
        _('subscription type'),
        max_length=20,
        choices=[
            ('free', _('Free Trial')),
            ('basic', _('Basic')),
            ('premium', _('Premium')),
            ('enterprise', _('Enterprise'))
        ],
        default='free'
    )
    trial_queries_used = models.PositiveIntegerField(_('trial queries used'), default=0)
    trial_queries_limit = models.PositiveIntegerField(_('trial queries limit'), default=10)

    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), blank=True, null=True)

    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'core_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['subscription_type']),
        ]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        """Return the user's display name (full name or email)."""
        return self.full_name if self.full_name else self.email.split('@')[0]

    @property
    def has_trial_queries_remaining(self):
        """Check if user has trial queries remaining."""
        return self.trial_queries_used < self.trial_queries_limit

    @property
    def trial_queries_remaining(self):
        """Get number of trial queries remaining."""
        return max(0, self.trial_queries_limit - self.trial_queries_used)

    def use_trial_query(self):
        """Increment trial queries used counter."""
        if self.has_trial_queries_remaining:
            self.trial_queries_used += 1
            self.save(update_fields=['trial_queries_used'])
            return True
        return False

    def get_full_name(self):
        """Return the user's full name."""
        return self.full_name

    def get_short_name(self):
        """Return the user's short name (first name or email prefix)."""
        if self.full_name:
            return self.full_name.split()[0]
        return self.email.split('@')[0]
