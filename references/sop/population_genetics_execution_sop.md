# Population Genetics Execution SOP

## Scope and Inputs

```yaml
knowledge_item.v2:
  doc_id: sop_population_genetics_execution
  version: v2
  species: multi_species
  blueprint_scope: population_genetics
  evidence_level: sop
  source: sop
  updated_at: 2026-06-11T00:00:00+08:00
  owner: popgen_quantgen
```

This SOP covers first-pass population structure, diversity, inbreeding, and selection-adjacent summaries available through the current `scripts/population_genetics/` bridge. Supported execution includes PCA preparation, LD pruning, PCA, LD summaries, ROH summaries, and limited VCFtools Fst/pi/Tajima window summaries when population lists are supplied.

Inputs include a genotype matrix in PLINK or VCF form, optional covariates, and optional population-list files. Population labels must come from reviewed metadata or explicit sample lists, not from unsupervised cluster labels alone.

## Preflight Checks

- Confirm genotype files pass the genotype-processing input contract or have an accepted upstream QC summary.
- Check that population-list sample IDs match the genotype matrix before Fst/pi/Tajima execution.
- Require LD pruning policy and PCA component-retention policy to be recorded.
- Require explicit `--threads`, `--memory-mb`, `--window-size` when window statistics are requested, and run-local `--tmp-dir`.
- Block automatic breed/ancestry naming from PCA clusters unless a report reviewer confirms the metadata basis.

## Execution Steps

1. Validate genotype and population-list inputs and write an execution manifest.
2. Run or simulate PLINK2 LD pruning before PCA when PCA is requested.
3. Generate PCA eigenvectors/eigenvalues and record the number of retained components.
4. Generate LD and ROH summaries only when marker density and missingness are acceptable.
5. Run VCFtools Fst/pi/Tajima summaries only for explicit population files.
6. Write stratification-risk notes for downstream GWAS or genomic prediction.

## Expected Outputs

- `results/structure/run_manifest.json`
- `results/structure/audit_sidecar.json`
- `results/structure/pruning_manifest.json`
- `results/structure/pca/eigenvec.tsv`
- `results/structure/pca/eigenval.tsv`
- `results/structure/ld/ld_decay.ld.gz` when LD is requested
- `results/structure/roh/roh.hom` when ROH is requested
- `results/structure/popstats/*` for requested Fst/pi/Tajima outputs
- `reports/structure_summary.md`
- `reports/stratification_risk.md`
- `logs/population_structure_diversity.log`

## Failure and Breaker Rules

Breaker conditions include missing genotype input, missing population lists for population-statistic targets, unreconciled sample IDs, missing `plink2` for PCA/LD/ROH targets, unindexed or malformed VCF for VCFtools targets, non-POSIX paths, output overwrite risk, and resource requests above caps.

The Agent may safely create directories, emit dry-run plans, and record missing-tool diagnostics. It must not auto-rename clusters, merge populations, change population definitions, or claim selection without statistic-specific and biological review.

## Report and Audit Handoff

Reports must separate descriptive structure/diversity outputs from selection claims. Audit handoff must include population files used, pruning policy, PCA component policy, window size, tool versions, command summaries, log paths, and explicit warnings when results are exploratory.
