import asyncio
import sys
from pathlib import Path

# Resolve workspace paths
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.db.core import get_db_pool

async def main():
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT project, source_file, layer, source_type, COUNT(*) as chunk_count "
            "FROM chunks "
            "GROUP BY project, source_file, layer, source_type "
            "ORDER BY project, layer, source_file;"
        )
        print("=== Database Chunks by Document ===")
        print(f"{'PROJECT':<20} | {'SOURCE FILE':<40} | {'LAYER':<10} | {'TYPE':<10} | {'CHUNKS':<6}")
        print("-" * 95)
        for r in rows:
            print(f"{r['project']:<20} | {r['source_file']:<40} | {r['layer']:<10} | {r['source_type']:<10} | {r['chunk_count']:<6}")

if __name__ == "__main__":
    asyncio.run(main())
