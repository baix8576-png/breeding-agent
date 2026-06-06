# Current Workflow And File Map

This document is the compact alignment map for the current GeneAgent V2 worktree. Use it when deciding where a change belongs, which file owns a behavior, and whether a request is executable, knowledge-only, or report-only.

Authoritative hierarchy:

1. `AGENTS.md` owns permanent architecture, safety, directory, and handoff rules.
2. `docs/v2_system_map.md` owns the broad V2 system view.
3. This file maps the current workflow to concrete files and current execution boundaries.
4. `docs/HANDOFF.md` records session continuity and gate evidence; it is not a truth source by itself.

## End-To-End Workflow

| Stage | Purpose | Primary owner files | Must not own |
|---|---|---|---|
| `Intake` | Normalize `request_text`, `working_directory`, task/run/session context, and input entries. | `src/runtime/facade.py`, `src/contracts/api.py`, `src/contracts/common.py`, `src/contracts/envelope.py`, `src/cli/app.py`, `src/api/routes/tasks.py` | Tool implementation, script internals, or scientific interpretation. |
| `Intent + Scope` | Route the request as `bioinformatics`, `system`, or `knowledge`. | `src/orchestration/router.py`, `src/orchestration/service.py`, `src/orchestration/workflow.py` | Scheduler submit or direct file mutation. |
| `Input Validation` | Convert paths and sidecars into an `InputBundle`, then check VCF/PLINK/BAM, phenotype, covariate, and pedigree consistency. | `src/pipeline/validators.py`, `references/input_specs/`, `references/qc_rules/` | Guessing sample ID transforms or applying irreversible filters. |
| `Local-first RAG` | Retrieve local evidence, SOPs, diagnostics, templates, and domain boundaries before planning. | `src/knowledge/`, `references/`, `.geneagent/knowledge/` runtime cache | Storing static SOP text in `src/knowledge/` or committing runtime indexes. |
| `Blueprint Selection` | Bind executable bio requests to compatibility blueprints and stage contracts. | `src/pipeline/catalog.py`, `src/pipeline/packs/builtin_blueprints.py`, `src/pipeline/workflows.py`, `src/pipeline/execution.py` | Treating blueprint names as the animal-genomics scientific taxonomy. |
| `Resource + Safety Gate` | Estimate resources, enforce write boundaries, block unsafe actions, and prepare dry-run/submit preview. | `src/scheduler/resource_estimator.py`, `src/safety/`, `src/runtime/settings.py`, `.env.example` | Bypassing caps, deleting outputs, or weakening filters to force success. |
| `Execution` | Materialize bounded Bash wrappers through local preview, trusted SSH shell, trusted SLURM, or manual fallback. | `src/scheduler/`, `src/runtime/bootstrap.py`, `src/runtime/automation.py`, `src/runtime/run_state.py`, `scripts/` | Embedding scheduler logic inside `scripts/` or putting core orchestration in shell templates. |
| `Artifact + Report` | Collect outputs, logs, figures, diagnostics, report index, and human-readable summaries. | `scripts/reporting_audit/`, `src/runtime/facade.py`, `references/report_templates/`, `references/evaluation/diagnostics/` | Inventing scientific conclusions that are not supported by upstream artifacts. |
| `Audit + Memory` | Persist input summary, planning summary, command, job id, logs, manual confirmations, and handoff state. | `src/audit/`, `src/memory/`, `docs/HANDOFF.md`, `.geneagent/runs/` | Storing secrets, raw entity data, or remote run paths as local filesystem roots. |
| `V2 Control Plane` | Provide stable `/v2/*` API, console, observability, audit export, release gate, release plan, and final review. | `src/api/routes/`, `src/runtime/facade.py`, `docs/release_process_v2.md`, `docs/v2_0_final_acceptance_review.md` | Changing execution behavior without updating contracts and tests. |

The `non-bio lightweight branch` is fixed:

`intake -> local retrieval -> answer blueprint -> optional safety review`

It must not generate scheduler scripts, submit jobs, poll jobs, allocate cluster job ids, or enter trusted remote execution.

## Current File Responsibilities

| Area | Files/directories | Function |
|---|---|---|
| CLI/API entry | `src/cli/app.py`, `src/api/routes/tasks.py` | Parse user/API requests and call runtime facade. Keep entrypoints thin. |
| Runtime assembly | `src/runtime/bootstrap.py`, `src/runtime/facade.py`, `src/runtime/settings.py`, `src/runtime/compat.py` | Wire dependencies, load settings, expose user operations, preserve compatibility envelopes. |
| Contracts | `src/contracts/` | Stable shared data models and enums. Add cross-module fields here first. |
| Orchestration | `src/orchestration/` | Intent routing, workflow planning, and stage sequencing. |
| Pipeline | `src/pipeline/` | Blueprint catalogs, stage contracts, artifact contracts, command planning, and input validation. |
| Scheduler | `src/scheduler/` | Submit/poll/recovery adapters, resource estimates, SSH shell, SLURM/PBS behavior, and scheduler-neutral status. |
| Safety | `src/safety/` | Approval gates, circuit breakers, path/resource/write/data-egress rules. |
| Tools | `src/tools/` | Atomic tool manifests and adapters. Do not define workflow order here. |
| Knowledge code | `src/knowledge/` | Parse, validate, chunk, index, retrieve, and trace knowledge assets. |
| Knowledge assets | `references/` | Git-versioned SOPs, paper cards, domain playbooks, templates, failures, and ontology. |
| Script entrypoints | `scripts/` | Thin executable Bash wrappers only. They receive explicit inputs and resource parameters. |
| Audit/memory | `src/audit/`, `src/memory/`, `docs/HANDOFF.md` | Traceability, durable summaries, and cross-session continuity. |
| Runtime state | `.geneagent/runs/`, `.geneagent/knowledge/` | Local generated state, raw PDFs, extracted text, chunks, and indexes. Not committed. |
| Generated outputs | `results/`, `reports/`, `logs/` | Run outputs and diagnostics. Not architecture or source of truth. |
| Tests | `tests/unit/`, `tests/integration/`, `tests/e2e/` | Verify contracts, routing, scripts, scheduler behavior, remote execution, and docs alignment. |

## CLI And API Operational Surface

CLI commands that should remain aligned with this map:

- `plan`
- `validate-inputs`
- `dry-run`
- `submit-preview`
- `submit`
- `poll-explain`
- `report`
- `diagnostic`
- `remote-check`
- `remote-session-doctor`
- `remote-session-open`
- `remote-session-check`
- `remote-session-close`
- `remote-session-smoke`
- `remote-password-set`
- `remote-smoke`
- `watch-run`
- `resume-run`
- `audit-export`
- `observability`
- `production-gate`
- `release-plan`
- `final-review`

CLI-only operator-auth commands:

- `remote-session-doctor`
- `remote-session-open`
- `remote-session-check`
- `remote-session-close`
- `remote-session-smoke`
- `remote-password-set`
- `remote-smoke`

These commands touch local SSH control-session state, local ignored `.env` password state, or the fixed harmless smoke submit. They are intentionally not API routes.

API task routes that should remain aligned with this map:

- `/tasks/draft-plan`
- `/tasks/validate-inputs`
- `/tasks/review-action`
- `/tasks/dry-run`
- `/tasks/submit-preview`
- `/tasks/submit`
- `/tasks/poll-explain`
- `/tasks/report`
- `/tasks/diagnostic`
- `/tasks/remote-check`
- `/tasks/watch-run`
- `/tasks/resume-run`
- `/tasks/audit-export`
- `/v2/tasks/draft-plan`
- `/v2/tasks/validate-inputs`
- `/v2/tasks/review-action`
- `/v2/tasks/dry-run`
- `/v2/tasks/submit-preview`
- `/v2/tasks/submit`
- `/v2/tasks/poll-explain`
- `/v2/tasks/report`
- `/v2/tasks/diagnostic`
- `/v2/tasks/remote-check`
- `/v2/tasks/watch-run`
- `/v2/tasks/resume-run`
- `/v2/tasks/audit-export`
- `/v2/release/production-gate`
- `/v2/release/plan`
- `/v2/release/final-review`

## Blueprint, Script, And Domain Alignment

Execution blueprints are compatibility entrypoints. Scientific domains live in `references/analysis_domains/` and `references/ontology/domain_scope_vocab.md`.

| Compatibility blueprint | Executable script | Primary scientific domains | Current boundary |
|---|---|---|---|
| `qc_pipeline` | `scripts/genotype_processing/run_genotype_qc.sh` | `references/analysis_domains/data_preparation_qc.md`, `references/analysis_domains/genotype_processing.md` | Executable for input/QC and first-pass VCF/PLINK checks. Advanced phasing, imputation, liftover, and allele harmonization are planning boundaries until dedicated wrappers exist. |
| `pca_pipeline` | `scripts/population_genetics/run_population_structure_diversity.sh` | `references/analysis_domains/population_structure.md`, `references/analysis_domains/genetic_diversity_inbreeding.md`, `references/analysis_domains/selection_signatures.md` | Executable for PCA, LD, ROH, and limited Fst/pi/Tajima outputs. Not a complete selection-signature workflow. |
| `grm_builder` | `scripts/quantitative_genetics/run_relationship_matrix.sh` | `references/analysis_domains/relationship_matrix_variance_components.md` | Executable for relationship-matrix construction and packaging. Heritability/model interpretation requires model contracts. |
| `association_mapping_gwas` | `scripts/association_mapping/run_gwas.sh` | `references/analysis_domains/association_mapping_gwas_qtl.md` | Executable for first-pass PLINK2 GWAS. QTL, fine mapping, mixed-model GWAS, and causal interpretation are not complete execution paths. |
| `genomic_prediction` | `scripts/quantitative_genetics/run_breeding_value_prediction.sh` | `references/analysis_domains/genomic_prediction_breeding_value.md` | Executable for bounded breeding-value prediction artifacts. Final breeding decisions are outside automation. |
| reporting/audit package | `scripts/reporting_audit/run_report_generator.sh` | `references/analysis_domains/hpc_execution_reporting_audit.md` | Executable for artifact packaging and traceability. It proves provenance, not scientific correctness. |
| report-only interpretation | no dedicated script yet | `references/analysis_domains/functional_genomics_annotation.md` | Knowledge/reporting supported. Gene overlap, consequence annotation, pangenome graph query, SV/CNV annotation, eQTL colocalization, TWAS, and pathway enrichment require future wrappers. |

## Script Directory Rules

Current script directories:

- `scripts/genotype_processing/`
- `scripts/population_genetics/`
- `scripts/quantitative_genetics/`
- `scripts/association_mapping/`
- `scripts/reporting_audit/`

Scripts must:

- use `#!/usr/bin/env bash`
- accept explicit `--threads`, `--memory-mb`, `--tmp-dir`, and `--log-dir`
- write manifests and audit sidecars
- keep raw inputs read-only
- reject Windows backslash paths before execution
- avoid scheduler-specific submit logic
- avoid core planning, safety, or orchestration logic

Historical script directories such as `scripts/qc_pipeline/`, `scripts/pca_pipeline/`, `scripts/grm_builder/`, `scripts/genomic_prediction/`, and `scripts/report_generator/` are compatibility history, not the current layout.

## Trusted Remote Execution Boundaries

Execution modes:

| Mode | Purpose | Submit behavior |
|---|---|---|
| `local_preview` | Safe default. | No real remote submit. |
| `ssh_shell_trusted` | Ordinary Linux server execution through SSH + Bash/nohup. | Real submit only after `remote-check` passes and `GENEAGENT_SCHEDULER_REAL_EXECUTION_ENABLED=true`. |
| `ssh_slurm_trusted` | SLURM-backed HPC execution. | Real `sbatch` only after SLURM checks pass and real execution is enabled. |
| `manual_sbase` | Manual SBASE/web-workbench fallback. | Generates a copyable submit card only. |
| `hpc_local` | Agent runs on HPC login node when explicitly configured. | Uses local scheduler environment. |

Ordinary-server automation must stay inside configured user-owned boundaries:

- `GENEAGENT_HPC_WORK_ROOT`
- `GENEAGENT_REMOTE_ALLOWED_WRITE_ROOTS`
- `GENEAGENT_REMOTE_SHELL_CPU_CAP`
- `GENEAGENT_REMOTE_SHELL_MEMORY_GB_CAP`
- `GENEAGENT_REMOTE_SHELL_WALLTIME_CAP`
- `GENEAGENT_REMOTE_SHELL_MAX_CONCURRENT_RUNS`

Remote run state:

- remote: `<remote_work_root>/<task_id>/<run_id>/run.sh`, `logs/stdout.log`, `logs/stderr.log`, `state/pid`, `state/done`, `state/failed`, `state/exit_code`
- local: `.geneagent/runs/<task_id>/<run_id>/state.json`
- follow-up commands: `watch-run`, `resume-run`

Automation may create directories, write wrapper files for the current run, read logs, retry transient SSH/scheduler failures, and continue only after output validation.

Automation must stop for:

- delete or overwrite of existing results
- sample filtering changes
- path boundary violations
- unknown tools
- resource-cap bypass
- repeated failures
- lost PID without state sentinels
- raw data egress
- secrets in logs, docs, state, examples, or audit records

## Knowledge Layer Alignment

The public knowledge base is the GeneAgent knowledge base. Version labels such as V1, V1.5, and V2 are development history, not user-facing knowledge-base names.

| Layer | Path | Versioned | Purpose |
|---|---|---|---|
| Git knowledge assets | `references/` | yes | Reviewed SOPs, method cards, domain playbooks, templates, failures, ontology, and literature summaries. |
| Local runtime knowledge | `.geneagent/knowledge/` | no | Raw PDFs, GROBID TEI, extracted text, chunks, BM25 indexes, embedding indexes, and private cache. |
| Knowledge code | `src/knowledge/` | yes | Metadata parsing, chunking, indexing, retrieval, rerank, traceability. |

Current domain files:

- `references/analysis_domains/data_preparation_qc.md`
- `references/analysis_domains/genotype_processing.md`
- `references/analysis_domains/population_structure.md`
- `references/analysis_domains/genetic_diversity_inbreeding.md`
- `references/analysis_domains/selection_signatures.md`
- `references/analysis_domains/association_mapping_gwas_qtl.md`
- `references/analysis_domains/functional_genomics_annotation.md`
- `references/analysis_domains/relationship_matrix_variance_components.md`
- `references/analysis_domains/genomic_prediction_breeding_value.md`
- `references/analysis_domains/hpc_execution_reporting_audit.md`

Knowledge items must preserve traceability:

`user_query -> retrieval_filters -> retrieved_doc_id -> chunk_id -> source_path -> page_or_anchor -> evidence_level -> final_answer_or_plan`

## Tightening Checklist For Future Changes

Before editing:

- State `intent_domain`, `stage_id`, `module_owner_path`, `cluster_execution_expected`, and `contracts_impacted`.
- Choose the owning directory from this map and `AGENTS.md`.
- Verify whether the request is executable or only knowledge/report interpretation.
- Check whether the current blueprint already supports the requested operation.

Before claiming completion:

- Run the relevant unit/integration/e2e tests.
- Run `python -m compileall src tests` or the documented `PYTHONPYCACHEPREFIX` fallback on Windows.
- Run `python -m pytest -q` for behavior changes.
- Run `git diff --check -- <changed files>`.
- Update `docs/HANDOFF.md` with `completed_checklist` and `not_yet_done_checklist`.

Do not merge if:

- a change cannot map to a stage and owner file
- core logic moved into `scripts/`
- knowledge assets moved into `src/knowledge/`
- runtime cache or raw data moved into Git
- non-bio paths can enter submit/poll
- trusted remote execution can write outside the configured work root
