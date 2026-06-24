import pytest
from pathlib import Path
from src.ingestion.chunker import (
    DocumentLayer,
    DocumentChunk,
    chunk_text,
    strip_html_comments,
    _split_by_headings,
    MIN_SECTION_BODY_TOKENS,
)

WORKSPACE_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# strip_html_comments
# ---------------------------------------------------------------------------

def test_strip_html_comments():
    """Verifies that HTML comment blocks are stripped while non-comment content remains."""
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


# ---------------------------------------------------------------------------
# chunk_text — basic guards
# ---------------------------------------------------------------------------

def test_chunk_text_empty():
    """Empty strings or comment-only strings return an empty chunk list."""
    assert chunk_text("", DocumentLayer.IDENTITY) == []
    assert chunk_text("<!-- comment -->", DocumentLayer.IDENTITY) == []
    assert chunk_text("   \n   ", DocumentLayer.IDENTITY) == []


# ---------------------------------------------------------------------------
# _split_by_headings
# ---------------------------------------------------------------------------

def test_split_by_headings_basic():
    """Verifies that headings correctly delimit sections."""
    text = "## Section A\nContent A.\n\n## Section B\nContent B."
    sections = _split_by_headings(text)
    assert len(sections) == 2
    assert sections[0].heading == "## Section A"
    assert "Content A" in sections[0].body
    assert sections[1].heading == "## Section B"
    assert "Content B" in sections[1].body


def test_split_by_headings_pre_heading_text():
    """Text before the first heading is captured as a headingless section."""
    text = "Preamble text.\n\n## First Heading\nBody here."
    sections = _split_by_headings(text)
    assert len(sections) == 2
    assert sections[0].heading is None
    assert "Preamble text" in sections[0].body
    assert sections[1].heading == "## First Heading"


def test_split_by_headings_no_headings():
    """A document with no Markdown headings is returned as a single headingless section."""
    text = "Just some plain text with no headings at all."
    sections = _split_by_headings(text)
    assert len(sections) == 1
    assert sections[0].heading is None
    assert "plain text" in sections[0].body


# ---------------------------------------------------------------------------
# heading field on DocumentChunk
# ---------------------------------------------------------------------------

def test_chunk_heading_field_populated():
    """Every chunk produced from a section must carry the section's heading."""
    text = "## Why PostgreSQL\nPostgreSQL provides ACID compliance and transactional integrity."
    chunks = chunk_text(text, DocumentLayer.DESIGN)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.heading == "## Why PostgreSQL"


def test_chunk_heading_in_content():
    """The heading must be prepended into every chunk's content string."""
    text = "## Why Redis\nRedis is used as the in-memory cache layer for fast key-value lookups."
    chunks = chunk_text(text, DocumentLayer.IDENTITY)
    for chunk in chunks:
        assert "## Why Redis" in chunk.content


# ---------------------------------------------------------------------------
# Oversized section — internal sliding window
# ---------------------------------------------------------------------------

def test_oversized_section_produces_multiple_chunks():
    """
    A section whose body exceeds the layer token limit must be split into
    multiple chunks via the internal sliding window. Every sub-chunk must
    carry the section heading.
    """
    # Build a body that is clearly > 256 tokens (Layer 1 limit)
    body = " ".join(["oversized"] * 300)
    text = f"## Large Section\n{body}"
    chunks = chunk_text(text, DocumentLayer.IDENTITY)

    assert len(chunks) > 1, "Oversized section must produce more than one chunk"
    for chunk in chunks:
        assert chunk.heading == "## Large Section"
        assert "## Large Section" in chunk.content
        assert chunk.token_count <= 256 + 20  # small tolerance for heading prepend


# ---------------------------------------------------------------------------
# Undersized section — merge / emit rules
# ---------------------------------------------------------------------------

def test_undersized_section_merged_into_previous():
    """
    A section whose body is under MIN_SECTION_BODY_TOKENS and has a previous
    chunk must be folded into that previous chunk, not emitted standalone.
    """
    # First section is normal-sized; second is tiny
    normal_body = " ".join(["word"] * 50)
    tiny_body = "Tiny."  # clearly under 20 tokens
    text = f"## Normal Section\n{normal_body}\n\n## Tiny Section\n{tiny_body}"

    chunks = chunk_text(text, DocumentLayer.IDENTITY)

    # The tiny section should be merged — we expect only 1 chunk
    assert len(chunks) == 1
    # The tiny content should appear in the merged chunk
    assert "Tiny." in chunks[0].content
    assert "Tiny Section" in chunks[0].content


def test_undersized_first_section_emitted_standalone():
    """
    An undersized FIRST section (no previous chunk to merge into) must be
    emitted as a standalone chunk — content must not be silently dropped.
    """
    tiny_body = "Short."  # clearly under 20 tokens
    text = f"## First Section\n{tiny_body}"

    chunks = chunk_text(text, DocumentLayer.IDENTITY)

    assert len(chunks) == 1
    assert "Short." in chunks[0].content
    assert chunks[0].heading == "## First Section"


# ---------------------------------------------------------------------------
# Integration — layer 1: resume.md
# ---------------------------------------------------------------------------

def test_resume_integration_layer1():
    """
    Integration test against the live knowledge/resume.md.
    Validates: comment stripping, token limits, heading field presence.
    """
    path = WORKSPACE_ROOT / "knowledge" / "resume.md"
    assert path.exists(), f"resume.md not found at {path}"

    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text, DocumentLayer.IDENTITY)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "<!--" not in chunk.content
        assert "DESIGN DECISION" not in chunk.content
        assert chunk.token_count <= 256 + 20  # tolerance for heading prepend


# ---------------------------------------------------------------------------
# Integration — layer 2: decisions.md
# ---------------------------------------------------------------------------

def test_decisions_integration_layer2():
    """
    Integration test against the live knowledge/talentforge/decisions.md.
    Validates: Layer 2 token limits, heading isolation, comment stripping.
    """
    path = WORKSPACE_ROOT / "knowledge" / "talentforge" / "decisions.md"
    assert path.exists(), f"decisions.md not found at {path}"

    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text, DocumentLayer.DESIGN)

    assert len(chunks) > 0
    for chunk in chunks:
        assert "<!--" not in chunk.content
        assert chunk.token_count <= 512 + 30  # tolerance for heading prepend

    # Each chunk should carry the heading of its originating section
    headings_found = {c.heading for c in chunks if c.heading}
    assert len(headings_found) > 1, "Multiple decision sections should yield multiple distinct headings"
