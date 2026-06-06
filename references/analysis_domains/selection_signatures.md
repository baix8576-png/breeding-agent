# Selection Signatures Domain

This file defines the selection-signature knowledge domain. Some basic statistics are currently available through the population-genetics wrapper, but complete selection-scan workflows require additional contracts.

## Domain scope and scientific intent

```yaml
knowledge_item.v2:
  doc_id: domain_selection_signatures_scope
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Primary `domain_scope`: `selection_signatures`.

Selection-signature analysis looks for genomic regions whose variation patterns are unusual under stated demographic and sampling assumptions. It is an inferential domain and needs stronger safeguards than descriptive PCA or diversity summaries.

Currently executable:
- limited Fst, pi, and Tajima's D style summaries when VCF and population lists are provided
- ROH artifacts that can support candidate-region review

Not yet automated:
- iHS, XP-EHH, nSL, EHH-family haplotype scans
- XP-CLR, PBS, composite-likelihood scans
- phased haplotype workflows
- candidate-region annotation and functional interpretation as a complete pipeline
- cross-statistic consensus ranking

Risk boundary: demographic history, population structure, sample imbalance, reference bias, and ascertainment can mimic selection.

## Population definition policy

```yaml
knowledge_item.v2:
  doc_id: domain_selection_signatures_population_definition
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Selection scans require explicit comparison groups. Population labels should come from user-supplied metadata, sample lists, or a reviewed structure analysis, not from automatic PCA cluster naming.

Required planning inputs:
- population A and population B sample lists for pairwise Fst-like scans
- group labels for multi-population descriptive summaries
- sample counts after QC for each group
- marker filtering provenance
- species and reference assembly context

Blocking conditions:
- missing or empty population files for pairwise statistics
- sample IDs in population files not present in the genotype matrix
- population definitions derived from unreviewed clusters
- severe sample-size imbalance without explicit caveat

Risk boundary: selection analysis starts with group definition. If groups are wrong, the statistic can be perfectly computed and scientifically meaningless.

## Statistic family boundary

```yaml
knowledge_item.v2:
  doc_id: domain_selection_signatures_statistic_family_boundary
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Different selection statistics answer different questions and need different inputs.

| Statistic family | Examples | Required inputs | Current status |
|---|---|---|---|
| population differentiation | Fst, PBS, dXY-style contrasts | population lists, genotype matrix | basic Fst bridge only |
| site-frequency spectrum | Tajima's D, Fay and Wu's H style scans | VCF, window size, comparable sampling | basic Tajima's D bridge only |
| haplotype homozygosity | iHS, XP-EHH, nSL | phased haplotypes, map positions, population definitions | not yet automated |
| composite likelihood | XP-CLR, CLR-style scans | dense genotypes, population contrast, recombination or map assumptions | not yet automated |
| ROH-based candidate regions | shared ROH islands, FROH windows | dense markers, ROH thresholds, group context | partial artifact support |

Planning rule:
- Select the statistic family before choosing tools.
- Do not call the wrapper a complete selection scan when it only ran Fst/pi/Tajima's D.
- Require phasing provenance before haplotype-based scans.

Risk boundary: combining statistics can improve confidence only when each statistic's assumptions and failure modes are visible.

## Candidate region and annotation policy

```yaml
knowledge_item.v2:
  doc_id: domain_selection_signatures_candidate_region_policy
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: expert_opinion
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

Candidate selected regions should be reported as prioritized hypotheses, not validated causal loci.

Minimum candidate-region fields:
- chromosome, start, end, and reference assembly
- statistic family and parameter settings
- population contrast or group definition
- number of markers or windows supporting the region
- nearby gene or regulatory annotation source, if used
- overlap with GWAS/QTL/functional evidence when available

Do not overclaim:
- a nearest gene is not automatically causal
- GO/KEGG enrichment is not proof of selection
- overlap with a known trait locus is supporting context, not validation
- pangenome or SV-aware interpretation requires compatible inputs and annotation assets

Risk boundary: candidate-region annotation belongs to `functional_genomics_annotation` when the task moves from statistical outlier detection to biological explanation.

## Execution bridge and artifacts

```yaml
knowledge_item.v2:
  doc_id: domain_selection_signatures_execution_bridge
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-06T00:00:00+08:00
  owner: popgen_quantgen
```

The current bridge is intentionally limited. `scripts/population_genetics/run_population_structure_diversity.sh` can generate basic population statistics, but GeneAgent should label this as a first-pass screen.

Artifact mapping:

| Domain concern | Current artifact |
|---|---|
| Fst-style contrast | `results/structure/popstats/fst.*` when population lists and VCFtools run |
| nucleotide diversity | `results/structure/popstats/pi.*` |
| Tajima-style windows | `results/structure/popstats/tajima.*` |
| ROH support | `results/structure/roh/roh.hom` |
| caveat summary | `reports/structure_summary.md`, `reports/stratification_risk.md` |

Must remain knowledge/planning only until implemented:
- phased haplotype selection scans
- complete XP-CLR/PBS workflows
- candidate-region merging and ranking
- functional annotation of selected windows

Risk boundary: this execution bridge supports descriptive and first-pass selection-adjacent statistics, not a complete selection-signature deliverable.
