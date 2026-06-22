"""
DESIGN DECISION: 
This module implements the document chunking pipeline for the RAG database.
By tokenizing raw text using the 'cl100k_base' schema via tiktoken, we align
our chunk boundaries precisely with the token parsing behavior of the 
'text-embedding-3-small' embedding model. This prevents token overflow and
underflow. The sliding window algorithm with document-layer-specific configurations 
(Layer 1, 2, and 3) ensures that:
1. Short identity facts remain granular (256 tokens).
2. Deep design concepts are kept cohesive (512 tokens).
3. Comment stripping occurs beforehand to preserve token budgets and avoid embedding pollution.
"""

import re
from enum import IntEnum
from typing import List
import tiktoken
from pydantic import BaseModel, Field


class DocumentLayer(IntEnum):
    """
    Specifies the document knowledge layer per Section 3.1 of the PRD.
    
    Layer 1: Identity documents (resume, faq, about-me)
    Layer 2: Manual project design docs (architecture, decisions, challenges)
    Layer 3: Auto-ingested source code artifacts
    """
    IDENTITY = 1
    DESIGN = 2
    ARTIFACT = 3


class LayerConfig(BaseModel):
    """
    Configuration parameters for a specific document layer's chunking behavior.
    """
    chunk_size: int = Field(description="Max tokens allowed per chunk")
    overlap: int = Field(description="Token overlap between consecutive chunks")


# Global mapping of layer properties as defined in Section 3.1 & 4.2 of the PRD.
LAYER_CONFIGS = {
    DocumentLayer.IDENTITY: LayerConfig(chunk_size=256, overlap=32),
    DocumentLayer.DESIGN: LayerConfig(chunk_size=512, overlap=64),
    DocumentLayer.ARTIFACT: LayerConfig(chunk_size=256, overlap=32),
}


class DocumentChunk(BaseModel):
    """
    Pydantic schema representing a single structured chunk of a document.
    """
    content: str = Field(description="The decoded string content of the chunk")
    token_count: int = Field(description="The number of tokens within this chunk")
    chunk_index: int = Field(description="The zero-indexed positional index of this chunk")


def strip_html_comments(text: str) -> str:
    """
    Removes HTML and Markdown comment blocks (<!-- ... -->) from a raw string.
    
    Why: Internal RAG design comments and notes are useful to human editors,
    but they waste token quota and pollute vector space if ingested into the DB.
    """
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def chunk_text(text: str, layer: DocumentLayer) -> List[DocumentChunk]:
    """
    Converts a document string into a list of overlapping token chunks.
    
    This function:
    1. Preprocesses the text by removing comments.
    2. Uses tiktoken to encode the raw string into LLM tokens.
    3. Loops through the tokens using a sliding window.
    4. Decodes each window back into a UTF-8 string chunk.
    """
    # 1. Preprocess & strip metadata comments
    clean_text = strip_html_comments(text)
    
    # If the document is empty after cleaning, return no chunks
    if not clean_text.strip():
        return []

    # 2. Get encoding and tokenize
    # Concept: tiktoken translates words/characters into integers (tokens) that
    # the LLM's neural network actually processes. The 'cl100k_base' vocabulary
    # is the standard format used by text-embedding-3-small.
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(clean_text)
    
    config = LAYER_CONFIGS[layer]
    chunk_size = config.chunk_size
    overlap = config.overlap
    
    chunks: List[DocumentChunk] = []
    token_length = len(tokens)
    
    # 3. Sliding Window
    # Concept: Overlap (e.g. 32 or 64 tokens) is included at the start of the next 
    # chunk so that context is not abruptly severed at arbitrary boundaries. 
    # This prevents the LLM from losing connection between concepts split across chunks.
    i = 0
    chunk_index = 0
    
    while i < token_length:
        # Extract subset of tokens for the current chunk
        chunk_tokens = tokens[i : i + chunk_size]
        
        # Decode back into human-readable text
        chunk_content = encoding.decode(chunk_tokens)
        
        chunks.append(DocumentChunk(
            content=chunk_content,
            token_count=len(chunk_tokens),
            chunk_index=chunk_index
        ))
        
        # Stop if this window reached or exceeded the end of the token list
        if i + chunk_size >= token_length:
            break
            
        # Move window forward by chunk_size minus the overlap
        step = max(1, chunk_size - overlap)
        i += step
        chunk_index += 1
        
    return chunks
