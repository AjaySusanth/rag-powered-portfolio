"""
DESIGN DECISION:
This module contains unit tests for the Azure OpenAI embedding generator.
It uses standard `unittest.mock` to mock the AsyncAzureOpenAI client, preventing any
real network calls during test execution (aligning with our testing conventions).

Since `pytest-asyncio` is not in requirements, we leverage the pre-installed `anyio` plugin
with `@pytest.mark.anyio` to execute async test coroutines cleanly.
"""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from src.ingestion.embedder import embed_texts, embed_query, EmbeddingError


@pytest.fixture(autouse=True)
def mock_cache_always_miss():
    """Ensures that all embedder tests run with a clean cache miss, preventing real Redis connectivity or cache hits."""
    with patch("src.ingestion.embedder.create_cache_from_settings") as mock_factory:
        mock_cache = MagicMock()
        mock_cache.get_embeddings = AsyncMock(side_effect=lambda texts: [None] * len(texts))
        mock_cache.set_embeddings = AsyncMock()
        mock_factory.return_value = mock_cache
        yield mock_cache


@pytest.mark.anyio
async def test_embed_texts_success() -> None:
    """
    Verifies that embed_texts correctly parses and returns the embedding vectors
    returned by the Azure OpenAI API, maintaining correct index ordering.
    """
    mock_response = AsyncMock()
    # Mock data items representing return value of response.data
    # Sorted by index to verify we sort them correctly in the code
    mock_item_1 = AsyncMock()
    mock_item_1.index = 1
    mock_item_1.embedding = [0.2] * 1536

    mock_item_0 = AsyncMock()
    mock_item_0.index = 0
    mock_item_0.embedding = [0.1] * 1536

    mock_response.data = [mock_item_1, mock_item_0]

    with patch("src.ingestion.embedder.get_azure_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        texts = ["hello", "world"]
        results = await embed_texts(texts)

        # Assert results match sorted order of indices (0 first, then 1)
        assert len(results) == 2
        assert results[0] == pytest.approx([0.1] * 1536)
        assert results[1] == pytest.approx([0.2] * 1536)
        
        # Verify call parameters
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.anyio
async def test_embed_texts_empty() -> None:
    """Verifies that an empty input list returns an empty list without calling the API."""
    with patch("src.ingestion.embedder.get_azure_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        
        results = await embed_texts([])
        assert results == []
        mock_client.embeddings.create.assert_not_called()


@pytest.mark.anyio
async def test_embed_texts_failure() -> None:
    """Verifies that a custom EmbeddingError is raised when the API call fails."""
    with patch("src.ingestion.embedder.get_azure_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.embeddings.create.side_effect = Exception("API rate limit exceeded")
        mock_get_client.return_value = mock_client

        with pytest.raises(EmbeddingError) as exc_info:
            await embed_texts(["error test"])

        assert "Azure OpenAI embedding generation failed" in str(exc_info.value)


@pytest.mark.anyio
async def test_embed_query_returns_single_vector() -> None:
    """
    Verifies that embed_query returns a single flat vector (list[float])
    for a single input string, not a nested list.
    """
    mock_response = AsyncMock()
    mock_item = AsyncMock()
    mock_item.index = 0
    mock_item.embedding = [0.42] * 1536
    mock_response.data = [mock_item]

    with patch("src.ingestion.embedder.get_azure_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = await embed_query("what is Ajay's experience with Kubernetes?")

        # Must be a flat list of floats, not a list of lists
        assert isinstance(result, list)
        assert len(result) == 1536
        assert result[0] == pytest.approx(0.42)
        # Exactly one API call, with the query wrapped in a single-element list
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.anyio
async def test_embed_query_propagates_error() -> None:
    """
    Verifies that EmbeddingError raised inside embed_texts propagates
    cleanly through the embed_query wrapper without being swallowed.
    """
    with patch("src.ingestion.embedder.get_azure_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.embeddings.create.side_effect = Exception("timeout")
        mock_get_client.return_value = mock_client

        with pytest.raises(EmbeddingError):
            await embed_query("trigger failure")
