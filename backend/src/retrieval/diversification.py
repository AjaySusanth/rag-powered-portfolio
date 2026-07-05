"""
WHY THIS WAS CHOSEN:
To implement source diversification as a distinct post-ranking selection stage.
By keeping only a limited number of chunks from each unique source file and filtering
out subsequent duplicate source files, we ensure that the Top-K results sent to the LLM
contain a diverse set of references (context variety). This directly mitigates
'duplicate source domination' where a single large document (like architecture.md)
crowds out other specific codebase artifacts.
"""

from collections import Counter
from typing import List

from src.models.retrieval_result import RetrievalResult


def diversify_by_source(
    results: List[RetrievalResult],
    limit: int,
    max_per_source: int = 3
) -> List[RetrievalResult]:
    """
    Greedily selects chunks from unique source files up to max_per_source per file.
    It scans the ranked list of results, keeping up to max_per_source occurrences
    of each source file until 'limit' chunks are collected or
    the input results list is exhausted.
    """
    source_counts = Counter()
    diversified = []

    for res in results:
        source = res.chunk.source_file or "unknown"
        if source_counts[source] < max_per_source:
            source_counts[source] += 1
            diversified.append(res)
            if len(diversified) == limit:
                break

    return diversified
