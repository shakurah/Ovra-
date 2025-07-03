#!/usr/bin/env python
"""Test script to verify RAG services can be imported."""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ovra_backend.settings')
django.setup()

try:
    from apps.rag_app.services import EmbeddingService, DocumentProcessingService, VectorSearchService
    print("✅ All RAG services imported successfully!")
    print("✅ EmbeddingService available")
    print("✅ DocumentProcessingService available")
    print("✅ VectorSearchService available")

    # Test database connection
    from apps.rag_app.models import LegalDocument, DocumentChunk
    print("✅ Database models imported successfully!")
    
    # Test basic database query
    doc_count = LegalDocument.objects.count()
    chunk_count = DocumentChunk.objects.count()
    print(f"✅ Database connection working - {doc_count} documents, {chunk_count} chunks")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)
