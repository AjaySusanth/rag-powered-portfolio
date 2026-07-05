from unittest.mock import patch

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from src.config import settings
from src.db.core import close_db_pool
from src.db.init_db import init_db
from src.main import app
from src.models.document import Document
from src.vectorstore.pgvector_store import count_chunks, delete_project


# Helper to check database availability
async def is_db_available() -> bool:
    """Checks if the PostgreSQL database is reachable."""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL, timeout=2.0)
        await conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
async def cleanup_database() -> None:
    """Ensures test projects are cleaned up before and after tests."""
    if await is_db_available():
        await init_db()
        await delete_project("test-project")
        await delete_project("__global__")
    yield
    if await is_db_available():
        await delete_project("test-project")
        await delete_project("__global__")
        await close_db_pool()


@pytest.mark.anyio
@patch("src.services.ingestion_service.IngestionService.ingest_project")
async def test_ingest_success(mock_ingest_project) -> None:
    """Verifies that the /ingest endpoint returns 200 and wraps IngestSummary on success."""
    from src.api.schemas.admin import IngestSummary

    mock_summary = IngestSummary(
        status="success",
        project_name="test-project",
        documents_processed=5,
        chunks_created=15,
        embeddings_generated=15,
        duration_seconds=1.23,
        errors=[]
    )
    mock_ingest_project.return_value = mock_summary

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ingest", json={"project_name": "test-project"})
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        summary = data["summary"]
        assert summary["status"] == "success"
        assert summary["project_name"] == "test-project"
        assert summary["documents_processed"] == 5
        assert summary["chunks_created"] == 15
        assert summary["embeddings_generated"] == 15
        assert summary["duration_seconds"] == 1.23
        assert summary["errors"] == []


@pytest.mark.anyio
@patch("src.services.ingestion_service.IngestionService.ingest_project")
async def test_ingest_missing_config(mock_ingest_project) -> None:
    """Verifies that a missing config file (FileNotFoundError) triggers an HTTP 404."""
    mock_ingest_project.side_effect = FileNotFoundError("Configuration ingest.yml not found")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ingest", json={"project_name": "invalid-project"})
        assert response.status_code == 404
        assert "Configuration ingest.yml not found" in response.json()["detail"]


@pytest.mark.anyio
@patch("src.services.ingestion_service.IngestionService.ingest_project")
async def test_ingest_pipeline_failure(mock_ingest_project) -> None:
    """Verifies that a pipeline error triggers an HTTP 500 error."""
    mock_ingest_project.side_effect = Exception("Database insertion failed")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/ingest", json={"project_name": "test-project"})
        assert response.status_code == 500
        assert "Database insertion failed" in response.json()["detail"]


@pytest.mark.anyio
@patch("src.services.ingestion_service.fetch_github_repository")
@patch("src.services.ingestion_service.load_manual_documents")
@patch("src.services.ingestion_service.embed_chunks")
@patch("src.services.ingestion_service.Path.exists")
async def test_ingest_repeated_success_no_duplicates(
    mock_exists, mock_embed, mock_manual, mock_github
) -> None:
    """
    Integration test: Runs /ingest twice for the same project.
    Verifies that the second run completes successfully and does not duplicate chunks in the database.
    """
    if not await is_db_available():
        pytest.skip("PostgreSQL database is not running or unreachable.")

    # 1. Mock external pipeline dependencies
    mock_exists.return_value = True  # Pretend ingest.yml exists

    # Return 1 dummy GitHub document and 1 dummy manual document
    github_doc = Document(
        content="This is GitHub content for the project.",
        project="test-project",
        layer="design",
        source_type="github",
        source_file="github_doc.md",
        metadata={"source": "github"}
    )
    manual_doc = Document(
        content="This is manual identity content.",
        project="__global__",
        layer="identity",
        source_type="manual",
        source_file="manual_doc.md",
        metadata={"source": "manual"}
    )

    mock_github.return_value = [github_doc]
    mock_manual.return_value = [manual_doc]

    # Return dummy 1536-dimensional embeddings for chunks
    # Chunker creates 1 chunk per document for short text
    dummy_embeddings = [
        [0.1] * 1536,  # Chunk 1 (github)
        [0.2] * 1536   # Chunk 2 (manual)
    ]
    mock_embed.return_value = dummy_embeddings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First Ingestion Run
        resp1 = await client.post("/ingest", json={"project_name": "test-project"})
        assert resp1.status_code == 200
        data1 = resp1.json()["summary"]
        assert data1["status"] == "success"
        assert data1["documents_processed"] == 2
        assert data1["chunks_created"] == 2
        assert data1["embeddings_generated"] == 2

        # Verify the database has the expected chunks
        initial_chunks = await count_chunks()
        assert initial_chunks >= 2

        # Second Ingestion Run (Repeated Ingestion)
        resp2 = await client.post("/ingest", json={"project_name": "test-project"})
        assert resp2.status_code == 200
        data2 = resp2.json()["summary"]
        assert data2["status"] == "success"
        assert data2["documents_processed"] == 2
        assert data2["chunks_created"] == 2
        assert data2["embeddings_generated"] == 2

        # Verify database chunk count is unchanged (no duplicates created due to clean re-indexing)
        final_chunks = await count_chunks()
        assert final_chunks == initial_chunks
