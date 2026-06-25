"""
DESIGN DECISION:
This script orchestrates the full end-to-end RAG retrieval loop. It enables testing the
entire pipeline (User Query -> Embedding -> pgvector HNSW Retrieval -> Gemini Generation)
via a command-line interface.

It has been updated to use the canonical Document, Chunk, Chunker, and pgvector_store
modules.
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add backend directory to sys.path to resolve src imports
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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
from src.ingestion.embedder import embed_query


# We stub LLM generation imports to be robust if google library is missing
try:
    from src.llm.gemini_client import generate_answer, LLMError
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


async def ingest_test_documents(force: bool = False) -> None:
    """
    Ingests resume.md and decisions.md into the local database if they don't already exist.
    """
    print("[Ingestion] Checking database status...")
    await init_db()

    # Check if we already have chunks for portfolio or talentforge
    existing_resume = await similarity_search([0.0] * 1536, limit=1, project_filter="portfolio")
    existing_decisions = await similarity_search([0.0] * 1536, limit=1, project_filter="talentforge")

    if existing_resume and existing_decisions and not force:
        print("[Ingestion] Test documents already present in database. Skipping ingestion.")
        return

    print("[Ingestion] Ingesting source files into database...")
    workspace_root = BACKEND_DIR.parent
    resume_path = workspace_root / "knowledge" / "resume.md"
    decisions_path = workspace_root / "knowledge" / "talentforge" / "decisions.md"

    if not resume_path.exists() or not decisions_path.exists():
        print(f"[Error] Required knowledge files not found in workspace:\n  - {resume_path}\n  - {decisions_path}")
        sys.exit(1)

    # 1. Ingest Resume
    print("[Ingestion] Processing resume.md...")
    resume_text = resume_path.read_text(encoding="utf-8")
    resume_doc = Document(
        content=resume_text,
        project="portfolio",
        layer="identity",
        source_type="manual",
        source_file="resume.md"
    )
    resume_chunks = chunk_document(resume_doc)
    resume_embeddings = await embed_chunks(resume_chunks)
    
    await delete_project("portfolio")
    await upsert_chunks(resume_chunks, resume_embeddings)
    print(f"[Ingestion] Saved {len(resume_chunks)} chunks for portfolio (resume.md)")

    # 2. Ingest Decisions
    print("[Ingestion] Processing decisions.md...")
    decisions_text = decisions_path.read_text(encoding="utf-8")
    decisions_doc = Document(
        content=decisions_text,
        project="talentforge",
        layer="design",
        source_type="manual",
        source_file="decisions.md"
    )
    decisions_chunks = chunk_document(decisions_doc)
    decisions_embeddings = await embed_chunks(decisions_chunks)
    
    await delete_project("talentforge")
    await upsert_chunks(decisions_chunks, decisions_embeddings)
    print(f"[Ingestion] Saved {len(decisions_chunks)} chunks for talentforge (decisions.md)")


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
    retrieved_chunks = await similarity_search(
        query_embedding=query_vector,
        limit=4,
        project_filter=project_filter
    )

    print(f"[RAG Pipeline] Retrieved {len(retrieved_chunks)} relevant context chunks:")
    for i, chunk in enumerate(retrieved_chunks):
        score = chunk.get("similarity", 0.0)
        source = chunk.get("source_file", "unknown")
        heading = chunk.get("metadata", {}).get("heading") or "No Heading"
        print(f"  {i+1}. [Similarity: {score:.4f}] {source} > {heading}")

    # 3. Generate answer
    if not HAS_GEMINI:
        print("[RAG Pipeline] Gemini LLM Client is not available (missing google-genai library). Skipping generation.")
        return

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
