"""
WHY THIS WAS CHOSEN:
We use strongly typed dataclasses for evaluation metrics to ensure that the evaluation framework
does not rely on raw dictionaries. This provides compile-time safety, easier JSON serialization,
and clear contracts between the evaluator and the reporting layers.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QuestionResult:
    question_id: str
    question: str
    category: str
    expected_sources: List[str]
    retrieved_sources: List[str]
    similarity_scores: List[float]
    is_hit: bool
    rank: Optional[int]
    expected_layers: List[str] = field(default_factory=list)
    failure_reason: Optional[str] = None
    rewritten_query: Optional[str] = None
    rewritten: Optional[bool] = None
    rewrite_explanation: Optional[str] = None
    rewrite_latency: Optional[float] = None


@dataclass
class CategoryMetrics:
    category: str
    total_questions: int
    hit_rate: float
    recall: float
    mrr: float
    average_similarity: float


@dataclass
class LayerMetrics:
    layer: str
    total_questions: int
    hit_rate: float
    recall: float
    mrr: float
    average_similarity: float


@dataclass
class EvaluationResult:
    project: str
    generated_at: str
    top_k: int
    total_questions: int
    recall: float
    hit_rate: float
    mrr: float
    average_similarity: float
    category_metrics: List[CategoryMetrics]
    layer_metrics: List[LayerMetrics]
    failures: List[QuestionResult]
    question_results: List[QuestionResult] = field(default_factory=list)
