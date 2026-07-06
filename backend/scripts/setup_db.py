"""
DESIGN DECISION:
This script initializes the database schema (enables pgvector, creates the chunks table,
and provisions the HNSW index) on the target database specified by DATABASE_URL.
This allows manual DB initialization before running full ingestion.
"""

import sys
import asyncio
from pathlib import Path

# Resolve workspace paths so import works from anywhere
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.db.init_db import init_db


async def main() -> None:
    print("Connecting to database and initializing schema...")
    try:
        await init_db()
        print("Database schema successfully initialized!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
