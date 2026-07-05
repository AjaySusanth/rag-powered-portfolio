from unittest.mock import AsyncMock, patch

import pytest

from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.retrieval.vector_retriever import retrieve


@pytest.fixture
def mock_db_rows():
    """Returns a list of dictionaries simulating asyncpg DB rows from pgvector."""
    return [
        {
            "similarity": 0.95,
            "chunk_id": "test-chunk-1",
            "parent_document_id": "test-doc-1",
            "content_hash": "hash1",
            "content": "This is a great chunk about backend development.",
            "project": "test-project",
            "layer": "artifact",
            "source_type": "github",
            "source_file": "backend/app/main.py",
            "chunk_index": 0,
            "token_count": 10,
            "char_count": 48,
            "metadata": {"heading": "## Main"}
        },
        {
            "similarity": 0.82,
            "chunk_id": "test-chunk-2",
            "parent_document_id": "test-doc-1",
            "content_hash": "hash2",
            "content": "This is another chunk.",
            "project": "test-project",
            "layer": "artifact",
            "source_type": "github",
            "source_file": "backend/app/main.py",
            "chunk_index": 1,
            "token_count": 5,
            "char_count": 25,
            "metadata": {}
        }
    ]


@pytest.mark.anyio
@patch("src.retrieval.vector_retriever.embed_query", new_callable=AsyncMock)
@patch("src.retrieval.vector_retriever.similarity_search", new_callable=AsyncMock)
async def test_retrieve_success(mock_search, mock_embed, mock_db_rows):
    """
    Verifies that the retrieve function correctly embeds the query, searches the DB,
    and constructs strongly-typed RetrievalResult and Chunk objects.
    """
    # Setup mocks
    mock_embed.return_value = [0.1] * 1536
    mock_search.return_value = mock_db_rows

    results = await retrieve(query="backend development", top_k=2, project="test-project")

    # Verify calls
    mock_embed.assert_called_once_with("backend development")
    mock_search.assert_called_once_with(
        query_embedding=[0.1] * 1536,
        limit=2,
        project_filter="test-project"
    )

    # Verify output mappings
    assert len(results) == 2
    assert isinstance(results[0], RetrievalResult)
    assert isinstance(results[0].chunk, Chunk)

    assert results[0].score == 0.95
    assert results[0].chunk.chunk_id == "test-chunk-1"
    assert results[0].chunk.content == "This is a great chunk about backend development."
    assert results[0].chunk.metadata == {"heading": "## Main"}

    assert results[1].score == 0.82
    assert results[1].chunk.chunk_index == 1


@pytest.mark.anyio
async def test_retrieve_empty_query():
    """
    Verifies that an empty query string short-circuits and returns an empty list
    without calling the embedding or database APIs.
    """
    with patch("src.retrieval.vector_retriever.embed_query", new_callable=AsyncMock) as mock_embed:
        results = await retrieve(query="   ", top_k=5)
        assert results == []
        mock_embed.assert_not_called()


@pytest.mark.anyio
@patch("src.retrieval.vector_retriever.embed_query", new_callable=AsyncMock)
@patch("src.retrieval.vector_retriever.similarity_search", new_callable=AsyncMock)
async def test_retrieve_no_matches(mock_search, mock_embed):
    """
    Verifies that when the DB returns no rows, an empty list is returned.
    """
    mock_embed.return_value = [0.1] * 1536
    mock_search.return_value = []

    results = await retrieve(query="something obscure", top_k=5)

    assert results == []
