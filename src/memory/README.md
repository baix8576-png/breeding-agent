# Memory Module (Placeholder)

This module owns short-term/session context and run-level handoff context.

## Current scope
- Keep session records in process (`InMemorySessionStore`).
- Keep run records in process (`InMemoryRunStore`).
- Build deterministic stage and handoff placeholders (`MemoryCoordinator`).

## Out of scope in the skeleton phase
- Persistent storage backends.
- Cross-run retrieval/ranking.
- Retention and eviction policies.

## Next iteration hook
- Add storage adapter interfaces before introducing database-backed memory.
