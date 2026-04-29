# N23 — FixReporter

**Type:** formatter
**Mode:** inline
**Active in:** `fix`

## Inputs

```
per_fix_outcomes: FixOutcome[]       // from N19
baseline_metrics: object             // from N18
post_metrics: object | null          // null on partial (halt before N21 completed)
audit_rerun_delta: object | null     // null on partial
diff_scope_result: string            // from N21
unmapped_hunks: DiffHunk[]
resolved_flags: (from entry)
recovery_manifest_ref: string | null
is_partial: boolean                  // true on halt-mid-fix-*
halt_state_id: string | null         // present on partial
```

## Outputs

```
fix_report_markdown: string   // fix report per Schema v1
fix_report_id: string         // uuid v4 (generated here)
```

## Side Effects

- Write-report: saves fix report to `~/docs/epiphany/audit/fix-reports/<source-report-id>-fix-<YYYYMMDD>-<HHMMSS>.md`
- Write-log

## Halt Conditions

None. N23 always writes what it has.

## Two Invocation Modes

**(1) Planned termination** (reached via E13 chain end):
- `partial: false`, `halt_state: null`
- Full report: one body entry per source audit finding (plus induced-regression / new-finding descendants)
- Then E_finalize fires → N22 archives manifest → E_complete → user

**(2) halt-mid-fix-\*** (reached via E_halt_partial):
- `partial: true`, `halt_state: <id>`
- Partial report: body entries reflect work-to-date (verified/failed/deferred so far)
- Then halt envelope emitted to user; recovery manifest stays live for `resume`

## Status-Priority Sort Order

`failed > induced-regression > deferred > simulated > verified > skipped`

This order surfaces problems first.

## Top-of-Body Sections

1. **Deferred items** — consolidated list with `defer_reason` per item; surfaced first
2. **Manual edits** (only if user authorized scope-creep at `halt-on-scope-creep`)
3. **Recovery** (only if run died mid-flight and was resumed)

## Token Budget

Scales with finding count (~200 tokens per entry for formatting).

## Backtrack / Aggregation

AGGREGATION owner (per-fix outcome rollup).

## Fan-out Cardinality

1:1 → E_finalize → N22 (planned), OR 1:1 → user via E_halt_partial (partial).

## Back-edge Endpoints

E_finalize: N23 → N22 (strictly sequential — N23 writes first, then N22 archives).
