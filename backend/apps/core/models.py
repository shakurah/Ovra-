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
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=[('es', 'Español'), ('en', 'English')],
        default='es'
    )



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
        ]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        """Return the user's display name (full name or email)."""
        return self.full_name if self.full_name else self.email.split('@')[0]



    def get_full_name(self):
        """Return the user's full name."""
        return self.full_name

    def get_short_name(self):
        """Return the user's short name (first name or email prefix)."""
        if self.full_name:
            return self.full_name.split()[0]
        return self.email.split('@')[0]
