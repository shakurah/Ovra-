"""
Vector Search Service for RAG app.
Service for managing vector search operations using database storage.
"""
import math
from typing import List, Dict, Any
from pgvector.django import CosineDistance
import logging

logger = logging.getLogger(__name__)


class VectorSearchService:
    """
    Service for managing vector search operations using database storage.
    Uses cosine similarity for finding relevant document chunks.
    """

    @classmethod
    def calculate_cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))

            # Calculate magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))

            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    @classmethod
    def search_similar_chunks(
        cls,
        query_embedding: List[float],
        n_results: int = 5,
        similarity_threshold: float = 0.7,
        law_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using database-based vector search.

        Args:
            query_embedding: Query vector
            n_results: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            law_filter: Optional filter by document type/law

        Returns:
            List of similar chunks with metadata
        """
        try:
            from ..models import DocumentChunk
            
            # Use pgvector's optimized cosine distance search
            chunks_query = DocumentChunk.objects.filter(
                embedding_vector__isnull=False
            ).select_related('document')

            # Apply law filter if specified
            if law_filter:
                chunks_query = chunks_query.filter(
                    document__document_type__icontains=law_filter
                )

            # Order by cosine distance (lower distance = higher similarity)
            # Convert similarity threshold to distance threshold (1 - similarity)
            distance_threshold = 1.0 - similarity_threshold

            chunks_with_distance = chunks_query.annotate(
                distance=CosineDistance('embedding_vector', query_embedding)
            ).filter(
                distance__lte=distance_threshold
            ).order_by('distance')[:n_results]

            similar_chunks = []
            for chunk in chunks_with_distance:
                # Convert distance back to similarity (1 - distance)
                similarity = 1.0 - chunk.distance

                if similarity >= similarity_threshold:
                    similar_chunks.append({
                        "content": chunk.content,
                        "similarity": similarity,
                        "metadata": {
                            "document_id": str(chunk.document.id),
                            "document_title": chunk.document.title,
                            "document_type": chunk.document.document_type,
                            "chunk_index": chunk.chunk_index,
                            "filename": chunk.document.filename
                        }
                    })

            # Sort by similarity (highest first) and limit results
            similar_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            similar_chunks = similar_chunks[:n_results]

            # Add rank information
            for i, chunk in enumerate(similar_chunks):
                chunk["rank"] = i + 1

            logger.info(f"Found {len(similar_chunks)} similar chunks above threshold {similarity_threshold}")
            return similar_chunks

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    @classmethod
    def get_collection_stats(cls) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        try:
            from ..models import LegalDocument, DocumentChunk

            total_documents = LegalDocument.objects.count()
            total_chunks = DocumentChunk.objects.count()
            chunks_with_embeddings = DocumentChunk.objects.filter(
                embedding_vector__isnull=False
            ).count()

            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "chunks_with_embeddings": chunks_with_embeddings,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "chunks_with_embeddings": 0,
                "status": "error",
                "error": str(e)
            }

    @classmethod
    def search_by_document_type(
        cls,
        query_embedding: List[float],
        document_type: str,
        n_results: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks within a specific document type.

        Args:
            query_embedding: Query vector
            document_type: Document type to filter by
            n_results: Maximum number of results
            similarity_threshold: Minimum similarity threshold

        Returns:
            List of similar chunks with metadata
        """
        return cls.search_similar_chunks(
            query_embedding=query_embedding,
            n_results=n_results,
            similarity_threshold=similarity_threshold,
            law_filter=document_type
        )

    @classmethod
    def get_document_chunks(cls, document_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific document.

        Args:
            document_id: Document ID
            limit: Maximum number of chunks to return

        Returns:
            List of document chunks
        """
        try:
            from ..models import DocumentChunk

            chunks = DocumentChunk.objects.filter(
                document_id=document_id,
                embedding_vector__isnull=False
            ).select_related('document').order_by('chunk_index')[:limit]

            chunk_list = []
            for chunk in chunks:
                chunk_list.append({
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "metadata": {
                        "document_id": str(chunk.document.id),
                        "document_title": chunk.document.title,
                        "document_type": chunk.document.document_type,
                        "filename": chunk.document.filename
                    }
                })

            return chunk_list

        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []

    @classmethod
    def validate_embedding_dimension(cls, embedding: List[float], expected_dim: int = 1536) -> bool:
        """
        Validate that an embedding has the expected dimension.

        Args:
            embedding: Embedding vector to validate
            expected_dim: Expected dimension (default: 1536 for text-embedding-3-small)

        Returns:
            True if valid, False otherwise
        """
        try:
            return len(embedding) == expected_dim and all(isinstance(x, (int, float)) for x in embedding)
        except Exception:
            return False
