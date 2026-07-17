"""
WHY THIS WAS CHOSEN:
This module orchestrates hybrid retrieval by executing semantic vector search and lexical BM25 search
concurrently. Combining both approaches compensates for the weaknesses of each: vector search retrieves
conceptually relevant chunks that lack exact query keywords, while BM25 retrieves exact technical matching
identifiers (such as function names or configuration lines) that might otherwise get lost in the embedding space.
"""

import asyncio
import logging
import time
from typing import List, Optional

from src.config import settings
from src.llm.factory import create_grader_from_settings
from src.models.retrieval_result import RetrievalResult
from src.observability.tracing import ChunkTrace, PipelineTrace, RetrievalStageTrace
from src.retrieval import bm25_retriever, vector_retriever
from src.retrieval.diversification import diversify_by_source
from src.retrieval.retrieval_grader import filter_relevant_chunks
from src.retrieval.rrf import RRFFuser

logger = logging.getLogger(__name__)


def _record_stage(
    results: List[RetrievalResult],
    latency_ms: float,
    stage_name: str,
    trace: Optional[PipelineTrace],
    candidate_count: int,
    duplicates_removed: Optional[int] = None,
) -> None:
    """
    Helper function to record a retrieval sub-stage trace in a type-safe manner.
    """
    if not trace:
        return

    chunk_traces: List[ChunkTrace] = []
    for idx, r in enumerate(results):
        preview = r.chunk.content[:200]
        if len(r.chunk.content) > 200:
            preview += "..."

        chunk_traces.append(
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

    scores = [r.score for r in results]
    score_range = [min(scores), max(scores)] if scores else None

    stage_trace = RetrievalStageTrace(
        results=chunk_traces,
        latency_ms=latency_ms,
        candidate_count=candidate_count,
        score_range=score_range,
        duplicates_removed=duplicates_removed,
    )

    if stage_name == "vector":
        trace.retrieval.vector_stage = stage_trace
    elif stage_name == "bm25":
        trace.retrieval.bm25_stage = stage_trace
    elif stage_name == "rrf":
        trace.retrieval.rrf_stage = stage_trace
    elif stage_name == "diversified":
        trace.retrieval.diversified_stage = stage_trace
    elif stage_name == "graded":
        trace.retrieval.graded_stage = stage_trace

    trace.timings.stages[f"retrieval_{stage_name}"] = latency_ms


async def retrieve(
    query: str,
    top_k: int = 5,
    project: Optional[str] = None,
    candidate_k: int = 20,
    diversify: bool = True,
    grade: bool = False,
    min_chunks: Optional[int] = None,
    trace: Optional[PipelineTrace] = None,
) -> List[RetrievalResult]:
    """
    Executes a hybrid search query using both Vector and BM25 retrievers concurrently.
    Fetches candidate_k items from both retrievers to prevent candidate starvation,
    fuses the outputs using Reciprocal Rank Fusion (RRF), applies source diversification,
    grades/filters chunks if enabled, and returns the final results.
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to hybrid retrieve. Returning empty results.")
        return []

    overall_start = time.perf_counter()

    try:
        # Run both retrievers concurrently to reduce overall search latency.
        async def timed_vector_retrieve() -> tuple[List[RetrievalResult], float]:
            t0 = time.perf_counter()
            res = await vector_retriever.retrieve(
                query=query, top_k=candidate_k, project=project, trace=trace
            )
            dt = (time.perf_counter() - t0) * 1000.0
            return res, dt

        async def timed_bm25_retrieve() -> tuple[List[RetrievalResult], float]:
            t0 = time.perf_counter()
            res = await bm25_retriever.retrieve(query=query, top_k=candidate_k, project=project)
            dt = (time.perf_counter() - t0) * 1000.0
            return res, dt

        (vector_results, vector_latency), (bm25_results, bm25_latency) = await asyncio.gather(
            timed_vector_retrieve(), timed_bm25_retrieve()
        )

        _record_stage(vector_results, vector_latency, "vector", trace, candidate_count=candidate_k)
        _record_stage(bm25_results, bm25_latency, "bm25", trace, candidate_count=candidate_k)

        # Fuse and rank results using RRFFuser
        rrf_start = time.perf_counter()
        fuser = RRFFuser(k=60)
        fused_results = fuser.fuse(vector_results, bm25_results)
        rrf_latency = (time.perf_counter() - rrf_start) * 1000.0

        rrf_candidates = len(vector_results) + len(bm25_results)

        # Track retrieval candidates count in Prometheus
        from src.observability.metrics import rag_retrieval_candidates

        retrieval_scope = "project" if project else "global"
        rag_retrieval_candidates.labels(retrieval_scope=retrieval_scope).observe(rrf_candidates)

        rrf_duplicates_removed = rrf_candidates - len(fused_results)
        _record_stage(
            fused_results,
            rrf_latency,
            "rrf",
            trace,
            candidate_count=rrf_candidates,
            duplicates_removed=rrf_duplicates_removed,
        )

        # Apply source diversification if enabled
        div_start = time.perf_counter()
        if diversify:
            results = diversify_by_source(
                fused_results, limit=top_k, max_per_source=settings.DIVERSIFICATION_MAX_PER_SOURCE
            )
        else:
            results = fused_results[:top_k]
        div_latency = (time.perf_counter() - div_start) * 1000.0

        div_candidates = len(fused_results)
        div_removed = div_candidates - len(results)
        _record_stage(
            results,
            div_latency,
            "diversified",
            trace,
            candidate_count=div_candidates,
            duplicates_removed=div_removed,
        )

        # Apply grading stage if enabled
        if grade:
            grade_start = time.perf_counter()
            grader = create_grader_from_settings()
            actual_min_chunks = min_chunks if min_chunks is not None else settings.GRADER_MIN_CHUNKS
            graded_results = await filter_relevant_chunks(
                query=query,
                results=results,
                grader=grader,
                min_chunks=actual_min_chunks,
                trace=trace,
            )
            grade_latency = (time.perf_counter() - grade_start) * 1000.0

            if trace and trace.retrieval.graded_stage:
                trace.retrieval.graded_stage.latency_ms = grade_latency
                trace.timings.stages["retrieval_graded"] = grade_latency

            results = graded_results

        overall_latency_ms = (time.perf_counter() - overall_start) * 1000.0
        if trace:
            trace.timings.total_retrieval_ms = overall_latency_ms

        # Track retrieval pipeline latency in Prometheus (in seconds)
        overall_latency_seconds = time.perf_counter() - overall_start
        from src.observability.metrics import rag_retrieval_duration_seconds

        retrieval_scope = "project" if project else "global"
        rag_retrieval_duration_seconds.labels(retrieval_scope=retrieval_scope).observe(
            overall_latency_seconds
        )

        return results

    except Exception as e:
        logger.error(f"Hybrid retrieval failed for query '{query}': {e}")
        raise
