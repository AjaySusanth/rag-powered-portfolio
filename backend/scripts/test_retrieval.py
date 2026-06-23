"""
DESIGN DECISION:
This script orchestrates the full end-to-end RAG retrieval loop. It enables testing the
entire pipeline (User Query -> Embedding -> pgvector HNSW Retrieval -> Gemini Generation)
via a command-line interface.

Why this script:
  To avoid coupling retrieval validation with the FastAPI server or streaming architectures
  (which are Block 3 requirements), this CLI script serves as a lightweight, end-to-end
  integration test bench. It handles on-demand database ingestion of resume.md and decisions.md
  to ensure we have actual grounded data to query.
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import List

# Add backend directory to sys.path to resolve src imports
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.config import settings
from src.db.init_db import init_db
from src.db.core import close_db_pool
from src.db.vector_store import (
    upsert_document_chunks,
    search_similar_chunks,
    delete_project_chunks
)
from src.ingestion.chunker import chunk_text, DocumentLayer
from src.ingestion.embedder import embed_texts, embed_query
from src.llm.gemini_client import generate_answer, LLMError


async def ingest_test_documents(force: bool = False) -> None:
    """
    Ingests resume.md and decisions.md into the local database if they don't already exist.
    """
    print("[Ingestion] Checking database status...")
    await init_db()

    # Check if we already have chunks for portfolio or reservation-system
    existing_resume = await search_similar_chunks([0.0] * 1536, limit=1, project_filter="portfolio")
    existing_decisions = await search_similar_chunks([0.0] * 1536, limit=1, project_filter="reservation-system")

    if existing_resume and existing_decisions and not force:
        print("[Ingestion] Test documents already present in database. Skipping ingestion.")
        return

    print("[Ingestion] Ingesting source files into database...")
    workspace_root = BACKEND_DIR.parent
    resume_path = workspace_root / "knowledge" / "resume.md"
    decisions_path = workspace_root / "knowledge" / "reservation-system" / "decisions.md"

    if not resume_path.exists() or not decisions_path.exists():
        print(f"[Error] Required knowledge files not found in workspace:\n  - {resume_path}\n  - {decisions_path}")
        sys.exit(1)

    # 1. Ingest Resume
    print("[Ingestion] Processing resume.md...")
    resume_text = resume_path.read_text(encoding="utf-8")
    resume_chunks = chunk_text(resume_text, DocumentLayer.IDENTITY)
    resume_embeddings = await embed_texts([c.content for c in resume_chunks])
    await upsert_document_chunks(
        project="portfolio",
        layer=DocumentLayer.IDENTITY,
        source_file="resume.md",
        chunks=resume_chunks,
        embeddings=resume_embeddings
    )
    print(f"[Ingestion] Saved {len(resume_chunks)} chunks for portfolio (resume.md)")

    # 2. Ingest Decisions
    print("[Ingestion] Processing decisions.md...")
    decisions_text = decisions_path.read_text(encoding="utf-8")
    decisions_chunks = chunk_text(decisions_text, DocumentLayer.DESIGN)
    decisions_embeddings = await embed_texts([c.content for c in decisions_chunks])
    await upsert_document_chunks(
        project="reservation-system",
        layer=DocumentLayer.DESIGN,
        source_file="decisions.md",
        chunks=decisions_chunks,
        embeddings=decisions_embeddings
    )
    print(f"[Ingestion] Saved {len(decisions_chunks)} chunks for reservation-system (decisions.md)")


async def run_rag_pipeline(query: str, project_filter: str = None) -> None:
    """
    Executes the full RAG pipeline:
    Query -> Embed -> pgvector search -> prompt template -> Gemini generation
    """
    print(f"\n[RAG Pipeline] Processing query: '{query}'")
    if project_filter:
        print(f"[RAG Pipeline] Scoping search to project: '{project_filter}'")

    # 1. Embed the query
    print("[RAG Pipeline] Generating query embedding...")
    query_vector = await embed_query(query)

    # 2. Retrieve similar chunks
    print("[RAG Pipeline] Searching pgvector database...")
    retrieved_chunks = await search_similar_chunks(
        query_embedding=query_vector,
        limit=4,
        project_filter=project_filter
    )

    print(f"[RAG Pipeline] Retrieved {len(retrieved_chunks)} relevant context chunks:")
    for i, chunk in enumerate(retrieved_chunks):
        score = chunk.get("similarity", 0.0)
        source = chunk.get("source_file", "unknown")
        heading = chunk.get("heading") or "No Heading"
        print(f"  {i+1}. [Similarity: {score:.4f}] {source} > {heading}")

    # 3. Generate answer
    print(f"[RAG Pipeline] Contacting {settings.GEMINI_MODEL_NAME}...")
    try:
        answer = await generate_answer(query, retrieved_chunks)
        print("\n==================== GEMINI RESPONSE ====================")
        print(answer)
        print("=========================================================")
    except LLMError as e:
        print(f"[Error] LLM generation failed: {e}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test RAG retrieval pipeline end-to-end.")
    parser.add_argument("query", type=str, nargs="?", help="The natural language question to ask.")
    parser.add_argument("--force-ingest", action="store_true", help="Force re-ingestion of source markdown files.")
    parser.add_argument("--project", type=str, default=None, help="Scope retrieval to a specific project filter.")
    args = parser.parse_args()

    # Verify settings are present
    if not settings.AZURE_OPENAI_API_KEY:
        print("[Error] AZURE_OPENAI_KEY / AZURE_OPENAI_API_KEY is not configured in .env")
        sys.exit(1)
    if not settings.GEMINI_API_KEY:
        print("[Error] GEMINI_API_KEY is not configured in .env")
        sys.exit(1)

    try:
        # Step 1: Ensure database contains test content
        await ingest_test_documents(force=args.force_ingest)

        # Step 2: Prompt for input if no query passed via args
        query = args.query
        if not query:
            default_query = "What is Ajay's experience with Kubernetes?"
            print(f"\nNo query provided. Using default: '{default_query}'")
            query = default_query

        # Step 3: Run RAG Pipeline
        await run_rag_pipeline(query, project_filter=args.project)
        
    finally:
        # Step 4: Ensure pool is closed cleanly
        await close_db_pool()


if __name__ == "__main__":
    # Ensure Windows event loop policy plays nice with asyncpg/anyio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
