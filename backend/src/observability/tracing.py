"""
WHY THIS WAS CHOSEN:
This module defines the strongly typed PipelineTrace execution-state object and its nested components.
Structuring the trace into logical sections (request, retrieval, generation, timings, metadata) avoids
flat field pollution and provides a reusable schema suitable for both ad-hoc admin debugging and future
dashboard ingestion (such as Prometheus logging, analytics tracking, or RAG evaluation metrics).
"""

import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TraceRequest(BaseModel):
    """Encapsulates incoming user query parameters and rewrite stages."""

    original_query: str = Field("", description="Original question submitted by the user.")
    detected_project: Optional[str] = Field(
        None, description="Project scope parsed from the query."
    )
    rewritten_query: Optional[str] = Field(
        None, description="The query after context-aware rewriting."
    )
    rewrite_applied: bool = Field(
        False, description="Whether query rewriting was actually executed/applied."
    )
    rewrite_reason: Optional[str] = Field(
        None, description="The explanation of why the query was rewritten."
    )
    project_scope: Optional[str] = Field(
        None, description="The actual project scope namespace used for query execution."
    )


class ChunkTrace(BaseModel):
    """A lightweight representation of a chunk at a specific step in the pipeline."""

    chunk_id: str = Field(..., description="Deterministic hash ID of the chunk.")
    content_preview: str = Field(..., description="Truncated content snippet for verification.")
    source_file: str = Field(..., description="Name of the source file.")
    layer: str = Field(..., description="Which layer the chunk belongs to (1, 2, or 3).")
    project: str = Field(..., description="Associated project tag.")
    score: float = Field(..., description="Retrieval score (similarity, frequency, or RRF weight).")
    rank: Optional[int] = Field(
        None, description="Optional rank index within that specific retrieval step."
    )
    reason: Optional[str] = Field(None, description="Rejection or filtering reason if applicable.")


class RetrievalStageTrace(BaseModel):
    """Holds results, latency, and metrics for a single phase of retrieval."""

    results: List[ChunkTrace] = Field(
        default_factory=list, description="List of chunks at this stage."
    )
    latency_ms: float = Field(0.0, description="Stage execution time in milliseconds.")
    candidate_count: int = Field(0, description="Number of candidate chunks fetched or processed.")
    score_range: Optional[List[float]] = Field(
        None, description="Min and max score range [min, max] at this stage."
    )
    duplicates_removed: Optional[int] = Field(
        None, description="Number of duplicate or filtered-out chunks."
    )
    rejected_results: Optional[List[ChunkTrace]] = Field(
        None, description="List of rejected chunks at this stage."
    )


class TraceRetrieval(BaseModel):
    """Groups all step-by-step phases of the hybrid retrieval sub-pipeline."""

    vector_stage: Optional[RetrievalStageTrace] = Field(
        None, description="Raw results from vector semantic search."
    )
    bm25_stage: Optional[RetrievalStageTrace] = Field(
        None, description="Raw results from BM25 lexical search."
    )
    rrf_stage: Optional[RetrievalStageTrace] = Field(
        None, description="Results after Reciprocal Rank Fusion."
    )
    diversified_stage: Optional[RetrievalStageTrace] = Field(
        None, description="Results after source diversification rules."
    )
    graded_stage: Optional[RetrievalStageTrace] = Field(
        None, description="Final results kept after LLM grader filtering."
    )
    final_context: Optional[str] = Field(
        None, description="The compiled context string sent to the LLM."
    )


class TraceGeneration(BaseModel):
    """Captures generation details and response previews."""

    response_preview: Optional[str] = Field(
        None, description="A preview of the generated answer (first 300 characters)."
    )
    latency_ms: float = Field(0.0, description="Response generation time in milliseconds.")
    token_count: Optional[int] = Field(
        None, description="Token size of the prompt context or generation."
    )


class TraceTimings(BaseModel):
    """Consolidates execution latencies across major blocks of the orchestrator."""

    query_processing_ms: float = Field(
        0.0, description="Query rewriting and project detection latency in milliseconds."
    )
    total_retrieval_ms: float = Field(
        0.0, description="Total hybrid retrieval latency in milliseconds."
    )
    generation_ms: float = Field(
        0.0,
        description="LLM prompt building and streaming response generation latency in milliseconds.",
    )
    total_request_ms: float = Field(
        0.0, description="Total end-to-end request latency in milliseconds."
    )
    stages: Dict[str, float] = Field(
        default_factory=dict,
        description="Key-value mapping of custom sub-stages to latency (e.g., project_detection: 12.4).",
    )


class TraceMetadata(BaseModel):
    """Environment, cache, and system metadata for the execution."""

    timestamp: float = Field(
        default_factory=time.time, description="Unix timestamp of the request."
    )
    cache_hit: bool = Field(False, description="Whether the request hit the Redis cache.")
    model_name: Optional[str] = Field(
        None, description="LLM provider and model version string used."
    )


class PipelineTrace(BaseModel):
    """Root model representing the entire diagnostic trace of a RAG query execution."""

    request: TraceRequest = Field(default_factory=TraceRequest)
    retrieval: TraceRetrieval = Field(default_factory=TraceRetrieval)
    generation: TraceGeneration = Field(default_factory=TraceGeneration)
    timings: TraceTimings = Field(default_factory=TraceTimings)
    metadata: TraceMetadata = Field(default_factory=TraceMetadata)
