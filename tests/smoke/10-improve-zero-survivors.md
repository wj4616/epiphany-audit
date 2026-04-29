# Smoke Test 10 — Improve Zero Survivors

**Scenario:** All improvement candidates are filtered by OEF.

**Setup:**
- Arrange for N25 to produce candidates that all fail OEF rules
  (all have cost > utility, or utility=1, or speculative language)

**Expected outcomes:**
- N27 emits a valid improvement report with `survivors: 0`, `notable: 0`, `quick_wins: 0`, `worthwhile: 0`
- Report body is empty (zero improvement entries)
- Summary section contains: *"No improvements above the utility/cost threshold were found. This is a valid result."*
- `improvement_partial: false` (pipeline completed; just no survivors)
- Pipeline does NOT halt; fix-offer (E21) fires normally after E20
