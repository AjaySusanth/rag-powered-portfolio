"""
WHY THIS WAS CHOSEN:
This module contains unit/integration tests for the POST /admin/retrieval-trace endpoint.
It validates the endpoint routing, schema validation, telemetry recording, caching bypass,
and the calculations for stage/aggregate latencies and statistics without making real network or DB calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.observability.tracing import PipelineTrace


def make_test_chunk() -> Chunk:
    """Helper to generate a mock Chunk."""
    return Chunk(
        chunk_id="chk_123",
        parent_document_id="doc_123",
        content_hash="hash_123",
        content="Ajay is a DevOps Engineer skilled in Kubernetes and Terraform.",
        project="n8n-aks-platform",
        layer="identity",
        source_type="manual",
        source_file="about-me.md",
        chunk_index=0,
        token_count=10,
        char_count=50,
        metadata={"heading": "About Ajay"},
    )


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.detect_project")
@patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock)
@patch("src.services.chat_orchestrator.create_generator_from_settings")
@patch("src.services.chat_orchestrator.create_cache_from_settings")
async def test_retrieval_trace_endpoint_success(
    mock_create_cache, mock_create_generator, mock_retrieve, mock_detect_project
) -> None:
    """Verifies that the /admin/retrieval-trace endpoint correctly populates all stages of the PipelineTrace."""
    # 1. Setup mock returns
    mock_detect_project.return_value = "n8n-aks-platform"

    # Setup mock cache
    mock_cache = MagicMock()
    mock_cache.get_chat_response = AsyncMock(return_value=None)
    mock_create_cache.return_value = mock_cache

    chunk = make_test_chunk()
    mock_retrieve.return_value = [RetrievalResult(chunk=chunk, score=0.95)]

    # Stream generator mock
    mock_generator = MagicMock()

    async def mock_stream_iter(prompt, system_instruction):
        yield "Hello"
        yield " "
        yield "world!"

    mock_generator.stream.side_effect = mock_stream_iter
    mock_create_generator.return_value = mock_generator

    # 2. Make request using AsyncClient
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"query": "Tell me about Ajay's skills", "session_id": "session_abc"}
        headers = {"X-Admin-Key": "dev-admin-key"}
        response = await client.post("/admin/retrieval-trace", json=payload, headers=headers)

        assert response.status_code == 200, response.json()
        data = response.json()

        # 3. Assert trace structure matches Pydantic model
        trace = PipelineTrace(**data)

        # Request verification
        assert trace.request.original_query == "Tell me about Ajay's skills"
        assert trace.request.detected_project == "n8n-aks-platform"

        # Cache bypass verification
        assert trace.metadata.cache_hit is False
        mock_cache.get_chat_response.assert_not_called()

        # Timings verification
        assert trace.timings.query_processing_ms >= 0
        assert trace.timings.total_request_ms >= 0
        assert "project_detection" in trace.timings.stages

        # Generation verification
        assert trace.generation.response_preview == "Hello world!"
        assert trace.generation.latency_ms >= 0


@pytest.mark.anyio
async def test_retrieval_trace_validation_failure() -> None:
    """Verifies that missing request fields trigger standard HTTP 422 errors."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-Admin-Key": "dev-admin-key"}
        response = await client.post("/admin/retrieval-trace", json={}, headers=headers)
        assert response.status_code == 422


@pytest.mark.anyio
async def test_retrieval_trace_authentication_failure() -> None:
    """Verifies that invalid or missing admin keys are rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"query": "test"}

        # Missing header -> 401
        res1 = await client.post("/admin/retrieval-trace", json=payload)
        assert res1.status_code == 401

        # Incorrect header -> 403
        res2 = await client.post(
            "/admin/retrieval-trace", json=payload, headers={"X-Admin-Key": "wrong-key"}
        )
        assert res2.status_code == 403


@pytest.mark.anyio
async def test_verify_admin_endpoint() -> None:
    """Verifies the status of the admin verification endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Missing header -> 401
        res1 = await client.get("/admin/verify")
        assert res1.status_code == 401

        # 2. Incorrect header -> 403
        res2 = await client.get("/admin/verify", headers={"X-Admin-Key": "wrong-key"})
        assert res2.status_code == 403

        # 3. Correct header -> 200
        res3 = await client.get("/admin/verify", headers={"X-Admin-Key": "dev-admin-key"})
        assert res3.status_code == 200
        assert res3.json() == {"status": "authenticated"}
