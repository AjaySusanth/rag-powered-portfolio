"""
DESIGN DECISION:
This script provides an interactive CLI to manually test the Vector Retrieval Engine.
It uses standard input to accept queries and invokes the vector_retriever to return
the top matching chunks, enabling rapid iteration and manual evaluation of the knowledge base.
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add backend directory to sys.path to resolve src imports
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.retrieval.vector_retriever import retrieve
from src.db.core import close_db_pool


async def interactive_search(project_filter: str = None, top_k: int = 5) -> None:
    print(f"=== Vector Retrieval Interactive CLI ===")
    if project_filter:
        print(f"Project Filter: {project_filter}")
    print("Type your queries below (or 'quit' to exit):\n")

    while True:
        try:
            query = input("> ")
            if query.strip().lower() in {"quit", "exit", "q"}:
                break
            if not query.strip():
                continue

            print("Searching...")
            results = await retrieve(query=query, top_k=top_k, project=project_filter)

            if not results:
                print("No results found.\n")
                continue

            print(f"\nTop {len(results)} Chunks:")
            for result in results:
                print("-" * 60)
                print(f"Score: {result.score:.4f}")
                print(f"Source: {result.chunk.source_file}")
                print(f"Project: {result.chunk.project} | Layer: {result.chunk.layer}")
                
                # Display heading metadata if available
                heading = result.chunk.metadata.get("heading")
                if heading:
                    print(f"Heading: {heading}")
                
                print("\n[Preview]")
                
                # Preview up to 300 characters
                preview_len = 300
                snippet = result.chunk.content[:preview_len].strip()
                if len(result.chunk.content) > preview_len:
                    snippet += "..."
                print(snippet)
                print()

        except EOFError:
            break
        except Exception as e:
            print(f"\n[Error] {e}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test RAG Vector Retrieval manually.")
    parser.add_argument("query", type=str, nargs="?", help="A natural language question to ask.")
    parser.add_argument("--project", type=str, default=None, help="Scope retrieval to a specific project.")
    parser.add_argument("--k", type=int, default=5, help="Number of chunks to retrieve (top_k).")
    args = parser.parse_args()

    try:
        if args.query:
            # Single shot search mode
            print(f"> {args.query}\n")
            results = await retrieve(query=args.query, top_k=args.k, project=args.project)
            
            if not results:
                print("No results found.")
                return
                
            for result in results:
                print("-" * 60)
                print(f"Score: {result.score:.4f}")
                print(f"Source: {result.chunk.source_file}")
                print(f"Project: {result.chunk.project} | Layer: {result.chunk.layer}")
                
                heading = result.chunk.metadata.get("heading")
                if heading:
                    print(f"Heading: {heading}")
                
                print("\n[Preview]")
                preview_len = 300
                snippet = result.chunk.content[:preview_len].strip()
                if len(result.chunk.content) > preview_len:
                    snippet += "..."
                print(snippet)
                print()
        else:
            # Interactive mode
            await interactive_search(project_filter=args.project, top_k=args.k)
            
    finally:
        await close_db_pool()


if __name__ == "__main__":
    # Ensure Windows event loop policy plays nice with asyncpg/anyio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
