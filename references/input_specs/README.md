# input_specs

Owner: `popgen_quantgen`

Purpose:
- Define input package contracts, file roles, sample ID policy, and sidecar expectations for GeneAgent planning.
- Support the `Input Validation` stage before blueprint selection and scheduler preview.

Formal knowledge files:
- `input_bundle_contract.md`: request envelope, file role matrix, sample ID policy, and path/sidecar policy.
- `dataset-bundle-template.md`: user-facing dataset bundle template and validation reminders.

Maintenance notes:
- Keep raw entity data out of this directory.
- New formal Markdown files must include at least one `knowledge_item.v2` section.
- Path guidance should use `/` for scheduler-facing scripts.
