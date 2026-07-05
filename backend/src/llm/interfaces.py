"""
WHY THIS WAS CHOSEN:
We define base interfaces for all LLM interactions in a centralized interfaces file.
This decouples our higher-level pipelines (like retrieval grading or answer generation)
from specific API vendors (like Google Gemini, OpenAI, or local Llama instances),
enabling easy testing and provider swapping.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Literal, Optional

from pydantic import BaseModel, Field

from src.models.retrieval_result import RetrievalResult


class ChunkGrade(BaseModel):
    chunk_index: int = Field(description="The 0-based index of the chunk in the input list.")
    is_relevant: bool = Field(description="True if the chunk contains information relevant to the user query, False otherwise.")
    rejection_reason: Optional[Literal[
        "answers_question",
        "background_only",
        "duplicate_information",
        "off_topic",
        "insufficient_information"
    ]] = Field(
        default=None,
        description="The category that describes the relevance status. If relevant, this is usually 'answers_question'."
    )
    explanation: Optional[str] = Field(
        default=None,
        description="A brief explanation for debugging why the chunk is relevant or irrelevant."
    )


class BaseGrader(ABC):
    """
    Abstract interface for a Retrieval Grader provider.
    All grading providers must implement this interface.
    """
    @abstractmethod
    async def grade(self, query: str, results: List[RetrievalResult]) -> List[ChunkGrade]:
        """
        Batch grade an ordered list of retrieved chunks against a query.

        Args:
            query: The user query string.
            results: The list of RetrievalResult objects to grade.

        Returns:
            A list of ChunkGrade results, one for each input chunk.
        """
        pass


class BaseGenerator(ABC):
    """
    Abstract interface for answer generation (streaming).
    """
    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generates answer tokens streaming from the LLM based on a prompt.
        """
        pass


class BaseCitationAttributor(ABC):
    """
    Abstract interface for post-generation citation attribution.
    Determines which chunks directly support the generated response.
    """
    @abstractmethod
    async def attribute_citations(
        self,
        answer: str,
        results: List[RetrievalResult]
    ) -> List[str]:
        """
        Filters a list of RetrievalResults, returning a list of chunk IDs
        that directly support statements made in the answer.
        """
        pass

