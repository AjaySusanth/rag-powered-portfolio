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

GLOBAL_PROJECT_NAME = "__global__"

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
    DIVERSIFICATION_MAX_PER_SOURCE: int = Field(
        default=3,
        description="Maximum number of chunks allowed from a single source file in the diversified results."
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
    MODEL_ATTRIBUTOR: str = Field(
        default="gemini-3.1-flash-lite",
        description="The Gemini model name to use for citation attribution"
    )
    ATTRIBUTOR_PROVIDER: str = Field(
        default="gemini",
        description="The provider for the citation attributor (e.g., gemini, mock)"
    )

    GITHUB_TOKEN: Optional[str] = Field(
        default=None,
        description="GitHub Personal Access Token"
    )

    # API Rate Limiting Configuration
    RATE_LIMIT_REQUESTS: int = Field(
        default=10,
        description="Maximum requests allowed per window"
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        description="Duration of rate limiting window in seconds"
    )

    # Cache Configuration
    CACHE_TTL_SECONDS: int = Field(
        default=86400,
        description="Time to live for cached chat responses in seconds (default: 24h)"
    )
    EMBEDDING_CACHE_TTL_SECONDS: int = Field(
        default=604800,
        description="Time to live for cached embeddings in seconds (default: 7d)"
    )
    EMBEDDING_PROVIDER: str = Field(
        default="azure_openai",
        description="The provider for generating embeddings (e.g., azure_openai, mock)"
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="The model name for embeddings"
    )
    PROMPT_VERSION: str = Field(
        default="v1.0",
        description="Version string for the system prompt to invalidate cache on prompt updates"
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
