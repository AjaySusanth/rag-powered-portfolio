import asyncio
import sys
from pathlib import Path

# Resolve workspace paths
SCRIPTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPTS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "src"))

from src.ingestion.manual_loader import load_manual_documents
from src.chunking.chunker import chunk_document

def main():
    knowledge_dir = PROJECT_ROOT / "knowledge"
    docs = load_manual_documents("talentforge", knowledge_dir)
    for d in docs:
        if d.project == "__global__":
            chunks = chunk_document(d)
            print(f"File: {d.source_file} | Chunks created: {len(chunks)}")
            for idx, c in enumerate(chunks):
                print(f"  - Chunk {idx}: {c.token_count} tokens, content snippet: {c.content[:60]}...")

if __name__ == "__main__":
    main()
