"""
WHY THIS WAS CHOSEN:
This service orchestrates the ingestion pipeline, reusing all existing ingestion components
(GitHub fetcher, manual loader, chunker, embedder, database initializer, pgvector store, and BM25 indexer).
By wrapping this orchestration in a service class, both the command-line script (index_project.py)
and the administrative HTTP route (POST /ingest) can invoke the same logic without duplication.
"""

import time
from pathlib import Path
from typing import List

from src.config import PROJECT_ROOT
from src.ingestion.github_fetcher import fetch_github_repository
from src.ingestion.manual_loader import load_manual_documents
from src.chunking.chunker import chunk_document
from src.embedding.azure_openai_embedder import embed_chunks
from src.db.init_db import init_db
from src.vectorstore.pgvector_store import upsert_chunks, delete_project
from src.retrieval.bm25_retriever import index_instance
from src.api.schemas.admin import IngestSummary


class IngestionService:
    """
    Service responsible for orchestrating the document ingestion, chunking,
    embedding, database storage, and retrieval indexing pipeline.
    """

    @staticmethod
    async def ingest_project(project_name_raw: str) -> IngestSummary:
        """
        Triggers the full ingestion pipeline for the specified project.
        
        Args:
            project_name_raw: Raw name of the project to ingest.
            
        Returns:
            An IngestSummary containing statistics and errors (if any) about the run.
        """
        start_time = time.time()
        project_name = project_name_raw.strip().lower()
        yaml_path = PROJECT_ROOT / "knowledge" / project_name / "ingest.yml"
        knowledge_dir = PROJECT_ROOT / "knowledge"
        
        errors: List[str] = []

        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration ingest.yml not found at: {yaml_path}")

        # 1. Fetch documents from GitHub
        github_documents = await fetch_github_repository(str(yaml_path))

        # 2. Load manual documents
        manual_documents = load_manual_documents(project_name, knowledge_dir)

        # 3. Merge documents
        documents = github_documents + manual_documents
        num_docs = len(documents)
        if num_docs == 0:
            duration = time.time() - start_time
            return IngestSummary(
                status="success",
                project_name=project_name,
                documents_processed=0,
                chunks_created=0,
                embeddings_generated=0,
                duration_seconds=round(duration, 2),
                errors=["No documents found to ingest."]
            )

        # 4. Chunk documents
        all_chunks = []
        for doc in documents:
            try:
                chunks = chunk_document(doc)
                all_chunks.extend(chunks)
            except Exception as e:
                # Capture chunking failure as a partial failure / error
                errors.append(f"Failed to chunk document '{doc.metadata.get('source', 'unknown')}': {str(e)}")

        num_chunks = len(all_chunks)
        if num_chunks == 0:
            duration = time.time() - start_time
            return IngestSummary(
                status="success",
                project_name=project_name,
                documents_processed=num_docs,
                chunks_created=0,
                embeddings_generated=0,
                duration_seconds=round(duration, 2),
                errors=errors + ["No chunks were produced from documents."]
            )

        # 5. Generate embeddings
        embeddings = await embed_chunks(all_chunks)
        num_embeddings = len(embeddings)

        # 6. Initialize Database
        await init_db()

        # 7. Delete existing chunks (clean re-index)
        await delete_project(project_name)
        await delete_project("__global__")

        # 8. Store in pgvector
        await upsert_chunks(all_chunks, embeddings)

        # 9. Refresh BM25 Index in-memory
        await index_instance.refresh_index()

        duration = time.time() - start_time
        return IngestSummary(
            status="success",
            project_name=project_name,
            documents_processed=num_docs,
            chunks_created=num_chunks,
            embeddings_generated=num_embeddings,
            duration_seconds=round(duration, 2),
            errors=errors
        )
