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

from src.ingestion.github_fetcher import fetch_github_repository
from src.chunking.chunker import chunk_document
from src.embedding.azure_openai_embedder import embed_chunks
from src.db.init_db import init_db
from src.vectorstore.pgvector_store import upsert_chunks, delete_project, count_chunks


async def main() -> None:
    if len(sys.argv) < 2:
        print("Error: Missing project name argument.")
        print("Usage: python scripts/index_project.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1].strip().lower()
    yaml_path = PROJECT_ROOT / "knowledge" / project_name / "ingest.yml"

    if not yaml_path.exists():
        print(f"Error: ingest.yml not found at {yaml_path}")
        sys.exit(1)

    print(f"Project: {project_name}\n")

    # 1. Fetch documents
    try:
        documents = await fetch_github_repository(str(yaml_path))
    except Exception as e:
        print(f"Failed to fetch documents from GitHub: {e}")
        sys.exit(1)

    num_docs = len(documents)
    if num_docs == 0:
        print("No documents found to ingest.")
        sys.exit(0)

    # 2. Chunk documents
    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc))

    num_chunks = len(all_chunks)
    if num_chunks == 0:
        print("No chunks produced from documents.")
        sys.exit(0)

    # 3. Generate embeddings
    try:
        embeddings = await embed_chunks(all_chunks)
    except Exception as e:
        print(f"Failed to generate embeddings: {e}")
        sys.exit(1)

    num_embeddings = len(embeddings)

    # 4. Initialize Database
    try:
        await init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)

    # 5. Delete existing chunks for this project (clean re-index)
    try:
        await delete_project(project_name)
    except Exception as e:
        print(f"Failed to clear existing project chunks: {e}")
        sys.exit(1)

    # 6. Store in pgvector
    try:
        await upsert_chunks(all_chunks, embeddings)
    except Exception as e:
        print(f"Failed to store chunks in database: {e}")
        sys.exit(1)

    print(f"Documents: {num_docs}")
    print(f"Chunks: {num_chunks}")
    print(f"Embeddings Generated: {num_embeddings}")
    print(f"Vectors Stored: {num_chunks}")


if __name__ == "__main__":
    asyncio.run(main())
