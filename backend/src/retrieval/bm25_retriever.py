"""
DESIGN DECISION:
This module implements BM25 keyword-based retrieval.
We choose an in-process, in-memory BM25 index using the `rank-bm25` library to comply with the
PRD requirement of low-latency retrieval with no network hop.

To support code-heavy Layer 3 documents (e.g. YAML, source files), standard whitespace tokenization is insufficient.
We implement a custom regex-based tokenizer that splits camelCase identifiers and punctuation (like '.' or '_'),
ensuring query matches succeed against components of longer technical identifiers.

State is encapsulated in a singleton `BM25Index` class to keep the module-level globals clean,
providing a thread-safe-like wrapper to initialize, refresh, and query the index.
"""

import logging
import re
from typing import List, Optional

from rank_bm25 import BM25Okapi

from src.models.chunk import Chunk
from src.models.retrieval_result import RetrievalResult
from src.vectorstore.pgvector_store import get_all_chunks

logger = logging.getLogger(__name__)


def tokenize_code(text: str) -> List[str]:
    """
    Tokenizes a string, optimized for code and technical documents.

    BM25 Tokenization Concept:
    Unlike natural language tokenization which only splits on whitespace, code tokenization must break down
    complex identifiers. For example, 'authMiddleware' or 'app.kubernetes.io/name' contain multiple terms
    that a user might search for individually.

    This function:
    1. Splits camelCase patterns (e.g., 'authMiddleware' -> 'auth Middleware') using regex.
    2. Replaces all non-alphanumeric characters with spaces to split on punctuation ('.', '/', '-', '_', etc.).
    3. Converts to lowercase, strips whitespace, and removes empty tokens while preserving numbers.
    """
    if not text:
        return []

    # 1. Insert space before capitals to split camelCase/PascalCase
    # e.g., 'authMiddleware' -> 'auth Middleware', 'HTTPResponse' -> 'HTTP Response'
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s1)

    # Insert space between letters and numbers
    # e.g., 'Token123' -> 'Token 123', '123Token' -> '123 Token'
    s3 = re.sub(r"([a-zA-Z])([0-9])", r"\1 \2", s2)
    s4 = re.sub(r"([0-9])([a-zA-Z])", r"\1 \2", s3)

    # 2. Split on punctuation by replacing any non-alphanumeric character with a space
    s5 = re.sub(r"[^a-zA-Z0-9\s]", " ", s4)

    # 3. Lowercase and split on whitespace to get clean tokens
    tokens = [t.lower() for t in s5.split() if t]
    return tokens


class BM25Index:
    """
    In-memory representation of the BM25 index.

    Concept:
    BM25 (Best Matching 25) is a ranking function used by search engines to estimate the relevance
    of documents to a given search query. It is based on term frequency (TF) and inverse document frequency (IDF).
    This class maintains the corpus, tokenized representation, metadata mappings, and the raw BM25Okapi object.
    """

    def __init__(self) -> None:
        self.corpus: List[Chunk] = []
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self._is_initialized = False

    async def refresh_index(self) -> None:
        """
        Rebuilds the BM25 index completely from the PostgreSQL database.
        Can be invoked directly after manual or automated ingestion.
        """
        try:
            logger.info("Refreshing BM25 in-memory index from database...")
            db_chunks = await get_all_chunks()

            # Map database dictionaries back to Chunk objects
            chunks = []
            for row in db_chunks:
                chunks.append(
                    Chunk(
                        chunk_id=row.get("chunk_id", ""),
                        parent_document_id=row.get("parent_document_id", ""),
                        content_hash=row.get("content_hash", ""),
                        content=row.get("content", ""),
                        project=row.get("project", "unknown"),
                        layer=row.get("layer", "unknown"),
                        source_type=row.get("source_type", "unknown"),
                        source_file=row.get("source_file", "unknown"),
                        chunk_index=row.get("chunk_index", 0),
                        token_count=row.get("token_count", 0),
                        char_count=row.get("char_count", 0),
                        metadata=row.get("metadata", {}),
                    )
                )

            if not chunks:
                logger.warning(
                    "No chunks found in database. Initializing BM25 index with empty corpus."
                )
                self.corpus = []
                self.tokenized_corpus = []
                self.bm25 = None
                self._is_initialized = True
                return

            tokenized_corpus = [tokenize_code(chunk.content) for chunk in chunks]

            self.corpus = chunks
            self.tokenized_corpus = tokenized_corpus
            self.bm25 = BM25Okapi(tokenized_corpus)
            self._is_initialized = True
            logger.info(f"BM25 index successfully refreshed with {len(chunks)} chunks.")

        except Exception as e:
            logger.error(f"Failed to refresh BM25 index: {e}")
            raise

    def search(
        self, query: str, top_k: int = 5, project: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Queries the BM25 index, scores all chunks, filters by project, and returns ranked results.
        """
        if not self._is_initialized or not self.bm25:
            # If the index is uninitialized (e.g. on first query), we log a warning.
            # But the caller should ensure refresh_index has been called.
            logger.warning("BM25 index is not initialized or is empty. Returning empty results.")
            return []

        if not query or not query.strip():
            return []

        # 1. Tokenize query using the same tokenizer
        query_tokens = tokenize_code(query)
        if not query_tokens:
            return []

        # 2. Compute BM25 scores for the entire corpus
        scores = self.bm25.get_scores(query_tokens)

        # 3. Map to RetrievalResult objects
        results = []
        for chunk, score in zip(self.corpus, scores):
            # 4. Post-filter by project (preserving __global__ limitation where if project is filtered,
            # we only keep items matching that project, potentially ignoring global resume/faq items).
            if project is not None and chunk.project != project:
                continue

            # BM25 scores can be 0 or slightly negative; we only include positive score matches
            # to remain high signal, or keep everything matching project with positive scores.
            if score > 0.0:
                results.append(RetrievalResult(chunk=chunk, score=float(score)))

        # 5. Sort by score descending and return top_k
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]


# Singleton index instance
index_instance = BM25Index()


async def retrieve(
    query: str, top_k: int = 5, project: Optional[str] = None
) -> List[RetrievalResult]:
    """
    Retrieves chunks matching the natural language query using the BM25 index.

    Why:
    Acts as the public interface for the BM25 retriever path, matching the signature
    of the vector retriever.
    """
    # Lazy-init the index if it hasn't been initialized yet.
    if not index_instance._is_initialized:
        await index_instance.refresh_index()

    return index_instance.search(query=query, top_k=top_k, project=project)
