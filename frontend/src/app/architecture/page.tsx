import * as React from "react";
import { PageContainer } from "@/components/common/PageContainer";
import { PageHeader } from "@/components/common/PageHeader";
import { ArchitectureSection } from "@/components/architecture/ArchitectureSection";
import { TimelineStep } from "@/components/architecture/TimelineStep";
import { Database, GitBranch, ShieldCheck, Terminal, Layers, Cpu } from "lucide-react";

export default function ArchitecturePage() {
  return (
    <PageContainer className="space-y-8 max-w-5xl mx-auto py-8">
      <PageHeader
        title="System Architecture"
        description="A technical deep-dive into the ingestion pipelines, retrieval strategies, database modeling, and deployment architectures of this RAG-powered showcase."
      />

      {/* 1. Overview Section */}
      <ArchitectureSection
        id="overview"
        title="1. System Overview"
        badge="Core Concept"
        description="The portfolio implements a highly specialized, context-grounded Retrieval-Augmented Generation (RAG) system. The core goal is to deliver zero-hallucination, low-latency, and evidence-backed answers to recruiter questions about projects, work history, and engineering decisions."
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-2">
          <div className="flex flex-col p-4 bg-muted/40 border border-border/50 rounded-xl space-y-2">
            <Layers className="h-5 w-5 text-primary" />
            <h4 className="text-xs font-bold text-foreground">Three-Layer Knowledge</h4>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Structured catalog: Layer 1 (Identity files), Layer 2 (Design docs & project briefs), and Layer 3 (GitHub codebase artifacts).
            </p>
          </div>
          <div className="flex flex-col p-4 bg-muted/40 border border-border/50 rounded-xl space-y-2">
            <ShieldCheck className="h-5 w-5 text-primary" />
            <h4 className="text-xs font-bold text-foreground">Grounded Citations</h4>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              A post-generation LLM attribution step filters out unreferenced sources, displaying only documents that directly evidence the answer.
            </p>
          </div>
          <div className="flex flex-col p-4 bg-muted/40 border border-border/50 rounded-xl space-y-2">
            <Cpu className="h-5 w-5 text-primary" />
            <h4 className="text-xs font-bold text-foreground">Hybrid Engine</h4>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Combines semantic embeddings (pgvector cosine distance) with lexical keywords (BM25) using Reciprocal Rank Fusion (RRF).
            </p>
          </div>
        </div>
      </ArchitectureSection>

      {/* 2. Ingestion Section */}
      <ArchitectureSection
        id="ingestion"
        title="2. Ingestion Pipeline"
        badge="Data Flow"
        description="Data ingestion runs as an idempotent, metadata-aware process. It extracts documents from local files and remote GitHub repositories, processes their layouts, and maps them to a centralized Postgres schema."
      >
        <div className="space-y-4">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Ingestion is configured per-project via <code>ingest.yml</code> files specifying inclusion/exclusion rules. The workflow isolates global identity contexts from project-specific code and design resources, enforcing clear scopes inside the database.
          </p>
          <div className="rounded-xl border border-border/60 bg-muted/20 p-4 font-mono text-[10px] text-muted-foreground overflow-x-auto space-y-1">
            <div className="text-foreground font-bold"># Document Database Schema (chunks table)</div>
            <div>CREATE TABLE chunks (</div>
            <div>  id UUID PRIMARY KEY,</div>
            <div>  content TEXT NOT NULL,</div>
            <div>  embedding VECTOR(1536), <span className="text-primary/70">-- OpenAI text-embedding-3-small</span></div>
            <div>  project VARCHAR(50) NOT NULL,</div>
            <div>  file VARCHAR(255) NOT NULL,</div>
            <div>  layer VARCHAR(20) NOT NULL,</div>
            <div>  metadata JSONB NOT NULL</div>
            <div>);</div>
          </div>
        </div>
      </ArchitectureSection>

      {/* 3. Retrieval Section (Pipeline Timeline) */}
      <ArchitectureSection
        id="retrieval"
        title="3. Retrieval & Synthesis Pipeline"
        badge="Real-time Execution"
        description="Every incoming query traverses a linear multi-stage pipeline designed to optimize relevance, balance search pools, stream responses, and verify citation honesty."
      >
        <div className="mt-4 p-4 border border-border/40 bg-muted/10 rounded-2xl">
          <TimelineStep
            number={1}
            title="Query Analysis & Rewrite"
            technologies={["FastAPI", "Gemini 2.0"]}
            description="Incoming questions are analyzed to determine project scope. If a query references a specific project (e.g., 'TalentForge'), a regex boundary filter resolves the scope to prevent cross-project noise. A query rewriter cleans shorthand questions."
            details={[
              "Deterministic project routing isolates search space.",
              "Maintains session history to resolve contextual references."
            ]}
          />
          <TimelineStep
            number={2}
            title="Heading-Aware Chunking"
            technologies={["Python Markdown", "Custom Tokenizer"]}
            description="Source documents are split using a customized heading-aware chunker. Heading hierarchies are prepended to body paragraphs rather than emitted as standalone header-only chunks, preserving context."
            details={[
              "Configurable chunk token sizes (256/512 tokens) based on layer rules.",
              "Overlap values (32/64 tokens) ensure no information is sliced at boundaries."
            ]}
          />
          <TimelineStep
            number={3}
            title="Dual Vector + Lexical Search"
            technologies={["pgvector (HNSW)", "BM25 (Rank-BM25)"]}
            description="The query is executed concurrently against two indices to locate candidates. Semantic lookup scans the HNSW vector database using cosine distance, while lexical lookup indexes token matches."
            details={[
              "HNSW index on pgvector column optimizes cosine similarity checks.",
              "Concurrent retrieval prevents slow-downs on database IO."
            ]}
          />
          <TimelineStep
            number={4}
            title="Reciprocal Rank Fusion (RRF)"
            technologies={["Math / RRF Algorithms"]}
            description="RRF merges the semantic candidate pool and keyword matches. By assigning reciprocal rank weights, RRF promotes items that appear high in both lists while protecting against code-keyword starvation."
            details={[
              "Constant factor (k=60) stabilizes rank-merge distributions.",
              "Configurable limit limits output candidate lists to top results."
            ]}
          />
          <TimelineStep
            number={5}
            title="Source Diversification"
            technologies={["Python Filtering"]}
            description="Filters final candidates to enforce a maximum of 3 chunks per source file. This guarantees that one large document cannot monopolize the context window, leaving space for other files."
            details={[
              "Deduplicates overlapping or redundant content chunks.",
              "Improves answer depth by pulling details from multiple file targets."
            ]}
          />
          <TimelineStep
            number={6}
            title="Context Synthesis & Prompting"
            technologies={["Gemini 2.0 Flash"]}
            description="Builds the LLM generation prompt. Rules enforce best-effort synthesis from retrieved context while prohibiting hallucinations, instructing the model to decline if no documentation exists."
            details={[
              "Encodes strict grounding instructions into system prompt.",
              "Maintains token counts to prevent context overflow."
            ]}
          />
          <TimelineStep
            number={7}
            title="Streaming Response Generation"
            technologies={["Server-Sent Events (SSE)"]}
            description="As the LLM generates tokens, FastAPI streams them directly to the client as Server-Sent Events. This minimizes Time-To-First-Token (TTFT) and makes the UI responsive."
            details={[
              "Asynchronous generator prevents thread blocking.",
              "Handles client disconnects cleanly via abort notifications."
            ]}
          />
          <TimelineStep
            number={8}
            title="Post-Generation Citation Attribution"
            technologies={["gemini-3.1-flash-lite"]}
            description="After streaming completes, the final text is analyzed against short summaries of retrieved chunks. The model determines which chunks actually supported the answer, filtering out unused sources."
            details={[
              "Runs post-stream to eliminate generation latency.",
              "Eliminates irrelevant citations from showing up on the frontend."
            ]}
          />
        </div>
      </ArchitectureSection>

      {/* 4. Generation & Caching */}
      <ArchitectureSection
        id="generation"
        title="4. Caching & Performance"
        badge="Latency & Cost Control"
        description="The backend incorporates multi-tier caching to guarantee sub-5ms responses for repeated queries and protect outbound API rate limits."
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
          <div className="flex items-start gap-3 p-4 bg-muted/40 border border-border/50 rounded-xl">
            <Database className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-foreground">Redis Embedding Caching</h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Stores generated vector embeddings in Redis keyed by MD5 hashes. Ingesting modified codebases retrieves cached vectors in bulk, bypassing external API calls.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-4 bg-muted/40 border border-border/50 rounded-xl">
            <GitBranch className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-foreground">Redis Response Limiting</h4>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Rate limiter tracks client requests per IP address using a fixed-window pattern in Redis, defending the hosting cluster from abusive usage.
              </p>
            </div>
          </div>
        </div>
      </ArchitectureSection>

      {/* 5. Evaluation */}
      <ArchitectureSection
        id="evaluation"
        title="5. Evaluation & Quality Gates"
        badge="Offline Testing"
        description="System verification utilizes an offline evaluation framework that runs regression tests against a golden dataset of questions. This ensures retrieval and generation parameters remain optimized."
      >
        <p className="text-xs text-muted-foreground leading-relaxed">
          Retrieval quality is measured using metrics like Recall@K, Hit Rate, and Mean Reciprocal Rank (MRR). CI/CD gates re-run validations on pull requests to ensure that chunking changes or database migrations do not cause regressions.
        </p>
      </ArchitectureSection>

      {/* 6. Deployment */}
      <ArchitectureSection
        id="deployment"
        title="6. Deployment Topology"
        badge="Infrastructure"
        description="The RAG showcase runs on containerized infrastructure configured for high isolation and low overhead."
      >
        <div className="space-y-4">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Local development is managed via Docker Compose, running PostgreSQL (with pgvector), Redis 7, the FastAPI backend, and Next.js. Production is designed to deploy container apps scaling dynamically from zero to manage hosting costs.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
            <div className="p-3 bg-muted/30 border border-border/50 rounded-lg text-xs font-bold text-foreground">
              NGINX Proxy
            </div>
            <div className="p-3 bg-muted/30 border border-border/50 rounded-lg text-xs font-bold text-foreground">
              FastAPI backend
            </div>
            <div className="p-3 bg-muted/30 border border-border/50 rounded-lg text-xs font-bold text-foreground">
              Redis 7 Cache
            </div>
            <div className="p-3 bg-muted/30 border border-border/50 rounded-lg text-xs font-bold text-foreground">
              pgvector / pg16
            </div>
          </div>
        </div>
      </ArchitectureSection>
    </PageContainer>
  );
}
