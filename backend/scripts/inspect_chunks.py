"""
DESIGN DECISION:
This inspection script verifies the Layer-Aware Chunking Pipeline.
It parses the project name, reads the corresponding ingest.yml, fetches Documents
from GitHub, transforms them into Chunk objects using the chunker, and prints
aggregated statistics.

It calculates and displays the total number of documents, total chunks, chunk counts
broken down by layer, average chunk size in tokens/characters, the largest chunk,
and a preview snippet of a sample chunk.
"""

import sys
import asyncio
from pathlib import Path
from collections import Counter

# Programmatically resolve workspace paths so import works from anywhere
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.ingestion.github_fetcher import fetch_github_repository
from src.chunking.chunker import chunk_document


async def main() -> None:
    if len(sys.argv) < 2:
        print("Error: Missing project name argument.")
        print("Usage: python scripts/inspect_chunks.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1].strip().lower()
    yaml_path = PROJECT_ROOT / "knowledge" / project_name / "ingest.yml"

    if not yaml_path.exists():
        print(f"Error: ingest.yml not found at {yaml_path}")
        sys.exit(1)

    print(f"Project: {project_name}\n")
    print(f"Fetching and chunking documents using {yaml_path.name}...\n")

    try:
        documents = await fetch_github_repository(str(yaml_path))
    except Exception as e:
        print(f"Failed to fetch documents: {e}")
        sys.exit(1)

    total_docs = len(documents)
    all_chunks = []

    # Skip empty documents is handled by chunk_document returning []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    total_chunks = len(all_chunks)

    if total_chunks == 0:
        print(f"No chunks produced for project '{project_name}'.")
        print(f"Total documents: {total_docs}")
        print("Total chunks: 0")
        sys.exit(0)

    # Calculate statistics
    layers_counter = Counter(c.layer for c in all_chunks)
    avg_tokens = sum(c.token_count for c in all_chunks) / total_chunks
    avg_chars = sum(c.char_count for c in all_chunks) / total_chunks
    
    largest_chunk_by_tokens = max(all_chunks, key=lambda c: c.token_count)
    largest_chunk_by_chars = max(all_chunks, key=lambda c: c.char_count)

    print(f"Total documents: {total_docs}")
    print(f"Total chunks: {total_chunks}\n")

    print("Chunks by layer:")
    for layer, count in layers_counter.items():
        print(f"  - {layer}: {count}")
    print()

    print(f"Average chunk size: {avg_tokens:.1f} tokens ({avg_chars:.1f} characters)")
    print(f"Largest chunk (by tokens): {largest_chunk_by_tokens.token_count} tokens in {largest_chunk_by_tokens.source_file} (Index {largest_chunk_by_tokens.chunk_index})")
    print(f"Largest chunk (by characters): {largest_chunk_by_chars.char_count} characters in {largest_chunk_by_chars.source_file} (Index {largest_chunk_by_chars.chunk_index})\n")

    # Sample chunk preview
    sample_chunk = all_chunks[0]
    print("Sample chunk preview:")
    print("-" * 50)
    print(f"Chunk ID: {sample_chunk.chunk_id}")
    print(f"Parent Document ID: {sample_chunk.parent_document_id}")
    print(f"Content Hash: {sample_chunk.content_hash}")
    print(f"Source File: {sample_chunk.source_file} (Index {sample_chunk.chunk_index})")
    print(f"Layer: {sample_chunk.layer} | Type: {sample_chunk.source_type}")
    print(f"Tokens: {sample_chunk.token_count} | Characters: {sample_chunk.char_count}")
    print(f"Metadata: {sample_chunk.metadata}")
    print("-" * 50)
    # Print preview snippet of content
    preview_len = 300
    snippet = sample_chunk.content[:preview_len]
    print(snippet)
    if len(sample_chunk.content) > preview_len:
        print("...")
    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
