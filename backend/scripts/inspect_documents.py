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
from src.ingestion.manual_loader import load_manual_documents


async def main() -> None:
    if len(sys.argv) < 2:
        print("Error: Missing project name argument.")
        print("Usage: python scripts/inspect_documents.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1].strip().lower()
    yaml_path = PROJECT_ROOT / "knowledge" / project_name / "ingest.yml"
    knowledge_dir = PROJECT_ROOT / "knowledge"

    if not yaml_path.exists():
        print(f"Error: ingest.yml not found at {yaml_path}")
        sys.exit(1)

    print(f"Project: {project_name}\n")
    print(f"Fetching GitHub documents using {yaml_path.name}...")

    try:
        github_documents = await fetch_github_repository(str(yaml_path))
    except Exception as e:
        print(f"Failed to fetch GitHub documents: {e}")
        sys.exit(1)

    print(f"Loading manual documents from {knowledge_dir}...")
    try:
        manual_documents = load_manual_documents(project_name, knowledge_dir)
    except Exception as e:
        print(f"Failed to load manual documents: {e}")
        sys.exit(1)

    # Merge
    documents = github_documents + manual_documents
    print(f"\nTotal Documents: {len(documents)}\n")

    # Print individual document metadata
    for doc in documents:
        print(f"Source File: {doc.source_file}")
        print(f"  Project: {doc.project}")
        print(f"  Layer: {doc.layer}")
        print(f"  Type: {doc.source_type}")
        print(f"  Length: {len(doc.content)}")
        print()

    # Calculate summary statistics
    total_docs = len(documents)
    
    # We want to format layers count exactly: Identity, Design, Artifact
    # So we get them case-sensitively or capitalize them.
    # The prompt expects:
    # Documents by source:
    # github : 39
    # manual : 4
    # Also report:
    # Identity
    # Design
    # Artifact
    # counts after merging.
    
    layers_counter = Counter(doc.layer.lower() for doc in documents)
    types_counter = Counter(doc.source_type.lower() for doc in documents)

    print("--- Summary Statistics ---")
    print(f"Total Documents: {total_docs}")
    print("\nDocuments by source:")
    print(f"github : {types_counter.get('github', 0)}")
    print(f"manual : {types_counter.get('manual', 0)}")
    
    print("\nDocuments by layer:")
    print(f"Identity : {layers_counter.get('identity', 0)}")
    print(f"Design   : {layers_counter.get('design', 0)}")
    print(f"Artifact : {layers_counter.get('artifact', 0)}")
    print()


if __name__ == "__main__":
    asyncio.run(main())

