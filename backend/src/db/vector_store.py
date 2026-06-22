"""
DESIGN DECISION:
This module manages database CRUD operations for document chunks, leveraging `asyncpg`
for performance. It implements bulk upserts (`executemany`) and similarity search
using pgvector's cosine distance operator (`<=>`).

Why Upsert on (project, source_file, chunk_index):
  By defining a unique constraint on these three fields, we make the ingestion pipeline
  idempotent. Running the pipeline multiple times for the same files will update the
  content/embeddings rather than creating duplicates.
  
Why Cosine Distance Similarity search:
  The `<=>` operator computes cosine distance (1 - cosine similarity) in a single instruction.
  Ordering by `<=>` and taking the top results returns the most semantically relevant chunks.
"""

import logging
from typing import List, Optional, Dict, Any
from src.db.core import get_db_pool
from src.ingestion.chunker import DocumentChunk

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class DatabaseError(Exception):
    """Raised when a database operation fails."""
    pass


# ---------------------------------------------------------------------------
# Vector Store Operations
# ---------------------------------------------------------------------------

async def upsert_document_chunks(
    project: str,
    layer: int,
    source_file: str,
    chunks: List[DocumentChunk],
    embeddings: List[List[float]]
) -> None:
    """
    Saves a batch of document chunks and their corresponding embeddings into the database.
    If a chunk with the same project, source_file, and chunk_index already exists,
    it updates the fields in-place (idempotent ingestion).
    
    Why: `executemany` runs the batch inside a single database transaction,
    offering maximum throughput.
    """
    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks and embeddings must match.")

    if not chunks:
        return

    # Prepare data tuple for bulk execution
    data = [
        (
            project,
            int(layer),
            source_file,
            chunk.heading,
            chunk.chunk_index,
            chunk.content,
            embeddings[i]
        )
        for i, chunk in enumerate(chunks)
    ]

    query = """
        INSERT INTO document_chunks (
            project, layer, source_file, heading, chunk_index, content, embedding
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (project, source_file, chunk_index) DO UPDATE
        SET heading = EXCLUDED.heading,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            ingested_at = CURRENT_TIMESTAMP;
    """

    delete_orphans_query = """
        DELETE FROM document_chunks
        WHERE project = $1 AND source_file = $2 AND chunk_index >= $3;
    """

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # We run both operations inside a transaction to guarantee atomicity.
            async with conn.transaction():
                await conn.executemany(query, data)
                await conn.execute(delete_orphans_query, project, source_file, len(chunks))
        logger.info(f"Successfully upserted {len(chunks)} chunks and removed orphans for {project} ({source_file})")
    except Exception as e:
        logger.error(f"Failed to upsert document chunks for project {project}, file {source_file}: {e}")
        raise DatabaseError(f"Database upsert failed: {e}") from e


async def search_similar_chunks(
    query_embedding: List[float],
    limit: int = 5,
    project_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches the vector store for the closest chunks to the query embedding using cosine similarity.
    Optionally filters chunks by project.
    
    Why: Cosine distance (<=>) is mapped to cosine similarity (1 - distance) for human-readable scoring.
    """
    # SQL query uses '<=>' for cosine distance. Similarity = 1 - distance.
    query = """
        SELECT id, project, layer, source_file, heading, chunk_index, content,
               1 - (embedding <=> $1) AS similarity
        FROM document_chunks
        WHERE ($3::text IS NULL OR project = $3)
        ORDER BY embedding <=> $1
        LIMIT $2;
    """

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, query_embedding, limit, project_filter)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to search similar chunks: {e}")
        raise DatabaseError(f"Similarity search failed: {e}") from e


async def delete_project_chunks(project: str) -> None:
    """
    Deletes all chunks associated with a specific project.
    Useful for full re-indexing or manual pruning.
    """
    query = "DELETE FROM document_chunks WHERE project = $1;"
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(query, project)
        logger.info(f"Deleted all chunks for project {project}")
    except Exception as e:
        logger.error(f"Failed to delete chunks for project {project}: {e}")
        raise DatabaseError(f"Deletion failed: {e}") from e
