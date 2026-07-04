# Frontend Technical Design --- RAG-Powered Developer Portfolio

**Version:** 1.0
**Status:** Technical Design (Pre-Implementation)
**Depends on:** Frontend UX Proposal v3.0 (approved) · PRD v2.1

---

# Purpose

Translate the approved UX Proposal into an implementable frontend architecture: component tree, folder structure, state management, API integration, SSE streaming, error handling, and caching. This document is the contract between design intent and code.

---

# 1. Technology Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | Next.js 14 (App Router) | File-based routing matches the IA (`/`, `/projects`, `/architecture`, `/resume`, `/stack`, `/hire`); RSC for static, no-API sections (Tech Stack shell, Hero copy) |
| Language | TypeScript (strict mode) | Response/citation payloads are structured; typed contracts prevent silent shape drift between backend and UI |
| Styling | Tailwind CSS | Matches UX Proposal's utility-first, fast-iteration requirement |
| Components | shadcn/ui | Accessible primitives (Radix under the hood) satisfy the Accessibility-first principle without hand-rolling focus management |
| Server-state | TanStack Query | Caching, retry, and loading states for `/stack`, `/resume`, `/hire` requests |
| Client/UI-state | Zustand | Lightweight global store for chat transcript, streaming status, citation panel open/closed, offline-mode flag — no boilerplate, no Context re-render storms |
| Markdown rendering | react-markdown + remark-gfm | Renders LLM responses (tables, code blocks, lists) safely |
| PDF | react-pdf | Embedded resume viewer |
| Motion | Framer Motion (minimal) | Per UX Proposal: used sparingly, respects `prefers-reduced-motion` |
| Icons | lucide-react | Pairs natively with shadcn/ui |

---

# 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Next.js App Router                     │
│                                                               │
│  Static/RSC segments          Client-interactive segments    │
│  ─────────────────────        ────────────────────────────  │
│  Hero copy, Summary strip     AI Chat (SSE)                  │
│  Footer, About card           Citation sidebar                │
│  Architecture page shell      Hire form                       │
│  Tech Stack (SSR + cached)    Terminal mode toggle            │
│                                                                │
└──────────────────────────┬────────────────────────────────────┘
                           │
              ┌────────────▼─────────────┐
              │   API Client Layer        │
              │   (lib/api/*)             │
              │   - fetch wrapper         │
              │   - SSE stream reader     │
              │   - typed request/response│
              └────────────┬─────────────┘
                           │ HTTPS
              ┌────────────▼─────────────┐
              │   FastAPI Backend         │
              │   /chat  /hire  /stack    │
              │   /resume  /admin/*       │
              └───────────────────────────┘
```

**Rendering strategy:**
- Above-the-fold Summary, Hero, Footer, and the "About This Portfolio" card are static/RSC — no API dependency, matches UX Proposal's "no layout shift, fast perceived performance" goal.
- `/stack` data is fetched server-side at build/request time and cached (see §7); the Tech Stack page is not a client-side waterfall.
- `/resume` is a client component wrapping `react-pdf` (binary payload, needs a browser runtime).
- The AI Chat is fully client-side — it owns a persistent EventSource-like connection and needs component-level state that outlives navigation-free interactions.

---

# 3. Folder Structure

```
frontend/
├── app/
│   ├── layout.tsx                    # Root layout: fonts, ThemeProvider, QueryProvider
│   ├── page.tsx                      # Home: Hero + Summary + Chat + Featured Project
│   ├── globals.css
│   │
│   ├── projects/
│   │   ├── page.tsx                  # Project list (expandable cards)
│   │   └── [slug]/page.tsx           # Optional deep-link per project
│   │
│   ├── architecture/
│   │   └── page.tsx                  # System diagram, pipelines, deployment
│   │
│   ├── resume/
│   │   └── page.tsx                  # Embedded PDF viewer
│   │
│   ├── stack/
│   │   └── page.tsx                  # Grouped tech stack (RSC + cached fetch)
│   │
│   ├── hire/
│   │   └── page.tsx                  # Availability + contact + form
│   │
│   └── admin/                        # Not linked from public nav
│       └── analytics/page.tsx        # Bearer-token gated, client-side auth check
│
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── OfflineBanner.tsx
│   │
│   ├── hero/
│   │   ├── HeroSection.tsx
│   │   └── SummaryStrip.tsx          # Identity + Highlight Cards
│   │
│   ├── chat/
│   │   ├── ChatContainer.tsx         # Orchestrates message list + input + citations
│   │   ├── MessageList.tsx
│   │   ├── MessageBubble.tsx         # Renders markdown, handles streaming cursor
│   │   ├── SuggestedPrompts.tsx
│   │   ├── ChatInput.tsx
│   │   ├── StreamingIndicator.tsx    # "Searching portfolio..." → "Generating..."
│   │   ├── CitationSidebar.tsx       # Desktop: persistent right panel
│   │   ├── CitationCard.tsx          # Mobile: inline expandable card
│   │   └── RetryButton.tsx
│   │
│   ├── projects/
│   │   ├── ProjectCard.tsx
│   │   ├── ProjectExpanded.tsx
│   │   └── FeaturedProject.tsx
│   │
│   ├── architecture/
│   │   ├── SystemDiagram.tsx
│   │   ├── PipelineSection.tsx
│   │   └── DeploymentSection.tsx
│   │
│   ├── stack/
│   │   └── StackCategoryGroup.tsx
│   │
│   ├── hire/
│   │   ├── AvailabilityCard.tsx
│   │   └── HireForm.tsx
│   │
│   ├── terminal/
│   │   └── TerminalMode.tsx          # Code-split, lazy-loaded
│   │
│   └── ui/                           # shadcn/ui generated primitives
│       ├── button.tsx
│       ├── card.tsx
│       ├── sheet.tsx                 # Mobile citation drawer
│       ├── dialog.tsx
│       └── ...
│
├── lib/
│   ├── api/
│   │   ├── client.ts                 # fetch wrapper: base URL, headers, error normalization
│   │   ├── chat.ts                   # streamChat() — SSE reader
│   │   ├── hire.ts                   # postHire()
│   │   ├── stack.ts                  # getStack()
│   │   ├── resume.ts                 # getResumeUrl()
│   │   └── analytics.ts              # getAnalytics() (admin, bearer token)
│   │
│   ├── stores/
│   │   ├── chatStore.ts              # Zustand: messages, streamingState, sessionId
│   │   └── uiStore.ts                # Zustand: citationPanelOpen, offlineMode, terminalMode
│   │
│   ├── hooks/
│   │   ├── useChatStream.ts          # Wraps chatStore + streamChat()
│   │   ├── useStack.ts               # TanStack Query wrapper
│   │   ├── useHire.ts                # TanStack Query mutation
│   │   └── useOnlineStatus.ts        # navigator.onLine + failed-request detection
│   │
│   ├── types/
│   │   ├── chat.ts                   # ChatMessage, Citation, SSEEvent
│   │   ├── stack.ts
│   │   └── hire.ts
│   │
│   └── utils/
│       ├── sanitize.ts               # Client-side input trimming/length caps (defense in depth)
│       └── formatters.ts
│
├── providers/
│   ├── QueryProvider.tsx             # TanStack Query client + devtools
│   └── ThemeProvider.tsx
│
├── public/
│   └── resume.pdf                    # Fallback static asset if /resume API fails
│
├── middleware.ts                     # Optional: admin route gating
├── next.config.js
├── tailwind.config.ts
└── package.json
```

---

# 4. Component Tree

```
RootLayout
├── ThemeProvider
├── QueryProvider
├── Header
├── OfflineBanner (conditional, driven by uiStore.offlineMode)
│
├── / (Home)
│   ├── HeroSection
│   ├── SummaryStrip
│   │   └── HighlightCard × 3 (Current Focus, Flagship Project, Core Technologies)
│   ├── ChatContainer
│   │   ├── SuggestedPrompts
│   │   ├── MessageList
│   │   │   └── MessageBubble × N
│   │   │       ├── StreamingIndicator (while streaming)
│   │   │       ├── ReactMarkdown (rendered content)
│   │   │       ├── CitationCard[] (mobile, inline)
│   │   │       └── RetryButton (on error)
│   │   ├── CitationSidebar (desktop only, persistent)
│   │   └── ChatInput
│   └── FeaturedProject
│
├── /projects
│   └── ProjectCard[] → expands to ProjectExpanded
│
├── /architecture
│   ├── SystemDiagram
│   ├── PipelineSection (ingestion, retrieval, caching)
│   └── DeploymentSection
│
├── /resume
│   └── PDFViewer (react-pdf, dynamically imported)
│
├── /stack
│   └── StackCategoryGroup[] (Languages, Backend, Frontend, DB, Cloud, DevOps, AI/ML, Tools)
│
├── /hire
│   ├── AvailabilityCard
│   └── HireForm
│
├── TerminalMode (lazy-loaded, mounted via toggle/shortcut, overlays chat)
│
└── Footer
```

**Composition notes:**
- `ChatContainer` is the only component that touches `chatStore` directly; children receive data via props so `MessageBubble` and `CitationCard` stay presentational and easy to snapshot-test.
- `CitationSidebar` and `CitationCard` render from the same `Citation[]` shape — one component tree, two layouts, switched by a `useMediaQuery('(min-width: 1024px)')` hook rather than duplicated logic.
- `TerminalMode` is dynamically imported (`next/dynamic`, `ssr: false`) since it's an optional showcase surface, not part of the MVP critical path — keeps it out of the main bundle.

---

# 5. State Management

Two deliberately separate stores, matching the UX Proposal's split between "AI Chat" (stateful, streaming) and everything else (static or simple server-state):

### 5.1 Server state — TanStack Query
Used for anything backed by a cacheable GET or a simple mutation:

| Query/Mutation | Endpoint | Notes |
|---|---|---|
| `useStack()` | `GET /stack` | `staleTime: Infinity` — tech stack changes rarely, manual invalidation on deploy |
| `useResumeUrl()` | `GET /resume` | `staleTime: Infinity`, falls back to `/public/resume.pdf` on error |
| `useHire()` | `POST /hire` | Mutation, optimistic UI (button → "Sending..." → "Sent") |
| `useAnalytics()` | `GET /admin/analytics` | Admin only, `enabled: hasAdminToken` |

Why not Zustand for these: they're server-owned, cacheable, and benefit from TanStack Query's built-in retry/backoff and devtools — reimplementing that in a store is wasted effort.

### 5.2 Client/UI state — Zustand

**`chatStore.ts`**
```typescript
interface ChatState {
  sessionId: string;
  messages: ChatMessage[];
  streamingMessageId: string | null;
  streamingPhase: 'idle' | 'searching' | 'finding' | 'generating' | 'streaming';
  error: { messageId: string; retryable: boolean } | null;

  sendMessage: (content: string) => Promise<void>;
  retryMessage: (messageId: string) => Promise<void>;
  cancelStream: () => void;
}
```
- `sessionId` is generated client-side on first mount (`crypto.randomUUID()`) and held in memory + `sessionStorage` (not `localStorage` — session-scoped, matches backend's 30-minute session TTL).
- SSE streaming is *not* modeled as a TanStack Query mutation because it's a long-lived, multi-event stream, not a single request/response — Zustand + a dedicated `streamChat()` function (see §6) is a better fit.

**`uiStore.ts`**
```typescript
interface UIState {
  citationPanelOpen: boolean;      // desktop sidebar toggle
  offlineMode: boolean;            // set by useOnlineStatus + failed /chat probe
  terminalModeActive: boolean;
  reducedMotion: boolean;          // mirrors prefers-reduced-motion, overridable in-app
}
```

State is intentionally partitioned so that a chat re-render (new token arriving) never triggers a re-render of `Header`, `Footer`, or `SummaryStrip` — those only subscribe to `uiStore`.

---

# 6. API Integration & SSE Streaming

### 6.1 API client layer
`lib/api/client.ts` centralizes:
- Base URL from `NEXT_PUBLIC_API_URL`
- Consistent error shape: `{ status, message, retryable }`
- Timeout handling via `AbortController` (10s default for non-streaming calls)

### 6.2 `streamChat()` implementation

The backend streams SSE frames (`data: {...}\n\n`). Since `EventSource` doesn't support `POST` bodies, streaming is implemented with `fetch()` + a manual `ReadableStream` reader rather than the native `EventSource` API:

```typescript
// lib/api/chat.ts
export async function streamChat(
  message: string,
  sessionId: string,
  handlers: {
    onPhaseChange: (phase: StreamingPhase) => void;
    onToken: (token: string) => void;
    onCitations: (citations: Citation[]) => void;
    onDone: () => void;
    onError: (err: ChatStreamError) => void;
  },
  signal: AbortSignal
) {
  handlers.onPhaseChange('searching');

  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!res.ok || !res.body) {
    handlers.onError({ status: res.status, retryable: res.status >= 500 });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let firstTokenReceived = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split('\n\n');
    buffer = frames.pop() ?? ''; // keep incomplete frame for next chunk

    for (const frame of frames) {
      const line = frame.replace(/^data:\s*/, '').trim();
      if (!line) continue;

      if (line === '[DONE]') {
        handlers.onDone();
        return;
      }

      const parsed = JSON.parse(line);

      if (parsed.token) {
        if (!firstTokenReceived) {
          handlers.onPhaseChange('streaming');
          firstTokenReceived = true;
        }
        handlers.onToken(parsed.token);
      }

      if (parsed.citations) {
        handlers.onCitations(parsed.citations);
      }
    }
  }
}
```

**Phase transitions** map directly onto the UX Proposal's streaming UX spec:
`idle → searching ("Searching portfolio...") → finding ("Finding relevant documents...") → streaming (first token replaces loading state instantly, no layout shift)`

The `searching`/`finding` phases are optimistic client-side labels shown while awaiting the first byte — the backend doesn't emit separate events for them (per the SSE schema in the PRD, only `token`, `citations`, and `[DONE]` are sent). This is a deliberate UX-layer simplification: the client owns the perceived-progress narrative, the server just streams tokens.

### 6.3 Cancellation
`ChatContainer` holds an `AbortController` per in-flight request. Navigating away, sending a new message, or an explicit "Stop generating" action calls `.abort()`, which the `fetch` call surfaces as an `AbortError` — handled distinctly from network errors (no retry UI shown for user-initiated cancellation).

### 6.4 Cached responses
Per the UX Proposal: *"Cached responses should render immediately without showing the thinking animation."* The backend can't signal "this is a cache hit" mid-stream without a protocol change, so the client approximates this: if the full response (all tokens + `[DONE]`) arrives within a single `read()` cycle (effectively <50ms from request start), `onPhaseChange` is skipped entirely and the message renders as already-complete. This is a heuristic, not a guarantee — flagged as a candidate for a future explicit `cache_hit: true` field in the SSE payload.

### 6.5 Other endpoints (non-streaming)

| Function | Method | Notes |
|---|---|---|
| `postHire()` | `POST /hire` | TanStack mutation, surfaces `status: "sent"` |
| `getStack()` | `GET /stack` | Simple JSON fetch, RSC-compatible |
| `getResumeUrl()` | `GET /resume` | Returns a URL, not the binary — `react-pdf` fetches it directly |
| `getAnalytics()` | `GET /admin/analytics` | Requires `Authorization: Bearer <token>`, admin-only route |

---

# 7. Caching Strategy

| Layer | What | Mechanism | TTL/Invalidation |
|---|---|---|---|
| Server (backend, out of scope here) | LLM responses | Redis | 24h, flushed on `/ingest` |
| TanStack Query | `/stack`, `/resume` | In-memory query cache | `staleTime: Infinity`; manual `queryClient.invalidateQueries()` on deploy if needed |
| Next.js RSC fetch cache | `/stack` (server-rendered) | `fetch(..., { next: { revalidate: 3600 } })` | 1 hour, since stack data is near-static |
| Client memory | Chat transcript | Zustand store | Cleared on tab close (not persisted — matches PRD's "no persistent user identity" non-goal) |
| Browser | `sessionId` | `sessionStorage` | Cleared on tab close, aligns with backend's 30-min session TTL |

No `localStorage` is used for chat state — conversation history persistence is explicitly deferred (MVP Scope → Deferred: "Conversation history"), so there's nothing to persist beyond the current tab session.

---

# 8. Error Boundaries & Offline Mode

### 8.1 Boundary placement
- **Root-level `error.tsx`**: catches unrecoverable render errors, shows a minimal "Something went wrong" state with a reload action — never blocks the whole app for a chat-only failure.
- **Segment-level boundaries** around `ChatContainer` specifically: a chat-rendering error (e.g., malformed markdown) degrades to a plain-text fallback for that message rather than crashing the page. This directly serves the UX Proposal's "Graceful degradation" principle — a broken chat message must never take down Projects, Resume, or Hire.
- Static sections (Hero, Summary, Featured Project, Footer) are RSC/no-API by design, so they have no error boundary dependency on backend health at all — this is the primary defense specified in the UX Proposal's Offline Mode section.

### 8.2 Offline Mode detection
`useOnlineStatus()` combines two signals:
1. `navigator.onLine` / `online`/`offline` browser events (network-level).
2. A failed `/chat` request classified as connectivity-related (`fetch` throws `TypeError`, or repeated 5xx) — because a user can be "online" per the browser while the backend itself is down.

Either signal sets `uiStore.offlineMode = true`, which:
- Renders `OfflineBanner` with the copy specified in the UX Proposal ("AI assistant is temporarily unavailable" / "Static portfolio loaded successfully").
- Disables `ChatInput` (with a tooltip explaining why) rather than letting users send messages into a void.
- Leaves Projects, Resume, Stack, Hire, and Architecture fully interactive, since none of them depend on the same backend liveness in the MVP (Resume/Stack are cached after first successful load; Hire submission will itself surface its own error state if attempted while offline).

### 8.3 Retry UX
Each failed message gets a `RetryButton` that re-invokes `retryMessage(messageId)` — re-sends the original user query with a fresh `AbortController`, without duplicating it in the transcript.

---

# 9. Accessibility Implementation Notes

Concrete implementation of the UX Proposal's accessibility principles:

| Requirement | Implementation |
|---|---|
| Keyboard navigation | shadcn/ui (Radix) primitives handle roving focus/tab order out of the box for `Sheet` (mobile citation drawer), `Dialog`, `Button` |
| Screen reader labels | `aria-live="polite"` region wrapping the streaming message so new tokens are announced without spamming; `aria-label` on icon-only buttons (retry, citation expand) |
| High contrast | Color tokens (see Visual Design System) meet WCAG AA at minimum; verified against both light/dark themes |
| Visible focus rings | Tailwind `focus-visible:ring-2` applied globally via base layer, never `outline-none` without a replacement |
| Reduced motion | `uiStore.reducedMotion` mirrors `prefers-reduced-motion: reduce`; Framer Motion variants check this flag and fall back to instant transitions |
| Touch targets | Mobile citation cards and suggested-prompt chips enforce `min-h-[44px]` per the UX Proposal's Apple HIG reference |

---

# 10. Performance Considerations

- **Code splitting**: `TerminalMode` and `react-pdf` (Resume page) are dynamically imported (`next/dynamic`) — neither is needed for the critical recruiter path (Hero → Chat → Featured Project).
- **Streaming-first perceived performance**: first token target <1s per PRD success metrics; the client's phase-label heuristic (§6.2) covers the gap before that.
- **No layout shift on stream start**: `MessageBubble` reserves its container before the first token arrives (skeleton height matches loading-indicator height) so the swap from "Generating response..." to live text doesn't reflow the page.
- **Citation sidebar**: virtualized only if a single response can plausibly return >20 citations (unlikely given top-3 context assembly per PRD §4.3) — not implemented in MVP, noted as a v2 consideration if context size grows.
- **Static-first home page**: Hero/Summary/Featured Project ship as RSC HTML with zero client JS required to be useful — chat hydration happens after, non-blocking.

---

# 11. Environment Configuration

```
NEXT_PUBLIC_API_URL=          # FastAPI base URL
NEXT_PUBLIC_ADMIN_ENABLED=    # feature-flag the /admin route in prod builds
```

Admin routes (`/admin/analytics`) are excluded from the public sitemap and gated behind a client-side token prompt — full server-side auth is a backend concern (bearer token, per PRD §6), the frontend's job is just to not expose the route in navigation and to fail closed if no token is present.

---

# 12. Build & Deployment

Matches the PRD's infrastructure (§8): the frontend is one service in the Docker Compose stack locally, and one of the Azure Container Apps in production.

```dockerfile
# frontend/Dockerfile (multi-stage)
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

Deployed via the same GitHub Actions → Azure Container Apps pipeline described in PRD §5 Block 5, as a sibling container to the FastAPI backend behind the shared NGINX/Container Apps ingress.

---

# 13. Open Questions / Deviations Log

| Item | Status | Note |
|---|---|---|
| Explicit `cache_hit` flag in SSE payload | Proposed, not in current PRD API spec | Would replace the client-side latency heuristic in §6.4 with a guarantee |
| Conversation history persistence | Deferred (MVP Scope) | No storage layer built for it; `chatStore` is intentionally ephemeral |
| Admin auth flow (token entry UI) | Out of scope for MVP frontend | `/admin/analytics` is a bearer-token API; frontend token entry is a placeholder gate, not a full auth system |
