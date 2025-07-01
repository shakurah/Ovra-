import uuid
from django.db import models
from django.db.models import UniqueConstraint


class LegalArticle(models.Model):
    """
    Model for storing Spanish tax law articles from BOE (Boletín Oficial del Estado).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    law = models.CharField(
        max_length=200, 
        db_index=True,
        help_text="Name of the law (e.g., 'Ley del IVA', 'Ley del IRPF')"
    )
    article_num = models.CharField(
        max_length=50,
        help_text="Article number (e.g., '21', '21.1', '21 bis')"
    )
    text = models.TextField(
        help_text="Full text content of the article"
    )
    source_url = models.URLField(
        max_length=500,
        help_text="Direct BOE URL to the article"
    )
    sync_ts = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the article was last synchronized"
    )
    
    # Additional metadata fields
    title = models.CharField(
        max_length=500,
        blank=True,
        help_text="Article title if available"
    )
    last_modified = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last modification date from BOE"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this article is currently in force"
    )
    
    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['law', 'article_num'],
                name='unique_law_article'
            )
        ]
        indexes = [
            models.Index(fields=['law', 'article_num']),
            models.Index(fields=['sync_ts']),
        ]
        ordering = ['law', 'article_num']
        verbose_name = 'Legal Article'
        verbose_name_plural = 'Legal Articles'
    
    def __str__(self):
        return f"{self.law} - Article {self.article_num}"
    
    @property
    def citation(self):
        """Generate a formal citation for the article."""
        return f"Article {self.article_num} of {self.law}"
