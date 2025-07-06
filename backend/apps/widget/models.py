from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class UserEngagement(models.Model):
    """
    Model to track widget user engagement via email.
    
    This model stores email addresses of users who interact with the chat widget
    on the homepage or external sites. No password or authentication required.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    
    # Widget-specific fields
    source_website = models.URLField(
        _('source website'),
        blank=True,
        default='',
        help_text=_('The website where the user engaged from')
    )
    
    # Privacy and terms acceptance
    privacy_accepted = models.BooleanField(
        _('privacy policy accepted'),
        default=False,
        help_text=_('Whether the user accepted privacy policy')
    )
    terms_accepted = models.BooleanField(
        _('terms accepted'),
        default=False,
        help_text=_('Whether the user accepted terms of service')
    )
    accepted_at = models.DateTimeField(
        _('accepted at'),
        blank=True,
        null=True,
        help_text=_('When the user accepted privacy and terms')
    )
    
    # Engagement tracking
    first_interaction = models.DateTimeField(
        _('first interaction'),
        auto_now_add=True,
        help_text=_('When the user first interacted with the widget')
    )
    last_interaction = models.DateTimeField(
        _('last interaction'),
        auto_now=True,
        help_text=_('Most recent interaction with the widget')
    )
    total_questions = models.PositiveIntegerField(
        _('total questions'),
        default=0,
        help_text=_('Total number of questions asked')
    )
    
    # Status
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether this engagement user is active')
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('User Engagement')
        verbose_name_plural = _('User Engagements')
        db_table = 'widget_user_engagement'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['source_website']),
        ]
    
    def __str__(self):
        return f"Widget User: {self.email}"
    
    def increment_questions(self):
        """Increment the total questions counter."""
        self.total_questions += 1
        self.save(update_fields=['total_questions', 'last_interaction'])