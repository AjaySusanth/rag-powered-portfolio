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
