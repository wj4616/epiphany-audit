# N21 — RegressionBattery (battery + tiered audit-rerun delta)

**Type:** verifier
**Mode:** inline (battery) + conditional subagent (audit-rerun under `--deep` when full rerun)
**Active in:** `both` (battery always; audit-rerun fires in fix-mode N21 when tiered policy requires it)

## Inputs

```
per_fix_outcomes: FixOutcome[]    // from N19
baseline_metrics: object          // from N18
applied_tier_max: 1 | 2 | 3       // highest tier of fixes applied this run
resolved_flags: (from entry)
test_cmd: string
```

## Outputs

```
battery_result: "pass" | "fail"
diff_scope_result: "pass" | "fail-with-unmapped-hunks"
unmapped_hunks: DiffHunk[]
audit_rerun_delta: {
  scope: "full" | "narrow" | "skipped-tier-policy" | "skipped-by-flag" | null,
  reran_dimensions: string[],
  resolved: string[],                    // finding IDs confirmed fixed by the rerun
  fix_induced_regressions: string[],     // finding IDs newly introduced in touched files
  unchanged: string[],                   // finding IDs still present after fixes
  new_findings_discovered: Finding[]     // new findings in untouched files (record only; no E_rerun_fail)
}
```

## Side Effects

- Write-log: events per battery step and audit-rerun
- Spawns subagent for audit-rerun (under `--deep` when full-rerun tiered) — 1 optional spawn

## Halt Conditions

- `halt-on-scope-creep` (E_diffscope): unmapped diff hunks; do NOT auto-revert; user choice = authorize (manual-edits section in fix report) or revert manually
- `halt-mid-fix-on-induced-regression-cap-hit`: E_repair cap exhausted on a regression-induced fix-group

## Battery Steps (runs BEFORE audit-rerun — always inline)

Order:
1. Full test suite vs baseline (no new failures allowed)
2. Type check (no new errors vs baseline)
3. Lint (`new_warnings_in_changed_regions == 0`)
4. Build clean
5. Diff-scope check: every diff line maps to an AUDIT-ID; regression-prevention test additions (in `[AUDIT-NNN]` or `[AUDIT-NNN-test]` commits) count as in-scope; unmapped hunks → `halt-on-scope-creep`

Battery failure → E_repair; audit-rerun not run (no point if battery fails).

## Audit-Rerun Policy (tiered by `applied_tier_max`)

| applied_tier_max | Behavior |
|-----------------|----------|
| 1 (Tier-1 only) | **Skip** (battery covers failure modes; no audit-rerun) |
| 2 (Tier-2 only) | **Narrow rerun**: re-run only N04..N09 instances matching dimension tags of applied fixes. Post-pipeline subset: N10 FPV, N11 aggregator, N12 prioritizer, N14 Pass A (N13 formatter and N14 Pass B skipped). |
| 3 (any Tier-3)  | **Full rerun**: N01..N14 Pass A (N14 Pass B skipped — delta semantics). |

Override: `--full-rerun` forces full regardless of tier; `--no-rerun` forces skip. Fix report records `audit_rerun_delta.scope: skipped-by-flag` when `--no-rerun`.

## Induced Regression vs New Finding

- New finding in **files touched by applied fixes** → `induced-regression` → route to E_rerun_fail → N16 for re-triage
- New finding in **untouched files** → `new-finding-discovered` → record in fix report body only; no E_rerun_fail

## Token Budget

Battery: minimal (shell commands). Narrow rerun: 30k per re-run analyzer. Full rerun: full N01..N14 pass budget.

## Backtrack / Aggregation

Adversarial-via-rerun.

## Fan-out Cardinality

1 optional subagent spawn (full rerun under `--deep`).

## Back-edge Endpoints

E_repair: N21 fail → N19 (1st) or N17 (2nd) per E_repair rules.
E_rerun_fail: N21 induced-regression → N16 (batched re-triage).
E_diffscope: N21 diff-scope fail → halt.
