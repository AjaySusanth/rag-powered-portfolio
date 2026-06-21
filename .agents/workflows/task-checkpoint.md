---
description: 
---

# Workflow: /task-checkpoint
Use this for every non-trivial task (anything beyond a one-line fix).

## Phase 1 — Before writing code

Produce a short brief with these sections, then STOP and wait for my
explicit approval before writing any code:

1. **Concept** — what problem is this task solving, in plain English.
2. **Architecture** — where this fits in the system (which layer/module,
   what it talks to, what depends on it).
3. **Design decisions** — the 1-3 real choices being made (e.g. "BM25 vs
   vector-only", "256 vs 512 token chunks") and why this option over the
   alternatives. If a decision is already fixed by the PRD or
   architecture-guardrails.md, say so instead of re-deriving it.
4. **Implementation plan** — a numbered list of concrete steps/files to
   be created or changed. No code yet.

Do not proceed to Phase 2 until I respond with approval or changes.

## Phase 2 — After writing code

Once the code is written, before considering the task done:

1. **Explain the code** — a short walkthrough of what was built, file by
   file if more than one file changed.
2. **Flag non-intuitive parts** — any algorithm, library, or pattern that
   isn't obvious (e.g. RRF, HNSW, SSE, cache key hashing) explained in
   plain language at the point it's used.
3. **Ask me a question** — one question that tests whether I understood
   the key tradeoff or mechanism in this task.
4. **Wait for my answer and any follow-up questions.** Resolve every
   question I raise — fully, not just acknowledged — before telling me
   the task is ready to commit/merge or moving to the next task.

Do not start the next task until Phase 2 is fully resolved.