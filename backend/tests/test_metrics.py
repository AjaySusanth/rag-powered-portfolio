"""
WHY THIS WAS CHOSEN:
This module contains unit tests for the Prometheus metrics system and GET /metrics endpoint.
It ensures that metrics are correctly declared, exposed on the endpoint with the right HTTP headers,
and that querying the chat system increments/updates the Prometheus registry.
All external connections are mocked to prevent real database or LLM network requests.
"""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.observability.metrics import (
    rag_queries_total,
    rag_requests_in_progress,
    rag_query_duration_seconds,
)


@pytest.mark.anyio
async def test_metrics_endpoint_success() -> None:
    """
    Verifies that the GET /metrics endpoint is exposed, returns HTTP 200,
    and includes standard Prometheus format headers and content.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert "rag_queries_total" in response.text
        assert "rag_requests_in_progress" in response.text
        assert "rag_query_duration_seconds" in response.text


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.detect_project")
@patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock)
@patch("src.services.chat_orchestrator.create_generator_from_settings")
async def test_metrics_updated_on_chat(
    mock_create_generator: MagicMock,
    mock_retrieve: AsyncMock,
    mock_detect_project: MagicMock,
) -> None:
    """
    Verifies that processing a chat request correctly increments the RAG query counters
    in the Prometheus registry.
    """
    # 1. Setup mocks
    mock_detect_project.return_value = None
    mock_retrieve.return_value = []
    
    mock_generator = MagicMock()
    async def mock_stream_iter(prompt: str, system_instruction: str):
        yield "Response"
    mock_generator.stream.side_effect = mock_stream_iter
    mock_create_generator.return_value = mock_generator

    # Get initial values of the counter
    # prometheus_client collects metric values using collect()
    def get_query_count() -> float:
        for metric in rag_queries_total.collect():
            for sample in metric.samples:
                # Filter for samples with labels match our test route (miss, global, success)
                if (
                    sample.labels.get("cache_status") == "miss"
                    and sample.labels.get("retrieval_scope") == "global"
                    and sample.labels.get("status") == "success"
                ):
                    return sample.value
        return 0.0

    initial_queries = get_query_count()

    # 2. Fire a chat request to trigger metrics recording
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"message": "Test metrics query"}
        response = await client.post("/chat", json=payload)
        assert response.status_code == 200

    # 3. Check that query counter incremented by 1
    new_queries = get_query_count()
    assert new_queries == initial_queries + 1
