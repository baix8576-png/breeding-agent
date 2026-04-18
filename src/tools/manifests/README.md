# manifests

This directory stores file-based tool manifest definitions.

Current state:
- `catalog.v1.json` is the primary source loaded by `src/tools/manifest_loader.py`.
- `ToolRegistry` still keeps a legacy fallback source through `src/tools/manifest_legacy.py` for
  gradual migration safety.
- Manifest schema is validated by `src/tools/manifest_schema.py`.

Conventions:
- Use JSON files with UTF-8 encoding.
- Keep `schema_version` and `manifest_version` in every manifest entry.
- Keep stage/domain values aligned with the orchestrator stage map and `TaskDomain` values.
