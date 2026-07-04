"""
DESIGN DECISION:
This script implements the RAG indexing pipeline.
Given a project name:
1. It loads the project's ingest.yml configuration.
2. It fetches all matched files from the GitHub repository via REST API.
3. It initializes the pgvector database schema if not already present.
4. It deletes previously ingested chunks for this project to start clean.
5. It processes all documents into layer-aware chunks.
6. It generates embeddings via Azure OpenAI.
7. It stores all chunks and embeddings in pgvector.
"""

import sys
import asyncio
from pathlib import Path

# Resolve workspace paths
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.services.ingestion_service import IngestionService


async def main() -> None:
    if len(sys.argv) < 2:
        print("Error: Missing project name argument.")
        print("Usage: python scripts/index_project.py <project_name>")
        print("Note: Use '__global__' as the project name to index root global identity files (resume.md, about-me.md, faq.md).")
        sys.exit(1)

    project_name = sys.argv[1].strip().lower()
    print(f"Project: {project_name}\n")
    print("Triggering ingestion pipeline...")

    try:
        summary = await IngestionService.ingest_project(project_name)
        print(f"\nIndexing complete:")
        print(f"Status: {summary.status}")
        print(f"Documents: {summary.documents_processed}")
        print(f"Chunks: {summary.chunks_created}")
        print(f"Embeddings Generated: {summary.embeddings_generated}")
        print(f"Vectors Stored: {summary.chunks_created}")
        print(f"Duration: {summary.duration_seconds}s")
        if summary.errors:
            print("\nWarnings/Errors:")
            for err in summary.errors:
                print(f"- {err}")
    except Exception as e:
        print(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())


