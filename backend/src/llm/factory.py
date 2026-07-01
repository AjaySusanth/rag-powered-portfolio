"""
WHY THIS WAS CHOSEN:
This module implements the Factory Pattern to construct grader instances at runtime.
By referencing settings (GRADER_PROVIDER and MODEL_GRADER), we can change the grading model
or swap providers completely (e.g. from Google Gemini to Azure OpenAI or a Mock) without
modifying the retrieval pipeline or evaluation suite.
"""

from src.config import settings
from src.llm.interfaces import BaseGrader, BaseGenerator
from src.llm.providers.gemini import GeminiGrader, GeminiGenerator


def create_grader_from_settings() -> BaseGrader:
    """
    Creates and returns a BaseGrader instance based on application settings.
    """
    provider = settings.GRADER_PROVIDER.lower()

    if provider == "gemini":
        return GeminiGrader(model_name=settings.MODEL_GRADER)
    else:
        raise ValueError(f"Unknown GRADER_PROVIDER: {settings.GRADER_PROVIDER}")


def create_generator_from_settings() -> BaseGenerator:
    """
    Creates and returns a BaseGenerator instance based on application settings.
    
    Why: Uses GENERATOR_PROVIDER configuration to determine if the provider
    is Gemini or if we should add other providers (like OpenAI or local LLMs) in the future.
    """
    provider = settings.GENERATOR_PROVIDER.lower()

    if provider == "gemini":
        return GeminiGenerator(model_name=settings.GEMINI_MODEL_NAME)
    else:
        raise ValueError(f"Unknown generator provider: {settings.GENERATOR_PROVIDER}")
