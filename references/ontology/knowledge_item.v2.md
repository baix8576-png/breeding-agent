# knowledge_item.v2

Schema id:
- `knowledge_item.v2`

Required fields:
- `doc_id`
- `version`
- `species`
- `blueprint_scope`
- `evidence_level`
- `source`
- `updated_at`
- `owner`

Field definitions:
- `doc_id`: stable document identifier, unique inside this repository.
- `version`: metadata version token for this knowledge item (for example `v2`, `v2.1`).
- `species`: target species or species scope (for example `sus_scrofa`, `bos_taurus`, `multi_species`).
- `blueprint_scope`: one of `qc`, `pca`, `grm`, `genomic_prediction`, or `shared`.
- `evidence_level`: one of `sop`, `benchmark`, `peer_reviewed`, `incident_verified`, or `expert_opinion`.
- `source`: one of `paper`, `sop`, `parameter_playbook`, `failure_case`, `ontology`, or `internal_note`.
- `updated_at`: ISO-8601 timestamp with timezone.
- `owner`: accountable maintainer for content accuracy.

Example:
```yaml
doc_id: "paper_qc_missingness_2026_001"
version: "v2"
species: "sus_scrofa"
blueprint_scope: "qc"
evidence_level: "peer_reviewed"
source: "paper"
updated_at: "2026-05-09T12:00:00+08:00"
owner: "popgen_quantgen"
```
