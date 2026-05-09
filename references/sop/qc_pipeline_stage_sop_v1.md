# QC Pipeline Stage SOP (v1)

```yaml
knowledge_item.v2:
  doc_id: "sop_qc_pipeline_stage_v1"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "qc"
  evidence_level: "sop"
  source: "sop"
  updated_at: "2026-05-09T15:10:00+08:00"
  owner: "popgen_quantgen"
```

## Purpose
- Standardize stage-by-stage operation for `qc_pipeline`.
- Keep execution behavior aligned with `scripts/qc_pipeline/run_qc_pipeline.sh` and runtime contracts.

## Stage: dataset_inventory

### Input Thresholds
- At least one genotype-bearing dataset is required: `VCF(.vcf/.vcf.gz)` or PLINK trio (`.bed/.bim/.fam`).
- If both VCF and PLINK are provided, choose one canonical backbone before execution.
- Optional sidecars: phenotype/covariate/pedigree tables must be readable files if provided.

### Default Parameters
- `analysis_targets=qc,sample_qc,variant_qc`
- `input_root=workdir` when not explicitly set.
- Prefer existing PLINK prefix; if absent and VCF is present, allow temporary conversion via `plink2 --vcf --make-bed`.

### Manual Confirmation Points
- Confirm canonical genotype source when multiple modalities exist.
- Confirm sidecar files are only indexed, not interpreted biologically, in QC stage.
- Confirm all input paths are local and within approved workspace/cluster storage.

### Disable Conditions
- No genotype input found.
- PLINK trio is incomplete and no VCF fallback is available.
- Input validation gate is `blocked_by_validation`.

## Stage: sample_qc

### Input Thresholds
- Executable PLINK dataset is required (`--plink-prefix` or successful VCF-to-PLINK conversion).
- Recommended sample count >= 20 for stable exploratory missingness summary.

### Default Parameters
- `plink2 --missing --hardy --freq --out results/qc/plink_qc`
- Project default review thresholds:
- `sample_missing_rate <= 0.10` as retain baseline.
- `heterozygosity_outlier` review by cohort z-score (manual review required).

### Manual Confirmation Points
- Confirm sample exclusion uses both metric evidence and cohort context.
- Confirm sex/pedigree mismatch handling is documented rather than auto-dropped.
- Confirm any outlier removal is captured in audit records with rationale.

### Disable Conditions
- `plink2` unavailable and no precomputed sample QC artifacts.
- No valid PLINK backbone for sample-level metrics.
- Requested operation is non-bio branch (must not enter cluster execution).

## Stage: variant_qc

### Input Thresholds
- Variant-level metrics require PLINK-backed marker representation.
- Recommended marker count >= 1,000 for baseline distribution sanity.

### Default Parameters
- Use same PLINK run output (`plink_qc.vmiss`, `plink_qc.afreq`) to derive variant table.
- Project default review thresholds:
- `variant_missing_rate <= 0.05`
- `maf >= 0.01` for default common-variant analyses.
- `hwe_p >= 1e-6` (case/control-sensitive contexts must be manually reviewed).

### Manual Confirmation Points
- Confirm thresholds are species/project-specific overrides when needed.
- Confirm variants failing thresholds are tagged with explicit reason codes.
- Confirm low-frequency retention policy for rare-variant analysis is explicitly approved.

### Disable Conditions
- Missing required PLINK variant metric files and no rerun path.
- Marker metrics are malformed or empty.
- Any request that tries to convert QC metrics directly into biological claims.

## Stage: qc_report

### Input Thresholds
- `sample_qc.tsv` and `variant_qc.tsv` must exist or be explicitly marked unavailable with reason.
- Input manifest must include request context and selected analysis targets.

### Default Parameters
- Output contracts:
- `results/qc/input_manifest.json`
- `results/qc/sample_qc.tsv`
- `results/qc/variant_qc.tsv`
- `results/qc/retained_dataset/README.md`
- `reports/qc_summary.md`

### Manual Confirmation Points
- Confirm summary separates "observed metrics" from "decision recommendations".
- Confirm unresolved QC questions are listed before downstream handoff.
- Confirm report does not contain breeding or culling directives.

### Disable Conditions
- No QC algorithm step executed (hard fail in wrapper).
- Output tables missing and regeneration failed.
- Audit/memory writeback path unavailable for this run.
