# Smoke Test 03 — Fix a Known-Good Report

**Scenario:** Run `/epiphany-audit --fix <report>` on a valid saved audit report.

**Setup:**
- A valid audit report exists at `~/docs/epiphany/audit/myproject-20260427-100000.md`
- The report has ≥1 main-body finding with a literal-patch remediation
- The project is in a clean git state with ≥1 commit

**Actions:**
1. Invoke `/epiphany-audit --fix ~/docs/epiphany/audit/myproject-20260427-100000.md`
2. Approve the fix plan when prompted (N17)
3. Allow N18 → N19 → N20 → N21 → N23 to complete

**Expected outcomes:**
- N01..N15 SKIPPED entirely
- N16 F-VAL validates the report; SHA-256 captured
- Branch `epiphany-audit/<report-id>-YYYYMMDD` created
- Per-finding: `[AUDIT-NNN]` commit created on success; working-tree discarded on fail
- Fix report saved to `~/docs/epiphany/audit/fix-reports/`
- Recovery manifest archived to `.recovery/.archive/<report-id>-completed-<ISO>.json`
- Live recovery manifest removed (`<report-id>.json` gone)
- No `partial: true` in fix report
