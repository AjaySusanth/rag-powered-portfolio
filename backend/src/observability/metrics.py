"""
WHY THIS WAS CHOSEN:
This module defines the Prometheus metrics for the RAG-Powered Developer Portfolio backend.
Exposing metrics via prometheus-client allows external systems like Prometheus and Grafana
to scrape performance, error rates, and query metrics with near-zero runtime overhead.
Metrics are defined globally and updated directly from the orchestration and router layers
independently of trace objects to ensure high decoupling and avoid dependency pollution.

CONCEPTS INLINE EXPLANATION:
- Counter: A cumulative metric that only increases or resets on restart. Used for request counts and errors.
- Gauge: A metric that can go up and down. Used here to track concurrent active requests (rag_requests_in_progress).
- Histogram: Measures the statistical distribution of values (e.g., latency, candidate counts) in configurable buckets.
- Low-Cardinality Labels: We restrict labels to values like 'cache_status' (hit/miss) or 'retrieval_scope' (global/project)
  to prevent unbounded memory consumption (high cardinality) in the Prometheus registry.
"""

from prometheus_client import Counter, Gauge, Histogram

# Latency Buckets (in seconds) tailored for different RAG stages
E2E_LATENCY_BUCKETS = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 30.0]
RETRIEVAL_LATENCY_BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
GENERATION_LATENCY_BUCKETS = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0]
CANDIDATE_BUCKETS = [0.0, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0, 30.0, 50.0]

# --- METRIC DEFINITIONS ---

# 1. Active Requests Gauge
rag_requests_in_progress = Gauge(
    "rag_requests_in_progress", "Number of RAG queries currently being processed."
)

# 2. Total Queries Counter
rag_queries_total = Counter(
    "rag_queries_total",
    "Total number of RAG queries processed.",
    labelnames=["cache_status", "retrieval_scope", "status"],
)

# 3. Cache Hits/Misses Counters
rag_cache_hits_total = Counter("rag_cache_hits_total", "Total number of cache hits in Redis.")

rag_cache_misses_total = Counter("rag_cache_misses_total", "Total number of cache misses in Redis.")

# 4. Latency Histograms
rag_query_duration_seconds = Histogram(
    "rag_query_duration_seconds",
    "End-to-end RAG query execution duration in seconds.",
    labelnames=["cache_status"],
    buckets=E2E_LATENCY_BUCKETS,
)

rag_retrieval_duration_seconds = Histogram(
    "rag_retrieval_duration_seconds",
    "RAG retrieval pipeline latency in seconds.",
    labelnames=["retrieval_scope"],
    buckets=RETRIEVAL_LATENCY_BUCKETS,
)

rag_generation_duration_seconds = Histogram(
    "rag_generation_duration_seconds",
    "LLM generation stage latency in seconds.",
    labelnames=["retrieval_scope"],
    buckets=GENERATION_LATENCY_BUCKETS,
)

# 5. Candidates Histogram
rag_retrieval_candidates = Histogram(
    "rag_retrieval_candidates",
    "Number of candidate chunks retrieved before filtering and grading.",
    labelnames=["retrieval_scope"],
    buckets=CANDIDATE_BUCKETS,
)

# 6. Errors Counter
rag_errors_total = Counter(
    "rag_errors_total",
    "Total number of errors encountered during RAG query orchestration, categorized by stage.",
    labelnames=["stage"],
)
