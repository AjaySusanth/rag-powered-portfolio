"""
DESIGN DECISION:
This module orchestrates the core vector retrieval pipeline.
Given a natural language query, it generates an embedding vector, performs a cosine similarity
search against the pgvector database, and reconstructs the raw dictionary results back into
strongly-typed Chunk and RetrievalResult models.

Why return RetrievalResult:
This decoupling ensures that downstream consumers (e.g. grading, hybrid search) have consistent
access to both the chunks and their relevance scores without parsing raw dicts.
"""

import logging
import time
from typing import List, Optional

from src.embedding.azure_openai_embedder import embed_query
from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.observability.tracing import PipelineTrace
from src.vectorstore.pgvector_store import similarity_search

logger = logging.getLogger(__name__)


async def retrieve(
    query: str, top_k: int = 5, project: Optional[str] = None, trace: Optional[PipelineTrace] = None
) -> List[RetrievalResult]:
    """
    Executes a vector similarity search for the given natural language query.

    Pipeline:
    1. Embed the query using Azure OpenAI.
    2. Search the pgvector store for the closest `top_k` matches (optionally scoped to a project).
    3. Reconstruct canonical Chunk models from the database rows.
    4. Return a list of RetrievalResult objects combining the chunk and its similarity score.
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to retrieve. Returning empty results.")
        return []

    try:
        # 1. Embed the query
        t0 = time.perf_counter()
        query_vector = await embed_query(query)
        embed_duration = (time.perf_counter() - t0) * 1000.0
        if trace:
            trace.timings.stages["retrieval_embedding"] = embed_duration

        # 2. Execute pgvector similarity search
        t1 = time.perf_counter()
        rows = await similarity_search(
            query_embedding=query_vector, limit=top_k, project_filter=project
        )
        search_duration = (time.perf_counter() - t1) * 1000.0
        if trace:
            trace.timings.stages["retrieval_vector_db_search"] = search_duration

        # 3. Reconstruct models
        results: List[RetrievalResult] = []
        for row in rows:
            # Extract the similarity score injected by the pgvector query
            score = row.pop("similarity", 0.0)

            # Map remaining database fields to the Chunk dataclass
            chunk = Chunk(
                chunk_id=row.get("chunk_id", ""),
                parent_document_id=row.get("parent_document_id", ""),
                content_hash=row.get("content_hash", ""),
                content=row.get("content", ""),
                project=row.get("project", "unknown"),
                layer=row.get("layer", "unknown"),
                source_type=row.get("source_type", "unknown"),
                source_file=row.get("source_file", "unknown"),
                chunk_index=row.get("chunk_index", 0),
                token_count=row.get("token_count", 0),
                char_count=row.get("char_count", 0),
                metadata=row.get("metadata", {}),
            )

            results.append(RetrievalResult(chunk=chunk, score=score))

        return results

    except Exception as e:
        logger.error(f"Vector retrieval failed for query '{query}': {e}")
        raise
