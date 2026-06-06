# Genetic Diversity And Inbreeding Domain

This file defines the genetic diversity and inbreeding knowledge domain that is partly executed by `scripts/population_genetics/run_population_structure_diversity.sh` and partly interpreted through reports and relatedness context.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_inbreeding_scope
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `genetic_diversity_inbreeding`.

This domain describes within-population and between-population diversity, LD patterns, heterozygosity, ROH, and inbreeding-related summaries. It is often paired with population structure and relationship-matrix analysis.

Current execution bridge:
- `pca_pipeline` compatibility key for LD, ROH, pi, and structure-linked summaries.
- `grm_builder` compatibility key for relatedness context when GRM outputs are available.
- `scripts/population_genetics/run_population_structure_diversity.sh` for first-pass LD, ROH, and VCFtools summaries.

Not in scope:
- automatic demographic inference
- effective population size claims without a dedicated method
- breed-conservation recommendations without curated species context
- final inbreeding coefficients for breeding decisions without review

Risk boundary: diversity statistics are sensitive to sample design, marker density, ascertainment, reference genome, and breed composition.

## LD decay and marker-density policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_inbreeding_ld_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

LD summaries support PCA pruning, marker-density interpretation, GWAS resolution, imputation caveats, and genomic prediction transferability. They should be reported with population definitions and marker filtering provenance.

Minimum context:
- species and breed or population grouping
- marker source: SNP array, WGS, imputed panel, or pangenome/SV-aware callset
- QC filters applied before LD calculation
- LD window parameters and r2 threshold
- whether related or duplicated animals were removed

Interpretation rules:
- Do not compare LD decay across groups with very different sample sizes without caveats.
- Do not treat LD pruning parameters as universal across species or marker densities.
- Use LD decay to explain power and resolution, not to prove selection by itself.
- Report whether LD output is genome-wide or limited to selected windows.

Risk boundary: LD can reflect demography, selection, genotyping platform, or sampling. A single LD curve is not a complete population-history model.

## ROH and inbreeding policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_inbreeding_roh_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

ROH analyses summarize autozygosity and recent or ancient inbreeding patterns. In livestock, ROH length distributions are shaped by breed history, selection, marker density, genotyping error, and population management.

Planning checks:
- Declare minimum ROH length and SNP count thresholds.
- Record whether LD-pruned or unpruned markers were used; ROH usually needs dense marker information rather than PCA-pruned sets.
- Summarize ROH by length class when possible.
- Keep individual-level and group-level summaries separate.
- Compare FROH with pedigree or GRM-based inbreeding only when those sources are available.

Manual-review conditions:
- extreme ROH burden in a known inbred line
- mixed-breed samples with unusual ROH distribution
- low-density panels where ROH calls may be unstable
- sex chromosome or scaffold handling differences

Risk boundary: high ROH does not automatically mean sample error, and low ROH does not guarantee unrelatedness.

## Pi and heterozygosity policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_inbreeding_pi_heterozygosity_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Nucleotide diversity, observed heterozygosity, expected heterozygosity, and allele-frequency summaries are descriptive statistics. They become meaningful only with population labels, filtering context, and comparable marker sets.

Recommended report fields:
- group sample counts
- window size for pi or Tajima-style summaries
- missingness and MAF filters used before calculation
- autosomal or chromosome-specific scope
- outlier windows separated from genome-wide summaries

Interpretation cautions:
- Low diversity may reflect small sample size, ascertainment, or filtering, not only biological bottlenecks.
- Heterozygosity outliers can reflect crossbreeding, contamination, inbreeding, or batch effects.
- Pi and heterozygosity should not be mixed across variant callers or reference assemblies without caveats.

Risk boundary: diversity metrics are descriptive evidence. Management or conservation recommendations require species-specific playbooks and human review.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_inbreeding_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current wrapper can produce first-pass LD, ROH, pi, and diversity-adjacent artifacts, but it is not a full demographic or conservation-genetics workflow.

Artifact mapping:

| Domain concern | Current artifact |
|---|---|
| LD pairwise statistics | `results/structure/ld/ld_decay.ld.gz` |
| ROH segments | `results/structure/roh/roh.hom` |
| nucleotide diversity | `results/structure/popstats/pi.windowed.pi` when VCFtools runs |
| figure handoff | `results/structure/figures/README.md` |
| summary context | `reports/structure_summary.md` |

Submit blockers:
- no genotype matrix for PLINK2 LD/ROH
- no VCF when pi or Tajima-style statistics are requested
- missing `vcftools` for VCFtools-only statistics
- missing population definitions when population-specific interpretation is requested

Risk boundary: if only first-pass artifacts exist, the report should call them diversity diagnostics, not final population-genetic inference.

## ROH threshold detail policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_roh_threshold_detail
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

ROH thresholds must be stated because ROH calls depend on marker density, genotyping error, heterozygote allowance, gap rules, and minimum segment length. A threshold from one species, chip, or sequencing design should not be treated as universal.

Minimum threshold fields:
- minimum ROH length
- minimum SNP count per segment
- maximum gap between markers
- maximum heterozygous calls allowed
- maximum missing calls allowed
- marker-density or map-distance requirement
- autosome-only or chromosome-specific scope

Interpretation policy:
- short ROH often reflects older shared ancestry or high LD
- long ROH often reflects recent inbreeding, but still requires sample and marker context
- FROH should state denominator genome length or marker-covered length
- group-level ROH summaries should show sample counts and dispersion, not only means

Risk boundary: changing ROH thresholds can change biological conclusions. Reports must make threshold choices visible and auditable.

## LD decay window policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_ld_decay_window_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

LD decay summaries need window and distance policy. In animal breeding datasets, LD can be high because of selection, family structure, recent bottlenecks, or SNP-chip ascertainment.

Required plan fields:
- maximum pairwise distance
- distance bin size
- LD statistic such as r2 or D prime
- MAF and missingness filters before LD
- whether related animals were retained
- population labels and sample counts

Report requirements:
- show LD decay by group when groups are compared
- avoid comparing groups with very different marker density or sample size without caveats
- state if LD was computed on SNP array, WGS, imputed markers, or filtered variants
- keep LD pruning parameters separate from LD decay summary parameters

Risk boundary: LD decay informs resolution and transferability; it does not by itself prove selection or demographic history.

## Effective population size and inbreeding caveat policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_ne_inbreeding_caveat_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Effective population size, pedigree inbreeding, genomic inbreeding, and ROH-based inbreeding answer related but different questions. GeneAgent should keep their estimators separate unless a dedicated analysis has been run.

Estimator distinctions:
- pedigree inbreeding depends on pedigree depth and completeness
- GRM diagonal summaries depend on allele-frequency base and marker filtering
- FROH depends on ROH threshold and covered genome length
- LD-based Ne depends on LD model, distance bins, and population assumptions

Required caveats:
- small samples can destabilize Ne and diversity estimates
- crossbred or admixed cohorts violate simple population assumptions
- commercial-line data may represent selected closed populations, not natural population history
- pedigree and genomic inbreeding can disagree for legitimate reasons

Risk boundary: inbreeding and Ne summaries can influence management decisions. GeneAgent should present them as evidence requiring expert review unless species-specific thresholds and decision rules are provided.

## Group diversity summary policy

```yaml
knowledge_item.v2:
  doc_id: domain_genetic_diversity_group_summary_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T21:30:00+08:00
  owner: popgen_quantgen
```

Group summaries are the safest way to make diversity results interpretable. Every group-level statistic should carry sample count, marker count, filter context, and uncertainty or dispersion when available.

Minimum group summary table:
- group label and label source
- sample count before and after QC
- retained marker count
- observed and expected heterozygosity when computed
- nucleotide diversity or pi when computed
- ROH burden or FROH when computed
- LD summary such as median r2 by distance bin when computed
- missingness and MAF filters

Reporting rules:
- do not rank breeds or lines without stating sampling design
- show missing or unavailable metrics instead of leaving blank interpretations
- separate technical batch groups from biological population groups
- link every summary to the input sample list used

Risk boundary: group summaries are descriptive. Conservation, management, or breeding recommendations require additional species-specific context and review.
