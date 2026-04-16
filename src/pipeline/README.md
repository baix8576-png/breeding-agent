# Pipeline Module

This module owns local pipeline validation, workflow blueprints, and v1 execution command planning.

## Current scope
- Validate local input bundle structure and file-path readiness.
- Publish deterministic pipeline catalog metadata.
- Build execution-ready workflow blueprints and output templates.
- Resolve bioinformatics requests into concrete wrapper commands under `scripts/*`.

## v1 analysis coverage
- QC: sample and variant QC contracts with executable wrapper entrypoints.
- Population genetics: PCA, structure summary, LD, ROH, Fst, pi, and Tajima's D contracts.
- Quantitative genetics: GRM/kinship, GWAS, heritability, and genomic prediction contracts.

## Boundary
- The Python layer composes command plans; scheduler submission and polling remain in `src/scheduler`.
- Biological interpretation is never automated and must be reviewed by domain experts.
