"""
WHY THIS WAS CHOSEN:
We define structured Pydantic schemas for the administrative ingestion API.
IngestSummary acts as the canonical data model returned by the service layer,
sharing the contract between the CLI tool and the HTTP endpoint.
"""

from typing import List

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Request payload for triggering ingestion."""
    project_name: str = Field(..., description="The name of the project to ingest.")


class IngestSummary(BaseModel):
    """Canonical ingestion summary returned by the ingestion service."""
    status: str = Field(..., description="Overall status (e.g., 'success', 'failed').")
    project_name: str = Field(..., description="The name of the project ingested.")
    documents_processed: int = Field(..., description="Number of documents processed.")
    chunks_created: int = Field(..., description="Number of chunks created.")
    embeddings_generated: int = Field(..., description="Number of embeddings generated.")
    duration_seconds: float = Field(..., description="Duration of the ingestion run in seconds.")
    errors: List[str] = Field(default_factory=list, description="List of error messages or partial failures encountered.")


class IngestResponse(BaseModel):
    """API response model wrapping the ingestion summary."""
    summary: IngestSummary = Field(..., description="Summary details of the ingestion run.")
