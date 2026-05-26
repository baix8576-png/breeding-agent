# references index

This directory stores the Git-tracked layer of the GeneAgent 知识库 for genetics workflow design, interpretation boundaries, report packaging, and literature-backed planning.

Current status:
- Documents in this tree are copyright-safe summaries, templates, SOPs, and curated paper cards.
- Original PDFs, extracted full text, chunks, and indexes belong under `.geneagent/knowledge/*` and are not committed.
- Pipeline blueprints may point to these files as human-readable and retrieval-ready companions.

Subdirectories:
- `input_specs/`: expected file roles, naming patterns, and dataset bundle templates.
- `qc_rules/`: placeholder thresholds, anomaly review checklists, and QC decision notes.
- `structure_analysis/`: PCA interpretation notes, cluster-labeling cautions, and stratification guidance.
- `modeling_guides/`: genomic prediction route notes and model-family decision templates.
- `evaluation/`: correlation, bias, cross-validation, subgroup validation guidance, and runtime diagnostics playbooks.
- `report_templates/`: markdown templates for QC, structure, and genomic prediction summaries.
- `papers/`: curated paper notes, method evidence extracts, and citation-ready summaries.
- `sop/`: project-local SOP and execution standards used by runtime planning and review.
- `parameter_playbooks/`: reusable parameter baselines, tuning boundaries, and model presets.
- `failure_cases/`: postmortem-style failure records with trigger, diagnosis, and recovery actions.
- `ontology/`: controlled vocabulary, concept mapping, and metadata schema definitions.

Diagnostics entrypoint:
- `evaluation/diagnostics/README.md`: stable markdown schema (`diagnostics_v1`) for pattern-based troubleshooting knowledge.
- `evaluation/diagnostics/scheduler_error_patterns.md`: common SLURM/PBS submit and poll failures with executable remediation steps.
- `evaluation/diagnostics/bio_tool_error_patterns.md`: common `plink2`/`bcftools`/`vcftools`/`gcta64` failures with executable remediation steps.

Metadata standard:
- `ontology/knowledge_item.v2.md`: required field contract for knowledge assets (`doc_id/version/species/blueprint_scope/evidence_level/source/updated_at/owner`).

Current paper seed packs:
- `papers/qc_core_papers_v1.md`
- `papers/pca_core_papers_v1.md`
- `papers/grm_core_papers_v1.md`
- `papers/genomic_prediction_core_papers_v1.md`
- `papers/animal_genomics_classic_landmarks.md`
- `papers/animal_genomics_recent_high_impact_2022_2026.md`
- `papers/species_literature_index.md`

Literature curation policy:
- `ontology/literature_curation_policy.md`
- Public-facing name: `GeneAgent 知识库`
- Development-history labels (`V1`, `V1.5`, `V2`) must not replace the user-facing knowledge-base name.

PDF ingestion SOP:
- `sop/grobid_pdf_ingestion_sop.md`

Blueprint stage SOP library (M2-04):
- `sop/qc_pipeline_stage_sop_v1.md`
- `sop/pca_pipeline_stage_sop_v1.md`
- `sop/grm_builder_stage_sop_v1.md`
- `sop/genomic_prediction_stage_sop_v1.md`

Conventions:
- Keep thresholds and modeling choices explicitly marked as project-specific until validated by SOPs.
- Reference files should explain assumptions, not hide them.
- If a blueprint depends on a reference file, list the exact file path inside the blueprint asset index.
