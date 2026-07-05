"""
WHY THIS WAS CHOSEN:
This module provides a MockQueryRewriter implementation. It allows unit tests
to specify deterministic mapping from input queries to RewriteResult outputs,
preventing the test suite from making real external network calls to Gemini.
"""

from typing import Dict, Optional

from src.models.rewrite_result import RewriteResult
from src.retrieval.rewriters.base import BaseQueryRewriter


class MockQueryRewriter(BaseQueryRewriter):
    """
    Mock query rewriter for unit tests.
    """
    def __init__(self, rewrites: Optional[Dict[str, RewriteResult]] = None):
        """
        Initializes the mock rewriter.

        Args:
            rewrites: Optional dictionary mapping input queries to their expected RewriteResult.
        """
        self.rewrites = rewrites or {}

    async def rewrite(self, query: str, project: Optional[str] = None) -> RewriteResult:
        """
        Returns a mock RewriteResult if the query is in the preconfigured dictionary,
        otherwise falls back to returning the query unchanged.
        """
        if query in self.rewrites:
            return self.rewrites[query]

        # Default fallback: return the original query as-is
        return RewriteResult(
            rewritten_query=query,
            rewritten=False,
            explanation="Mock rewriter: no preconfigured rule found. Query passed through unchanged."
        )
