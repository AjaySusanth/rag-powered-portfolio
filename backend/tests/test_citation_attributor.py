import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.models.retrieval_result import RetrievalResult
from src.models.chunk import Chunk
from src.services.citation_attributor import GeminiCitationAttributor
from src.llm.gemini_client import LLMError

def make_mock_result(chunk_id: str, source_file: str) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=chunk_id,
            parent_document_id="doc-1",
            content_hash="h1",
            content="sample text here for chunk",
            project="test-proj",
            layer="identity",
            source_type="github",
            source_file=source_file,
            chunk_index=0,
            token_count=5,
            char_count=20
        ),
        score=0.9
    )

@pytest.mark.anyio
async def test_citation_attributor_success() -> None:
    # Setup mock response
    mock_response = AsyncMock()
    mock_parsed = MagicMock()
    mock_parsed.chunk_ids = ["c1", "c3"]
    mock_response.parsed = mock_parsed

    with patch("src.services.citation_attributor.get_gemini_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.aio.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        attributor = GeminiCitationAttributor(model_name="gemini-3.1-flash-lite")
        results = [
            make_mock_result("c1", "file1.md"),
            make_mock_result("c2", "file2.md"),
            make_mock_result("c3", "file3.md"),
        ]

        grounding_ids = await attributor.attribute_citations(
            answer="This supports file1 and file3.",
            results=results
        )

        assert grounding_ids == ["c1", "c3"]
        mock_client.aio.models.generate_content.assert_called_once()


@pytest.mark.anyio
async def test_citation_attributor_api_failure_raises_llm_error() -> None:
    with patch("src.services.citation_attributor.get_gemini_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.aio.models.generate_content.side_effect = Exception("API quota exceeded")
        mock_get_client.return_value = mock_client

        attributor = GeminiCitationAttributor(model_name="gemini-3.1-flash-lite")
        
        with pytest.raises(LLMError) as exc_info:
            await attributor.attribute_citations(
                answer="Answer",
                results=[make_mock_result("c1", "file.md")]
            )
        assert "Gemini citation attribution failed" in str(exc_info.value)
