# reporting_audit

`reporting_audit` is the V2 packaging layer for artifact indexing, figure collation, summary rendering, diagnostics summarization, and traceability export.

Detailed operation guide:
- `operation_guide.md`

Scripts:
- `run_report_generator.sh`: top-level entrypoint that runs indexing, figure collection, summary rendering, and traceability export in order.
- `build_result_index.sh`: scan artifacts and write `results/report_index.json` using `report_index.v2` schema.
- `collect_figures.sh`: copy figures into a stable output directory without overwriting by default.
- `render_summary_report.sh`: render a markdown summary from the V2 index.
- `export_traceability.sh`: export JSON and markdown traceability bundles with scheduler/wrapper/log/audit links.
- `manifest.example.yaml`: example contract for wiring the report generator into a workflow or release step.

Example:

```bash
bash scripts/reporting_audit/run_report_generator.sh --workdir D:/geneagent
bash scripts/reporting_audit/run_report_generator.sh --workdir D:/geneagent --figure-root D:/geneagent/results/structure/figures --manifest D:/geneagent/results/qc/input_manifest.json
bash scripts/reporting_audit/build_result_index.sh --workdir D:/geneagent
bash scripts/reporting_audit/collect_figures.sh --workdir D:/geneagent --figure-root D:/geneagent/results/structure/figures
bash scripts/reporting_audit/render_summary_report.sh --workdir D:/geneagent
bash scripts/reporting_audit/export_traceability.sh --workdir D:/geneagent --manifest D:/geneagent/results/qc/input_manifest.json
```

Defaults and safety:
- Missing input paths fail fast with clear error messages.
- Existing outputs are not overwritten unless `--force` is provided.
- The scripts package declared artifacts and diagnostics only; they do not validate scientific claims.
- `run_report_generator.sh --dry-run` writes `results/report_generator_run_manifest.json` and `logs/report_generator.log` without invoking the packaging subcommands.
- Scientific-domain knowledge for this directory is maintained in `references/analysis_domains/hpc_execution_reporting_audit.md`.
- Reporting/audit scripts may package evidence, diagnostics, and traceability, but must not modify raw scientific outputs or invent biological conclusions.
