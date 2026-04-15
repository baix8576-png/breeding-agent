# manifests

This directory is reserved for future file-based tool manifest definitions.

Current state:
- Tool manifest definitions are still bootstrapped from `src/tools/registry.py`.
- When a file loader is introduced, manifest files should be moved here and registered through
  the same stable `ToolRegistry` entrypoint.
