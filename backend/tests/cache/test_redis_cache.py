import json
from unittest.mock import AsyncMock, patch

import pytest
from redis.exceptions import RedisError

from src.api.schemas.chat import Citation
from src.cache.redis import RedisCache
from src.config import settings


@pytest.fixture
def mock_redis():
    with patch("src.cache.redis.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        yield mock_client


@pytest.mark.anyio
async def test_redis_cache_get_hit(mock_redis):
    cache = RedisCache("redis://localhost:6379")
    mock_redis.get.return_value = json.dumps({
        "answer": "Test answer",
        "citations": [{"file": "test.md", "layer": "layer-1", "project": "global"}]
    })

    result = await cache.get_chat_response("test query")

    assert result is not None
    assert result["answer"] == "Test answer"
    assert len(result["citations"]) == 1
    mock_redis.get.assert_called_once()

    # Verify key hashing format
    args, _ = mock_redis.get.call_args
    assert args[0].startswith("rag:chat:v1:")


@pytest.mark.anyio
async def test_redis_cache_get_miss(mock_redis):
    cache = RedisCache("redis://localhost:6379")
    mock_redis.get.return_value = None

    result = await cache.get_chat_response("test query")
    assert result is None


@pytest.mark.anyio
async def test_redis_cache_set(mock_redis):
    cache = RedisCache("redis://localhost:6379")
    citations = [Citation(file="test.md", layer="layer-1", project="global")]

    await cache.set_chat_response("test query", "Test answer", citations)

    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert kwargs["ex"] == settings.CACHE_TTL_SECONDS

    payload = json.loads(kwargs["value"])
    assert payload["answer"] == "Test answer"
    assert payload["citations"][0]["file"] == "test.md"


@pytest.mark.anyio
async def test_redis_cache_silently_degrades_on_get_error(mock_redis):
    cache = RedisCache("redis://localhost:6379")
    mock_redis.get.side_effect = RedisError("Connection refused")

    result = await cache.get_chat_response("test query")
    assert result is None  # Degrades to cache miss


@pytest.mark.anyio
async def test_redis_cache_silently_degrades_on_set_error(mock_redis):
    cache = RedisCache("redis://localhost:6379")
    mock_redis.set.side_effect = RedisError("Connection refused")

    # Should not raise exception
    await cache.set_chat_response("test query", "answer", [])
