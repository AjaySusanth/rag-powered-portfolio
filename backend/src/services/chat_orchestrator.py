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
from src.cache.factory import create_cache_from_settings
from src.retrieval.project_detector import detect_project
from src.retrieval.rewriters.factory import create_rewriter_from_settings
from src.retrieval.hybrid_retriever import retrieve
from src.services.prompt_builder import PromptBuilder, PromptBuildResult
from src.services.prompt_guard import PromptGuard
from src.llm.factory import create_generator_from_settings, create_attributor_from_settings
from src.llm.gemini_client import LLMError

logger = logging.getLogger(__name__)


class ChatOrchestrator:
    """
    Orchestrates the lifecycle of a single user chat message.
    """
    
    def __init__(self):
        self.cache = create_cache_from_settings()

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

        # 0.5 Cache Lookup
        cached_response = await self.cache.get_chat_response(query)
        if cached_response:
            logger.info("Cache hit for query.")
            yield StreamTokenEvent(token=cached_response["answer"])
            citations = [Citation(**c) for c in cached_response.get("citations", [])]
            yield StreamCitationsEvent(citations=citations)
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
                top_k=15,
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
        full_answer = ""
        try:
            generator = create_generator_from_settings()
            async for token in generator.stream(build_result.prompt, system_instruction=PromptBuilder.SYSTEM_INSTRUCTION):
                full_answer += token
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
        citations = []
        try:
            # Post-generation citation attribution
            try:
                attributor = create_attributor_from_settings()
                logger.info("Executing post-generation citation attribution...")
                supporting_ids = await attributor.attribute_citations(full_answer, build_result.chunks_used)
                
                # 1. Deduplicate supporting_ids returned by the LLM
                seen_supporting = set()
                deduped_supporting = []
                for cid in supporting_ids:
                    if cid not in seen_supporting:
                        seen_supporting.add(cid)
                        deduped_supporting.append(cid)
                
                # 2. Filter and map back to RetrievalResult, ignoring unknown IDs safely
                valid_chunks_map = {res.chunk.chunk_id: res for res in build_result.chunks_used if res.chunk.chunk_id}
                
                attributed_chunks = []
                for cid in deduped_supporting:
                    if cid in valid_chunks_map:
                        attributed_chunks.append(valid_chunks_map[cid])
                    else:
                        logger.warning(f"Attributor returned unknown chunk ID: {cid}. Safely ignoring.")
                
                # 3. Apply fallback if no valid grounding chunks are returned (unless explicitly 0)
                if attributed_chunks:
                    logger.info(f"Attribution complete. Filtered citations from {len(build_result.chunks_used)} -> {len(attributed_chunks)}.")
                    chunks_for_citations = attributed_chunks
                else:
                    if len(supporting_ids) == 0:
                        logger.info("Attributor explicitly returned 0 citations.")
                        chunks_for_citations = []
                    else:
                        logger.warning("Attributor returned no valid grounding chunks. Falling back to all retrieved chunks.")
                        chunks_for_citations = build_result.chunks_used
            except Exception as attr_err:
                logger.error(f"Citation attribution failed: {attr_err}. Falling back to all retrieved chunks.")
                chunks_for_citations = build_result.chunks_used

            seen_files = set()
            for res in chunks_for_citations:
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
            yield StreamCitationsEvent(citations=[])
            
        # 7. Cache the successful response
        if full_answer.strip():
            await self.cache.set_chat_response(query, full_answer, citations)
