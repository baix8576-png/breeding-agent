# Audit Module

This module owns trace records for reproducibility and safety review.

## Current scope
- Define a stable audit event model.
- Store audit events in memory for local development.
- Return immutable snapshots of the current event list.

## Out of scope in V1
- Persistent audit storage.
- Signed audit trails and tamper detection.
- Export pipelines for compliance systems.

## Next iteration hook
- Introduce append-only adapter interfaces and file/database implementations.
