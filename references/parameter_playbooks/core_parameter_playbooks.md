# Core Parameter Playbooks

## QC defaults playbook

```yaml
knowledge_item.v2:
  doc_id: playbook_qc_defaults
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

QC defaults are conservative planning presets. They should be rendered in dry-run output as proposed parameters with editable thresholds, not as hidden constants.

Default parameter categories:
- sample missingness threshold
- variant missingness threshold
- MAF threshold
- HWE review toggle and threshold if applicable
- duplicate marker and duplicate sample policy
- sex-check, pedigree-check, and heterozygosity review toggles when metadata supports them

Always report retained counts after each major filter and require manual review for threshold changes that remove large sample fractions.

## PCA component policy

```yaml
knowledge_item.v2:
  doc_id: playbook_pca_component_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

PCA component policy controls how many components are plotted, summarized, and proposed for downstream covariate review. It does not automatically add PCs to prediction models.

Preset behavior:
- Plot at least PC1/PC2 and PC3/PC4 when enough components exist.
- Export eigenvalues or variance summaries when the backend provides them.
- Flag metadata association patterns rather than assigning biological labels.
- Treat candidate covariate PCs as manual-review items.

Risk boundary: adding too many PCs can remove signal or create unstable estimates.

## GRM resource baseline

```yaml
knowledge_item.v2:
  doc_id: playbook_grm_resource_baseline
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

GRM construction scales with sample count, marker count, output format, and backend implementation. Resource presets should be shown as estimates and paired with scheduler limits.

Planning fields:
- sample count and marker count after QC
- memory estimate class: small, medium, large, high-risk
- thread count and walltime preset
- scratch/output path capacity check
- output matrix format and downstream consumer

Risk boundary: large GRM jobs can fail late if storage or memory is underestimated; dry-run should call out high-risk matrix sizes before submit.

## Genomic prediction CV policy

```yaml
knowledge_item.v2:
  doc_id: playbook_genomic_prediction_cv_policy
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Cross-validation policy must prevent leakage and produce interpretable metrics. Random folds are acceptable only when relatedness, family, time, herd, and breed structure do not make them misleading for the intended deployment.

Preset options:
- random k-fold for exploratory baseline
- family-aware or sire-family split
- breed/subpopulation stratified split
- time-forward or cohort-forward validation
- external validation when a held-out cohort exists

Risk boundary: random CV in closely related breeding populations often overestimates real-world prediction performance.

## Scheduler resource presets

```yaml
knowledge_item.v2:
  doc_id: playbook_scheduler_resource_presets
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: hpc_scheduler
```

Scheduler resource presets translate blueprint resource classes into SLURM/PBS/SGE-style requests. The playbook should remain conservative because production environments vary by cluster policy.

Preset fields:
- queue or partition target
- walltime
- memory per job or memory per CPU
- CPU/thread count
- scratch directory policy
- job name and log path convention

Risk boundary: queue, QOS, and account names are cluster-specific; they must be configurable and never hard-coded as universal defaults.

## Report artifact retention policy

```yaml
knowledge_item.v2:
  doc_id: playbook_report_artifact_retention
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: parameter_playbook
  updated_at: 2026-05-26T00:00:00Z
  owner: orchestrator
```

Every run should preserve the minimum artifacts needed for traceability: normalized input bundle summary, generated script preview, scheduler command, job ID when submitted, log paths, result inventory, report index, diagnostics, and audit bundle.

Retention guidance:
- Keep large raw entity data outside Git and outside report bundles.
- Store relative artifact paths from the run directory.
- Include checksums for small text artifacts when possible.
- Keep manual confirmation records with the audit trail.

Risk boundary: a successful result without traceability should not be treated as production-ready.

## Command resource matrix for core tools

```yaml
knowledge_item.v2:
  doc_id: playbook_command_resource_matrix
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: expert_opinion
  source: parameter_playbook
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

This matrix gives GeneAgent a conservative first-pass resource vocabulary for command preview, remote-shell wrappers, and report explanations. Values are planning presets for ordinary Linux servers or scheduler submissions; they are not universal scientific defaults.

| Workflow | Tool | Input size trigger | Default CPU/threads | Memory estimate | Walltime preset | Command flag or wrapper field | Primary output | Breaker condition |
|---|---|---|---|---|---|---|---|---|
| genotype QC | PLINK2 | SNP-chip or PLINK/VCF cohort up to moderate livestock scale | `--threads 8-16` | `--memory 32768-65536` MB | `02:00:00-06:00:00` | `--threads`, `--memory-mb`, `--tmp-dir` | sample/variant QC tables, retained dataset pointer | missing genotype triplet, sample ID mismatch, output overwrite, resource request above cap |
| VCF normalization/stats | bcftools | bgzipped/indexed VCF; large WGS VCF requires review | `--threads 4-16` where supported | `16-128` GB depending on sites and samples | `02:00:00-12:00:00` | `--threads`, `TMPDIR`, run-local output path | `bcftools.stats.txt`, normalized VCF only when authorized | uncompressed or unindexed VCF, unknown reference assembly, raw data copy outside work root |
| PCA/LD/ROH | PLINK2 | post-QC genotype matrix | `--threads 8-16` | `32-128` GB | `02:00:00-12:00:00` | `--threads`, `--memory`, pruning/window flags | eigenvectors, LD summaries, ROH segments | missing LD pruning policy, automatic population labels, marker density too low for requested statistic |
| GRM/REML | GCTA | post-QC PLINK input; memory scales with sample count | `--thread-num 8-32` | `64-256` GB for medium jobs; higher requires manual review | `06:00:00-24:00:00` | `--thread-num`, GRM prefix, REML phenotype/covariate files | GRM binary/text outputs, REML summaries, sample-order files | matrix dimension mismatch, phenotype mismatch, REML convergence failure, storage estimate above cap |
| first-pass GWAS | PLINK2 `--glm` or reviewed mixed-model backend | genotype + phenotype + covariates | `--threads 8-16` | `32-128` GB | `02:00:00-12:00:00` | `--glm`, phenotype/covariate fields, memory/thread flags | association result files, model spec, metrics | missing trait, unreviewed covariates, no population correction when required, causal claims without validation |
| genomic prediction CV | GCTA/Rscript/reviewed model backend | genotype + phenotype + validation split | `8-32` threads according to backend | `64-256` GB | `06:00:00-24:00:00` | explicit split file, model family, seed, thread flags | GEBV table, validation metrics, bias/calibration report | leakage-prone split, missing validation, auto-changing sample filters, deployment decision without review |
| reporting/audit | shell/Rscript/Python report helpers | existing results/logs only | `1-4` threads | `4-16` GB | `00:30:00-02:00:00` | report root, task/run/session IDs, log paths | `report_index.json`, summary report, traceability bundle | secrets in logs, writing outside run root, overwriting upstream scientific artifacts |

For a 96-core/1 TB ordinary server, default automated plans should still stay conservative: no more than 32 CPU threads, 256 GB memory, 24 hours walltime, and two concurrent trusted shell runs unless the operator explicitly changes local caps. The breaker policy has priority over throughput.
