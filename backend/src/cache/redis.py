"""
WHY THIS WAS CHOSEN:
Implements a Redis-backed response cache to reduce latency and LLM costs.
It catches Redis exceptions to ensure that Redis unavailibility degrades gracefully
to a cache miss, keeping the core chat functionality resilient.

The cache key incorporates the normalized query, the prompt version, and the 
generator provider, ensuring that future prompt or model changes invalidate old cache entries.
"""

import hashlib
import json
from typing import Optional, List, Dict, Any

from redis.asyncio import Redis, from_url
from redis.exceptions import RedisError

from src.cache.base import BaseCache
from src.config import settings
from src.api.schemas.chat import Citation


class RedisCache(BaseCache):
    """
    Redis implementation of the BaseCache for chat responses.
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[Redis] = None

    async def _get_client(self) -> Redis:
        if self._redis is None:
            self._redis = from_url(self.redis_url, decode_responses=True)
        return self._redis

    def _generate_key(self, query: str) -> str:
        """
        Generates a SHA-256 hash of the normalized query, prompt version, and model provider.
        """
        normalized_query = query.strip().lower()
        key_content = f"{normalized_query}:{settings.PROMPT_VERSION}:{settings.GENERATOR_PROVIDER}"
        key_hash = hashlib.sha256(key_content.encode("utf-8")).hexdigest()
        return f"rag:chat:v1:{key_hash}"

    async def get_chat_response(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the cached answer and citations. Silently degrades on Redis failure.
        """
        try:
            client = await self._get_client()
            key = self._generate_key(query)
            data = await client.get(key)
            if data:
                return json.loads(data)
            return None
        except RedisError:
            # Silently degrade to cache miss (Feature #18 specifies no logging yet)
            return None
        except Exception:
            return None

    async def set_chat_response(self, query: str, answer: str, citations: List[Citation]) -> None:
        """
        Stores the answer and citations with a TTL. Silently degrades on Redis failure.
        """
        try:
            client = await self._get_client()
            key = self._generate_key(query)
            payload = {
                "answer": answer,
                "citations": [c.model_dump() for c in citations]
            }
            await client.set(
                name=key,
                value=json.dumps(payload),
                ex=settings.CACHE_TTL_SECONDS
            )
        except RedisError:
            pass
        except Exception:
            pass
