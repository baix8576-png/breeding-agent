# Pipeline Pack Integration Guide

This guide describes how to add or evolve blueprint packs under `src/pipeline/packs/` while keeping V1.5 behavior stable.

## Pack Contract
Each pack must provide:
- `spec`: pack identity and blueprint binding
- `stages`: ordered stage definitions with IO semantics
- `artifacts`: expected outputs and classification
- `report_template`: report summary sections and required markers
- `tests`: minimum regression test references

Current implementation references:
- `src/pipeline/packs/models.py`
- `src/pipeline/packs/registry.py`
- `src/pipeline/packs/builtin_blueprints.py`

## Integration Steps
1. Define or update pack payload:
- Add or edit blueprint payload in `src/pipeline/packs/builtin_blueprints.py`.
- Keep canonical keys aligned with `qc/pca/grm/gwas/genomic_prediction` compatibility routing.

2. Register pack:
- Ensure registry alias resolution maps user intents and legacy names to the canonical pack.
- Verify `build_pipeline_pack(name)` returns deterministic pack object.

3. Preserve compatibility surface:
- Confirm `build_blueprint(name)` remains behavior-equivalent by comparing to `pack.to_blueprint_payload()`.
- Do not break stage order, stage contract names, or artifact contract labels used by runtime.

4. Add/update tests:
- Unit: `tests/unit/pipeline/test_packs.py`
- Unit/compat: `tests/unit/pipeline/test_pipeline_execution.py`
- E2E sanity: `tests/e2e/test_v1_completion.py`

5. Validate with gates:
- `python -m compileall src tests`
- `python -m pytest -q`

## Definition of Done
- [ ] Pack schema is valid and registry resolves aliases correctly.
- [ ] Old blueprint outputs remain behavior-equivalent.
- [ ] Pack tests and baseline pipeline tests are all green.
- [ ] No core workflow logic leaked into `scripts/*`.
