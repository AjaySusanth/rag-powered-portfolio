"""
DESIGN DECISION:
This module contains unit tests for the Gemini 2.0 Flash LLM client wrapper.
It mocks the Google GenAI Client and the async context manager (`client.aio`) using
standard `unittest.mock` to verify prompt construction, config parameters, and error propagation
without executing real external network calls.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.gemini_client import LLMError, generate_answer


@pytest.mark.anyio
async def test_generate_answer_success() -> None:
    """Verifies that generate_answer formats prompts correctly and invokes the Gemini model asynchronously."""
    mock_response = MagicMock()
    mock_response.text = "Ajay has worked with Kubernetes on AKS."

    with patch("src.llm.gemini_client.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_aclient = AsyncMock()
        mock_aclient.models.generate_content.return_value = mock_response

        # client.aio works as an async context manager (__aenter__ returns the client)
        mock_client.aio.__aenter__.return_value = mock_aclient
        mock_get_client.return_value = mock_client

        context_chunks = [
            {"source_file": "resume.md", "heading": "### Experience", "content": "Ajay deployed microservices on AKS."}
        ]

        result = await generate_answer("What is Ajay's experience with AKS?", context_chunks)

        assert result == "Ajay has worked with Kubernetes on AKS."
        mock_aclient.models.generate_content.assert_called_once()

        # Verify call args
        from src.config import settings
        args, kwargs = mock_aclient.models.generate_content.call_args
        assert kwargs["model"] == settings.GEMINI_MODEL_NAME
        assert "AKS" in kwargs["contents"]
        assert "context" in kwargs["contents"].lower()
        assert kwargs["config"].temperature == 0.0
        assert "STRICT GROUNDING RULES" in kwargs["config"].system_instruction


@pytest.mark.anyio
async def test_generate_answer_failure() -> None:
    """Verifies that exceptions during the API call are caught and wrapped in LLMError."""
    with patch("src.llm.gemini_client.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_aclient = AsyncMock()
        mock_aclient.models.generate_content.side_effect = Exception("API rate limit exceeded")

        mock_client.aio.__aenter__.return_value = mock_aclient
        mock_get_client.return_value = mock_client

        with pytest.raises(LLMError) as exc_info:
            await generate_answer("test query", [])

        assert "Gemini API call failed" in str(exc_info.value)
