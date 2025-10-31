from django.db import models
from django.utils import timezone

class CitationVerificationLog(models.Model):
    """Audit log for citation verifications"""
    
    citation_text = models.CharField(max_length=255)
    document_id = models.CharField(max_length=100)
    article_id = models.CharField(max_length=100, null=True, blank=True)
    
    verification_status = models.BooleanField()
    verification_date = models.DateTimeField(default=timezone.now)
    verification_method = models.CharField(
        max_length=20,
        choices=[
            ('local', 'Local Database'),
            ('api', 'BOE API'),
            ('cache', 'Cache')
        ]
    )
    
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['verification_date']),
        ]
        
    def __str__(self):
        return f"{self.document_id} - {self.verification_date}"

class CitationVersion(models.Model):
    """Tracks different versions of legal citations"""
    
    document_id = models.CharField(max_length=100)
    article_id = models.CharField(max_length=100, null=True, blank=True)
    
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    
    modification_type = models.CharField(
        max_length=20,
        choices=[
            ('amendment', 'Amendment'),
            ('repeal', 'Repeal'),
            ('new', 'New Version')
        ]
    )
    
    superseded_by = models.CharField(max_length=100, null=True, blank=True)
    modification_reference = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['document_id', 'effective_from']),
        ]
    
    def __str__(self):
        return f"{self.document_id} - {self.effective_from}"