# Smoke Test 01 — Default Invocation

**Scenario:** Run `/epiphany-audit` from within a small Python project directory with no flags.

**Setup:**
- cwd is inside a git repo with ≥1 commit
- Project has Python source files + a `pytest` test suite
- Dimension plugin files are present and valid in `dimensions/`

**Actions:**
1. Invoke `/epiphany-audit` (no flags, no path argument)
2. Allow the full pipeline to run (N01 → N14)
3. Respond "y" to the save prompt (N15)
4. Respond "n" to the fix-offer prompt (E21)

**Expected outcomes:**
- N01 resolves `audit_target` via `git rev-parse --show-toplevel`
- N02 activates CORRECTNESS + MAINTAINABILITY (floor); activates or skips other dimensions based on heuristics
- N14 Q-GATE produces `pass_a: pass`; Pass B: `skipped-low-volume` if <5 findings and no CRITICAL/HIGH
- Audit report saved to `~/docs/epiphany/audit/<project-slug>-<YYYYMMDD>-<HHMMSS>.md`
- Idempotency state file written to `~/docs/epiphany/audit/.state/<report-id>.json`
- Fix-offer shown; user responds "n"; pipeline ends
- Structured event log created at `~/docs/epiphany/audit/.logs/<report-id>.jsonl`
- No halt states triggered
