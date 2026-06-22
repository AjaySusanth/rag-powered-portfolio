"""
DESIGN DECISION:
This module contains unit tests for the Azure OpenAI embedding generator.
It uses standard `unittest.mock` to mock the AsyncAzureOpenAI client, preventing any
real network calls during test execution (aligning with our testing conventions).

Since `pytest-asyncio` is not in requirements, we leverage the pre-installed `anyio` plugin
with `@pytest.mark.anyio` to execute async test coroutines cleanly.
"""

from unittest.mock import AsyncMock, patch
import pytest
from src.ingestion.embedder import embed_texts, EmbeddingError


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
        assert results[0] == [0.1] * 1536
        assert results[1] == [0.2] * 1536
        
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
