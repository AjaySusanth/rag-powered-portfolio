"""
WHY THIS WAS CHOSEN:
We use a Pydantic BaseModel for RewriteResult because Google Gemini's structured output API
requires a Pydantic schema to enforce the JSON structure of responses at the API boundary.
Defining this in the models package keeps our data schemas separated from retrieval execution logic.
"""

from pydantic import BaseModel, Field


class RewriteResult(BaseModel):
    """
    Encapsulates the structured output of the query rewriter.
    """

    rewritten_query: str = Field(
        description="The expanded, search-optimized query. If no rewrite was needed, this contains the original query."
    )
    rewritten: bool = Field(
        description="True if the query was modified to improve retrieval quality, False if the query was kept as-is."
    )
    explanation: str = Field(
        description="A concise reason explaining why the query was or was not rewritten."
    )
