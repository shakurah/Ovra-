"""
Embeddings service for generating and caching text embeddings.
"""
import hashlib
import json
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
    
    @classmethod
    def _generate_cache_key(cls, text: str, model: str = None) -> str:
        """
        Generate a cache key for the given text and model.
        
        Args:
            text: The text to embed
            model: The embedding model (defaults to class default)
            
        Returns:
            SHA-256 hash-based cache key
        """
        model = model or cls.EMBEDDING_MODEL
        content = f"{model}:{text}"
        hash_digest = hashlib.sha256(content.encode()).hexdigest()
        return f"{cls.CACHE_PREFIX}{hash_digest}"
    
    @classmethod
    def get_embedding(cls, text: str, use_cache: bool = True) -> List[float]:
        """
        Get embedding for a single text, with caching.
        
        Args:
            text: The text to embed
            use_cache: Whether to use cache (default: True)
            
        Returns:
            List of embedding floats
            
        Raises:
            OpenAIException: If OpenAI API call fails
        """
        if not text.strip():
            return []
        
        # Check cache first
        if use_cache:
            cache_key = cls._generate_cache_key(text)
            cached_embedding = cache.get(cache_key)
            if cached_embedding:
                logger.debug(f"Cache hit for embedding: {cache_key}")
                return cached_embedding
        
        try:
            # Generate embedding via OpenAI
            response = client.embeddings.create(
                model=cls.EMBEDDING_MODEL,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            if use_cache:
                cache_key = cls._generate_cache_key(text)
                cache.set(cache_key, embedding, cls.CACHE_TTL)
                logger.debug(f"Cached embedding: {cache_key}")
            
            return embedding
            
        except openai.OpenAIError as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise OpenAIException(
                detail=f"Failed to generate embedding: {str(e)}",
                code="EMBEDDING_GENERATION_ERROR"
            )
        except Exception as e:
            logger.error(f"Unexpected embedding error: {str(e)}")
            raise OpenAIException(
                detail="Unexpected error generating embedding",
                code="EMBEDDING_ERROR"
            )
    
    @classmethod
    def get_embeddings_batch(
        cls, 
        texts: List[str], 
        use_cache: bool = True
    ) -> Dict[str, List[float]]:
        """
        Get embeddings for multiple texts, with caching.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Dictionary mapping text to embedding
        """
        if not texts:
            return {}
        
        embeddings_map = {}
        texts_to_embed = []
        
        # Check cache for each text
        if use_cache:
            for text in texts:
                if not text.strip():
                    embeddings_map[text] = []
                    continue
                    
                cache_key = cls._generate_cache_key(text)
                cached_embedding = cache.get(cache_key)
                if cached_embedding:
                    embeddings_map[text] = cached_embedding
                else:
                    texts_to_embed.append(text)
        else:
            texts_to_embed = [t for t in texts if t.strip()]
        
        # Generate embeddings for uncached texts
        if texts_to_embed:
            try:
                response = client.embeddings.create(
                    model=cls.EMBEDDING_MODEL,
                    input=texts_to_embed
                )
                
                # Process and cache results
                for idx, text in enumerate(texts_to_embed):
                    embedding = response.data[idx].embedding
                    embeddings_map[text] = embedding
                    
                    if use_cache:
                        cache_key = cls._generate_cache_key(text)
                        cache.set(cache_key, embedding, cls.CACHE_TTL)
                
            except openai.OpenAIError as e:
                logger.error(f"OpenAI batch embedding error: {str(e)}")
                raise OpenAIException(
                    detail=f"Failed to generate embeddings: {str(e)}",
                    code="BATCH_EMBEDDING_ERROR"
                )
            except Exception as e:
                logger.error(f"Unexpected batch embedding error: {str(e)}")
                raise OpenAIException(
                    detail="Unexpected error generating embeddings",
                    code="EMBEDDING_ERROR"
                )
        
        return embeddings_map
    
    @classmethod
    def clear_embedding_cache(cls, text: Optional[str] = None) -> bool:
        """
        Clear embedding cache for specific text or all embeddings.
        
        Args:
            text: Specific text to clear cache for (None = clear all)
            
        Returns:
            Success status
        """
        if text:
            cache_key = cls._generate_cache_key(text)
            return cache.delete(cache_key)
        else:
            # Clear all embedding cache (pattern-based delete)
            # Note: This requires Redis backend with delete_pattern support
            pattern = f"{cls.CACHE_PREFIX}*"
            deleted = cache.delete_pattern(pattern)
            logger.info(f"Cleared {deleted} embedding cache entries")
            return True
    
    @classmethod
    def estimate_tokens(cls, text: str) -> int:
        """
        Estimate token count for text (rough approximation).
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4 