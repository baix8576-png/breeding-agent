# Knowledge Module

This module owns local-first retrieval and controlled external fallback behavior.

## Current scope
- Define stable retrieval data contracts.
- Serve deterministic local starter knowledge hits.
- Trigger external fallback hits only when local coverage is not high.

## Out of scope in V1
- Real network retrieval connectors.
- Vector index construction and refresh jobs.
- Multi-source ranking and reranking.

## Next iteration hook
- Add retriever adapter interfaces and sanitized external connector integration.
