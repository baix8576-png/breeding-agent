# Population Genetics Operation Guide

This guide documents `scripts/population_genetics/` after the scientific-domain script restructure. It covers practical execution boundaries for population structure, diversity, inbreeding, and first-pass selection-adjacent summaries.

## Directory role

`scripts/population_genetics/` currently contains one thin wrapper:

- `run_population_structure_diversity.sh`

Compatibility routing:

| Current scientific directory | Compatibility blueprint key | Knowledge domains |
|---|---|---|
| `scripts/population_genetics/` | `pca_pipeline` | `population_structure`, `genetic_diversity_inbreeding`, limited `selection_signatures` |

This directory is not a complete population-genetics framework. It is an execution bridge for current safe artifacts.

## Expected input package

At least one genotype-bearing input is required:

- `--plink-prefix` for PLINK `.bed/.bim/.fam`
- `--vcf` for VCF/VCF.GZ, with conversion when PLINK input is absent
- auto-discovery under `--input-root` for simple dry-run or fixture use

Optional inputs:

- `--covariate` for downstream report context
- `--population-a` and `--population-b` for Fst-style pairwise statistics
- `--window-size` for pi and Tajima's D style windows

Input rules:

- Use POSIX `/` paths only.
- Population files must contain sample IDs that match the genotype matrix.
- PCA cluster labels must not be used as population definitions unless reviewed.
- Raw genotype and population-list inputs remain read-only.

## Common invocation

PCA, LD, and ROH dry run:

```bash
scripts/population_genetics/run_population_structure_diversity.sh \
  --workdir /data2/user/geneagent_runs/task_002/run_001 \
  --plink-prefix /data2/user/project_inputs/cohort \
  --analysis-targets pca,population_structure,ld,roh \
  --threads 16 \
  --memory-mb 65536 \
  --tmp-dir /data2/user/geneagent_runs/task_002/run_001/tmp/population_structure_diversity \
  --dry-run
```

First-pass Fst, pi, and Tajima's D with VCF:

```bash
scripts/population_genetics/run_population_structure_diversity.sh \
  --workdir /data2/user/geneagent_runs/task_002/run_001 \
  --vcf /data2/user/project_inputs/cohort.vcf.gz \
  --population-a /data2/user/project_inputs/pop_a.samples.txt \
  --population-b /data2/user/project_inputs/pop_b.samples.txt \
  --analysis-targets pca,ld,roh,fst,pi,tajima_d \
  --window-size 50000 \
  --threads 16 \
  --memory-mb 65536
```

## Method boundaries

| Target | Current support | Boundary |
|---|---|---|
| PCA | supported through PLINK2 after LD pruning | no automatic breed or ancestry labels |
| LD | supported through PLINK2 pairwise statistics | not a full demographic model |
| ROH | supported through PLINK2 homozyg runs | ROH thresholds need species and marker-density review |
| Fst | supported through VCFtools when two population lists exist | not a full selection scan |
| pi | supported through VCFtools window summaries | descriptive diversity only |
| Tajima's D | supported through VCFtools window summaries | demography-sensitive and not proof of selection |
| iHS / XP-EHH / XP-CLR / PBS | not yet automated | knowledge/planning only |

## Resource parameters

Always pass explicit resource parameters:

| Option | Purpose |
|---|---|
| `--threads` | caps supported PLINK2 operations and thread environment variables |
| `--memory-mb` | passes PLINK2 memory cap and sets script virtual-memory guard |
| `--tmp-dir` | tool spill directory under the approved run root |
| `--log-dir` | log capture directory |

`vcftools` does not expose a stable general thread flag in this wrapper, so it is bounded by the script environment, memory guard, and the Agent's pre-submit caps.

## Output contract

The wrapper writes:

| Path | Meaning |
|---|---|
| `results/structure/run_manifest.json` | inputs, targets, resources, tools, and safety notes |
| `results/structure/audit_sidecar.json` | run context for report and audit packaging |
| `results/structure/pruning_manifest.json` | LD pruning parameter record |
| `results/structure/pca/eigenvec.tsv` | PCA coordinates |
| `results/structure/pca/eigenval.tsv` | PCA component magnitudes |
| `results/structure/ld/ld_decay.ld.gz` | LD pairwise output when requested |
| `results/structure/roh/roh.hom` | ROH segments when requested |
| `results/structure/popstats/*` | VCFtools Fst/pi/Tajima outputs when requested |
| `reports/structure_summary.md` | execution and input summary |
| `reports/stratification_risk.md` | downstream modeling caveats |

## Failure handling

Pre-submit blockers:

- missing genotype input
- missing `plink2` for PCA, LD, or ROH
- population lists missing when Fst is requested
- population-list sample IDs not reconciled by upstream validation
- resource request above configured caps
- non-POSIX paths

Safe automatic actions:

- create result, report, log, and tmp directories inside the approved run root
- skip optional VCFtools statistics when VCF or tool is missing and the requested core PCA/LD/ROH target can still run
- keep warnings in logs and report summaries

Breaker conditions:

- no analysis step executed
- guessed population labels
- automatic sample removal from PCA clusters
- output overwrite without approval
- any attempt to claim complete selection-signature delivery from first-pass Fst/pi/Tajima outputs

## Cross-links

Use these knowledge assets when planning or explaining this directory:

- `references/analysis_domains/population_structure.md`
- `references/analysis_domains/genetic_diversity_inbreeding.md`
- `references/analysis_domains/selection_signatures.md`
- `references/structure_analysis/pca_structure_interpretation.md`
- `references/parameter_playbooks/pca_component_policy.md`
- `references/papers/pca_core_papers_v1.md`
- `references/papers/animal_genomics_classic_landmarks.md`
- `references/papers/animal_genomics_recent_high_impact_2022_2026.md`
