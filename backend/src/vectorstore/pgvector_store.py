"""
DESIGN DECISION:
This module manages database CRUD operations for the new canonical Chunk model,
leveraging `asyncpg` for high-performance async database access.

It supports:
1. upsert_chunks: Uses a PostgreSQL `INSERT ... ON CONFLICT (chunk_id) DO UPDATE`
   statement to ensure idempotent ingestion. We run this inside a transaction.
2. similarity_search: Uses pgvector's cosine distance operator `<=>` to find
   semantic matches, returning results sorted by similarity (1 - distance).
3. delete_project: Removes all chunks associated with a given project.
4. count_chunks: Returns the total number of chunks stored.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from src.db.core import get_db_pool
from src.models.chunk import Chunk

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised when a vector store database operation fails."""
    pass


async def upsert_chunks(
    chunks: List[Chunk],
    embeddings: List[List[float]]
) -> None:
    """
    Saves a batch of Chunk objects and their corresponding embeddings into the database.
    If a chunk with the same chunk_id already exists, it updates fields in-place.
    
    Why: ON CONFLICT (chunk_id) DO UPDATE is used because chunk_id is a deterministic hash
    of the source file and chunk index, making re-ingestion idempotent.
    """
    if len(chunks) != len(embeddings):
        raise ValueError("The number of chunks and embeddings must match.")

    if not chunks:
        return

    # Prepare data for bulk execution
    data = [
        (
            chunk.chunk_id,
            chunk.parent_document_id,
            chunk.project,
            chunk.layer,
            chunk.source_type,
            chunk.source_file,
            chunk.chunk_index,
            chunk.content,
            chunk.content_hash,
            chunk.token_count,
            chunk.char_count,
            json.dumps(chunk.metadata),
            embeddings[i]
        )
        for i, chunk in enumerate(chunks)
    ]

    query = """
        INSERT INTO chunks (
            chunk_id, parent_document_id, project, layer, source_type,
            source_file, chunk_index, content, content_hash, token_count,
            char_count, metadata, embedding
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::jsonb, $13)
        ON CONFLICT (chunk_id) DO UPDATE
        SET parent_document_id = EXCLUDED.parent_document_id,
            project = EXCLUDED.project,
            layer = EXCLUDED.layer,
            source_type = EXCLUDED.source_type,
            source_file = EXCLUDED.source_file,
            chunk_index = EXCLUDED.chunk_index,
            content = EXCLUDED.content,
            content_hash = EXCLUDED.content_hash,
            token_count = EXCLUDED.token_count,
            char_count = EXCLUDED.char_count,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding,
            created_at = CURRENT_TIMESTAMP;
    """

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(query, data)
        logger.info(f"Successfully upserted {len(chunks)} chunks into the database.")
    except Exception as e:
        logger.error(f"Failed to upsert chunks: {e}")
        raise DatabaseError(f"Database upsert failed: {e}") from e


async def similarity_search(
    query_embedding: List[float],
    limit: int = 5,
    project_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches the vector store for closest chunks to the query embedding using cosine similarity.
    Optionally filters by project.
    
    Why: Cosine distance (<=>) measures angular similarity. We return 1 - distance
    as the 'similarity' score.
    """
    query = """
        SELECT chunk_id, parent_document_id, project, layer, source_type,
               source_file, chunk_index, content, content_hash, token_count,
               char_count, metadata, 1 - (embedding <=> $1) AS similarity
        FROM chunks
        WHERE ($3::text IS NULL OR project = $3)
        ORDER BY embedding <=> $1
        LIMIT $2;
    """

    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, query_embedding, limit, project_filter)
            
            results = []
            for row in rows:
                row_dict = dict(row)
                # Parse metadata JSON back into a python dictionary
                if isinstance(row_dict["metadata"], str):
                    row_dict["metadata"] = json.loads(row_dict["metadata"])
                results.append(row_dict)
            return results
    except Exception as e:
        logger.error(f"Failed to search similar chunks: {e}")
        raise DatabaseError(f"Similarity search failed: {e}") from e


async def delete_project(project: str) -> None:
    """
    Deletes all chunks associated with a specific project.
    """
    query = "DELETE FROM chunks WHERE project = $1;"
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(query, project)
        logger.info(f"Deleted all chunks for project {project}")
    except Exception as e:
        logger.error(f"Failed to delete chunks for project {project}: {e}")
        raise DatabaseError(f"Deletion failed: {e}") from e


async def count_chunks() -> int:
    """
    Returns the total number of chunks stored in the database.
    """
    query = "SELECT COUNT(*) FROM chunks;"
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            val = await conn.fetchval(query)
            return int(val) if val is not None else 0
    except Exception as e:
        logger.error(f"Failed to count chunks: {e}")
        raise DatabaseError(f"Count failed: {e}") from e
