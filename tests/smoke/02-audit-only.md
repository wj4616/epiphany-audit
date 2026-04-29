# Smoke Test 02 — Audit-Only Mode

**Scenario:** Run `/epiphany-audit --audit` — report produced, no fix offered.

**Actions:**
1. Invoke `/epiphany-audit --audit`
2. Allow pipeline to complete
3. Respond "y" to save prompt

**Expected outcomes:**
- E21 (fix-offer) is NEVER emitted
- Fix pipeline (N16–N23) is NEVER entered
- Audit report saved
- No fix report, no recovery manifest, no branch created
