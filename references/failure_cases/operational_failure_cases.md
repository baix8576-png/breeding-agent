# Operational Failure Cases

## Scheduler account partition mismatch

```yaml
knowledge_item.v2:
  doc_id: failure_scheduler_account_partition_mismatch
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: incident_verified
  source: failure_case
  updated_at: 2026-05-26T00:00:00Z
  owner: hpc_scheduler
```

Symptom: SLURM or PBS rejects a job before execution because the account, partition, queue, project, or QOS is invalid for the user.

Safe response:
- Do not retry with guessed account names.
- Show the submitted resource block and scheduler message.
- Ask the operator to select an approved queue/account mapping.
- Preserve the failed script and scheduler output for audit.

Retry boundary: only retry after the account/partition mapping is confirmed.

## Bio tool missing sidecar failure

```yaml
knowledge_item.v2:
  doc_id: failure_bio_tool_missing_sidecar
  version: v2
  species: multi_species
  blueprint_scope: qc
  evidence_level: incident_verified
  source: failure_case
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Symptom: `plink2`, `bcftools`, `vcftools`, or `gcta` fails because a required companion file or index is absent.

Safe response:
- Identify the expected sidecar, such as `.bim/.fam`, `.pvar/.psam`, `.tbi`, `.csi`, or GRM companion files.
- Stop submit flow until the sidecar exists or a generation step is explicitly approved.
- Record tool command, working directory, and file inventory.

Retry boundary: do not retry the same command without changing the file inventory.

## ID consistency failure

```yaml
knowledge_item.v2:
  doc_id: failure_id_sample_consistency
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: incident_verified
  source: failure_case
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Symptom: genotype, phenotype, covariate, and pedigree sample IDs do not intersect as expected, or duplicate IDs prevent stable joins.

Safe response:
- Report counts and examples for every unmatched side.
- Do not auto-normalize IDs.
- Require a mapping table or user-approved harmonization rule.
- Keep original and normalized IDs in separate columns if harmonization proceeds.

Retry boundary: model execution remains blocked until duplicate and unmatched critical IDs are resolved or explicitly scoped out.

## Report traceability failure

```yaml
knowledge_item.v2:
  doc_id: failure_report_traceability_missing
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: incident_verified
  source: failure_case
  updated_at: 2026-05-26T00:00:00Z
  owner: orchestrator
```

Symptom: an analysis produced output files but cannot produce a complete `report_index.v2`, audit bundle, or source-to-artifact trace.

Safe response:
- Treat the run as incomplete for production.
- Locate missing run context, input summary, script preview, job ID, log paths, and result inventory.
- Regenerate the report index only from audited artifacts.
- Do not backfill unverifiable metadata as if it were observed.

Retry boundary: a run can be accepted only after report traceability is restored or the limitation is documented as blocking.

## Knowledge retrieval failure

```yaml
knowledge_item.v2:
  doc_id: failure_knowledge_retrieval_gap
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: incident_verified
  source: failure_case
  updated_at: 2026-05-26T00:00:00Z
  owner: llm_orchestrator
```

Symptom: a planner or answer path cannot retrieve local evidence for a parameter, failure diagnosis, or report explanation.

Safe response:
- Declare local coverage gap instead of fabricating a rule.
- Show retrieval filters and empty or low-confidence hits.
- Use external fallback only if the safety gate allows it.
- Add a curated reference card after the answer path is reviewed.

Retry boundary: do not use a low-confidence retrieval hit as a hard production recommendation.

## Raw data boundary violation

```yaml
knowledge_item.v2:
  doc_id: failure_raw_data_boundary_violation
  version: v2
  species: multi_species
  blueprint_scope: shared
  evidence_level: incident_verified
  source: failure_case
  updated_at: 2026-05-26T00:00:00Z
  owner: safety_fuse
```

Symptom: raw VCF, BAM, FASTQ, FASTA, or large private entity data is about to be committed, copied outside the approved workspace, or sent to an external service.

Safe response:
- Stop the operation and require manual review.
- Keep only paths, counts, schemas, and non-sensitive summaries in Git assets.
- Move raw files to approved local or cluster storage when needed.
- Record the attempted action and resolution in audit notes.

Retry boundary: any operation that moves raw entity data must be explicitly approved and stay within the cluster/local policy.
