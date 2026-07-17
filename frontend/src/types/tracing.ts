export interface ChunkTrace {
  chunk_id: string;
  content_preview: string;
  source_file: string;
  layer: string;
  project: string;
  score: number;
  rank?: number;
  reason?: string;
}

export interface RetrievalStageTrace {
  results: ChunkTrace[];
  latency_ms: number;
  candidate_count: number;
  score_range?: [number, number] | null;
  duplicates_removed?: number | null;
  rejected_results?: ChunkTrace[] | null;
}

export interface TraceRequest {
  original_query: string;
  detected_project?: string | null;
  rewritten_query?: string | null;
  rewrite_applied?: boolean;
  rewrite_reason?: string | null;
  project_scope?: string | null;
}

export interface TraceRetrieval {
  vector_stage?: RetrievalStageTrace | null;
  bm25_stage?: RetrievalStageTrace | null;
  rrf_stage?: RetrievalStageTrace | null;
  diversified_stage?: RetrievalStageTrace | null;
  graded_stage?: RetrievalStageTrace | null;
  final_context?: string | null;
}

export interface TraceGeneration {
  response_preview?: string | null;
  latency_ms: number;
  token_count?: number | null;
}

export interface TraceTimings {
  query_processing_ms: number;
  total_retrieval_ms: number;
  generation_ms: number;
  total_request_ms: number;
  stages: Record<string, number>;
}

export interface TraceMetadata {
  timestamp: number;
  cache_hit: boolean;
  model_name?: string | null;
}

export interface PipelineTrace {
  request: TraceRequest;
  retrieval: TraceRetrieval;
  generation: TraceGeneration;
  timings: TraceTimings;
  metadata: TraceMetadata;
}
