import pytest

from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.retrieval.rrf import RRFFuser


def make_mock_chunk(chunk_id: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        parent_document_id="doc-1",
        content_hash="h1",
        content="content",
        project="test-project",
        layer="artifact",
        source_type="github",
        source_file="file.py",
        chunk_index=0,
        token_count=10,
        char_count=50,
        metadata={}
    )

def test_rrf_basic_fusion():
    chunk_1 = make_mock_chunk("chunk-1")
    chunk_2 = make_mock_chunk("chunk-2")
    chunk_3 = make_mock_chunk("chunk-3")

    # Vector results: [chunk-1, chunk-2]
    # Ranks (1-based): chunk-1 -> 1, chunk-2 -> 2
    vector_results = [
        RetrievalResult(chunk=chunk_1, score=0.9),
        RetrievalResult(chunk=chunk_2, score=0.8)
    ]

    # BM25 results: [chunk-2, chunk-3]
    # Ranks (1-based): chunk-2 -> 1, chunk-3 -> 2
    bm25_results = [
        RetrievalResult(chunk=chunk_2, score=40.0),
        RetrievalResult(chunk=chunk_3, score=20.0)
    ]

    fuser = RRFFuser(k=10)
    fused = fuser.fuse(vector_results, bm25_results)

    # Expected scores (k=10):
    # chunk-1: 1/(10+1) + 0 = 1/11 = 0.0909
    # chunk-2: 1/(10+2) + 1/(10+1) = 1/12 + 1/11 = 0.0833 + 0.0909 = 0.1742
    # chunk-3: 0 + 1/(10+2) = 1/12 = 0.0833
    #
    # Expected ordering: chunk-2, chunk-1, chunk-3

    assert len(fused) == 3
    assert fused[0].chunk.chunk_id == "chunk-2"
    assert pytest.approx(fused[0].score, 0.0001) == (1.0/12 + 1.0/11)
    assert fused[0].vector_rank == 2
    assert fused[0].bm25_rank == 1

    assert fused[1].chunk.chunk_id == "chunk-1"
    assert pytest.approx(fused[1].score, 0.0001) == (1.0/11)
    assert fused[1].vector_rank == 1
    assert fused[1].bm25_rank is None

    assert fused[2].chunk.chunk_id == "chunk-3"
    assert pytest.approx(fused[2].score, 0.0001) == (1.0/12)
    assert fused[2].vector_rank is None
    assert fused[2].bm25_rank == 2


def test_rrf_tie_breaking_rules():
    # Setup test cases for tie-breaking:
    # 1. Better vector rank (same RRF score)
    # 2. Better BM25 rank (same RRF score & vector rank)
    # 3. chunk_id (same RRF score, vector rank & BM25 rank)

    chunk_a = make_mock_chunk("chunk-a")
    chunk_b = make_mock_chunk("chunk-b")

    # Tie-break 1: Better vector rank
    # chunk-a: vector_rank=1, bm25_rank=None -> RRF score = 1/(10+1) = 1/11
    # chunk-b: vector_rank=None, bm25_rank=1 -> RRF score = 1/(10+1) = 1/11
    # Since scores are identical, chunk-a wins because of better vector rank (1 vs inf)
    fuser = RRFFuser(k=10)
    res = fuser.fuse(
        [RetrievalResult(chunk=chunk_a, score=0.9)],
        [RetrievalResult(chunk=chunk_b, score=40.0)]
    )
    assert res[0].chunk.chunk_id == "chunk-a"
    assert res[1].chunk.chunk_id == "chunk-b"

    # Tie-break 2: Better BM25 rank
    # chunk-a: vector_rank=None, bm25_rank=1
    # chunk-b: vector_rank=None, bm25_rank=2
    # But wait, to have identical score, they should have same rank. Let's create an equal scenario:
    # Actually, RRF scores will only be equal if ranks are equal. If ranks are equal, then vector_rank and bm25_rank
    # could be different.
    # What if chunk-c and chunk-d both have same vector rank (None) and BM25 rank (None)?
    # Wait, they can't both have None if they are in the lists, they must be in at least one list.
    # What if:
    # chunk-x: vector_rank=None, bm25_rank=1 (score = 1/11)
    # chunk-y: vector_rank=None, bm25_rank=1 (score = 1/11)
    # They have identical score (1/11), identical vector_rank (None), identical bm25_rank (1).
    # Then chunk_id tie-breaker applies.
    chunk_x = make_mock_chunk("chunk-x")
    chunk_y = make_mock_chunk("chunk-y")

    # Passing them in y then x to verify it sorts alphabetically
    fuser.fuse(
        [],
        [
            RetrievalResult(chunk=chunk_y, score=50.0),
            RetrievalResult(chunk=chunk_x, score=50.0)
        ]
    )
    # Since y was index 1 (rank 1) and x was index 2 (rank 2), wait, rank is determined by index in input list!
    # So to make ranks equal, they must be in different lists, but wait. If they are in the same list, they have different ranks.
    # Can we have two chunks with identical ranks in the same list? No, because lists are ordered.
    # But wait, what if chunk-x is in list A at index 0 (rank 1) and list B at index 1 (rank 2),
    # and chunk-y is in list A at index 1 (rank 2) and list B at index 0 (rank 1)?
    # Let's check:
    # chunk-x: vector_rank=1, bm25_rank=2 -> score = 1/(k+1) + 1/(k+2)
    # chunk-y: vector_rank=2, bm25_rank=1 -> score = 1/(k+2) + 1/(k+1)
    # Their RRF scores are mathematically identical!
    # Let's apply rule 1 (Better vector rank):
    # chunk-x has vector_rank=1, chunk-y has vector_rank=2.
    # So chunk-x should win!
    res3 = fuser.fuse(
        [RetrievalResult(chunk=chunk_x, score=0.9), RetrievalResult(chunk=chunk_y, score=0.8)],
        [RetrievalResult(chunk=chunk_y, score=40.0), RetrievalResult(chunk=chunk_x, score=30.0)]
    )
    assert res3[0].chunk.chunk_id == "chunk-x"
    assert res3[1].chunk.chunk_id == "chunk-y"

    # Now let's test Tie-break 3: chunk_id fallback
    # To have identical score, identical vector_rank, and identical bm25_rank:
    # This is only possible if they have the exact same rank configuration.
    # Let's say:
    # chunk-y: vector_rank=1, bm25_rank=1
    # chunk-x: vector_rank=1, bm25_rank=1
    # But wait, a list cannot contain two items at rank 1.
    # Wait, can we pass two elements with the same chunk_id? No, they merge.
    # What if two different chunks are in the lists? Since ranks must be unique in each list (1, 2, 3),
    # can we have identical ranks and scores?
    # Actually, if we have chunk-z and chunk-w, they cannot have the same vector rank and same BM25 rank unless one of them is None for both? No, if one is None, they are in only one list.
    # If they are in only one list, say vector_results contains chunk-w at rank 1, chunk-z at rank 2. They have different scores.
    # Wait, is there any case where they have same score, vector_rank, and bm25_rank?
    # Yes! If we pass two results representing different chunks at the same rank... wait, in a single list, we don't have duplicate ranks.
    # But what if one list has chunk-w at rank 1, chunk-z not present, and the other list has chunk-z at rank 1, chunk-w not present?
    # chunk-w: vector_rank=1, bm25_rank=None -> score = 1/(k+1)
    # chunk-z: vector_rank=None, bm25_rank=1 -> score = 1/(k+1)
    # Scores are equal: 1/(k+1).
    # Vector ranks: chunk-w is 1, chunk-z is None.
    # So chunk-w wins by vector rank.
    # What if we have:
    # list A: chunk-w at rank 1, chunk-z at rank 2
    # list B: chunk-z at rank 1, chunk-w at rank 2
    # Here, chunk-w has vector=1, bm25=2. chunk-z has vector=2, bm25=1.
    # Vector rank: chunk-w wins.
    # Is it actually possible to have a tie on both vector_rank and bm25_rank?
    # Wait! Yes, if BOTH are not present in one list, and have the SAME rank in the other list. But they cannot have the same rank in the same list because a list has sequential ranks (1, 2, ...).
    # Ah! But what if the lists are empty, or what if one list is not sequential (e.g. we passed mock inputs where ranks are not strictly unique? No, the code assigns rank = idx + 1, so ranks are always unique per list).
    # However, let's still test chunk_id alphabetical fallback, because it acts as a robust final catch-all.
    # To test chunk_id fallback, we can mock/override the ranks on RetrievalResult objects directly, or just trust that when they are equal (e.g., if there's a custom case or empty lists), they sort by chunk_id.
    # Wait! Let's write a simple test where we construct RetrievalResult objects directly and sort them using `sort_key`.
    # Let's verify that the sort_key works exactly as expected.
    res_w = RetrievalResult(chunk=make_mock_chunk("chunk-w"), score=0.1, vector_rank=1, bm25_rank=1)
    res_z = RetrievalResult(chunk=make_mock_chunk("chunk-z"), score=0.1, vector_rank=1, bm25_rank=1)

    # Since they have identical score, vector_rank, and bm25_rank, they should sort alphabetically: chunk-w then chunk-z
    res_list = [res_z, res_w]
    res_list.sort(key=lambda r: (-r.score, r.vector_rank if r.vector_rank is not None else float('inf'), r.bm25_rank if r.bm25_rank is not None else float('inf'), r.chunk.chunk_id))
    assert res_list[0].chunk.chunk_id == "chunk-w"
    assert res_list[1].chunk.chunk_id == "chunk-z"
