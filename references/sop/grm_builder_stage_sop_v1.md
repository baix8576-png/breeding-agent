# GRM Builder Stage SOP (v1)

```yaml
knowledge_item.v2:
  doc_id: "sop_grm_builder_stage_v1"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "grm"
  evidence_level: "sop"
  source: "sop"
  updated_at: "2026-05-09T15:10:00+08:00"
  owner: "popgen_quantgen"
```

## Purpose
- Standardize stage-by-stage operation for `grm_builder`.
- Align outputs with `scripts/grm_builder/run_grm_builder.sh` and downstream model consumers.

## Stage: marker_standardization

### Input Thresholds
- Genotype backbone required: PLINK trio or VCF convertible to PLINK.
- Recommended sample count >= 20 for stable relationship estimation.
- Optional pedigree file must be readable if provided.

### Default Parameters
- `analysis_targets=grm,kinship`
- If VCF-only input: convert via `plink2 --vcf --make-bed`.
- Marker standardization note output:
- `results/grm/marker_standardization.md`

### Manual Confirmation Points
- Confirm allele coding and filtering assumptions are recorded.
- Confirm whether pedigree is for cross-check only or downstream ssGBLUP integration.
- Confirm conversion artifacts are tagged as temporary if generated.

### Disable Conditions
- No usable genotype backbone.
- Neither `plink2` nor `gcta64` is available in execution environment.
- Input validation or safety gate blocks execution.

## Stage: relationship_estimation

### Input Thresholds
- PLINK prefix must exist and be complete.
- For full GRM route, at least one backend tool must be available:
- `plink2` for `--make-rel square`
- `gcta64` for `--make-grm`

### Default Parameters
- PLINK route: `plink2 --bfile <prefix> --make-rel square --out results/grm/grm`
- GCTA route: `gcta64 --bfile <prefix> --make-grm --out results/grm/grm_gcta`
- Required contract outputs:
- `results/grm/grm_matrix.tsv`
- `results/grm/grm_ids.tsv`

### Manual Confirmation Points
- Confirm selected backend route (`plink2`, `gcta64`, or both) is explicit.
- Confirm matrix row/column ordering is tied to exported ID map.
- Confirm fallback matrix pointer file is acceptable when text matrix is unavailable.

### Disable Conditions
- Backend command failure with no successful fallback route.
- Matrix artifact cannot be generated and no pointer metadata exists.
- Request tries to bypass ID map export.

## Stage: matrix_qc

### Input Thresholds
- `grm_matrix.tsv` and `grm_ids.tsv` must be present.
- Matrix shape extraction must be possible (rows/columns detectable).

### Default Parameters
- Minimum QC checks:
- matrix shape recorded
- square-matrix check (`rows == cols`)
- output provenance notes
- Report output:
- `reports/grm_qc.md`

### Manual Confirmation Points
- Confirm square check status is reviewed before downstream prediction use.
- Confirm sample-count mismatch between matrix and ID map is explicitly flagged.
- Confirm diagonal and symmetry deep checks are scheduled if required by study.

### Disable Conditions
- Matrix dimensions cannot be determined.
- ID map missing or unreadable.
- QC report generation fails.

## Stage: grm_package

### Input Thresholds
- `grm_qc.md` must exist.
- At least one relationship artifact must be indexable.

### Default Parameters
- Package index output:
- `results/grm/README.md`
- Include any available binaries:
- `grm_gcta.grm.bin`
- `grm_gcta.grm.N.bin`
- `grm_gcta.grm.id`

### Manual Confirmation Points
- Confirm package index includes all produced artifacts and missing-file reasons.
- Confirm downstream consumers are documented (prediction modules, audits).
- Confirm no biological interpretation is embedded in package index.

### Disable Conditions
- No relationship artifacts produced.
- Package index path unavailable.
- Audit chain cannot capture final artifact manifest.
