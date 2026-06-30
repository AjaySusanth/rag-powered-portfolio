"""
WHY THIS WAS CHOSEN:
To implement source diversification as a distinct post-ranking selection stage. 
By keeping only the highest-ranked chunk from each unique source file and filtering 
out subsequent duplicate source files, we ensure that the Top-K results sent to the LLM 
contain a diverse set of references (context variety). This directly mitigates 
'duplicate source domination' where a single large document (like architecture.md) 
crowds out other specific codebase artifacts.
"""

from typing import List
from src.models.retrieval_result import RetrievalResult

def diversify_by_source(
    results: List[RetrievalResult],
    limit: int
) -> List[RetrievalResult]:
    """
    Greedily selects the highest-ranked chunk for each unique source file.
    It scans the ranked list of results, keeping only the first occurrence 
    of each source file until 'limit' unique sources are collected or 
    the input results list is exhausted.
    
    Concept Explanation:
    Source diversification ensures that we do not fill the LLM context window with 
    multiple redundant chunks from the same file. Instead, we select the highest-scoring 
    chunk from each source document, and remove any lower-ranked chunks from that same 
    document, allowing chunks from other unique files to rise into the Top-K.
    """
    seen_sources = set()
    diversified = []
    
    for res in results:
        source = res.chunk.source_file
        if source not in seen_sources:
            seen_sources.add(source)
            diversified.append(res)
            if len(diversified) == limit:
                break
                
    return diversified
