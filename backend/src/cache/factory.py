"""
WHY THIS WAS CHOSEN:
Factory pattern allows swapping cache implementations (e.g., to a mock cache in tests)
without modifying the orchestrator logic, following the same pattern as LLM and Retriever factories.
"""

from src.config import settings
from src.cache.base import BaseCache
from src.cache.redis import RedisCache

def create_cache_from_settings() -> BaseCache:
    """
    Instantiates and returns the cache implementation based on configuration.
    Currently always returns a RedisCache.
    """
    return RedisCache(redis_url=settings.REDIS_URL)
