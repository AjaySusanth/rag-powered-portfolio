"""
WHY THIS WAS CHOSEN:
We define structured Pydantic schemas for deterministic portfolio endpoints (/resume and /stack).
This guarantees type safety, enforces consistent API contracts, and validates static data
structures returned by portfolio services.
"""

from typing import List
from pydantic import BaseModel, Field


class StackResponse(BaseModel):
    """Schema for technical stack info."""
    languages: List[str] = Field(..., description="Programming languages.")
    frameworks: List[str] = Field(..., description="Software frameworks and UI styling frameworks.")
    databases: List[str] = Field(..., description="Databases and cache layers.")
    cloud: List[str] = Field(..., description="Cloud providers and database/container cloud resources.")
    devops: List[str] = Field(..., description="DevOps tools, container orchestration, IaC, CI/CD, and monitoring.")
    ai_ml: List[str] = Field(..., description="AI/ML components and techniques (LLM, NLP, vector search).")
    tools: List[str] = Field(..., description="Workflows, ORMs, and developer utility tools.")
