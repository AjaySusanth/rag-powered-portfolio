"""
DESIGN DECISION:
This test file validates the in-memory BM25 retrieval engine, ensuring tokenization correctness,
search ranking quality, metadata filtering behavior, and compliance with the canonical RetrievalResult schema.

We mock the PostgreSQL database dependency (`get_all_chunks`) to run these unit tests in-process
without requiring a live database or Docker container, keeping execution times fast.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.retrieval.bm25_retriever import BM25Index, index_instance, retrieve, tokenize_code


def test_tokenizer_basic():
    """
    Verifies that the tokenizer handles basic text: converting to lowercase,
    removing extra whitespace, and retaining numbers.
    """
    text = "  Hello World 123  "
    tokens = tokenize_code(text)
    assert tokens == ["hello", "world", "123"]


def test_tokenizer_camelcase():
    """
    Verifies that the tokenizer splits camelCase and PascalCase identifiers.
    This is critical for RAG queries searching codebases (e.g. searching 'auth'
    should match a chunk containing 'authMiddleware').
    """
    text = "authMiddleware HTTPResponse parseJWTToken123"
    tokens = tokenize_code(text)
    assert tokens == ["auth", "middleware", "http", "response", "parse", "jwt", "token", "123"]


def test_tokenizer_punctuation():
    """
    Verifies that all non-alphanumeric punctuation marks act as token delimiters.
    """
    text = "app.kubernetes.io/name: my-service_name"
    tokens = tokenize_code(text)
    assert tokens == ["app", "kubernetes", "io", "name", "my", "service", "name"]


@pytest.mark.anyio
@patch("src.retrieval.bm25_retriever.get_all_chunks", new_callable=AsyncMock)
async def test_empty_corpus_handling(mock_get_all_chunks):
    """
    Verifies that when the database is empty, the BM25 index handles it gracefully
    without raising exceptions and returns empty lists for searches.
    """
    mock_get_all_chunks.return_value = []

    # Instantiate a clean index to isolate test state
    test_index = BM25Index()
    await test_index.refresh_index()

    results = test_index.search("auth")
    assert results == []


@pytest.fixture
def mock_db_chunks():
    """Fixture providing dummy database chunk dicts similar to pgvector_store.get_all_chunks outputs."""
    return [
        {
            "chunk_id": "chunk-1",
            "parent_document_id": "doc-1",
            "content_hash": "hash1",
            "content": "Using backend authMiddleware for authorization and JWT validation in main.py.",
            "project": "n8n",
            "layer": "artifact",
            "source_type": "github",
            "source_file": "backend/app/main.py",
            "chunk_index": 0,
            "token_count": 10,
            "char_count": 70,
            "metadata": {}
        },
        {
            "chunk_id": "chunk-2",
            "parent_document_id": "doc-1",
            "content_hash": "hash2",
            "content": "Configuring app.kubernetes.io/name in service deployment manifest.",
            "project": "n8n",
            "layer": "artifact",
            "source_type": "github",
            "source_file": "k8s/deployment.yml",
            "chunk_index": 1,
            "token_count": 10,
            "char_count": 65,
            "metadata": {}
        },
        {
            "chunk_id": "chunk-3",
            "parent_document_id": "doc-2",
            "content_hash": "hash3",
            "content": "Resume details for senior backend developer, expert in Python and FastAPI.",
            "project": "__global__",
            "layer": "identity",
            "source_type": "manual",
            "source_file": "resume.md",
            "chunk_index": 0,
            "token_count": 12,
            "char_count": 74,
            "metadata": {}
        }
    ]


@pytest.mark.anyio
@patch("src.retrieval.bm25_retriever.get_all_chunks", new_callable=AsyncMock)
async def test_retrieval_ordering_and_shape(mock_get_all_chunks, mock_db_chunks):
    """
    Verifies that the retrieve function ranks chunks correctly based on BM25 frequency/overlap
    and returns correctly typed RetrievalResult / Chunk objects.
    """
    mock_get_all_chunks.return_value = mock_db_chunks

    test_index = BM25Index()
    await test_index.refresh_index()

    # Query matching chunk 1 heavily ("authMiddleware", "JWT", "authorization")
    results = test_index.search("JWT auth authorization", top_k=2)

    assert len(results) == 1  # Only chunk 1 should have a score > 0
    assert isinstance(results[0], RetrievalResult)
    assert isinstance(results[0].chunk, Chunk)

    assert results[0].chunk.chunk_id == "chunk-1"
    assert results[0].score > 0.0

    # Query matching chunk 2 ("kubernetes", "service")
    results2 = test_index.search("kubernetes deployment name", top_k=5)
    assert len(results2) == 1
    assert results2[0].chunk.chunk_id == "chunk-2"


@pytest.mark.anyio
@patch("src.retrieval.bm25_retriever.get_all_chunks", new_callable=AsyncMock)
async def test_project_filtering_parity(mock_get_all_chunks, mock_db_chunks):
    """
    Verifies that project filtering matches vector retriever behavior.
    Filtering by a specific project should exclude global documents, reflecting the known
    __global__ bug limitation.
    """
    mock_get_all_chunks.return_value = mock_db_chunks

    test_index = BM25Index()
    await test_index.refresh_index()

    # Querying "backend developer" with no project filter
    results_no_filter = test_index.search("backend developer", project=None)
    assert len(results_no_filter) == 2
    # chunk-3 (resume) and chunk-1 (authMiddleware for authorization)
    assert {r.chunk.chunk_id for r in results_no_filter} == {"chunk-1", "chunk-3"}

    # Querying "backend developer" filtered to project "n8n"
    # Should exclude chunk-3 because it is in "__global__" project, mirroring pgvector behavior.
    results_filtered = test_index.search("backend developer", project="n8n")
    assert len(results_filtered) == 1
    assert results_filtered[0].chunk.chunk_id == "chunk-1"


@pytest.mark.anyio
@patch("src.retrieval.bm25_retriever.get_all_chunks", new_callable=AsyncMock)
async def test_lazy_initialization(mock_get_all_chunks, mock_db_chunks):
    """
    Verifies that calling the module-level `retrieve()` function automatically triggers
    lazy initialization of the default `index_instance` singleton if not yet initialized.
    """
    mock_get_all_chunks.return_value = mock_db_chunks

    # Force state back to uninitialized for testing lazy init
    index_instance._is_initialized = False
    index_instance.bm25 = None

    results = await retrieve("kubernetes", project="n8n")
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "chunk-2"
    assert index_instance._is_initialized is True


def test_tokenizer_manual_cases():
    """
    Verifies tokenization behavior on specific technical identifiers:
    verifyJWT, verify_jwt, verify-jwt, JWT, jwt, authMiddleware, app.kubernetes.io/name
    """
    assert tokenize_code("verifyJWT") == ["verify", "jwt"]
    assert tokenize_code("verify_jwt") == ["verify", "jwt"]
    assert tokenize_code("verify-jwt") == ["verify", "jwt"]
    assert tokenize_code("JWT") == ["jwt"]
    assert tokenize_code("jwt") == ["jwt"]
    assert tokenize_code("authMiddleware") == ["auth", "middleware"]
    assert tokenize_code("app.kubernetes.io/name") == ["app", "kubernetes", "io", "name"]
