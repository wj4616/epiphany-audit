# Smoke Test 06 — Suspicious Target Halt

**Scenario:** Invoke with a suspicious target root.

**Actions:**
1. Invoke `/epiphany-audit $HOME`

**Expected outcomes:**
- `halt-suspicious-target` emitted immediately with structured envelope:
  `{halt_state: "halt-suspicious-target", subreason: "$HOME", diagnostic: "resolved target $HOME looks like a wrapper/aggregator, not a project."}`
- Pipeline does NOT proceed past N01
- No files written, no branches created
