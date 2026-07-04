import sys
import asyncio
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from src.retrieval.hybrid_retriever import retrieve

async def main():
    q = "What projects have you built?"
    chunks = await retrieve(q, top_k=15, diversify=False, grade=False)
    with open(SCRIPTS_DIR / "projects_query_chunks.txt", "w", encoding="utf-8") as f:
        for i, res in enumerate(chunks):
            source = res.chunk.source_file
            project = res.chunk.project
            heading = res.chunk.metadata.get("heading") or "No Heading"
            score = res.score
            content_preview = (res.chunk.content.replace('\n', ' ')[:120] + "...") if res.chunk.content else "EMPTY"
            f.write(f"Rank {i+1} | Score: {score:.4f} | Project: {project} | Source: {source} > {heading}\nPreview: {content_preview}\n\n")

if __name__ == "__main__":
    asyncio.run(main())
