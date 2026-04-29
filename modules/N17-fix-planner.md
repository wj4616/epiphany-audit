# N17 — FixPlanner

**Type:** planner
**Mode:** inline
**Active in:** `fix`

## Inputs

```
triage_result: (from N16 — includes input_type from report frontmatter)
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

## Per-Input-Type Confirmation Thresholds (v2.x)

For non-code input types, the risk classification thresholds override the tier system. Auto-apply without confirmation when ALL low-risk criteria for the input type are met:

| Input Type | Low-Risk (auto-apply) | High-Risk (require confirmation) |
|-----------|----------------------|--------------------------------|
| Code | Tier-1: ≤2 lines, single file, no signature change, confidence=HIGH, effort=trivial (v1.x unchanged) | Tier-2 and Tier-3 (v1.x unchanged) |
| Specification document | Single-section addition only, no removal of existing content, no heading hierarchy restructuring | Any removal, heading restructuring, multi-section edits, or acceptance-criteria rewrites |
| Plan document | Checkpoint addition (new checkpoint only, no reordering), task-list append (new tasks only), or missing-rollback-procedure addition | Phase reordering, dependency corrections, task removal, any edit touching existing phase structure |
| Claude code ai agent skill | YAML frontmatter field addition only (new field, no existing-field modification), or supporting-file addition (new file, no existing-file edits) | Any SKILL.md prose modification, existing frontmatter field changes, supporting-file modifications, module edits |
| Detailed prompt | `<meta>` tag addition, output-format addition (new section, no existing-format modification), or verification-scaffolding addition | Prompt body modifications, frontmatter changes, embedded schema changes, technique-application modifications |

These thresholds override the existing tier system for non-code types. For code, the existing v1.x tier system remains authoritative and unchanged.

When `input_type` is not "code", the Tier Confirmation Protocol above is replaced by this per-type table. The `--auto`, `--confirm-all`, and `--dry-run` flags still gate behavior: `--auto` auto-applies low-risk; `--confirm-all` requires confirmation for everything; `--dry-run` emits plan only.

## Token Budget

Low (plan generation + interactive prompts).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N18 (or halt under `--dry-run`).

## Back-edge Endpoints

E_repair (2nd invocation): N20 fail → N17 replan (replan the failed fix-group with failure context; then retry via N19).
