"""
WHY THIS WAS CHOSEN:
Exposes administrative endpoints (specifically POST /ingest) at the API root level.
The route remains thin by delegating ingestion logic to IngestionService.
Exceptions are propagated as HTTP 500 (or HTTP 404 for missing config files)
to shield users from internal server issues and let admins debug failures directly.
"""

from fastapi import APIRouter, HTTPException

from src.api.schemas.admin import IngestRequest, IngestResponse
from src.services.ingestion_service import IngestionService


router = APIRouter(tags=["Admin"])


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingestion(request: IngestRequest) -> IngestResponse:
    """
    Triggers document ingestion and indexing for a specific project.
    Reuses existing ingestion components synchronously.
    """
    try:
        summary = await IngestionService.ingest_project(request.project_name)
        return IngestResponse(summary=summary)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server-side configuration or pipeline error: {str(e)}"
        )
