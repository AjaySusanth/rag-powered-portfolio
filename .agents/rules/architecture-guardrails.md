---
trigger: always_on
---

# Architecture Guardrails

This project follows a fixed architecture defined in prd-rag-portfolio.md.
The agent must treat that document as the source of truth and follow these
constraints:

1. Stack is fixed — do not substitute without asking first:
   - Backend: FastAPI (Python 3.12)
   - Frontend: React + Tailwind CSS
   - Vector store: PostgreSQL + pgvector (HNSW index, cosine similarity)
   - Cache: Redis 7
   - Embeddings: OpenAI text-embedding-3-small (1536-dim)
   - LLM primary: Gemini 2.0 Flash — fallback: Groq llama-3.1-70b
   - GitHub ingestion: GitHub REST API, driven by per-project ingest.yml
   - Reverse proxy: NGINX
   - IaC: Terraform (Block 5 only) — CI/CD: GitHub Actions (Block 5 only)

2. Follow the three-layer knowledge base model exactly as specified:
   - Layer 1 (Identity): resume.md, about-me.md, faq.md — 256 tokens, 32 overlap
   - Layer 2 (Design, per project, manual): architecture.md, decisions.md,
     challenges.md, lessons-learned.md — 512 tokens, 64 overlap
   - Layer 3 (Artifacts, per project, auto-ingested via ingest.yml) —
     256 tokens, 32 overlap
   Do not merge layers, change chunk sizes, or change overlap values
   without flagging it as a question first.

3. Retrieval must be hybrid by design: pgvector vector search + BM25
   keyword search in parallel, merged via Reciprocal Rank Fusion (RRF).
   Do not replace BM25 with vector-only search, even if it "seems simpler" —
   this is a deliberate PRD decision (code retrieves poorly via vector
   search alone; see Challenge 2 in the PRD).

4. Build order follows the PRD's Block 1 → Block 6 sequence:
   Block 1 (RAG core) → Block 2 (retrieval quality + caching) →
   Block 3 (API + streaming) → Block 4 (observability) →
   Block 5 (cloud deployment) → Block 6 (polish).
   Do not start Block 5 (Terraform/Azure) or Block 4 (Prometheus/analytics)
   work before Blocks 1-3 are functioning end-to-end locally via
   Docker Compose. If asked to jump ahead, flag the dependency instead
   of silently complying.

5. Local development uses Docker Compose only
   (pgvector/pgvector:pg16 image + redis:7-alpine). Do not introduce
   Azure Database for PostgreSQL Flexible Server or Azure Cache for
   Redis until Block 5 work is explicitly requested.

6. Any deviation from the PRD — including ones that seem like genuine
   improvements — must be raised as a question with a one-line
   justification, not applied silently. I decide; you propose.

7. When in doubt about which layer, chunk size, or component a feature
   belongs to, re-check prd-rag-portfolio.md before guessing.