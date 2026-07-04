"""
WHY THIS WAS CHOSEN:
This service implements post-generation citation attribution. It determines which of the retrieved 
chunks directly support statements made in the generated answer, ensuring only accurate grounding 
sources are cited in the frontend rather than all retrieved candidate chunks.
"""

import logging
from typing import List
from pydantic import BaseModel, Field
from google.genai import types

from src.config import settings
from src.llm.gemini_client import get_gemini_client, LLMError
from src.llm.interfaces import BaseCitationAttributor
from src.models.retrieval_result import RetrievalResult

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a Grounded Citation Attributor for an AI portfolio assistant.
Your task is to identify which of the retrieved document chunks directly support statements made in the generated answer.

Analyze the generated answer carefully and check each retrieved chunk's content preview:
1. ONLY select a chunk if its content directly supports, provides evidence for, or is mentioned in the generated answer.
2. Ignore any chunks that were not actually used or do not support the answer (even if they are contextually related).
3. Do NOT perform any answer generation, rewriting, or summarization. Your sole job is to classify which chunk IDs are relevant sources.
4. If multiple chunks support the same statement, include all of them.
5. If none of the chunks support the answer, return an empty list.

Your output must contain only the list of supporting chunk IDs in the requested JSON structure.
"""

class CitationAttributionSchema(BaseModel):
    chunk_ids: List[str] = Field(
        description="A list of chunk IDs that directly support statements made in the generated answer."
    )


class GeminiCitationAttributor(BaseCitationAttributor):
    """
    Citation Attributor implementation using Google Gemini structured JSON outputs.
    """
    def __init__(self, model_name: str = settings.MODEL_ATTRIBUTOR):
        self.model_name = model_name

    def _format_prompt(self, answer: str, results: List[RetrievalResult]) -> str:
        """Formats the generated answer and chunk previews into a single prompt."""
        prompt = f"Generated Answer:\n{answer}\n\n"
        prompt += "Retrieved Chunks to analyze:\n"
        for res in results:
            chunk_id = res.chunk.chunk_id or "unknown"
            source = res.chunk.source_file or "unknown"
            project = res.chunk.project or "unknown"
            heading = res.chunk.metadata.get("heading") if res.chunk.metadata else None
            content = res.chunk.content or ""
            
            # Short preview/snippet to minimize latency and token usage
            preview = content[:200]
            if len(content) > 200:
                preview += "..."
                
            prompt += f"--- Chunk ID: {chunk_id} ---\n"
            prompt += f"Source File: {source}\n"
            prompt += f"Project: {project}\n"
            if heading:
                prompt += f"Heading: {heading}\n"
            prompt += f"Content Preview: {preview}\n\n"
        return prompt

    async def attribute_citations(
        self,
        answer: str,
        results: List[RetrievalResult]
    ) -> List[str]:
        """
        Determines which retrieved chunks support the answer in a structured JSON call.
        """
        if not results or not answer.strip():
            return []

        import asyncio
        client = get_gemini_client()
        prompt_content = self._format_prompt(answer, results)

        max_retries = 3
        backoff = 1.0  # seconds

        for attempt in range(max_retries):
            try:
                response = await client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt_content,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.0,
                        response_mime_type="application/json",
                        response_schema=CitationAttributionSchema,
                    )
                )

                result: CitationAttributionSchema = response.parsed
                if result is None or not hasattr(result, "chunk_ids"):
                    raise LLMError("Gemini structured output parsing failed.")

                return result.chunk_ids

            except Exception as e:
                err_str = str(e)
                is_transient = any(code in err_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"])
                if is_transient and attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        f"Gemini Attributor API transient issue (attempt {attempt+1}/{max_retries}). "
                        f"Retrying in {sleep_time:.2f}s... Error: {e}"
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"Gemini citation attribution failed after {attempt+1} attempts: {e}")
                    raise LLMError(f"Gemini citation attribution failed: {e}") from e
