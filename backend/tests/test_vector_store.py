"""
DESIGN DECISION:
This module contains integration tests for the pgvector database store.
It connects to the local PostgreSQL database (running in Docker Compose) to verify
that schema initialization, bulk upserts, cosine similarity search, and deletion
work correctly.

Why Integration Tests:
  Database operations (especially vector search and HNSW indexing) are highly dependent
  on Postgres extensions and index operators. Mocking these operations provides low value,
  so we test them directly against the running local PG container. If the database is
  unreachable, the test suite will skip them gracefully.
"""

import pytest
import asyncpg
from src.config import settings
from src.db.init_db import init_db
from src.db.core import get_db_pool, close_db_pool
from src.db.vector_store import (
    upsert_document_chunks,
    search_similar_chunks,
    delete_project_chunks,
    DatabaseError
)
from src.ingestion.chunker import DocumentChunk


# Helper fixture to determine database availability
async def is_db_available() -> bool:
    """Checks if the PostgreSQL database is reachable."""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL, timeout=2.0)
        await conn.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.anyio


@pytest.fixture(autouse=True)
async def setup_database() -> None:
    """Initializes the database schema before running vector store tests."""
    if not await is_db_available():
        pytest.skip("PostgreSQL database is not running or unreachable.")
    
    # Initialize the database schema (creates tables/indices if they don't exist)
    await init_db()
    
    # Clear test project chunks to ensure clean state
    await delete_project_chunks("test-project")
    
    yield
    
    # Cleanup after test
    await delete_project_chunks("test-project")
    await close_db_pool()


async def test_upsert_and_similarity_search() -> None:
    """
    Verifies that chunks can be successfully upserted, and that search_similar_chunks
    returns them sorted by cosine similarity correctly.
    """
    chunks = [
        DocumentChunk(content="Python is a popular programming language.", token_count=8, chunk_index=0, heading="## Python"),
        DocumentChunk(content="Kubernetes is an container orchestration system.", token_count=8, chunk_index=1, heading="## Kubernetes"),
        DocumentChunk(content="FastAPI is a fast web framework for building APIs.", token_count=9, chunk_index=2, heading="## FastAPI"),
    ]
    
    # Create simple mock 1536-dimensional embeddings.
    # We make embedding 2 (FastAPI) close to our query vector semantically.
    embedding_0 = [1.0] + [0.0] * 1535
    embedding_1 = [0.0, 1.0] + [0.0] * 1534
    # Let's make embedding 2 very close to our query (e.g. identical values)
    embedding_2 = [0.0, 0.0, 1.0] + [0.0] * 1533
    
    embeddings = [embedding_0, embedding_1, embedding_2]
    
    # 1. Test Ingestion / Upsert
    await upsert_document_chunks(
        project="test-project",
        layer=2,
        source_file="test_file.md",
        chunks=chunks,
        embeddings=embeddings
    )
    
    # 2. Test Similarity Search
    # Query vector is identical to embedding 2
    query_vector = [0.0, 0.0, 1.0] + [0.0] * 1533
    
    results = await search_similar_chunks(query_vector, limit=2, project_filter="test-project")
    
    # Assert limit is respected
    assert len(results) == 2
    
    # The first result should be the FastAPI chunk since its embedding is closest (exact match)
    assert results[0]["chunk_index"] == 2
    assert "FastAPI" in results[0]["content"]
    assert results[0]["similarity"] > 0.99  # Should be very close to 1.0 (exact match)
    
    # 3. Test Idempotency (Upserting same chunks updates them)
    updated_chunks = [
        DocumentChunk(content="Python is an awesome programming language.", token_count=8, chunk_index=0, heading="## Python"),
    ]
    updated_embeddings = [[1.0] + [0.0] * 1535]
    
    await upsert_document_chunks(
        project="test-project",
        layer=2,
        source_file="test_file.md",
        chunks=updated_chunks,
        embeddings=updated_embeddings
    )
    
    # Query again and check if content is updated and orphans (indices 1 and 2) are removed
    results_after_update = await search_similar_chunks(embedding_0, limit=5, project_filter="test-project")
    assert len(results_after_update) == 1
    assert results_after_update[0]["chunk_index"] == 0
    assert "awesome" in results_after_update[0]["content"]


async def test_delete_project_chunks() -> None:
    """Verifies that deleting project chunks removes them entirely from the store."""
    chunks = [
        DocumentChunk(content="Test content.", token_count=3, chunk_index=0, heading="## Test"),
    ]
    embeddings = [[1.0] + [0.0] * 1535]
    
    await upsert_document_chunks(
        project="test-project",
        layer=1,
        source_file="delete_test.md",
        chunks=chunks,
        embeddings=embeddings
    )
    
    # Ensure they are in the database
    results = await search_similar_chunks(embeddings[0], limit=1, project_filter="test-project")
    assert len(results) == 1
    
    # Delete them
    await delete_project_chunks("test-project")
    
    # Verify they are gone
    results_after = await search_similar_chunks(embeddings[0], limit=1, project_filter="test-project")
    assert len(results_after) == 0
