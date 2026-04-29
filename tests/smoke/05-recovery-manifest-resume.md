# Smoke Test 05 — Recovery Manifest Resume

**Scenario:** Simulate a mid-flight process death, then resume.

**Setup:**
- A live recovery manifest exists at `~/docs/epiphany/audit/.recovery/<report-id>.json`
- The manifest has `in_flight_finding_id` set (process died inside the atomic loop)
- The audit branch exists at `epiphany-audit/<report-id>-YYYYMMDD`

**Actions:**
1. Invoke `/epiphany-audit --fix <report>`
2. Observe `halt-on-recovery-conflict` prompt
3. Choose `resume`
4. Allow pipeline to complete

**Expected outcomes:**
- `halt-on-recovery-conflict` emitted with structured envelope at top of message
- Resume-handler sub-step runs: tree-divergence safety check → git checkout/clean if safe → `in_flight_finding_id` moved back to `pending`
- Applied findings skipped (idempotency)
- Pending findings processed in topo-sort order
- On completion: recovery manifest archived as `completed-<ISO>.json`; live manifest removed
