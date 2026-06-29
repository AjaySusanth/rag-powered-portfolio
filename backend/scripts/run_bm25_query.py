import asyncio
import sys
from pathlib import Path

# Resolve paths
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.retrieval.bm25_retriever import retrieve
from src.vectorstore.pgvector_store import count_chunks

async def main():
    if len(sys.argv) < 2:
        print("Error: Missing query string.")
        print("Usage: python scripts/run_bm25_query.py <query> [project_name]")
        sys.exit(1)
        
    query = sys.argv[1].strip()
    project = sys.argv[2].strip() if len(sys.argv) > 2 else None
    
    print(f"Checking database chunks...")
    total = await count_chunks()
    print(f"Total chunks in DB: {total}")
    
    if total == 0:
        print("Warning: Database is empty. Please run index_project.py first.")
        sys.exit(1)
        
    print(f"\nRunning BM25 search for query: '{query}' (Project filter: {project})")
    results = await retrieve(query, top_k=5, project=project)
    
    print(f"\nFound {len(results)} matches:")
    for i, res in enumerate(results):
        print(f"\n[{i+1}] Score: {res.score:.4f} | Project: {res.chunk.project} | File: {res.chunk.source_file}")
        print(f"    Content: {res.chunk.content[:150]}...")

if __name__ == "__main__":
    asyncio.run(main())
