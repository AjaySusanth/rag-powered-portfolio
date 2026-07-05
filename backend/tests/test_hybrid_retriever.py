from unittest.mock import AsyncMock, patch

import pytest

from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.retrieval.hybrid_retriever import retrieve


def make_mock_chunk(chunk_id: str, project: str = "n8n", source_file: str = "file.py") -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        parent_document_id="doc-1",
        content_hash="h1",
        content="content",
        project=project,
        layer="artifact",
        source_type="github",
        source_file=source_file,
        chunk_index=0,
        token_count=10,
        char_count=50,
        metadata={}
    )

@pytest.mark.anyio
async def test_hybrid_retrieve_empty_query():
    res = await retrieve("")
    assert res == []

    res = await retrieve("   ")
    assert res == []

@pytest.mark.anyio
@patch("src.retrieval.vector_retriever.retrieve", new_callable=AsyncMock)
@patch("src.retrieval.bm25_retriever.retrieve", new_callable=AsyncMock)
async def test_hybrid_retrieve_orchestration(mock_bm25_retrieve, mock_vector_retrieve):
    chunk_v1 = make_mock_chunk("chunk-v1")
    chunk_v2 = make_mock_chunk("chunk-v2")
    chunk_b1 = make_mock_chunk("chunk-b1")

    mock_vector_retrieve.return_value = [
        RetrievalResult(chunk=chunk_v1, score=0.9),
        RetrievalResult(chunk=chunk_v2, score=0.8)
    ]

    mock_bm25_retrieve.return_value = [
        RetrievalResult(chunk=chunk_b1, score=30.0),
        RetrievalResult(chunk=chunk_v1, score=15.0) # duplicate / overlap
    ]

    results = await retrieve("kubernetes", top_k=2, project="n8n", diversify=False)

    # Assert retriever functions called with correct arguments (candidate_k=20 by default)
    mock_vector_retrieve.assert_called_once_with(query="kubernetes", top_k=20, project="n8n")
    mock_bm25_retrieve.assert_called_once_with(query="kubernetes", top_k=20, project="n8n")

    # Top-K should slice result to 2
    assert len(results) == 2

    # chunk-v1 was rank 1 in vector, rank 2 in bm25 -> score = 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.0325
    # chunk-v2 was rank 2 in vector, not in bm25 -> score = 1/(60+2) = 1/62 = 0.0161
    # chunk-b1 was rank 1 in bm25, not in vector -> score = 1/(60+1) = 1/61 = 0.0163
    #
    # Order should be: chunk-v1 (0.0325), chunk-b1 (0.0163), chunk-v2 (0.0161)
    # sliced to 2 results -> [chunk-v1, chunk-b1]

    assert results[0].chunk.chunk_id == "chunk-v1"
    assert results[0].vector_rank == 1
    assert results[0].bm25_rank == 2

    assert results[1].chunk.chunk_id == "chunk-b1"
    assert results[1].vector_rank is None
    assert results[1].bm25_rank == 1

@pytest.mark.anyio
@patch("src.retrieval.vector_retriever.retrieve", new_callable=AsyncMock)
@patch("src.retrieval.bm25_retriever.retrieve", new_callable=AsyncMock)
async def test_hybrid_retrieve_with_diversification(mock_bm25_retrieve, mock_vector_retrieve):
    chunk_v1 = make_mock_chunk("chunk-v1", source_file="file_a.py")
    chunk_v2 = make_mock_chunk("chunk-v2", source_file="file_a.py")
    chunk_b1 = make_mock_chunk("chunk-b1", source_file="file_b.py")

    mock_vector_retrieve.return_value = [
        RetrievalResult(chunk=chunk_v1, score=0.9),
        RetrievalResult(chunk=chunk_v2, score=0.8)
    ]

    mock_bm25_retrieve.return_value = [
        RetrievalResult(chunk=chunk_b1, score=30.0),
        RetrievalResult(chunk=chunk_v1, score=15.0)
    ]

    # top_k=2 with diversify=True should keep chunk-v1 (file_a.py) and chunk-b1 (file_b.py)
    # but discard chunk-v2 (file_a.py) because file_a.py is already represented.
    results = await retrieve("kubernetes", top_k=2, project="n8n", diversify=True)

    assert len(results) == 2
    assert results[0].chunk.chunk_id == "chunk-v1"  # file_a.py (RRF score: 0.0325)
    assert results[1].chunk.chunk_id == "chunk-b1"  # file_b.py (RRF score: 0.0163)


@pytest.mark.anyio
@patch("src.retrieval.vector_retriever.retrieve", new_callable=AsyncMock)
@patch("src.retrieval.bm25_retriever.retrieve", new_callable=AsyncMock)
@patch("src.retrieval.hybrid_retriever.create_grader_from_settings")
async def test_hybrid_retrieve_with_grading(mock_create_grader, mock_bm25_retrieve, mock_vector_retrieve):
    chunk_v1 = make_mock_chunk("chunk-v1", source_file="file_a.py")
    chunk_v2 = make_mock_chunk("chunk-v2", source_file="file_b.py")
    chunk_v3 = make_mock_chunk("chunk-v3", source_file="file_c.py")

    mock_vector_retrieve.return_value = [
        RetrievalResult(chunk=chunk_v1, score=0.9),
        RetrievalResult(chunk=chunk_v2, score=0.8),
        RetrievalResult(chunk=chunk_v3, score=0.7)
    ]
    mock_bm25_retrieve.return_value = []

    # Mock grader grades:
    # chunk-v1 is relevant
    # chunk-v2 is irrelevant
    # chunk-v3 is relevant
    from src.llm.interfaces import ChunkGrade
    class SimpleMockGrader:
        async def grade(self, query, results):
            return [
                ChunkGrade(chunk_index=0, is_relevant=True, rejection_reason=None, explanation="Relevant"),
                ChunkGrade(chunk_index=1, is_relevant=False, rejection_reason="off_topic", explanation="Off-topic"),
                ChunkGrade(chunk_index=2, is_relevant=True, rejection_reason=None, explanation="Relevant")
            ]

    mock_create_grader.return_value = SimpleMockGrader()

    # Run with top_k=3, diversify=True, grade=True, min_chunks=2
    # chunk-v2 is filtered out, leaving chunk-v1 and chunk-v3.
    # Since 2 relevant chunks >= min_chunks (2), it should return [chunk-v1, chunk-v3]
    results = await retrieve("kubernetes", top_k=3, project="n8n", diversify=True, grade=True, min_chunks=2)

    assert len(results) == 2
    assert results[0].chunk.chunk_id == "chunk-v1"
    assert results[1].chunk.chunk_id == "chunk-v3"


