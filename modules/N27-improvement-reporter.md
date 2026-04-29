# N27 — ImprovementReporter (IR)

**Type:** formatter
**Mode:** inline
**Active in:** `improve`

## Inputs

```
survivors: ImprovementCandidate[]       // from N26
discarded_improvements: object[]        // from N26 (for --verbose section)
improvement_context: (from N24)
resolved_flags: (from entry)
source_report_id: string
saved_audit_report_path: string | null  // null if N15 save was declined
improvement_partial: boolean            // true if N24..N26 pipeline failed partway
improvement_partial_warning: string | null
```

## Outputs

```
improvement_report_markdown: string
improvement_report_path: string   // absolute path where the report was saved
```

## Side Effects

- Write-report: saves improvement report to `~/docs/epiphany/audit/improvement-reports/<project-slug>-<YYYYMMDD>-<HHMMSS>-improve.md` **unconditionally** (no save prompt)
- Conditional in-place patch: updates `improvement_report_ref` in the already-saved audit report's YAML frontmatter (only when N15 save was accepted)
- Write-log

## Halt Conditions

None. N27 always writes what it has (including partial results when `improvement_partial: true`).

## Backpatch Failure Handling

If the in-place frontmatter patch of the audit report fails (e.g., permission error, file modified since save):
- Log the absolute path of the improvement report to the event log
- Emit a user-facing warning: *"Could not patch improvement_report_ref into audit report. Improvement report is at: <path>"*
- Do NOT retry; do NOT halt

## Sections (in order)

1. Summary (total candidates, filtered, survivors by category; zero-survivors message if applicable)
2. Notable improvements (utility = 3, cost ≤ 2)
3. Quick wins (utility ≥ 2, cost = 1, not notable)
4. Worthwhile improvements (utility ≥ cost ≥ 2, not notable)
5. Filtered improvements (under `--verbose` only) with OEF discard rationale per candidate

## `improvement_partial: true` Behavior

Two causes; distinguished by warning text:
- Source audit was token-capped: *"source audit was token-capped at `<truncated_at_node>`; improvement analysis is based on incomplete findings and may miss opportunities in unanalyzed dimensions."*
- N24..N26 pipeline failure: *"improvement analysis failed partway through — output may be incomplete. Check the event log at `~/docs/epiphany/audit/.logs/<report-id>.jsonl` for details."*

Both set `improvement_partial: true` in the report frontmatter.

## E20 → E21 Sequencing

E20 fires when N27 writes the report and summarizes to user. In no-flag mode (fix offered after improve), E21 (fix? offer) fires AFTER E20 resolves.

## Token Budget

Scales with survivors count (~300 tokens per entry for formatting).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → user (E20, terminal for --improve subpipeline).

## Back-edge Endpoints

None.
