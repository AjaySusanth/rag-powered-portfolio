"""
DESIGN DECISION:
This inspection script provides verification of the Document model ingestion.
It resolves the target project's ingest.yml configuration, invokes the github_fetcher,
and prints a detailed summary of the fetched Document objects (grouped by layer
and source type).

We run it using asyncio since the fetcher operates asynchronously. We programmatically
ensure the PYTHONPATH includes the backend root directory so that it runs seamlessly
without manual environment configuration.
"""

import sys
import asyncio
from pathlib import Path
from collections import Counter

# Programmatically resolve workspace paths so import works from anywhere
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.ingestion.github_fetcher import fetch_github_repository


async def main() -> None:
    if len(sys.argv) < 2:
        print("Error: Missing project name argument.")
        print("Usage: python scripts/inspect_documents.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1].strip().lower()
    yaml_path = PROJECT_ROOT / "knowledge" / project_name / "ingest.yml"

    if not yaml_path.exists():
        print(f"Error: ingest.yml not found at {yaml_path}")
        sys.exit(1)

    print(f"Project: {project_name}\n")
    print(f"Fetching documents using {yaml_path.name}...\n")

    try:
        documents = await fetch_github_repository(str(yaml_path))
    except Exception as e:
        print(f"Failed to fetch documents: {e}")
        sys.exit(1)

    print(f"Documents: {len(documents)}\n")

    # Print individual document metadata
    for doc in documents:
        print(doc.source_file)
        print(f"Layer: {doc.layer}")
        print(f"Type: {doc.source_type}")
        print(f"Length: {len(doc.content)}")
        print()

    # Calculate summary statistics
    total_docs = len(documents)
    layers_counter = Counter(doc.layer for doc in documents)
    types_counter = Counter(doc.source_type for doc in documents)

    print("Summary:")
    print(f"- Total documents: {total_docs}")
    print("- Documents by layer:")
    for layer, count in layers_counter.items():
        print(f"  - {layer}: {count}")
    print("- Documents by source type:")
    for src_type, count in types_counter.items():
        print(f"  - {src_type}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
