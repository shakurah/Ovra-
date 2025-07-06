"""
RAG App URL Configuration

This module defines URL patterns for the RAG (Retrieval-Augmented Generation) system,
including daily BOE capture management, document processing, and embedding operations.
"""

from django.urls import path
from . import views

app_name = 'rag_app'

urlpatterns = [
    # Daily BOE Capture Management
    path('capture/daily/', views.DailyCaptureView.as_view(), name='daily-capture'),
    path('capture/status/', views.CaptureStatusView.as_view(), name='capture-status'),
    path('capture/logs/', views.CaptureLogsView.as_view(), name='capture-logs'),
    
    # BOE API Testing
    path('boe/test/', views.BOETestView.as_view(), name='boe-test'),
    
    # Document and Embedding Statistics
    path('documents/stats/', views.DocumentStatsView.as_view(), name='document-stats'),
]