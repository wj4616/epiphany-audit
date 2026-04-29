# Smoke Test 09 — Improve Mode

**Scenario:** `/epiphany-audit --improve` — improvement report produced after audit.

**Actions:**
1. Invoke `/epiphany-audit --improve`
2. Allow audit pipeline (N01–N14) to complete
3. Respond "y" to save prompt (N15)
4. Allow improvement subpipeline (N24–N27) to complete
5. Respond "n" to fix-offer (E21)

**Expected outcomes:**
- N24 ImprovementContextualizer runs immediately after N15
- N25 ImprovementBrainstormer generates candidates
- N26 OEF filters by utility/cost
- N27 writes improvement report to `~/docs/epiphany/audit/improvement-reports/`
- Audit report frontmatter updated: `improvement_report_ref: <absolute path>` patched in-place
- Improvement report has correct count invariants: `survivors == notable + quick_wins + worthwhile`
- `total_candidates == filtered_out + survivors`
