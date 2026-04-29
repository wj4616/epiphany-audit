# Smoke Test 07 — Target Conflict Halt

**Scenario:** Explicit path disagrees with report's audit_target.

**Actions:**
1. Invoke `/epiphany-audit /some/other/project --fix ~/docs/epiphany/audit/myproject-report.md`
   (where `myproject-report.md` has `audit_target: /home/user/myproject`)

**Expected outcomes:**
- `halt-on-target-conflict` emitted:
  `{halt_state: "halt-on-target-conflict", subreason: "path-report-disagreement", diagnostic: "explicit path /some/other/project does not match the audit_target field of the report."}`
- Pipeline does NOT proceed
