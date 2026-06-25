"""
WHY THIS WAS CHOSEN:
This module implements the DatasetValidator, which enforces schema rules and verifies 
that all expected source files exist in the indexed database for a given project.
Enforcing validation prevents execution of outdated or malformed test cases, providing
fast feedback and preserving dataset integrity.
"""
from typing import Dict, Any, List
import logging
from src.db.core import get_db_pool

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"core_logic", "pipeline", "data_models", "infrastructure", "documentation"}
VALID_LAYERS = {"identity", "design", "artifact"}

class DatasetValidationError(Exception):
    """Custom exception raised when dataset validation fails."""
    pass

class DatasetValidator:
    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> None:
        """
        Validates the schema, duplicate IDs, missing fields, categories, layers,
        empty lists, minimum_match <= expected_sources.
        """
        if not data:
            raise DatasetValidationError("Dataset is empty.")
            
        project = data.get("project")
        if not project or not project.strip():
            raise DatasetValidationError("Dataset is missing a 'project' field.")
            
        questions = data.get("questions")
        if questions is None:
            raise DatasetValidationError("Dataset is missing 'questions' field.")
        if not isinstance(questions, list):
            raise DatasetValidationError("'questions' field must be a list.")
        if len(questions) == 0:
            raise DatasetValidationError("Dataset must contain at least one question.")
            
        seen_ids = set()
        for idx, q in enumerate(questions):
            q_id = q.get("id")
            if not q_id:
                raise DatasetValidationError(f"Question at index {idx} is missing an 'id'.")
            if q_id in seen_ids:
                raise DatasetValidationError(f"Duplicate question ID found: {q_id}")
            seen_ids.add(q_id)
            
            category = q.get("category")
            if not category:
                raise DatasetValidationError(f"Question {q_id} is missing a 'category'.")
            if category not in VALID_CATEGORIES:
                raise DatasetValidationError(
                    f"Question {q_id} has invalid category '{category}'. "
                    f"Must be one of {VALID_CATEGORIES}"
                )
                
            question_text = q.get("question")
            if not question_text or not question_text.strip():
                raise DatasetValidationError(f"Question {q_id} is missing 'question' text.")
                
            expected_sources = q.get("expected_sources")
            if not expected_sources or not isinstance(expected_sources, list):
                raise DatasetValidationError(f"Question {q_id} must have a non-empty 'expected_sources' list.")
                
            # Check duplicate expected sources
            if len(expected_sources) != len(set(expected_sources)):
                raise DatasetValidationError(f"Question {q_id} contains duplicate entries in 'expected_sources'.")
                
            expected_layers = q.get("expected_layers")
            if not expected_layers or not isinstance(expected_layers, list):
                raise DatasetValidationError(f"Question {q_id} must have a non-empty 'expected_layers' list.")
                
            if len(expected_sources) != len(expected_layers):
                raise DatasetValidationError(
                    f"Question {q_id}: length of 'expected_sources' ({len(expected_sources)}) "
                    f"does not match 'expected_layers' ({len(expected_layers)})."
                )
                
            for layer in expected_layers:
                if layer not in VALID_LAYERS:
                    raise DatasetValidationError(
                        f"Question {q_id} has invalid layer '{layer}'. "
                        f"Must be one of {VALID_LAYERS}"
                    )
                    
            # Check minimum match if present
            minimum_match = q.get("minimum_match")
            if minimum_match is not None:
                if not isinstance(minimum_match, int):
                    raise DatasetValidationError(f"Question {q_id}: 'minimum_match' must be an integer.")
                if minimum_match <= 0:
                    raise DatasetValidationError(f"Question {q_id}: 'minimum_match' must be greater than 0.")
                if minimum_match > len(expected_sources):
                    raise DatasetValidationError(
                        f"Question {q_id}: 'minimum_match' ({minimum_match}) cannot be greater than "
                        f"the number of 'expected_sources' ({len(expected_sources)})."
                    )

    @staticmethod
    async def validate_knowledge_base(project: str, questions: List[Dict[str, Any]], db_check: bool = True) -> None:
        """
        Validates that all expected source files exist in the indexed database for the given project.
        """
        if not db_check:
            return

        all_sources = set()
        for q in questions:
            for src in q.get("expected_sources", []):
                all_sources.add(src)
                
        if not all_sources:
            return
            
        try:
            pool = await get_db_pool()
        except Exception as e:
            raise DatasetValidationError(
                f"Failed to connect to database for knowledge base validation: {e}. "
                "Ensure PostgreSQL is running and seeded."
            )
            
        async with pool.acquire() as conn:
            query = "SELECT DISTINCT source_file FROM chunks WHERE project = $1 AND source_file = any($2::text[])"
            rows = await conn.fetch(query, project, list(all_sources))
            existing = {row["source_file"] for row in rows}
            
            missing = all_sources - existing
            if missing:
                raise DatasetValidationError(
                    f"The following expected source files are missing from the indexed knowledge base "
                    f"for project '{project}': {sorted(list(missing))}. "
                    "Please ensure these files are indexed before running the evaluation."
                )
