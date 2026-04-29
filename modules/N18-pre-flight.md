# N18 — PreFlight

**Type:** preflight
**Mode:** inline
**Active in:** `fix`

## Inputs

```
fix_plan_doc: (from N17)
project_model: (from entry, or derived from --fix report)
source_report_id: string
resolved_flags: (from entry)
is_resume: boolean          // true when entered via resume
existing_baseline: object | null  // present on resume
```

## Outputs

```
baseline_metrics: {
  tests:      { passed: int, failed: int, skipped: int },
  type_check: { errors: int },
  lint:       { total_warnings: int },
  build:      "pass" | "fail"
}
branch_name: string
```

## Side Effects

- Write-baseline: `~/docs/epiphany/audit/.baselines/<report-id>.json` (fresh runs only)
- Write-log: structured events per step
- Git operation: branch creation (step 3 below)
- **Does NOT write recovery manifest** — that is N19/N22 responsibility

## Halt Conditions

- `halt-on-git-state-incompatible`: dirty tree, detached HEAD, or no commits (fresh runs); subreason: `branch-name-exhausted` if branch creation fails
- `halt-on-baseline-failure`: baseline runner crashes / cannot produce output (NOT for pre-existing test failures — those are recorded as baseline state)
- `halt-on-test-cmd-unknown`: no test command auto-detected and `--test-cmd` not provided

## Step Ordering (mandatory)

Steps execute in this order; a halt at any step does not progress to the next:

**(0) Orphan-branch sweep (fresh runs only):**
Scan for ALL branches matching `epiphany-audit/*` that have:
- No corresponding live recovery manifest at `~/docs/epiphany/audit/.recovery/<report-id>.json` AND
- No corresponding archive at `.recovery/.archive/<report-id>-*.json`

This catches orphans from prior runs against different audit reports. If found: prompt with a multi-select list: *"orphan audit branches found: [numbered list with branch name and last-commit-date]. Delete which? (comma-separated indices, `all`, `none`)."* Default on enter: `none`. Delete only user-selected.

**(1) Git-state check:**
Halt with `halt-on-git-state-incompatible` on dirty tree, detached HEAD, or no commits.
On a **resumed run** (post `git checkout -- . && git clean -fd`): accept the post-cleanup tree as clean; do NOT re-halt on residual state from the prior run.

**(2) Baseline capture:**
Run test suite, type check, lint, build **before any fix**. Write result to `~/docs/epiphany/audit/.baselines/<report-id>.json`.
Pre-existing failing tests → record as baseline state (NOT a halt condition).
Runner crashes / produces no output → `halt-on-baseline-failure`.
On a **resumed run**: skip capture; read existing baseline from the .baselines file. If file missing → `halt-on-baseline-failure` (subreason: `resume-baseline-missing`).

**(3) Branch creation:**
Primary name: `epiphany-audit/<source-report-id>-YYYYMMDD`.
Collision policy:
- If primary name exists AND a recovery manifest exists for `<source-report-id>` → this is a resume; re-use the existing branch (do NOT create a new one).
- If primary name exists AND no manifest exists → prior run completed cleanly; append `-<HHMMSS>` for the fresh run.
- If even the timestamped name collides → `halt-on-git-state-incompatible` (subreason: `branch-name-exhausted`).

## Token Budget

Low (shell commands + file writes).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N19 (E13 chain).

## Back-edge Endpoints

None.
