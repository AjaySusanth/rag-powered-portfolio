# RAG-Powered Developer Portfolio

> AI-powered developer portfolio that answers recruiter and engineer questions using a production-grade Retrieval-Augmented Generation pipeline with grounded citations.

A portfolio that goes beyond a static resume. Ask questions in natural language and receive grounded, cited answers drawn directly from project documentation, architecture notes, and engineering decisions.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://postgresql.org)
[![pgvector](https://img.shields.io/badge/pgvector-HNSW-336791?logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-Embeddings-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![Gemini](https://img.shields.io/badge/Google_Gemini-Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**[Live Demo](https://rag-powered-portfolio.vercel.app/)**


## Why This Project?

Traditional developer portfolios are static. They require a recruiter or engineer to manually browse project pages, read lengthy descriptions, and mentally assemble a picture of the candidate's depth and capabilities.

This project replaces that experience with an AI assistant that:

- **Retrieves grounded answers** from actual project documentation, architecture decisions, and engineering notes — not hallucinated responses.
- **Cites every claim** with a direct source reference, giving the reader full transparency into what the system knows.
- **Answers naturally** across domains: projects, technologies, architecture, deployment, availability, and experience.
- **Demonstrates engineering depth** as a project in itself — the portfolio is a production RAG system, not a demo.

The system is also an intentional learning artefact. Every design decision in the retrieval pipeline is documented inline, from chunk size choices to why Reciprocal Rank Fusion was preferred over single-ranker approaches.

---

## Key Features

### AI & Retrieval
- **Hybrid Retrieval** — pgvector semantic search and BM25 lexical search executed concurrently, then merged via Reciprocal Rank Fusion (RRF)
- **Query Rewriting** — LLM-powered query expansion to improve retrieval recall on ambiguous inputs
- **Retrieval Grading** — LLM-based relevance filtering that discards low-signal chunks before generation
- **Source Diversification** — prevents a single document from dominating the context window
- **Project Detection** — deterministic token-based routing that scopes retrieval to the correct project namespace
- **Citation Attribution** — LLM-based source mapping that links each generated claim back to a retrieved chunk
- **Streaming Responses** — Server-Sent Events (SSE) for real-time token delivery to the browser

### Backend
- **FastAPI** with async-first route handlers and Pydantic v2 request/response models
- **PostgreSQL + pgvector** with HNSW index and cosine similarity for sub-millisecond vector search
- **Redis Cache** for response caching (24h TTL) and embedding caching (7d TTL) with binary serialization
- **Rate Limiting** — fixed-window in-memory rate limiter per client IP (configurable, default 10 req/min)
- **Structured Prompt Builder** — versioned prompt assembly with context injection and citation formatting
- **Prompt Guard** — input sanitization to reject off-topic or adversarial queries before retrieval

### Frontend
- **Next.js 16** with App Router and React Server Components
- **Streaming Chat UI** with SSE-based real-time token rendering and typing cursor animation
- **Markdown Rendering** — full GFM support including tables, code blocks with syntax highlighting, and blockquotes
- **Citation Cards** — per-source attribution cards displayed below each assistant response
- **Mobile-First Responsive Design** — tested at 320px, 375px, 425px, and 768px viewports
- **Dark / Light Mode** with system preference detection

### Engineering
- **Docker Compose** for local development (pgvector/pgvector:pg16 + redis:7-alpine)
- **GitHub Actions** for CI with ruff linting and pytest unit tests
- **Render** for backend deployment via Docker + render.yaml blueprint
- **Evaluation Framework** — golden dataset with Recall@K, Hit Rate, and MRR metrics for retrieval regression testing
- **24 unit test files** covering retrieval, chunking, embedding, caching, rate limiting, and API endpoints

---

## Architecture

### Request Lifecycle

```mermaid
graph TD
    A[User] -->|types question| B[Next.js Frontend]
    B -->|POST /chat SSE| C[FastAPI Backend]
    C -->|check cache| D{Redis Cache}
    D -->|cache hit| B
    D -->|cache miss| E[Prompt Guard]
    E -->|sanitised query| F[Project Detector]
    F -->|scoped query + namespace| G[Query Rewriter]
    G -->|expanded query| H[Hybrid Retriever]
    H -->|parallel| I[Vector Search pgvector HNSW]
    H -->|parallel| J[BM25 Search rank-bm25]
    I --> K[RRF Fusion]
    J --> K
    K --> L[Source Diversification]
    L --> M[Retrieval Grader]
    M -->|filtered chunks| N[Prompt Builder]
    N -->|structured prompt| O[Gemini Flash]
    O -->|streamed tokens| P[Citation Attributor]
    P -->|response + citations| Q[SSE Stream]
    Q -->|token by token| B
    B -->|rendered markdown + citation cards| A
```

### Three-Layer Knowledge Base

The knowledge base is divided into three layers with different chunking strategies:

| Layer | Content | Chunk Size | Overlap | Source |
|-------|---------|-----------|---------|--------|
| Layer 1 — Identity | `resume.md`, `about-me.md`, `faq.md` | 256 tokens | 32 | Manual |
| Layer 2 — Design | Per-project `architecture.md`, `decisions.md`, `challenges.md`, `lessons-learned.md` | 512 tokens | 64 | Manual |
| Layer 3 — Artifacts | Source code, YAML, configuration files | 256 tokens | 32 | GitHub API via `ingest.yml` |

---

## Retrieval Pipeline

Each user query passes through the following stages before a response is generated:

1. **Prompt Guard** — Rejects clearly off-topic queries (e.g. weather, sports) before triggering retrieval or LLM calls.
2. **Project Detection** — Identifies whether the query targets a specific project using normalized token-based regex matching, then scopes the vector search to that project's namespace.
3. **Query Rewriting** — Optionally expands the query using an LLM to improve recall for ambiguous or terse inputs (e.g. "how does caching work" → "explain the Redis embedding cache and response cache architecture").
4. **Vector Search** — Embeds the query using `text-embedding-3-small` via Azure OpenAI, then retrieves the top-K chunks by cosine similarity from the pgvector HNSW index.
5. **BM25 Search** — Tokenizes the query and retrieves the top-K chunks by BM25 score using `rank-bm25` against an in-memory corpus per project namespace.
6. **Reciprocal Rank Fusion (RRF)** — Merges the two ranked lists into a single fused ranking without requiring normalized scores. Each document's RRF score is `1 / (k + rank)` where `k=60`, making it robust to outlier scores from either retriever.
7. **Source Diversification** — Caps the number of chunks from any single source file (default: 3) to prevent one document from consuming the entire context window.
8. **Retrieval Grading** — An LLM evaluates each remaining chunk for relevance to the original query. Irrelevant chunks are discarded; if too few remain, the system falls back to the pre-grading set.
9. **Prompt Assembly** — Surviving chunks are injected into a versioned structured prompt that instructs the model to answer only from the provided context and to include citation markers.
10. **Generation** — Gemini Flash streams the response token by token via SSE.
11. **Citation Attribution** — After generation completes, a second LLM pass maps each claim in the response back to its source chunk, producing the citation cards displayed in the UI.

---

## RAG Pipeline Debugger (Admin Only)

To inspect and audit the retrieval pipeline's internal state, the portfolio contains a dedicated administrative path (`/admin/trace`). For any given query, this dashboard visualizes the execution flow step-by-step:
1. **Query Processing**: Displays the original query, detected project, scope resolution, rewrite decision, and expansion logic.
2. **Vector Retrieval**: Displays top semantic search matches from the pgvector HNSW index.
3. **BM25 Retrieval**: Displays keyword matches from the rank-bm25 index.
4. **Reciprocal Rank Fusion**: Shows the rank-fused union and score calculations.
5. **Source Diversification**: Displays source coverage stats and chunk capping results.
6. **Retrieval Grader**: Highlights accepted versus rejected chunks (including explicit grading rejection reasons).
7. **Context Assembly**: Shows token counts, layer distribution, and input documents.
8. **Answer Generation**: Shows the model preview and token estimates.

> [!NOTE]
> The debugger operates as a **passive tool**. The `PipelineTrace` collection logic is completely isolated from production chat paths and will not influence the retrieval results, ranking algorithms, or prompt context assembly of regular visitors.

---

## Tech Stack

| Category | Technology |
|----------|-----------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS |
| **Backend** | FastAPI, Python 3.12, Pydantic v2, Uvicorn |
| **Database** | PostgreSQL 16, pgvector (HNSW index, cosine similarity) |
| **Vector Search** | pgvector, Azure OpenAI `text-embedding-3-small` (1536-dim) |
| **AI — Generation** | Google Gemini Flash (primary), Groq llama-3.1-70b (fallback) |
| **AI — Retrieval** | BM25 (`rank-bm25`), RRF fusion |
| **Caching** | Redis 7 (response cache + embedding cache) |
| **Cloud — Embeddings** | Azure OpenAI |
| **DevOps** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |
| **Deployment** | Render (backend), Vercel (frontend), Neon (database), Upstash (Redis) |
| **Testing** | pytest, anyio, pytest-asyncio |

---

## Repository Structure

```
rag-portfolio/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/         # chat.py, portfolio.py, admin.py
│   │   │   └── schemas/        # Pydantic request/response models
│   │   ├── cache/              # Redis + base cache, embedding cache, factory
│   │   ├── chunking/           # Token-based chunker with configurable overlap
│   │   ├── db/                 # asyncpg pool, connection management
│   │   ├── embedding/          # Azure OpenAI embedder with Redis caching
│   │   ├── ingestion/          # GitHub fetcher, manual loader, embedder, pipeline
│   │   ├── llm/                # Gemini client, grader, rewriter, attributor, factory
│   │   ├── models/             # Domain models (RetrievalResult, etc.)
│   │   ├── retrieval/          # vector_retriever, bm25_retriever, rrf, hybrid_retriever, grader
│   │   ├── services/           # chat_service, ingestion_service, prompt_builder, prompt_guard
│   │   ├── vectorstore/        # pgvector upsert, query, schema
│   │   ├── config.py           # Pydantic Settings — all env vars in one place
│   │   └── main.py             # FastAPI app, lifespan, CORS, router registration
│   ├── scripts/                # Ingestion CLI, evaluation runners, inspection utilities
│   ├── tests/                  # 24 test files covering all modules
│   ├── assets/resume/          # Resume PDF served by the portfolio endpoint
│   ├── data/                   # Static JSON files (projects, stack, hire info)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages
│       ├── components/         # chat/, layout/, home/, resume/, projects/, hire/
│       ├── hooks/              # useChat, useAutoScroll
│       ├── services/api/       # Typed API client for chat and portfolio endpoints
│       └── types/              # TypeScript interfaces
├── knowledge/                  # Manual knowledge base (Markdown files per project)
│   ├── resume.md
│   ├── about-me.md
│   ├── faq.md
│   ├── talentforge/
│   ├── classsync/
│   └── n8n-aks-platform/
├── evaluation/                 # Golden datasets and retrieval evaluation results
├── docker-compose.yml          # Local dev: pgvector + redis
├── render.yaml                 # Render deployment blueprint
└── pyproject.toml
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose
- Azure OpenAI account with `text-embedding-3-small` deployed
- Google Gemini API key

### Installation

```bash
git clone https://github.com/AjaySusanth/rag-portfolio.git
cd rag-portfolio

# Create Python virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
.\venv\Scripts\Activate.ps1     # PowerShell
```

### Environment Variables

```bash
cp backend/.env.example .env
```

Edit `.env` and fill in the following required values:

```env
# Database (local Docker or Neon)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/portfolio

# Redis (local Docker or Upstash)
REDIS_URL=redis://localhost:6379

# Azure OpenAI (required for embeddings)
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Google Gemini (required for generation, grading, attribution)
GEMINI_API_KEY=your-key
```

### Start Infrastructure (Docker)

```bash
docker compose up -d
# Starts: PostgreSQL 16 with pgvector on :5432, Redis 7 on :6379
```

### Backend

```bash
# From repo root with venv active
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
# Available at http://localhost:3000
```

### Ingestion

Before the chat works, the knowledge base must be indexed:

```bash
# PowerShell (from repo root)
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/index_project.py __global__
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/index_project.py talentforge
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/index_project.py classsync
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/index_project.py n8n-aks-platform
```

### Tests

```bash
# From repo root
python -m pytest backend/tests -v
```

---

## Deployment

The production deployment uses fully managed services to minimize operational overhead:

| Component | Platform | Notes |
|-----------|----------|-------|
| **Frontend** | Vercel | Automatic deploys from `main` branch |
| **Backend** | Render | Dockerized via `render.yaml` blueprint |
| **Database** | Neon | PostgreSQL with pgvector extension, serverless |
| **Redis** | Upstash | Serverless Redis with TLS, Redis 7 compatible |

> **Azure deployment** (AKS, Azure Database for PostgreSQL Flexible Server, Azure Cache for Redis) is planned as a separate Block 5 milestone per the project PRD.

### Production Environment Variables

Set the following in Render's environment dashboard or via `render.yaml`:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@neon-host/portfolio?sslmode=require
REDIS_URL=rediss://default:password@upstash-host:6379
ALLOWED_ORIGINS=https://your-frontend.vercel.app
AZURE_OPENAI_KEY=...
AZURE_OPENAI_ENDPOINT=...
GEMINI_API_KEY=...
```

---

## Evaluation

The retrieval pipeline is evaluated against a **golden dataset** of question–answer pairs with known relevant chunks. This prevents retrieval regressions when tuning chunk sizes, retrieval parameters, or ranking logic.

**Metrics computed:**

| Metric | Description |
|--------|-------------|
| **Hit Rate @ K** | Fraction of queries where the correct chunk appears in the top-K results |
| **Recall @ K** | Fraction of all relevant chunks retrieved within the top-K |
| **MRR (Mean Reciprocal Rank)** | Mean of 1/rank for the first correct result, measuring ranking quality |

**Why evaluation exists:** RAG systems are sensitive to chunking strategy, embedding model, and retrieval parameters. Without a quantified baseline, it is impossible to distinguish improvements from regressions when the pipeline changes.

```bash
# Run retrieval evaluation
$env:PYTHONPATH="backend"; .\venv\Scripts\python backend/scripts/run_golden_eval.py
```

Results are written to `evaluation/results/` as JSON and Markdown reports.

---

## Example Questions

The portfolio can answer a broad range of recruiter and engineer questions:

```
Tell me about yourself.
What projects have you built?
Explain TalentForge — what problem does it solve?
What technologies and frameworks do you work with?
Describe your Kubernetes platform project.
How does your RAG pipeline work?
Which project best demonstrates your backend engineering?
What cloud platforms have you worked with?
How do you handle database performance?
What is your approach to system design?
How can I contact you or discuss a role?
```

---

## Roadmap

### Completed

- [x] Three-layer knowledge base with project namespacing
- [x] Hybrid retrieval: vector search + BM25 + RRF fusion
- [x] Source diversification
- [x] Retrieval grading with LLM-based relevance filtering
- [x] Query rewriting with configurable provider
- [x] Citation attribution with per-source cards
- [x] Streaming SSE chat with real-time token delivery
- [x] Redis response cache + embedding cache
- [x] Rate limiting per client IP
- [x] Prompt guard and input sanitization
- [x] Mobile-first responsive UI (tested 320px–1440px)
- [x] Public deployment (Render + Vercel + Neon + Upstash)
- [x] Retrieval evaluation framework with golden dataset
- [x] GitHub Actions CI with linting and unit tests

### Planned

- [ ] Azure deployment (AKS, Azure PostgreSQL, Azure Cache for Redis)
- [ ] Admin dashboard for re-indexing and cache management
- [ ] Analytics dashboard (query volume, cache hit rates, retrieval quality over time)
- [ ] Conversation history with session persistence
- [ ] Streaming citation attribution during generation
- [ ] Multi-turn conversation context


---

## Acknowledgements

This project is built on the shoulders of excellent open-source tools and managed services:

- **[FastAPI](https://fastapi.tiangolo.com)** — async Python web framework
- **[Next.js](https://nextjs.org)** — React framework with App Router and streaming support
- **[pgvector](https://github.com/pgvector/pgvector)** — vector similarity search extension for PostgreSQL
- **[rank-bm25](https://github.com/dorianbrown/rank_bm25)** — BM25 implementation for lexical retrieval
- **[Google Gemini](https://ai.google.dev)** — LLM for generation, grading, rewriting, and citation attribution
- **[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)** — `text-embedding-3-small` for dense vector embeddings
- **[Redis](https://redis.io)** — response and embedding caching
- **[Neon](https://neon.tech)** — serverless PostgreSQL
- **[Upstash](https://upstash.com)** — serverless Redis
