"""
DESIGN DECISION:
This module contains end-to-end pipeline tests for the chunking, embedding, and storage steps.
It validates the full ingestion flow:
  1. Reading Markdown files (resume.md, decisions.md)
  2. Running the heading-aware chunker
  3. Generating 1536-dimensional embeddings (mocked by default, or live if configured)
  4. Saving results to PostgreSQL via pgvector
  5. Performing a similarity search query and verifying metadata.

Why this file contains both mock and live paths:
  This matches our workflow. The mock test runs as part of the fast unit test suite,
  while the live integration test verifies real API communication (Azure OpenAI) and
  database integration, which can be run manually when a key is available.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
import asyncpg
from src.config import settings
from src.db.init_db import init_db
from src.db.core import close_db_pool
from src.db.vector_store import (
    upsert_document_chunks,
    search_similar_chunks,
    delete_project_chunks
)
from src.ingestion.chunker import chunk_text, DocumentLayer, DocumentChunk
from src.ingestion.embedder import embed_texts

WORKSPACE_ROOT = Path(__file__).parent.parent.parent

pytestmark = pytest.mark.anyio


# Helper function to check if local database is running
async def is_db_available() -> bool:
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL, timeout=2.0)
        await conn.close()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Mock End-to-End Test (Runs automatically)
# ---------------------------------------------------------------------------

async def test_pipeline_end_to_end_mocked() -> None:
    """
    Simulates the entire pipeline end-to-end using mocked Azure OpenAI embeddings.
    Ensures data flows from raw files to the database correctly.
    """
    if not await is_db_available():
        pytest.skip("PostgreSQL database is unreachable.")

    # 1. Initialize schema
    await init_db()
    
    # 2. Clean up past test runs
    await delete_project_chunks("pipeline-test-resume")
    await delete_project_chunks("pipeline-test-decisions")

    try:
        # 3. Read and chunk local knowledge files
        resume_path = WORKSPACE_ROOT / "knowledge" / "resume.md"
        decisions_path = WORKSPACE_ROOT / "knowledge" / "reservation-system" / "decisions.md"
        
        assert resume_path.exists(), f"Missing test file: {resume_path}"
        assert decisions_path.exists(), f"Missing test file: {decisions_path}"
        
        resume_text = resume_path.read_text(encoding="utf-8")
        decisions_text = decisions_path.read_text(encoding="utf-8")
        
        resume_chunks = chunk_text(resume_text, DocumentLayer.IDENTITY)
        decisions_chunks = chunk_text(decisions_text, DocumentLayer.DESIGN)
        
        assert len(resume_chunks) > 0
        assert len(decisions_chunks) > 0
        
        # 4. Generate mocked embeddings
        mock_embedding = [0.1] * 1536
        resume_embeddings = [mock_embedding for _ in resume_chunks]
        decisions_embeddings = [mock_embedding for _ in decisions_chunks]
        
        # 5. Upsert chunks into database
        await upsert_document_chunks(
            project="pipeline-test-resume",
            layer=DocumentLayer.IDENTITY,
            source_file="resume.md",
            chunks=resume_chunks,
            embeddings=resume_embeddings
        )
        
        await upsert_document_chunks(
            project="pipeline-test-decisions",
            layer=DocumentLayer.DESIGN,
            source_file="decisions.md",
            chunks=decisions_chunks,
            embeddings=decisions_embeddings
        )
        
        # 6. Retrieve similar chunks and verify
        # Search specifically for a query within our resume project
        results = await search_similar_chunks(mock_embedding, limit=5, project_filter="pipeline-test-resume")
        assert len(results) > 0
        assert all(r["project"] == "pipeline-test-resume" for r in results)
        assert results[0]["source_file"] == "resume.md"
        
        # Search within decisions project
        results_decisions = await search_similar_chunks(mock_embedding, limit=5, project_filter="pipeline-test-decisions")
        assert len(results_decisions) > 0
        assert all(r["project"] == "pipeline-test-decisions" for r in results_decisions)
        assert results_decisions[0]["source_file"] == "decisions.md"
        
    finally:
        # Cleanup
        await delete_project_chunks("pipeline-test-resume")
        await delete_project_chunks("pipeline-test-decisions")
        await close_db_pool()


# ---------------------------------------------------------------------------
# Manual Integration Test (Runs only when explicitly enabled)
# ---------------------------------------------------------------------------

# We skip this test unless the RUN_LIVE_INTEGRATION env var is set.
# This prevents test suites failing in environments without Azure OpenAI API credentials.
run_live_integration = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_INTEGRATION", "false").lower() != "true",
    reason="RUN_LIVE_INTEGRATION is not set to true. Skipping live API integration test."
)


@run_live_integration
async def test_pipeline_end_to_end_live() -> None:
    """
    Runs the pipeline against the real Azure OpenAI endpoint and PostgreSQL database.
    This creates actual embeddings for resume.md and decisions.md and upserts them.
    
    To run this test:
      Set the environment variable RUN_LIVE_INTEGRATION=true in the environment.
    """
    if not await is_db_available():
        pytest.fail("PostgreSQL database is unreachable.")

    assert settings.AZURE_OPENAI_API_KEY, "Azure OpenAI API key is missing."
    assert settings.AZURE_OPENAI_ENDPOINT, "Azure OpenAI endpoint is missing."

    print("\n--- Starting Live Ingestion Pipeline Integration Test ---")
    
    # 1. Initialize schema
    await init_db()
    
    # 2. Clean up test projects
    await delete_project_chunks("live-test-resume")
    await delete_project_chunks("live-test-decisions")

    try:
        # 3. Read raw files
        resume_path = WORKSPACE_ROOT / "knowledge" / "resume.md"
        decisions_path = WORKSPACE_ROOT / "knowledge" / "reservation-system" / "decisions.md"
        
        resume_text = resume_path.read_text(encoding="utf-8")
        decisions_text = decisions_path.read_text(encoding="utf-8")
        
        # 4. Chunk files
        resume_chunks = chunk_text(resume_text, DocumentLayer.IDENTITY)
        decisions_chunks = chunk_text(decisions_text, DocumentLayer.DESIGN)
        
        print(f"Produced {len(resume_chunks)} chunks for resume.md")
        print(f"Produced {len(decisions_chunks)} chunks for decisions.md")
        
        # 5. Embed chunks using real Azure OpenAI API
        print("Calling Azure OpenAI to generate embeddings...")
        resume_texts = [chunk.content for chunk in resume_chunks]
        decisions_texts = [chunk.content for chunk in decisions_chunks]
        
        resume_embeddings = await embed_texts(resume_texts)
        decisions_embeddings = await embed_texts(decisions_texts)
        
        assert len(resume_embeddings) == len(resume_chunks)
        assert len(decisions_embeddings) == len(decisions_chunks)
        assert len(resume_embeddings[0]) == 1536, "Embedding dimension must be 1536"
        print("Generated embeddings successfully.")
        
        # 6. Upsert into database
        print("Saving to PostgreSQL...")
        await upsert_document_chunks(
            project="live-test-resume",
            layer=DocumentLayer.IDENTITY,
            source_file="resume.md",
            chunks=resume_chunks,
            embeddings=resume_embeddings
        )
        
        await upsert_document_chunks(
            project="live-test-decisions",
            layer=DocumentLayer.DESIGN,
            source_file="decisions.md",
            chunks=decisions_chunks,
            embeddings=decisions_embeddings
        )
        print("Saved to PostgreSQL successfully.")
        
        # 7. Query and search
        print("Running similarity search queries...")
        # Embed a natural language query using the API
        query_text = "What is Ajay's experience with Kubernetes?"
        query_embeddings = await embed_texts([query_text])
        
        results = await search_similar_chunks(query_embeddings[0], limit=3, project_filter="live-test-resume")
        print(f"\nQuery: '{query_text}'")
        print("Top matches:")
        for r in results:
            print(f"- [Score: {r['similarity']:.4f}] heading: '{r['heading']}' (file: {r['source_file']})")
        
        assert len(results) > 0
        assert results[0]["similarity"] > 0.0, "Similarity score should be positive"
        
    finally:
        # Cleanup
        await delete_project_chunks("live-test-resume")
        await delete_project_chunks("live-test-decisions")
        await close_db_pool()
        print("Live integration test cleanup complete.")
