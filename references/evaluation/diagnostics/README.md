# diagnostics

Structured knowledge assets for mapping runtime errors to executable remediation actions.

Scope:
- Scheduler diagnostics: SLURM and PBS submit/poll/recovery failures.
- Bioinformatics tool diagnostics: `plink2`, `bcftools`, `vcftools`, `gcta64`.

## Stable Markdown Schema (diagnostics_v1)

Each diagnostic entry must keep the same field keys and order:

1. `pattern_id`
2. `component`
3. `stage`
4. `severity`
5. `trigger_keywords`
6. `trigger_regex`
7. `likely_root_causes`
8. `executable_fix_steps`
9. `command_examples`
10. `risk_notice`
11. `verification`

Field conventions:
- `pattern_id`: globally unique identifier, recommended style `domain.topic.short_name`.
- `trigger_keywords`: plain text snippets that can be matched by lexical retrieval.
- `trigger_regex`: regex hints for log scanners (case-insensitive by default).
- `executable_fix_steps`: explicit sequence, no generic guidance-only text.
- `command_examples`: runnable shell command blocks with placeholders.
- `risk_notice`: highlight side effects and safety constraints.
- `verification`: concrete checks to confirm the fix path.

## Files

- `scheduler_error_patterns.md`: SLURM/PBS diagnostic patterns.
- `bio_tool_error_patterns.md`: plink2/bcftools/vcftools/gcta diagnostic patterns.
