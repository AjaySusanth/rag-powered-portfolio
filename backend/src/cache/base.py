"""
DESIGN DECISION:
This module defines the BaseCache interface for response caching.
It ensures that the ChatOrchestrator can interact with any cache implementation
(e.g., Redis, In-Memory, or Mock) without coupling to specific transport details.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from src.api.schemas.chat import Citation


class BaseCache(ABC):
    """
    Abstract base class for response caching.
    """

    @abstractmethod
    async def get_chat_response(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a cached response for the given query.
        Returns a dictionary containing 'answer' and 'citations' if found, else None.
        """
        pass

    @abstractmethod
    async def set_chat_response(self, query: str, answer: str, citations: List[Citation]) -> None:
        """
        Stores the synthesized answer and citations for a given query in the cache.
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Retrieves a cached embedding vector for the given text.
        """
        pass

    @abstractmethod
    async def set_embedding(self, text: str, embedding: List[float]) -> None:
        """
        Stores an embedding vector for the given text in the cache.
        """
        pass

    async def get_embeddings(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Retrieves cached embedding vectors for a list of texts in order.
        Default implementation calls get_embedding sequentially.
        """
        return [await self.get_embedding(t) for t in texts]

    async def set_embeddings(self, texts: List[str], embeddings: List[List[float]]) -> None:
        """
        Stores embedding vectors for a list of texts in the cache.
        Default implementation calls set_embedding sequentially.
        """
        for t, emb in zip(texts, embeddings):
            await self.set_embedding(t, emb)
