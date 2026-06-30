import pytest
from src.models.retrieval_result import RetrievalResult
from src.models.chunk import Chunk
from src.retrieval.diversification import diversify_by_source

def make_mock_chunk(chunk_id: str, source_file: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        parent_document_id="doc-1",
        content_hash="h1",
        content="content",
        project="n8n",
        layer="artifact",
        source_type="github",
        source_file=source_file,
        chunk_index=0,
        token_count=10,
        char_count=50,
        metadata={}
    )

def test_diversify_by_source_basic():
    # Setup results:
    # 1. file_a.py (score 0.9)
    # 2. file_b.py (score 0.8)
    # 3. file_a.py (score 0.7) - duplicate
    # 4. file_c.py (score 0.6)
    # 5. file_b.py (score 0.5) - duplicate
    results = [
        RetrievalResult(chunk=make_mock_chunk("c1", "file_a.py"), score=0.9),
        RetrievalResult(chunk=make_mock_chunk("c2", "file_b.py"), score=0.8),
        RetrievalResult(chunk=make_mock_chunk("c3", "file_a.py"), score=0.7),
        RetrievalResult(chunk=make_mock_chunk("c4", "file_c.py"), score=0.6),
        RetrievalResult(chunk=make_mock_chunk("c5", "file_b.py"), score=0.5),
    ]

    # Limit = 2. Should return file_a.py (c1) and file_b.py (c2)
    div_2 = diversify_by_source(results, limit=2)
    assert len(div_2) == 2
    assert div_2[0].chunk.chunk_id == "c1"
    assert div_2[1].chunk.chunk_id == "c2"

    # Limit = 3. Should return file_a.py (c1), file_b.py (c2), file_c.py (c4)
    div_3 = diversify_by_source(results, limit=3)
    assert len(div_3) == 3
    assert div_3[0].chunk.chunk_id == "c1"
    assert div_3[1].chunk.chunk_id == "c2"
    assert div_3[2].chunk.chunk_id == "c4"

    # Limit = 5. Should only return 3 results because we only have 3 unique files
    div_5 = diversify_by_source(results, limit=5)
    assert len(div_5) == 3

def test_diversify_by_source_empty():
    assert diversify_by_source([], limit=5) == []
