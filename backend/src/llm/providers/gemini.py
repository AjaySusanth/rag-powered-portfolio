"""
WHY THIS WAS CHOSEN:
This module implements the Gemini-based Retrieval Grader.
It batches all retrieved chunks into a single prompt and requests a structured JSON array
using the Gemini 2.0/2.5 schema-enforcement features. This avoids making multiple sequential or parallel
LLM calls, which significantly reduces latency and token cost.
"""

import logging
from typing import AsyncGenerator, List, Optional

from google.genai import types
from pydantic import BaseModel, Field

from src.config import settings
from src.llm.gemini_client import LLMError, get_gemini_client
from src.llm.interfaces import BaseGenerator, BaseGrader, ChunkGrade
from src.models.retrieval_result import RetrievalResult

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a Retrieval Quality Grader for an AI portfolio assistant.
Your task is to evaluate a batch of retrieved document chunks and determine if they are relevant to answering a user's query.

For each chunk, you must output a structured evaluation containing:
1. chunk_index: The 0-based index of the chunk in the provided list.
2. is_relevant: A boolean (true/false) indicating if the chunk contains information directly relevant to the user query.
3. rejection_reason: A string categorizing the relevance status. If is_relevant is true, you MUST choose 'answers_question'. If false, choose one of:
   - 'background_only': The chunk contains high-level design or background info that is contextually related but doesn't answer the specific question.
   - 'duplicate_information': The chunk contains details that are already present in another, higher-ranked chunk.
   - 'off_topic': The chunk is about a completely different topic, component, or system.
   - 'insufficient_information': The chunk touches the topic but contains no useful details to address the query.
4. explanation: A concise one-sentence explanation of your grading decision.

Be strict but fair. High-level design documents that do not provide concrete details for infrastructure/logic questions should generally be classified as 'background_only' (not_relevant) if more specific code/infrastructure chunks are present.
"""

class RetrievalGrading(BaseModel):
    """Container schema for batched chunk grading output."""
    grades: List[ChunkGrade] = Field(description="A list of grades corresponding to each of the evaluated chunks.")


class GeminiGrader(BaseGrader):
    """
    Retrieval Grader implementation using Google Gemini structured JSON outputs.
    """
    def __init__(self, model_name: str = settings.MODEL_GRADER):
        self.model_name = model_name

    def _format_prompt(self, query: str, results: List[RetrievalResult]) -> str:
        """Formats the query and chunks into a single batched text prompt."""
        prompt = f"User Query: {query}\n\n"
        prompt += "Retrieved Chunks to evaluate:\n"
        for i, res in enumerate(results):
            source = res.chunk.source_file or "unknown"
            content = res.chunk.content or ""
            prompt += f"--- CHUNK INDEX {i} (Source: {source}) ---\n{content}\n\n"
        return prompt

    async def grade(self, query: str, results: List[RetrievalResult]) -> List[ChunkGrade]:
        """
        Grades all chunks in a single batched call to the Gemini API.
        """
        if not results:
            return []

        import asyncio
        client = get_gemini_client()
        prompt_content = self._format_prompt(query, results)

        max_retries = 5
        backoff = 2.0  # seconds

        for attempt in range(max_retries):
            try:
                # Do NOT use the context manager 'async with client.aio' here because concurrent requests
                # running in parallel in the evaluation framework will close the connection pool prematurely.
                response = await client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt_content,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.0,
                        response_mime_type="application/json",
                        response_schema=RetrievalGrading,
                    )
                )

                # Parsed structured output is automatically available in response.parsed
                result: RetrievalGrading = response.parsed
                if result is None or not hasattr(result, "grades"):
                    logger.warning("Gemini did not return parsed grades, attempting fallback parsing.")
                    raise LLMError("Gemini structured output parsing failed.")

                return result.grades

            except Exception as e:
                err_str = str(e)
                # Check for rate limit (429) or temporary server unavailability (503)
                is_transient = any(code in err_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"])
                if is_transient and attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        f"Gemini API transient issue (attempt {attempt+1}/{max_retries}). "
                        f"Retrying in {sleep_time:.2f}s... Error: {e}"
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"Gemini retrieval grading failed after {attempt+1} attempts: {e}")
                    raise LLMError(f"Gemini retrieval grading failed: {e}") from e


class GeminiGenerator(BaseGenerator):
    """
    Answer Generator implementation using Google Gemini content streaming.
    """
    def __init__(self, model_name: str = settings.GEMINI_MODEL_NAME):
        self.model_name = model_name

    async def stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams answer tokens asynchronously from Gemini.
        """
        client = get_gemini_client()
        config = types.GenerateContentConfig(
            temperature=0.0,
        )
        if system_instruction:
            config.system_instruction = system_instruction

        try:
            response_stream = await client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise LLMError(f"Gemini streaming failed: {e}") from e

