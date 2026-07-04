# Frontend Visual Design System --- RAG-Powered Developer Portfolio

**Version:** 1.0
**Status:** Design System (Pre-Implementation)
**Depends on:** Frontend UX Proposal v3.0 (approved) · Frontend Technical Design v1.0

---

# Purpose

Define the concrete visual language — color, type, spacing, iconography, motion, and component mapping — that implements the UX Proposal's Visual Design principles:

> Prioritize clarity, familiarity, fast information retrieval. Avoid hacker aesthetics, neon terminal themes, heavy animations.

This system supports a **recruiter-first, engineer-approved** aesthetic: calm and legible by default, with technical depth (Terminal Mode, Architecture diagrams) available but never forced on the primary path.

---

# 1. Design Tokens Overview

All tokens are implemented as CSS variables (Tailwind `theme.extend` + `:root` / `.dark` overrides) so shadcn/ui components inherit them automatically without per-component overrides.

---

# 2. Color System

### 2.1 Palette philosophy
Neutral-first UI with a single accent color reserved for interactive/AI-generated elements — this keeps the interface calm (per "avoid neon terminal themes") while still visually distinguishing "this came from the AI" (chat bubbles, citation highlights, streaming cursor) from static portfolio content.

### 2.2 Core palette

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--background` | `#FFFFFF` | `#0B0E14` | Page background |
| `--foreground` | `#0F1115` | `#E6E8EB` | Primary text |
| `--muted` | `#F4F5F7` | `#161A22` | Card backgrounds, subtle panels |
| `--muted-foreground` | `#5B6270` | `#9AA1AC` | Secondary text, captions |
| `--border` | `#E4E6EA` | `#242933` | Dividers, card borders |
| `--accent` | `#3B6BE5` | `#5C8AFF` | Primary interactive color — buttons, links, active states |
| `--accent-foreground` | `#FFFFFF` | `#0B0E14` | Text/icons on accent-filled surfaces |

### 2.3 Semantic colors

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--ai-surface` | `#EEF2FE` | `#141A2E` | AI/assistant message bubble background — visually distinct from user messages |
| `--user-surface` | `#F4F5F7` | `#1B1F27` | User message bubble background |
| `--citation-accent` | `#7C5CFF` | `#9B85FF` | Citation chips, source-file badges — deliberately distinct hue from `--accent` so citations read as "grounding metadata," not another button |
| `--success` | `#1F9D55` | `#3ECF7A` | `/hire` confirmation, "sent" states |
| `--warning` | `#B45309` | `#F0A93D` | Offline banner, degraded-mode notices |
| `--error` | `#D92D20` | `#F87171` | Failed message, retry state |
| `--focus-ring` | `#3B6BE5` | `#5C8AFF` | Matches `--accent`, 2px, always visible on `:focus-visible` |

### 2.4 Contrast requirements
All text/background pairs above meet **WCAG AA (4.5:1)** at minimum for body text; `--muted-foreground` on `--background` meets AA for large text (≥18px) use cases like captions and citation metadata. Verified for both themes independently — dark mode is not simply an inverted light mode.

### 2.5 What's deliberately absent
No neon greens, no scanline/CRT textures, no monospace-green-on-black default theme. Those cues are reserved exclusively for **Terminal Mode** (§7.4), which is opt-in and clearly framed as an engineering showcase, not the default experience.

---

# 3. Typography

### 3.1 Type families

| Role | Family | Fallback stack |
|---|---|---|
| UI / body | `Inter` | `system-ui, -apple-system, sans-serif` |
| Headings | `Inter` (same family, heavier weights) | — |
| Code / Terminal Mode / citation file paths | `JetBrains Mono` | `ui-monospace, 'SF Mono', monospace` |

Using one primary family (Inter) for both body and headings keeps the "familiar interactions over novelty" principle intact — no display font competing for attention. Monospace is reserved for genuinely code-like content (file paths, Terminal Mode, code block rendering in chat responses), so its appearance always signals "this is technical/literal."

### 3.2 Type scale

| Token | Size / Line-height | Weight | Usage |
|---|---|---|---|
| `text-display` | 40px / 48px | 700 | Hero name |
| `text-h1` | 32px / 40px | 700 | Page titles (Projects, Architecture, Resume, Stack, Hire) |
| `text-h2` | 24px / 32px | 600 | Section headers within a page |
| `text-h3` | 20px / 28px | 600 | Card titles, citation sidebar header |
| `text-body-lg` | 17px / 26px | 400 | Hero tagline, chat message text |
| `text-body` | 15px / 24px | 400 | Default body copy |
| `text-sm` | 14px / 20px | 400 | Captions, metadata, tech badges — matches the UX Proposal's mobile 14px minimum |
| `text-xs` | 12px / 16px | 500 | Timestamps, citation layer tags (`identity` / `design` / `artifact`) |

Minimum body size never drops below 14px at any breakpoint, per the UX Proposal's Accessibility and Mobile requirements.

### 3.3 Markdown rendering in chat
LLM responses render through `react-markdown`. Mapped explicitly so streamed content never breaks the type scale:
- `h1`–`h3` in responses → clamp to `text-h3` max (a response should never out-size the page's own headings)
- Inline `code` → `text-sm`, `JetBrains Mono`, `--muted` background pill
- Code blocks → `text-sm`, `JetBrains Mono`, `--muted` background, horizontal scroll (never wrap-break identifiers)
- Lists/tables → inherit `text-body`

---

# 4. Spacing & Layout Grid

### 4.1 Base unit
4px base unit, Tailwind default scale (`1 = 4px`) used throughout — no custom spacing scale needed, which keeps implementation friction low.

| Token | Value | Common usage |
|---|---|---|
| `space-1` | 4px | Icon-to-label gaps |
| `space-2` | 8px | Chip/badge internal padding |
| `space-3` | 12px | Compact card padding |
| `space-4` | 16px | Default card padding, form field gaps |
| `space-6` | 24px | Section internal spacing |
| `space-8` | 32px | Between major page sections |
| `space-12` | 48px | Hero vertical padding (mobile) |
| `space-16` | 64px | Hero vertical padding (desktop) |

### 4.2 Content width
- Max content width: `1120px`, centered, with `24px` gutters on mobile / `48px` on desktop.
- Chat column max width: `720px` — kept narrower than full content width for readability, matching standard chat-UI conventions.
- Citation sidebar (desktop): fixed `320px`, docked right, independent scroll from the message list.

### 4.3 Grid
- Highlight Cards (Summary Strip): 3-column grid on desktop (`≥1024px`), stacks to 1-column below `768px`.
- Tech Stack categories: responsive grid, `auto-fit, minmax(220px, 1fr)`.
- Project cards: 2-column on desktop, 1-column on mobile.

### Hero Constraints

Maximum width:
720px

Primary CTA:
Start Chat

Secondary CTAs:
Resume
Hire Me
GitHub

The hero should remain fully visible without scrolling on laptops around 1366×768 resolution.

---

# 5. Breakpoints

| Token | Width | Notes |
|---|---|---|
| `sm` | 375px | Minimum supported viewport (PRD success metric: "fully functional on 375px") |
| `md` | 768px | Terminal chrome → clean chat UI switch point (per PRD Challenge 8); Summary cards go 1-col → 3-col |
| `lg` | 1024px | Citation sidebar becomes visible/persistent; Highlight Cards go full 3-column |
| `xl` | 1280px | Max-width content container engages, extra whitespace beyond this |

Mobile-first implementation: base styles target `sm`, each breakpoint adds complexity upward — matches the UX Proposal's "Mobile-first responsiveness" principle directly.

---

# 6. Iconography

- **Library**: `lucide-react` exclusively — consistent stroke width (1.5px–2px) and geometry across the whole app, pairs natively with shadcn/ui.
- **Sizing**: `16px` inline with text-sm/text-body, `20px` for standalone buttons, `24px` for section/feature icons (e.g., cloud/DevOps/AI category icons on the Tech Stack page).
- **Color**: icons inherit `currentColor` — never hard-coded, so they adapt correctly across light/dark and semantic states (error icon uses `--error`, etc.).
- **No custom icon set**: avoids the maintenance and consistency risk of mixing icon styles; lucide's catalog covers everything needed (cloud, terminal, git-branch, database, cpu, send, download, github, linkedin, mail).

---

# 7. Motion

Per the UX Proposal: Framer Motion used **minimally**. Motion exists to reduce perceived latency and confirm state changes — never as decoration.

### 7.1 Motion tokens

| Token | Duration | Easing | Usage |
|---|---|---|---|
| `motion-instant` | 0ms | — | Streaming token append (no animation — text should feel live, not tweened) |
| `motion-fast` | 120ms | `ease-out` | Button press states, hover feedback |
| `motion-base` | 200ms | `ease-in-out` | Card expand/collapse (Projects), citation card expand |
| `motion-slow` | 320ms | `ease-in-out` | Mobile citation drawer (Sheet) slide-in, streaming-phase label crossfade |

### 7.2 What gets animated
- Streaming phase label crossfade (`Searching... → Finding... → [replaced by first token]`)
- Project card expand/collapse
- Mobile citation drawer slide-up
- Suggested-prompt chip hover/press
- Offline banner slide-down entrance

### 7.3 What does NOT get animated
- Token-by-token text append — instant, no per-character animation, to avoid the "typewriter jank" the PRD explicitly flags as a mobile risk (Challenge 8). This is a deliberate deviation from a literal typewriter effect toward a plain, fast-appending stream.
- Page transitions — standard Next.js navigation, no custom route-transition choreography (keeps "familiar interactions over novelty").
- Hero section — static on load, no entrance animation, so the recruiter's first 30 seconds aren't spent watching things fly in.

### 7.4 Reduced motion
`prefers-reduced-motion: reduce` (or the in-app override in `uiStore`) collapses every `motion-*` token to `0ms` with no transform — components simply appear/disappear in their final state.

---

# 8. shadcn/ui Component Mapping

| UX Proposal feature | shadcn/ui component(s) | Notes |
|---|---|---|
| Hero CTA buttons | `Button` (variants: `default`, `outline`) | `default` for Start Chat/Hire Me, `outline` for Resume/GitHub |
| Highlight Cards | `Card` | `CardHeader` + `CardContent`, no shadow — flat with `--border` |
| Chat message bubbles | `Card` (custom radius) | Distinguished by `--ai-surface` / `--user-surface` background, not shadcn variant |
| Suggested prompts | `Badge` (as clickable chip) | `min-h-[44px]` override applied for mobile tap targets |
| Citation sidebar (desktop) | Custom panel (not a shadcn primitive) | Persistent, non-modal — a `Sheet` would be wrong here since it's meant to co-exist with the chat, not overlay it |
| Citation card (mobile) | `Collapsible` | Expandable inline beneath each response, matches UX Proposal's "inline expandable card" spec |
| Project expand | `Accordion` or `Collapsible` | `Accordion` if only one project should be open at a time; `Collapsible` if multiple can be open — **decision needed, defaulting to independent `Collapsible` per card** so recruiters can compare two projects side-open |
| Resume viewer frame | `Card` wrapping `react-pdf` canvas | Download/Print as `Button` group above the viewer |
| Hire form | `Form` (react-hook-form + zod resolver, shadcn `Form` wrapper) + `Input`, `Textarea`, `Button` | Validates email/company before `POST /hire` |
| Offline banner | `Alert` (`variant: warning`, custom `--warning` token) | Slides down from under `Header` |
| Admin token gate | `Dialog` + `Input` | Simple bearer-token entry, not a full auth UI |
| Terminal Mode toggle | `Switch` or hidden keyboard shortcut | Lives in `Footer`, low visual weight per "not the default" |
| Focus rings | Radix `:focus-visible` default, styled via `--focus-ring` | No custom focus-trap logic needed — Radix primitives handle it |

---

# 9. Wireframes

Low-fidelity structural wireframes — box-and-label level, sufficient to hand to implementation without prescribing exact pixel layout (which the Technical Design's component tree already scaffolds).

### 9.1 Home — Desktop (≥1024px)

### Suggested Prompt Layout

Desktop

Suggested prompt chips wrap naturally into multiple rows.

Mobile

Suggested prompt chips scroll horizontally.

Maximum visible prompt chips:
6

Additional prompts are accessible through a **More** button rather than
increasing the height of the chat area.

Prompt chips should represent recruiter-focused questions such as:

- Tell me about yourself
- Explain your flagship project
- What technologies do you use?
- Show your resume
- Are you currently available?
- Explain your architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ Header:  [Logo/Name]                    [Projects][Arch][Resume]  │
│                                          [Stack][Hire]             │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│   HERO                                                            │
│   Ajay Susanth                                                    │
│   Backend Engineer · AI Applications · Cloud · DevOps             │
│   [Short professional summary paragraph]                          │
│   [Start Chat] [Resume] [Hire Me] [GitHub]                        │
│                                                                    │
├──────────────────────────────────────────────────────────────────┤
│   SUMMARY STRIP                                                   │
│   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐       │
│   │ Current Focus  │ │ Flagship Proj. │ │ Core Tech      │       │
│   └────────────────┘ └────────────────┘ └────────────────┘       │
├──────────────────────────────────────────────────────────────────┤
│   AI CHAT                                                          │
│   ┌──────────────────────────────────┐  ┌──────────────────────┐ │
│   │ [chip][chip][chip][chip]          │  │  CITATIONS            │ │
│   │                                    │  │  ┌──────────────────┐│ │
│   │  ┌──────────────────────────┐      │  │  │ auth.middleware..││ │
│   │  │ user msg                 │      │  │  │ artifact · resv. ││ │
│   │  └──────────────────────────┘      │  │  └──────────────────┘│ │
│   │       ┌──────────────────────────┐ │  │  ┌──────────────────┐│ │
│   │       │ AI response (markdown)   │ │  │  │ decisions.md      ││ │
│   │       │ [Searching portfolio...] │ │  │  │ design · resv.    ││ │
│   │       └──────────────────────────┘ │  │  └──────────────────┘│ │
│   │                                    │  │                       │ │
│   │  [Type your question...    ][Send]│  └──────────────────────┘ │
│   └──────────────────────────────────┘                            │
├──────────────────────────────────────────────────────────────────┤
│   FEATURED PROJECT                                                 │
│   [Screenshot]  n8n Workflow Automation Platform on AKS            │
│                 [Terraform][Helm][ArgoCD][KEDA]   [Learn More →]  │
├──────────────────────────────────────────────────────────────────┤
│   FOOTER: GitHub · LinkedIn · Email · Resume · Status · Built With│
└──────────────────────────────────────────────────────────────────┘
```

### 9.2 Home — Mobile (375px–767px)

```
┌───────────────────────┐
│ Header  [☰]            │
├───────────────────────┤
│ HERO                   │
│ Ajay Susanth            │
│ Backend · AI · Cloud    │
│ [summary]                │
│ [Start Chat]              │
│ [Resume] [Hire] [GitHub] │
├───────────────────────┤
│ SUMMARY STRIP (stacked) │
│ ┌───────────────────┐  │
│ │ Current Focus     │  │
│ └───────────────────┘  │
│ ┌───────────────────┐  │
│ │ Flagship Project   │  │
│ └───────────────────┘  │
│ ┌───────────────────┐  │
│ │ Core Technologies  │  │
│ └───────────────────┘  │
├───────────────────────┤
│ AI CHAT                 │
│ [chip][chip][chip]  →   │  (horiz. scroll)
│                          │
│ ┌─────────────────────┐│
│ │ user msg             ││
│ └─────────────────────┘│
│      ┌─────────────────┐│
│      │ AI response      ││
│      │ ▸ Sources (2)     ││  ← Collapsible, min-h 44px
│      └─────────────────┘│
│                          │
│ [Ask a question...][➤] │
├───────────────────────┤
│ FEATURED PROJECT        │
│ [Screenshot]              │
│ n8n Platform on AKS       │
│ [Learn More →]            │
├───────────────────────┤
│ FOOTER (stacked)          │
└───────────────────────┘
```

### 9.3 Mobile citation drawer (expanded state)

```
┌───────────────────────┐
│ ┌─────────────────────┐│
│ │ AI response text...  ││
│ │                       ││
│ │ ▾ Sources (2)         ││
│ │ ┌───────────────────┐││
│ │ │ 📄 auth.middleware.ts││
│ │ │ artifact · reservation-system│
│ │ │ [preview snippet...]  ││
│ │ └───────────────────┘││
│ │ ┌───────────────────┐││
│ │ │ 📄 decisions.md      ││
│ │ │ design · reservation-system│
│ │ └───────────────────┘││
│ └─────────────────────┘│
└───────────────────────┘
```

### 9.4 Architecture Page (Desktop)

```
┌──────────────────────────────────────────────────────────────────┐
│ Header                                                             │
├──────────────────────────────────────────────────────────────────┤
│  Architecture                                                      │
│                                                                     │
│  [ System Diagram — full-width box/arrow illustration ]            │
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐                │
│  │ Retrieval Pipeline    │  │ Ingestion Pipeline   │                │
│  │ [stage list/diagram]  │  │ [stage list/diagram] │                │
│  └─────────────────────┘  └─────────────────────┘                │
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────┐                │
│  │ Caching Strategy      │  │ API Overview          │                │
│  └─────────────────────┘  └─────────────────────┘                │
│                                                                     │
│  [ Deployment Architecture — full-width diagram ]                  │
├──────────────────────────────────────────────────────────────────┤
│ Footer                                                             │
└──────────────────────────────────────────────────────────────────┘
```

### 9.5 Hire Page

```
┌──────────────────────────────────────────────────────────────────┐
│ Header                                                             │
├──────────────────────────────────────────────────────────────────┤
│  Hire Me                                                           │
│                                                                     │
│  ┌─────────────────────┐  ┌─────────────────────────────────────┐│
│  │ AVAILABILITY CARD     │  │ CONTACT FORM                        ││
│  │ Status: Open           │  │ [Email input]                       ││
│  │ Roles: Cloud, DevOps    │  │ [Company input]                     ││
│  │ Type: Full-time         │  │ [Message textarea]                  ││
│  │ Location: Remote/India  │  │ [Send →]                             ││
│  │ [Resume]                 │  └─────────────────────────────────────┘│
│  └─────────────────────┘                                          │
├──────────────────────────────────────────────────────────────────┤
│ Footer                                                             │
└──────────────────────────────────────────────────────────────────┘
```

---

# 10. Deviations & Decisions Log

| Item | Decision | Reason |
|---|---|---|
| Typewriter animation on streamed tokens | Rejected — instant append instead | PRD Challenge 8 explicitly flags typewriter jank as a mobile risk; motion tokens (§7.3) codify "no per-token animation" as a rule, not an oversight |
| Single accent color vs. multi-color brand palette | Single accent (`--accent`) + one distinct semantic hue for citations (`--citation-accent`) | Keeps the UI calm per "avoid neon terminal themes"; citations still need to visually register as "grounding data," not just more accent-colored UI |
| Project card expand pattern | Independent `Collapsible` per card (not `Accordion`) | Lets a recruiter compare two projects open side-by-side, which a single-open `Accordion` would prevent |

---

# Empty States

The interface should never display an empty page.

## Chat

Display:

> Ask me anything about my projects, architecture, or experience.

Provide suggested prompts immediately.

---

## Projects

Display:

> Projects are currently unavailable.

Provide a navigation action back to Home.

---

## Architecture

Display:

> Architecture documentation is currently unavailable.

Provide navigation back to Projects or Home.

---

## Resume

Display:

> Resume is temporarily unavailable.

Provide a retry button.

---

## Tech Stack

Display:

> Technology stack is temporarily unavailable.

Provide a retry button.

---

## Hire

Display:

> Hiring information is temporarily unavailable.

Provide a retry button.

---

## General Rule

Every empty state must:

- Explain what happened
- Tell the user what they can do next
- Never leave a blank screen

# Engineering Metrics Cards

Desktop:
4-column grid

Tablet:
2-column grid

Mobile:
2-column grid

Each card contains:

• Icon
• Primary Metric
• Label
• Optional caption

Example:

160+
Backend Tests

19
Backend Features

Hybrid
RAG Retrieval

Redis
Caching


# Project Badges

Projects should prominently display capability badges.

Examples:

Docker

Azure

Redis

CI/CD

Hybrid RAG

FastAPI

Next.js

Production Ready

Purpose:
Recruiters and engineers can quickly identify technologies without reading long descriptions.


