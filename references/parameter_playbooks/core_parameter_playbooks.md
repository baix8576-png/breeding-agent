# Core Parameter Playbooks

## QC defaults playbook

```yaml
knowledge_item.v2:
  doc_id: playbook_qc_defaults
  version: v2
  species: multi_species
  blueprint_scope: qc
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
  blueprint_scope: pca
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
  blueprint_scope: grm
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
  blueprint_scope: genomic_prediction
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
  blueprint_scope: shared
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
  blueprint_scope: shared
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
