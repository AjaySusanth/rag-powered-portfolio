"""
WHY THIS WAS CHOSEN:
This module contains the RetrievalEvaluator, which drives the evaluation pipeline.
It takes a retriever implementation (decoupled via Python Protocol), executes queries 
defined in validation-safe datasets, and calculates granular IR metrics (Recall@K, Hit Rate, MRR, 
Average Similarity, Layer Recall, Category Accuracy) alongside detailed failure logs.
"""
from typing import List, Dict, Any, Optional, Protocol
from src.models.evaluation_result import (
    EvaluationResult, QuestionResult, CategoryMetrics, LayerMetrics
)
from src.models.retrieval_result import RetrievalResult
from src.evaluation.dataset_validator import DatasetValidator

class Retriever(Protocol):
    async def retrieve(self, query: str, top_k: int, project: Optional[str] = None) -> List[RetrievalResult]:
        """Contract for any retrieval implementation (Vector, BM25, Hybrid, RRF)."""
        ...

class RetrievalEvaluator:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    async def evaluate_dataset(
        self, 
        dataset: Dict[str, Any], 
        top_k: int = 5, 
        db_check: bool = True
    ) -> EvaluationResult:
        """
        Runs the evaluator against a single validated dataset.
        """
        # Validate schema first
        DatasetValidator.validate_schema(dataset)
        
        project = dataset.get("project")
        # Validate expected sources exist in the database (can be bypassed for tests)
        await DatasetValidator.validate_knowledge_base(project, dataset["questions"], db_check=db_check)

        question_results: List[QuestionResult] = []

        for q in dataset["questions"]:
            q_id = q["id"]
            category = q["category"]
            question_text = q["question"]
            expected_sources = q["expected_sources"]
            expected_layers = q["expected_layers"]
            minimum_match = q.get("minimum_match", 1)

            # Invoke retriever
            retrieved = await self.retriever.retrieve(
                query=question_text, 
                top_k=top_k, 
                project=project
            )

            # Extract retrieved properties
            retrieved_sources = [r.chunk.source_file for r in retrieved]
            similarity_scores = [r.score for r in retrieved]

            # Find rank of the first correct match
            first_match_rank: Optional[int] = None
            for idx, res in enumerate(retrieved):
                if res.chunk.source_file in expected_sources:
                    first_match_rank = idx + 1
                    break

            # Calculate unique expected sources retrieved
            unique_retrieved_expected = set()
            for src in retrieved_sources:
                if src in expected_sources:
                    unique_retrieved_expected.add(src)

            recall = len(unique_retrieved_expected) / len(expected_sources)
            is_hit = len(unique_retrieved_expected) >= minimum_match

            failure_reason = None
            if not is_hit:
                if len(unique_retrieved_expected) == 0:
                    failure_reason = "No expected sources retrieved."
                else:
                    failure_reason = (
                        f"Retrieved {len(unique_retrieved_expected)} unique source(s), "
                        f"which is less than minimum_match={minimum_match}."
                    )

            # Extract rewrite details if the retriever supports it
            rewritten_query = None
            rewritten = None
            rewrite_explanation = None
            rewrite_latency = None
            if hasattr(self.retriever, "get_rewrite_details"):
                details = self.retriever.get_rewrite_details(question_text)
                if details:
                    rewritten_query = details.get("rewritten_query")
                    rewritten = details.get("rewritten")
                    rewrite_explanation = details.get("explanation")
                    rewrite_latency = details.get("latency")

            question_results.append(QuestionResult(
                question_id=q_id,
                question=question_text,
                category=category,
                expected_sources=expected_sources,
                retrieved_sources=retrieved_sources,
                similarity_scores=similarity_scores,
                is_hit=is_hit,
                rank=first_match_rank,
                expected_layers=expected_layers,
                failure_reason=failure_reason,
                rewritten_query=rewritten_query,
                rewritten=rewritten,
                rewrite_explanation=rewrite_explanation,
                rewrite_latency=rewrite_latency
            ))

        total_questions = len(question_results)
        
        # 1. Compute Global Metrics
        hits = sum(1 for r in question_results if r.is_hit)
        hit_rate = hits / total_questions if total_questions > 0 else 0.0
        
        global_recalls = [
            len(set(r.retrieved_sources) & set(r.expected_sources)) / len(r.expected_sources)
            for r in question_results
        ]
        avg_recall = sum(global_recalls) / total_questions if total_questions > 0 else 0.0

        mrr = sum(
            1.0 / r.rank if r.rank else 0.0
            for r in question_results
        ) / total_questions if total_questions > 0 else 0.0

        successful_scores = [
            r.similarity_scores[r.rank - 1]
            for r in question_results
            if r.rank is not None
        ]
        avg_similarity = sum(successful_scores) / len(successful_scores) if successful_scores else 0.0

        # 2. Compute Category Metrics
        categories = sorted(list({q.category for q in question_results}))
        category_metrics_list: List[CategoryMetrics] = []
        for cat in categories:
            cat_results = [r for r in question_results if r.category == cat]
            cat_total = len(cat_results)
            if cat_total == 0:
                continue
            cat_hits = sum(1 for r in cat_results if r.is_hit)
            cat_hit_rate = cat_hits / cat_total
            cat_recall = sum(
                len(set(r.retrieved_sources) & set(r.expected_sources)) / len(r.expected_sources)
                for r in cat_results
            ) / cat_total
            cat_mrr = sum(
                1.0 / r.rank if r.rank else 0.0
                for r in cat_results
            ) / cat_total
            cat_successful_scores = [
                r.similarity_scores[r.rank - 1]
                for r in cat_results
                if r.rank is not None
            ]
            cat_avg_similarity = sum(cat_successful_scores) / len(cat_successful_scores) if cat_successful_scores else 0.0

            category_metrics_list.append(CategoryMetrics(
                category=cat,
                total_questions=cat_total,
                hit_rate=cat_hit_rate,
                recall=cat_recall,
                mrr=cat_mrr,
                average_similarity=cat_avg_similarity
            ))

        # 3. Compute Layer Metrics
        layer_metrics_list: List[LayerMetrics] = []
        for layer in ["identity", "design", "artifact"]:
            layer_results = []
            for r in question_results:
                layer_indices = [i for i, l in enumerate(r.expected_layers) if l == layer]
                if layer_indices:
                    layer_results.append((r, layer_indices))

            layer_total = len(layer_results)
            if layer_total == 0:
                continue

            layer_hits = 0
            layer_recalls = []
            layer_mrrs = []
            layer_similarities = []

            for r, indices in layer_results:
                expected_sources_in_layer = [r.expected_sources[i] for i in indices]
                retrieved_in_layer = [src for src in r.retrieved_sources if src in expected_sources_in_layer]
                
                unique_retrieved_in_layer = set(retrieved_in_layer)
                recall_in_layer = len(unique_retrieved_in_layer) / len(expected_sources_in_layer)
                layer_recalls.append(recall_in_layer)

                if len(unique_retrieved_in_layer) > 0:
                    layer_hits += 1

                first_rank_in_layer = None
                for idx, src in enumerate(r.retrieved_sources):
                    if src in expected_sources_in_layer:
                        first_rank_in_layer = idx + 1
                        layer_similarities.append(r.similarity_scores[idx])
                        break
                
                layer_mrrs.append(1.0 / first_rank_in_layer if first_rank_in_layer else 0.0)

            layer_hit_rate = layer_hits / layer_total
            layer_avg_recall = sum(layer_recalls) / len(layer_recalls) if layer_recalls else 0.0
            layer_avg_mrr = sum(layer_mrrs) / len(layer_mrrs) if layer_mrrs else 0.0
            layer_avg_similarity = sum(layer_similarities) / len(layer_similarities) if layer_similarities else 0.0

            layer_metrics_list.append(LayerMetrics(
                layer=layer,
                total_questions=layer_total,
                hit_rate=layer_hit_rate,
                recall=layer_avg_recall,
                mrr=layer_avg_mrr,
                average_similarity=layer_avg_similarity
            ))

        failures = [r for r in question_results if not r.is_hit]

        return EvaluationResult(
            project=project,
            generated_at=dataset.get("generated_at", ""),
            top_k=top_k,
            total_questions=total_questions,
            recall=avg_recall,
            hit_rate=hit_rate,
            mrr=mrr,
            average_similarity=avg_similarity,
            category_metrics=category_metrics_list,
            layer_metrics=layer_metrics_list,
            failures=failures,
            question_results=question_results
        )
