"""
DESIGN DECISION:
This module manages embedding generation using the Azure OpenAI Service.
It initializes the AsyncAzureOpenAI client using settings loaded from the environment,
cleans the endpoint URL to match the expected Azure SDK format, and implements
batching to optimize API calls and minimize network latency during bulk ingestion.

Why Azure OpenAI:
  Azure OpenAI is selected for cost-efficiency (billed against existing credits) and
  enterprise availability. The underlying model is 'text-embedding-3-small' (1536 dimensions),
  but requests are routed to a specific deployment name using the Azure SDK.
"""

import logging
from typing import List, Optional

from openai import AsyncAzureOpenAI

from src.cache.factory import create_cache_from_settings
from src.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class EmbeddingError(Exception):
    """
    Raised when embedding generation fails due to API errors, timeouts, or
    configuration issues.
    """

    pass


# ---------------------------------------------------------------------------
# Client Initialization
# ---------------------------------------------------------------------------

# Initialize the client lazily or at module import. We fetch settings at import.
# Note: AZURE_OPENAI_ENDPOINT is parsed and cleaned in settings (retains only scheme and netloc).
_client: Optional[AsyncAzureOpenAI] = None


def get_azure_client() -> AsyncAzureOpenAI:
    """
    Returns the AsyncAzureOpenAI client instance.

    Why: Lazy initialization ensures settings are fully loaded before client instantiation
    and allows for easier mocking/testing.
    """
    global _client
    if _client is None:
        if not settings.AZURE_OPENAI_API_KEY:
            raise EmbeddingError("Azure OpenAI API key is missing. Please set AZURE_OPENAI_KEY.")
        _client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
    return _client


# ---------------------------------------------------------------------------
# Embedding Logic
# ---------------------------------------------------------------------------


async def embed_texts(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """
    Generates 1536-dimensional embeddings for a list of text strings.

    Checks the Redis cache first. For cache misses, delegates to the Azure OpenAI client.
    Deduplicates identical strings within the same batch to avoid redundant API calls.
    """
    if not texts:
        return []

    # 1. Deduplicate texts in this batch while preserving order
    seen = set()
    unique_texts = []
    for text in texts:
        if text not in seen:
            seen.add(text)
            unique_texts.append(text)

    # 2. Check the Redis cache for unique texts using MGET bulk lookup
    cache = create_cache_from_settings()
    cached_embeddings = await cache.get_embeddings(unique_texts)

    # 3. Separate hits and misses
    miss_texts = []
    for text, cached_emb in zip(unique_texts, cached_embeddings):
        if cached_emb is None:
            miss_texts.append(text)

    # 4. Generate embeddings for cache misses
    new_embeddings = []
    if miss_texts:
        client = get_azure_client()
        # Clean inputs to avoid empty strings which can cause API errors
        cleaned_misses = [text if text.strip() else "[empty]" for text in miss_texts]

        # Process in batches
        for i in range(0, len(cleaned_misses), batch_size):
            batch = cleaned_misses[i : i + batch_size]
            try:
                # Azure OpenAI uses the deployment name as the "model" parameter
                response = await client.embeddings.create(
                    input=batch, model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
                )
                # Sort data by index to guarantee order matches the input
                sorted_data = sorted(response.data, key=lambda x: x.index)
                new_embeddings.extend([item.embedding for item in sorted_data])
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i // batch_size}: {e}")
                raise EmbeddingError(f"Azure OpenAI embedding generation failed: {e}") from e

        # 5. Store newly generated embeddings in the Redis cache
        if new_embeddings:
            await cache.set_embeddings(miss_texts, new_embeddings)

    # 6. Reconstruct the mapping dictionary from unique texts to final vectors
    lookup = {}
    new_emb_idx = 0
    for text, cached_emb in zip(unique_texts, cached_embeddings):
        if cached_emb is not None:
            lookup[text] = cached_emb
        else:
            lookup[text] = new_embeddings[new_emb_idx]
            new_emb_idx += 1

    # 7. Map back to the original list sequence (including any duplicate positions)
    return [lookup[text] for text in texts]


async def embed_query(text: str) -> List[float]:
    """
    Embeds a single query string and returns its 1536-dimensional vector.

    This is a thin wrapper around embed_texts() for the retrieval path.
    Keeping it separate from embed_texts() makes call sites readable:
    embed_texts() is for bulk ingestion; embed_query() is for a single
    user query at search time. The underlying client and config are shared.
    """
    results = await embed_texts([text])
    return results[0]
