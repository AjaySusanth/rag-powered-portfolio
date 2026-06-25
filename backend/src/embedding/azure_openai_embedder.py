"""
DESIGN DECISION:
This module acts as a thin adapter between our canonical Chunk model and the
underlying Azure OpenAI embedding client.

It extracts the raw string content from a list of Chunk objects, generates
ordered 1536-dimensional embeddings by delegating to the existing embedder,
and returns them. It guarantees that chunks[i] corresponds exactly to embeddings[i].
"""

import logging
from typing import List
from src.models.chunk import Chunk
from src.ingestion.embedder import embed_texts

logger = logging.getLogger(__name__)


async def embed_chunks(chunks: List[Chunk], batch_size: int = 100) -> List[List[float]]:
    """
    Generates 1536-dimensional embeddings for a list of Chunk objects.
    
    Extracts text from each Chunk and passes it to the underlying Azure OpenAI embedder.
    The order of returned embeddings is guaranteed to match the input chunks list.
    """
    if not chunks:
        return []

    # Extract raw content from all chunks in order
    texts = [chunk.content for chunk in chunks]

    try:
        # Delegate to the existing batch-aware embedding function
        embeddings = await embed_texts(texts, batch_size=batch_size)
        
        # Guard check to ensure alignment was preserved
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Embedding count mismatch: generated {len(embeddings)} for {len(chunks)} chunks."
            )
            
        return embeddings
    except Exception as e:
        logger.error(f"Failed to generate embeddings for chunks batch: {e}")
        raise
