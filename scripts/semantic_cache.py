#!/usr/bin/env python3
"""
Semantic Caching System for LiteLLM Gateway.

Implements intelligent caching based on semantic similarity of prompts
rather than exact text matching. This allows cache hits for similar
queries even when wording differs.

Features:
- Embedding-based similarity matching
- Configurable similarity threshold
- Redis backend for distributed caching
- TTL management per cache entry
- Cost tracking and analytics
- Cache warming capabilities

Usage:
    from semantic_cache import SemanticCache

    cache = SemanticCache()

    # Check cache before API call
    cached_response = cache.get(user_prompt, model="gpt-4o")
    if cached_response:
        return cached_response

    # After API call, store in cache
    cache.set(user_prompt, response, model="gpt-4o", ttl=3600)

Configuration:
    Set environment variables:
    - REDIS_HOST: Redis server host (default: 127.0.0.1)
    - REDIS_PORT: Redis server port (default: 6379)
    - SEMANTIC_CACHE_THRESHOLD: Similarity threshold 0.0-1.0 (default: 0.85)
    - SEMANTIC_CACHE_EMBEDDING_MODEL: Model for embeddings (default: text-embedding-3-small)
"""

import hashlib
import json
import os
from typing import Any, Optional

import numpy as np
import redis
from loguru import logger
from sentence_transformers import SentenceTransformer


class SemanticCache:
    """
    Semantic caching system using embedding similarity.

    This cache stores responses indexed by semantic embeddings of prompts,
    allowing cache hits even when queries are phrased differently but have
    similar meaning.

    Attributes:
        redis_client: Redis connection for distributed caching
        embedding_model: Sentence transformer model for creating embeddings
        similarity_threshold: Minimum cosine similarity for cache hit (0.0-1.0)
        default_ttl: Default time-to-live in seconds for cache entries
    """

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        similarity_threshold: float = None,
        embedding_model: str = None,
    ):
        """
        Initialize semantic cache with Redis backend and embedding model.

        Args:
            redis_host: Redis server host (default from env or 127.0.0.1)
            redis_port: Redis server port (default from env or 6379)
            similarity_threshold: Similarity threshold for cache hits (default 0.85)
            embedding_model: Model for generating embeddings (default: all-MiniLM-L6-v2)
        """
        # Redis configuration
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "127.0.0.1")
        self.redis_port = int(redis_port or os.getenv("REDIS_PORT", "6379"))

        # Semantic cache configuration
        self.similarity_threshold = float(
            similarity_threshold or os.getenv("SEMANTIC_CACHE_THRESHOLD", "0.85")
        )
        self.embedding_model_name = (
            embedding_model or os.getenv("SEMANTIC_CACHE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )
        self.default_ttl = 3600  # 1 hour default

        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=1,  # Use separate database from standard cache
                decode_responses=False,  # Handle binary data for embeddings
            )
            self.redis_client.ping()
            logger.info(
                "Semantic cache connected to Redis",
                host=self.redis_host,
                port=self.redis_port,
            )
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(
                "Semantic cache initialized",
                embedding_model=self.embedding_model_name,
                threshold=self.similarity_threshold,
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate semantic embedding for text using sentence transformer.

        Args:
            text: Input text to embed

        Returns:
            numpy.ndarray: Embedding vector
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding

    def _compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            float: Cosine similarity score (0.0-1.0)
        """
        # Cosine similarity formula
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)

    def _create_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """
        Create unique cache key from prompt and parameters.

        Args:
            prompt: User prompt text
            model: Model identifier
            **kwargs: Additional parameters affecting response

        Returns:
            str: Cache key for Redis storage
        """
        # Include model and relevant parameters in key
        key_data = {
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens"),
            "top_p": kwargs.get("top_p", 1.0),
        }
        key_hash = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        return f"semantic_cache::{model}::{key_hash}"

    def get(
        self,
        prompt: str,
        model: str,
        **kwargs
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve cached response if semantically similar prompt exists.

        Args:
            prompt: User prompt to search for
            model: Model identifier
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            dict or None: Cached response if found, None otherwise
        """
        try:
            # Generate embedding for input prompt
            query_embedding = self._generate_embedding(prompt)

            # Get all cached prompts for this model/params combination
            cache_key_pattern = self._create_cache_key(prompt, model, **kwargs)
            base_key = cache_key_pattern.rsplit("::", 1)[0]  # Model + params

            # Search for similar cached prompts
            for key in self.redis_client.scan_iter(f"{base_key}::*"):
                try:
                    cached_data = self.redis_client.get(key)
                    if not cached_data:
                        continue

                    cached_entry = json.loads(cached_data)
                    cached_embedding = np.array(cached_entry["embedding"])

                    # Compute similarity
                    similarity = self._compute_similarity(query_embedding, cached_embedding)

                    if similarity >= self.similarity_threshold:
                        logger.info(
                            "Semantic cache HIT",
                            model=model,
                            similarity=f"{similarity:.3f}",
                            original_prompt=cached_entry["prompt"][:50] + "...",
                            query_prompt=prompt[:50] + "...",
                        )
                        return {
                            "response": cached_entry["response"],
                            "similarity": similarity,
                            "cached_prompt": cached_entry["prompt"],
                            "cache_metadata": cached_entry.get("metadata", {}),
                        }
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Invalid cache entry: {e}")
                    continue

            logger.debug("Semantic cache MISS", model=model, prompt=prompt[:50] + "...")
            return None

        except Exception as e:
            logger.error(f"Semantic cache get error: {e}")
            return None

    def set(
        self,
        prompt: str,
        response: Any,
        model: str,
        ttl: Optional[int] = None,
        metadata: Optional[dict] = None,
        **kwargs
    ) -> bool:
        """
        Store response in semantic cache with embedding.

        Args:
            prompt: User prompt that generated this response
            response: Model response to cache
            model: Model identifier
            ttl: Time-to-live in seconds (default: 3600)
            metadata: Additional metadata to store
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            bool: True if successfully cached, False otherwise
        """
        try:
            # Generate embedding for prompt
            embedding = self._generate_embedding(prompt)

            # Create cache entry
            cache_entry = {
                "prompt": prompt,
                "response": response,
                "embedding": embedding.tolist(),  # Convert to list for JSON
                "model": model,
                "metadata": metadata or {},
            }

            # Create unique key for this specific prompt
            prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            cache_key = f"{self._create_cache_key(prompt, model, **kwargs)}::{prompt_hash}"

            # Store in Redis with TTL
            ttl = ttl or self.default_ttl
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_entry)
            )

            logger.info(
                "Semantic cache SET",
                model=model,
                prompt=prompt[:50] + "...",
                ttl=ttl,
            )
            return True

        except Exception as e:
            logger.error(f"Semantic cache set error: {e}")
            return False

    def invalidate(self, model: Optional[str] = None) -> int:
        """
        Invalidate cached entries for a specific model or all models.

        Args:
            model: Model to invalidate (None = invalidate all)

        Returns:
            int: Number of keys deleted
        """
        try:
            pattern = f"semantic_cache::{model}::*" if model else "semantic_cache::*"
            deleted = 0

            for key in self.redis_client.scan_iter(pattern):
                self.redis_client.delete(key)
                deleted += 1

            logger.info("Semantic cache invalidated", model=model or "all", deleted_keys=deleted)
            return deleted

        except Exception as e:
            logger.error(f"Semantic cache invalidation error: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics and metrics.

        Returns:
            dict: Statistics including total keys, memory usage, etc.
        """
        try:
            total_keys = len(list(self.redis_client.scan_iter("semantic_cache::*")))
            info = self.redis_client.info("memory")

            return {
                "total_cached_prompts": total_keys,
                "redis_memory_used": info.get("used_memory_human"),
                "similarity_threshold": self.similarity_threshold,
                "embedding_model": self.embedding_model_name,
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


# CLI for testing and management
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Cache Management")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--invalidate", type=str, help="Invalidate cache for model")
    parser.add_argument("--test", action="store_true", help="Run test queries")

    args = parser.parse_args()

    cache = SemanticCache()

    if args.stats:
        stats = cache.get_stats()
        print(json.dumps(stats, indent=2))

    elif args.invalidate:
        deleted = cache.invalidate(args.invalidate if args.invalidate != "all" else None)
        print(f"Deleted {deleted} cache entries")

    elif args.test:
        # Test semantic similarity
        test_prompts = [
            "What is the capital of France?",
            "Tell me the capital city of France",
            "Which city is the capital of France?",
        ]

        model = "gpt-4o-mini"

        # Cache first prompt
        response = {"choices": [{"message": {"content": "Paris is the capital of France."}}]}
        cache.set(test_prompts[0], response, model)

        # Test similarity matching
        for prompt in test_prompts[1:]:
            result = cache.get(prompt, model)
            if result:
                print(f"✓ Cache HIT for: {prompt}")
                print(f"  Similarity: {result['similarity']:.3f}")
                print(f"  Original: {result['cached_prompt']}")
            else:
                print(f"✗ Cache MISS for: {prompt}")
