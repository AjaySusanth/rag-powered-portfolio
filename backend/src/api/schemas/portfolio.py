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


class ContactInfo(BaseModel):
    """Schema for professional contact information."""
    email: str = Field(..., description="Professional email address.")
    linkedin: str = Field(..., description="LinkedIn profile URL.")
    github: str = Field(..., description="GitHub profile URL.")
    portfolio: str = Field(..., description="Personal portfolio website URL.")


class HireResponse(BaseModel):
    """Schema for hiring and availability status."""
    name: str = Field(..., description="Full name of the candidate.")
    currently_available: bool = Field(..., description="Whether the candidate is currently open for offers.")
    status: str = Field(..., description="Human-readable availability description.")
    preferred_roles: List[str] = Field(..., description="List of preferred job titles/roles.")
    employment_types: List[str] = Field(..., description="Types of employment sought.")
    preferred_locations: List[str] = Field(..., description="Preferred work locations.")
    work_authorization: str = Field(..., description="Countries authorized to work in.")
    contact: ContactInfo = Field(..., description="Contact details and links.")
    resume_url: str = Field(..., description="Navigable URL to download/view the resume PDF.")

