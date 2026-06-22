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
    creating the `document_chunks` table, and establishing the HNSW index.
    
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
        logger.info("Creating document_chunks table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project VARCHAR(255) NOT NULL,
                layer INTEGER NOT NULL,
                source_file VARCHAR(1024) NOT NULL,
                heading VARCHAR(1024),
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536) NOT NULL,
                ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_project_file_chunk UNIQUE (project, source_file, chunk_index)
            );
        """)
        
        # Create HNSW index using cosine operators
        logger.info("Creating HNSW index on document_chunks.embedding...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
            ON document_chunks USING hnsw (embedding vector_cosine_ops);
        """)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise RuntimeError(f"Database initialization failed: {e}") from e
    finally:
        await conn.close()
