"""
WHY THIS WAS CHOSEN:
The PromptGuard class acts as a passive detection layer for identifying potential
prompt injection and instruction override attempts in user queries.
We implement it as a stateless, deterministic service that analyzes the query against
a set of highly specific regex patterns and outputs a PromptGuardResult metadata container.
It does not rewrite the query or disrupt the pipeline, leaving downstream layers (specifically PromptBuilder)
as the primary defense through grounding. This metadata will support future Block 4 observability.
"""

import re
from typing import List
from pydantic import BaseModel


class PromptGuardResult(BaseModel):
    """
    Metadata container representing the analysis results of a prompt guard run.
    """
    original_query: str
    contains_injection: bool
    matched_rules: List[str]


class PromptGuard:
    """
    Stateless detector for potential prompt injection attempts.
    """

    # Curator of highly specific regex rules to target override and jailbreak phrasing
    # while minimizing false positives on legitimate queries.
    RULES = {
        "ignore_previous_instructions": re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+)?(?:instructions|prompts|queries)", re.IGNORECASE),
        "disregard_previous_instructions": re.compile(r"disregard\s+(?:all\s+)?(?:previous\s+)?(?:instructions|prompts|queries)", re.IGNORECASE),
        "forget_system_prompt": re.compile(r"forget\s+(?:your\s+)?system\s+prompt", re.IGNORECASE),
        "reveal_prompt": re.compile(r"reveal\s+(?:your\s+)?prompt", re.IGNORECASE),
        "developer_mode": re.compile(r"developer\s+mode", re.IGNORECASE),
        "jailbreak": re.compile(r"jailbreak", re.IGNORECASE),
    }

    @classmethod
    def analyze(cls, query: str) -> PromptGuardResult:
        """
        Analyzes a query to identify blocklisted prompt injection patterns.

        Args:
            query: The raw string query from the user.

        Returns:
            A PromptGuardResult mapping matched rules and injection status.
        """
        matched_rules = []
        for rule_name, pattern in cls.RULES.items():
            if pattern.search(query):
                matched_rules.append(rule_name)

        return PromptGuardResult(
            original_query=query,
            contains_injection=len(matched_rules) > 0,
            matched_rules=matched_rules
        )
