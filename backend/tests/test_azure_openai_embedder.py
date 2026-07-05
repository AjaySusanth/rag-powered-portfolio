from unittest.mock import AsyncMock, patch

import pytest

from src.embedding.azure_openai_embedder import embed_chunks
from src.models.chunk import Chunk


@pytest.fixture
def mock_chunks():
    """Returns a list of 5 mock Chunk objects."""
    return [
        Chunk(
            chunk_id=f"c{i}",
            parent_document_id="doc1",
            content_hash=f"h{i}",
            content=f"This is chunk number {i}",
            project="test",
            layer="identity",
            source_type="github",
            source_file="test.md",
            chunk_index=i,
            token_count=10,
            char_count=50,
            metadata={"document_id": "doc1"}
        )
        for i in range(5)
    ]


@pytest.mark.anyio
async def test_embed_chunks_success(mock_chunks):
    """
    Verifies that embed_chunks extracts chunk content and returns corresponding embeddings.
    """
    mock_embeddings = [[float(i)] * 1536 for i in range(5)]

    with patch("src.embedding.azure_openai_embedder.embed_texts", new_callable=AsyncMock) as mock_embed_texts:
        mock_embed_texts.return_value = mock_embeddings

        results = await embed_chunks(mock_chunks)

        # Verify call arguments
        mock_embed_texts.assert_called_once_with(
            [c.content for c in mock_chunks],
            batch_size=100
        )

        # Verify ordering and alignment
        assert len(results) == 5
        for i in range(5):
            assert results[i] == mock_embeddings[i]


@pytest.mark.anyio
async def test_embed_chunks_empty():
    """
    Verifies that passing an empty list of chunks returns an empty list immediately.
    """
    results = await embed_chunks([])
    assert results == []


@pytest.mark.anyio
async def test_embed_chunks_batching(mock_chunks):
    """
    Verifies that the batch_size argument is correctly passed down to the underlying embedder.
    """
    mock_embeddings = [[0.1] * 1536] * 5

    with patch("src.embedding.azure_openai_embedder.embed_texts", new_callable=AsyncMock) as mock_embed_texts:
        mock_embed_texts.return_value = mock_embeddings

        await embed_chunks(mock_chunks, batch_size=2)

        mock_embed_texts.assert_called_once_with(
            [c.content for c in mock_chunks],
            batch_size=2
        )


@pytest.mark.anyio
async def test_embed_chunks_mismatch_guard(mock_chunks):
    """
    Verifies that a ValueError is raised if the underlying embedder returns
    a different number of embeddings than the input chunks.
    """
    # Only return 4 embeddings instead of 5
    mock_embeddings = [[0.1] * 1536] * 4

    with patch("src.embedding.azure_openai_embedder.embed_texts", new_callable=AsyncMock) as mock_embed_texts:
        mock_embed_texts.return_value = mock_embeddings

        with pytest.raises(ValueError, match="Embedding count mismatch"):
            await embed_chunks(mock_chunks)
