# report_generator

`report_generator` is the V1.5 packaging layer for artifact indexing, figure collation, summary report rendering, diagnostics summarization, and traceability export.

Scripts:
- `run_report_generator.sh`: top-level entrypoint that runs indexing, figure collection, summary rendering, and traceability export in order.
- `build_result_index.sh`: scan artifacts and write `results/report_index.json` using `report_index.v2` schema (with legacy-compatible artifact lists).
- `collect_figures.sh`: copy figures into a stable output directory without overwriting by default.
- `render_summary_report.sh`: render a markdown summary from the v2 index (blueprint summary, diagnostics, traceability links).
- `export_traceability.sh`: export JSON and markdown traceability bundles with scheduler/wrapper/log/audit links.
- `manifest.example.yaml`: example contract for wiring the report generator into a workflow or release step.

Typical usage:
1. Run a pipeline first so `results/` and `reports/` exist.
2. Build the artifact index.
3. Collect figures from one or more figure roots.
4. Render the summary report.
5. Export traceability metadata for audit or release packaging.

Example:

```bash
bash scripts/report_generator/run_report_generator.sh --workdir D:/geneagent
bash scripts/report_generator/run_report_generator.sh --workdir D:/geneagent --figure-root D:/geneagent/results/structure/figures --manifest D:/geneagent/results/qc/input_manifest.json
bash scripts/report_generator/build_result_index.sh --workdir D:/geneagent
bash scripts/report_generator/collect_figures.sh --workdir D:/geneagent --figure-root D:/geneagent/results/structure/figures
bash scripts/report_generator/render_summary_report.sh --workdir D:/geneagent
bash scripts/report_generator/export_traceability.sh --workdir D:/geneagent --manifest D:/geneagent/results/qc/input_manifest.json
```

Defaults and safety:
- Missing input paths fail fast with clear error messages.
- Existing outputs are not overwritten unless `--force` is provided.
- The scripts package declared artifacts and diagnostics only; they do not validate scientific claims.
