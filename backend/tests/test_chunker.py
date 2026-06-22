import os
from pathlib import Path
import pytest
from src.ingestion.chunker import (
    DocumentLayer,
    chunk_text,
    strip_html_comments,
)

# Base path relative to test file location (backend/tests/test_chunker.py)
WORKSPACE_ROOT = Path(__file__).parent.parent.parent


def test_strip_html_comments():
    """
    Verifies that HTML comment blocks are correctly stripped from raw text,
    while non-comment content and styling markdown remain untouched.
    """
    raw_text = (
        "<!-- This is a comment that should be stripped -->\n"
        "# Title\n"
        "Some standard paragraph text.\n"
        "<!-- Another nested \n"
        "multi-line comment -->\n"
        "Footer text."
    )
    expected = (
        "\n"
        "# Title\n"
        "Some standard paragraph text.\n\n"
        "Footer text."
    )
    assert strip_html_comments(raw_text) == expected


def test_chunk_text_empty():
    """
    Verifies that empty strings or strings containing only HTML comments 
    return an empty list of chunks.
    """
    assert chunk_text("", DocumentLayer.IDENTITY) == []
    assert chunk_text("<!-- comment -->", DocumentLayer.IDENTITY) == []
    assert chunk_text("   \n   ", DocumentLayer.IDENTITY) == []


def test_chunking_logic_layer_1():
    """
    Verifies that Layer 1 chunking (256 chunk size, 32 overlap) 
    applies the sliding window correctly.
    """
    # Create a string with exactly 300 words to ensure it splits into at least 2 chunks
    words = ["word"] * 300
    text = " ".join(words)
    
    chunks = chunk_text(text, DocumentLayer.IDENTITY)
    
    assert len(chunks) > 1
    # Verify Pydantic structure
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_index == idx
        assert chunk.token_count <= 256
        assert len(chunk.content) > 0


def test_resume_chunking_integration():
    """
    Integration test reading the actual knowledge/resume.md file
    and verifying the Layer 1 chunking behavior.
    """
    resume_path = WORKSPACE_ROOT / "knowledge" / "resume.md"
    assert resume_path.exists(), f"resume.md not found at {resume_path}"
    
    with open(resume_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    chunks = chunk_text(content, DocumentLayer.IDENTITY)
    
    # Check that comments are removed from output
    for chunk in chunks:
        assert "DESIGN DECISION" not in chunk.content
        assert "<!--" not in chunk.content
        assert "-->" not in chunk.content
        assert chunk.token_count <= 256
        
    assert len(chunks) > 0


def test_decisions_chunking_integration():
    """
    Integration test reading the actual reservation-system decisions.md file
    and verifying the Layer 2 chunking behavior.
    """
    decisions_path = WORKSPACE_ROOT / "knowledge" / "reservation-system" / "decisions.md"
    assert decisions_path.exists(), f"decisions.md not found at {decisions_path}"
    
    with open(decisions_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    chunks = chunk_text(content, DocumentLayer.DESIGN)
    
    # Verify Layer 2 constraint checks
    for chunk in chunks:
        assert "DESIGN DECISION" not in chunk.content
        assert "<!--" not in chunk.content
        assert chunk.token_count <= 512
        
    # Check for sliding window overlap by verifying that some text from the 
    # end of chunk 0 appears at the start of chunk 1 (if there are multiple chunks)
    if len(chunks) > 1:
        c0_words = chunks[0].content.split()
        c1_words = chunks[1].content.split()
        # Ensure there is some overlap in word content
        common_words = set(c0_words) & set(c1_words)
        assert len(common_words) > 0
