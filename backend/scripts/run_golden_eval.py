import asyncio
import sys
from pathlib import Path

# Resolve workspace paths
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.db.core import get_db_pool, close_db_pool
from src.retrieval.hybrid_retriever import retrieve
from src.retrieval.bm25_retriever import index_instance

GOLDEN_QUERIES = [
    "Tell me about yourself",
    "What projects have you built?",
    "What is your technology stack?",
    "How can I hire you?",
    "What backend technologies do you know?",
    "Explain your RAG Portfolio project.",
    "What cloud technologies have you used?",
    "What DevOps experience do you have?"
]

async def main():
    try:
        # Ensure BM25 is initialized
        await index_instance.refresh_index()
        
        output_path = SCRIPTS_DIR / "golden_eval_results.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, query in enumerate(GOLDEN_QUERIES, 1):
                f.write(f"\n==========================================\n")
                f.write(f"QUERY {idx}: \"{query}\"\n")
                f.write(f"==========================================\n")
                
                try:
                    results = await retrieve(
                        query=query,
                        top_k=10,
                        project=None,
                        candidate_k=20,
                        diversify=False,
                        grade=False
                    )
                    
                    if not results:
                        f.write("No chunks retrieved.\n")
                        continue
                        
                    for rank, r in enumerate(results, 1):
                        chunk = r.chunk
                        f.write(f"Rank {rank}:\n")
                        f.write(f"  Project:      {chunk.project}\n")
                        f.write(f"  Document:     {chunk.source_file}\n")
                        f.write(f"  Chunk ID:     {chunk.chunk_id}\n")
                        f.write(f"  RRF Score:    {r.score:.6f}\n")
                        f.write(f"  Vector Rank:  {r.vector_rank}\n")
                        f.write(f"  BM25 Rank:    {r.bm25_rank}\n")
                        f.write(f"  Source Type:  {chunk.source_type}\n")
                        f.write(f"  Layer:        {chunk.layer}\n")
                        
                        # Show first 120 chars preview
                        preview = chunk.content.replace('\n', ' ').strip()
                        if len(preview) > 120:
                            preview = preview[:120] + "..."
                        f.write(f"  Preview:      {preview}\n\n")
                except Exception as e:
                    f.write(f"Error executing query: {e}\n")
        print(f"Results successfully written to {output_path}")
    finally:
        await close_db_pool()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
