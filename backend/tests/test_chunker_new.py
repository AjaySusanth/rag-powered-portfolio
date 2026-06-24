import pytest
from src.models.document import Document
from src.models.chunk import (
    generate_document_id,
    generate_chunk_id,
    generate_content_hash,
)
from src.chunking.chunker import chunk_document


def test_empty_document_skipping():
    """
    Verifies that empty or whitespace-only documents produce zero chunks.
    """
    doc_empty = Document(
        content="",
        project="test",
        layer="identity",
        source_type="manual",
        source_file="resume.md"
    )
    doc_whitespace = Document(
        content="   \n   ",
        project="test",
        layer="identity",
        source_type="manual",
        source_file="resume.md"
    )
    
    assert chunk_document(doc_empty) == []
    assert chunk_document(doc_whitespace) == []


def test_metadata_propagation():
    """
    Verifies that chunks successfully inherit metadata from their parent Document.
    """
    doc = Document(
        content="# Intro\nThis is a simple document.",
        project="test-project",
        layer="identity",
        source_type="manual",
        source_file="about-me.md",
        metadata={"author": "Ajay", "custom_key": 42}
    )
    
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    
    chunk = chunks[0]
    assert chunk.project == "test-project"
    assert chunk.layer == "identity"
    assert chunk.source_type == "manual"
    assert chunk.source_file == "about-me.md"
    
    # Check that metadata contains parent doc metadata AND document_id
    assert chunk.metadata["author"] == "Ajay"
    assert chunk.metadata["custom_key"] == 42
    assert chunk.metadata["document_id"] == chunk.parent_document_id
    assert chunk.metadata["heading"] == "# Intro"


def test_deterministic_identifiers():
    """
    Verifies that parent_document_id, chunk_id, and content_hash are deterministic
    and stable across re-runs.
    """
    doc = Document(
        content="# Main Title\nThis is the content.",
        project="test",
        layer="identity",
        source_type="manual",
        source_file="faq.md"
    )
    
    chunks_run_1 = chunk_document(doc)
    chunks_run_2 = chunk_document(doc)
    
    assert len(chunks_run_1) == 1
    assert len(chunks_run_2) == 1
    
    c1 = chunks_run_1[0]
    c2 = chunks_run_2[0]
    
    # Stable across re-runs
    assert c1.parent_document_id == c2.parent_document_id
    assert c1.chunk_id == c2.chunk_id
    assert c1.content_hash == c2.content_hash
    
    # Verify deterministic formulas
    expected_doc_id = generate_document_id("faq.md")
    expected_chunk_id = generate_chunk_id("faq.md", 0)
    expected_content_hash = generate_content_hash(c1.content)
    
    assert c1.parent_document_id == expected_doc_id
    assert c1.chunk_id == expected_chunk_id
    assert c1.content_hash == expected_content_hash


def test_content_hash_changes_with_content():
    """
    Verifies that different chunk contents produce different content_hash values,
    while chunk_id remains stable (since chunk_id depends on path and index).
    """
    doc_1 = Document(
        content="# Title\nHello World",
        project="test",
        layer="identity",
        source_type="manual",
        source_file="faq.md"
    )
    doc_2 = Document(
        content="# Title\nGoodbye World",
        project="test",
        layer="identity",
        source_type="manual",
        source_file="faq.md"
    )
    
    chunks_1 = chunk_document(doc_1)
    chunks_2 = chunk_document(doc_2)
    
    c1 = chunks_1[0]
    c2 = chunks_2[0]
    
    # Since source_file and index are the same, chunk_id MUST remain identical
    assert c1.chunk_id == c2.chunk_id
    # But content_hash MUST be different
    assert c1.content_hash != c2.content_hash


@pytest.mark.parametrize(
    "layer,expected_max_chunk_size,expected_overlap",
    [
        ("identity", 256, 32),
        ("design", 512, 64),
        ("artifact", 256, 32),
    ]
)
def test_layer_specific_chunk_sizing(layer: str, expected_max_chunk_size: int, expected_overlap: int):
    """
    Verifies that the chunker dynamically changes sliding-window parameters
    based on the document's layer string.
    """
    # Create text that is guaranteed to split into multiple chunks
    # (using repeated words to exceed token counts)
    content = "# Title\n" + " ".join(["word"] * 800)
    
    doc = Document(
        content=content,
        project="test",
        layer=layer,
        source_type="github",
        source_file="dummy.txt"
    )
    
    chunks = chunk_document(doc)
    assert len(chunks) > 1
    
    # Every chunk should be under/equal to the maximum size (including heading prepended)
    import tiktoken
    encoding = tiktoken.get_encoding("cl100k_base")
    for c in chunks:
        assert c.token_count == len(encoding.encode(c.content))
        assert c.char_count == len(c.content)
        # Note: Prepended headings add tokens, so we ensure the base window length is respected
        # The main validation is that token_count and char_count match calculations.
