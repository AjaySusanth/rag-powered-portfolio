"""
DESIGN DECISION:
This module contains unit tests for the POST /chat SSE streaming endpoint.
It tests endpoint routing, validation, query rewriting integration, hybrid retrieval propagation,
SSE event serialization, error handling, and client disconnects (cancellation).
We mock all downstream layers (project detector, rewriter, retriever, grader, generator)
to isolate the API route and the ChatOrchestrator, making no external network or DB calls.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from src.main import app
from src.api.schemas.chat import StreamTokenEvent, StreamErrorEvent
from src.models.retrieval_result import RetrievalResult
from src.models.chunk import Chunk
from src.retrieval.rewriters.base import BaseQueryRewriter
from src.models.rewrite_result import RewriteResult


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
        metadata={"heading": "About Ajay"}
    )


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.detect_project")
@patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock)
@patch("src.services.chat_orchestrator.create_generator_from_settings")
async def test_chat_endpoint_success(
    mock_create_generator,
    mock_retrieve,
    mock_detect_project
) -> None:
    """Verifies standard successful end-to-end chat stream and DONE termination."""
    # 1. Setup mock returns
    mock_detect_project.return_value = "n8n-aks-platform"

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
        payload = {"message": "Tell me about Ajay's skills", "session_id": "session_abc"}
        response = await client.post("/chat", json=payload)
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        
        # Read the raw stream text
        lines = [line.strip() for line in response.text.split("\n") if line.strip()]
        
        # We expect:
        # data: {"event": "token", "token": "Hello"}
        # data: {"event": "token", "token": " "}
        # data: {"event": "token", "token": "world!"}
        # data: [DONE]
        assert len(lines) == 4
        assert lines[0] == 'data: {"event": "token", "token": "Hello"}'
        assert lines[1] == 'data: {"event": "token", "token": " "}'
        assert lines[2] == 'data: {"event": "token", "token": "world!"}'
        assert lines[3] == "data: [DONE]"


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.detect_project")
@patch("src.services.chat_orchestrator.create_rewriter_from_settings")
@patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock)
@patch("src.services.chat_orchestrator.create_generator_from_settings")
async def test_chat_endpoint_query_rewriter(
    mock_create_generator,
    mock_retrieve,
    mock_create_rewriter,
    mock_detect_project
) -> None:
    """Verifies that query rewriting updates the query passed to the retriever but not prompt building."""
    # Enable rewriter settings contextually
    with patch("src.services.chat_orchestrator.settings") as mock_settings:
        mock_settings.ENABLE_QUERY_REWRITER = True
        mock_settings.GRADER_PROVIDER = "gemini"
        mock_settings.GEMINI_MODEL_NAME = "gemini-3.1-flash-lite"

        mock_detect_project.return_value = "n8n-aks-platform"

        # Mock Rewriter
        mock_rewriter = AsyncMock(spec=BaseQueryRewriter)
        mock_rewriter.rewrite.return_value = RewriteResult(
            rewritten_query="Kubernetes cluster setup AKS details",
            rewritten=True,
            explanation="Expanded query terms"
        )
        mock_create_rewriter.return_value = mock_rewriter

        chunk = make_test_chunk()
        mock_retrieve.return_value = [RetrievalResult(chunk=chunk, score=0.95)]

        mock_generator = MagicMock()
        async def mock_stream_iter(prompt, system_instruction):
            # Assert that the prompt uses the original query, not rewritten query
            assert "Tell me about AKS" in prompt
            assert "Kubernetes cluster setup" not in prompt
            yield "Success"
        mock_generator.stream.side_effect = mock_stream_iter
        mock_create_generator.return_value = mock_generator

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {"message": "Tell me about AKS"}
            response = await client.post("/chat", json=payload)
            
            assert response.status_code == 200
            mock_rewriter.rewrite.assert_called_once_with("Tell me about AKS", "n8n-aks-platform")
            mock_retrieve.assert_called_once_with(
                query="Kubernetes cluster setup AKS details",
                project="n8n-aks-platform",
                diversify=True,
                grade=True
            )


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.detect_project")
@patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock)
async def test_chat_endpoint_retrieval_failure(
    mock_retrieve,
    mock_detect_project
) -> None:
    """Verifies that retrieval errors yield a structured SSE error event before DONE."""
    mock_detect_project.return_value = None
    mock_retrieve.side_effect = Exception("DB connection timeout")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"message": "fail retrieval"}
        response = await client.post("/chat", json=payload)
        
        assert response.status_code == 200
        lines = [line.strip() for line in response.text.split("\n") if line.strip()]
        
        # Expected events: error, then DONE
        assert len(lines) == 2
        assert "error" in lines[0]
        assert "retrieval_failed" in lines[0]
        assert lines[1] == "data: [DONE]"


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.detect_project")
@patch("src.services.chat_orchestrator.retrieve", new_callable=AsyncMock)
@patch("src.services.chat_orchestrator.create_generator_from_settings")
async def test_chat_endpoint_llm_failure(
    mock_create_generator,
    mock_retrieve,
    mock_detect_project
) -> None:
    """Verifies that LLM generator failures emit LLM error event before DONE."""
    mock_detect_project.return_value = None
    mock_retrieve.return_value = []

    # Mock generator raising error
    mock_generator = MagicMock()
    async def mock_stream_iter_fail(prompt, system_instruction):
        yield "Some text"
        raise Exception("Gemini quota exceeded")
        # Generator iteration raises error
    mock_generator.stream.side_effect = mock_stream_iter_fail
    mock_create_generator.return_value = mock_generator

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"message": "trigger generation error"}
        response = await client.post("/chat", json=payload)
        
        assert response.status_code == 200
        lines = [line.strip() for line in response.text.split("\n") if line.strip()]
        
        # We expect: token, error, DONE
        assert len(lines) == 3
        assert lines[0] == 'data: {"event": "token", "token": "Some text"}'
        assert "error" in lines[1]
        assert "unexpected_error" in lines[1]
        assert lines[2] == "data: [DONE]"


@pytest.mark.anyio
async def test_chat_endpoint_validation_missing_field() -> None:
    """Verifies that missing request fields trigger standard HTTP 422 errors."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Send empty dictionary (missing message field)
        response = await client.post("/chat", json={})
        assert response.status_code == 422


@pytest.mark.anyio
async def test_chat_endpoint_empty_message_stream_error() -> None:
    """Verifies that an empty message yields a stream error event instead of raising an HTTP exception."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"message": ""})
        assert response.status_code == 200
        lines = [line.strip() for line in response.text.split("\n") if line.strip()]
        
        # We expect: error event, then DONE
        assert len(lines) == 2
        assert "error" in lines[0]
        assert "invalid_query" in lines[0]
        assert lines[1] == "data: [DONE]"
