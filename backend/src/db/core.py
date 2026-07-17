"""
DESIGN DECISION:
This module establishes and manages the connection pool to the PostgreSQL database.
It uses `asyncpg` for asynchronous database interactions, aligning with the project's
I/O requirements.

Using a connection pool prevents the overhead of opening and closing connections
for every single query, which is crucial for maintaining sub-second RAG search latencies.
We register the pgvector type handler on every connection in the pool to allow passing
lists of floats directly as query arguments.
"""

import logging
from typing import Optional

import asyncpg
from pgvector.asyncpg import register_vector

from src.config import settings

logger = logging.getLogger(__name__)

# Global pool instance
_pool: Optional[asyncpg.Pool] = None


async def init_connection(conn: asyncpg.Connection) -> None:
    """
    Called when a new connection is established in the pool.
    Registers pgvector handlers so that Python lists can be mapped to pgvector columns natively.
    """
    await register_vector(conn)


async def get_db_pool() -> asyncpg.Pool:
    """
    Returns the active asyncpg database connection pool. Lazily instantiates
    the pool if it hasn't been created yet.
    """
    global _pool
    if _pool is None:
        try:
            logger.info("Initializing database connection pool...")
            _pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=2,
                max_size=10,
                timeout=30.0,
                init=init_connection,
            )
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {e}")
            raise RuntimeError(f"Database pool initialization failed: {e}") from e
    return _pool


async def close_db_pool() -> None:
    """
    Closes the active database connection pool.
    """
    global _pool
    if _pool is not None:
        logger.info("Closing database connection pool...")
        await _pool.close()
        _pool = None
