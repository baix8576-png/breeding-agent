# Tool Manifest Authoring Spec (V1.5)

This document standardizes authoring for file-based manifests in `src/tools/manifests/`.

## Source of Truth
- Schema: `src/tools/manifest_schema.py`
- Loader: `src/tools/manifest_loader.py`
- Registry entry: `src/tools/registry.py`
- Manifest files: `src/tools/manifests/*.json`

## Required Fields (per manifest item)
- `schema_version`
- `manifest_version`
- `name`
- `description`
- `category`
- `stage_scope`
- `domain_scope`
- `inputs`
- `outputs`
- `preconditions`

For atomic algorithms, also require:
- `algorithm_family`
- `atomic_resource_profile` (`cpus`, `memory_gb`, `walltime`, optional `partition`)
- `failure_code_map` (code, retryable, retry_suggestion, reason)

## Authoring Rules
1. Naming and version:
- Use stable snake_case tool names, e.g. `plink2_pca`, `gcta_reml`.
- Keep semantic versions in `schema_version` and `manifest_version`.

2. Scope discipline:
- `stage_scope` must map to concrete runtime stages.
- `domain_scope` must be explicit (`shared`, `bioinformatics`, `knowledge`, `system`).

3. Atomic metadata quality:
- Resource profile must be conservative and production-safe.
- Failure map must include at least one actionable retry recommendation when retryable.

4. Compatibility:
- Do not remove or rename existing manifest names without migration plan.
- Add new manifests in additive manner and verify loader strict-mode behavior.

## Validation and Regression
- Unit schema tests: `tests/unit/tools/test_manifest_schema.py`
- Loader tests: `tests/unit/tools/test_manifest_loader.py`
- Registry tests: `tests/unit/tools/test_registry.py`
- Scheduler atomic profile tests: `tests/unit/scheduler/test_atomic_profiles.py`

## Example Change Checklist
- [ ] Added/updated manifest JSON under `src/tools/manifests/`.
- [ ] Schema validation passes.
- [ ] Registry stage/domain filtering behavior remains correct.
- [ ] Atomic failure mapping and retry guidance tests pass.
- [ ] Full gate (`compileall + pytest -q`) is green.

