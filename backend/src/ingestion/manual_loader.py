"""
DESIGN DECISION:
This module implements the local knowledge document ingestion pipeline.
It scans the manually maintained markdown files in `/knowledge` directory,
creates canonical Document objects with `source_type = "manual"`, and maps
them to layers (Identity vs Design) according to their filenames.

We assign global identity documents (resume.md, about-me.md, faq.md, etc.) to a
reserved project namespace GLOBAL_PROJECT_NAME to avoid duplicating identity
information across multiple projects while still keeping them available for indexing.

WHY THIS WAS CHOSEN:
To ensure namespace isolation, manual loading is strictly partitioned:
1. If the project_name matches GLOBAL_PROJECT_NAME, we only load root global identity markdown files.
2. If it is a specific project name, we only load markdown files inside that project's subdirectory.
This avoids project-specific re-index operations from accidentally reading, deleting, or re-inserting global identity data.
"""

import logging
from pathlib import Path
from typing import List

from src.config import GLOBAL_PROJECT_NAME
from src.models.document import Document, determine_document_layer

logger = logging.getLogger(__name__)


class ManualIngestionError(Exception):
    """Raised for errors during manual document loading."""
    pass


def discover_projects(knowledge_dir: Path) -> List[str]:
    """
    Scans the knowledge directory and returns a list of discovered project names.
    Any subdirectory in knowledge_dir is considered a project directory.
    """
    if not knowledge_dir.exists() or not knowledge_dir.is_dir():
        logger.warning(f"Knowledge directory does not exist: {knowledge_dir}")
        return []

    projects = []
    for p in knowledge_dir.iterdir():
        if p.is_dir():
            projects.append(p.name)
    return sorted(projects)


def load_manual_documents(project_name: str, knowledge_dir: Path) -> List[Document]:
    """
    Loads manual Markdown documents for either a specific project or the global namespace.

    1. If project_name == GLOBAL_PROJECT_NAME:
       Reads global identity files in the root knowledge_dir (resume.md, about-me.md, faq.md, etc.)
       and assigns them project = GLOBAL_PROJECT_NAME.
    2. If project_name != GLOBAL_PROJECT_NAME:
       Reads project-specific files in knowledge_dir / project_name recursively
       and assigns them project = project_name.
    """
    if not knowledge_dir.exists() or not knowledge_dir.is_dir():
        raise ManualIngestionError(f"Knowledge directory not found: {knowledge_dir}")

    documents: List[Document] = []

    # 1. Load global identity documents from root knowledge_dir
    if project_name == GLOBAL_PROJECT_NAME:
        for path in knowledge_dir.iterdir():
            if path.is_file() and path.suffix.lower() == ".md":
                # Determine layer
                layer = determine_document_layer(path.name, "manual")
                if layer == "identity":
                    try:
                        content = path.read_text(encoding="utf-8")
                        documents.append(
                            Document(
                                content=content,
                                project=GLOBAL_PROJECT_NAME,
                                layer=layer,
                                source_type="manual",
                                source_file=path.name,
                                metadata={"source": "manual", "original_file": path.name}
                            )
                        )
                    except Exception as e:
                        logger.error(f"Failed to read global document {path.name}: {e}")
                        raise ManualIngestionError(f"Failed to load global document {path.name}: {e}") from e
        return documents

    # 2. Load project-specific documents
    project_dir = knowledge_dir / project_name
    if project_dir.exists() and project_dir.is_dir():
        # Recursively search for markdown files in project_dir
        for path in project_dir.rglob("*.md"):
            if path.is_file():
                # Compute source file relative to the project directory or relative path
                # e.g., 'talentforge/architecture.md'
                try:
                    rel_path = path.relative_to(knowledge_dir).as_posix()
                except ValueError:
                    rel_path = path.name

                layer = determine_document_layer(path.name, "manual")
                try:
                    content = path.read_text(encoding="utf-8")
                    documents.append(
                        Document(
                            content=content,
                            project=project_name,
                            layer=layer,
                            source_type="manual",
                            source_file=rel_path,
                            metadata={"source": "manual", "original_file": rel_path}
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to read project document {rel_path}: {e}")
                    raise ManualIngestionError(f"Failed to load project document {rel_path}: {e}") from e
    else:
        logger.warning(f"Project manual directory does not exist: {project_dir}")

    return documents
