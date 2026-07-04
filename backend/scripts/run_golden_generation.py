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

from src.services.chat_orchestrator import ChatOrchestrator

async def run_query(f, orchestrator, query):
    f.write("==========================================\n")
    f.write(f"QUERY: {query}\n")
    f.write("==========================================\n")
    
    answer_parts = []
    citations = []
    
    async for event in orchestrator.stream_chat(query):
        if event.event == "token":
            answer_parts.append(event.token)
        elif event.event == "citations":
            citations = event.citations
            
    full_answer = "".join(answer_parts)
    f.write("--- ANSWER ---\n")
    f.write(full_answer + "\n")
    f.write("\n--- CITATIONS ---\n")
    for c in citations:
        f.write(f"- {c.file} ({c.project} | {c.layer})\n")
    f.write("\n\n")

async def main():
    orchestrator = ChatOrchestrator()
    queries = [
        "What projects have you built?",
        "Name the projects in Ajay's portfolio",
        "Explain TalentForge",
        "Explain ClassSync"
    ]
    output_path = SCRIPTS_DIR / "golden_generation_results.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        for q in queries:
            await run_query(f, orchestrator, q)

if __name__ == "__main__":
    asyncio.run(main())
