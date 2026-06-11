# Association Mapping Operation Guide

This guide documents `scripts/association_mapping/` after the scientific-domain script restructure. It covers the practical boundary for first-pass GWAS and explains what remains outside the current automatic execution bridge.

## Directory role

`scripts/association_mapping/` currently contains one thin wrapper:

- `run_gwas.sh`

Compatibility routing:

| Current scientific directory | Execution blueprint key | Knowledge domain |
|---|---|---|
| `scripts/association_mapping/` | `association_mapping_gwas` | `association_mapping_gwas_qtl` |

This directory supports first-pass marker-trait association execution. It does not perform QTL mapping, fine mapping, or functional validation.

## Knowledge bridge

- SOP: `references/sop/association_mapping_execution_sop.md`
- Parameter playbooks: `references/parameter_playbooks/core_parameter_playbooks.md`, `references/parameter_playbooks/scheduler_resource_presets.md`
- Failure diagnostics: `references/evaluation/diagnostics/bio_tool_error_patterns.md`, `references/failure_cases/operational_failure_cases.md`

## Expected input package

Required:

- genotype matrix through `--plink-prefix` or `--vcf`
- phenotype table through `--phenotype`

Optional:

- covariate table through `--covariate`
- trait column hint through `--trait-column`
- input auto-discovery under `--input-root` for simple fixture-like runs

Input rules:

- Use POSIX `/` paths only.
- Phenotype and covariate sample IDs must be reconciled before submit.
- Raw genotype, phenotype, and covariate inputs remain read-only.
- PCA or GRM correction must be supplied as explicit covariates or handled by a future mixed-model bridge; the wrapper does not infer correction terms.

## Common invocation

Dry run:

```bash
scripts/association_mapping/run_gwas.sh \
  --workdir /data2/user/geneagent_runs/task_003/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --phenotype /data2/user/project_inputs/phenotype.tsv \
  --covariate /data2/user/project_inputs/covariates.tsv \
  --trait-column body_weight \
  --threads 16 \
  --memory-mb 65536 \
  --tmp-dir /data2/user/geneagent_runs/task_003/run_001/tmp/association_mapping_gwas \
  --dry-run
```

Execute first-pass GWAS:

```bash
scripts/association_mapping/run_gwas.sh \
  --workdir /data2/user/geneagent_runs/task_003/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --phenotype /data2/user/project_inputs/phenotype.tsv \
  --covariate /data2/user/project_inputs/covariates.tsv \
  --analysis-targets gwas \
  --threads 16 \
  --memory-mb 65536
```

## Method boundaries

| Target | Current support | Boundary |
|---|---|---|
| first-pass GWAS | supported through PLINK2 `--glm` | exploratory unless model correction is reviewed |
| PCA covariate GWAS | supported only when covariate file is supplied | wrapper does not compute PCs |
| mixed-model GWAS | not yet automated | requires GRM/kinship contract and tool support |
| QTL interval mapping | not yet automated | family/linkage design differs from GWAS |
| fine mapping | not yet automated | requires regional model, LD reference, and credible-set policy |
| candidate gene interpretation | not executed by wrapper | report/knowledge reasoning only |

## Resource parameters

Always pass explicit resource parameters:

| Option | Purpose |
|---|---|
| `--threads` | caps PLINK2 thread use and common thread environment variables |
| `--memory-mb` | passes PLINK2 memory cap and sets virtual-memory guard |
| `--tmp-dir` | tool spill directory under approved run root |
| `--log-dir` | log capture directory |

On an ordinary Linux server, these are pre-submit and process-level guards. They are not a substitute for scheduler or cgroup isolation.

## Output contract

The wrapper writes:

| Path | Meaning |
|---|---|
| `results/association/gwas/run_manifest.json` | inputs, resources, tools, outputs, and safety notes |
| `results/association/gwas/audit_sidecar.json` | run context for report and audit packaging |
| `results/association/gwas/cohort_alignment.json` | effective genotype, phenotype, covariate, and trait hints |
| `results/association/gwas/model_spec.json` | PLINK2 `--glm` model family and input summary |
| `results/association/gwas/README.md` | GWAS result-file index |
| `results/association/gwas/metrics.tsv` | row-count metrics |
| `reports/gwas_summary.md` | human-readable execution summary |
| `logs/association_mapping_gwas.log` | script stdout/stderr capture |

Downstream reporting should add multiple-testing, QQ/Manhattan, locus annotation, and validation context only when those artifacts exist.

## Failure handling

Pre-submit blockers:

- missing genotype matrix
- missing phenotype table
- missing `plink2`
- non-POSIX paths
- output overwrite without approval
- resource request above configured caps

Safe automatic actions:

- create result, report, log, and tmp directories inside approved run root
- convert VCF to a temporary PLINK dataset when `plink2` is available
- preserve model and cohort metadata even for dry runs

Breaker conditions:

- no GWAS step executed
- automatic phenotype aggregation
- guessed trait column when multiple traits exist
- automatic PCA/GRM correction without explicit input
- any claim that first-pass PLINK2 output is fine mapping or causal validation

## Cross-links

Use these knowledge assets when planning or explaining this directory:

- `references/analysis_domains/association_mapping_gwas_qtl.md`
- `references/analysis_domains/population_structure.md`
- `references/analysis_domains/data_preparation_qc.md`
- `references/papers/qc_core_papers_v1.md`
- `references/papers/pca_core_papers_v1.md`
- `references/papers/animal_genomics_classic_landmarks.md`
- `references/papers/animal_genomics_recent_high_impact_2022_2026.md`
