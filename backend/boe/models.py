# boe/models.py
from django.db import models
from django.utils import timezone


class BOEUpdateLog(models.Model):
    STATUS_CHOICES = [
        ("success", "Success"),
        ("failure", "Failure"),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.TextField(blank=True, null=True)  # store error/success details
    articles_ingested = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.timestamp} - {self.status} ({self.articles_ingested} articles)"

class BOEDocument(models.Model):
    boe_id = models.CharField(max_length=255, unique=True)  # canonical id from BOE
    title = models.TextField(blank=True)
    url = models.URLField()
    published_at = models.DateTimeField(null=True, blank=True)
    raw_html = models.TextField(blank=True)
    raw_text = models.TextField(blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=100, default='boe')

    def __str__(self):
        return f"{self.boe_id} - {self.title[:120]}"

class BOEArticle(models.Model):
    document = models.ForeignKey(BOEDocument, on_delete=models.CASCADE, related_name='articles')
    article_number = models.CharField(max_length=100, blank=True, null=True)
    heading = models.TextField(blank=True)
    content = models.TextField()
    section = models.CharField(max_length=100, blank=True, null=True)
    start_offset = models.IntegerField(default=0)
    end_offset = models.IntegerField(default=0)
    indexed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    source_url = models.URLField(blank=True, null=True)

    normative_version = models.CharField(max_length=100, blank=True, null=True)


    class Meta:
        indexes = [
            models.Index(fields=['article_number']),
            models.Index(fields=['indexed']),
        ]

    def __str__(self):
        return f"{self.article_number or '-'} ({self.document.boe_id})"

class IngestLog(models.Model):
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, default='running')  # running, success, partial, failed
    message = models.TextField(blank=True)
    processed = models.IntegerField(default=0)

    def mark_done(self, status='success', message=''):
        self.finished_at = timezone.now()
        self.status = status
        self.message = message
        self.save()

class CendojDecision(models.Model):
    """
    Minimal model to store parsed CENDOJ decisions metadata and content.
    """
    unique_id = models.CharField(max_length=200, unique=True, db_index=True)  # provider id
    court = models.CharField(max_length=255, blank=True, null=True)
    decision_date = models.DateField(blank=True, null=True)
    decision_number = models.CharField(max_length=200, blank=True, null=True)
    subject = models.CharField(max_length=400, blank=True, null=True)
    parties = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    raw_xml = models.TextField(blank=True, null=True)
    source_url = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.unique_id} - {self.court or 'unknown'}"
