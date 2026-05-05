# N27 — ImprovementReporter (IR)

**Type:** formatter
**Mode:** inline
**Active in:** `improve`
**Persistence:** conditional — writes to disk only under `--reports`; otherwise emits inline survivors table only

## Inputs

```
survivors: ImprovementCandidate[]       // from N26
discarded_improvements: object[]        // from N26 (for --verbose section)
improvement_context: (from N24)
resolved_flags: (from entry)
source_report_id: string
saved_audit_report_path: string | null  // null if N15 save was declined or skipped
improvement_partial: boolean            // true if N24..N26 pipeline failed partway
improvement_partial_warning: string | null
```

## Flag Gate

**If `--reports` is NOT set:**
- Do NOT write any files to disk
- Do NOT attempt backpatch of audit report
- Emit an inline survivors table in conversation output (with utility/cost scores and categories)
- Fire T5 tracer with `IMPROVEPATH=""` and `SURVIVORS` count
- Return

**If `--reports` is set:**
- Proceed with the disk-write + backpatch flow below

## Outputs

```
improvement_report_markdown: string
improvement_report_path: string   // absolute path where the report was saved
```

## Side Effects

- Write-report (only under `--reports`): saves improvement report to `~/docs/epiphany/audit/improvement-reports/<project-slug>-<YYYYMMDD>-<HHMMSS>-improve.md`
- Conditional in-place patch (only under `--reports`): updates `improvement_report_ref` in the already-saved audit report's YAML frontmatter (only when N15 save was accepted)
- Write-log
- **TRACE (mandatory, non-blocking) — immediately after N27 completes, call this Bash command.** Substitute: `IMPROVEPATH` = absolute path of the saved improvement report (empty string `""` if `--reports` not set); `SURVIVORS` = length of the `survivors` array:
  ```
  python3 ~/.claude/skills/epiphany-audit-v2/scripts/langfuse_tracer.py improve-complete --improve-report-path "IMPROVEPATH" --survivors SURVIVORS 2>/dev/null || true
  ```

## Halt Conditions

None. N27 always emits an inline summary (and writes to disk only under `--reports`).

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
