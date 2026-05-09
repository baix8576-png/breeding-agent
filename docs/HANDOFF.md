# HANDOFF

## Mandatory Usage Policy
- This file is mandatory for continuity and hallucination control.
- Update this file at three checkpoints:
- `1)` after each stage task is completed
- `2)` before context compression
- `3)` before opening a new window
- In every resumed/new-window session, read this file first, then run `git status --short` and verify key files before coding.
- If any record in this file conflicts with current repository reality, trust `AGENTS.md` + real code/command output, then fix this file immediately.

## HANDOFF v2 (Project-Specific Rules)
- This project is stage-driven (`V1.5` chain + non-bio lightweight branch), so each handoff update must explicitly map to `stage_id`.
- Every handoff entry must include a cluster policy statement:
- `cluster_execution_expected=true` for bio submit/poll paths
- `cluster_execution_expected=false` for non-bio branch (must not enter scheduler flow)
- Every new task/stage completion status must use checklist blocks:
- `completed_checklist` with `- [x] ...` items for completed work.
- `not_yet_done_checklist` with `- [ ] ...` items for unfinished, deferred, blocked, or follow-up work.
- `in_progress_checklist` with `- [ ] ...` items may be used when work has started but is not complete.
- Do not rely on prose-only `completed:` / `not yet done:` fields for new stage entries.
- `gate_result` remains separate from checklist completion; passing tests does not automatically mark deferred items complete.
- Every handoff entry must include a gate verdict with concrete command evidence:
- `python -m pytest -q`
- `python -m compileall src tests`
- If Windows permission blocks pycache writes, record the fallback command with `PYTHONPYCACHEPREFIX` and its result.
- Never mark a stage task as completed unless this file has been updated in the same session.

## Trigger -> Required Update Matrix
- `stage_task_completed`: update `Change Card`, `completed_checklist`, `not_yet_done_checklist`, `Verification Log`, and `Resume Prompt`.
- `before_context_compression`: update `Session Snapshot`, `In Progress`, `Key Decisions`, `Important Files`, and `Hallucination Traps`.
- `before_new_window`: append latest `git status --short`, pending risks, and next executable command as first action.

## Required Entry Schema (Minimum)
- `intent_domain`
- `stage_id`
- `module_owner_path`
- `cluster_execution_expected`
- `contracts_impacted`
- `files_changed`
- `completed_checklist`
- `not_yet_done_checklist`
- `verification_commands`
- `gate_result` (`pass` / `fail` / `partial`)
- `known_risks`
- `next_actions`
- `resume_first_command`

## Session Start Checklist (Mandatory)
- Read this file from top to bottom.
- Run `git status --short`.
- Verify the highest-priority truth source (`AGENTS.md`) has no conflicting rule updates.
- Verify at least one changed file mentioned in this handoff still matches current repository state.
- Only then continue coding.

## Session Snapshot
- Date/time: 2026-04-28 14:27:17 +08:00
- Project root: `D:\geneagent`
- Current goal: maintain a compact continuity document for context compression, resumed sessions, and new Codex windows.
- Current phase: project documentation and session recovery support.

## Change Card
- intent_domain: `system`
- stage_id: `Audit + Memory`
- module_owner_path: `D:\geneagent\docs`
- responsibility_owner: `orchestrator`
- cluster_execution_expected: `false`
- contracts_impacted: none
- files_changed: `D:\geneagent\docs\HANDOFF.md`, `D:\geneagent\docs\README.md`
- verification_commands: `git status --short`, `git diff --check -- docs/HANDOFF.md docs/README.md`
- gate_result: `partial` (documentation update only)
- known_risks: `handoff notes can drift from code unless continuously refreshed`
- next_actions: `refresh handoff after each stage task and before window switch`
- resume_first_command: `git status --short`
- reviewer_gates: `architect`, `safety_fuse`, `test_eval`

## Non-Negotiable Constraints
- Workspace/tooling constraints: default workspace is `D:\geneagent`; development is Windows PowerShell plus WSL2 hybrid; virtualenv convention is `.venv\Scripts\python.exe`.
- Product/architecture constraints: `AGENTS.md` is the highest-priority project architecture source; new work must stay inside the existing layer and directory charter.
- Root layout constraint: the root allowlist in `AGENTS.md` does not include a root-level `HANDOFF.md`; this handoff lives at `D:\geneagent\docs\HANDOFF.md`.
- Privacy/security constraints: do not store secrets, tokens, private keys, raw credentials, or raw entity data such as VCF, BAM, FASTQ, or FASTA content in this file.
- Things that must not be assumed: do not assume tests passed, branch state is clean, or existing dirty files were created by the current session without verifying.

## Completed
- [x] Added this project handoff document at `D:\geneagent\docs\HANDOFF.md` to support continuity after context compression or a new window.
- [x] Added a docs index entry in `D:\geneagent\docs\README.md`.

## In Progress
- Current task: add project-level handoff support.
- Last concrete action: verified the handoff path, docs index diff, and whitespace check.
- Next safe step: if continuing beyond this doc-only update, inspect the current dirty worktree and run the relevant Python gates before claiming runtime behavior is healthy.

## Not Yet Done
- [ ] Full Python gate (`python -m compileall src tests` and `python -m pytest -q`) was not run for this documentation-only update unless a later verification log says otherwise.

## Key Decisions
- Decision: store the handoff as `docs/HANDOFF.md`, not root `HANDOFF.md`.
  Reason: `AGENTS.md` allows `docs/` as a versioned project directory, while its root file allowlist does not include `HANDOFF.md`.
  Files affected: `D:\geneagent\docs\HANDOFF.md`.
- Decision: treat this file as continuity support, not as an independent source of truth.
  Reason: project handoff notes can drift; future sessions must verify claims against `AGENTS.md`, source files, and fresh command output.
  Files affected: `D:\geneagent\docs\HANDOFF.md`.

## Errors, Causes, Fixes
- Symptom/error: PowerShell printed a profile execution-policy warning while reading files.
  Cause: `C:\Users\Xiaobobai\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1` cannot be loaded under the current execution policy.
  Fix: no project change required for this documentation task; treat the warning as environment noise unless a command actually fails.
  Verification: commands still returned exit code 0.

## Verification Log
- Command: `Get-ChildItem -Force`
  Result: confirmed project root contains allowed project directories including `docs`, plus runtime/cache directories.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: root also had existing untracked or modified files before this handoff update; do not attribute them to this change without checking git history.
- Command: `rg --files -g '*HANDOFF*' -g '*handoff*' -g 'README.md' -g 'docs/**'`
  Result: no pre-existing handoff document was found; `docs/README.md` and `docs/v1_5_system_map.md` exist.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: use `rg --files -g '*HANDOFF*' -g '*handoff*'` to re-check.
- Command: `git status --short`
  Result: worktree was already dirty before this handoff file was added.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: preserve user changes; do not revert unrelated files.
- Command: `Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'`
  Result: `2026-04-28 14:27:17 +08:00`.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: timestamp used for this snapshot.
- Command: `Test-Path -LiteralPath 'docs\HANDOFF.md'`
  Result: `True`.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: confirmed the handoff file exists at the AGENTS-compliant docs path.
- Command: `git diff --check -- docs/HANDOFF.md docs/README.md`
  Result: exit code 0; Git warned that `docs/README.md` LF may be replaced by CRLF the next time Git touches it.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: no whitespace errors were reported.
- Command: `rg -n "HANDOFF.md|Root layout constraint|Resume Prompt|Key files" docs\HANDOFF.md docs\README.md`
  Result: confirmed the handoff entry, root-layout constraint, and resume prompt are present.
  Date/time: 2026-04-28 14:27 +08:00
  Notes: useful quick check for future sessions.

## Important Files
- `D:\geneagent\AGENTS.md`: highest-priority architecture, directory, role, safety, and gate instructions.
- `D:\geneagent\docs\HANDOFF.md`: continuity notes for context compression and new-window recovery.
- `D:\geneagent\docs\README.md`: docs directory index; should point readers to this handoff file.
- `D:\geneagent\docs\v1_5_system_map.md`: current V1.5 system map and executable loop summary.
- `D:\geneagent\README.md`: user-facing project overview; verify before citing because it may have local edits.
- `D:\geneagent\src\memory\README.md`: memory-layer context, including project handoff semantics in runtime memory.

## Hallucination Traps
- Trap: assuming a root-level `HANDOFF.md` should exist because many agents look for that name at the project root.
  Correct fact / how to verify: this repository's root file allowlist does not include `HANDOFF.md`; use `D:\geneagent\docs\HANDOFF.md` unless `AGENTS.md` is formally changed.
- Trap: assuming existing modified source files were changed by the session that edited this document.
  Correct fact / how to verify: run `git status --short` and inspect diffs before making claims.
- Trap: assuming a doc-only update means test gates passed.
  Correct fact / how to verify: only claim `compileall` or `pytest` passed after running those exact commands and recording their output.
- Trap: treating this handoff as more authoritative than `AGENTS.md`.
  Correct fact / how to verify: read `D:\geneagent\AGENTS.md` first for architecture and safety rules, then verify this file against real files.

## Resume Prompt
Paste this into a new session:
> Continue this project from `D:\geneagent\docs\HANDOFF.md`. First read it, then verify current files with `git status --short` and targeted file reads before making changes. Latest goal: maintain V1.5 continuity without violating `AGENTS.md` directory, safety, or testing gates.

## Session Update 2026-05-09 (M2-01 + M2-02)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`
- module_owner_path: `D:\geneagent\references`, `D:\geneagent\src\contracts`, `D:\geneagent\tests\unit\contracts`
- cluster_execution_expected: `false`
- contracts_impacted: `KnowledgeItemV2` (`doc_id/version/species/blueprint_scope/evidence_level/source/updated_at/owner`)
- files_changed:
  - `D:\geneagent\references\INDEX.md`
  - `D:\geneagent\references\papers\README.md`
  - `D:\geneagent\references\sop\README.md`
  - `D:\geneagent\references\parameter_playbooks\README.md`
  - `D:\geneagent\references\failure_cases\README.md`
  - `D:\geneagent\references\ontology\README.md`
  - `D:\geneagent\references\ontology\knowledge_item.v2.md`
  - `D:\geneagent\src\contracts\knowledge.py`
  - `D:\geneagent\src\contracts\__init__.py`
  - `D:\geneagent\tests\unit\contracts\test_knowledge.py`
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m compileall src tests` (permission error on existing `__pycache__` paths)
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` (pass)
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/contracts/test_knowledge.py tests/unit/contracts/test_execution.py` (pass)
- gate_result: `pass` (with compileall fallback evidence recorded)
- known_risks:
  - Existing repository already has many unrelated modified/untracked files; this update only touched the M2 knowledge scope above.
  - `knowledge_item.v2` is defined and tested at contract level; retrieval-side metadata ingestion is not yet enforced at runtime.
- next_actions:
  - Wire `KnowledgeItemV2` validation into knowledge indexing/loading path (`src/knowledge/retrieval.py`) for runtime-level enforcement.
  - Add integration tests for metadata parsing and invalid-asset rejection behavior.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 (M2-03 seed ingest: 40 core paper cards)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`
- module_owner_path: `D:\geneagent\references\papers`, `D:\geneagent\references\sop`
- cluster_execution_expected: `false`
- contracts_impacted: `knowledge_item.v2` (paper-card metadata usage and enforcement convention)
- files_changed:
  - `D:\geneagent\references\papers\qc_core_papers_v1.md`
  - `D:\geneagent\references\papers\pca_core_papers_v1.md`
  - `D:\geneagent\references\papers\grm_core_papers_v1.md`
  - `D:\geneagent\references\papers\genomic_prediction_core_papers_v1.md`
  - `D:\geneagent\references\papers\README.md`
  - `D:\geneagent\references\sop\grobid_pdf_ingestion_sop.md`
  - `D:\geneagent\references\INDEX.md`
- verification_commands:
  - `Get-ChildItem -Path references/papers -Name` (confirm files exist)
  - `Select-String -Path <paper_pack> -Pattern '^## ' | Measure-Object` (confirm each pack has 10 cards)
  - `git status --short` (confirm change visibility in working tree)
- gate_result: `partial` (knowledge assets updated; compileall/pytest not rerun in this session because source code behavior not changed)
- known_risks:
  - Paper cards are seed-level expert summaries; they are not yet auto-generated from full-text TEI extraction.
  - Google Scholar citation counts are intentionally not hard-coded due temporal drift; links are provided for manual refresh.
- next_actions:
  - Implement runtime metadata ingestion in `src/knowledge/retrieval.py` to parse/validate `knowledge_item.v2` fields from paper assets.
  - Add extraction-side integration tests for GROBID TEI -> card augmentation pipeline.
  - Add `M2-03` regression tests to ensure retrieval ranking can use `blueprint_scope/evidence_level/source`.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 (M2 knowledge-base charter in AGENTS)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`
- module_owner_path: `D:\geneagent\AGENTS.md`, `D:\geneagent\docs`
- cluster_execution_expected: `false`
- contracts_impacted: `knowledge_item.v2`, future chunk/index metadata conventions
- files_changed:
  - `D:\geneagent\AGENTS.md`
  - `D:\geneagent\docs\HANDOFF.md`
- verification_commands:
  - `Select-String -Path AGENTS.md -Pattern '知识库搭建宪章|raw_pdfs|grobid_tei|embeddings|hybrid retrieval|knowledge_item.v2|references/papers|受版权保护' -Context 1,2` (confirmed new charter terms)
  - `git diff --check -- AGENTS.md docs/HANDOFF.md` (pass; Git line-ending warning only)
- gate_result: `partial` (documentation-only architecture update; runtime tests not rerun)
- known_risks:
  - `AGENTS.md` already had unrelated local edits before this update; preserve them and review full file before committing.
  - Runtime implementation still needs metadata parsing, chunk construction, BM25/embedding index builders, and traceability tests.
- next_actions:
  - Implement `src/knowledge` metadata/chunk/index ingestion path according to the new AGENTS knowledge-base charter.
  - Add tests for `knowledge_item.v2` parsing from references, chunk traceability, and local index manifest behavior.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 14:53 +08:00 (M2-03 runtime knowledge ingestion/index)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`
- module_owner_path: `D:\geneagent\src\contracts`, `D:\geneagent\src\knowledge`, `D:\geneagent\tests\unit\contracts`, `D:\geneagent\tests\unit\knowledge`
- cluster_execution_expected: `false`
- contracts_impacted:
  - `KnowledgeItemV2` runtime parsing from `references/papers/*.md`
  - new `KnowledgeChunk`
  - new `KnowledgeIndexManifest`
  - extended `RetrievalDocument` traceability fields (`doc_id/chunk_id/section/page_or_anchor/blueprint_scope/species/evidence_level/retrieval_channels`)
- files_changed:
  - `D:\geneagent\src\contracts\knowledge.py`
  - `D:\geneagent\src\contracts\__init__.py`
  - `D:\geneagent\src\knowledge\indexing.py`
  - `D:\geneagent\src\knowledge\grobid.py`
  - `D:\geneagent\src\knowledge\__init__.py`
  - `D:\geneagent\src\knowledge\retrieval.py`
  - `D:\geneagent\tests\unit\contracts\test_knowledge.py`
  - `D:\geneagent\tests\unit\knowledge\test_indexing.py`
  - `D:\geneagent\tests\unit\knowledge\test_grobid.py`
  - `D:\geneagent\tests\unit\knowledge\test_retrieval.py`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] M2-03A: `ReferenceKnowledgeIndexer` parses fenced `knowledge_item.v2` metadata from local Markdown paper cards and validates with `KnowledgeItemV2`.
  - [x] M2-03B: `KnowledgeChunk` and `KnowledgeIndexManifest` contracts added and exported.
  - [x] M2-03C: local Markdown paper cards are chunked into traceable searchable units.
  - [x] M2-03D: in-memory BM25/keyword index implemented by `HybridKnowledgeIndex`.
  - [x] M2-03E: embedding-lite scoring is optional/configurable via `embedding_model="keyword-overlap-v1"` and is not the sole retrieval path.
  - [x] M2-03F: `GrobidTeiParser` mockable TEI adapter added with fixture-style unit test; no copyrighted PDF required.
  - [x] M2-03G: retrieval results now expose `doc_id/chunk_id/section/page_or_anchor/evidence_level/hit_reasons/confidence` for paper-card chunks.
- not_yet_done_checklist:
  - [ ] Persist BM25/embedding index artifacts under an ignored runtime cache if M2 decides rebuild-on-start is not enough.
  - [ ] Add ingestion QA for invalid metadata cards once user-supplied PDFs/cards enter the knowledge library.
  - [ ] Fix existing GBK subprocess warning separately by forcing UTF-8 in script-level subprocess calls/tests.
  - [ ] Add true external embedding model integration only after local-first deterministic retrieval remains stable.
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/contracts/test_knowledge.py tests/unit/knowledge/test_indexing.py tests/unit/knowledge/test_grobid.py tests/unit/knowledge/test_retrieval.py` -> pass (`26 passed`)
  - `& .\.venv\Scripts\python.exe -m compileall src tests` -> fail due Windows `PermissionError` writing existing `__pycache__` files
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q` -> pass (`100%`; 4 skips; existing GBK decode warnings in subprocess reader threads)
  - `git diff --check -- <M2-03 changed files>` -> pass (line-ending warnings only)
- gate_result: `pass` (compileall required the documented `PYTHONPYCACHEPREFIX` fallback)
- known_risks:
  - Some existing seed paper-card Chinese text displays mojibake in PowerShell output; metadata and English method identifiers still parse and test correctly.
  - `HybridKnowledgeIndex` is in-memory for M2-03; persistent index files can be added in a later M2/M3 task.
  - External embedding models are intentionally not introduced yet to keep local-first retrieval deterministic and offline-safe.
  - Worktree already contains many unrelated modified/untracked files from earlier V1.5/M2 work; preserve them and do not attribute all dirty state to this task.
- next_actions:
  - Decide whether M2 should persist BM25/embedding index artifacts under an ignored runtime cache (for example `.geneagent/knowledge_index/`) or keep deterministic rebuild-on-start for now.
  - Add ingestion QA for invalid metadata cards once the knowledge library starts accepting user-supplied PDFs/cards.
  - Consider fixing GBK subprocess warning separately by forcing UTF-8 in script-level subprocess calls/tests.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 15:01 +08:00 (HANDOFF checklist rule)
- intent_domain: `system`
- stage_id: `Audit + Memory`
- module_owner_path: `D:\geneagent\AGENTS.md`, `D:\geneagent\docs`
- cluster_execution_expected: `false`
- contracts_impacted: none
- files_changed:
  - `D:\geneagent\AGENTS.md`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Added a mandatory task completion checklist rule to `AGENTS.md`.
  - [x] Added `completed_checklist` and `not_yet_done_checklist` to the required HANDOFF entry schema.
  - [x] Updated the stage-task trigger rule so future completion updates must use checkbox lists.
  - [x] Preserved `gate_result` as a separate evidence field, not a replacement for completion status.
- not_yet_done_checklist:
  - [ ] Existing historical HANDOFF entries before this rule may still use older prose-style fields unless intentionally migrated later.
  - [ ] Future stage/session entries must follow the checklist format.
- verification_commands:
  - `git diff --check -- AGENTS.md docs/HANDOFF.md`
- gate_result: `partial` (rule/documentation update only; runtime tests not required)
- known_risks:
  - PowerShell still prints profile execution-policy warnings; treat them as environment noise when command exit code is 0.
  - `AGENTS.md` contains existing non-ASCII text that PowerShell may display as mojibake; this rule was added in ASCII to stay readable.
- next_actions:
  - Use `completed_checklist` / `not_yet_done_checklist` for every future task completion update.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 15:09 +08:00 (M2-04 SOP library by blueprint stages)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`
- module_owner_path: `D:\geneagent\references\sop`, `D:\geneagent\references`
- cluster_execution_expected: `false`
- contracts_impacted:
  - `knowledge_item.v2` metadata completeness for SOP assets
  - Stage-level SOP policy fields (`Input Thresholds/Default Parameters/Manual Confirmation Points/Disable Conditions`)
- files_changed:
  - `D:\geneagent\references\sop\qc_pipeline_stage_sop_v1.md`
  - `D:\geneagent\references\sop\pca_pipeline_stage_sop_v1.md`
  - `D:\geneagent\references\sop\grm_builder_stage_sop_v1.md`
  - `D:\geneagent\references\sop\genomic_prediction_stage_sop_v1.md`
  - `D:\geneagent\references\sop\README.md`
  - `D:\geneagent\references\INDEX.md`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Created stage-by-stage SOP for `qc_pipeline`.
  - [x] Created stage-by-stage SOP for `pca_pipeline`.
  - [x] Created stage-by-stage SOP for `grm_builder`.
  - [x] Created stage-by-stage SOP for `genomic_prediction`.
  - [x] Ensured every stage includes `Input Thresholds`, `Default Parameters`, `Manual Confirmation Points`, and `Disable Conditions`.
  - [x] Added `knowledge_item.v2` metadata blocks in all new SOP assets.
  - [x] Updated `references/sop/README.md` and `references/INDEX.md` to index the M2-04 SOP library.
- not_yet_done_checklist:
  - [ ] Add optional automated lint/check that verifies all SOP files keep the four mandatory stage fields.
- verification_commands:
  - `rg -n "^## Stage:|^### Input Thresholds|^### Default Parameters|^### Manual Confirmation Points|^### Disable Conditions|knowledge_item.v2" references\sop\qc_pipeline_stage_sop_v1.md references\sop\pca_pipeline_stage_sop_v1.md references\sop\grm_builder_stage_sop_v1.md references\sop\genomic_prediction_stage_sop_v1.md`
  - `git diff --check -- references\sop\README.md references\sop\qc_pipeline_stage_sop_v1.md references\sop\pca_pipeline_stage_sop_v1.md references\sop\grm_builder_stage_sop_v1.md references\sop\genomic_prediction_stage_sop_v1.md references\INDEX.md`
- gate_result: `pass` (documentation and knowledge-asset update; no runtime behavior change)
- known_risks:
  - Threshold defaults in SOP are project defaults and may need species/project-specific overrides before production use.
  - Existing repository has unrelated modified/untracked files; this update only targets SOP assets and index entries listed above.
- next_actions:
  - Link these SOP files from blueprint assets in retrieval/routing prompts so stage guidance is surfaced automatically at plan time.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 15:19 +08:00 (M2-05 retrieval evidence-chain output)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`
- module_owner_path: `D:\geneagent\src\knowledge`, `D:\geneagent\tests\unit\knowledge`
- cluster_execution_expected: `false`
- contracts_impacted:
  - `RetrievalDocument` adds `conflict_entries` and `confidence_sources`.
  - `RetrievalBundle` adds bundle-level `evidence_conflicts` and `confidence_sources`.
- files_changed:
  - `D:\geneagent\src\knowledge\retrieval.py`
  - `D:\geneagent\tests\unit\knowledge\test_retrieval.py`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Upgraded retrieval hit output to include evidence-chain fields: `hit_reasons`, `conflict_entries`, `confidence_sources`.
  - [x] Added conflict detection logic for competing blueprint scope / evidence-level overlap / same-doc multi-chunk focus.
  - [x] Added confidence provenance generation with formula components and signal sources.
  - [x] Added bundle-level evidence aggregation in `KnowledgeResolver.resolve()`.
  - [x] Added unit tests for conflict and confidence-source output paths.
  - [x] Passed compile gate with pycache fallback and full pytest gate.
- not_yet_done_checklist:
  - [ ] Add optional typed conflict schema (instead of string entries) if downstream API consumers need stricter parsing.
  - [ ] Add API/CLI serialization assertions for evidence-chain fields in integration tests.
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/knowledge/test_retrieval.py` -> pass
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q` -> pass (`100%`; existing GBK subprocess decode warnings remain)
  - `git diff --check -- src\knowledge\retrieval.py tests\unit\knowledge\test_retrieval.py docs\HANDOFF.md` -> pass (line-ending warnings only)
- gate_result: `pass`
- known_risks:
  - Conflict entries are heuristic and lexical; they indicate contention signals, not formal contradiction proof.
  - Existing Windows GBK decode warnings in subprocess reader threads are unchanged and pre-existing.
- next_actions:
  - Wire evidence-chain fields into runtime report section rendering (`report_index.v2` diagnostics block) for direct user-facing traceability.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 16:35 +08:00 (M2-06 safety-tiered external fallback gate)
- intent_domain: `knowledge`
- stage_id: `Local-first RAG`, `Resource + Safety Gate`
- module_owner_path: `D:\geneagent\src\knowledge`, `D:\geneagent\src\runtime`, `D:\geneagent\src\orchestration`, `D:\geneagent\tests`
- cluster_execution_expected: `false`
- contracts_impacted:
  - `RetrievalBundle.fallback_gate_audit` (policy decision audit trail)
  - `DiagnosticPreview.fallback_gate_audit` and `fallback.gate_audit`
  - runtime settings for external fallback tiered policy
- files_changed:
  - `D:\geneagent\src\knowledge\retrieval.py`
  - `D:\geneagent\src\runtime\settings.py`
  - `D:\geneagent\src\runtime\bootstrap.py`
  - `D:\geneagent\src\orchestration\service.py`
  - `D:\geneagent\src\runtime\facade.py`
  - `D:\geneagent\.env.example`
  - `D:\geneagent\tests\unit\knowledge\test_retrieval.py`
  - `D:\geneagent\tests\unit\runtime\test_settings.py`
  - `D:\geneagent\tests\integration\api\test_task_routes.py`
  - `D:\geneagent\tests\e2e\cli\test_plan_placeholder.py`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Reworked external fallback gate into policy-tiered mode (`tiered`) with domain + sensitivity control.
  - [x] Added sensitivity classification (`low/medium/high/restricted`) and domain ceiling policy (`bioinformatics/knowledge/system`).
  - [x] Kept legacy policies (`always/knowledge_only/diagnostic_only`) for compatibility.
  - [x] Added auditable gate payload (`fallback_gate_audit`) including policy, domain, sensitivity, decision, reason, and signals.
  - [x] Exposed audit trail through orchestration diagnostic output and CLI/API diagnostic payloads.
  - [x] Added configurable settings/env keys for fallback policy, default sensitivity, and per-domain sensitivity limits.
  - [x] Added unit/integration/e2e regression coverage for tiered policy allow/block behavior and audit serialization.
  - [x] Passed compile gate with `PYTHONPYCACHEPREFIX` fallback and passed full pytest gate.
- not_yet_done_checklist:
  - [ ] Sensitivity classification is currently rule-based/keyword-based; future iteration can add structured classifier calibration per species/project context.
  - [ ] Existing Windows GBK subprocess decode warnings in unrelated script tests remain and should be fixed separately.
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/knowledge/test_retrieval.py tests/unit/runtime/test_settings.py tests/integration/api/test_task_routes.py tests/e2e/cli/test_plan_placeholder.py` -> pass
  - `& .\.venv\Scripts\python.exe -m compileall src tests` -> fail on existing `__pycache__` permission
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q` -> pass (`100%`; 4 skips; pre-existing GBK warnings)
- gate_result: `pass`
- known_risks:
  - Tiered sensitivity detection currently relies on deterministic lexical/path signals and may need tuning to reduce false positives/negatives for edge-case prompts.
  - Worktree contains many unrelated historical modifications; this update only targets the files listed above.
- next_actions:
  - Add a small policy playbook in `references/parameter_playbooks/` to document recommended sensitivity ceilings by tenant/environment.
  - Consider surfacing `fallback_gate_audit` in report diagnostics (`report_index.v2`) for end-user traceability.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 17:18 +08:00 (M2-07 architect pipeline-pack mechanism)
- intent_domain: `bioinformatics`
- stage_id: `Blueprint Selection`, `Artifact + Report`
- module_owner_path: `D:\geneagent\src\pipeline\packs`, `D:\geneagent\src\pipeline`, `D:\geneagent\tests\unit\pipeline`
- cluster_execution_expected: `false`
- contracts_impacted:
  - New pipeline-pack contracts: `PipelinePackSpec / PipelinePackStage / PipelinePackArtifact / PipelinePackReportTemplate / PipelinePackTestSpec`
  - New pack registry API: `build_pipeline_pack / list_pipeline_packs / validate_pipeline_pack_tests`
  - `pipeline.__init__` exports pack APIs for runtime import consistency
- files_changed:
  - `D:\geneagent\src\pipeline\packs\models.py`
  - `D:\geneagent\src\pipeline\packs\registry.py`
  - `D:\geneagent\src\pipeline\packs\__init__.py`
  - `D:\geneagent\src\pipeline\__init__.py`
  - `D:\geneagent\src\pipeline\README.md`
  - `D:\geneagent\tests\unit\pipeline\test_packs.py`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Added `src/pipeline/packs/` with typed pack schema covering `spec + stage + artifact + report template + tests`.
  - [x] Added pack registry that maps canonical pipelines and aliases, and emits stable pack objects for all four V1.5 bio blueprints.
  - [x] Added compatibility conversion (`PipelinePack.to_blueprint_payload`) to preserve current blueprint contracts.
  - [x] Added `validate_pipeline_pack_tests` audit helper to ensure declared test paths are resolvable.
  - [x] Exported pack APIs through `src/pipeline/__init__.py`.
  - [x] Added unit regression `tests/unit/pipeline/test_packs.py` to verify canonical coverage, payload stability, and alias compatibility.
  - [x] Passed scoped and full gate tests (`pytest -q`) and compile gate via documented pycache fallback.
- not_yet_done_checklist:
  - [ ] Pack registry currently derives data from existing `build_blueprint`; future iteration can flip to pack-first source of truth and make workflows consume packs directly.
  - [ ] Optional follow-up: persist pack manifest snapshots for release-time diffing across versions.
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/pipeline/test_packs.py tests/unit/pipeline/test_pipeline_execution.py tests/e2e/test_v1_completion.py` -> pass
  - `& .\.venv\Scripts\python.exe -m compileall src tests` -> fail on existing `__pycache__` permission
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q` -> pass (`100%`; existing GBK subprocess warnings unchanged)
- gate_result: `pass`
- known_risks:
  - Pipeline pack metadata currently bootstraps from existing workflow blueprint functions; architecture is standardized but not yet fully pack-first.
  - Existing GBK decode warnings in subprocess-based tests remain pre-existing environment debt.
- next_actions:
  - M2-08 candidate: migrate `pipeline.workflows` builder internals to consume pack registry directly and reduce duplicated schema logic.
  - Add pack-level integration checks under `tests/integration` if we later introduce external pack loading.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 17:56 +08:00 (M2-08 popgen_quantgen pack-first blueprint migration)
- intent_domain: `bioinformatics`
- stage_id: `Blueprint Selection`
- module_owner_path: `D:\geneagent\src\pipeline\packs`, `D:\geneagent\src\pipeline`, `D:\geneagent\tests\unit\pipeline`
- cluster_execution_expected: `false`
- contracts_impacted:
  - `build_blueprint/list_blueprints/build_output_template` now consume pack registry as source.
  - builtin four-blueprint payloads moved under `src/pipeline/packs`.
  - pack regression extends with explicit pack->blueprint payload equivalence assertion.
- files_changed:
  - `D:\geneagent\src\pipeline\packs\builtin_blueprints.py`
  - `D:\geneagent\src\pipeline\packs\registry.py`
  - `D:\geneagent\src\pipeline\workflows.py`
  - `D:\geneagent\tests\unit\pipeline\test_packs.py`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Migrated four canonical bio blueprints into pack-side builtin payload module (`src/pipeline/packs/builtin_blueprints.py`).
  - [x] Removed `registry -> pipeline.workflows` dependency and switched to `registry -> packs.builtin_blueprints`.
  - [x] Replaced `src/pipeline/workflows.py` with pack-first compatibility layer while preserving public API contracts.
  - [x] Kept behavior equivalent for alias mapping and artifact/stage payload shape.
  - [x] Added/updated pack regression to assert `build_blueprint(name)` output is equivalent to `build_pipeline_pack(name).to_blueprint_payload()`.
  - [x] Passed old test suite and new pack tests.
- not_yet_done_checklist:
  - [ ] Optional cleanup: decompose `builtin_blueprints.py` into per-blueprint files for easier review and future diffing.
  - [ ] Optional follow-up: add snapshot-style contract tests for blueprint payload drift detection.
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/pipeline/test_packs.py tests/e2e/test_v1_completion.py tests/unit/orchestration/test_orchestration_planning.py tests/unit/pipeline/test_pipeline_execution.py` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/pipeline/test_packs.py tests/unit/pipeline/test_pipeline_execution.py` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q` -> pass (`100%`; existing GBK subprocess warnings unchanged)
  - `& .\.venv\Scripts\python.exe -m compileall src tests` -> fail on existing `__pycache__` permission
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` -> pass
- gate_result: `pass`
- known_risks:
  - `builtin_blueprints.py` is currently monolithic and large; readability is acceptable but maintainability can be improved by splitting by blueprint.
  - Existing GBK decode warnings in subprocess-based tests remain pre-existing environment debt.
- next_actions:
  - Continue M2 roadmap with pack-level integration hooks if external/dynamic pack loading is introduced.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 16:29 +08:00 (M2-09 + M2-10 + M2-11)
- intent_domain: `system`
- stage_id: `Blueprint Selection`, `Resource + Safety Gate`, `Audit + Memory`
- module_owner_path: `D:\geneagent\src\tools`, `D:\geneagent\src\scheduler`, `D:\geneagent\src\memory`
- cluster_execution_expected: `false` (this session delivered contracts/planning/memory code only; no real cluster submit executed)
- contracts_impacted:
  - `ToolManifest` adds atomic metadata fields (`algorithm_family/atomic_resource_profile/failure_code_map`)
  - `PipelineSpec` adds `atomic_algorithms`
  - `SubmissionPlan` adds `atomic_tools` and `atomic_failure_code_mapping`
  - memory layer contracts add `ProjectRecord/FailureRecord/ApprovalRecord/ProvenanceRecord`
- files_changed:
  - `D:\geneagent\src\tools\manifest_schema.py`
  - `D:\geneagent\src\tools\manifests\atomic_algorithms.v1.json`
  - `D:\geneagent\src\tools\manifests\README.md`
  - `D:\geneagent\src\scheduler\atomic_profiles.py`
  - `D:\geneagent\src\scheduler\base.py`
  - `D:\geneagent\src\scheduler\pbs.py`
  - `D:\geneagent\src\scheduler\resource_estimator.py`
  - `D:\geneagent\src\scheduler\models.py`
  - `D:\geneagent\src\scheduler\__init__.py`
  - `D:\geneagent\src\contracts\execution.py`
  - `D:\geneagent\src\pipeline\execution.py`
  - `D:\geneagent\src\pipeline\__init__.py`
  - `D:\geneagent\src\orchestration\service.py`
  - `D:\geneagent\src\runtime\facade.py`
  - `D:\geneagent\src\memory\stores.py`
  - `D:\geneagent\src\memory\__init__.py`
  - `D:\geneagent\src\memory\README.md`
  - `D:\geneagent\tests\unit\tools\test_manifest_schema.py`
  - `D:\geneagent\tests\unit\tools\test_registry.py`
  - `D:\geneagent\tests\unit\scheduler\test_atomic_profiles.py`
  - `D:\geneagent\tests\unit\memory\test_stores.py`
- completed_checklist:
  - [x] M2-09: expanded manifest system to atomic algorithm level and added `atomic_algorithms.v1.json` entries for `plink2/gcta/vcftools/bcftools` tools.
  - [x] M2-09: schema-level validation now enforces structured atomic resource profile + failure-code map consistency.
  - [x] M2-10: added scheduler atomic profile registry with CPU/memory/walltime aggregation and retry guidance mapping.
  - [x] M2-10: wired atomic profiles into submission planning (`build_submission_plan`) and failure-recovery output.
  - [x] M2-10: surfaced atomic failure mapping in `SubmissionPlan` for structured downstream diagnostics.
  - [x] M2-11: implemented memory layering for `run/session/project/failure/approval/provenance` with project-level aggregation.
  - [x] M2-11: execution closure now writes approval/provenance slices and updates session/project memory indexes.
  - [x] Added unit coverage for new manifests, scheduler atomic profiles, and memory layered records.
- not_yet_done_checklist:
  - [ ] Propagate structured `atomic_failure_code_mapping` to API/CLI report payloads (currently available in scheduler plan object and recovery guidance text).
  - [ ] Add dedicated integration/e2e cases for project-level memory readback across multi-run sessions.
  - [ ] Address pre-existing Windows GBK subprocess decode warnings in script-based tests (non-blocking for this stage).
- verification_commands:
  - `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/tools/test_manifest_schema.py tests/unit/tools/test_registry.py tests/unit/scheduler/test_atomic_profiles.py tests/unit/scheduler/test_scheduler_planning.py tests/unit/memory/test_stores.py tests/unit/orchestration/test_orchestration_planning.py tests/unit/runtime/test_dry_run_branching.py` -> pass
  - `& .\.venv\Scripts\python.exe -m pytest -q` -> pass (`100%`; existing GBK decode warnings unchanged)
  - `& .\.venv\Scripts\python.exe -m compileall src tests` -> fail due existing `__pycache__` permissions
  - `$env:PYTHONPYCACHEPREFIX='D:\geneagent\pycache_temp'; & .\.venv\Scripts\python.exe -m compileall src tests` -> pass
- gate_result: `pass` (compileall passed with documented fallback)
- known_risks:
  - Atomic manifest and scheduler profile tables are static in-repo defaults; site-specific HPC policies may still require local override.
  - Repository remains a pre-existing dirty worktree with unrelated changes; this session intentionally touched only M2-09/10/11 scope files listed above.
- next_actions:
  - Wire `atomic_failure_code_mapping` into report diagnostics section and API/CLI diagnostic endpoints.
  - Add integration test for project memory continuity across 2+ runs in one session.
- resume_first_command: `git status --short`

## Session Update 2026-05-09 16:35 +08:00 (workspace hygiene and Git consolidation)
- intent_domain: `system`
- stage_id: `Audit + Memory`
- module_owner_path: `D:\geneagent\docs`, `D:\geneagent`
- cluster_execution_expected: `false`
- contracts_impacted: none
- files_changed:
  - `D:\geneagent\docs\genomic_agent_architecture_summary.md`
  - `D:\geneagent\docs\README.md`
  - `D:\geneagent\docs\HANDOFF.md`
- completed_checklist:
  - [x] Re-read HANDOFF and current `git status --short` before cleanup.
  - [x] Confirmed the dirty worktree primarily contains intended M2 source/test/docs/reference changes.
  - [x] Moved root-level `genomic_agent_architecture_summary.md` into `docs/` to comply with the root directory charter.
  - [x] Added the archived architecture summary to `docs/README.md`.
- not_yet_done_checklist:
  - [ ] Stage and commit the consolidated worktree after verification.
  - [ ] Push the resulting commit if the remote accepts it.
- verification_commands:
  - `git status --short` -> dirty before consolidation
  - `git diff --stat` -> confirmed M2 worktree scope
  - `git ls-files --others --exclude-standard` -> confirmed untracked versionable M2 assets
- gate_result: `partial` (cleanup in progress; final Git status to be recorded after commit)
- known_risks:
  - The worktree contains a broad multi-stage M2 change set, so the cleanup commit should be reviewed as a milestone consolidation rather than a tiny patch.
  - Existing Windows line-ending warnings are expected in this repository.
- next_actions:
  - Run `pytest -q`, compile gate with `PYTHONPYCACHEPREFIX`, then commit and push.
- resume_first_command: `git status --short`
