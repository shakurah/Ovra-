"""
Document Processing Service for RAG app.
Main service for orchestrating document processing pipeline.
"""
import os
import time
import logging
from typing import List, Optional, Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Main service for orchestrating document processing pipeline.
    Combines PDF processing, embedding generation, and database storage.
    """

    def __init__(self):
        from .pdf_processing_service import PDFProcessingService
        from .embedding_service import EmbeddingService
        from .vector_search_service import VectorSearchService
        
        self.pdf_service = PDFProcessingService()
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorSearchService()

    def process_pdf_document(
        self,
        file_path: str,
        document_title: str,
        document_type: str = "Legal Document"
    ) -> Dict[str, Any]:
        """
        Complete pipeline for processing a PDF document.

        Args:
            file_path: Path to the PDF file
            document_title: Human-readable title
            document_type: Type/category of document

        Returns:
            Processing results and statistics
        """
        start_time = time.time()

        try:
            # Import models here to avoid circular imports
            from ..models import LegalDocument, DocumentChunk

            # Step 1: Extract text from PDF
            logger.info(f"Starting PDF processing for: {document_title}")
            text_content, page_count = self.pdf_service.extract_text_from_pdf(file_path)

            if not text_content.strip():
                raise Exception("No text content extracted from PDF")

            # Step 2: Create or update document record
            filename = os.path.basename(file_path)
            document, created = LegalDocument.objects.get_or_create(
                filename=filename,
                defaults={
                    'title': document_title,
                    'file_path': file_path,
                    'document_type': document_type,
                    'total_pages': page_count,
                }
            )

            if not created:
                # Update existing document
                document.title = document_title
                document.document_type = document_type
                document.total_pages = page_count
                document.save()

                # Delete existing chunks (database handles this automatically)
                document.chunks.all().delete()

            # Step 3: Split text into chunks
            logger.info(f"Splitting text into chunks for document: {document.title}")
            chunk_metadata = {
                "document_id": str(document.id),
                "document_title": document.title,
                "document_type": document.document_type,
                "filename": filename
            }

            langchain_docs = self.pdf_service.split_text_into_chunks(text_content, chunk_metadata)

            # Step 4: Generate embeddings and create chunk records
            logger.info(f"Generating embeddings for {len(langchain_docs)} chunks")
            chunk_texts = [doc.page_content for doc in langchain_docs]
            embeddings_map = self.embedding_service.get_embeddings_batch(chunk_texts)

            # Step 5: Create database records with embeddings
            chunk_objects = []

            for i, doc in enumerate(langchain_docs):
                content = doc.page_content
                content_hash = self.pdf_service.generate_content_hash(content)
                embedding = embeddings_map.get(content, [])

                if not embedding:
                    logger.warning(f"No embedding generated for chunk {i}")
                    continue

                # Create DocumentChunk object with embedding stored in database
                chunk_obj = DocumentChunk(
                    document=document,
                    chunk_index=i,
                    content=content,
                    content_hash=content_hash,
                    embedding_vector=embedding,
                    token_count=self.embedding_service.estimate_tokens(content)
                )
                chunk_objects.append(chunk_obj)

            # Step 6: Bulk create chunk records (embeddings stored in database)
            DocumentChunk.objects.bulk_create(chunk_objects)
            logger.info(f"Created {len(chunk_objects)} chunks with embeddings in database")

            # Step 7: Update document metadata
            document.total_chunks = len(chunk_objects)
            document.processed_at = timezone.now()
            document.save()

            processing_time = time.time() - start_time

            result = {
                "success": True,
                "document_id": str(document.id),
                "document_title": document.title,
                "total_pages": page_count,
                "total_chunks": len(chunk_objects),
                "processing_time_seconds": round(processing_time, 2),
                "database_storage_success": True,
                "created_new": created
            }

            logger.info(f"Successfully processed document: {document.title} in {processing_time:.2f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Failed to process PDF document: {str(e)}"
            logger.error(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "processing_time_seconds": round(processing_time, 2)
            }

    def search_relevant_chunks(
        self,
        query: str,
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        law_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks based on a query.

        Args:
            query: Search query
            max_results: Maximum number of results
            similarity_threshold: Minimum similarity score
            law_filter: Optional filter by document type/law

        Returns:
            List of relevant chunks with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embedding_service.get_embedding(query)

            if not query_embedding:
                return []

            # Search using database-based vector search
            similar_chunks = self.vector_service.search_similar_chunks(
                query_embedding=query_embedding,
                n_results=max_results,
                similarity_threshold=similarity_threshold,
                law_filter=law_filter
            )

            # Log the search
            from ..models import EmbeddingSearchLog
            EmbeddingSearchLog.objects.create(
                query=query,
                query_embedding=query_embedding,
                results_count=len(similar_chunks),
                similarity_threshold=similarity_threshold
            )

            return similar_chunks

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_processing_status(self) -> Dict[str, Any]:
        """Get overall processing status and statistics."""
        try:
            from ..models import LegalDocument, DocumentChunk

            total_documents = LegalDocument.objects.count()
            processed_documents = LegalDocument.objects.filter(processed_at__isnull=False).count()
            total_chunks = DocumentChunk.objects.count()

            collection_stats = self.vector_service.get_collection_stats()

            return {
                "total_documents": total_documents,
                "processed_documents": processed_documents,
                "total_chunks": total_chunks,
                "collection_stats": collection_stats,
                "pdf_processing_available": True
            }

        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return {
                "error": str(e),
                "pdf_processing_available": False
            }
