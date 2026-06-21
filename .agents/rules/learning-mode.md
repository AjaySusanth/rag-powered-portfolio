---
trigger: always_on
---

# Learning Mode

This is a student portfolio project. The priority is understanding, not just
working code. Follow these constraints on every task:

1. Before writing any non-trivial code (retrieval logic, chunking, ranking,
   caching, ingestion), first explain the approach in plain English in
   3-5 sentences, and wait for explicit approval before writing code.

2. After generating code, add a short comment block at the top of the file
   explaining WHY this design was chosen — not just a restatement of what
   the code does.

3. If a concept is non-obvious or new to this codebase (e.g. RRF, HNSW,
   BM25 tokenization, SSE streaming, cosine similarity, reciprocal rank
   fusion, retrieval grading), explain it inline in plain language the
   first time it's introduced.

4. Never silently swap or "improve" an architectural decision already
   fixed in the project's PRD (e.g. swapping pgvector for Pinecone,
   or Gemini for OpenAI as the primary LLM) without flagging it to me
   as a question first.

5. Prefer explicit, readable code over clever one-liners or heavy
   abstraction. Optimize for a human reading this code for the first
   time, not for line count.

6. When fixing a bug, explain what the root cause was before showing
   the fix — don't just patch and move on.

7. If you're uncertain about a design choice, say so explicitly rather
   than presenting a guess with full confidence.