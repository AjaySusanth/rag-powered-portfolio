"""
Root-level conftest.py — WHY THIS EXISTS:
When pytest is run from the repo root (as in CI: `python -m pytest backend/tests`),
the `backend/` directory is not automatically added to sys.path. This means any
test doing `from src.xxx import ...` fails with ModuleNotFoundError.

This conftest.py is discovered by pytest before any test collection, and it inserts
`backend/` into sys.path, making `src` importable from anywhere pytest is launched.
This is the most portable fix: it works regardless of pytest version, pyproject.toml
support, or launch directory.
"""
import sys
from pathlib import Path

# Insert backend/ at the front of sys.path so `from src.xxx import ...` resolves
# correctly when pytest is invoked from the repo root (e.g. in CI).
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
