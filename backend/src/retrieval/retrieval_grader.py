"""
WHY THIS WAS CHOSEN:
This module orchestrates the filtering of retrieved chunks. It calls the abstract BaseGrader
to grade all chunks in a single batch, filters out chunks marked as irrelevant, and applies
the fallback logic (min_chunks) to ensure we do not starve the generation pipeline.
"""

import logging
from typing import List

from src.llm.interfaces import BaseGrader
from src.models.retrieval_result import RetrievalResult

logger = logging.getLogger(__name__)


async def filter_relevant_chunks(
    query: str,
    results: List[RetrievalResult],
    grader: BaseGrader,
    min_chunks: int = 3
) -> List[RetrievalResult]:
    """
    Filters a list of RetrievalResults by querying the provided grader.
    
    If the number of relevant chunks after filtering is less than min_chunks,
    it falls back to the original results list to prevent empty/insufficient context.
    
    Args:
        query: The user query string.
        results: The list of RetrievalResults from previous stages (RRF/Diversified).
        grader: An implementation of BaseGrader.
        min_chunks: Configurable minimum number of chunks to return. Falls back to original if below this.
        
    Returns:
        A filtered list of RetrievalResult objects (or the original list on fallback).
    """
    if not results:
        return []

    try:
        # Step 1: Request structured grades from the provider in a single batched call
        grades = await grader.grade(query, results)

        # Map grades by chunk index
        grades_by_idx = {g.chunk_index: g for g in grades}

        # Step 2: Filter results based on the binary is_relevant flag
        filtered = []
        for i, res in enumerate(results):
            grade = grades_by_idx.get(i)
            if grade and grade.is_relevant:
                filtered.append(res)
            else:
                reason = grade.rejection_reason if grade else "no_grade_returned"
                explanation = grade.explanation if grade else ""
                logger.info(
                    f"Chunk {i} from '{res.chunk.source_file}' filtered out. "
                    f"Reason: {reason}. Explanation: {explanation}"
                )

        # Step 3: Check fallback condition
        if len(filtered) >= min_chunks:
            logger.info(f"Filtering complete. Kept {len(filtered)} / {len(results)} chunks.")
            return filtered

        logger.warning(
            f"Filtered chunks count ({len(filtered)}) is less than min_chunks ({min_chunks}). "
            f"Falling back to original {len(results)} diversified chunks to avoid context starvation."
        )
        return results

    except Exception as e:
        logger.error(f"Error during retrieval grading: {e}. Falling back to original results.")
        return results
