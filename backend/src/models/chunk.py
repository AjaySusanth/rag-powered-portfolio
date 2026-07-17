"""
DESIGN DECISION:
This module defines the canonical Chunk model representing a processed slice of a
document. It inherits metadata from its parent Document and maps directly to the
downstream vector database representation.

We use a dataclass for a clean, lightweight in-memory representation.
Identifiers are computed deterministically using SHA-256 hashes to guarantee:
1. parent_document_id is stable based on the source_file path.
2. chunk_id is stable for a given file and index position to enable idempotent upserts.
3. content_hash is a separate field for change detection and cache invalidation.
"""

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Chunk:
    """
    Canonical chunk representation within the RAG pipeline.
    """

    chunk_id: str
    parent_document_id: str
    content_hash: str
    content: str
    project: str
    layer: str
    source_type: str
    source_file: str
    chunk_index: int
    token_count: int
    char_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


def generate_document_id(source_file: str) -> str:
    """
    Generates a deterministic document ID based on the source file path.
    """
    return hashlib.sha256(source_file.encode("utf-8")).hexdigest()


def generate_chunk_id(source_file: str, chunk_index: int) -> str:
    """
    Generates a deterministic chunk ID based on the source file path and chunk index.
    """
    return hashlib.sha256(f"{source_file}:{chunk_index}".encode("utf-8")).hexdigest()


def generate_content_hash(content: str) -> str:
    """
    Generates a deterministic content hash based on the chunk content.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
