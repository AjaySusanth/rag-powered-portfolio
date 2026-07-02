"""
WHY THIS WAS CHOSEN:
This service isolates filesystem interactions for deterministic portfolio resources.
The route layer remains thin and unaware of exact file locations. We use lru_cache
for get_stack to prevent redundant I/O operations on every API request.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

from src.config import PROJECT_ROOT


class PortfolioService:
    """
    Service class managing the retrieval of deterministic portfolio data.
    """

    @staticmethod
    def get_resume_path() -> Path:
        """
        Returns the absolute path to the resume PDF file.
        """
        return PROJECT_ROOT / "backend" / "assets" / "resume" / "Ajay_Susanth_Resume.pdf"

    @staticmethod
    @lru_cache(maxsize=1)
    def get_stack() -> Dict[str, Any]:
        """
        Reads, parses, and returns the technology stack from stack.json.
        Cached via lru_cache to ensure we only load and parse the JSON file once.
        """
        stack_file = PROJECT_ROOT / "backend" / "data" / "stack.json"
        
        if not stack_file.exists():
            raise FileNotFoundError(f"Stack metadata file not found at: {stack_file}")
            
        with open(stack_file, "r", encoding="utf-8") as f:
            return json.load(f)
