# sop

Owner: `popgen_quantgen`; ingestion entries owned by `llm_orchestrator`; HPC entries owned by `hpc_scheduler`

Purpose:
- Store local standard operating procedures used by planning, execution review, safety gates, report review, and knowledge updates.

Current SOP library:
- `genotype_processing_execution_sop.md`
- `population_genetics_execution_sop.md`
- `quantitative_genetics_execution_sop.md`
- `association_mapping_execution_sop.md`
- `reporting_audit_execution_sop.md`
- `qc_pipeline_stage_sop_v1.md`
- `pca_pipeline_stage_sop_v1.md`
- `grm_builder_stage_sop_v1.md`
- `genomic_prediction_stage_sop_v1.md`
- `grobid_pdf_ingestion_sop.md`
- `knowledge_update_sop.md`
- `report_review_sop.md`
- `hpc_execution_sop.md`

SOP authoring rule:
- Blueprint stage SOPs should include input thresholds, default parameters, manual confirmation points, and disable conditions.
- Knowledge and report SOPs must make traceability and copyright/data boundaries explicit.
- New formal Markdown files must include `knowledge_item.v2`.
