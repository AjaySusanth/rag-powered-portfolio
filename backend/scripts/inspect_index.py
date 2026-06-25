"""
DESIGN DECISION:
This script queries the canonical chunks table to inspect vector store metrics.
It prints aggregated database statistics, including:
1. Total vectors stored.
2. Vector count breakdown by project.
3. Vector count breakdown by layer.
4. Embedding dimensions (retrieved via pgvector's vector_dims helper).
5. A comprehensive preview of a sample stored chunk, including its metadata
   and a truncated list of its embedding floats.
"""

import sys
import asyncio
from pathlib import Path

# Resolve workspace paths
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.db.core import get_db_pool


async def main() -> None:
    try:
        pool = await get_db_pool()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)

    async with pool.acquire() as conn:
        # 1. Total vectors
        total_vectors = await conn.fetchval("SELECT COUNT(*) FROM chunks;")
        if total_vectors == 0:
            print("Vector store is empty.")
            sys.exit(0)

        # 2. Vectors by project
        project_rows = await conn.fetch(
            "SELECT project, COUNT(*) as cnt FROM chunks GROUP BY project ORDER BY cnt DESC;"
        )

        # 3. Vectors by layer
        layer_rows = await conn.fetch(
            "SELECT layer, COUNT(*) as cnt FROM chunks GROUP BY layer ORDER BY cnt DESC;"
        )

        # 4. Embedding dimensions
        emb_dim = await conn.fetchval(
            "SELECT vector_dims(embedding) FROM chunks LIMIT 1;"
        )

        # 5. Fetch a sample stored chunk
        sample_row = await conn.fetchrow(
            "SELECT chunk_id, parent_document_id, project, layer, source_type, source_file, "
            "chunk_index, content, content_hash, token_count, char_count, metadata, "
            "embedding::text as emb_text "
            "FROM chunks LIMIT 1;"
        )

    print("=== Vector Store Index Report ===\n")
    print(f"Total vectors: {total_vectors}")
    print(f"Embedding dimensions: {emb_dim}\n")

    print("Vectors by project:")
    for r in project_rows:
        print(f"  - {r['project']}: {r['cnt']}")
    print()

    print("Vectors by layer:")
    for r in layer_rows:
        print(f"  - {r['layer']}: {r['cnt']}")
    print()

    if sample_row:
        print("Sample stored chunk preview:")
        print("-" * 60)
        print(f"Chunk ID: {sample_row['chunk_id']}")
        print(f"Parent Document ID: {sample_row['parent_document_id']}")
        print(f"Content Hash: {sample_row['content_hash']}")
        print(f"Source File: {sample_row['source_file']} (Index {sample_row['chunk_index']})")
        print(f"Project: {sample_row['project']} | Layer: {sample_row['layer']} | Type: {sample_row['source_type']}")
        print(f"Tokens: {sample_row['token_count']} | Characters: {sample_row['char_count']}")
        print(f"Metadata: {sample_row['metadata']}")
        
        # Parse embedding string format "[x, y, z...]" and show first 5 dims
        emb_str = sample_row['emb_text'].strip("[]")
        emb_floats = [float(x) for x in emb_str.split(",") if x.strip()]
        preview_dims = emb_floats[:5]
        print(f"Embedding preview (first 5 dimensions): {preview_dims}...")
        print("-" * 60)
        preview_len = 300
        snippet = sample_row['content'][:preview_len]
        print(snippet)
        if len(sample_row['content']) > preview_len:
            print("...")
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
