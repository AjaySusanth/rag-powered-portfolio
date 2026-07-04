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

def main():
    knowledge_dir = PROJECT_ROOT / "knowledge"
    print(f"Loading from: {knowledge_dir}")
    docs = load_manual_documents("talentforge", knowledge_dir)
    print(f"Total documents loaded: {len(docs)}")
    for d in docs:
        print(f"File: {d.source_file} | Project: {d.project} | Layer: {d.layer} | Type: {d.source_type}")

if __name__ == "__main__":
    main()
