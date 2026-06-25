"""
DESIGN DECISION:
This module defines the canonical Document model used across the entire RAG pipeline.
Normalizing all incoming data (resumes, architecture decisions, and code files) into
a single, unified Document schema allows the chunker, embedder, and vector store to
process documents without knowing their specific origins.

We use Python dataclasses for lightweight, clean in-memory representation.
Layer classification is explicitly based on known filename sets to maintain a
strict separation of intent (e.g. Identity vs Design vs Artifact) as mandated by
the project's architectural guidelines.
"""

from dataclasses import dataclass, field
from typing import Any, Dict

IDENTITY_FILES = {"resume.md", "about-me.md", "faq.md"}

DESIGN_FILES = {
    "architecture.md",
    "decisions.md",
    "challenges.md",
    "lessons-learned.md",
    "approach.md",
}


@dataclass
class Document:
    """
    Canonical document representation utilized throughout the RAG pipeline.
    """
    content: str
    project: str
    layer: str  # 'identity', 'design', or 'artifact'
    source_type: str  # 'github' or 'manual'
    source_file: str
    metadata: Dict[str, Any] = field(default_factory=dict)


def determine_document_layer(source_file: str, source_type: str) -> str:
    """
    Determines the document layer based on the filename and source type.
    
    Identity and design layers are exclusively hand-authored files with known semantic
    purposes. Everything else defaults to the artifact layer.
    """
    if not source_file:
        return "artifact"
        
    # Get the basename of the file path (e.g., 'path/to/resume.md' -> 'resume.md')
    filename = source_file.split("/")[-1].split("\\")[-1].lower()
    
    if filename in IDENTITY_FILES:
        return "identity"
    if filename in DESIGN_FILES:
        return "design"
        
    return "artifact"
