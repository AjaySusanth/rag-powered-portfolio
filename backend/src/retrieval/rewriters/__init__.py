"""
WHY THIS WAS CHOSEN:
This module initializes the rewriters package, exposing the BaseQueryRewriter interface,
the GeminiQueryRewriter implementation, the MockQueryRewriter implementation, and the
factory creation function for clean package imports.
"""

from src.retrieval.rewriters.base import BaseQueryRewriter
from src.retrieval.rewriters.factory import create_rewriter_from_settings
from src.retrieval.rewriters.gemini import GeminiQueryRewriter
from src.retrieval.rewriters.mock import MockQueryRewriter

__all__ = [
    "BaseQueryRewriter",
    "GeminiQueryRewriter",
    "MockQueryRewriter",
    "create_rewriter_from_settings",
]
