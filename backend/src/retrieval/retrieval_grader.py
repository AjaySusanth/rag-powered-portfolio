"""
WHY THIS WAS CHOSEN:
This module orchestrates the filtering of retrieved chunks. It calls the abstract BaseGrader
to grade all chunks in a single batch, filters out chunks marked as irrelevant, and applies
the fallback logic (min_chunks) to ensure we do not starve the generation pipeline.
"""

import logging
from typing import List, Optional

from src.llm.interfaces import BaseGrader
from src.models.retrieval_result import RetrievalResult
from src.observability.tracing import ChunkTrace, PipelineTrace, RetrievalStageTrace

logger = logging.getLogger(__name__)


async def filter_relevant_chunks(
    query: str,
    results: List[RetrievalResult],
    grader: BaseGrader,
    min_chunks: int = 3,
    trace: Optional[PipelineTrace] = None,
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
        trace: Optional PipelineTrace to record graded results.

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
        final_results = filtered
        if len(filtered) < min_chunks:
            logger.warning(
                f"Filtered chunks count ({len(filtered)}) is less than min_chunks ({min_chunks}). "
                f"Falling back to original {len(results)} diversified chunks to avoid context starvation."
            )
            final_results = results

        # Record trace if enabled
        if trace:
            # Map final results to ChunkTrace
            final_traces = []
            for idx, r in enumerate(final_results):
                preview = r.chunk.content[:200]
                if len(r.chunk.content) > 200:
                    preview += "..."
                final_traces.append(
                    ChunkTrace(
                        chunk_id=r.chunk.chunk_id,
                        content_preview=preview,
                        source_file=r.chunk.source_file,
                        layer=r.chunk.layer,
                        project=r.chunk.project,
                        score=r.score,
                        rank=idx + 1,
                    )
                )

            # Map rejected results to ChunkTrace (those not in the filtered set)
            rejected_results_list = [r for r in results if r not in filtered]
            rejected_traces = []
            for idx, r in enumerate(rejected_results_list):
                original_idx = results.index(r)
                grade = grades_by_idx.get(original_idx)
                reason_str = ""
                if grade:
                    reason_str = (
                        f"[{grade.rejection_reason or 'irrelevant'}] {grade.explanation or ''}"
                    )
                else:
                    reason_str = "No grade returned from model."

                preview = r.chunk.content[:200]
                if len(r.chunk.content) > 200:
                    preview += "..."
                rejected_traces.append(
                    ChunkTrace(
                        chunk_id=r.chunk.chunk_id,
                        content_preview=preview,
                        source_file=r.chunk.source_file,
                        layer=r.chunk.layer,
                        project=r.chunk.project,
                        score=r.score,
                        rank=idx + 1,
                        reason=reason_str,
                    )
                )

            scores = [r.score for r in final_results]
            score_range = [min(scores), max(scores)] if scores else None

            trace.retrieval.graded_stage = RetrievalStageTrace(
                results=final_traces,
                candidate_count=len(results),
                score_range=score_range,
                duplicates_removed=len(rejected_traces),
                rejected_results=rejected_traces,
            )

        return final_results

    except Exception as e:
        logger.error(f"Error during retrieval grading: {e}. Falling back to original results.")
        if trace:
            # Fallback trace mapping on error
            final_traces = []
            for idx, r in enumerate(results):
                preview = r.chunk.content[:200]
                if len(r.chunk.content) > 200:
                    preview += "..."
                final_traces.append(
                    ChunkTrace(
                        chunk_id=r.chunk.chunk_id,
                        content_preview=preview,
                        source_file=r.chunk.source_file,
                        layer=r.chunk.layer,
                        project=r.chunk.project,
                        score=r.score,
                        rank=idx + 1,
                    )
                )
            trace.retrieval.graded_stage = RetrievalStageTrace(
                results=final_traces,
                candidate_count=len(results),
                score_range=None,
                duplicates_removed=0,
                rejected_results=[],
            )
        return results
