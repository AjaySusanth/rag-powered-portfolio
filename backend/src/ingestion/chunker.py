"""
DESIGN DECISION:
This module implements heading-aware document chunking for the RAG ingestion pipeline.

The strategy is a two-pass approach:
  Pass 1 — Split the cleaned document at every Markdown heading line (# / ## / ###).
            Each heading + its body text becomes a discrete "section".
  Pass 2 — Token-chunk each section independently using a sliding window scoped to
            that section. This guarantees that a chunk never crosses a heading boundary,
            so every retrieved chunk knows exactly which topic it belongs to.

Why heading-aware over pure sliding-window:
  Pure sliding-window splits mechanically every N tokens. It can sever a heading from
  its explanation or merge two unrelated topics into one chunk, degrading retrieval
  precision. Heading-aware chunking aligns chunk boundaries with the document's own
  semantic structure — a natural fit for well-structured Markdown like our Layer 1/2 docs.

Edge-case rules:
  - Oversized sections  → internal sliding window, heading prepended to every sub-chunk.
  - Undersized sections → standalone chunk (no merging). Exception: if the section body
                          is under MIN_SECTION_BODY_TOKENS AND a previous chunk exists,
                          the heading+body is appended to the previous chunk's content
                          to avoid polluting the vector space with near-empty embeddings.
                          If it is the FIRST section and undersized, emit it as-is.

  MIN_SECTION_BODY_TOKENS = 20  (a conservative default — not empirically tuned against
  real content yet; revisit once placeholder text is replaced with real project details.)
"""

import re
from enum import IntEnum
from typing import List, Optional
import tiktoken
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum token count for a section's body text (excluding the heading itself)
# before it gets folded into the previous chunk rather than emitted standalone.
# TODO: revisit once placeholder content in knowledge/ is replaced with real data.
MIN_SECTION_BODY_TOKENS: int = 20


# ---------------------------------------------------------------------------
# Enums & Configs
# ---------------------------------------------------------------------------

class DocumentLayer(IntEnum):
    """
    Specifies the document knowledge layer per Section 3.1 of the PRD.

    Layer 1: Identity documents (resume, faq, about-me)          — 256 tokens, 32 overlap
    Layer 2: Manual project design docs (architecture, decisions) — 512 tokens, 64 overlap
    Layer 3: Auto-ingested source code artifacts                  — 256 tokens, 32 overlap
    """
    IDENTITY = 1
    DESIGN = 2
    ARTIFACT = 3


class LayerConfig(BaseModel):
    """Configuration parameters for a specific document layer's chunking behavior."""
    chunk_size: int = Field(description="Max tokens allowed per chunk")
    overlap: int = Field(description="Token overlap between consecutive chunks")


# Global mapping of layer properties as defined in Section 3.1 & 4.2 of the PRD.
LAYER_CONFIGS: dict[DocumentLayer, LayerConfig] = {
    DocumentLayer.IDENTITY: LayerConfig(chunk_size=256, overlap=32),
    DocumentLayer.DESIGN:   LayerConfig(chunk_size=512, overlap=64),
    DocumentLayer.ARTIFACT: LayerConfig(chunk_size=256, overlap=32),
}


# ---------------------------------------------------------------------------
# Output Schema
# ---------------------------------------------------------------------------

class DocumentChunk(BaseModel):
    """Pydantic schema representing a single structured chunk of a document."""
    content: str = Field(description="The decoded string content of the chunk")
    token_count: int = Field(description="The number of tokens within this chunk")
    chunk_index: int = Field(description="The zero-indexed positional index of this chunk")
    heading: Optional[str] = Field(
        default=None,
        description="The Markdown heading of the section this chunk belongs to, if any"
    )


# ---------------------------------------------------------------------------
# Internal Data Structures
# ---------------------------------------------------------------------------

class _Section(BaseModel):
    """Internal representation of a heading + body pair after the first pass split."""
    heading: Optional[str]
    body: str


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def strip_html_comments(text: str) -> str:
    """
    Removes HTML and Markdown comment blocks (<!-- ... -->) from a raw string.

    Why: Internal RAG design comments are useful to human editors reading the raw file,
    but they waste token quota and pollute the embedding vector space if ingested.
    """
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


# ---------------------------------------------------------------------------
# Pass 1 — Heading Splitter
# ---------------------------------------------------------------------------

def _split_by_headings(text: str) -> List[_Section]:
    """
    Splits a Markdown document into sections at heading lines (# / ## / ###).

    Each section carries the heading that introduced it and all body text up to
    the next heading. Text before the first heading (if any) is captured as a
    headingless section so no content is silently dropped.

    Why regex split on heading lines:
      re.split with a capture group on the heading pattern preserves the heading
      text itself as elements in the result list, making it trivial to pair each
      heading with its following body without a second scan.
    """
    # Pattern matches any line starting with 1-3 '#' characters
    heading_pattern = re.compile(r"(^#{1,3} .+$)", re.MULTILINE)
    parts = heading_pattern.split(text)

    sections: List[_Section] = []

    # parts alternates: [pre-heading-text, heading, body, heading, body, ...]
    # The first element is always the text before the first heading (may be empty).
    pre_heading_text = parts[0].strip()
    if pre_heading_text:
        sections.append(_Section(heading=None, body=pre_heading_text))

    # Iterate over (heading, body) pairs
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i].strip()
        body = parts[i + 1].strip() if (i + 1) < len(parts) else ""
        sections.append(_Section(heading=heading, body=body))

    return sections


# ---------------------------------------------------------------------------
# Pass 2 — Token-level sliding window (scoped to one section)
# ---------------------------------------------------------------------------

def _sliding_window(
    text: str,
    heading: Optional[str],
    config: LayerConfig,
    encoding: tiktoken.Encoding,
    start_index: int,
) -> List[DocumentChunk]:
    """
    Applies a sliding-window token chunker to a single section's text.

    The heading is prepended to every sub-chunk produced from this section so
    that each chunk is self-contained and carries its topic context even when
    the section is split across multiple windows.

    Concept — sliding window:
      Step forward by (chunk_size - overlap) tokens on each iteration. The
      overlapping tail of the previous window becomes the leading context of
      the next window, preventing hard topic cuts at arbitrary token boundaries.
    """
    tokens = encoding.encode(text)
    chunk_size = config.chunk_size
    overlap = config.overlap
    chunks: List[DocumentChunk] = []

    i = 0
    local_index = 0

    while i < len(tokens):
        window_tokens = tokens[i : i + chunk_size]
        decoded = encoding.decode(window_tokens)

        # Prepend heading to every sub-chunk so it is self-contained
        content = f"{heading}\n\n{decoded}" if heading else decoded

        chunks.append(DocumentChunk(
            content=content,
            token_count=len(encoding.encode(content)),
            chunk_index=start_index + local_index,
            heading=heading,
        ))

        if i + chunk_size >= len(tokens):
            break

        step = max(1, chunk_size - overlap)
        i += step
        local_index += 1

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_text(text: str, layer: DocumentLayer) -> List[DocumentChunk]:
    """
    Converts a raw Markdown document into a list of structured, overlapping chunks.

    Two-pass strategy:
      Pass 1: strip_html_comments → _split_by_headings
              Produces a list of (heading, body) sections.
      Pass 2: For each section, apply _sliding_window scoped to that section's tokens.
              This ensures chunks never cross heading boundaries.

    Edge cases handled:
      - Oversized section  → internal sliding window, heading prepended to each sub-chunk.
      - Undersized section → standalone chunk. If body < MIN_SECTION_BODY_TOKENS AND a
                             previous chunk exists, fold into the previous chunk's content.
                             If it is the first section and undersized, emit standalone.
    """
    clean_text = strip_html_comments(text)

    if not clean_text.strip():
        return []

    encoding = tiktoken.get_encoding("cl100k_base")
    config = LAYER_CONFIGS[layer]
    sections = _split_by_headings(clean_text)

    chunks: List[DocumentChunk] = []

    for section in sections:
        heading = section.heading
        body = section.body

        if not body.strip():
            # Heading with zero body — emit a single chunk for the heading alone
            # so the section title is still present in the knowledge base.
            if heading:
                chunks.append(DocumentChunk(
                    content=heading,
                    token_count=len(encoding.encode(heading)),
                    chunk_index=len(chunks),
                    heading=heading,
                ))
            continue

        body_tokens = len(encoding.encode(body))

        # --- Undersized section guard ---
        # If the section body is below the minimum threshold AND there is a
        # previous chunk to merge into, fold the content in rather than emitting
        # a near-empty standalone chunk that would embed poorly.
        if body_tokens < MIN_SECTION_BODY_TOKENS and chunks:
            appended = f"\n\n{heading}\n\n{body}" if heading else f"\n\n{body}"
            last = chunks[-1]
            new_content = last.content + appended
            chunks[-1] = DocumentChunk(
                content=new_content,
                token_count=len(encoding.encode(new_content)),
                chunk_index=last.chunk_index,
                heading=last.heading,  # keep the original section's heading
            )
            continue

        # --- Normal / oversized section → sliding window ---
        new_chunks = _sliding_window(
            text=body,
            heading=heading,
            config=config,
            encoding=encoding,
            start_index=len(chunks),
        )
        chunks.extend(new_chunks)

    return chunks
