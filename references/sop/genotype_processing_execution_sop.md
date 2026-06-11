# Genotype Processing Execution SOP

## Scope and Inputs

```yaml
knowledge_item.v2:
  doc_id: sop_genotype_processing_execution
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

This SOP covers the current genotype-processing execution bridge for PLINK/PLINK2 and bcftools based readiness checks, file inventory, VCF/PLINK input validation, and first-pass genotype QC. It does not authorize phasing, imputation, liftover, allele harmonization, or BAM/FASTQ processing unless a dedicated wrapper and report contract exist.

Required inputs are a VCF/VCF.GZ, a complete PLINK `.bed/.bim/.fam` or `.pgen/.pvar/.psam` dataset, or an approved input root containing one of those genotype representations. Optional sidecars include phenotype, covariate, pedigree, sample manifest, checksum manifest, and reference assembly notes.

## Preflight Checks

- Normalize all paths to POSIX `/` form before script generation.
- Confirm raw genotype and sidecar files are read-only.
- Verify sample IDs are not silently rewritten; unresolved ID mismatches are breaker conditions.
- Check that requested tools are known: `plink2`, `plink`, `bcftools`, `tabix`, or documented dry-run fallback.
- Require explicit `--threads`, `--memory-mb`, `--tmp-dir`, and `--log-dir` before remote execution.
- Confirm requested output directories are inside the approved run root and will not overwrite existing results without explicit approval.

## Execution Steps

1. Build an input manifest with file role, source path, size, checksum status when available, and sample-count hints.
2. For VCF input, validate compression/index status and record whether `bcftools stats` or normalization is only planned versus executed.
3. For PLINK input, verify complete triplets or pfile components before invoking PLINK/PLINK2.
4. Run first-pass sample and variant missingness summaries when the tool is available and dry-run is disabled.
5. Export common thread-limit variables and pass tool-native thread/memory flags.
6. Write a run manifest, audit sidecar, logs, and a retained-dataset pointer rather than copying raw genotype files.

## Expected Outputs

- `results/qc/run_manifest.json`
- `results/qc/audit_sidecar.json`
- `results/qc/input_manifest.json`
- `results/qc/sample_qc.tsv` when PLINK/PLINK2 sample metrics are generated
- `results/qc/variant_qc.tsv` when PLINK/PLINK2 variant metrics are generated
- `results/qc/bcftools.stats.txt` when VCF stats are generated
- `results/qc/retained_dataset/README.md`
- `reports/qc_summary.md`
- `logs/genotype_qc.log`

## Failure and Breaker Rules

Breaker conditions include missing genotype input, incomplete PLINK file sets, non-POSIX paths, output overwrite risk, unknown tools, sample ID mismatch, resource requests above configured caps, and attempts to move raw VCF/BAM/FASTQ/FASTA data outside the operator-owned work root.

Low-risk automatic repairs are limited to creating run-local log/tmp/result directories, adding safe sidecar manifests, retrying transient SSH/read errors, and producing dry-run instructions. The Agent must not auto-change sample filters, allele coding, reference assembly, or genotype calls.

## Report and Audit Handoff

Reports must state input roles, observed file formats, tool availability, explicit resource parameters, QC metrics produced, skipped operations, and unresolved sidecar risks. Audit records must preserve input summaries, command previews, log paths, run IDs, and the reason when genotype processing was stopped at dry-run.
