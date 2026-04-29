# N17 — FixPlanner

**Type:** planner
**Mode:** inline
**Active in:** `fix`

## Inputs

```
triage_result: (from N16)
fix_groups: FixGroup[]
resolved_flags: (from entry)
```

## Outputs

```
fix_plan_doc: string        // Dry-Run Plan Schema v1 markdown
user_approvals: {           // per tier; populated after interactive confirmation
  tier_1: "approved" | "declined",
  tier_2: "approved" | "declined",
  tier_3_per_fix: { [finding_id]: "approved" | "declined" }
}
```

## Side Effects

- Write-report (under `--dry-run` only): saves dry-run plan to `~/docs/epiphany/audit/dry-run-plans/<source-report-id>-dryrun-<YYYYMMDD>-<HHMMSS>.md`
- Write-log: events per tier confirmation

## Halt Conditions

- `halt-on-user-abort`: explicit `halt` at any tier prompt

## `--dry-run` Behavior

Emits Dry-Run Plan v1 and **halts here** — no PreFlight, no FixApplier, no branch creation. The plan contains `proposed_diff` (the literal patch N19 WOULD apply) for each finding.

If `--no-rerun` or `--full-rerun` is also set, emit a user-facing warning before proceeding: *"`--no-rerun`/`--full-rerun` has no effect under `--dry-run` — the audit-rerun tier policy is irrelevant when the fix pipeline halts at N17."* This is a warning only; N17 continues normally.

## Tier Confirmation Protocol

Default policy (applied in order T1 → T2 → T3):

| Tier | Default | `--auto` | `--confirm-all` |
|------|---------|----------|-----------------|
| 1    | batch confirm: *"apply N Tier-1 fixes? y/n"* | silent apply | per-fix confirm |
| 2    | batch confirm: *"apply M Tier-2 fixes? y/n"* | batch confirm | per-fix confirm |
| 3    | per-fix confirm | per-fix confirm | per-fix confirm |

Decline on Tier-N → all Tier-N findings marked `deferred (user-declined-batch)`; pipeline proceeds to Tier-N+1. Explicit `halt` → stop entirely.

**Per-fix-opt-in floor (anti-conformity):** even under `--auto`, any finding with `confidence < HIGH OR effort > trivial` requires per-fix opt-in (not auto-applied). Only HIGH-confidence, trivial-effort findings auto-apply under `--auto`.

## Token Budget

Low (plan generation + interactive prompts).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N18 (or halt under `--dry-run`).

## Back-edge Endpoints

E_repair (2nd invocation): N20 fail → N17 replan (replan the failed fix-group with failure context; then retry via N19).
