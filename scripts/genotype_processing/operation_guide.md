# Genotype Processing Operation Guide

This guide documents the practical use of `scripts/genotype_processing/` after the scientific-domain script restructure. It is an execution guide, not the scientific taxonomy source. Domain classification lives in `references/analysis_domains/` and `references/ontology/domain_scope_vocab.md`.

## Directory role

`scripts/genotype_processing/` contains thin Bash entrypoints for genotype readiness and QC. The current executable wrapper is:

- `run_genotype_qc.sh`

Compatibility routing:

| Current scientific directory | Compatibility blueprint key | Knowledge domain |
|---|---|---|
| `scripts/genotype_processing/` | `qc_pipeline` | `data_preparation_qc`, partial `genotype_processing` |

The script does not submit jobs. Remote execution, queue submission, SSH shell execution, polling, retry, and resume are owned by `src/scheduler/` and `src/runtime/`.

## Advanced processing boundary

The current executable wrapper is QC-oriented. It can inventory VCF/PLINK inputs and run first-pass PLINK2/bcftools checks, but it should not be presented as a complete phasing, imputation, liftover, or allele-harmonization engine.

Use `references/analysis_domains/genotype_processing.md` when a request mentions:

- VCF normalization or PLINK conversion beyond basic QC.
- REF/ALT, A1/A2, strand-ambiguous SNPs, allele flips, or summary-statistic harmonization.
- Genome build conversion, chain files, coordinate liftover, or contig-name mapping.
- Beagle, Eagle, Minimac-style phasing/imputation, reference panels, dosages, or imputation quality.

For these requests the Agent may generate a reviewed plan and safety checklist, but real execution should remain blocked until a dedicated wrapper, tool manifest, report contract, and tests exist for the requested operation.

## Expected input package

At least one genotype-bearing input is required:

- VCF/VCF.GZ through `--vcf`
- PLINK binary prefix through `--plink-prefix`
- auto-discovered VCF or complete `.bed/.bim/.fam` triplet under `--input-root`

Optional sidecars:

- `--phenotype`
- `--covariate`
- `--pedigree`

Input rules:

- Use POSIX `/` paths only.
- Keep raw genotype, phenotype, covariate, and pedigree inputs read-only.
- Do not rely on suffix alone to define a file role; upstream planning should preserve role assignment.
- Do not auto-repair sample IDs inside this script. ID reconciliation belongs in planning/validation and report artifacts.
- Treat BAM-derived data as out of scope unless a supported upstream conversion wrapper has produced genotype matrices.

## Common invocation

Dry-run inventory:

```bash
scripts/genotype_processing/run_genotype_qc.sh \
  --workdir /data2/user/geneagent_runs/task_001/run_001 \
  --input-root /data2/user/project_inputs \
  --vcf /data2/user/project_inputs/cohort.vcf.gz \
  --phenotype /data2/user/project_inputs/phenotype.tsv \
  --threads 8 \
  --memory-mb 32768 \
  --tmp-dir /data2/user/geneagent_runs/task_001/run_001/tmp/genotype_qc \
  --dry-run
```

Execute with PLINK prefix:

```bash
scripts/genotype_processing/run_genotype_qc.sh \
  --workdir /data2/user/geneagent_runs/task_001/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --phenotype /data2/user/project_inputs/phenotype.tsv \
  --covariate /data2/user/project_inputs/covariates.tsv \
  --pedigree /data2/user/project_inputs/pedigree.tsv \
  --analysis-targets qc,sample_qc,variant_qc \
  --threads 16 \
  --memory-mb 65536
```

The examples intentionally use server-side POSIX paths. Windows local paths should be converted by the Agent before remote execution.

## Resource parameters

Every generated or manually launched command should include explicit resource parameters:

| Option | Purpose | Minimum expectation |
|---|---|---|
| `--threads` | caps PLINK2 and bcftools thread use when supported | positive integer |
| `--memory-mb` | passes PLINK2 memory cap and sets script virtual-memory guard | integer >= 256 |
| `--tmp-dir` | tool spill directory and `TMPDIR` | inside the approved working root |
| `--log-dir` | stdout/stderr capture path | inside the run working directory |

The script also exports common thread-control variables:

- `OMP_NUM_THREADS`
- `OPENBLAS_NUM_THREADS`
- `MKL_NUM_THREADS`
- `NUMEXPR_NUM_THREADS`

On an ordinary Linux server these are best-effort guards, not queue-side isolation. The Agent must block plans that exceed configured remote caps before materializing a run.

## Output contract

The wrapper writes:

| Path | Meaning |
|---|---|
| `results/qc/run_manifest.json` | script-level inputs, resource parameters, tools, outputs, and safety notes |
| `results/qc/audit_sidecar.json` | run context for downstream report and audit packaging |
| `results/qc/input_manifest.json` | effective input roles and request context for executed runs |
| `results/qc/sample_qc.tsv` | sample-level missingness metrics when PLINK2 output exists |
| `results/qc/variant_qc.tsv` | variant missingness and allele-frequency metrics when PLINK2 output exists |
| `results/qc/bcftools.stats.txt` | VCF summary when `bcftools` and VCF input are available |
| `results/qc/retained_dataset/README.md` | retained dataset pointer index |
| `reports/qc_summary.md` | human-readable QC summary |
| `logs/genotype_qc.log` | script stdout/stderr capture |

Downstream report generation should treat these as artifacts to index and explain, not as final biological decisions.

## Failure handling

Pre-submit blockers:

- Windows backslashes in any path
- no VCF and no complete PLINK genotype input
- missing required companion files
- resource request above Agent caps
- output path exists and overwrite was not approved

Execution failures:

- `plink2` missing: VCF-only conversion and PLINK QC are skipped or fail depending on available alternative inputs.
- `bcftools` missing: VCF stats are skipped; PLINK2 QC may still complete.
- malformed VCF or PLINK input: fail the run and keep logs for diagnostics.
- no algorithm executed: fail rather than producing an empty success report.

Auto-repair boundary:

- Allowed: create run, log, tmp, state, results, and reports directories inside the approved run root.
- Allowed: retry transient SSH or remote shell failures from the scheduler/runtime layer.
- Not allowed: delete raw inputs, overwrite prior results without approval, guess sample ID transformations, lower QC thresholds to force success, or submit beyond resource caps.

## Cross-links

Use these knowledge assets when planning or explaining this directory:

- `references/analysis_domains/data_preparation_qc.md`
- `references/analysis_domains/genotype_processing.md`
- `references/input_specs/input_bundle_contract.md`
- `references/qc_rules/default_qc_threshold_profile.md`
- `references/parameter_playbooks/qc_defaults.md`
- `references/failure_cases/operational_failure_cases.md`
- `references/evaluation/diagnostics/bio_tool_error_patterns.md`
