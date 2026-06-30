"""
WHY THIS WAS CHOSEN:
This module implements the Factory Pattern to construct query rewriter instances at runtime.
By referencing settings (REWRITER_PROVIDER and MODEL_REWRITER), we can easily switch between
the production Gemini query rewriter and a Mock implementation for deterministic testing,
without coupling client code directly to LLM providers.
"""

from src.config import settings
from src.retrieval.rewriters.base import BaseQueryRewriter
from src.retrieval.rewriters.gemini import GeminiQueryRewriter
from src.retrieval.rewriters.mock import MockQueryRewriter

def create_rewriter_from_settings() -> BaseQueryRewriter:
    """
    Creates and returns a BaseQueryRewriter instance based on application settings.
    """
    provider = settings.REWRITER_PROVIDER.lower()

    if provider == "gemini":
        return GeminiQueryRewriter(model_name=settings.MODEL_REWRITER)
    elif provider == "mock":
        return MockQueryRewriter()
    else:
        raise ValueError(f"Unknown REWRITER_PROVIDER: {settings.REWRITER_PROVIDER}")
