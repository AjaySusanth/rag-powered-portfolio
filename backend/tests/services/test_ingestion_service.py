"""
DESIGN DECISION:
This module contains tests for the IngestionService, focusing on the separation of
the __global__ identity namespace from project namespaces.
We test:
1. Ingestion of the global namespace (`__global__`).
2. Ingestion of a project namespace (`talentforge`).
3. Repeated mixed ingestion (__global__ -> talentforge -> classsync -> __global__)
   to verify namespace isolation, ensuring no global identity files are deleted
   during project ingestion, and no duplicates are created during repeated runs.
We mock external services (GitHub API, Azure OpenAI Embeddings) to ensure the
tests remain fast, deterministic, and runnable offline.
"""

from unittest.mock import patch

import asyncpg
import pytest

from src.config import GLOBAL_PROJECT_NAME, settings
from src.db.core import close_db_pool, get_db_pool
from src.db.init_db import init_db
from src.models.document import Document
from src.services.ingestion_service import IngestionService
from src.vectorstore.pgvector_store import delete_project


async def is_db_available() -> bool:
    """Checks if the PostgreSQL database is reachable."""
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL, timeout=2.0)
        await conn.close()
        return True
    except Exception:
        return False


async def get_project_chunk_count(project_name: str) -> int:
    """Helper to count chunks for a specific project in the database."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT count(*) FROM chunks WHERE project = $1",
            project_name
        )
        return row["count"] if row else 0


@pytest.fixture(autouse=True)
async def cleanup_database() -> None:
    """Ensures test namespaces are cleaned up before and after tests."""
    if await is_db_available():
        await init_db()
        await delete_project(GLOBAL_PROJECT_NAME)
        await delete_project("talentforge")
        await delete_project("classsync")
    yield
    if await is_db_available():
        await delete_project(GLOBAL_PROJECT_NAME)
        await delete_project("talentforge")
        await delete_project("classsync")
        await close_db_pool()


@pytest.mark.anyio
@patch("src.services.ingestion_service.embed_chunks")
@patch("src.services.ingestion_service.load_manual_documents")
async def test_ingest_global(mock_load_manual, mock_embed_chunks) -> None:
    """
    Verifies that ingesting the __global__ namespace runs successfully,
    loads global documents, and indexes them in the database.
    """
    if not await is_db_available():
        pytest.skip("PostgreSQL database is unreachable.")

    # Mock manual identity documents
    mock_load_manual.return_value = [
        Document(
            content="# About Me\nAjay is a DevOps engineer.",
            project=GLOBAL_PROJECT_NAME,
            layer="identity",
            source_type="manual",
            source_file="about-me.md",
            metadata={"source": "manual"}
        )
    ]

    # Mock embedding response
    mock_embed_chunks.return_value = [[0.1] * 1536]

    summary = await IngestionService.ingest_project(GLOBAL_PROJECT_NAME)
    assert summary.status == "success"
    assert summary.project_name == GLOBAL_PROJECT_NAME
    assert summary.documents_processed == 1
    assert summary.chunks_created == 1

    count = await get_project_chunk_count(GLOBAL_PROJECT_NAME)
    assert count == 1


@pytest.mark.anyio
@patch("src.services.ingestion_service.fetch_github_repository")
@patch("src.services.ingestion_service.embed_chunks")
@patch("src.services.ingestion_service.load_manual_documents")
async def test_ingest_project(mock_load_manual, mock_embed_chunks, mock_fetch_github) -> None:
    """
    Verifies that ingesting a specific project (talentforge) only indexes
    its own namespace and does not index or touch global files.
    """
    if not await is_db_available():
        pytest.skip("PostgreSQL database is unreachable.")

    # Mock project manual documents (no global files loaded)
    mock_load_manual.return_value = [
        Document(
            content="# TalentForge Architecture\nThis is a backend design doc.",
            project="talentforge",
            layer="design",
            source_type="manual",
            source_file="talentforge/architecture.md",
            metadata={"source": "manual"}
        )
    ]

    # Mock project GitHub documents
    mock_fetch_github.return_value = [
        Document(
            content="def main(): pass",
            project="talentforge",
            layer="artifact",
            source_type="github",
            source_file="src/main.py",
            metadata={"source": "github"}
        )
    ]

    # Mock embedding response (2 chunks total)
    mock_embed_chunks.return_value = [[0.1] * 1536, [0.2] * 1536]

    summary = await IngestionService.ingest_project("talentforge")
    assert summary.status == "success"
    assert summary.project_name == "talentforge"
    assert summary.documents_processed == 2
    assert summary.chunks_created == 2

    # Verify project has chunks
    project_count = await get_project_chunk_count("talentforge")
    assert project_count == 2

    # Verify global namespace has no chunks
    global_count = await get_project_chunk_count(GLOBAL_PROJECT_NAME)
    assert global_count == 0


@pytest.mark.anyio
@patch("src.services.ingestion_service.fetch_github_repository")
@patch("src.services.ingestion_service.embed_chunks")
@patch("src.services.ingestion_service.load_manual_documents")
async def test_repeated_mixed_ingestion(mock_load_manual, mock_embed_chunks, mock_fetch_github) -> None:
    """
    Verifies repeated mixed ingestion flow (__global__ -> talentforge -> classsync -> __global__)
    to ensure:
    1. Project ingestion does not delete global identity chunks.
    2. Repeated ingestion of global or projects cleanly re-indexes them without creating duplicates.
    3. Namespace boundaries are strictly isolated.
    """
    if not await is_db_available():
        pytest.skip("PostgreSQL database is unreachable.")

    # Setup loading behaviors for different runs
    def load_manual_side_effect(proj_name, base_dir):
        if proj_name == GLOBAL_PROJECT_NAME:
            return [
                Document(
                    content="# About Me\nAjay is a DevOps engineer.",
                    project=GLOBAL_PROJECT_NAME,
                    layer="identity",
                    source_type="manual",
                    source_file="about-me.md",
                    metadata={"source": "manual"}
                )
            ]
        elif proj_name == "talentforge":
            return [
                Document(
                    content="# TalentForge Manual\nManual info.",
                    project="talentforge",
                    layer="design",
                    source_type="manual",
                    source_file="talentforge/architecture.md",
                    metadata={"source": "manual"}
                )
            ]
        elif proj_name == "classsync":
            return [
                Document(
                    content="# ClassSync Manual\nManual details.",
                    project="classsync",
                    layer="design",
                    source_type="manual",
                    source_file="classsync/architecture.md",
                    metadata={"source": "manual"}
                )
            ]
        return []

    mock_load_manual.side_effect = load_manual_side_effect

    def fetch_github_side_effect(yaml_path):
        if "talentforge" in yaml_path:
            return [
                Document(
                    content="talentforge code",
                    project="talentforge",
                    layer="artifact",
                    source_type="github",
                    source_file="main.py",
                    metadata={"source": "github"}
                )
            ]
        elif "classsync" in yaml_path:
            return [
                Document(
                    content="classsync code",
                    project="classsync",
                    layer="artifact",
                    source_type="github",
                    source_file="app.js",
                    metadata={"source": "github"}
                )
            ]
        return []

    mock_fetch_github.side_effect = fetch_github_side_effect

    def embed_side_effect(chunks):
        return [[0.5] * 1536 for _ in chunks]

    mock_embed_chunks.side_effect = embed_side_effect

    # 1. Ingest __global__
    summary = await IngestionService.ingest_project(GLOBAL_PROJECT_NAME)
    assert summary.status == "success"
    assert await get_project_chunk_count(GLOBAL_PROJECT_NAME) == 1
    assert await get_project_chunk_count("talentforge") == 0
    assert await get_project_chunk_count("classsync") == 0

    # 2. Ingest talentforge
    summary = await IngestionService.ingest_project("talentforge")
    assert summary.status == "success"
    # Verify global is preserved
    assert await get_project_chunk_count(GLOBAL_PROJECT_NAME) == 1
    assert await get_project_chunk_count("talentforge") == 2
    assert await get_project_chunk_count("classsync") == 0

    # 3. Ingest classsync
    summary = await IngestionService.ingest_project("classsync")
    assert summary.status == "success"
    # Verify global and talentforge are preserved
    assert await get_project_chunk_count(GLOBAL_PROJECT_NAME) == 1
    assert await get_project_chunk_count("talentforge") == 2
    assert await get_project_chunk_count("classsync") == 2

    # 4. Ingest __global__ again (re-indexing global namespace)
    summary = await IngestionService.ingest_project(GLOBAL_PROJECT_NAME)
    assert summary.status == "success"
    # Verify global count is still 1 (re-indexed, no duplication)
    assert await get_project_chunk_count(GLOBAL_PROJECT_NAME) == 1
    # Verify other projects remain intact
    assert await get_project_chunk_count("talentforge") == 2
    assert await get_project_chunk_count("classsync") == 2
