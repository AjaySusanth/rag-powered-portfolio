# Frontend UX Proposal --- RAG-Powered Developer Portfolio

**Version:** 3.0\
**Status:** Frontend UX Blueprint (Pre-Implementation)

------------------------------------------------------------------------

# Purpose

Design a recruiter-first frontend that showcases a production-grade
RAG-powered developer portfolio while remaining approachable for
non-technical users and insightful for engineers.

## Goals

### Primary

Allow a recruiter to understand: - Who Ajay Susanth is - What he
builds - What technologies he uses - Whether he is a good fit

...within **30--60 seconds**.

### Secondary

Allow engineers and interviewers to explore: - System architecture -
Backend engineering - AI pipeline - Cloud & DevOps decisions -
Source-grounded responses

------------------------------------------------------------------------

# Design Principles

1.  Recruiter-first
2.  AI enhances the portfolio---not replaces it
3.  Familiar interactions over novelty
4.  Fast perceived performance
5.  Progressive disclosure of technical depth
6.  Graceful degradation
7.  Accessibility-first
8.  Mobile-first responsiveness

------------------------------------------------------------------------

# Target Users

## Recruiters

Most visitors will skim rather than chat.

The landing experience must communicate value before any interaction.

Typical goals:

-   Download resume
-   Check availability
-   Understand experience
-   View projects

## Engineers / Interviewers

Want to inspect:

-   Architecture
-   Retrieval pipeline
-   Cloud infrastructure
-   DevOps
-   Design decisions

------------------------------------------------------------------------

# Information Architecture

-   Home (AI Chat)
-   Projects
-   Architecture
-   Resume
-   Tech Stack
-   Hire Me

------------------------------------------------------------------------

# Home Layout

    Header
    │
    ├── Hero Section
    │
    ├── Above-the-Fold Summary
    │
    ├── AI Chat
    │
    ├── Featured Project
    |
    |-- Engineering Highlights
    │
    └── Footer

------------------------------------------------------------------------

# Hero Section

Immediately visible.

Contains:

-   Name
-   Short tagline
-   Professional summary

Buttons:

-   Start Chat
-   Resume
-   Hire Me
-   GitHub

------------------------------------------------------------------------

# Above-the-Fold Summary

Static content.

No API dependency.

Includes:

### Identity

Backend Engineer • AI Applications • Cloud • DevOps

### Highlight Cards

-   Current Focus
-   Flagship Project
-   Core Technologies

Cards either navigate or pre-fill chat prompts.

------------------------------------------------------------------------

# AI Chat

Primary interactive experience.

Features:

-   Streaming responses
-   Suggested prompts
-   Markdown rendering
-   Source citations
-   Retry support

Suggested prompts should reflect recruiter intent:

-   Explain your backend architecture
-   Tell me about your flagship project
-   What cloud technologies have you used?
-   What is your DevOps experience?
-   Download your resume


# How This AI Works

Provide a small visual explanation of the AI pipeline.

Example:

Question
↓
Hybrid Retrieval
↓
Prompt Builder
↓
Gemini
↓
Grounded Answer
↓
Citations

Purpose:
Increase user trust by making the RAG pipeline transparent instead of presenting the AI as a black box.

------------------------------------------------------------------------

# Streaming UX

Immediately after send:

    Searching portfolio...

↓

    Finding relevant documents...

↓

    Generating response...

When first token arrives:

-   Replace loading state instantly
-   No layout shift

Cached responses should render immediately without showing the thinking
animation.

------------------------------------------------------------------------

# Citations

Desktop:

Persistent right sidebar.

Displays:

-   File name
-   Project
-   Layer
-   Expandable preview

Mobile:

Inline expandable card beneath each response.

Minimum 44px touch targets.

------------------------------------------------------------------------

# Featured Project

Visible on the homepage.

Shows:

-   Screenshot/illustration
-   Short summary
-   Technology badges
-   Learn More button

Purpose:

Recruiters should discover the strongest project even if they never
chat.

If multiple flagship projects exist in the future, this section may evolve into a carousel while still highlighting one primary project by default.

------------------------------------------------------------------------

# Engineering Highlights

Immediately below the Featured Project, display a compact engineering metrics section to communicate technical maturity at a glance.

Example metrics:

- 19 Backend Features
- Hybrid RAG Retrieval
- Redis Response Cache
- Redis Embedding Cache
- pgvector Semantic Search
- 160+ Automated Tests
- Dockerized Architecture
- Azure Deployment Ready

Purpose:
Recruiters often scan rather than read. These metrics provide immediate engineering credibility before interacting with the AI.

------------------------------------------------------------------------

# Projects

Expandable cards.

Each project contains:

-   Summary
-   Architecture
-   Technologies
-   Challenges
-   Lessons learned
-   GitHub
-   Live demo

------------------------------------------------------------------------

# Architecture Page (New)

Dedicated technical page.

Sections:

-   System diagram
-   Retrieval pipeline
-   Ingestion pipeline
-   Caching strategy
-   API overview
-   Deployment architecture

Purpose:

Engineers can understand the system without asking the chatbot.

------------------------------------------------------------------------

# Resume

Embedded PDF.

Actions:

-   Download
-   Print

Powered by GET /resume.

------------------------------------------------------------------------

# Tech Stack

Grouped by category:

-   Languages
-   Backend
-   Frontend
-   Databases
-   Cloud
-   DevOps
-   AI/ML
-   Tools

Powered by GET /stack.

------------------------------------------------------------------------

# Hire Me

Displays:

-   Availability
-   Preferred roles
-   Employment types
-   Preferred locations
-   Contact details
-   Resume button

Future enhancement:

Contextual Hire Me suggestion after multiple meaningful chat
interactions.

------------------------------------------------------------------------

# About This Portfolio

Small informational card.

Example:

> Every AI response is grounded using my portfolio documents through a
> Retrieval-Augmented Generation (RAG) pipeline and includes source
> citations. The assistant never relies solely on model memory.

This explains why the chatbot is trustworthy.

------------------------------------------------------------------------

# Offline Mode

If backend chat is unavailable:

Display:

> AI assistant is temporarily unavailable.

> Static portfolio loaded successfully.

Continue serving:

-   Projects
-   Resume
-   Stack
-   Hire
-   Architecture
-   Hero section

Only chat becomes unavailable.

## API Fallback

If AI chat is unavailable, navigation should automatically redirect users toward deterministic portfolio pages (Projects, Resume, Stack, Hire) rather than presenting a dead-end experience.

# Live System Status

Display the health of the backend services.

Suggested indicators:

🟢 AI Assistant

🟢 Retrieval Index

🟢 Resume API

🟢 Stack API

🟢 Cache

If the AI service becomes unavailable, the status should clearly communicate that only chat is affected while deterministic endpoints remain operational.

------------------------------------------------------------------------

# Terminal Mode

Not the default.

Available as:

-   Toggle or
-   Hidden shortcut

Purpose:

Engineering showcase.

Not required for recruiter workflow.

------------------------------------------------------------------------

# Footer

Include:

-   GitHub
-   LinkedIn
-   Email
-   Resume
-   Current Status
-   Built With (FastAPI, Next.js, Redis, PostgreSQL, Azure)

------------------------------------------------------------------------

# Accessibility

-   Keyboard navigation
-   Screen reader labels
-   High contrast support
-   Visible focus rings
-   Reduced motion mode

------------------------------------------------------------------------

# Visual Design

Prioritize:

-   Clarity
-   Familiarity
-   Fast information retrieval

Avoid:

-   Hacker aesthetics
-   Neon terminal themes
-   Heavy animations

------------------------------------------------------------------------

# Frontend Technology

-   Next.js
-   React
-   TypeScript
-   Tailwind CSS
-   shadcn/ui
-   TanStack Query
-   React Markdown
-   react-pdf
-   Framer Motion (minimal)

------------------------------------------------------------------------

# MVP Scope

## Required

-   Hero
-   Summary strip
-   Chat
-   Featured project
-   Architecture page
-   Resume
-   Tech Stack
-   Hire
-   Mobile citations
-   Offline mode
-   Streaming UX

## Deferred

-   Conversation history
-   Voice input
-   Public API explorer
-   Themes
-   Analytics dashboard

------------------------------------------------------------------------

# PRD Deviation Log

## Terminal-first UI

Original PRD proposed a terminal-first experience.

Decision:

Use a modern AI chat interface as the default and expose terminal mode
as an optional experience.

Reason:

This reduces friction for recruiters while preserving a technical
showcase for engineers.

------------------------------------------------------------------------

# Guiding Principle

A recruiter should understand the value of the portfolio within 30
seconds.

An engineer should discover increasingly deeper technical detail the
more they explore.

The AI assistant should amplify the portfolio---not become the
portfolio.
