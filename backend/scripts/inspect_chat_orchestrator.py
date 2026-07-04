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
from src.services.prompt_builder import PromptBuilder
from src.llm.factory import create_grader_from_settings
from src.config import settings

async def main():
    q = "What projects have you built?"
    print(f"QUERY: {q}\n")
    
    # 1. Retrieve raw candidate chunks (top_k=15)
    # We simulate exactly what happens in hybrid_retriever when grade=True
    chunks = await retrieve(q, top_k=15, diversify=True, grade=False)
    print(f"Retrieved {len(chunks)} raw candidate chunks:")
    for idx, c in enumerate(chunks):
        print(f"  [{idx}] {c.chunk.source_file} (proj: {c.chunk.project}) > {c.chunk.metadata.get('heading')} (score: {c.score:.4f})")
    
    # 2. Grade chunks
    grader = create_grader_from_settings()
    grades = await grader.grade(q, chunks)
    print("\nGrader results:")
    filtered_chunks = []
    for idx, (c, g) in enumerate(zip(chunks, grades)):
        is_rel = g.is_relevant
        reason = g.rejection_reason if not is_rel else "N/A"
        print(f"  [{idx}] Relevant: {is_rel} | Reason: {reason} | File: {c.chunk.source_file} > {c.chunk.metadata.get('heading')}")
        if is_rel:
            filtered_chunks.append(c)
            
    # 3. Final chunks sent to PromptBuilder
    final_chunks = filtered_chunks
    if len(filtered_chunks) < settings.GRADER_MIN_CHUNKS:
        print(f"\nFallback triggered! Falling back to original diversified chunks.")
        final_chunks = chunks
        
    print(f"\nFinal {len(final_chunks)} chunks sent to PromptBuilder:")
    for idx, c in enumerate(final_chunks):
         print(f"  [{idx}] {c.chunk.source_file} > {c.chunk.metadata.get('heading')}")

if __name__ == "__main__":
    asyncio.run(main())
