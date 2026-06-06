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
