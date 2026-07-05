"""
WHY THIS WAS CHOSEN:
This service isolates filesystem interactions for deterministic portfolio resources.
The route layer remains thin and unaware of exact file locations. We use lru_cache
for get_stack to prevent redundant I/O operations on every API request.

WHY DATA_DIR / RESUME_DIR instead of PROJECT_ROOT / "backend" / ...:
All path constants are centralized in config.py. APP_ROOT always resolves to the
backend root — `backend/` on the host and `/app` inside Docker — so data/ and
assets/ are always at the right location regardless of execution environment.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from src.config import DATA_DIR, RESUME_DIR


class PortfolioService:
    """
    Service class managing the retrieval of deterministic portfolio data.
    """

    @staticmethod
    def get_resume_path() -> Path:
        """
        Returns the absolute path to the resume PDF file.
        """
        return RESUME_DIR / "Ajay_Susanth_Resume.pdf"

    @staticmethod
    @lru_cache(maxsize=1)
    def get_stack() -> Dict[str, Any]:
        """
        Reads, parses, and returns the technology stack from stack.json.
        Cached via lru_cache to ensure we only load and parse the JSON file once.
        """
        stack_file = DATA_DIR / "stack.json"

        if not stack_file.exists():
            raise FileNotFoundError(f"Stack metadata file not found at: {stack_file}")

        with open(stack_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    @lru_cache(maxsize=1)
    def get_hire() -> Dict[str, Any]:
        """
        Reads, parses, and returns hiring details from hire.json.
        Cached via lru_cache to ensure we only load and parse the JSON file once.
        """
        hire_file = DATA_DIR / "hire.json"

        if not hire_file.exists():
            raise FileNotFoundError(f"Hiring metadata file not found at: {hire_file}")

        with open(hire_file, "r", encoding="utf-8") as f:
            return json.load(f)
