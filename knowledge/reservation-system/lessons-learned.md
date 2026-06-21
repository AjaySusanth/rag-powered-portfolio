<!-- 
DESIGN DECISION: This document outlines the key engineering and architectural lessons learned during the construction of the Reservation System. Formatted for Layer 2 chunking (512 tokens, 64 overlap), each H2 block summarizes a practical takeaway and its broader architectural impact. This allows the RAG system to retrieve concrete engineering wisdom when queried about project reflections.
-->

# Reservation System - Lessons Learned

## Lesson: Pushing Constraints to the Database Layer
- **Takeaway**: Application-level checks for data integrity are insufficient in concurrent environments. Critical business rules—such as preventing overlapping reservations—must be enforced at the database schema tier.
- **Context**: Initially, booking conflicts in the Reservation System were checked via application code (e.g., querying existing bookings, verifying constraints in Python, and inserting if free). Under simulated load testing, this allowed duplicate bookings due to race conditions.
- **Resolution & Learning**: Moving constraint checks directly into PostgreSQL using range types (`tsrange`) and the `EXCLUDE` constraint solved the problem permanently. By allowing the database engine to reject overlapping inserts at the storage level, we simplified our application logic (removing complex lock management code) and guaranteed absolute data integrity. In the future, I will leverage native database features for transaction integrity rather than attempting to hand-code lock synchronization in stateless application layers.

---

## Lesson: Value of Explicit Cache Invalidation Strategies
- **Takeaway**: Time-to-Live (TTL) is a safety net, not a primary cache synchronization strategy. High-transaction environments demand active event-driven cache invalidation.
- **Context**: During the initial rollout of caching, we relied on a standard 5-minute TTL to expire cached slot availability. This led to a window of inconsistency where clients were shown outdated information.
- **Resolution & Learning**: We transitioned to an event-driven model where the booking service publishes an invalidation event whenever a booking changes, immediately flushing the corresponding Redis keys. This taught us that while explicit invalidation adds complexity (handling failures during cache deletion), it is critical for system accuracy. The learning is to design cache structures with clear, predictable key hierarchies (e.g., namespace grouping) so that bulk invalidation can be done atomically using patterns like Redis pipelines or Lua scripts.
