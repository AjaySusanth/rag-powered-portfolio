"""
WHY THIS WAS CHOSEN:
This module contains unit tests for the filter_relevant_chunks helper in retrieval_grader.py.
It uses a MockGrader that implements the BaseGrader interface to avoid making real LLM calls,
allowing us to test filtering and fallback behaviors deterministically.
"""

import pytest
from typing import List

from src.models.retrieval_result import RetrievalResult
from src.models.chunk import Chunk
from src.llm.interfaces import BaseGrader, ChunkGrade
from src.retrieval.retrieval_grader import filter_relevant_chunks


class MockGrader(BaseGrader):
    """A mock grader implementation that returns predefined ChunkGrade objects."""
    def __init__(self, grades: List[ChunkGrade], should_raise: bool = False):
        self.grades = grades
        self.should_raise = should_raise

    async def grade(self, query: str, results: List[RetrievalResult]) -> List[ChunkGrade]:
        if self.should_raise:
            raise RuntimeError("LLM API Call failed")
        return self.grades


def make_mock_chunk(chunk_id: str, source_file: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        parent_document_id="doc-1",
        content_hash="h1",
        content="content",
        project="n8n",
        layer="artifact",
        source_type="github",
        source_file=source_file,
        chunk_index=0,
        token_count=10,
        char_count=50,
        metadata={}
    )


@pytest.mark.anyio
async def test_filter_relevant_chunks_success():
    # Setup results: 4 chunks
    results = [
        RetrievalResult(chunk=make_mock_chunk("c1", "file_a.py"), score=0.9),
        RetrievalResult(chunk=make_mock_chunk("c2", "file_b.py"), score=0.8),
        RetrievalResult(chunk=make_mock_chunk("c3", "file_c.py"), score=0.7),
        RetrievalResult(chunk=make_mock_chunk("c4", "file_d.py"), score=0.6),
    ]

    # Mock grades: index 0, 1, 3 are relevant; index 2 is irrelevant
    grades = [
        ChunkGrade(chunk_index=0, is_relevant=True, rejection_reason=None, explanation="Direct match"),
        ChunkGrade(chunk_index=1, is_relevant=True, rejection_reason=None, explanation="Direct match"),
        ChunkGrade(chunk_index=2, is_relevant=False, rejection_reason="off_topic", explanation="Off topic details"),
        ChunkGrade(chunk_index=3, is_relevant=True, rejection_reason=None, explanation="Direct match"),
    ]

    grader = MockGrader(grades)

    # Filter with min_chunks=3 (we have 3 relevant, so no fallback should trigger)
    filtered = await filter_relevant_chunks(
        query="test query",
        results=results,
        grader=grader,
        min_chunks=3
    )

    assert len(filtered) == 3
    assert filtered[0].chunk.chunk_id == "c1"
    assert filtered[1].chunk.chunk_id == "c2"
    assert filtered[2].chunk.chunk_id == "c4"


@pytest.mark.anyio
async def test_filter_relevant_chunks_fallback():
    # Setup results: 3 chunks
    results = [
        RetrievalResult(chunk=make_mock_chunk("c1", "file_a.py"), score=0.9),
        RetrievalResult(chunk=make_mock_chunk("c2", "file_b.py"), score=0.8),
        RetrievalResult(chunk=make_mock_chunk("c3", "file_c.py"), score=0.7),
    ]

    # Mock grades: only index 0 is relevant
    grades = [
        ChunkGrade(chunk_index=0, is_relevant=True, rejection_reason=None, explanation="Direct match"),
        ChunkGrade(chunk_index=1, is_relevant=False, rejection_reason="background_only", explanation="Too general"),
        ChunkGrade(chunk_index=2, is_relevant=False, rejection_reason="off_topic", explanation="Off topic"),
    ]

    grader = MockGrader(grades)

    # Filter with min_chunks=3. Since only 1 is relevant, fallback should trigger
    # and return all 3 original chunks.
    filtered = await filter_relevant_chunks(
        query="test query",
        results=results,
        grader=grader,
        min_chunks=3
    )

    assert len(filtered) == 3
    assert [r.chunk.chunk_id for r in filtered] == ["c1", "c2", "c3"]


@pytest.mark.anyio
async def test_filter_relevant_chunks_error_fallback():
    results = [
        RetrievalResult(chunk=make_mock_chunk("c1", "file_a.py"), score=0.9),
    ]

    grader = MockGrader(grades=[], should_raise=True)

    # When grader raises exception, fallback should trigger and return original list
    filtered = await filter_relevant_chunks(
        query="test query",
        results=results,
        grader=grader,
        min_chunks=1
    )

    assert len(filtered) == 1
    assert filtered[0].chunk.chunk_id == "c1"


@pytest.mark.anyio
async def test_filter_relevant_chunks_empty():
    grader = MockGrader(grades=[])
    filtered = await filter_relevant_chunks(
        query="test query",
        results=[],
        grader=grader,
        min_chunks=1
    )
    assert filtered == []
