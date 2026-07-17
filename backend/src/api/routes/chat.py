"""
WHY THIS WAS CHOSEN:
This module defines the REST endpoint for chat interactions. It receives request payloads,
validates them via Pydantic, and handles the HTTP-specific streaming response (SSE formatting
and serialization). It also implements the transport-level client-disconnect handling,
keeping the downstream orchestrator and LLM layers cleanly decoupled from FastAPI/HTTP.
"""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.rate_limiter import RateLimiter
from src.api.schemas.chat import ChatRequest
from src.services.chat_orchestrator import ChatOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()
chat_limiter = RateLimiter()


@router.post("/chat", dependencies=[Depends(chat_limiter)])
async def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    """
    HTTP POST /chat endpoint. Validates request and returns a Server-Sent Events (SSE) stream.
    """
    orchestrator = ChatOrchestrator()

    async def sse_generator():
        try:
            async for event in orchestrator.stream_chat(
                query=request.message, session_id=request.session_id
            ):
                # Serialize the Pydantic model event to a JSON string
                payload = event.model_dump(mode="json")
                yield f"data: {json.dumps(payload)}\n\n"

            # Enforce exactly one [DONE] event on normal termination
            yield "data: [DONE]\n\n"
            logger.info("Chat stream completed successfully.")

        except asyncio.CancelledError:
            # Traps client disconnects cleanly without emitting further SSE events.
            logger.warning("Chat stream cancelled due to client disconnect.")
            # Re-raise CancelledError to allow FastAPI's server to close the socket properly.
            raise
        except Exception as e:
            logger.error(f"Error occurred in route SSE generator: {e}")
            err_payload = {
                "event": "error",
                "code": "internal_server_error",
                "message": "An unexpected error occurred.",
            }
            yield f"data: {json.dumps(err_payload)}\n\n"
            # Ensure DONE event is yielded even on error
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
