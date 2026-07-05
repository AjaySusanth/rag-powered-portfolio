"""
WHY THIS WAS CHOSEN:
This module implements the Gemini-based Query Rewriter. It uses the Gemini API's
structured schema validation to ensure the LLM returns a structured JSON matching
RewriteResult. It includes robust transient error handling with exponential backoff,
mirroring the behavior of the Retrieval Grader.
"""

import asyncio
import logging
from typing import Optional

from google.genai import types

from src.config import settings
from src.llm.gemini_client import LLMError, get_gemini_client
from src.models.rewrite_result import RewriteResult
from src.retrieval.rewriters.base import BaseQueryRewriter

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """You are a retrieval-optimization assistant for a Developer Portfolio RAG (Retrieval-Augmented Generation) system.
Your job is to rewrite the user's query into an optimized search query to retrieve the most relevant technical documents and code chunks.

Follow these strict guidelines:
1. NEVER attempt to answer the user's question. You are a pre-processing step. You do not generate answers.
2. Only rewrite the query if it is ambiguous, conversational, or underspecified such that expanding it will improve Vector/BM25 retrieval quality.
3. If the query is already specific, precise, and search-optimized (e.g. contains exact terms, specific file paths, or specific configuration options), return the original query UNCHANGED (set "rewritten" to false, and "rewritten_query" to the original query).
4. Preserve all key technical terms, project names, file names, API endpoints, code identifiers, database columns, and Kubernetes resource names (like SecretProviderClass, Ingress, Pod, Helm, etc.).
5. Expand abbreviations or acronyms only when they are highly relevant and helpful to retrieval.
6. Provide a clear, concise explanation of your decision in the "explanation" field.

You will be given the user's raw query and an optional project context detected for that query. If a project is specified, ensure terms relevant to that project are prioritized/expanded.

Format the output strictly as a JSON object matching the requested schema.
"""

class GeminiQueryRewriter(BaseQueryRewriter):
    """
    Query Rewriter implementation using Google Gemini structured JSON outputs.
    """
    def __init__(self, model_name: str = settings.MODEL_REWRITER):
        self.model_name = model_name

    def _format_prompt(self, query: str, project: Optional[str] = None) -> str:
        """Formats the query and project context into a single prompt."""
        prompt = f"User Query: {query}\n"
        if project:
            prompt += f"Detected Project Context: {project}\n"
        else:
            prompt += "Detected Project Context: None\n"
        return prompt

    async def rewrite(self, query: str, project: Optional[str] = None) -> RewriteResult:
        """
        Rewrites the query using Gemini structured JSON outputs.
        Includes exponential backoff for transient HTTP errors.
        """
        if not query or not query.strip():
            return RewriteResult(
                rewritten_query="",
                rewritten=False,
                explanation="Empty query provided."
            )

        client = get_gemini_client()
        prompt_content = self._format_prompt(query, project)

        max_retries = 5
        backoff = 2.0  # seconds

        for attempt in range(max_retries):
            try:
                response = await client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt_content,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.0,
                        response_mime_type="application/json",
                        response_schema=RewriteResult,
                    )
                )

                result: RewriteResult = response.parsed
                if result is None or not hasattr(result, "rewritten_query"):
                    logger.warning("Gemini did not return a valid RewriteResult, attempting fallback parsing.")
                    raise LLMError("Gemini structured output parsing failed.")

                logger.info(
                    f"Query rewrite result: rewritten={result.rewritten}, "
                    f"original='{query}', rewritten='{result.rewritten_query}'"
                )
                return result

            except Exception as e:
                err_str = str(e)
                # Check for rate limit (429) or temporary server unavailability (503)
                is_transient = any(code in err_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"])
                if is_transient and attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    logger.warning(
                        f"Gemini Query Rewriter transient issue (attempt {attempt+1}/{max_retries}). "
                        f"Retrying in {sleep_time:.2f}s... Error: {e}"
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"Gemini query rewrite failed after {attempt+1} attempts: {e}")
                    # Fallback to the original query if LLM rewriting fails completely
                    return RewriteResult(
                        rewritten_query=query,
                        rewritten=False,
                        explanation=f"Query rewriter failed after multiple retries. Error: {e}"
                    )
