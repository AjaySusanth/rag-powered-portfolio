"""
WHY THIS WAS CHOSEN:
The ChatOrchestrator acts as the application-layer orchestrator. It manages the sequential
execution of RAG stages (project detection, query rewriting, hybrid search, context assembly, LLM streaming)
without dependencies on web frameworks (like FastAPI) or transport details (like SSE).
This keeps the core business logic testable in isolation.

We added structured citations processing here to extract source details directly from the PromptBuildResult's
chunks_used. Citations are deduplicated by source file and yielded only after successful completion of the LLM stream.
This ensures a clear, sequential streaming protocol flow (tokens -> citations -> [DONE]).
"""

import logging
from typing import AsyncIterator, Optional

from src.config import settings
from src.api.schemas.chat import StreamTokenEvent, BaseStreamEvent, StreamErrorEvent, Citation, StreamCitationsEvent
from src.retrieval.project_detector import detect_project
from src.retrieval.rewriters.factory import create_rewriter_from_settings
from src.retrieval.hybrid_retriever import retrieve
from src.services.prompt_builder import PromptBuilder, PromptBuildResult
from src.services.prompt_guard import PromptGuard
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

        # 0. Prompt Injection Detection
        guard_result = PromptGuard.analyze(query)

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
            build_result = PromptBuilder.build(original_query=query, chunks=chunks)
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
            async for token in generator.stream(build_result.prompt, system_instruction=PromptBuilder.SYSTEM_INSTRUCTION):
                yield StreamTokenEvent(token=token)
        except LLMError as e:
            logger.error(f"LLM streaming error: {e}")
            yield StreamErrorEvent(code="llm_error", message="The model failed to stream a response.")
            return
        except Exception as e:
            logger.error(f"Unexpected generator error: {e}")
            yield StreamErrorEvent(code="unexpected_error", message="An unexpected error occurred during generation.")
            return

        # 6. Yield Citations (only on successful completion of token streaming)
        try:
            citations = []
            seen_files = set()
            for res in build_result.chunks_used:
                source_file = res.chunk.source_file or "unknown"
                project = res.chunk.project or "global"
                dedup_key = (project, source_file)
                if dedup_key not in seen_files:
                    seen_files.add(dedup_key)
                    citations.append(
                        Citation(
                            file=source_file,
                            layer=res.chunk.layer or "unknown",
                            project=project
                        )
                    )
            yield StreamCitationsEvent(citations=citations)
            logger.info(f"Successfully emitted {len(citations)} citations.")
        except Exception as e:
            logger.error(f"Error compiling citations: {e}")
            # If compiling citations fails after successful LLM streaming, we should probably log it,
            # but not completely crash the stream since the answer has already been successfully streamed.
            # However, for completeness we can yield an empty citations event.
            yield StreamCitationsEvent(citations=[])
