# Smoke Test 11 — Fix + Improve Warning

**Scenario:** `/epiphany-audit --fix <report> --improve` — improvement pipeline is silently skipped.

**Actions:**
1. Invoke `/epiphany-audit --fix <report> --improve`

**Expected outcomes:**
- A user-facing WARNING is emitted: *"--improve is ignored with --fix; run without --fix to include improvement analysis."*
- The warning is NOT a halt — the fix pipeline proceeds normally
- N24..N27 are NEVER entered
- The structured event log records the skip event at `~/docs/epiphany/audit/.logs/<report-id>.jsonl`
- Fix report `flags` field does NOT contain `improve` (effective flags only)
