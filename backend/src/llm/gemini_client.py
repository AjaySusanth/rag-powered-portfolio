"""
DESIGN DECISION:
This module manages interactions with the Gemini 2.0 Flash model via Google AI Studio.
It implements strict grounding guidelines (PRD Section 4.5 & Challenge 1) to prevent
hallucination by leveraging system instructions that restrict the model to provided context only.

Why Gemini 2.0 Flash:
  Per the PRD, Gemini 2.0 Flash is our primary LLM for generating answers. It is fast,
  highly capable, and cost-efficient via Google AI Studio free tier.

Why Temperature 0.0:
  To minimize hallucination and ensure deterministic, grounded answers, we run the model
  with a temperature of 0.0.
"""

import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from src.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Raised when an LLM API call fails."""
    pass


# ---------------------------------------------------------------------------
# System Prompt & Client Initialization
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the AI assistant for Ajay's Professional Portfolio.
Your goal is to answer questions about Ajay's skills, experience, education, projects, and background using ONLY the provided context chunks.

STRICT GROUNDING RULES:
1. You must answer the user's question using ONLY the provided context chunks. Do NOT make up facts, speculate, or draw on any outside or pre-trained knowledge about Ajay.
2. If the context chunks do not contain the answer, or do not have enough specific details to answer the user's query, you MUST begin your response with this exact phrase:
   "I don't have specific details on that. Here's what I do know: ..."
   Following this phrase, summarize any context that is remotely relevant, or list the areas of Ajay's background that are present in the context.
3. Be professional, direct, and concise. Format your response cleanly using Markdown.
"""

_client: Optional[genai.Client] = None


def get_gemini_client() -> genai.Client:
    """
    Returns the Google GenAI Client instance.
    
    Why: Lazy initialization ensures config keys are loaded from settings at call time
    and allows for easier mocking during unit testing.
    """
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise LLMError("GEMINI_API_KEY environment variable is not set.")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


# ---------------------------------------------------------------------------
# Core Generation Function
# ---------------------------------------------------------------------------

def format_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """Formats context chunks and query into a structured text prompt."""
    context_str = ""
    for i, chunk in enumerate(context_chunks):
        source_file = chunk.get("source_file", "unknown")
        heading = chunk.get("heading") or "No Heading"
        content = chunk.get("content", "")
        context_str += f"--- CONTEXT CHUNK {i+1} (Source: {source_file} > {heading}) ---\n{content}\n\n"
        
    prompt = f"User Question: {query}\n\nRetrieved Context:\n{context_str}"
    return prompt


async def generate_answer(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Asynchronously sends the query and context chunks to Gemini 2.0 Flash to generate an answer.
    
    Why: The `.aio` context manager ensures clean async connection pooling and resource cleanup.
    """
    client = get_gemini_client()
    contents = format_prompt(query, context_chunks)
    
    try:
        async with client.aio as aclient:
            response = await aclient.models.generate_content(
                model=settings.GEMINI_MODEL_NAME,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0,
                )
            )
            
            # The returned text response
            return response.text or ""
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        raise LLMError(f"Gemini API call failed: {e}") from e
