<!-- 
DESIGN DECISION: This document outlines the complex engineering challenges faced during the development of the Reservation System. Optimized for Layer 2 chunking (512 tokens, 64 overlap), each H2 section contains both the problem statement and the concrete engineering mitigation strategy. This allows the RAG system to directly retrieve the context of "what went wrong" and "how it was resolved" in a single step.
-->

# Reservation System - Engineering Challenges & Mitigations

## Challenge: Preventing Concurrent Double-Bookings (Race Conditions)
- **Problem**: In high-traffic scenarios, two concurrent users can query the availability of the same resource (e.g., Table 5) at the exact same millisecond. If both queries return "Available," the system proceeds to write two booking records to the database, resulting in a double-booked resource.
- **Impact**: High. Overbooking directly compromises system reliability and damages user trust.
- **Mitigation Strategy**: We mitigated this race condition in the Reservation System by moving booking verification into a database-level transaction. Using PostgreSQL's row-level locking mechanism, we query availability using a `SELECT ... FOR UPDATE` statement. This locks the target resource's availability state for the duration of the transaction. If a concurrent transaction tries to book the same slot, it is blocked until the first transaction commits or rolls back. Alternatively, we implemented database-level exclusion constraints using PostgreSQL's range types (`tsrange`), making it impossible for the database engine to accept overlapping durations for the same resource key.

---

## Challenge: Synchronizing Cache and Database State (Cache Staleness)
- **Problem**: When a user queries available tables in the Reservation System, the list is cached in Redis with a 10-minute TTL to reduce PostgreSQL load. If another user successfully books a table, the cached list in Redis remains "Available" for the remaining TTL duration, leading to user frustration when subsequent booking attempts fail at checkout.
- **Impact**: Medium. Degrades the user experience by showing stale availability data.
- **Mitigation Strategy**: We adopted the *Cache-Aside* pattern with explicit *Write-Through* cache invalidation. Whenever a write event occurs (e.g., booking creation, cancellation, or modification), the backend executes a database transaction to save the change and immediately issues a delete command to Redis for the associated cache keys (e.g., `avail:list:*`). This invalidates the cached availability immediately. The next read query misses the cache, retrieves the fresh state from PostgreSQL, and populates the cache with correct data.
