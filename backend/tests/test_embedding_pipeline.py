"""
DESIGN DECISION:
This module contains end-to-end pipeline tests for the chunking, embedding, and storage steps.
It validates the full ingestion flow:
  1. Reading Markdown files (resume.md, decisions.md)
  2. Creating Document objects
  3. Running the layer-aware chunker
  4. Generating 1536-dimensional embeddings (mocked by default, or live if configured)
  5. Saving results to PostgreSQL via pgvector using the new chunks table
  6. Performing a similarity search query and verifying metadata.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
import asyncpg
from src.config import settings
from src.db.init_db import init_db
from src.db.core import close_db_pool
from src.models.document import Document
from src.chunking.chunker import chunk_document
from src.embedding.azure_openai_embedder import embed_chunks
from src.vectorstore.pgvector_store import (
    upsert_chunks,
    similarity_search,
    delete_project
)

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
    await delete_project("pipeline-test-resume")
    await delete_project("pipeline-test-decisions")

    try:
        # 3. Read and chunk local knowledge files
        resume_path = WORKSPACE_ROOT / "knowledge" / "resume.md"
        decisions_path = WORKSPACE_ROOT / "knowledge" / "talentforge" / "decisions.md"
        
        assert resume_path.exists(), f"Missing test file: {resume_path}"
        assert decisions_path.exists(), f"Missing test file: {decisions_path}"
        
        resume_text = resume_path.read_text(encoding="utf-8")
        decisions_text = decisions_path.read_text(encoding="utf-8")
        
        resume_doc = Document(
            content=resume_text,
            project="pipeline-test-resume",
            layer="identity",
            source_type="manual",
            source_file="resume.md"
        )
        decisions_doc = Document(
            content=decisions_text,
            project="pipeline-test-decisions",
            layer="design",
            source_type="manual",
            source_file="decisions.md"
        )
        
        resume_chunks = chunk_document(resume_doc)
        decisions_chunks = chunk_document(decisions_doc)
        
        assert len(resume_chunks) > 0
        assert len(decisions_chunks) > 0
        
        # 4. Generate mocked embeddings
        mock_embedding = [0.1] * 1536
        resume_embeddings = [mock_embedding for _ in resume_chunks]
        decisions_embeddings = [mock_embedding for _ in decisions_chunks]
        
        # 5. Upsert chunks into database
        await upsert_chunks(
            chunks=resume_chunks,
            embeddings=resume_embeddings
        )
        
        await upsert_chunks(
            chunks=decisions_chunks,
            embeddings=decisions_embeddings
        )
        
        # 6. Retrieve similar chunks and verify
        # Search specifically for a query within our resume project
        results = await similarity_search(mock_embedding, limit=5, project_filter="pipeline-test-resume")
        assert len(results) > 0
        assert all(r["project"] == "pipeline-test-resume" for r in results)
        assert results[0]["source_file"] == "resume.md"
        
        # Search within decisions project
        results_decisions = await similarity_search(mock_embedding, limit=5, project_filter="pipeline-test-decisions")
        assert len(results_decisions) > 0
        assert all(r["project"] == "pipeline-test-decisions" for r in results_decisions)
        assert results_decisions[0]["source_file"] == "decisions.md"
        
    finally:
        # Cleanup
        await delete_project("pipeline-test-resume")
        await delete_project("pipeline-test-decisions")
        await close_db_pool()


# ---------------------------------------------------------------------------
# Manual Integration Test (Runs only when explicitly enabled)
# ---------------------------------------------------------------------------

run_live_integration = pytest.mark.skipif(
    os.environ.get("RUN_LIVE_INTEGRATION", "false").lower() != "true",
    reason="RUN_LIVE_INTEGRATION is not set to true. Skipping live API integration test."
)


@run_live_integration
async def test_pipeline_end_to_end_live() -> None:
    """
    Runs the pipeline against the real Azure OpenAI endpoint and PostgreSQL database.
    This creates actual embeddings for resume.md and decisions.md and upserts them.
    """
    if not await is_db_available():
        pytest.fail("PostgreSQL database is unreachable.")

    assert settings.AZURE_OPENAI_API_KEY, "Azure OpenAI API key is missing."
    assert settings.AZURE_OPENAI_ENDPOINT, "Azure OpenAI endpoint is missing."

    print("\n--- Starting Live Ingestion Pipeline Integration Test ---")
    
    # 1. Initialize schema
    await init_db()
    
    # 2. Clean up test projects
    await delete_project("live-test-resume")
    await delete_project("live-test-decisions")

    try:
        # 3. Read raw files
        resume_path = WORKSPACE_ROOT / "knowledge" / "resume.md"
        decisions_path = WORKSPACE_ROOT / "knowledge" / "talentforge" / "decisions.md"
        
        resume_text = resume_path.read_text(encoding="utf-8")
        decisions_text = decisions_path.read_text(encoding="utf-8")
        
        # 4. Chunk files
        resume_doc = Document(
            content=resume_text,
            project="live-test-resume",
            layer="identity",
            source_type="manual",
            source_file="resume.md"
        )
        decisions_doc = Document(
            content=decisions_text,
            project="live-test-decisions",
            layer="design",
            source_type="manual",
            source_file="decisions.md"
        )
        
        resume_chunks = chunk_document(resume_doc)
        decisions_chunks = chunk_document(decisions_doc)
        
        print(f"Produced {len(resume_chunks)} chunks for resume.md")
        print(f"Produced {len(decisions_chunks)} chunks for decisions.md")
        
        # 5. Embed chunks using real Azure OpenAI API
        print("Calling Azure OpenAI to generate embeddings...")
        resume_embeddings = await embed_chunks(resume_chunks)
        decisions_embeddings = await embed_chunks(decisions_chunks)
        
        assert len(resume_embeddings) == len(resume_chunks)
        assert len(decisions_embeddings) == len(decisions_chunks)
        assert len(resume_embeddings[0]) == 1536, "Embedding dimension must be 1536"
        print("Generated embeddings successfully.")
        
        # 6. Upsert into database
        print("Saving to PostgreSQL...")
        await upsert_chunks(resume_chunks, resume_embeddings)
        await upsert_chunks(decisions_chunks, decisions_embeddings)
        print("Saved to PostgreSQL successfully.")
        
        # 7. Query and search
        print("Running similarity search queries...")
        # Embed a natural language query using the API
        query_text = "What is Ajay's experience with Kubernetes?"
        # Using the underlying embedder's single query wrapper for convenience
        from src.ingestion.embedder import embed_query
        query_embedding = await embed_query(query_text)
        
        results = await similarity_search(query_embedding, limit=3, project_filter="live-test-resume")
        print(f"\nQuery: '{query_text}'")
        print("Top matches:")
        for r in results:
            heading = r['metadata'].get('heading', 'No Heading')
            print(f"- [Score: {r['similarity']:.4f}] heading: '{heading}' (file: {r['source_file']})")
        
        assert len(results) > 0
        assert results[0]["similarity"] > 0.0, "Similarity score should be positive"
        
    except Exception as e:
        print(f"Error during live test: {e}")
        raise
    finally:
        # Cleanup
        await delete_project("live-test-resume")
        await delete_project("live-test-decisions")
        await close_db_pool()
        print("Live integration test cleanup complete.")
