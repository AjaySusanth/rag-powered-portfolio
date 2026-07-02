"""
WHY THIS WAS CHOSEN:
Exposes deterministic endpoints /resume and /stack at the API root.
Bypasses all RAG/LLM components entirely to eliminate latency, cost, and hallucination.
Returns the PDF directly using FileResponse, and deserializes stack JSON using Pydantic models.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from pydantic import ValidationError

from src.api.schemas.portfolio import StackResponse, HireResponse
from src.services.portfolio_service import PortfolioService


router = APIRouter(tags=["Portfolio"])


@router.get("/resume", response_class=FileResponse)
async def get_resume() -> FileResponse:
    """
    Returns Ajay's latest resume PDF directly.
    Configured so the downloaded file is named 'Ajay_Susanth_Resume.pdf'.
    """
    path = PortfolioService.get_resume_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Resume PDF file not found.")
    
    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="Ajay_Susanth_Resume.pdf"
    )


@router.get("/stack", response_model=StackResponse)
async def get_stack() -> StackResponse:
    """
    Returns the structured technology stack.
    """
    try:
        data = PortfolioService.get_stack()
        return StackResponse(**data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load technology stack: {str(e)}")


@router.get("/hire", response_model=HireResponse)
async def get_hire() -> HireResponse:
    """
    Returns structured hiring, availability, and contact information.
    Bypasses RAG and LLM components to ensure high reliability.
    """
    try:
        data = PortfolioService.get_hire()
        return HireResponse(**data)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (ValidationError, Exception) as e:
        raise HTTPException(
            status_code=500,
            detail=f"Server-side configuration error: {str(e)}"
        )

