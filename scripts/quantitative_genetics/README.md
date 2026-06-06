# quantitative_genetics

Execution wrappers for relationship matrices, variance components, and breeding-value prediction.

Detailed operation guide:
- `operation_guide.md`

Entrypoints:
- `run_relationship_matrix.sh`
- `run_breeding_value_prediction.sh`

Compatibility blueprints:
- `grm_builder`
- `genomic_prediction`

Notes:
- Association mapping is separated into `scripts/association_mapping/`.
- Reusable modeling policy belongs in `src/pipeline/` and `references/modeling_guides/`; this directory stays as a thin executable wrapper layer.
- Scientific-domain knowledge for this directory is maintained in `references/analysis_domains/relationship_matrix_variance_components.md` and `references/analysis_domains/genomic_prediction_breeding_value.md`.
- Current prediction execution is a first-pass GCTA-compatible path; ssGBLUP, Bayesian/ML models, and breeding decisions remain reviewed downstream tasks until separate contracts exist.
