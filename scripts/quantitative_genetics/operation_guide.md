# Quantitative Genetics Operation Guide

This guide documents `scripts/quantitative_genetics/` after the scientific-domain script restructure. It separates relationship-matrix construction from genomic prediction and breeding-value reporting.

## Directory role

`scripts/quantitative_genetics/` contains two thin wrappers:

- `run_relationship_matrix.sh`
- `run_breeding_value_prediction.sh`

Compatibility routing:

| Wrapper | Compatibility blueprint key | Knowledge domain |
|---|---|---|
| `run_relationship_matrix.sh` | `grm_builder` | `relationship_matrix_variance_components` |
| `run_breeding_value_prediction.sh` | `genomic_prediction` | `genomic_prediction_breeding_value` |

Association mapping is intentionally separated into `scripts/association_mapping/`.

## Relationship matrix invocation

Dry run:

```bash
scripts/quantitative_genetics/run_relationship_matrix.sh \
  --workdir /data2/user/geneagent_runs/task_004/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --pedigree /data2/user/project_inputs/pedigree.tsv \
  --analysis-targets grm,kinship \
  --threads 16 \
  --memory-mb 65536 \
  --tmp-dir /data2/user/geneagent_runs/task_004/run_001/tmp/relationship_matrix \
  --dry-run
```

Execute:

```bash
scripts/quantitative_genetics/run_relationship_matrix.sh \
  --workdir /data2/user/geneagent_runs/task_004/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --analysis-targets grm,kinship \
  --threads 16 \
  --memory-mb 65536
```

## Breeding value invocation

Dry run:

```bash
scripts/quantitative_genetics/run_breeding_value_prediction.sh \
  --workdir /data2/user/geneagent_runs/task_005/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --phenotype /data2/user/project_inputs/phenotype.tsv \
  --covariate /data2/user/project_inputs/covariates.tsv \
  --trait-column milk_yield \
  --analysis-targets heritability,genomic_prediction \
  --threads 16 \
  --memory-mb 65536 \
  --dry-run
```

Execute:

```bash
scripts/quantitative_genetics/run_breeding_value_prediction.sh \
  --workdir /data2/user/geneagent_runs/task_005/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --phenotype /data2/user/project_inputs/phenotype.tsv \
  --covariate /data2/user/project_inputs/covariates.tsv \
  --analysis-targets heritability,genomic_prediction \
  --threads 16 \
  --memory-mb 65536
```

## Method boundaries

| Concern | Current support | Boundary |
|---|---|---|
| GRM / kinship | PLINK2 relationship matrix and optional GCTA GRM | sample order must be audited |
| variance components | GCTA REML in prediction wrapper when phenotype exists | model design must be reviewed |
| GBLUP-like prediction | GCTA random-effect prediction when available | first-pass, not deployment-ready |
| ssGBLUP | knowledge/planning only | requires pedigree-genomic H-matrix backend |
| Bayesian/ML prediction | knowledge/planning only | needs separate model and validation contracts |
| breeding decisions | not automated | requires reviewed decision workflow |

## Resource parameters

Always pass explicit resource parameters:

| Option | Purpose |
|---|---|
| `--threads` | caps supported PLINK2/GCTA thread use and thread environment variables |
| `--memory-mb` | passes PLINK2 memory cap where used and sets virtual-memory guard |
| `--tmp-dir` | tool spill directory under approved run root |
| `--log-dir` | log capture directory |

Large GRM jobs can be storage-heavy. Ordinary Linux server caps are pre-submit and process-level guards, not scheduler-side isolation.

## Output contract

Relationship matrix outputs:

| Path | Meaning |
|---|---|
| `results/grm/run_manifest.json` | inputs, resources, tools, outputs, and safety notes |
| `results/grm/audit_sidecar.json` | run context for report and audit packaging |
| `results/grm/marker_standardization.md` | marker and backend context |
| `results/grm/grm_matrix.tsv` | text matrix or pointer file |
| `results/grm/grm_ids.tsv` | matrix sample order |
| `reports/grm_qc.md` | matrix QC summary |

Prediction outputs:

| Path | Meaning |
|---|---|
| `results/prediction/run_manifest.json` | inputs, resources, tools, outputs, and safety notes |
| `results/prediction/audit_sidecar.json` | run context for report and audit packaging |
| `results/prediction/cohort_alignment.json` | genotype/phenotype/covariate/pedigree alignment summary |
| `results/prediction/model_family.md` | model route statement |
| `results/prediction/model_spec.json` | model input summary |
| `results/prediction/predictions.tsv` | first-pass predicted values |
| `results/prediction/validation_plan.md` | validation requirements |
| `results/prediction/metrics.tsv` | metric table |
| `reports/genomic_prediction_summary.md` | human-readable summary |

## Failure handling

Pre-submit blockers:

- missing genotype matrix
- missing phenotype table for prediction
- no PLINK2/GCTA backend available for requested relationship outputs
- missing `gcta64` for current executable prediction path
- non-POSIX paths
- resource request above configured caps
- output overwrite without approval

Safe automatic actions:

- create result, report, log, and tmp directories inside approved run root
- convert VCF to temporary PLINK dataset when backend support exists
- write manifest and audit sidecar in dry-run mode

Breaker conditions:

- matrix ID order cannot be established
- phenotype/genotype/GRM IDs cannot be reconciled
- no model step executed
- automatic breeding selection or culling decision
- treating first-pass GCTA output as validated deployment evidence

## Cross-links

Use these knowledge assets when planning or explaining this directory:

- `references/analysis_domains/relationship_matrix_variance_components.md`
- `references/analysis_domains/genomic_prediction_breeding_value.md`
- `references/modeling_guides/genomic_modeling_routes.md`
- `references/evaluation/evaluation_metric_playbook.md`
- `references/parameter_playbooks/grm_resource_baseline.md`
- `references/parameter_playbooks/genomic_prediction_cv_policy.md`
- `references/papers/grm_core_papers_v1.md`
- `references/papers/genomic_prediction_core_papers_v1.md`
