<!-- 
DESIGN DECISION: This document records the core architectural decisions made for the Reservation System. In compliance with Layer 2 chunking constraints (512-token limit, 64-token overlap), every H2 section is written to be entirely self-contained. Each decision clearly explains the context, options evaluated, trade-offs, and the final rationale to ensure the RAG system retrieves a complete decision-making unit.
-->

# Reservation System - Architectural Decisions

## Decision: Choice of Relational Database (PostgreSQL over MongoDB)
- **Context**: The Reservation System requires strict transaction guarantees. When two users attempt to book the same slot or table simultaneously, the database must enforce ACID compliance to prevent overbooking anomalies or race conditions.
- **Options Evaluated**: 
  - *PostgreSQL*: An ACID-compliant relational database supporting transactional locks and strict check constraints.
  - *MongoDB*: A document-oriented NoSQL database offering high write scaling but weaker relational consistency for transaction boundaries.
- **Trade-offs**: While MongoDB provides schema flexibility and simple JSON mapping, it lacks the out-of-the-box relational guarantees and SQL-level exclusion constraints necessary to block double-bookings natively at the database layer.
- **Rationale**: PostgreSQL was selected because it guarantees absolute data integrity. We can utilize table-level locking or reservation exclusion constraints (using SQL range functions) to block conflicting bookings at the database tier. Furthermore, PostgreSQL's compatibility with the `pgvector` extension ensures that this codebase can serve as a base for vector-embedding integration in the future.

---

## Decision: Choice of Backend Framework (FastAPI over Node.js Express)
- **Context**: The backend API for the Reservation System needs to handle high concurrent client requests for checking availability while remaining easy to document and type-safe.
- **Options Evaluated**:
  - *FastAPI (Python)*: A modern, high-performance web framework based on ASGI, Starlette, and Pydantic.
  - *Express (Node.js/TypeScript)*: A mature, widely-used minimalist web framework for JavaScript.
- **Trade-offs**: Express has a larger ecosystem and more middleware choices, but it requires manual integration of schema verification tools (like Zod) and lacks native asynchronous type-safety declarations out of the box.
- **Rationale**: FastAPI was chosen because of its native support for asynchronous Python (`async/await`), which allows for highly concurrent non-blocking database queries. FastAPI's auto-generated OpenAPI documentation (via Pydantic schemas) accelerates frontend integration. Pydantic models also act as strict request/response contracts, catching data validation issues before they reach the controller layer.

---

## Decision: Choice of Cache Layer (Redis for Session and Response Caching)
- **Context**: Read operations in the Reservation System (such as browsing available slots or table layouts) occur significantly more frequently than write operations (creating a booking). Continually querying PostgreSQL for static layouts creates unnecessary resource consumption.
- **Options Evaluated**:
  - *Redis*: An in-memory, key-value data structure store supporting high-throughput lookups and TTL-based eviction.
  - *In-Memory Application Cache (e.g., local dict or cache)*: Local caching within the FastAPI process memory space.
- **Trade-offs**: In-memory application caches are simple to write but fail to scale horizontally when multiple instances of the backend API run behind a load balancer, leading to cache inconsistency.
- **Rationale**: Redis was chosen because it provides a centralized, distributed cache that remains consistent across all API container instances. By setting a TTL (Time-To-Live) on cached availability queries, we ensure data refreshes automatically. Redis also serves as the session store for user states, preventing state loss during application redeployments.
