---
trigger: always_on
---

# Code Style & Conventions

## Python (FastAPI backend)

1. Type hints on every function signature, including return types.
2. Follow PEP 8. Use `ruff` for linting/formatting — don't hand-roll
   formatting opinions.
3. Use Pydantic models for all request/response schemas — no raw dicts
   crossing API boundaries.
4. Prefer `async def` for all I/O-bound routes (DB, Redis, GitHub API,
   LLM calls). Don't mix sync blocking calls into async routes.
5. One responsibility per module. Retrieval logic, chunking, embedding,
   caching, and LLM calls each live in their own module — no god-files.
6. Every non-trivial function gets a docstring: one line of what it does,
   and (per learning-mode.md) a note on why if the approach isn't obvious.
7. Custom exceptions for domain errors (e.g. `RetrievalLowConfidenceError`,
   `IngestionConfigError`) rather than bare `Exception` or silent `except: pass`.
8. No hardcoded secrets, API keys, or connection strings — environment
   variables only, loaded via a single `config.py` / `Settings` object.

## React / Frontend

1. Functional components with hooks only — no class components.
2. Tailwind utility classes for styling; no inline style objects unless
   dynamic values require it.
3. Co-locate component-specific logic with the component; shared logic
   (SSE handling, API client) goes in `/lib` or `/hooks`.
4. Type everything with TypeScript — no implicit `any`.

## Testing

1. Every new module gets at least one test file (`test_<module>.py` /
   `<Component>.test.tsx`) before it's considered "done" — not deferred
   to a later cleanup pass.
2. Tests should cover the actual logic (chunking boundaries, RRF ranking
   order, cache key hashing) — not just "does it not throw."
3. Mock external calls (GitHub API, Gemini, OpenAI embeddings) in unit
   tests; don't make real network calls in the test suite.

## Git / Commits

1. Use Conventional Commits for every commit message:
   `<type>(<scope>): <short summary>`
   Types: feat, fix, refactor, chore, test, docs, perf, ci, build
   Examples:
   - feat(retrieval): add hybrid BM25 + vector search with RRF
   - fix(ingestion): correct chunk overlap calculation for layer 2 docs
   - refactor(chunker): extract token counting into shared utility
   - chore(deps): bump pgvector image to pg16
   - docs(readme): document ingest.yml schema

2. Scope should name the module/feature, not the PRD block
   (e.g. `retrieval`, `ingestion`, `chat-api`, `cache`, `frontend`)
   — never reference internal planning structure like block numbers.

3. Commit body (optional, for non-trivial changes) explains *why*,
   not just what — especially for design decisions, not restated diffs.

4. Branching strategy:
   - `main` — always deployable, protected
   - `feat/<short-name>` — new features (e.g. `feat/hybrid-retrieval`)
   - `fix/<short-name>` — bug fixes
   - `refactor/<short-name>` — internal restructuring, no behavior change
   - `chore/<short-name>` — tooling, deps, config
   One branch per logical unit of work. Merge via PR into `main` even
   when working solo — keeps history reviewable and gives a clean PR
   trail to point to in interviews.

5. No direct commits to `main`. No commented-out dead code in commits —
   delete it or explain why it's kept.

6. Squash-merge feature branches so `main` history reads as one
   clean commit per feature, following the Conventional Commits format
   above.