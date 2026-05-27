# qc_rules

Owner: `popgen_quantgen`

Purpose:
- Store QC threshold guidance, genotype/sample anomaly rules, and input-format cautions.
- Support the `qc` blueprint and upstream readiness checks for PCA, GRM, and genomic prediction.

Formal knowledge files:
- `default_qc_threshold_profile.md`: missingness, MAF/HWE, heterozygosity, variant exclusion, VCF/PLINK/BAM-derived input, and sample anomaly policies.

Maintenance notes:
- Thresholds are planning defaults unless project SOP says otherwise.
- Expert-opinion entries must keep risk boundaries visible.
- New formal Markdown files must include `knowledge_item.v2`.
