"""
WHY THIS WAS CHOSEN:
This module initializes the FastAPI application. It registers CORS middleware to support
frontend interactions and mounts the chat router. Placing initialization in src/main.py
allows it to be imported and run easily by ASGI servers (like uvicorn).

We added a modern FastAPI lifespan handler to manage resources (like the DB connection pool)
and run diagnostic checks on external dependencies (PostgreSQL, Redis) at startup.
CORS origins are dynamically set based on the environment to ensure security in production.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.api.routes import chat, portfolio, admin
from src.db.core import get_db_pool, close_db_pool
from src.cache.factory import create_cache_from_settings
from src.cache.redis import RedisCache

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown tasks.
    Performs connection validation for PostgreSQL and Redis and logs configuration details.
    """
    logger.info("=== Starting Application ===")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Embedding Provider: {settings.EMBEDDING_PROVIDER}")
    logger.info(f"LLM Provider (Generator): {settings.GENERATOR_PROVIDER}")

    # 1. Database Connection Check
    db_connected = False
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        db_connected = True
        logger.info("Database connection: CONNECTED")
    except Exception as e:
        logger.error(f"Database connection: FAILED - {e}")
        # Fail fast in production if the database is unreachable
        if settings.ENVIRONMENT == "production":
            raise RuntimeError(f"Database is required but connection failed: {e}") from e

    # 2. Redis Connection Check
    redis_connected = False
    try:
        cache = create_cache_from_settings()
        if isinstance(cache, RedisCache):
            client = await cache._get_client()
            await client.ping()
            redis_connected = True
            logger.info("Redis connection: CONNECTED")
        else:
            logger.info("Redis connection: N/A (Using non-Redis cache)")
    except Exception as e:
        logger.error(f"Redis connection: FAILED - {e}")
        # In production, we don't necessarily fail fast for cache, but we log it.

    yield

    # Cleanup resources on shutdown
    logger.info("=== Shutting Down Application ===")
    await close_db_pool()

app = FastAPI(
    title="RAG-Powered Developer Portfolio Backend",
    description="API for the RAG-powered developer portfolio chatbot.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
if settings.ENVIRONMENT == "production":
    origins = settings.ALLOWED_ORIGINS
    logger.info(f"CORS origins configured for production: {origins}")
else:
    origins = ["*"]
    logger.info("CORS origins configured for development: ['*']")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat.router)
app.include_router(portfolio.router)
app.include_router(admin.router)


@app.get("/health")
async def health_check():
    """Simple healthcheck endpoint."""
    return {"status": "healthy"}

