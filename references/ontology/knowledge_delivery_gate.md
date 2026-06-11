# Knowledge Delivery Gate

This file defines delivery-time knowledge gates for the GeneAgent knowledge base. These gates are operator-facing SOP knowledge blocks used by retrieval, review, and audit workflows. They do not replace runtime safety code.

## Delivery Gate 01 - Input Bundle Ownership

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_input_bundle_ownership
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: every run must identify the owner, working directory, genotype-like inputs, phenotype table, covariate table, pedigree relationship file if present, and expected outputs before any executable template is materialized. Missing ownership blocks automatic execution and routes the request to an intake clarification.

## Delivery Gate 02 - Sample ID Reconciliation

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_sample_id_reconciliation
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: genotype sample IDs, phenotype IDs, covariate IDs, and pedigree IDs must be reconciled before QC, association mapping, GRM construction, or prediction. GeneAgent may report missing and duplicate IDs, but it must not silently drop animals or rewrite identifiers without operator approval.

## Delivery Gate 03 - Path Encoding and Line Ending Policy

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_path_encoding_line_endings
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: architect
```

Rule: generated scripts and sidecars must use POSIX-style path separators, UTF-8 text, LF line endings, and `#!/usr/bin/env bash`. Windows-style separators in a remote execution plan are a preflight failure because they can materialize invalid server paths.

## Delivery Gate 04 - Genotype QC Threshold Review

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_genotype_qc_threshold_review
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: missingness, allele-frequency, heterozygosity, Hardy-Weinberg, sex-check, duplicate-sample, duplicate-marker, and chromosome filters must be visible in the dry-run report. Species and platform context may change thresholds, but threshold changes must be recorded as a parameter decision.

## Delivery Gate 05 - Variant Filter Audit

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_variant_filter_audit
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: variant counts before and after each QC step must be retained in summary logs. A filter that removes an unexpectedly large fraction of markers triggers operator review before downstream population or quantitative analyses proceed.

## Delivery Gate 06 - Format Conversion Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_format_conversion_boundary
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: conversion between genotype formats must preserve sample order, chromosome naming, allele coding, missing genotype representation, and reference genome notes. The report must state whether allele orientation was checked or left as an operator responsibility.

## Delivery Gate 07 - Imputation and Phasing Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_imputation_phasing_boundary
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: imputation and phasing may only be treated as production-ready when the reference panel, target density, species, breed composition, and accuracy metrics are documented. Otherwise GeneAgent may create a planning card but must not claim validated genotype recovery.

## Delivery Gate 08 - PCA Pruning Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_pca_pruning_readiness
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: PCA should use a documented pruned marker set unless the operator intentionally requests unpruned exploratory visualization. The output must separate technical outlier detection from biological population interpretation.

## Delivery Gate 09 - Population Label Review

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_population_label_review
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: clusters must not be named as breeds, lines, ecotypes, or ancestry groups unless metadata supports the label. Reports should use neutral terms such as PC outlier, cluster, or stratification axis when biological labels are uncertain.

## Delivery Gate 10 - Relatedness and Kinship Sanity Check

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_relatedness_kinship_sanity_check
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: pairwise relatedness or kinship summaries must be inspected before association mapping and prediction. Unexpected duplicates, parent-offspring signals, or extreme inbreeding estimates require review because they can inflate association statistics or validation accuracy.

## Delivery Gate 11 - LD and ROH Window Policy

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_ld_roh_window_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: linkage-disequilibrium and runs-of-homozygosity windows must be chosen with marker density, breed history, and chromosome length in mind. A single default window is not transferable across cattle, pig, poultry, small ruminant, and aquaculture panels without validation.

## Delivery Gate 12 - Selection Signature Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_selection_signature_boundary
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: selection-scan results are candidate regions, not causal evidence. Reports must distinguish method signal, population contrast, marker density, and annotation evidence, and must avoid direct causal claims without independent validation.

## Delivery Gate 13 - GRM Sample Order

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_grm_sample_order
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: genomic relationship matrices must retain a sidecar that records sample order, marker filter, allele-frequency basis, and software command. Any downstream model must use the same sample order or explicitly remap it.

## Delivery Gate 14 - REML Model Review

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_reml_model_review
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: REML or mixed-model variance estimates must name the trait, fixed effects, random effects, relationship matrix, convergence status, and excluded samples. Non-convergence, boundary estimates, or implausible heritability require operator review.

## Delivery Gate 15 - Genomic Prediction Validation

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_genomic_prediction_validation
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: prediction accuracy must be reported with validation design, fold assignment, relatedness leakage notes, trait transformation, metric definition, and uncertainty where possible. Random cross-validation is not enough for deployment claims when family or generation leakage is likely.

## Delivery Gate 16 - Single-Step Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_single_step_boundary
  version: v2
  species: multi_species
  blueprint_scope: quantitative_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: single-step models require explicit pedigree depth, genotyped subset, phenotype coverage, compatibility between pedigree and genomic relationships, and software support. If those elements are incomplete, GeneAgent should propose a plan rather than generate a production run.

## Delivery Gate 17 - GWAS Trait Contract

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_gwas_trait_contract
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: every association run must record trait type, phenotype transformation, covariates, population structure correction, relationship correction, sample count, marker count, and multiple-testing policy before execution.

## Delivery Gate 18 - GWAS Covariate and PC Policy

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_gwas_covariate_pc_policy
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: covariates and principal components must be checked for missingness, rank deficiency, and biological interpretability. GeneAgent may suggest diagnostics but must not silently remove covariates to force model fitting.

## Delivery Gate 19 - QTL and Fine-Mapping Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_qtl_finemapping_boundary
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: QTL overlap and fine-mapping annotations must state genome build, interval definition, LD context, candidate-gene source, and whether evidence is positional, functional, or literature-supported. Overlap alone is not causal validation.

## Delivery Gate 20 - Functional Annotation Trace

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_functional_annotation_trace
  version: v2
  species: multi_species
  blueprint_scope: association_mapping
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: functional annotation outputs must retain source database, genome build, version date, and mapping rule. Reports must label annotation as interpretive context unless experimental or high-confidence functional evidence is present.

## Delivery Gate 21 - Cattle Overlay Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_species_cattle_overlay_readiness
  version: v2
  species: cattle
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: cattle workflows must separate dairy, beef, taurine, indicine, and crossbred contexts where relevant. Genomic prediction, pangenome, and regulatory interpretation should cite verified cattle-specific evidence before production claims.

## Delivery Gate 22 - Pig Overlay Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_species_pig_overlay_readiness
  version: v2
  species: pig
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: pig workflows must respect commercial line, crossbred, meat-quality, reproductive, and immune-trait contexts. Reference population composition should be visible in prediction and association reports because transfer across lines may be weak.

## Delivery Gate 23 - Poultry Overlay Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_species_poultry_overlay_readiness
  version: v2
  species: chicken
  blueprint_scope: association_mapping
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: poultry analyses must account for layer, broiler, local breed, and experimental population structure. Reports should avoid transferring mammalian marker-density assumptions to poultry without species-specific evidence.

## Delivery Gate 24 - Small Ruminant Overlay Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_species_small_ruminant_overlay_readiness
  version: v2
  species: sheep_goat
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: sheep and goat analyses must distinguish wool, milk, meat, reproduction, and adaptation goals. Breed structure and local adaptation can dominate signal interpretation, so population context belongs in the report summary.

## Delivery Gate 25 - Aquaculture Overlay Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_species_aquaculture_overlay_readiness
  version: v2
  species: aquaculture
  blueprint_scope: quantitative_genetics
  evidence_level: expert_opinion
  source: internal_note
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: aquaculture analyses must name the species, breeding design, family structure, ploidy or sex-system concerns where relevant, and trait environment. Cross-species defaults are unsafe because fish and shrimp panels vary sharply in genome resources and family structure.

## Delivery Gate 26 - Remote Shell Preflight

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_remote_shell_preflight
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: hpc_scheduler
```

Rule: ordinary Linux server execution requires successful SSH preflight, writable work root inside the operator-owned area, required shell utilities, tool path checks, and resource caps before `ssh_shell_trusted` execution is enabled.

## Delivery Gate 27 - Queue Backend Fallback

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_queue_backend_fallback
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: hpc_scheduler
```

Rule: SLURM, PBS, and manual workbench paths are optional execution backends, not the default assumption for every server. When queue commands are absent, GeneAgent should use ordinary trusted shell mode if configured, or produce a manual card.

## Delivery Gate 28 - Resource Caps Enforcement

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_resource_caps_enforcement
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: CPU, memory, walltime, and concurrency caps are pre-submit gates. A request above configured caps must stop before remote script creation; the operator can lower scope or explicitly reconfigure local-only settings.

## Delivery Gate 29 - Tool Path Manifest

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_tool_path_manifest
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: hpc_scheduler
```

Rule: executable paths for PLINK, PLINK2, bcftools, GCTA, Rscript, and reporting helpers must be resolved before run submission. Unknown tools trip a breaker instead of falling back to a shell lookup that may pick the wrong environment.

## Delivery Gate 30 - Log and State Sentinels

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_log_state_sentinels
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: orchestrator
```

Rule: every trusted run must preserve stdout, stderr, wrapper script, state sentinels, exit code, start time, end time if known, and local run state path. Missing state with no live process is ambiguous and requires operator review.

## Delivery Gate 31 - Safe Repair Policy

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_safe_repair_policy
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: automatic repair is limited to low-risk actions such as creating missing run-local directories, retrying transient connection failures, generating sidecars, and increasing resources inside caps. Data-filter changes, overwrite actions, and unknown-tool substitutions require human approval.

## Delivery Gate 32 - Retry Budget Policy

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_retry_budget_policy
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: repeated failures with the same signature must stop after the configured retry budget. The diagnostic report should include the last command summary, log excerpt, likely cause, safe repair options, and whether retry is blocked.

## Delivery Gate 33 - Output Overwrite Protection

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_output_overwrite_protection
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: GeneAgent must not delete or overwrite previous results during automatic execution. Re-runs should use a new run ID or require an operator-approved overwrite policy recorded in audit.

## Delivery Gate 34 - Report Index Completeness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_report_index_completeness
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: orchestrator
```

Rule: report indexes must include run context, blueprint summary, input summary, output collections, diagnostics, traceability, and a concise interpretation summary. Reports that lack traceability are draft artifacts, not delivery artifacts.

## Delivery Gate 35 - Audit Bundle Traceability

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_audit_bundle_traceability
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: orchestrator
```

Rule: audit bundles must preserve input summary, planning summary, command summary, job or process handle, log paths, manual confirmation records, and knowledge evidence references. This makes reruns and troubleshooting possible after context changes.

## Delivery Gate 36 - Diagnostic Report Readiness

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_diagnostic_report_readiness
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: diagnostic reports must include observed symptom, matched pattern, likely cause, safe repair, breaker rule, retry status, and operator action. A diagnostic that only repeats the tool error is incomplete.

## Delivery Gate 37 - Literature Evidence Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_literature_evidence_boundary
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

Rule: peer-reviewed cards may support report claims when DOI, PMID, or publisher metadata are present. Non-export candidates are retrieval leads only and must not be cited as verified evidence.

## Delivery Gate 38 - Local Knowledge Index Health

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_local_knowledge_index_health
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: llm_orchestrator
```

Rule: the reference index must build without metadata errors, duplicate document identifiers, or missing trace fields. Retrieval output used for plans or reports must keep document ID, source path, section anchor, evidence level, and reason for use.

## Delivery Gate 39 - Source Fetch Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_source_fetch_boundary
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: llm_orchestrator
```

Rule: external source fetching is allowed only when local knowledge coverage is insufficient and the safety gate permits it. Fetched source summaries must not store restricted full text in the versioned repository.

## Delivery Gate 40 - No Raw Data in Version Control

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_no_raw_data_in_version_control
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: versioned references may contain summaries, SOPs, templates, and metadata, but not raw biological datasets, restricted full text, generated local indexes, private credentials, or server-specific secrets.

## Delivery Gate 41 - Credential-Free Artifacts

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_credential_free_artifacts
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: safety_fuse
```

Rule: reports, logs, state files, examples, and tracked documentation must not include credentials, private keys, local-only secrets, or private server addresses. Operator-local configuration belongs in ignored local files.

## Delivery Gate 42 - Script Resource Controls

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_script_resource_controls
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: test_eval
```

Rule: executable templates must expose thread, memory, walltime, and output-directory controls where applicable. Unlimited commands are not acceptable in trusted remote execution.

## Delivery Gate 43 - Operation Guide Bridge

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_operation_guide_bridge
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: orchestrator
```

Rule: each script folder must have an operation guide that links SOPs, parameter playbooks, failure diagnostics, expected outputs, and report handoff. Thin scripts remain understandable only when those bridges are maintained.

## Delivery Gate 44 - PC to Server Workflow

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_pc_to_server_workflow
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: hpc_scheduler
```

Rule: the primary user workflow is PC Agent control plane to ordinary Linux server execution plane through trusted SSH. Desktop tools may help manual login or file transfer, but production automation should not depend on GUI clicking.

## Delivery Gate 45 - Handoff Completion Rule

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_handoff_completion_rule
  version: v2
  species: multi_species
  blueprint_scope: reporting_audit
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: orchestrator
```

Rule: a meaningful stage is not complete until the handoff file records completed, not-yet-done, verification, gate result, and next actions. This rule prevents context loss after a new window or compaction.

## Delivery Gate 46 - Delivery Acceptance Summary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_acceptance_summary
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: orchestrator
```

Rule: the GeneAgent knowledge base is delivery-ready only when the index builds cleanly, content floors pass, recent literature is either verified or marked non-export, script resources are bounded, diagnostics cover major failures, and audit/report traceability is intact.

## Delivery Gate 47 - Expansion Boundary

```yaml
knowledge_item.v2:
  doc_id: delivery_gate_expansion_boundary
  version: v2
  species: multi_species
  blueprint_scope: knowledge_governance
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: architect
```

Rule: future multi-omics, pangenome, single-cell, foundation-model, and knowledge-graph capabilities should extend existing modules and knowledge scopes rather than create parallel root directories or bypass existing contracts.
