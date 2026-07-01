"""
WHY THIS WAS CHOSEN:
The ChatOrchestrator acts as the application-layer orchestrator. It manages the sequential
execution of RAG stages (project detection, query rewriting, hybrid search, context assembly, LLM streaming)
without dependencies on web frameworks (like FastAPI) or transport details (like SSE).
This keeps the core business logic testable in isolation.
"""

import logging
from typing import AsyncIterator, Optional

from src.config import settings
from src.api.schemas.chat import StreamTokenEvent, BaseStreamEvent, StreamErrorEvent
from src.retrieval.project_detector import detect_project
from src.retrieval.rewriters.factory import create_rewriter_from_settings
from src.retrieval.hybrid_retriever import retrieve
from src.services.prompt_builder import PromptBuilder
from src.llm.factory import create_generator_from_settings
from src.llm.gemini_client import LLMError

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """
    Orchestrates the lifecycle of a single user chat message.
    """

    async def stream_chat(
        self,
        query: str,
        session_id: Optional[str] = None
    ) -> AsyncIterator[BaseStreamEvent]:
        """
        Processes a user query and yields a stream of typed events.
        
        Args:
            query: The user's original query.
            session_id: Optional tracking identifier.
            
        Yields:
            Subclasses of BaseStreamEvent (e.g. StreamTokenEvent or StreamErrorEvent).
        """
        # Session ID is passed through and can be used for future logging
        logger.info(f"Initiating chat request. session_id={session_id}")

        if not query or not query.strip():
            yield StreamErrorEvent(code="invalid_query", message="Query string cannot be empty.")
            return

        # 1. Project Detection
        try:
            project = detect_project(query)
            logger.info(f"Project detection completed. Detected project: {project}")
        except Exception as e:
            logger.error(f"Project detection failed: {e}. Falling back to global search.")
            project = None

        # 2. Query Rewriter (optional)
        search_query = query
        if settings.ENABLE_QUERY_REWRITER:
            try:
                rewriter = create_rewriter_from_settings()
                rewrite_result = await rewriter.rewrite(query, project)
                if rewrite_result.rewritten:
                    search_query = rewrite_result.rewritten_query
                    logger.info(f"Query rewritten: '{query}' -> '{search_query}'")
            except Exception as e:
                logger.error(f"Query rewriter failed: {e}. Falling back to original query.")
                search_query = query

        # 3. Hybrid Retrieval & Grader
        # Note: retrieve() handles vector search, BM25, RRF, Diversification, and Grader filtering.
        try:
            logger.info(f"Executing hybrid retrieval for: '{search_query}'")
            chunks = await retrieve(
                query=search_query,
                project=project,
                diversify=True,
                grade=True
            )
            logger.info(f"Retrieval complete. Retrieved {len(chunks)} relevant chunks.")
        except Exception as e:
            logger.error(f"Retrieval pipeline failed: {e}")
            yield StreamErrorEvent(
                code="retrieval_failed",
                message="Retrieval pipeline encountered an unexpected error."
            )
            return

        # 4. Prompt Construction (always with original query)
        try:
            prompt = PromptBuilder.build(original_query=query, chunks=chunks)
        except Exception as e:
            logger.error(f"Prompt construction failed: {e}")
            yield StreamErrorEvent(
                code="prompt_construction_failed",
                message="Context assembly failed."
            )
            return

        # 5. LLM Streaming
        try:
            generator = create_generator_from_settings()
            async for token in generator.stream(prompt, system_instruction=PromptBuilder.SYSTEM_INSTRUCTION):
                yield StreamTokenEvent(token=token)
        except LLMError as e:
            logger.error(f"LLM streaming error: {e}")
            yield StreamErrorEvent(code="llm_error", message="The model failed to stream a response.")
        except Exception as e:
            logger.error(f"Unexpected generator error: {e}")
            yield StreamErrorEvent(code="unexpected_error", message="An unexpected error occurred during generation.")
