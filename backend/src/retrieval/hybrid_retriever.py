"""
WHY THIS WAS CHOSEN:
This module orchestrates hybrid retrieval by executing semantic vector search and lexical BM25 search
concurrently. Combining both approaches compensates for the weaknesses of each: vector search retrieves 
conceptually relevant chunks that lack exact query keywords, while BM25 retrieves exact technical matching 
identifiers (such as function names or configuration lines) that might otherwise get lost in the embedding space.
"""

import asyncio
import logging
from typing import List, Optional

from src.models.retrieval_result import RetrievalResult
from src.retrieval import vector_retriever
from src.retrieval import bm25_retriever
from src.retrieval.rrf import RRFFuser
from src.retrieval.diversification import diversify_by_source

logger = logging.getLogger(__name__)

async def retrieve(
    query: str,
    top_k: int = 5,
    project: Optional[str] = None,
    candidate_k: int = 20,
    diversify: bool = True
) -> List[RetrievalResult]:
    """
    Executes a hybrid search query using both Vector and BM25 retrievers concurrently.
    Fetches candidate_k items from both retrievers to prevent candidate starvation,
    fuses the outputs using Reciprocal Rank Fusion (RRF), applies source diversification,
    and returns the final top_k results.
    """
    if not query or not query.strip():
        logger.warning("Empty query provided to hybrid retrieve. Returning empty results.")
        return []

    try:
        # Run both retrievers concurrently to reduce overall search latency.
        # Vector retriever makes network hops, while BM25 retriever runs in-memory.
        # Fetching candidate_k ensures documents pushed down by one retriever 
        # can still enter the fusion pool.
        vector_task = vector_retriever.retrieve(query=query, top_k=candidate_k, project=project)
        bm25_task = bm25_retriever.retrieve(query=query, top_k=candidate_k, project=project)
        
        vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)
        
        # Fuse and rank results using RRFFuser
        fuser = RRFFuser(k=60)
        fused_results = fuser.fuse(vector_results, bm25_results)
        
        # Apply source diversification if enabled
        if diversify:
            return diversify_by_source(fused_results, limit=top_k)
        
        # Return only the requested number of top results if diversification is disabled
        return fused_results[:top_k]

    except Exception as e:
        logger.error(f"Hybrid retrieval failed for query '{query}': {e}")
        raise

