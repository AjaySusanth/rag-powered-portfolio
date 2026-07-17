"use client";

/**
 * WHY THIS DESIGN WAS CHOSEN:
 * The TraceDashboard page serves as the user interface for administrative debugging of RAG queries.
 * By rendering aggregate timings in a clean dashboard layout and utilizing custom suggestion tags,
 * it provides a seamless interaction flow. It maps the returned PipelineTrace object to individual
 * PipelineStageCard components chronologically, illustrating the journey of a user query from raw
 * input, through retrieval algorithms, and into structured generation context.
 */

import { useState, useEffect } from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { fetchRetrievalTrace, verifyAdminKey } from "@/services/api/admin";
import { PipelineTrace } from "@/types/tracing";
import { PipelineStageCard } from "@/components/admin/PipelineStageCard";
import {
  Compass,
  Cpu,
  Clock,
  Sparkles,
  RefreshCw,
  Search,
  CheckCircle2,
  XCircle,
  Code2,
  Layers,
  LogOut,
} from "lucide-react";

export default function TraceDashboard() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [trace, setTrace] = useState<PipelineTrace | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Authentication states
  const [adminKey, setAdminKey] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingStorage, setIsCheckingStorage] = useState(true);
  const [isVerifyingKey, setIsVerifyingKey] = useState(false);
  const [inputKey, setInputKey] = useState("");
  const [rememberKey, setRememberKey] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const sampleQueries = [
    "Who is Ajay and what is his background?",
    "What technologies are used in TalentForge?",
    "Explain the n8n AKS platform architecture.",
    "Show me Ajay's contact details and FAQ info.",
  ];

  // Load saved key from localStorage on mount
  useEffect(() => {
    const savedKey = localStorage.getItem("admin_api_key");
    if (savedKey) {
      const autoVerify = async () => {
        const isValid = await verifyAdminKey(savedKey);
        if (isValid) {
          setAdminKey(savedKey);
          setIsAuthenticated(true);
        } else {
          // If the key is no longer valid, discard it
          localStorage.removeItem("admin_api_key");
        }
        setIsCheckingStorage(false);
      };
      autoVerify();
    } else {
      setIsCheckingStorage(false);
    }
  }, []);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputKey.trim()) return;

    setIsVerifyingKey(true);
    setAuthError(null);

    const isValid = await verifyAdminKey(inputKey);
    if (isValid) {
      setAdminKey(inputKey);
      setIsAuthenticated(true);
      if (rememberKey) {
        localStorage.setItem("admin_api_key", inputKey);
      } else {
        localStorage.removeItem("admin_api_key");
      }
    } else {
      setAuthError("Authentication failed: Invalid admin access key.");
    }
    setIsVerifyingKey(false);
  };

  const handleRunTrace = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchRetrievalTrace(searchQuery, adminKey);
      setTrace(result);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An unexpected error occurred while fetching trace.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleRunTrace(query);
  };

  if (isCheckingStorage) {
    return (
      <PageContainer className="max-w-md py-32 flex flex-col items-center justify-center space-y-4 font-sans">
        <RefreshCw className="h-8 w-8 text-primary animate-spin" />
        <p className="text-sm text-muted-foreground font-medium">Verifying authorization...</p>
      </PageContainer>
    );
  }

  if (!isAuthenticated) {
    return (
      <PageContainer className="max-w-md py-20 flex flex-col justify-center font-sans">
        <div className="bg-card/25 border border-border/60 rounded-2xl p-8 backdrop-blur-sm space-y-6 shadow-xl relative overflow-hidden">
          {/* Decorative gradient overlay */}
          <div className="absolute -right-20 -top-20 h-40 w-40 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
          <div className="absolute -left-20 -bottom-20 h-40 w-40 rounded-full bg-secondary/10 blur-3xl pointer-events-none" />

          <div className="text-center space-y-2 relative">
            <div className="mx-auto h-12 w-12 rounded-xl bg-primary/15 border border-primary/20 flex items-center justify-center text-primary mb-4 animate-pulse">
              <Compass className="h-6 w-6" />
            </div>
            <h2 className="text-2xl font-extrabold tracking-tight text-foreground">
              Admin Access Required
            </h2>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto">
              Please enter your administrator key to unlock the RAG Pipeline Debugger.
            </p>
          </div>

          <form onSubmit={handleAuthSubmit} className="space-y-4 relative">
            <div className="space-y-2">
              <label htmlFor="admin-key" className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                Admin Access Key
              </label>
              <input
                id="admin-key"
                type="password"
                placeholder="Enter access key..."
                value={inputKey}
                onChange={(e) => {
                  setInputKey(e.target.value);
                  if (authError) setAuthError(null);
                }}
                disabled={isVerifyingKey}
                className="w-full px-4 py-3 bg-background border border-border/80 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/45 disabled:opacity-50 transition-all duration-200 font-mono text-center tracking-widest text-foreground"
                required
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                id="remember-key"
                type="checkbox"
                checked={rememberKey}
                onChange={(e) => setRememberKey(e.target.checked)}
                disabled={isVerifyingKey}
                className="h-4 w-4 rounded border-border text-primary focus:ring-primary/45 cursor-pointer accent-primary"
              />
              <label htmlFor="remember-key" className="text-xs text-muted-foreground cursor-pointer select-none">
                Remember key on this device
              </label>
            </div>

            {authError && (
              <div className="flex items-start gap-2.5 bg-destructive/10 border border-destructive/20 text-destructive-foreground p-3.5 rounded-xl">
                <XCircle className="h-4.5 w-4.5 shrink-0 text-rose-500 mt-0.5" />
                <p className="text-xs text-rose-400 font-medium leading-normal">{authError}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isVerifyingKey || !inputKey.trim()}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-xl text-sm hover:bg-primary/95 focus:ring-2 focus:ring-primary/45 disabled:opacity-50 transition-all duration-200 shadow-lg shadow-primary/10 cursor-pointer"
            >
              {isVerifyingKey ? (
                <>
                  <RefreshCw className="h-4.5 w-4.5 animate-spin" />
                  Verifying...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4.5 w-4.5" />
                  Verify & Enter
                </>
              )}
            </button>
          </form>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="max-w-5xl py-8 space-y-8 font-sans">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-border/80 pb-6 gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold tracking-tight text-foreground flex items-center gap-2.5">
            <Cpu className="h-8 w-8 text-primary animate-pulse" />
            RAG Pipeline Debugger
          </h1>
          <p className="text-sm text-muted-foreground">
            Execute queries and audit execution metrics, latencies, and intermediate RAG pipeline states.
          </p>
        </div>
        <button
          onClick={() => {
            setAdminKey("");
            setIsAuthenticated(false);
            localStorage.removeItem("admin_api_key");
            setTrace(null);
            setError(null);
            setInputKey("");
          }}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground rounded-xl border border-border/80 transition-colors cursor-pointer self-start md:self-center"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign Out
        </button>
      </div>

      {/* Input Form */}
      <div className="bg-card/25 border border-border/60 rounded-2xl p-6 backdrop-blur-sm space-y-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Enter a debugging query (e.g. 'What is TalentForge?')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isLoading}
              className="w-full pl-12 pr-4 py-3 bg-background border border-border/80 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary/45 disabled:opacity-50 transition-all duration-200"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground font-semibold rounded-xl text-sm hover:bg-primary/95 focus:ring-2 focus:ring-primary/45 disabled:opacity-50 transition-all duration-200 shadow-lg shadow-primary/10 cursor-pointer"
          >
            {isLoading ? (
              <RefreshCw className="h-4.5 w-4.5 animate-spin" />
            ) : (
              <Sparkles className="h-4.5 w-4.5" />
            )}
            Run Trace
          </button>
        </form>

        {/* Suggestion tags */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-xs text-muted-foreground mr-1">Suggestions:</span>
          {sampleQueries.map((q) => (
            <button
              key={q}
              onClick={() => {
                setQuery(q);
                handleRunTrace(q);
              }}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 bg-muted/65 border border-border/50 hover:border-primary/30 rounded-lg transition-colors cursor-pointer hover:bg-muted text-muted-foreground hover:text-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="flex items-start gap-3 bg-destructive/10 border border-destructive/20 text-destructive-foreground p-5 rounded-xl">
          <XCircle className="h-5.5 w-5.5 shrink-0 text-rose-500 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-bold text-sm text-foreground">Pipeline Execution Failed</h4>
            <p className="text-xs text-rose-400 font-mono leading-relaxed">{error}</p>
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="space-y-6 animate-pulse">
          <div className="h-32 bg-muted rounded-xl" />
          <div className="space-y-3">
            <div className="h-12 bg-muted rounded-xl" />
            <div className="h-12 bg-muted rounded-xl" />
            <div className="h-12 bg-muted rounded-xl" />
          </div>
        </div>
      )}

      {/* Trace Results */}
      {trace && !isLoading && (
        <div className="space-y-8 animate-fade-in">
          {/* Pipeline Execution Summary */}
          <div className="bg-card/20 border border-border/60 rounded-2xl p-6 backdrop-blur-sm space-y-6 shadow-sm">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2 border-b border-border/30 pb-3">
              <Cpu className="h-5 w-5 text-primary" /> Pipeline Execution Summary
            </h3>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1 hover:border-primary/25 transition-colors">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Scope</span>
                <span className="text-sm font-mono font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 inline-block">
                  {trace.request.project_scope || "global"}
                </span>
              </div>
              
              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1 hover:border-primary/25 transition-colors">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Rewritten</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded border inline-block ${
                  trace.request.rewrite_applied
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                    : "bg-muted text-muted-foreground border-border"
                }`}>
                  {trace.request.rewrite_applied ? "Yes" : "No"}
                </span>
              </div>

              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1 hover:border-primary/25 transition-colors">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Vector Chunks</span>
                <span className="text-sm font-mono font-bold text-foreground block">
                  {trace.retrieval.vector_stage?.candidate_count || 0}
                </span>
              </div>

              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1 hover:border-primary/25 transition-colors">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">BM25 Chunks</span>
                <span className="text-sm font-mono font-bold text-foreground block">
                  {trace.retrieval.bm25_stage?.candidate_count || 0}
                </span>
              </div>

              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1 hover:border-primary/25 transition-colors">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">After Fusion</span>
                <span className="text-sm font-mono font-bold text-secondary block">
                  {trace.retrieval.rrf_stage?.results?.length || 0}
                </span>
              </div>

              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1 hover:border-primary/25 transition-colors">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">After Grader</span>
                <span className="text-sm font-mono font-bold text-emerald-400 block">
                  {trace.retrieval.graded_stage?.results?.length || 0}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Query Processing</span>
                <span className="text-lg font-mono font-bold text-primary">
                  {trace.timings.query_processing_ms.toFixed(1)} <span className="text-xs font-normal">ms</span>
                </span>
              </div>

              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Total Retrieval</span>
                <span className="text-lg font-mono font-bold text-secondary">
                  {trace.timings.total_retrieval_ms.toFixed(1)} <span className="text-xs font-normal">ms</span>
                </span>
              </div>

              <div className="bg-background/40 border border-border/40 p-4 rounded-xl space-y-1">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">LLM Generation</span>
                <span className="text-lg font-mono font-bold text-indigo-400">
                  {trace.timings.generation_ms.toFixed(1)} <span className="text-xs font-normal">ms</span>
                </span>
              </div>

              <div className="bg-primary/5 border border-primary/20 p-4 rounded-xl space-y-1">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider block">Total Request E2E</span>
                <span className="text-lg font-mono font-bold text-primary dark:text-primary-foreground">
                  {trace.timings.total_request_ms.toFixed(1)} <span className="text-xs font-normal">ms</span>
                </span>
              </div>
            </div>
          </div>

          {/* Pipeline Stage Cards */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider pl-1">
              RAG Stages Pipeline
            </h4>

            {/* 1. Request Query Processing Stage */}
            <PipelineStageCard
              title="1. Query Processing"
              description="Identifies project-assigned scopes and rewrites query for optimal search compatibility."
              latencyMs={trace.timings.query_processing_ms}
            >
              <div className="space-y-4 text-sm py-2">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-b border-border/30 pb-4">
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1 font-semibold uppercase tracking-wider">Original Query</span>
                    <span className="font-medium text-foreground">{trace.request.original_query}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1 font-semibold uppercase tracking-wider">Rewritten Query</span>
                    <span className="font-medium text-primary">
                      {trace.request.rewritten_query || trace.request.original_query}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1 font-semibold uppercase tracking-wider">Detected Project</span>
                    <span className="font-mono text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20 inline-block">
                      {trace.request.detected_project || "None"}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1 font-semibold uppercase tracking-wider">Project Scope</span>
                    <span className="font-mono text-xs font-semibold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20 inline-block">
                      {trace.request.project_scope || "global"}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1 font-semibold uppercase tracking-wider">Rewrite Applied</span>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border inline-block ${
                      trace.request.rewrite_applied
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : "bg-muted text-muted-foreground border-border"
                    }`}>
                      {trace.request.rewrite_applied ? "Yes" : "No"}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1 font-semibold uppercase tracking-wider">Rewrite Reason</span>
                    <span className="text-xs text-muted-foreground leading-relaxed block italic">
                      {trace.request.rewrite_reason || "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            </PipelineStageCard>

            {/* 2. Vector Semantic Retrieval Stage */}
            {trace.retrieval.vector_stage && (
              <PipelineStageCard
                title="2. Vector Semantic Retrieval"
                description="Performs cosine similarity search using OpenAI text-embedding-3-small vectors against pgvector HNSW index."
                latencyMs={trace.retrieval.vector_stage.latency_ms}
                candidateCount={trace.retrieval.vector_stage.candidate_count}
                scoreRange={trace.retrieval.vector_stage.score_range}
                chunks={trace.retrieval.vector_stage.results}
              />
            )}

            {/* 3. BM25 Lexical Retrieval Stage */}
            {trace.retrieval.bm25_stage && (
              <PipelineStageCard
                title="3. BM25 Lexical Retrieval"
                description="Performs keyword BM25 frequency-based search against the in-memory document index."
                latencyMs={trace.retrieval.bm25_stage.latency_ms}
                candidateCount={trace.retrieval.bm25_stage.candidate_count}
                scoreRange={trace.retrieval.bm25_stage.score_range}
                chunks={trace.retrieval.bm25_stage.results}
              />
            )}

            {/* 4. Reciprocal Rank Fusion (RRF) Stage */}
            {trace.retrieval.rrf_stage && (
              <PipelineStageCard
                title="4. Reciprocal Rank Fusion (RRF)"
                description="Fuses vector semantic search and BM25 lexical results in parallel, utilizing reciprocal ranks to find the best union."
                latencyMs={trace.retrieval.rrf_stage.latency_ms}
                candidateCount={trace.retrieval.rrf_stage.candidate_count}
                duplicatesRemoved={trace.retrieval.rrf_stage.duplicates_removed}
                chunks={trace.retrieval.rrf_stage.results}
              />
            )}

            {/* 5. Source Diversification Stage */}
            {trace.retrieval.diversified_stage && (
              <PipelineStageCard
                title="5. Source Diversification"
                description="Restricts top-ranked chunks so no single source document dominates context, ensuring rich cross-file reference."
                latencyMs={trace.retrieval.diversified_stage.latency_ms}
                candidateCount={trace.retrieval.diversified_stage.candidate_count}
                duplicatesRemoved={trace.retrieval.diversified_stage.duplicates_removed}
                chunks={trace.retrieval.diversified_stage.results}
              >
                {/* Diversity statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-muted/20 dark:bg-muted/10 border border-border/40 rounded-xl mb-2 text-xs">
                  <div className="space-y-1">
                    <span className="text-muted-foreground block uppercase font-semibold tracking-wider">Chunks Before</span>
                    <span className="text-sm font-mono font-bold text-foreground">
                      {trace.retrieval.rrf_stage?.results?.length || 0}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-muted-foreground block uppercase font-semibold tracking-wider">Chunks After</span>
                    <span className="text-sm font-mono font-bold text-primary">
                      {trace.retrieval.diversified_stage.results.length}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-muted-foreground block uppercase font-semibold tracking-wider">Unique Sources Before</span>
                    <span className="text-sm font-mono font-bold text-foreground">
                      {new Set(trace.retrieval.rrf_stage?.results?.map(r => r.source_file) || []).size}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-muted-foreground block uppercase font-semibold tracking-wider">Unique Sources After</span>
                    <span className="text-sm font-mono font-bold text-emerald-400">
                      {new Set(trace.retrieval.diversified_stage.results.map(r => r.source_file)).size}
                    </span>
                  </div>
                </div>
              </PipelineStageCard>
            )}

            {/* 6. LLM Retrieval Grader Stage */}
            {trace.retrieval.graded_stage && (
              <PipelineStageCard
                title="6. LLM Retrieval Grader"
                description="Filters out chunks deemed irrelevant to the query by running an LLM-based binary classification step."
                latencyMs={trace.retrieval.graded_stage.latency_ms}
                candidateCount={trace.retrieval.graded_stage.candidate_count}
                duplicatesRemoved={trace.retrieval.graded_stage.duplicates_removed}
                chunks={trace.retrieval.graded_stage.results}
                rejectedChunks={trace.retrieval.graded_stage.rejected_results}
              />
            )}

            {/* 7. Context Assembly Stage */}
            <PipelineStageCard
              title="7. Context Assembly"
              description="Aggregates and formats the validated relevant chunks into the final prompt context."
              latencyMs={0.0}
            >
              <div className="space-y-4 py-2 text-sm">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-muted/15 border border-border/40 p-3.5 rounded-xl text-center space-y-1">
                    <span className="text-xs text-muted-foreground block font-medium uppercase tracking-wider">Total Chunks</span>
                    <span className="text-lg font-bold text-foreground font-mono">
                      {trace.retrieval.graded_stage?.results?.length || 0}
                    </span>
                  </div>
                  <div className="bg-muted/15 border border-border/40 p-3.5 rounded-xl text-center space-y-1">
                    <span className="text-xs text-muted-foreground block font-medium uppercase tracking-wider">Estimated Tokens</span>
                    <span className="text-lg font-bold text-primary font-mono">
                      {trace.generation.token_count || Math.round((trace.retrieval.final_context || "").length / 4)}
                    </span>
                  </div>
                  <div className="bg-muted/15 border border-border/40 p-3.5 rounded-xl text-center space-y-1">
                    <span className="text-xs text-muted-foreground block font-medium uppercase tracking-wider">Source Files</span>
                    <span className="text-lg font-bold text-secondary font-mono">
                      {new Set(trace.retrieval.graded_stage?.results?.map(r => r.source_file) || []).size}
                    </span>
                  </div>
                  <div className="bg-muted/15 border border-border/40 p-3.5 rounded-xl text-center space-y-1">
                    <span className="text-xs text-muted-foreground block font-medium uppercase tracking-wider">Total Characters</span>
                    <span className="text-lg font-bold text-indigo-400 font-mono">
                      {(trace.retrieval.final_context || "").length}
                    </span>
                  </div>
                </div>

                {/* Layer Distribution */}
                <div className="space-y-2 border border-border/50 bg-card/5 p-4 rounded-xl">
                  <span className="text-xs text-muted-foreground block font-semibold uppercase tracking-wider flex items-center gap-1">
                    <Layers className="h-3.5 w-3.5 text-primary" /> Layer Distribution
                  </span>
                  <div className="flex gap-4">
                    {(() => {
                      const chunks = trace.retrieval.graded_stage?.results || [];
                      const l1 = chunks.filter(c => c.layer === "1" || c.layer.toLowerCase() === "identity").length;
                      const l2 = chunks.filter(c => c.layer === "2" || c.layer.toLowerCase() === "design").length;
                      const l3 = chunks.filter(c => c.layer === "3" || c.layer.toLowerCase() === "artifact").length;
                      return (
                        <>
                          <div className="flex items-center gap-1.5 text-xs">
                            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                            <span className="text-muted-foreground">Layer 1 (Identity):</span>
                            <span className="font-bold text-foreground font-mono">{l1}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-xs">
                            <span className="h-2.5 w-2.5 rounded-full bg-blue-400" />
                            <span className="text-muted-foreground">Layer 2 (Design):</span>
                            <span className="font-bold text-foreground font-mono">{l2}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-xs">
                            <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                            <span className="text-muted-foreground">Layer 3 (Artifact):</span>
                            <span className="font-bold text-foreground font-mono">{l3}</span>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                </div>

                {/* Source Files Used */}
                <div className="space-y-2 border border-border/50 bg-card/5 p-4 rounded-xl">
                  <span className="text-xs text-muted-foreground block font-semibold uppercase tracking-wider flex items-center gap-1">
                    <Code2 className="h-3.5 w-3.5 text-secondary" /> Sources Included
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {Array.from(new Set(trace.retrieval.graded_stage?.results?.map(r => r.source_file) || [])).map(src => (
                      <span key={src} className="text-xs px-2.5 py-1 bg-muted rounded border border-border/40 font-mono text-foreground/80">
                        {src}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </PipelineStageCard>

            {/* 8. Answer Generation Stage */}
            <PipelineStageCard
              title="8. Answer Generation & Preview"
              description="Sends prompt context to Gemini 2.0 and streams response tokens back."
              latencyMs={trace.generation.latency_ms}
            >
              <div className="space-y-4 py-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 border-b border-border/30 pb-3">
                  <div>
                    <span className="text-xs text-muted-foreground block">Model Name</span>
                    <span className="text-xs font-semibold bg-muted px-2 py-0.5 rounded inline-block text-foreground border border-border/50">
                      {trace.metadata.model_name || "gemini-2.0-flash"}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block">Token Estimate</span>
                    <span className="text-xs font-semibold text-foreground">
                      {trace.generation.token_count || "N/A"}
                    </span>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <span className="text-xs text-muted-foreground block">Generated Response Preview (Truncated):</span>
                  <div className="p-3 bg-primary/5 border border-primary/10 rounded-lg text-sm text-foreground whitespace-pre-wrap leading-relaxed">
                    {trace.generation.response_preview}
                  </div>
                </div>
              </div>
            </PipelineStageCard>
          </div>

          {/* Detailed Performance Breakdown */}
          <div className="bg-card/25 border border-border/60 rounded-2xl p-6 backdrop-blur-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-border/80 pb-4">
              <Clock className="h-5 w-5 text-primary" />
              <h3 className="text-base font-bold text-foreground">Pipeline Performance Breakdown</h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b border-border/50 text-xs uppercase text-muted-foreground tracking-wider font-semibold">
                    <th className="py-3 px-4">Pipeline Stage</th>
                    <th className="py-3 px-4">Telemetry Label</th>
                    <th className="py-3 px-4 text-right">Latency (ms)</th>
                    <th className="py-3 px-4 text-right">Share (%)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/30">
                  {(() => {
                    const total = trace.timings.total_request_ms || 1.0;
                    
                    const rows = [
                      {
                        stage: "Query Processing (Detection & Rewrite)",
                        label: "query_processing_ms",
                        val: trace.timings.query_processing_ms,
                      },
                      {
                        stage: "Embedding Generation (Azure OpenAI)",
                        label: "retrieval_embedding",
                        val: trace.timings.stages["retrieval_embedding"] || 0,
                      },
                      {
                        stage: "Vector similarity search (pgvector)",
                        label: "retrieval_vector_db_search",
                        val: trace.timings.stages["retrieval_vector_db_search"] || 0,
                      },
                      {
                        stage: "BM25 keyword search",
                        label: "retrieval_bm25",
                        val: trace.timings.stages["retrieval_bm25"] || 0,
                      },
                      {
                        stage: "Reciprocal Rank Fusion (RRF)",
                        label: "retrieval_rrf",
                        val: trace.timings.stages["retrieval_rrf"] || 0,
                      },
                      {
                        stage: "Source Diversification",
                        label: "retrieval_diversified",
                        val: trace.timings.stages["retrieval_diversified"] || 0,
                      },
                      {
                        stage: "Retrieval Grader (LLM Filter)",
                        label: "retrieval_graded",
                        val: trace.timings.stages["retrieval_graded"] || 0,
                      },
                      {
                        stage: "Total Retrieval Pipeline",
                        label: "total_retrieval_ms",
                        val: trace.timings.total_retrieval_ms,
                        isHighlight: true,
                      },
                      {
                        stage: "Answer Generation (LLM Streaming)",
                        label: "generation_ms",
                        val: trace.timings.generation_ms,
                        isHighlight: true,
                      },
                      {
                        stage: "Total Request E2E Execution",
                        label: "total_request_ms",
                        val: trace.timings.total_request_ms,
                        isHighlight: true,
                        isTotal: true,
                      },
                    ];

                    return rows.map((r, idx) => (
                      <tr
                        key={idx}
                        className={`hover:bg-muted/30 transition-colors duration-150 ${
                          r.isTotal
                            ? "bg-primary/5 font-bold text-primary border-t border-primary/20"
                            : r.isHighlight
                            ? "bg-muted/10 font-semibold"
                            : ""
                        }`}
                      >
                        <td className="py-3 px-4 font-medium text-foreground">{r.stage}</td>
                        <td className="py-3 px-4 font-mono text-xs text-muted-foreground">{r.label}</td>
                        <td className="py-3 px-4 text-right font-mono font-bold text-foreground">
                          {r.val.toFixed(1)} ms
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-xs text-muted-foreground">
                          {((r.val / total) * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ));
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </PageContainer>
  );
}
