import pytest
import struct
import base64
from unittest.mock import AsyncMock, patch, MagicMock
from src.cache.redis import RedisCache
from src.config import settings
from src.ingestion.embedder import embed_texts, EmbeddingError


# ---------------------------------------------------------------------------
# Unit Tests: Key Generation & Serialization
# ---------------------------------------------------------------------------

def test_generate_embedding_key_normalized() -> None:
    """Verifies that key generation is normalized and provider-agnostic."""
    cache = RedisCache(redis_url="redis://localhost:6379")
    
    # Check that whitespace and casing differences produce the same key
    key1 = cache._generate_embedding_key(" Hello World   ")
    key2 = cache._generate_embedding_key("hello world")
    assert key1 == key2

    # Check key format matches pattern: rag:embed:v1:<sha256>
    assert key1.startswith("rag:embed:v1:")
    
    # Verify that different provider/model changes the key
    original_provider = settings.EMBEDDING_PROVIDER
    try:
        settings.EMBEDDING_PROVIDER = "other_provider"
        key3 = cache._generate_embedding_key("hello world")
        assert key1 != key3
    finally:
        settings.EMBEDDING_PROVIDER = original_provider


def test_binary_serialization_struct_packing() -> None:
    """Verifies float vectors are encoded to Base64-packed bytes and decoded accurately."""
    original_vector = [0.123, -0.456, 0.789, 0.0]
    
    # Pack
    packed_bytes = struct.pack(f"{len(original_vector)}f", *original_vector)
    b64_str = base64.b64encode(packed_bytes).decode("ascii")
    
    # Unpack
    decoded_bytes = base64.b64decode(b64_str.encode("ascii"))
    unpacked_vector = list(struct.unpack(f"{len(decoded_bytes)//4}f", decoded_bytes))
    
    # Assert tolerance parity
    assert len(unpacked_vector) == len(original_vector)
    for a, b in zip(unpacked_vector, original_vector):
        assert pytest.approx(a) == b


@pytest.mark.anyio
@patch("src.cache.redis.RedisCache._get_client")
async def test_redis_failure_degrades_gracefully(mock_get_client) -> None:
    """Verifies that Redis exceptions degrade gracefully to None/no-ops."""
    from redis.exceptions import ConnectionError
    
    # Mock Redis client to raise ConnectionError on operations
    mock_redis = MagicMock()
    mock_redis.get.side_effect = ConnectionError("Could not connect to Redis")
    mock_redis.set.side_effect = ConnectionError("Could not connect to Redis")
    mock_redis.mget.side_effect = ConnectionError("Could not connect to Redis")
    mock_redis.pipeline.side_effect = ConnectionError("Could not connect to Redis")
    mock_get_client.return_value = mock_redis

    cache = RedisCache(redis_url="redis://localhost:6379")
    
    # get_embedding should return None
    assert await cache.get_embedding("test") is None
    
    # get_embeddings should return list of Nones
    assert await cache.get_embeddings(["test1", "test2"]) == [None, None]
    
    # set_embedding and set_embeddings should complete without raising errors
    await cache.set_embedding("test", [0.1, 0.2])
    await cache.set_embeddings(["test"], [[0.1, 0.2]])


# ---------------------------------------------------------------------------
# Integration Tests: Embedding Cache Pipeline & Batch Deduplication
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("src.ingestion.embedder.get_azure_client")
@patch("src.ingestion.embedder.create_cache_from_settings")
async def test_embedding_pipeline_cache_hit_and_miss(mock_create_cache, mock_get_client) -> None:
    """
    Verifies that cached embeddings are returned directly, and only
    cache misses invoke the Azure OpenAI client.
    """
    # 1. Setup Mock Cache returning:
    # "cached-text" -> [0.5, 0.5]
    # "miss-text" -> None (cache miss)
    mock_cache = MagicMock()
    
    async def mock_get_embeddings(texts):
        res = []
        for t in texts:
            if t == "cached-text":
                res.append([0.5, 0.5])
            else:
                res.append(None)
        return res
        
    mock_cache.get_embeddings = mock_get_embeddings
    mock_cache.set_embeddings = AsyncMock()
    mock_create_cache.return_value = mock_cache

    # 2. Setup Mock OpenAI Client
    mock_client = MagicMock()
    mock_response = MagicMock()
    
    # Embedding API returns a structure with .data list of items having .embedding and .index
    item = MagicMock()
    item.index = 0
    item.embedding = [0.9, 0.9]
    mock_response.data = [item]
    
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)
    mock_get_client.return_value = mock_client

    # 3. Call embed_texts
    results = await embed_texts(["cached-text", "miss-text"])

    # 4. Asserts
    # Verifies both inputs were returned in original order
    assert len(results) == 2
    assert results[0] == [0.5, 0.5]  # cache hit
    assert results[1] == [0.9, 0.9]  # cache miss, fetched from API

    # Assert API was called only for "miss-text"
    mock_client.embeddings.create.assert_called_once_with(
        input=["miss-text"],
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )
    
    # Assert newly fetched "miss-text" was cached
    mock_cache.set_embeddings.assert_called_once_with(
        ["miss-text"],
        [[0.9, 0.9]]
    )


@pytest.mark.anyio
@patch("src.ingestion.embedder.get_azure_client")
@patch("src.ingestion.embedder.create_cache_from_settings")
async def test_embedding_pipeline_deduplicates_duplicate_chunks_in_batch(
    mock_create_cache, mock_get_client
) -> None:
    """
    Verifies that duplicate chunks within the same embedding batch are only
    embedded once by the provider, even on a completely cold cache.
    """
    # 1. Setup Mock Cache returning None (cold cache)
    mock_cache = MagicMock()
    mock_cache.get_embeddings = AsyncMock(return_value=[None])  # Cold cache (for unique "hello")
    mock_cache.set_embeddings = AsyncMock()
    mock_create_cache.return_value = mock_cache

    # 2. Setup Mock OpenAI Client
    mock_client = MagicMock()
    mock_response = MagicMock()
    
    item = MagicMock()
    item.index = 0
    item.embedding = [0.1, 0.2, 0.3]
    mock_response.data = [item]
    
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)
    mock_get_client.return_value = mock_client

    # 3. Call embed_texts with duplicate strings
    results = await embed_texts(["hello", "hello", "hello"])

    # 4. Asserts
    # The output should contain three identical embedding vectors matching original list length
    assert len(results) == 3
    assert results[0] == [0.1, 0.2, 0.3]
    assert results[1] == [0.1, 0.2, 0.3]
    assert results[2] == [0.1, 0.2, 0.3]

    # Verify cache lookup was performed only on the UNIQUE texts (length 1)
    mock_cache.get_embeddings.assert_called_once_with(["hello"])

    # Verify that the provider API was called exactly ONCE with a list of length 1
    mock_client.embeddings.create.assert_called_once_with(
        input=["hello"],
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
    )

    # Verify the unique embedding was saved to the cache
    mock_cache.set_embeddings.assert_called_once_with(
        ["hello"],
        [[0.1, 0.2, 0.3]]
    )
