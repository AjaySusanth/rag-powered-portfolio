"""
WHY THIS WAS CHOSEN:
We define a provider-agnostic abstract base class (BaseQueryRewriter) to decouple our
higher-level workflows (like evaluation, API handlers, or chat pipelines) from specific
LLM API client implementations. This makes it easy to swap rewriter models or use a mock
rewriter for deterministic testing.
"""

from abc import ABC, abstractmethod
from typing import Optional

from src.models.rewrite_result import RewriteResult


class BaseQueryRewriter(ABC):
    """
    Abstract interface for query rewriting.
    All query rewriter implementations must inherit from this and implement the rewrite method.
    """

    @abstractmethod
    async def rewrite(self, query: str, project: Optional[str] = None) -> RewriteResult:
        """
        Asynchronously rewrites a user query to optimize it for vector and keyword search.

        Args:
            query: The original raw user query.
            project: Optional detected project canonical ID to provide context.

        Returns:
            A RewriteResult containing the rewritten query string, whether it was rewritten,
            and an explanation of the decision.
        """
        pass
