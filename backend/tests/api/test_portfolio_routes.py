from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.config import DATA_DIR, RESUME_DIR
from src.main import app
from src.services.portfolio_service import PortfolioService


@pytest.fixture
def clean_lru_cache():
    """Clears the lru_cache for get_stack and get_hire before and after tests."""
    PortfolioService.get_stack.cache_clear()
    PortfolioService.get_hire.cache_clear()
    yield
    PortfolioService.get_stack.cache_clear()
    PortfolioService.get_hire.cache_clear()


@pytest.mark.anyio
@patch("src.services.portfolio_service.PortfolioService.get_resume_path")
async def test_get_resume_success(mock_get_resume_path, tmp_path) -> None:
    # Create a temporary PDF file for testing
    temp_pdf = tmp_path / "Ajay_Susanth_Resume.pdf"
    temp_pdf.write_text("dummy pdf contents")
    mock_get_resume_path.return_value = temp_pdf

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/resume")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert (
            'attachment; filename="Ajay_Susanth_Resume.pdf"'
            in response.headers["content-disposition"]
        )
        assert response.content == b"dummy pdf contents"


@pytest.mark.anyio
@patch("src.services.portfolio_service.PortfolioService.get_resume_path")
async def test_get_resume_missing(mock_get_resume_path) -> None:
    # Mock a non-existent file path
    mock_get_resume_path.return_value = Path("non_existent_file.pdf")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/resume")
        assert response.status_code == 404
        assert "Resume PDF file not found." in response.json()["detail"]


@pytest.mark.anyio
async def test_get_stack_success(clean_lru_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/stack")
        assert response.status_code == 200
        data = response.json()
        for field in ["languages", "frameworks", "databases", "cloud", "devops", "ai_ml", "tools"]:
            assert field in data
            assert isinstance(data[field], list)


@pytest.mark.anyio
@patch("src.services.portfolio_service.DATA_DIR")
async def test_get_stack_missing(mock_data_dir, clean_lru_cache) -> None:
    # Force service to look for stack.json in a non-existent folder
    mock_data_dir.__truediv__.return_value.exists.return_value = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/stack")
        # Should fail to locate the stack file and raise a 404
        assert response.status_code == 404
        assert "Stack metadata file not found" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_hire_success(clean_lru_cache) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/hire")
        assert response.status_code == 200
        data = response.json()

        # Verify schema elements
        assert data["name"] == "Ajay Susanth"
        assert data["currently_available"] is True
        assert isinstance(data["preferred_roles"], list)
        assert isinstance(data["employment_types"], list)
        assert isinstance(data["preferred_locations"], list)
        assert data["work_authorization"] == "India"
        assert "email" in data["contact"]
        assert "linkedin" in data["contact"]
        assert "github" in data["contact"]
        assert "portfolio" in data["contact"]
        assert data["resume_url"] == "/resume"


@pytest.mark.anyio
@patch("src.services.portfolio_service.DATA_DIR")
async def test_get_hire_missing(mock_data_dir, clean_lru_cache) -> None:
    # Force service to look for hire.json in a non-existent folder
    mock_data_dir.__truediv__.return_value.exists.return_value = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/hire")
        assert response.status_code == 404
        assert "Hiring metadata file not found" in response.json()["detail"]


@pytest.mark.anyio
@patch("src.services.portfolio_service.PortfolioService.get_hire")
async def test_get_hire_malformed_returns_500(mock_get_hire, clean_lru_cache) -> None:
    # Mock returning invalid data missing required fields to trigger ValidationError
    mock_get_hire.return_value = {"name": "Ajay Susanth"}  # Missing all other fields

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/hire")
        assert response.status_code == 500
        assert "Server-side configuration error" in response.json()["detail"]


@pytest.mark.anyio
@patch("src.services.chat_orchestrator.ChatOrchestrator")
@patch("src.services.chat_orchestrator.retrieve")
@patch("src.services.chat_orchestrator.PromptBuilder")
@patch("src.services.chat_orchestrator.create_generator_from_settings")
@patch("src.services.chat_orchestrator.create_cache_from_settings")
async def test_no_rag_components_invoked(
    mock_cache, mock_gen, mock_builder, mock_retrieve, mock_orchestrator, clean_lru_cache
) -> None:
    """Verifies that RAG pipeline, chat orchestrator, generators, builders, and caches are never invoked."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Call GET /resume
        resp_resume = await client.get("/resume")
        assert resp_resume.status_code == 200

        # Call GET /stack
        resp_stack = await client.get("/stack")
        assert resp_stack.status_code == 200

        # Call GET /hire
        resp_hire = await client.get("/hire")
        assert resp_hire.status_code == 200

    # Ensure none of the RAG/LLM/caching decorators or modules were invoked
    mock_orchestrator.assert_not_called()
    mock_retrieve.assert_not_called()
    mock_builder.assert_not_called()
    mock_gen.assert_not_called()
    mock_cache.assert_not_called()


def test_portfolio_filesystem_layout() -> None:
    """
    Regression test: verifies that the centralized path constants in config.py
    resolve to files that actually exist on the current filesystem layout.

    WHY THIS MATTERS:
    This test would have caught the Docker path regression (PROJECT_ROOT resolving
    to the repo root inside the container, making backend/data unreachable) before
    it reached production. If DATA_DIR or RESUME_DIR are wrong, this test fails
    during CI — before any Docker build or Render deploy can succeed.
    """
    assert DATA_DIR.is_dir(), (
        f"DATA_DIR does not exist: {DATA_DIR}. "
        "Check APP_ROOT in config.py matches the current runtime layout."
    )
    assert (DATA_DIR / "stack.json").is_file(), f"stack.json not found in {DATA_DIR}"
    assert (DATA_DIR / "hire.json").is_file(), f"hire.json not found in {DATA_DIR}"
    assert RESUME_DIR.is_dir(), f"RESUME_DIR does not exist: {RESUME_DIR}"
    assert (RESUME_DIR / "Ajay_Susanth_Resume.pdf").is_file(), (
        f"Resume PDF not found in {RESUME_DIR}"
    )
