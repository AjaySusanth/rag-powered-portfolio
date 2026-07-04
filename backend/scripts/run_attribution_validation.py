import sys
import asyncio
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from src.services.chat_orchestrator import ChatOrchestrator
from src.retrieval.hybrid_retriever import retrieve
from src.retrieval.project_detector import detect_project
from src.retrieval.rewriters.factory import create_rewriter_from_settings
from src.config import settings

async def run_validation_query(f, orchestrator, query):
    f.write("======================================================================\n")
    f.write(f"QUERY: {query}\n")
    f.write("======================================================================\n\n")

    # 1. Manually retrieve chunks first to show the "BEFORE" citation list
    project = detect_project(query)
    search_query = query
    if settings.ENABLE_QUERY_REWRITER:
        try:
            rewriter = create_rewriter_from_settings()
            rewrite_result = await rewriter.rewrite(query, project)
            if rewrite_result.rewritten:
                search_query = rewrite_result.rewritten_query
        except Exception:
            pass

    retrieved = await retrieve(
        query=search_query,
        project=project,
        top_k=15,
        diversify=True,
        grade=True
    )
    
    before_citations = []
    seen = set()
    for res in retrieved:
        source_file = res.chunk.source_file or "unknown"
        proj = res.chunk.project or "global"
        dedup_key = (proj, source_file)
        if dedup_key not in seen:
            seen.add(dedup_key)
            before_citations.append(f"{source_file} ({proj})")

    # 2. Run the orchestrator stream to get the actual generation, grounded citations, and measure latency
    start_time = time.time()
    answer_parts = []
    after_citations = []
    
    async for event in orchestrator.stream_chat(query):
        if event.event == "token":
            answer_parts.append(event.token)
        elif event.event == "citations":
            for c in event.citations:
                after_citations.append(f"{c.file} ({c.project})")
                
    latency = time.time() - start_time
    full_answer = "".join(answer_parts)

    f.write(f"LATENCY: {latency:.2f} seconds\n\n")
    
    f.write("--- BEFORE CITATIONS (ALL RETRIEVED CHUNKS) ---\n")
    for c in before_citations:
        f.write(f"- {c}\n")
    if not before_citations:
        f.write("(None)\n")
        
    f.write("\n--- AFTER CITATIONS (GROUNDED / ATTRIBUTED CHUNKS) ---\n")
    for c in after_citations:
        f.write(f"- {c}\n")
    if not after_citations:
        f.write("(None)\n")
        
    f.write("\n--- GENERATED ANSWER ---\n")
    f.write(full_answer + "\n\n")

async def main():
    orchestrator = ChatOrchestrator()
    queries = [
        "What deployment strategy is used in ClassSync?",
        "Which projects did Ajay deploy and where?",
        "Explain the resume parsing pipeline in TalentForge.",
        "What projects have you built?"
    ]
    
    output_path = SCRIPTS_DIR / "attribution_validation_results.txt"
    print("Running attribution validation queries...")
    with open(output_path, "w", encoding="utf-8") as f:
        for q in queries:
            print(f"Executing: {q}")
            await run_validation_query(f, orchestrator, q)
    print(f"Validation complete! Results saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
