"""
Embedding service for generating and caching text embeddings.
Enhanced with PDF processing and vector database functionality.
"""
import hashlib
import json
import time
from typing import List, Optional, Dict, Any
from django.core.cache import cache
from django.conf import settings
import openai
from apps.core.exceptions import OpenAIException
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI's API with Redis caching.
    """
    
    EMBEDDING_MODEL = "text-embedding-3-small"
    CACHE_PREFIX = "embedding:"
    CACHE_TTL = 60 * 60 * 24 * 30  # 30 days
    
    def __init__(self):
        self.model = self.EMBEDDING_MODEL
        self.client = client

    def _generate_cache_key(self, text: str) -> str:
        """Generate a cache key for the given text."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"{self.CACHE_PREFIX}{self.model}:{text_hash}"

    def get_embedding(self, text: str, use_cache: bool = True) -> Optional[List[float]]:
        """
        Get embedding for a single text string.
        
        Args:
            text: Text to embed
            use_cache: Whether to use Redis cache
            
        Returns:
            List of floats representing the embedding, or None if failed
        """
        if not text or not text.strip():
            return None

        text = text.strip()
        cache_key = self._generate_cache_key(text)

        # Try to get from cache first
        if use_cache:
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                logger.debug(f"Cache hit for embedding: {text[:50]}...")
                return cached_embedding

        try:
            # Generate embedding using OpenAI API
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            if use_cache:
                cache.set(cache_key, embedding, self.CACHE_TTL)
                logger.debug(f"Cached embedding for: {text[:50]}...")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise OpenAIException(f"Embedding generation failed: {str(e)}")

    def get_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 100,
        use_cache: bool = True
    ) -> Dict[str, List[float]]:
        """
        Get embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each API call
            use_cache: Whether to use Redis cache
            
        Returns:
            Dictionary mapping text to embedding
        """
        if not texts:
            return {}

        embeddings_map = {}
        texts_to_process = []
        
        # Check cache for existing embeddings
        if use_cache:
            for text in texts:
                if not text or not text.strip():
                    continue
                    
                text = text.strip()
                cache_key = self._generate_cache_key(text)
                cached_embedding = cache.get(cache_key)
                
                if cached_embedding:
                    embeddings_map[text] = cached_embedding
                    logger.debug(f"Cache hit for batch embedding: {text[:30]}...")
                else:
                    texts_to_process.append(text)
        else:
            texts_to_process = [text.strip() for text in texts if text and text.strip()]

        # Process remaining texts in batches
        if texts_to_process:
            logger.info(f"Processing {len(texts_to_process)} texts for embeddings")
            
            for i in range(0, len(texts_to_process), batch_size):
                batch = texts_to_process[i:i + batch_size]
                batch_embeddings = self._process_embedding_batch(batch, use_cache)
                embeddings_map.update(batch_embeddings)
                
                # Add small delay between batches to respect rate limits
                if i + batch_size < len(texts_to_process):
                    time.sleep(0.1)

        logger.info(f"Generated embeddings for {len(embeddings_map)} texts")
        return embeddings_map

    def _process_embedding_batch(
        self, 
        texts: List[str], 
        use_cache: bool = True
    ) -> Dict[str, List[float]]:
        """Process a single batch of texts for embeddings."""
        try:
            # Generate embeddings using OpenAI API
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            
            batch_embeddings = {}
            
            for i, embedding_data in enumerate(response.data):
                text = texts[i]
                embedding = embedding_data.embedding
                batch_embeddings[text] = embedding
                
                # Cache individual embeddings
                if use_cache:
                    cache_key = self._generate_cache_key(text)
                    cache.set(cache_key, embedding, self.CACHE_TTL)
            
            logger.debug(f"Processed batch of {len(texts)} embeddings")
            return batch_embeddings
            
        except Exception as e:
            logger.error(f"Failed to process embedding batch: {str(e)}")
            # Return empty dict for this batch - calling code will handle missing embeddings
            return {}

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text string.
        Uses a simple approximation: ~4 characters per token for English text.
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings for the current model."""
        if self.model == "text-embedding-3-small":
            return 1536
        elif self.model == "text-embedding-3-large":
            return 3072
        elif self.model == "text-embedding-ada-002":
            return 1536
        else:
            # Default fallback
            return 1536

    def clear_cache(self, text: Optional[str] = None) -> bool:
        """
        Clear embedding cache.
        
        Args:
            text: If provided, clear cache for specific text. Otherwise clear all.
            
        Returns:
            True if successful
        """
        try:
            if text:
                cache_key = self._generate_cache_key(text)
                cache.delete(cache_key)
                logger.info(f"Cleared cache for specific text: {text[:50]}...")
            else:
                # Clear all embedding cache keys (this is a simplified approach)
                # In production, you might want to use cache.delete_pattern if available
                logger.warning("Full cache clear not implemented - clear specific texts instead")
                
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache."""
        try:
            # This is a simplified implementation
            # In production, you might want more detailed cache statistics
            return {
                "cache_enabled": True,
                "cache_ttl_seconds": self.CACHE_TTL,
                "model": self.model,
                "embedding_dimension": self.get_embedding_dimension()
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {
                "cache_enabled": False,
                "error": str(e)
            }
