# Default QC Threshold Profile

## Missingness threshold policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_missingness_thresholds
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Default missingness thresholds are starting points for dry-run planning, not universal scientific truth. A common first-pass profile is sample call rate filtering followed by variant call rate filtering, with stricter review for WGS or low-depth sequencing than for dense SNP arrays.

Recommended planning behavior:
- Show both sample missingness and variant missingness as separate gates.
- Flag high missingness concentration by batch, farm, family, sequencing lane, or chip version.
- Keep pre-filter and post-filter counts in the report index.
- Do not reuse a threshold across species or genotyping platforms without recording the rationale.

Risk boundary: aggressive missingness filtering can remove population subgroups and bias downstream PCA, GRM, GWAS, and genomic prediction.

## MAF and HWE policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_maf_hwe_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Minor allele frequency and Hardy-Weinberg equilibrium filters require context. MAF filtering controls sparse-marker instability, while HWE filtering can identify genotyping artifacts but may be inappropriate in structured, selected, crossbred, or family-based animal populations.

Planning guidance:
- Use MAF as a tunable threshold with report-visible retained marker counts.
- Apply HWE only when the population assumption is defensible.
- For multi-breed cohorts, consider subgroup-aware diagnostics before global HWE removal.
- Record whether the downstream task is QC-only, PCA, GRM, GWAS-like screening, or genomic prediction.

Risk boundary: HWE exclusion can remove true biology under selection or admixture; the report must label this as a review item.

## Heterozygosity and inbreeding outlier policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_heterozygosity_inbreeding
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Heterozygosity and inbreeding outlier checks help detect contamination, sample swaps, low-quality genotypes, and extreme biological relatedness. These checks should be interpreted with breed composition, family structure, and genotyping platform in view.

Execution notes:
- Compute heterozygosity only after basic variant missingness and chromosome filters are applied.
- Compare outliers within breed or management groups when group labels exist.
- Flag outliers for manual review before removal.
- Preserve the exact formula or tool option used for inbreeding estimates.

Risk boundary: a high or low heterozygosity point is not automatically an error; it can reflect crossbreeding, inbreeding, or population history.

## Variant exclusion policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_variant_exclusion_policy
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Variant exclusion should be explainable and reversible. Standard exclusion reasons include missing chromosome, non-autosomal marker when autosomal analysis is requested, duplicated marker ID, duplicated position, allele coding conflict, extreme missingness, and platform-specific artifact flags.

Report requirements:
- Count each exclusion category separately.
- Keep duplicate marker and allele conflict examples in diagnostic output.
- Avoid overwriting the original marker map.
- Distinguish marker removal for QC from marker pruning for PCA or LD-sensitive analyses.

Risk boundary: duplicate IDs and allele flips can break PLINK, GCTA, and merge operations; they should be surfaced before scheduler submission.

## VCF PLINK BAM derived input policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_vcf_plink_bam_inputs
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

VCF, PLINK, and BAM-derived routes have different QC assumptions. VCF/BCF inputs require genotype field integrity and index availability; PLINK inputs require complete companion files; BAM-derived routes require explicit upstream variant-calling or coverage tooling before GeneAgent treats them as genotype matrices.

Validation reminders:
- Check VCF headers and genotype fields before downstream conversion.
- Check PLINK `.fam` sample IDs against phenotype and pedigree tables.
- Do not claim BAM QC support unless a supported wrapper is selected.
- Record software tools and versions in the audit bundle.

Risk boundary: treating BAM as a ready genotype matrix will create false readiness; BAM-derived inputs should remain diagnostic-only unless a supported conversion pipeline exists.

## Sample anomaly review policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_sample_anomaly_review
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-05-26T00:00:00Z
  owner: popgen_quantgen
```

Sample anomaly review covers missingness outliers, heterozygosity outliers, sex-check mismatches when applicable, pedigree conflicts, duplicate genotypes, cryptic relatedness, and phenotype/genotype merge failures.

Operational policy:
- Treat hard failures, such as duplicate primary sample IDs, as submit blockers.
- Treat statistical outliers as manual-review unless the user has supplied a removal rule.
- Keep removed and retained sample lists as report artifacts.
- Record the reason for every exclusion in an audit-friendly table.

Risk boundary: removing samples can alter population structure, relatedness, and prediction validation; every exclusion should be traceable.
