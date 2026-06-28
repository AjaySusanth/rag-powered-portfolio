"""
DESIGN DECISION:
This module contains unit tests for the Manual Ingestion Pipeline (manual_loader.py).
We use the pytest `tmp_path` fixture to dynamically construct a mock knowledge base
with diverse files (global identity documents, project-specific design files, and
unsupported types like .yml or .txt). This ensures our loader traverses the directory
correctly, assigns correct layers and projects, ignores non-Markdown files, and propagates
metadata correctly without needing to access the live filesystem during tests.
"""

import pytest
from pathlib import Path
from src.ingestion.manual_loader import discover_projects, load_manual_documents, ManualIngestionError
from src.models.document import Document


def test_discover_projects(tmp_path):
    """
    Verifies that discover_projects correctly scans the directory structure
    and identifies subdirectories as project names while ignoring root files.
    """
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    
    # Add project subdirectories
    (knowledge_dir / "talentforge").mkdir()
    (knowledge_dir / "n8n-aks-platform").mkdir()
    
    # Add files at the root (should not count as project directories)
    (knowledge_dir / "resume.md").write_text("resume", encoding="utf-8")
    
    projects = discover_projects(knowledge_dir)
    assert projects == ["n8n-aks-platform", "talentforge"]


def test_discover_projects_empty_or_missing(tmp_path):
    """
    Verifies that discover_projects handles non-existent or empty directories gracefully.
    """
    missing_dir = tmp_path / "missing"
    assert discover_projects(missing_dir) == []


def test_load_manual_documents_success(tmp_path):
    """
    Verifies correct load, recursive discovery, layer assignments, project assignments,
    ignoring unsupported file types, and metadata propagation.
    """
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    
    # 1. Root global identity files
    (knowledge_dir / "resume.md").write_text("Resume Content", encoding="utf-8")
    (knowledge_dir / "about-me.md").write_text("About Me Content", encoding="utf-8")
    (knowledge_dir / "faq.md").write_text("FAQ Content", encoding="utf-8")
    (knowledge_dir / "ignored_root.txt").write_text("Text file", encoding="utf-8")  # Unsupported extension
    
    # 2. Project subdirectory files
    project_dir = knowledge_dir / "talentforge"
    project_dir.mkdir()
    (project_dir / "architecture.md").write_text("Architecture Content", encoding="utf-8")
    (project_dir / "decisions.md").write_text("Decisions Content", encoding="utf-8")
    (project_dir / "challenges.md").write_text("Challenges Content", encoding="utf-8")
    (project_dir / "lessons-learned.md").write_text("Lessons Learned Content", encoding="utf-8")
    (project_dir / "ingest.yml").write_text("yaml content", encoding="utf-8")  # Unsupported extension
    
    # Nested folder under project
    nested_dir = project_dir / "nested"
    nested_dir.mkdir()
    (nested_dir / "deep_doc.md").write_text("Deep Markdown Content", encoding="utf-8")

    # Load manual documents for project "talentforge"
    documents = load_manual_documents("talentforge", knowledge_dir)
    
    # Counts validation:
    # Global identity files: resume.md, about-me.md, faq.md = 3
    # Project files: architecture.md, decisions.md, challenges.md, lessons-learned.md, nested/deep_doc.md = 5
    # Total = 8 documents (ignored_root.txt and ingest.yml are ignored)
    assert len(documents) == 8
    
    # Verify file types ignored
    unsupported_files = [doc for doc in documents if doc.source_file.endswith(".txt") or doc.source_file.endswith(".yml")]
    assert len(unsupported_files) == 0

    # Verify Project Assignment & Layer Mapping
    global_docs = [doc for doc in documents if doc.project == "__global__"]
    assert len(global_docs) == 3
    for doc in global_docs:
        assert doc.layer == "identity"
        assert doc.source_type == "manual"
        assert doc.source_file in ["resume.md", "about-me.md", "faq.md"]
        assert doc.metadata == {"source": "manual", "original_file": doc.source_file}
        
    project_docs = [doc for doc in documents if doc.project == "talentforge"]
    assert len(project_docs) == 5
    
    # Check specific project files
    for doc in project_docs:
        assert doc.source_type == "manual"
        assert doc.metadata == {"source": "manual", "original_file": doc.source_file}
        
        if doc.source_file == "talentforge/nested/deep_doc.md":
            # Any file not explicitly listed in DESIGN_FILES defaults to 'artifact' layer
            assert doc.layer == "artifact"
        else:
            assert doc.layer == "design"


def test_load_manual_documents_missing_directory(tmp_path):
    """
    Verifies that load_manual_documents raises a ManualIngestionError if the base path is invalid.
    """
    missing_dir = tmp_path / "missing"
    with pytest.raises(ManualIngestionError):
        load_manual_documents("talentforge", missing_dir)


def test_merge_github_and_manual_documents():
    """
    Verifies that GitHub documents and Manual documents can be merged
    cleanly into a single list of canonical Document objects.
    """
    github_docs = [
        Document(
            content="GH content 1",
            project="talentforge",
            layer="artifact",
            source_type="github",
            source_file="src/main.py"
        ),
        Document(
            content="GH content 2",
            project="talentforge",
            layer="artifact",
            source_type="github",
            source_file="src/utils.py"
        )
    ]
    
    manual_docs = [
        Document(
            content="Manual resume",
            project="__global__",
            layer="identity",
            source_type="manual",
            source_file="resume.md"
        ),
        Document(
            content="Manual architecture",
            project="talentforge",
            layer="design",
            source_type="manual",
            source_file="talentforge/architecture.md"
        )
    ]
    
    combined = github_docs + manual_docs
    assert len(combined) == 4
    assert combined[0].source_type == "github"
    assert combined[2].source_type == "manual"
    assert combined[2].project == "__global__"
    assert combined[3].project == "talentforge"
