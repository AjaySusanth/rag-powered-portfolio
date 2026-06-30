"""
WHY THIS WAS CHOSEN:
This module implements the Factory Pattern to construct grader instances at runtime.
By referencing settings (GRADER_PROVIDER and MODEL_GRADER), we can change the grading model
or swap providers completely (e.g. from Google Gemini to Azure OpenAI or a Mock) without
modifying the retrieval pipeline or evaluation suite.
"""

from src.config import settings
from src.llm.interfaces import BaseGrader
from src.llm.providers.gemini import GeminiGrader


def create_grader_from_settings() -> BaseGrader:
    """
    Creates and returns a BaseGrader instance based on application settings.
    """
    provider = settings.GRADER_PROVIDER.lower()

    if provider == "gemini":
        return GeminiGrader(model_name=settings.MODEL_GRADER)
    else:
        raise ValueError(f"Unknown GRADER_PROVIDER: {settings.GRADER_PROVIDER}")
