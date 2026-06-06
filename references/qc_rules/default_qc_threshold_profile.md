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

## Sex, duplicate, and relatedness check policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_sex_duplicate_relatedness_checks
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Sex checks, duplicate checks, and relatedness checks are sample-identity safeguards. They should be planned before population structure, GRM, GWAS, or genomic prediction because a small number of swapped or duplicated samples can dominate downstream inference.

Use these checks when supported by species, chromosome annotation, and tool capability:
- sex check from sex chromosome genotype patterns when reliable sex chromosome coordinates exist
- duplicate genotype detection from identity-by-state or pairwise similarity
- cryptic relatedness screening before PCA or validation splitting
- pedigree-genomic consistency review when pedigree is supplied

Planning rules:
- Do not run sex checks on species/builds where sex chromosome coding is unknown or unreliable without a caveat.
- Treat duplicate primary sample IDs as blocking.
- Treat nearly identical genotypes with different IDs as manual-review unless the user supplied replicate policy.
- Treat close relatives as expected biology in family datasets but a validation-leakage risk in random splits.
- Preserve the pairwise relatedness or duplicate evidence table.

Risk boundary: sex or duplicate flags are high-impact sample decisions. Automatic removal requires an explicit rule; otherwise GeneAgent should block or request review before submit.

## Batch and platform missingness review policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_batch_platform_missingness_review
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Missingness should be reviewed by batch and platform whenever metadata are available. In animal datasets, chip version, sequencing lane, farm, breed, family, and operator batch can be confounded with biology.

Required summaries when metadata exist:
- sample missingness by batch, chip, sequencing lane, farm, breed, line, or family
- variant missingness by chromosome and marker source
- retained sample and marker counts per group before and after filtering
- extreme groups that would be disproportionately removed by a global threshold
- whether missingness correlates with phenotype or case/control status

Review rules:
- global thresholds are allowed as defaults but must show subgroup impact
- group-specific thresholds require manual justification
- filtering that removes an entire breed, line, family, or batch must trip a review gate
- downstream PCA, GRM, GWAS, and prediction reports should inherit the missingness caveat

Risk boundary: missingness can encode platform or environment. Filtering it away without subgroup accounting can turn technical bias into biological-looking signal.

## Filter order and count audit policy

```yaml
knowledge_item.v2:
  doc_id: qc_rule_filter_order_and_count_audit
  version: v2
  species: multi_species
  blueprint_scope: genotype_processing
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

QC filters must be ordered and counted so the run can be replayed. The same set of filters in a different order can produce different retained samples or markers, especially when sample and variant missingness interact.

Minimum audit columns:
- filter step number
- filter name and exact parameter
- input sample count and output sample count
- input marker count and output marker count
- excluded sample or marker list path when available
- rationale and downstream consequence

Recommended order for first-pass planning:
1. input/sidecar/ID integrity checks
2. duplicate ID and gross format blockers
3. sample missingness
4. variant missingness
5. chromosome/marker-class selection
6. MAF and optional HWE with population caveats
7. heterozygosity, relatedness, sex, and pedigree review
8. task-specific pruning or thinning, such as LD pruning for PCA

Report rules:
- distinguish QC filtering from LD pruning, GWAS marker inclusion, or imputation quality filtering
- keep pre-filter and post-filter manifests
- do not overwrite the original dataset
- show operator-reviewed filters separately from automatic defaults

Risk boundary: an undocumented filter sequence breaks reproducibility and can hide sample or marker exclusion bias.
