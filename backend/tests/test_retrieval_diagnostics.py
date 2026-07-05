from unittest.mock import AsyncMock, patch

import pytest

from src.evaluation.retrieval_diagnostics import RetrievalDiagnostics
from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult


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
@patch("src.retrieval.vector_retriever.retrieve", new_callable=AsyncMock)
@patch("src.retrieval.bm25_retriever.retrieve", new_callable=AsyncMock)
async def test_diagnostics_failure_classification(mock_bm25_retrieve, mock_vector_retrieve):
    diagnostics = RetrievalDiagnostics(k=10)

    dataset = {
        "project": "n8n",
        "questions": [
            {
                "id": "Q1",
                "question": "Query 1",
                "expected_sources": ["expected-1.md"],
                "minimum_match": 1
            }
        ]
    }

    # CASE 1: Missing from both retrievers
    # Expected: "expected-1.md". Let's retrieve files that do NOT match it.
    mock_vector_retrieve.return_value = [
        RetrievalResult(chunk=make_mock_chunk("c1", "other-1.md"), score=0.9)
    ]
    mock_bm25_retrieve.return_value = [
        RetrievalResult(chunk=make_mock_chunk("c2", "other-2.md"), score=40.0)
    ]

    summary = await diagnostics.analyze_dataset(dataset)
    assert len(summary.query_details) == 1
    failures = summary.query_details[0].failures
    assert len(failures) == 1
    assert failures[0].category == "Missing from both retrievers"

    # CASE 2: Candidate starvation
    # Expected file "expected-1.md" is at rank 6 (index 5) in vector, and not present in BM25 (both > 5)
    v_results = [make_mock_chunk(f"v{i}", f"other-{i}.md") for i in range(5)] + [make_mock_chunk("exp", "expected-1.md")]
    b_results = [make_mock_chunk(f"b{i}", f"other-{i+10}.md") for i in range(5)]

    mock_vector_retrieve.return_value = [RetrievalResult(chunk=c, score=0.9) for c in v_results]
    mock_bm25_retrieve.return_value = [RetrievalResult(chunk=c, score=40.0) for c in b_results]

    summary = await diagnostics.analyze_dataset(dataset)
    failures = summary.query_details[0].failures
    assert len(failures) == 1
    assert failures[0].category == "Candidate starvation"

    # CASE 3: Duplicate source domination
    # Expected file "expected-1.md" is at rank 5 in Vector (enters pool!)
    # But RRF fusion ranks it at position 10 because duplicates of "duplicate.md" fill the list
    v_results = [
        make_mock_chunk("u1", "unique-1.md"),
        make_mock_chunk("d1", "duplicate.md"),
        make_mock_chunk("d2", "duplicate.md"),
        make_mock_chunk("d3", "duplicate.md"),
        make_mock_chunk("exp", "expected-1.md")
    ]
    b_results = [
        make_mock_chunk("u2", "unique-2.md"),
        make_mock_chunk("d4", "duplicate.md"),
        make_mock_chunk("d5", "duplicate.md"),
        make_mock_chunk("d6", "duplicate.md"),
        make_mock_chunk("d7", "duplicate.md")
    ]
    mock_vector_retrieve.return_value = [RetrievalResult(chunk=c, score=0.9) for c in v_results]
    mock_bm25_retrieve.return_value = [RetrievalResult(chunk=c, score=40.0) for c in b_results]

    summary = await diagnostics.analyze_dataset(dataset)
    failures = summary.query_details[0].failures
    assert len(failures) == 1
    assert failures[0].category == "Duplicate source domination"

    # CASE 4: Fusion ordering
    # Expected file is in the pool (e.g. rank 5 in Vector), but even after deduplication,
    # it sits at rank > 5 because there are 5 other unique files ahead of it.
    v_results = [
        make_mock_chunk("u1", "unique-1.md"),
        make_mock_chunk("u2", "unique-2.md"),
        make_mock_chunk("u3", "unique-3.md"),
        make_mock_chunk("u4", "unique-4.md"),
        make_mock_chunk("exp", "expected-1.md")
    ]
    b_results = [
        make_mock_chunk("u5", "unique-5.md")
    ]
    mock_vector_retrieve.return_value = [RetrievalResult(chunk=c, score=0.9) for c in v_results]
    mock_bm25_retrieve.return_value = [RetrievalResult(chunk=c, score=40.0) for c in b_results]

    summary = await diagnostics.analyze_dataset(dataset)
    failures = summary.query_details[0].failures
    assert len(failures) == 1
    assert failures[0].category == "Fusion ordering"
