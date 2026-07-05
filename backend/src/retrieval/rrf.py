"""
WHY THIS WAS CHOSEN:
We use Reciprocal Rank Fusion (RRF) to merge the rankings of vector search and BM25 search.
RRF is chosen because it is simple, parameter-free (other than a constant k), and highly robust.
It scores each document based on the reciprocal of its rank in each source list, preventing any single
scoring distribution (like cosine similarity vs BM25 raw scores) from dominating the merge.

Plain Language Explanation of RRF:
Reciprocal Rank Fusion (RRF) is a method that merges ranking scores from different retrieval engines without 
relying on their raw scores. Since vector search uses cosine similarity (typically 0.5 to 1.0) and BM25 uses 
term-frequency scaling (typically 0 to 50+), we cannot add their raw scores directly. Instead, RRF converts 
ranks (first, second, third, etc.) into reciprocal fractions (1 / (k + rank)) and sums them up. The constant k 
(default 60) regulates how much we penalize lower ranks.
"""

import logging
from typing import List, Dict, Any
from src.models.retrieval_result import RetrievalResult

logger = logging.getLogger(__name__)

class RRFFuser:
    """
    Reciprocal Rank Fusion (RRF) Fuser.
    
    RRF combines multiple ranked lists into a single ranked list. The score of a document d
    is computed as:
        RRF_Score(d) = sum_{m in models} 1 / (k + rank_m(d))
    where rank_m(d) is the 1-based rank of document d in model m's results.
    
    A default constant k = 60 is standard in research (e.g. Cormack et al.), as it ensures that
    consensus (presence in both lists) is valued higher than extreme outliers in a single list.
    """
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        vector_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        Fuses a list of vector search results and BM25 search results using RRF.
        Returns a sorted list of RetrievalResult objects descending by score.
        
        Tie-breaking rules:
        1. Better vector rank (lower rank is better).
        2. Better BM25 rank (lower rank is better).
        3. chunk_id (alphabetical order).
        """
        fused_data: Dict[str, Dict[str, Any]] = {}
        
        # Process vector results
        for idx, res in enumerate(vector_results):
            cid = res.chunk.chunk_id
            fused_data[cid] = {
                "chunk": res.chunk,
                "vector_rank": idx + 1,
                "bm25_rank": None
            }
            
        # Process BM25 results
        for idx, res in enumerate(bm25_results):
            cid = res.chunk.chunk_id
            if cid in fused_data:
                fused_data[cid]["bm25_rank"] = idx + 1
            else:
                fused_data[cid] = {
                    "chunk": res.chunk,
                    "vector_rank": None,
                    "bm25_rank": idx + 1
                }
                
        # Calculate RRF score for each unique chunk
        results: List[RetrievalResult] = []
        for cid, info in fused_data.items():
            vr = info["vector_rank"]
            br = info["bm25_rank"]
            
            score = 0.0
            if vr is not None:
                score += 1.0 / (self.k + vr)
            if br is not None:
                score += 1.0 / (self.k + br)
                
            results.append(RetrievalResult(
                chunk=info["chunk"],
                score=score,
                vector_rank=vr,
                bm25_rank=br
            ))
            
        # Sort results descending by RRF score, with tie-breaking
        # Python's Timsort is stable, but we can supply a composite key:
        # Key: (-score, vr_key, br_key, chunk_id)
        # where vr_key = vr if vr is not None else infinity (so smaller is better)
        # br_key = br if br is not None else infinity (so smaller is better)
        # chunk_id = string (alphabetical comparison)
        
        def sort_key(res: RetrievalResult) -> tuple:
            vr_val = res.vector_rank if res.vector_rank is not None else float('inf')
            br_val = res.bm25_rank if res.bm25_rank is not None else float('inf')
            return (-res.score, vr_val, br_val, res.chunk.chunk_id)
            
        results.sort(key=sort_key)
        return results
