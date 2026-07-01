"""
DESIGN DECISION:
This module manages all configuration variables for the application via Pydantic Settings.
It loads variables from the environment and falls back to a `.env` file if present.

Using a central Settings class prevents configuration fragmentation and hardcoded values,
ensuring security and consistency across the database and OpenAI integrations.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path
from urllib.parse import urlparse

# Resolve the absolute path to the project root where .env resides
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    """
    Application settings, populated from environment variables or a .env file.
    """
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/portfolio",
        description="PostgreSQL connection string"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )

    # Azure OpenAI Configuration
    AZURE_OPENAI_API_KEY: Optional[str] = Field(
        default=None,
        validation_alias="AZURE_OPENAI_KEY",  # Allow either AZURE_OPENAI_API_KEY or AZURE_OPENAI_KEY
        description="Azure OpenAI API key"
    )
    AZURE_OPENAI_ENDPOINT: str = Field(
        ...,
        description="Azure OpenAI Endpoint URL"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-02-01",
        description="Azure OpenAI API version"
    )
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = Field(
        default="text-embedding-3-small",
        description="The deployment name of the embedding model in Azure"
    )

    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google Gemini API Key"
    )
    GEMINI_MODEL_NAME: str = Field(
        default="gemini-3.1-flash-lite",
        description="The Gemini model name to use for answer generation"
    )
    MODEL_GRADER: str = Field(
        default="gemini-3.1-flash-lite",
        description="The model name to use for retrieval chunk grading"
    )
    GRADER_PROVIDER: str = Field(
        default="gemini",
        description="The provider for the retrieval grader (e.g., gemini, mock)"
    )
    GENERATOR_PROVIDER: str = Field(
        default="gemini",
        description="The provider for answer generation (e.g., gemini, mock)"
    )
    GRADER_MIN_CHUNKS: int = Field(
        default=3,
        description="Minimum number of chunks to return from grader. If relevant chunks are less than this, fallback to original list."
    )
    ENABLE_QUERY_REWRITER: bool = Field(
        default=False,
        description="Whether to enable the query rewriter preprocessing step"
    )
    MODEL_REWRITER: str = Field(
        default="gemini-3.1-flash-lite",
        description="The Gemini model name to use for query rewriting"
    )
    REWRITER_PROVIDER: str = Field(
        default="gemini",
        description="The provider for the query rewriter (e.g., gemini, mock)"
    )

    GITHUB_TOKEN: Optional[str] = Field(
        default=None,
        description="GitHub Personal Access Token"
    )


    @field_validator("AZURE_OPENAI_ENDPOINT", mode="before")
    @classmethod
    def clean_endpoint(cls, v: str) -> str:
        """
        Cleans the Azure endpoint. The Azure OpenAI SDK expects the base URL, e.g.:
        'https://<resource-name>.cognitiveservices.azure.com/'
        If the full deployment embedding path was copied in, strip it back to the base URL.
        """
        if not v:
            return v
        parsed = urlparse(v)
        # Reconstruct just the scheme and netloc (e.g., https://resource-name.cognitiveservices.azure.com)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return v

# Global settings instance
settings = Settings()
