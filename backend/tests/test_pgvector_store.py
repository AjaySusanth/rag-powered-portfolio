import pytest
import asyncpg
from src.config import settings
from src.db.init_db import init_db
from src.db.core import close_db_pool
from src.models.chunk import Chunk
from src.vectorstore.pgvector_store import (
    upsert_chunks,
    similarity_search,
    delete_project,
    count_chunks
)


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
    await delete_project("test-project")
    
    yield
    
    # Cleanup after test
    await delete_project("test-project")
    await close_db_pool()


async def test_upsert_and_similarity_search() -> None:
    """
    Verifies that Chunk objects can be successfully upserted, and that similarity_search
    returns them sorted by cosine similarity correctly with metadata parsed.
    """
    chunks = [
        Chunk(
            chunk_id="chunk-id-0",
            parent_document_id="parent-doc-0",
            content_hash="hash-0",
            content="Python is a popular programming language.",
            project="test-project",
            layer="identity",
            source_type="github",
            source_file="test_file.md",
            chunk_index=0,
            token_count=8,
            char_count=40,
            metadata={"document_id": "parent-doc-0", "category": "programming"}
        ),
        Chunk(
            chunk_id="chunk-id-1",
            parent_document_id="parent-doc-0",
            content_hash="hash-1",
            content="Kubernetes is a container orchestration system.",
            project="test-project",
            layer="design",
            source_type="github",
            source_file="test_file.md",
            chunk_index=1,
            token_count=8,
            char_count=46,
            metadata={"document_id": "parent-doc-0", "category": "devops"}
        ),
        Chunk(
            chunk_id="chunk-id-2",
            parent_document_id="parent-doc-0",
            content_hash="hash-2",
            content="FastAPI is a fast web framework for building APIs.",
            project="test-project",
            layer="artifact",
            source_type="github",
            source_file="test_file.md",
            chunk_index=2,
            token_count=9,
            char_count=50,
            metadata={"document_id": "parent-doc-0", "category": "web"}
        ),
    ]
    
    # Create simple mock 1536-dimensional embeddings.
    # We make embedding 2 (FastAPI) close to our query vector semantically.
    embedding_0 = [1.0] + [0.0] * 1535
    embedding_1 = [0.0, 1.0] + [0.0] * 1534
    embedding_2 = [0.0, 0.0, 1.0] + [0.0] * 1533
    
    embeddings = [embedding_0, embedding_1, embedding_2]
    
    # 1. Test Ingestion / Upsert
    await upsert_chunks(chunks=chunks, embeddings=embeddings)
    
    # Verify count
    assert await count_chunks() >= 3
    
    # 2. Test Similarity Search
    # Query vector is identical to embedding 2
    query_vector = [0.0, 0.0, 1.0] + [0.0] * 1533
    
    results = await similarity_search(query_vector, limit=2, project_filter="test-project")
    
    # Assert limit is respected
    assert len(results) == 2
    
    # The first result should be the FastAPI chunk since its embedding is closest (exact match)
    assert results[0]["chunk_index"] == 2
    assert "FastAPI" in results[0]["content"]
    assert results[0]["similarity"] > 0.99  # Should be very close to 1.0 (exact match)
    
    # Verify metadata was parsed back to dict
    assert isinstance(results[0]["metadata"], dict)
    assert results[0]["metadata"]["category"] == "web"
    assert results[0]["metadata"]["document_id"] == "parent-doc-0"
    
    # 3. Test Idempotency (Upserting same chunks updates them instead of duplicating)
    updated_chunks = [
        Chunk(
            chunk_id="chunk-id-0",
            parent_document_id="parent-doc-0",
            content_hash="hash-0-new",
            content="Python is an awesome programming language.",
            project="test-project",
            layer="identity",
            source_type="github",
            source_file="test_file.md",
            chunk_index=0,
            token_count=8,
            char_count=42,
            metadata={"document_id": "parent-doc-0", "category": "programming-new"}
        )
    ]
    updated_embeddings = [[1.0] + [0.0] * 1535]
    
    await upsert_chunks(chunks=updated_chunks, embeddings=updated_embeddings)
    
    # Query again and check if content is updated
    results_after_update = await similarity_search(embedding_0, limit=1, project_filter="test-project")
    assert len(results_after_update) == 1
    assert results_after_update[0]["chunk_id"] == "chunk-id-0"
    assert "awesome" in results_after_update[0]["content"]
    assert results_after_update[0]["metadata"]["category"] == "programming-new"


async def test_delete_project() -> None:
    """Verifies that delete_project removes all chunks for a project."""
    chunks = [
        Chunk(
            chunk_id="chunk-delete-test",
            parent_document_id="parent-delete-test",
            content_hash="hash-delete",
            content="Delete test content.",
            project="test-project",
            layer="identity",
            source_type="github",
            source_file="delete_test.md",
            chunk_index=0,
            token_count=3,
            char_count=20,
            metadata={"document_id": "parent-delete-test"}
        ),
    ]
    embeddings = [[1.0] + [0.0] * 1535]
    
    await upsert_chunks(chunks=chunks, embeddings=embeddings)
    
    # Ensure it's in the database
    results = await similarity_search(embeddings[0], limit=1, project_filter="test-project")
    assert len(results) == 1
    
    # Delete the project
    await delete_project("test-project")
    
    # Verify it is gone
    results_after = await similarity_search(embeddings[0], limit=1, project_filter="test-project")
    assert len(results_after) == 0
