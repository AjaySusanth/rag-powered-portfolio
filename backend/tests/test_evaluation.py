"""
WHY THIS WAS CHOSEN:
This test suite verifies the correctness of the dataset validation rules and evaluation metrics
(Recall@K, Hit Rate, MRR, Layer Recall, Category Accuracy) under various scenarios.
Mocking the database pool and retriever allows testing these features in isolation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Optional

from src.evaluation.dataset_validator import DatasetValidator, DatasetValidationError
from src.evaluation.retrieval_evaluator import RetrievalEvaluator, Retriever
from src.models.retrieval_result import RetrievalResult
from src.models.chunk import Chunk


# A Mock Retriever implementation
class DummyRetriever(Retriever):
    def __init__(self, mock_results):
        self.mock_results = mock_results
        self.call_count = 0

    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        self.call_count += 1
        return self.mock_results.get(query, [])


@pytest.fixture
def valid_dataset_data():
    return {
        "project": "talentforge",
        "generated_at": "2026-06-25T12:00:00Z",
        "questions": [
            {
                "id": "TF-001",
                "category": "core_logic",
                "question": "How does ranking work?",
                "expected_sources": ["src/ranking.py"],
                "expected_layers": ["design"],
                "reason": "Ranking core is in ranking.py"
            },
            {
                "id": "TF-002",
                "category": "pipeline",
                "question": "How does CI work?",
                "expected_sources": ["ci.yml"],
                "expected_layers": ["artifact"],
                "reason": "CI runs ci.yml"
            }
        ]
    }


def test_schema_validation_valid(valid_dataset_data):
    # Should not raise an exception
    DatasetValidator.validate_schema(valid_dataset_data)


def test_schema_validation_empty():
    with pytest.raises(DatasetValidationError, match="Dataset is empty."):
        DatasetValidator.validate_schema({})


def test_schema_validation_missing_project(valid_dataset_data):
    del valid_dataset_data["project"]
    # Should not raise an exception since project is optional now
    DatasetValidator.validate_schema(valid_dataset_data)


def test_schema_validation_duplicate_ids(valid_dataset_data):
    valid_dataset_data["questions"][1]["id"] = "TF-001"
    with pytest.raises(DatasetValidationError, match="Duplicate question ID found: TF-001"):
        DatasetValidator.validate_schema(valid_dataset_data)


def test_schema_validation_invalid_category(valid_dataset_data):
    valid_dataset_data["questions"][0]["category"] = "invalid_category_name"
    with pytest.raises(DatasetValidationError, match="has invalid category"):
        DatasetValidator.validate_schema(valid_dataset_data)


def test_schema_validation_invalid_layer(valid_dataset_data):
    valid_dataset_data["questions"][0]["expected_layers"] = ["invalid_layer"]
    with pytest.raises(DatasetValidationError, match="has invalid layer"):
        DatasetValidator.validate_schema(valid_dataset_data)


def test_schema_validation_sources_layers_mismatch(valid_dataset_data):
    valid_dataset_data["questions"][0]["expected_layers"] = ["design", "artifact"]
    with pytest.raises(DatasetValidationError, match="length of 'expected_sources' .* does not match"):
        DatasetValidator.validate_schema(valid_dataset_data)


def test_schema_validation_minimum_match_validation(valid_dataset_data):
    # minimum_match exceeds expected_sources length
    valid_dataset_data["questions"][0]["minimum_match"] = 2
    with pytest.raises(DatasetValidationError, match="cannot be greater than the number of 'expected_sources'"):
        DatasetValidator.validate_schema(valid_dataset_data)


@pytest.mark.anyio
@patch("src.evaluation.dataset_validator.get_db_pool", new_callable=AsyncMock)
async def test_knowledge_base_validation_missing_files(mock_get_pool, valid_dataset_data):
    # Mock database to return only one of the files
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [{"source_file": "src/ranking.py"}]
    
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_conn
    
    mock_pool = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=mock_context_manager)
    mock_get_pool.return_value = mock_pool

    with pytest.raises(DatasetValidationError, match="expected source files are missing"):
        await DatasetValidator.validate_knowledge_base(
            "talentforge", 
            valid_dataset_data["questions"], 
            db_check=True
        )


@pytest.mark.anyio
@patch("src.evaluation.dataset_validator.get_db_pool", new_callable=AsyncMock)
async def test_knowledge_base_validation_success(mock_get_pool, valid_dataset_data):
    # Mock database to return both files
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = [
        {"source_file": "src/ranking.py"},
        {"source_file": "ci.yml"}
    ]
    
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_conn
    
    mock_pool = AsyncMock()
    mock_pool.acquire = MagicMock(return_value=mock_context_manager)
    mock_get_pool.return_value = mock_pool

    # Should not raise an error
    await DatasetValidator.validate_knowledge_base(
        "talentforge", 
        valid_dataset_data["questions"], 
        db_check=True
    )


@pytest.mark.anyio
async def test_retrieval_evaluator_metrics(valid_dataset_data):
    # Setup dummy chunk responses
    chunk_1 = Chunk(
        chunk_id="c1", parent_document_id="d1", project="talentforge",
        layer="design", source_type="github", source_file="src/ranking.py",
        chunk_index=0, content="code details", content_hash="h1",
        token_count=10, char_count=20, metadata={}
    )
    chunk_2 = Chunk(
        chunk_id="c2", parent_document_id="d2", project="talentforge",
        layer="artifact", source_type="github", source_file="wrong_file.py",
        chunk_index=0, content="random code", content_hash="h2",
        token_count=10, char_count=20, metadata={}
    )
    chunk_3 = Chunk(
        chunk_id="c3", parent_document_id="d3", project="talentforge",
        layer="artifact", source_type="github", source_file="ci.yml",
        chunk_index=0, content="yaml details", content_hash="h3",
        token_count=10, char_count=20, metadata={}
    )

    # Question 1: Hit rank 1
    # Question 2: Hit rank 2 (first chunk is wrong_file, second is ci.yml)
    mock_results = {
        "How does ranking work?": [
            RetrievalResult(chunk=chunk_1, score=0.9)
        ],
        "How does CI work?": [
            RetrievalResult(chunk=chunk_2, score=0.8),
            RetrievalResult(chunk=chunk_3, score=0.7)
        ]
    }

    retriever = DummyRetriever(mock_results)
    evaluator = RetrievalEvaluator(retriever)

    # Disable db check for unit tests
    result = await evaluator.evaluate_dataset(valid_dataset_data, top_k=5, db_check=False)

    assert result.project == "talentforge"
    assert result.total_questions == 2
    assert result.top_k == 5

    # Recall: 1.0 (both questions matched their 1 expected source file)
    assert result.recall == 1.0
    # Hit rate: 1.0
    assert result.hit_rate == 1.0
    # MRR: (1/1 + 1/2) / 2 = 0.75
    assert result.mrr == 0.75
    # Average Similarity: (0.9 + 0.7) / 2 = 0.8
    assert result.average_similarity == 0.8

    # Failures list should be empty
    assert len(result.failures) == 0

    # Test category breakdown
    cat_metrics = {cm.category: cm for cm in result.category_metrics}
    assert "core_logic" in cat_metrics
    assert cat_metrics["core_logic"].total_questions == 1
    assert cat_metrics["core_logic"].mrr == 1.0
    assert cat_metrics["core_logic"].average_similarity == 0.9

    assert "pipeline" in cat_metrics
    assert cat_metrics["pipeline"].total_questions == 1
    assert cat_metrics["pipeline"].mrr == 0.5
    assert cat_metrics["pipeline"].average_similarity == 0.7

    # Test layer breakdown
    layer_metrics = {lm.layer: lm for lm in result.layer_metrics}
    assert "design" in layer_metrics
    assert layer_metrics["design"].total_questions == 1
    assert layer_metrics["design"].mrr == 1.0
    assert layer_metrics["design"].recall == 1.0

    assert "artifact" in layer_metrics
    assert layer_metrics["artifact"].total_questions == 1
    assert layer_metrics["artifact"].mrr == 0.5
    assert layer_metrics["artifact"].recall == 1.0


@pytest.mark.anyio
async def test_retrieval_evaluator_failures(valid_dataset_data):
    # Setup dummy chunk responses (no matches)
    chunk_wrong = Chunk(
        chunk_id="c2", parent_document_id="d2", project="talentforge",
        layer="artifact", source_type="github", source_file="wrong_file.py",
        chunk_index=0, content="random code", content_hash="h2",
        token_count=10, char_count=20, metadata={}
    )

    mock_results = {
        "How does ranking work?": [
            RetrievalResult(chunk=chunk_wrong, score=0.5)
        ],
        "How does CI work?": []
    }

    retriever = DummyRetriever(mock_results)
    evaluator = RetrievalEvaluator(retriever)

    result = await evaluator.evaluate_dataset(valid_dataset_data, top_k=5, db_check=False)

    assert result.recall == 0.0
    assert result.hit_rate == 0.0
    assert result.mrr == 0.0
    assert result.average_similarity == 0.0
    assert len(result.failures) == 2
    assert result.failures[0].question_id == "TF-001"
    assert result.failures[0].failure_reason == "No expected sources retrieved."
