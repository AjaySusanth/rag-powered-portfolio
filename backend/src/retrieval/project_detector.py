"""
WHY THIS WAS CHOSEN:
This module provides a deterministic, regex-based project detector that maps natural language queries
to canonical project IDs. It is placed outside the core retrieval pipeline (as a routing concern)
to ensure the retrieval layer remains reusable and testable in isolation.

By sorting aliases by descending length and replacing matched spans with spaces, we prevent shorter
nested aliases (e.g. "reservation") from matching when a longer alias (e.g. "reservation system") has
already matched, while still preserving query structure and word boundaries for subsequent matches.
"""

import re
from typing import Dict, List, Optional

# Registry of projects and their case-insensitive aliases
PROJECTS: Dict[str, List[str]] = {
    "talentforge": [
        "talentforge",
        "talent forge",
    ],
    "reservation-system": [
        "reservation",
        "reservation system",
    ],
    "n8n-aks-platform": [
        "n8n",
        "aks",
        "kubernetes",
    ],
    "classsync": [
        "classsync",
        "class sync",
    ],
}


def normalize_text(text: str) -> str:
    """
    Normalizes text by lowercasing, replacing punctuation/symbols with spaces,
    and collapsing multiple spaces into a single space.
    """
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Replace punctuation, hyphens, and slashes with spaces to avoid merging words
    text = re.sub(r'[-_/\\,.:;!?(){}[\]"\'`]', " ", text)
    # Collapse multiple spaces into one
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_project(query: str) -> Optional[str]:
    """
    Analyzes a user query to detect if it refers to a specific project.

    Uses word-boundary regexes to prevent partial matching (e.g., matching "tasks" for "aks").
    Sorts aliases by length descending and consumes matched spans in the query to prevent
    shorter sub-aliases from double-matching. If multiple distinct projects match, returns None.
    """
    if not query or not query.strip():
        return None

    normalized_query = normalize_text(query)

    # Flatten the PROJECTS registry into a list of (normalized_alias, project_id)
    flat_aliases: List[tuple[str, str]] = []
    for project_id, aliases in PROJECTS.items():
        for alias in aliases:
            flat_aliases.append((normalize_text(alias), project_id))

    # Sort aliases by descending length to match longer, more specific aliases first
    flat_aliases.sort(key=lambda x: len(x[0]), reverse=True)

    matched_projects = set()
    current_query = normalized_query

    for alias, project_id in flat_aliases:
        # Match using word boundaries on both ends of the alias
        pattern = rf"\b{re.escape(alias)}\b"
        match = re.search(pattern, current_query)
        if match:
            matched_projects.add(project_id)
            # Replace the matched span with spaces of equal length.
            # This consumes the matched tokens so shorter nested aliases won't match,
            # while preserving the query's total length and word boundaries for other tokens.
            start, end = match.span()
            current_query = current_query[:start] + " " * (end - start) + current_query[end:]

    # If exactly one project matches, route to it. If multiple projects match, it's ambiguous.
    if len(matched_projects) == 1:
        return next(iter(matched_projects))

    return None
