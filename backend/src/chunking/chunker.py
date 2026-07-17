"""
DESIGN DECISION & REFINEMENT (JULY 2026):
This module implements the canonical layer-aware document chunking service.
It takes a Document object and splits it into a list of Chunk objects using a
two-pass heading-aware strategy:
  Pass 1 — Split the cleaned document at every Markdown heading line (# / ## / ###)
            so that chunks align with the document's native semantic sections.
  Pass 2 — Track active headings using a stack to construct a fully qualified
            hierarchical path prefix. Pop siblings/sub-siblings as we navigate,
            avoiding sibling merge pollution. Do not emit standalone chunks for
            empty headings; instead, carry them forward to the next non-empty
            section as hierarchical context prepended to each sub-chunk.
  Pass 3 — Token-chunk each section independently using a sliding window. This
            guarantees that chunks never cross heading boundaries, and the
            hierarchical path is prepended to each sub-chunk to preserve context.

Layer configs (chunk_size and overlap) are dynamically looked up based on the
Document's layer string ('identity'/'artifact' = 256/32, 'design' = 512/64).
Deterministic SHA-256 IDs are generated to support idempotent upserts in the database.
"""

import re
from typing import Dict, List, Optional

import tiktoken
from pydantic import BaseModel, Field

from src.models.chunk import (
    Chunk,
    generate_chunk_id,
    generate_content_hash,
    generate_document_id,
)
from src.models.document import Document

# Minimum token count for a section's body text (excluding the heading itself)
# before it gets folded into the previous chunk rather than emitted standalone.
MIN_SECTION_BODY_TOKENS: int = 20


class LayerConfig(BaseModel):
    """Configuration parameters for a specific document layer's chunking behavior."""

    chunk_size: int = Field(description="Max tokens allowed per chunk")
    overlap: int = Field(description="Token overlap between consecutive chunks")


# Config mapping based on Section 3.1 & 4.2 of the PRD
LAYER_CONFIGS: Dict[str, LayerConfig] = {
    "identity": LayerConfig(chunk_size=256, overlap=32),
    "design": LayerConfig(chunk_size=512, overlap=64),
    "artifact": LayerConfig(chunk_size=256, overlap=32),
}


class _Section(BaseModel):
    """Internal representation of a heading + body pair after the first pass split."""

    heading: Optional[str]
    body: str


def strip_html_comments(text: str) -> str:
    """
    Removes HTML and Markdown comment blocks (<!-- ... -->) from a raw string.
    """
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _split_by_headings(text: str) -> List[_Section]:
    """
    Splits a Markdown document into sections at heading lines (# / ## / ###).
    """
    # Pattern matches any line starting with 1-3 '#' characters
    heading_pattern = re.compile(r"(^#{1,3} .+$)", re.MULTILINE)
    parts = heading_pattern.split(text)

    sections: List[_Section] = []

    # parts alternates: [pre-heading-text, heading, body, heading, body, ...]
    pre_heading_text = parts[0].strip()
    if pre_heading_text:
        sections.append(_Section(heading=None, body=pre_heading_text))

    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if (i + 1) < len(parts) else ""
        sections.append(_Section(heading=heading, body=body))

    return sections


class _RawChunk(BaseModel):
    """Temporary struct to hold chunked text content and heading before mapping to Chunk model."""

    content: str
    heading: Optional[str]


def _sliding_window(
    text: str,
    heading: Optional[str],
    config: LayerConfig,
    encoding: tiktoken.Encoding,
) -> List[_RawChunk]:
    """
    Applies sliding-window token chunking to a single section's text.
    """
    tokens = encoding.encode(text)
    chunk_size = config.chunk_size
    overlap = config.overlap
    raw_chunks: List[_RawChunk] = []

    i = 0
    while i < len(tokens):
        window_tokens = tokens[i : i + chunk_size]
        decoded = encoding.decode(window_tokens)

        # Prepend heading to every sub-chunk so it is self-contained
        content = f"{heading}\n\n{decoded}" if heading else decoded
        raw_chunks.append(_RawChunk(content=content, heading=heading))

        if i + chunk_size >= len(tokens):
            break

        step = max(1, chunk_size - overlap)
        i += step

    return raw_chunks


def chunk_document(doc: Document) -> List[Chunk]:
    """
    Converts a Document into a list of structured, overlapping Chunks.

    This function:
      1. Skips empty documents.
      2. Dynamically loads the layer configuration.
      3. Performs heading-aware splitting and token sliding-window.
      4. Propagates metadata and generates stable deterministic IDs.
    """
    clean_text = strip_html_comments(doc.content)

    if not clean_text.strip():
        return []

    # Retrieve layer configuration, defaulting to 'artifact' if layer is unknown
    layer_name = doc.layer.lower()
    config = LAYER_CONFIGS.get(layer_name, LAYER_CONFIGS["artifact"])

    encoding = tiktoken.get_encoding("cl100k_base")
    sections = _split_by_headings(clean_text)

    raw_chunks: List[_RawChunk] = []
    # Track the active heading path (stack of tuples: (level, heading_text))
    heading_stack: List[tuple] = []

    for section in sections:
        heading = section.heading
        body = section.body

        if heading:
            # Determine heading level by counting leading '#'
            level_match = re.match(r"^(#{1,3})\s", heading)
            level = len(level_match.group(1)) if level_match else 1

            # Pop headings that are siblings or deeper (level >= current level)
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()

            # Push the current heading to the stack
            heading_stack.append((level, heading))
        else:
            # No heading (e.g. pre-heading content), clear the active stack
            heading_stack = []

        if not body.strip():
            # Skip emitting chunks for empty/header-only sections
            continue

        # Construct full hierarchical prefix from the active heading stack
        full_heading = "\n".join(h[1] for h in heading_stack) if heading_stack else None
        body_tokens = len(encoding.encode(body))

        # Undersized section guard: fold into the previous chunk if it exists
        if body_tokens < MIN_SECTION_BODY_TOKENS and raw_chunks:
            appended_heading = full_heading if full_heading else ""
            appended = f"\n\n{appended_heading}\n\n{body}" if appended_heading else f"\n\n{body}"
            last = raw_chunks[-1]
            raw_chunks[-1] = _RawChunk(content=last.content + appended, heading=last.heading)
            continue

        # Normal/oversized section: run sliding window
        section_chunks = _sliding_window(
            text=body,
            heading=full_heading,
            config=config,
            encoding=encoding,
        )
        raw_chunks.extend(section_chunks)

    # Now, transform raw chunks into the canonical Chunk model
    parent_doc_id = generate_document_id(doc.source_file)
    chunks: List[Chunk] = []

    for idx, raw_c in enumerate(raw_chunks):
        chunk_id = generate_chunk_id(doc.source_file, idx)
        content_hash = generate_content_hash(raw_c.content)
        token_count = len(encoding.encode(raw_c.content))
        char_count = len(raw_c.content)

        # Build chunk-specific metadata, merging parent doc metadata
        chunk_metadata = doc.metadata.copy()
        chunk_metadata["document_id"] = parent_doc_id
        if raw_c.heading:
            chunk_metadata["heading"] = raw_c.heading

        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                parent_document_id=parent_doc_id,
                content_hash=content_hash,
                content=raw_c.content,
                project=doc.project,
                layer=doc.layer,
                source_type=doc.source_type,
                source_file=doc.source_file,
                chunk_index=idx,
                token_count=token_count,
                char_count=char_count,
                metadata=chunk_metadata,
            )
        )

    return chunks
