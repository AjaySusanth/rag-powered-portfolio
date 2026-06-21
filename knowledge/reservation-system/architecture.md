<!-- 
DESIGN DECISION: This document outlines the architectural blueprint of the Reservation System. It is configured for Layer 2 chunking (512-token limit, 64-token overlap). Each H2 section is designed to be fully self-contained, explicitly referencing the "Reservation System" and its stack. This prevents context fragmentation, ensuring the RAG model returns complete architectural patterns when queried about the system's design.
-->
  
# Reservation System - Architecture Design

## High-Level System Architecture
The Reservation System is a lightweight, high-performance backend application built using a modern RESTful API design. The core engine is implemented using **FastAPI** (Python 3.12) to handle client requests with minimal latency and high concurrency. The application is supported by two main data layers:
1. **PostgreSQL** serves as the primary relational database, maintaining transactional consistency and storing core resources such as users, tables, and bookings.
2. **Redis** acts as an in-memory caching and session store, shielding the primary database from redundant query loads and keeping endpoint latency sub-millisecond.

Clients connect to the FastAPI application via HTTP REST endpoints. The entire local ecosystem is containerized and coordinated using **Docker Compose** to guarantee environment parity across development and deployment setups.

---

## Database & Data Model
The database architecture of the Reservation System is structured around strict relational integrity and transactional boundaries to prevent double-booking issues. We model the domain using three primary entities:
- **Users**: Represents customers and administrators, handling authentication references.
- **Resources / Tables**: Represents reservation capacities (e.g., dining tables, venue slots, or equipment items) that can be claimed for specific time ranges.
- **Bookings / Reservations**: Connects a User to a specific Resource for a defined duration. Bookings use composite database constraints and range exclusion checks to guarantee no overlap occurs.

Schema migrations and database access are abstracted using **Prisma ORM** (or SQLAlchemy/Alembic in pure Python configurations), allowing the backend to execute type-safe queries and programmatically enforce relational constraints.

---

## Component Roles & Directory Layout
The Reservation System adheres to a clean, decoupled three-tier architecture to isolate concerns and ease maintainability. The codebase is organized into the following distinct directories:
- **Routes / Router**: Defines the HTTP endpoints and handles input verification using Pydantic models. It delegates business logic execution to controllers or services.
- **Controllers**: Acts as the traffic controller, extracting parameters from routes, orchestrating calls to the service layer, and formatting the outgoing JSON responses.
- **Services**: Contains the raw business logic. This layer processes booking availability checks, calculates rates, and handles transactional logic.
- **Middleware**: Intercepts requests for cross-cutting concerns such as logging, CORS, rate limiting, and JWT validation.
- **Prisma Schema**: Holds the declarative schema file (`schema.prisma`), serving as the single source of truth for the database layout.

---

## Deployment & Containerization Layout
To facilitate ease of deployment, the Reservation System uses multi-stage **Docker** builds to minimize production image sizes and security vulnerability surfaces. The container orchestration is handled locally via a multi-service `docker-compose.yml` config, exposing:
- An API service mapping internal port 8000 to the host network.
- A PostgreSQL database utilizing a persistent volume to prevent data loss across container lifecycle events.
- A Redis instance mapping port 6379 for caching.
- An NGINX reverse proxy acting as an entry gateway to distribute traffic and handle CORS configurations.
