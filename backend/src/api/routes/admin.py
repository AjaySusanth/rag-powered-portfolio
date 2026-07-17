"""
WHY THIS WAS CHOSEN:
Exposes administrative endpoints (specifically POST /ingest) at the API root level.
The route remains thin by delegating ingestion logic to IngestionService.
Exceptions are propagated as HTTP 500 (or HTTP 404 for missing config files)
to shield users from internal server issues and let admins debug failures directly.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import APIKeyHeader

from src.api.schemas.admin import IngestRequest, IngestResponse, RetrievalTraceRequest
from src.config import settings
from src.observability.tracing import PipelineTrace
from src.services.chat_orchestrator import ChatOrchestrator
from src.services.ingestion_service import IngestionService

api_key_header = APIKeyHeader(name="X-Admin-Key")


async def verify_admin_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid admin key")
    return api_key


router = APIRouter(tags=["Admin"], dependencies=[Depends(verify_admin_key)])


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
            status_code=500, detail=f"Server-side configuration or pipeline error: {str(e)}"
        )


@router.post("/admin/retrieval-trace", response_model=PipelineTrace)
async def trigger_retrieval_trace(request: RetrievalTraceRequest) -> PipelineTrace:
    """
    Executes retrieval and generation for a query, tracing all stages and measurements.
    Bypasses caching to ensure retrieval statistics are collected.
    """
    try:
        orchestrator = ChatOrchestrator()
        trace = PipelineTrace()
        # Consume the stream to run the orchestrator process end-to-end
        async for _ in orchestrator.stream_chat(
            query=request.query, session_id=request.session_id, trace=trace, skip_cache=True
        ):
            pass
        return trace
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error gathering retrieval trace: {str(e)}")


@router.get("/admin/verify")
async def verify_admin() -> dict:
    """
    Simple endpoint to check if the provided X-Admin-Key is valid.
    Inherits router dependencies so it will reject invalid keys with 403 or 401.
    """
    return {"status": "authenticated"}
