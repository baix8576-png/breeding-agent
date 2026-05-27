# failure_cases

Owner: `popgen_quantgen`; scheduler entries owned by `hpc_scheduler`; safety entries owned by `safety_fuse`

Purpose:
- Store reproducible operational failure cases with trigger, diagnosis, safe repair, and retry boundary.
- Support diagnostic reports and incident-informed planning.

Formal knowledge files:
- `operational_failure_cases.md`: scheduler account mismatch, missing sidecar, ID consistency, report traceability, knowledge retrieval gap, and raw data boundary violations.

Maintenance notes:
- Use `incident_verified` only for observed or strongly pattern-matched failure modes.
- Do not hide high-risk retry decisions inside generic prose.
- New formal Markdown files must include `knowledge_item.v2`.
