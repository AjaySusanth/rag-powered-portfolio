"""
DESIGN DECISION:
This module initializes the database schema, including enabling the `pgvector` extension,
creating the table for document chunks, and provisioning the HNSW (Hierarchical Navigable Small World) index.

Why HNSW:
  HNSW is a graph-based index for approximate nearest neighbor search. It offers high search recall
  and sub-second query latency even with high-dimensional embeddings. Unlike IVFFlat, it requires
  no training phase and performs optimally even as data is incrementally added.

Why Cosine Similarity:
  Cosine similarity (mapped via `<=>` cosine distance in pgvector) evaluates the angle between
  vectors, measuring semantic similarity independent of document/chunk length.
"""

import logging

import asyncpg

from src.config import settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """
    Sets up the database by ensuring the vector extension is loaded,
    creating the `chunks` table, and establishing the HNSW index.

    Why: A separate standalone connection is used here to avoid bootstrapping issues
    with connection pooling (since pgvector type registration requires the extension
    to exist before the pool is initialized).
    """
    logger.info("Initializing database schema...")
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        # Enable pgvector extension
        logger.info("Enabling pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create table for chunks
        logger.info("Creating chunks table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                parent_document_id TEXT NOT NULL,
                project VARCHAR(255) NOT NULL,
                layer VARCHAR(50) NOT NULL,
                source_type VARCHAR(50) NOT NULL,
                source_file VARCHAR(1024) NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                token_count INTEGER NOT NULL,
                char_count INTEGER NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}',
                embedding vector(1536) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create HNSW index using cosine operators
        logger.info("Creating HNSW index on chunks.embedding...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON chunks USING hnsw (embedding vector_cosine_ops);
        """)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise RuntimeError(f"Database initialization failed: {e}") from e
    finally:
        await conn.close()

