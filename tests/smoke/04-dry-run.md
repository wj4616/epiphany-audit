# Smoke Test 04 — Dry-Run Mode

**Scenario:** `/epiphany-audit --fix <report> --dry-run` — plan emitted, nothing applied.

**Actions:**
1. Invoke `/epiphany-audit --fix <report> --dry-run`
2. Observe output

**Expected outcomes:**
- N17 FixPlanner writes a Dry-Run Plan v1 to `~/docs/epiphany/audit/dry-run-plans/`
- Pipeline HALTS at N17; N18 (branch creation) is NEVER entered
- No working-tree changes, no branch created, no commits
- Plan contains `proposed_diff` for each finding
- Fix report: NOT created (dry-run plan is the artifact)
- Warning emitted if `--no-rerun` is also passed: *"--no-rerun has no effect under --dry-run"*
