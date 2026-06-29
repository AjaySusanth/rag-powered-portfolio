"""
WHY THIS WAS CHOSEN:
This module contains the RetrievalDiagnostics runner, which is kept completely separate
from the standard RetrievalEvaluator. It queries both Vector and BM25 retrievers at a depth
of 20 candidates, performs RRF fusion, and classifies failures for target expected documents
into mutually exclusive categories to isolate the exact bottleneck in the retrieval pipeline.
"""

import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set
from src.retrieval import vector_retriever, bm25_retriever
from src.retrieval.rrf import RRFFuser
from src.models.retrieval_result import RetrievalResult

logger = logging.getLogger(__name__)

@dataclass
class DiagnosticTrace:
    """Represents the retrieval trace of a single candidate document."""
    source_file: str
    vector_rank: Optional[int]
    bm25_rank: Optional[int]
    rrf_score: float
    fused_rank: int

@dataclass
class FailureDetail:
    """Detailed diagnostics of a single unretrieved expected source."""
    source_file: str
    category: str  # Missing from both, Candidate starvation, Fusion ordering, Duplicate domination
    explanation: str
    recommendation: str
    vector_rank: Optional[int]
    bm25_rank: Optional[int]
    rrf_rank: Optional[int]

@dataclass
class QueryDiagnostics:
    """Diagnostic state for a single query."""
    question_id: str
    question: str
    is_hit: bool
    overlap_count: int
    jaccard_overlap: float
    duplicate_density: float  # avg chunks per unique source in top-5
    failures: List[FailureDetail]
    top_5_sources: List[str]

@dataclass
class DiagnosticsSummary:
    """Global diagnostics summary for the dataset."""
    project: str
    total_queries: int
    failed_queries: int
    failure_category_counts: Dict[str, int]
    avg_overlap_count: float
    avg_jaccard_overlap: float
    avg_duplicate_density: float
    top_recommendation: str
    query_details: List[QueryDiagnostics]


class RetrievalDiagnostics:
    """
    Orchestrates deep diagnostics of the retrieval pipeline by querying
    underlying systems at top_k=20 and analyzing failures.
    """
    def __init__(self, k: int = 60):
        self.fuser = RRFFuser(k=k)

    async def analyze_dataset(self, dataset: Dict[str, Any]) -> DiagnosticsSummary:
        """
        Runs diagnostics over a complete golden dataset.
        """
        project = dataset["project"]
        questions = dataset["questions"]
        
        query_details: List[QueryDiagnostics] = []
        
        for q in questions:
            q_id = q["id"]
            question_text = q["question"]
            expected_sources = q["expected_sources"]
            minimum_match = q.get("minimum_match", 1)
            
            # 1. Fetch top-20 candidates concurrently
            vector_task = vector_retriever.retrieve(query=question_text, top_k=20, project=project)
            bm25_task = bm25_retriever.retrieve(query=question_text, top_k=20, project=project)
            vector_20, bm25_20 = await asyncio.gather(vector_task, bm25_task)
            
            # 2. Compute candidate overlap metrics
            vector_ids = {res.chunk.chunk_id for res in vector_20}
            bm25_ids = {res.chunk.chunk_id for res in bm25_20}
            overlap_count = len(vector_ids & bm25_ids)
            union_count = len(vector_ids | bm25_ids)
            jaccard_overlap = overlap_count / union_count if union_count > 0 else 0.0
            
            # 3. Fuse using RRF
            fused_all = self.fuser.fuse(vector_20, bm25_20)
            
            # Identify top-5 fused sources
            top_5_fused = fused_all[:5]
            top_5_sources = [res.chunk.source_file for res in top_5_fused]
            
            # Calculate duplicate density in top-5 (chunks per unique source)
            unique_top_5_sources = set(top_5_sources)
            duplicate_density = len(top_5_sources) / len(unique_top_5_sources) if unique_top_5_sources else 1.0
            
            # Determine if query succeeded (minimum match met in top-5)
            retrieved_expected = [src for src in top_5_sources if src in expected_sources]
            unique_retrieved_expected = set(retrieved_expected)
            is_hit = len(unique_retrieved_expected) >= minimum_match
            
            failures: List[FailureDetail] = []
            
            if not is_hit:
                # Find which expected sources were missed in the top 5
                missed_sources = [src for src in expected_sources if src not in unique_retrieved_expected]
                
                for missed_src in missed_sources:
                    # Trace ranking state of this missed source in the fused list
                    fused_match = None
                    for rank_idx, res in enumerate(fused_all):
                        if res.chunk.source_file == missed_src:
                            fused_match = (rank_idx + 1, res)
                            break
                            
                    # 1. Missing from both retrievers
                    if fused_match is None:
                        failures.append(FailureDetail(
                            source_file=missed_src,
                            category="Missing from both retrievers",
                            explanation=f"The expected file '{missed_src}' did not appear in the top-20 candidates of either Vector or BM25 search.",
                            recommendation="Improve retrieval quality, chunking, or indexing.",
                            vector_rank=None,
                            bm25_rank=None,
                            rrf_rank=None
                        ))
                    else:
                        rrf_rank, res = fused_match
                        vr = res.vector_rank
                        br = res.bm25_rank
                        
                        # 2. Candidate starvation
                        # Starvation occurs if the file was retrieved but both of its component ranks
                        # are beyond the top 5 limit (i.e. neither retriever would have fed it in a top-5 candidate run)
                        v_starved = vr is None or vr > 5
                        b_starved = br is None or br > 5
                        
                        if v_starved and b_starved:
                            failures.append(FailureDetail(
                                source_file=missed_src,
                                category="Candidate starvation",
                                explanation=f"The expected file was retrieved (fused rank: {rrf_rank}) but both Vector rank ({vr}) and BM25 rank ({br}) were > 5, preventing it from entering the fusion candidate pool under top-5 limits.",
                                recommendation="Increase retrieval candidate pool before fusion.",
                                vector_rank=vr,
                                bm25_rank=br,
                                rrf_rank=rrf_rank
                            ))
                        else:
                            # The file entered the fusion pool (at least one rank <= 5), but missed top 5 fused results.
                            # Deduplicate fused results by source file
                            dedup_fused: List[RetrievalResult] = []
                            seen_sources: Set[str] = set()
                            for r in fused_all:
                                if r.chunk.source_file not in seen_sources:
                                    seen_sources.add(r.chunk.source_file)
                                    dedup_fused.append(r)
                                    
                            # Find rank in deduplicated list
                            dedup_rank = None
                            for idx, r in enumerate(dedup_fused):
                                if r.chunk.source_file == missed_src:
                                    dedup_rank = idx + 1
                                    break
                                    
                            # 3. Fusion ordering
                            # If even after deduplication it remains outside top 5, RRF simply ranked it too low
                            if dedup_rank is None or dedup_rank > 5:
                                failures.append(FailureDetail(
                                    source_file=missed_src,
                                    category="Fusion ordering",
                                    explanation=f"The expected file entered the RRF pool but was ranked poorly (fused rank: {rrf_rank}, deduplicated rank: {dedup_rank}) due to weak scores in both retrievers.",
                                    recommendation="Tune RRF parameters or investigate fusion strategy.",
                                    vector_rank=vr,
                                    bm25_rank=br,
                                    rrf_rank=rrf_rank
                                ))
                            # 4. Duplicate source domination
                            # If deduplication would have successfully raised it into the top 5
                            else:
                                failures.append(FailureDetail(
                                    source_file=missed_src,
                                    category="Duplicate source domination",
                                    explanation=f"The expected file entered the RRF pool (fused rank: {rrf_rank}) but was crowded out of the top-5 by duplicate chunks of other source files. Deduplication would raise it to rank {dedup_rank}.",
                                    recommendation="Implement Source Diversification.",
                                    vector_rank=vr,
                                    bm25_rank=br,
                                    rrf_rank=rrf_rank
                                ))
                                
            query_details.append(QueryDiagnostics(
                question_id=q_id,
                question=question_text,
                is_hit=is_hit,
                overlap_count=overlap_count,
                jaccard_overlap=jaccard_overlap,
                duplicate_density=duplicate_density,
                failures=failures,
                top_5_sources=top_5_sources
            ))
            
        # 4. Compute global aggregations
        total_queries = len(questions)
        failed_queries = sum(1 for qd in query_details if not qd.is_hit)
        
        category_counts = {
            "Missing from both retrievers": 0,
            "Candidate starvation": 0,
            "Fusion ordering": 0,
            "Duplicate source domination": 0
        }
        
        for qd in query_details:
            for f in qd.failures:
                if f.category in category_counts:
                    category_counts[f.category] += 1
                    
        avg_overlap = sum(qd.overlap_count for qd in query_details) / total_queries if total_queries > 0 else 0.0
        avg_jaccard = sum(qd.jaccard_overlap for qd in query_details) / total_queries if total_queries > 0 else 0.0
        avg_dup_density = sum(qd.duplicate_density for qd in query_details) / total_queries if total_queries > 0 else 0.0
        
        # Determine top recommendation based on the dominant failure mode
        dominant_mode = max(category_counts, key=category_counts.get)
        if category_counts[dominant_mode] == 0:
            top_rec = "No failures detected. System is operating optimally."
        elif dominant_mode == "Missing from both retrievers":
            top_rec = "Retrieval quality improvements (improve retrieval quality, chunking, or indexing)."
        elif dominant_mode == "Candidate starvation":
            top_rec = "Larger candidate pool (increase retrieval candidate pool size before fusion)."
        elif dominant_mode == "Fusion ordering":
            top_rec = "Tune RRF parameters or investigate fusion strategy."
        else:
            top_rec = "Source Diversification (prevent duplicate source files from dominating the Top-K)."
            
        return DiagnosticsSummary(
            project=project,
            total_queries=total_queries,
            failed_queries=failed_queries,
            failure_category_counts=category_counts,
            avg_overlap_count=avg_overlap,
            avg_jaccard_overlap=avg_jaccard,
            avg_duplicate_density=avg_dup_density,
            top_recommendation=top_rec,
            query_details=query_details
        )
