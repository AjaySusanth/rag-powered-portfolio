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
import struct
import base64
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

    def _generate_embedding_key(self, text: str) -> str:
        """
        Generates a SHA-256 hash of the normalized text.
        Prefixes with provider and model to ensure cache is provider-agnostic.
        """
        normalized_text = text.strip().lower()
        key_content = f"{normalized_text}:{settings.EMBEDDING_PROVIDER}:{settings.EMBEDDING_MODEL}"
        key_hash = hashlib.sha256(key_content.encode("utf-8")).hexdigest()
        return f"rag:embed:v1:{key_hash}"

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Retrieves a cached embedding vector for the given text.
        """
        try:
            client = await self._get_client()
            key = self._generate_embedding_key(text)
            data = await client.get(key)
            if data:
                packed_bytes = base64.b64decode(data.encode("ascii"))
                return list(struct.unpack(f"{len(packed_bytes)//4}f", packed_bytes))
            return None
        except RedisError:
            return None
        except Exception:
            return None

    async def set_embedding(self, text: str, embedding: List[float]) -> None:
        """
        Stores an embedding vector for the given text in the cache.
        """
        try:
            client = await self._get_client()
            key = self._generate_embedding_key(text)
            packed_bytes = struct.pack(f"{len(embedding)}f", *embedding)
            b64_str = base64.b64encode(packed_bytes).decode("ascii")
            await client.set(
                name=key,
                value=b64_str,
                ex=settings.EMBEDDING_CACHE_TTL_SECONDS
            )
        except RedisError:
            pass
        except Exception:
            pass

    async def get_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Retrieves cached embedding vectors for a list of texts in order.
        Uses MGET for bulk efficiency.
        """
        if not texts:
            return []
        try:
            client = await self._get_client()
            keys = [self._generate_embedding_key(t) for t in texts]
            results = await client.mget(keys)
            
            embeddings: List[Optional[List[float]]] = []
            for data in results:
                if data:
                    packed_bytes = base64.b64decode(data.encode("ascii"))
                    embeddings.append(list(struct.unpack(f"{len(packed_bytes)//4}f", packed_bytes)))
                else:
                    embeddings.append(None)
            return embeddings
        except RedisError:
            return [None] * len(texts)
        except Exception:
            return [None] * len(texts)

    async def set_embeddings(self, texts: List[str], embeddings: List[List[float]]) -> None:
        """
        Stores embedding vectors for a list of texts in the cache.
        Uses pipeline for bulk efficiency.
        """
        if not texts or not embeddings:
            return
        try:
            client = await self._get_client()
            async with client.pipeline(transaction=False) as pipe:
                for text, embedding in zip(texts, embeddings):
                    key = self._generate_embedding_key(text)
                    packed_bytes = struct.pack(f"{len(embedding)}f", *embedding)
                    b64_str = base64.b64encode(packed_bytes).decode("ascii")
                    pipe.set(name=key, value=b64_str, ex=settings.EMBEDDING_CACHE_TTL_SECONDS)
                await pipe.execute()
        except RedisError:
            pass
        except Exception:
            pass
