# PCA Pipeline Stage SOP (v1)

```yaml
knowledge_item.v2:
  doc_id: "sop_pca_pipeline_stage_v1"
  version: "v2"
  species: "multi_species"
  blueprint_scope: "pca"
  evidence_level: "sop"
  source: "sop"
  updated_at: "2026-05-09T15:10:00+08:00"
  owner: "popgen_quantgen"
```

## Purpose
- Standardize stage-by-stage operation for `pca_pipeline`.
- Keep execution aligned with `scripts/pca_pipeline/run_pca_pipeline.sh` and population-structure safeguards.

## Stage: ld_pruning

### Input Thresholds
- PLINK-executable genotype dataset is required.
- If only VCF is supplied, conversion to temporary PLINK dataset must succeed before pruning.
- Recommended marker count >= 5,000 for stable PCA backbone.

### Default Parameters
- `plink2 --indep-pairwise 50 5 0.2`
- `analysis_targets=pca,population_structure,ld,roh,fst,pi,tajima_d`
- Pruning manifest output: `results/structure/pruning_manifest.json`

### Manual Confirmation Points
- Confirm pruning parameters match species LD scale when overrides are used.
- Confirm conversion from VCF to PLINK is logged in audit trail.
- Confirm target list does not include unsupported custom metrics.

### Disable Conditions
- `plink2` unavailable.
- No usable PLINK backbone after VCF conversion attempt.
- Input validation gate is blocked.

## Stage: pca_computation

### Input Thresholds
- `prune.prune.in` must exist from prior stage.
- Effective sample size should be >= 20 for interpretable exploratory PCs.

### Default Parameters
- `plink2 --pca 20` on pruned markers.
- Optional LD/ROH defaults when requested:
- `plink2 --r2 gz --ld-window-kb 500 --ld-window 99999 --ld-window-r2 0.0`
- `plink2 --homozyg`
- Optional population statistics window: `window_size=50000` for `pi` and `TajimaD`.

### Manual Confirmation Points
- Confirm PC axis interpretation remains descriptive (no automatic ancestry claims).
- Confirm Fst uses explicit `--population-a/--population-b` files reviewed by human.
- Confirm covariates are annotated as optional design aids, not auto-selected model covariates.

### Disable Conditions
- PCA target requested but no pruned marker list available.
- `vcftools`-dependent targets requested without VCF input or vcftools binary.
- Population labels missing for Fst while Fst target is requested.

## Stage: structure_summary

### Input Thresholds
- `eigenvec.tsv` and `eigenval.tsv` must exist for structure summary.
- Optional LD/ROH/popstats outputs may be absent but must be explicitly flagged.

### Default Parameters
- Required outputs:
- `results/structure/figures/README.md`
- `reports/structure_summary.md`
- Include optional artifacts if generated:
- `results/structure/ld/ld_decay.ld.gz`
- `results/structure/roh/roh.hom`
- `results/structure/popstats/*`

### Manual Confirmation Points
- Confirm figure labeling uses neutral cohort naming.
- Confirm cluster boundaries are not promoted to biological/breed claims.
- Confirm missing optional statistics are declared as "not generated" with reason.

### Disable Conditions
- PCA core outputs missing and rerun unavailable.
- Summary attempts to infer causal interpretation from structure alone.
- Report/audit output path unavailable.

## Stage: stratification_warning

### Input Thresholds
- `structure_summary.md` must be present.
- Downstream consumers (GWAS/prediction) should be identified for warning handoff.

### Default Parameters
- Output: `reports/stratification_risk.md`
- Baseline warning content:
- outlier clusters require review before downstream inference.
- PC covariates should be considered when structure is strong.
- population statistics require species-context interpretation.

### Manual Confirmation Points
- Confirm warning severity level (low/medium/high) with analyst sign-off.
- Confirm downstream handoff records whether PCs will be used as covariates.
- Confirm non-bio requests do not receive bio-specific stratification warnings.

### Disable Conditions
- No structure summary available.
- Request is non-bio lightweight branch.
- Any automation tries to suppress stratification warning despite detected structure anomalies.
