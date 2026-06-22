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
    Generates 1536-dimensional embeddings for a list of text strings using Azure OpenAI.
    
    Why batch:
      Sending texts in batches (default: 100) avoids payload limits, respects rate limits,
      and reduces HTTP connection overhead by bundling requests.
      
    Concept — Embeddings:
      An embedding converts a text string into a high-dimensional vector of floats (1536 for text-embedding-3-small).
      Distance between these vectors (e.g. cosine distance) represents semantic similarity,
      allowing search queries to match documents with similar meaning even if they use different words.
    """
    if not texts:
        return []

    client = get_azure_client()
    embeddings: List[List[float]] = []

    # Clean inputs to avoid empty strings which can cause API errors
    cleaned_texts = [text if text.strip() else "[empty]" for text in texts]

    # Process in batches
    for i in range(0, len(cleaned_texts), batch_size):
        batch = cleaned_texts[i : i + batch_size]
        try:
            # Azure OpenAI uses the deployment name as the "model" parameter
            response = await client.embeddings.create(
                input=batch,
                model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT
            )
            # The API returns data objects containing the embedding vectors.
            # We sort them by index to guarantee ordering matches the input texts.
            sorted_data = sorted(response.data, key=lambda x: x.index)
            embeddings.extend([item.embedding for item in sorted_data])
        except Exception as e:
            logger.error(f"Failed to generate embeddings for batch {i//batch_size}: {e}")
            raise EmbeddingError(f"Azure OpenAI embedding generation failed: {e}") from e

    return embeddings
