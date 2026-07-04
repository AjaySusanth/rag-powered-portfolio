import sys
import asyncio
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.retrieval.hybrid_retriever import retrieve
from src.services.prompt_builder import PromptBuilder
from src.db.core import get_db_pool

async def main():
    queries = [
        "Tell me about yourself",
        "Explain what is ClassSync",
        "What projects have you built?"
    ]
    
    pool = await get_db_pool()
    output_path = SCRIPTS_DIR / "prompt_inspection_results.txt"
    
    with open(output_path, "w", encoding="utf-8") as f:
        for q in queries:
            f.write("==========================================\n")
            f.write(f"QUERY: {q}\n")
            f.write("==========================================\n")
            
            chunks = await retrieve(q, top_k=5, diversify=False, grade=False)
            result = PromptBuilder.build(q, chunks, max_chunks=5)
            
            f.write("--- FINAL PROMPT ---\n\n")
            f.write(PromptBuilder.SYSTEM_INSTRUCTION + "\n\n")
            f.write(result.prompt + "\n\n\n")
        
    await pool.close()

if __name__ == "__main__":
    asyncio.run(main())
