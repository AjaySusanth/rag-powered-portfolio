"""
DESIGN DECISION:
This module defines the RetrievalResult model.
Returning a dedicated dataclass rather than a raw dictionary ensures type safety
and provides a stable interface. Future retrieval stages (like BM25, Hybrid Search,
RRF ranking, and Retrieval Graders) can operate on this model without breaking
the pipeline structure.
"""

from dataclasses import dataclass
from typing import Optional
from src.models.chunk import Chunk

@dataclass
class RetrievalResult:
    """
    Encapsulates a retrieved Chunk and its relevance score.
    The score is typically a cosine similarity metric (1 - cosine distance),
    where higher values indicate stronger semantic similarity to the query.
    For hybrid search (RRF), it holds the fused RRF score.
    """
    chunk: Chunk
    score: float
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
