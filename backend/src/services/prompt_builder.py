"""
WHY THIS WAS CHOSEN:
This class separates prompt engineering and formatting from both retrieval and LLM providers.
It manages system instructions, context assembly, maximum chunk constraints, and formatting layout,
meaning prompts can be modified or versioned without touching the orchestrator or provider client.

We added the PromptBuildResult model as the single source of truth for the context sent to the LLM.
By returning both the formatted prompt and the chunks_used list, we prevent duplicating the sorting/slicing
logic in the orchestrator, ensuring that citations perfectly match only the documents actually read by the LLM.
"""

from typing import List

from pydantic import BaseModel

from src.models.retrieval_result import RetrievalResult


class PromptBuildResult(BaseModel):
    """Container holding the constructed prompt and the actual chunks used to build it."""

    prompt: str
    chunks_used: List[RetrievalResult]


class PromptBuilder:
    """
    Constructs the final grounded context prompt and holds the system guidelines.
    """

    SYSTEM_INSTRUCTION = (
        "You are the AI assistant for Ajay's Professional Portfolio.\n"
        "Your goal is to answer questions about Ajay's skills, experience, education, projects, and background using ONLY the provided context chunks.\n\n"
        "STRICT GROUNDING RULES:\n"
        "1. You must answer the user's question using ONLY the provided context chunks. Do NOT make up facts, speculate, or draw on any outside or pre-trained knowledge about Ajay. Maintain strict grounding and do not hallucinate.\n"
        "2. Synthesize information across multiple context chunks to provide a complete and integrated response.\n"
        "3. If only partial information is available in the context chunks, provide the best possible grounded answer using that partial information, stating clearly what is known.\n"
        "4. If NONE of the provided context chunks are relevant or contain information to answer the user's query, state clearly that you do not have that information.\n"
        "5. Be professional, direct, and concise. Format your response cleanly using Markdown."
    )

    @classmethod
    def build(
        cls, original_query: str, chunks: List[RetrievalResult], max_chunks: int = 15
    ) -> PromptBuildResult:
        """
        Assembles and formats the final prompt text.

        Args:
            original_query: The original user question.
            chunks: The filtered RetrievalResults to assemble as context.
            max_chunks: Upper limit of chunks to include in the context.

        Returns:
            A PromptBuildResult containing the structured string prompt and the list of chunks used.
        """
        # Ensure ordering: highest score (relevance) first
        sorted_results = sorted(chunks, key=lambda r: r.score, reverse=True)[:max_chunks]

        context_str = ""
        for i, res in enumerate(sorted_results):
            source_file = res.chunk.source_file or "unknown"
            project = res.chunk.project or "global"
            heading = res.chunk.metadata.get("heading") or "No Heading"
            content = res.chunk.content or ""
            context_str += f"--- CONTEXT CHUNK {i + 1} (Project: {project} | Source: {source_file} > {heading}) ---\n{content}\n\n"

        prompt = f"User Question: {original_query}\n\nRetrieved Context:\n{context_str}"
        return PromptBuildResult(prompt=prompt, chunks_used=sorted_results)
