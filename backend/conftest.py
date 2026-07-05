"""
WHY THIS EXISTS:
When pytest is invoked from the repo root (as in CI: `python -m pytest backend/tests`),
the `backend/` directory is not automatically on sys.path. This conftest.py lives at
`backend/conftest.py` — which IS within pytest's rootdir — and inserts `backend/`
into sys.path before any test module is imported, making `from src.xxx import ...`
resolve correctly regardless of the launch directory.
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
