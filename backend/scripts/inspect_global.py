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
        count = await conn.fetchval("SELECT COUNT(*) FROM chunks WHERE project = '__global__';")
        print(f"Chunks for '__global__': {count}")
        
        # Let's count by project
        proj_counts = await conn.fetch("SELECT project, COUNT(*) FROM chunks GROUP BY project;")
        print("All projects count:")
        for r in proj_counts:
            print(f"  {r['project']}: {r['count']}")

if __name__ == "__main__":
    asyncio.run(main())
