# N14 — Q-GATE

**Type:** verifier
**Mode:** inline (Pass A) + conditional subagent (Pass B)
**Active in:** `audit`

## Inputs

```
formatted_report_markdown: string       // from N13
location_verification_cache: Cache     // from N10 (read-only)
resolved_flags: (from N01)
```

## Outputs

```
q_gate_result: {
  pass_a: "pass" | "pass-minimal" | "fail" | "skipped-token-cap",
  pass_b: "pass" | "fail" | "exec-error" | "skipped-token-cap" | "skipped-low-volume",
  pass_b_lens: string | null,
  pass_b_skip_reason: string | null
}
validated_report: string   // the report with any Pass A/B corrections applied
```

## Side Effects

Read-only (may read source files for location verification on cache miss).

## Halt Conditions

- `halt-on-q-gate-failure` (subreason: `pass-a`): Pass A fails mandatory checks
- `halt-on-q-gate-failure` (subreason: `pass-b`): Pass B content-fail
- `halt-on-q-gate-failure` (subreason: `pass-b-exec-error`): Pass B subagent timeout or crash

## Pass A — Mechanical Checks (inline, mandatory)

1. Mandatory-field completeness: every finding has all required schema fields; missing → demote to Unverified Hypotheses
2. **Tetrad-completeness check (v2.x):** verify all 4 tetrad tags (`presenting_symptom`, `underlying_cause`, `prognosis`, `confidence_interval`) are present on every finding. Missing any tetrad element → finding is malformed, demote to Unverified Hypotheses with reason `"tetrad-incomplete"`
3. Location verification: for each finding's `location`, check `location_verification_cache`; on cache miss, Read the file and verify; unverifiable → demote
4. CRITICAL/HIGH × Confidence floor: CRITICAL or HIGH severity requires Confidence ≥ MEDIUM; violation → demote or lower severity
5. Duplicate merge: any remaining duplicates N11 missed → merge with count
6. No-comment-echo: finding text must not merely quote the project's own TODO/FIXME without independent verification; violation → demote
7. No-LOW-only warning: if every main-body finding is LOW or INFO severity, emit a user-facing warning (not a halt) — signals possible under-sensitivity

Under token-cap: run `pass-a-minimal` (mandatory-field + location only; other checks skipped).

## Pass B — Adversarial Review (conditional subagent)

**Activation policy (cost-aware):** Pass B runs when ANY of:
- Report has ≥5 findings
- Any finding has severity CRITICAL or HIGH
- `--deep` flag is set

Otherwise: `pass_b: skipped-low-volume` with `pass_b_skip_reason: "fewer than 5 findings and no CRITICAL/HIGH severity"`.

**Pass B checks:**
1. Anti-iatrogenic: does any remediation introduce a worse defect than the one it fixes?
2. Evidence-rationale coherence: does the evidence excerpt actually support the stated rationale?
3. Dimension-classification correctness: is each finding in the right dimension?

Pass B uses a **clean lens** (subagent that hasn't seen the audit pipeline — avoids anchoring).
`pass_b_model` is recorded in provenance when Pass B demotes a finding.

## Token Budget

Pass A: ~200 tokens per finding (mechanical). Pass B: one subagent spawn, budget per the spawn cap.

## Backtrack / Aggregation

Adversarial self-review. No backtracking to N04..N09.

## Fan-out Cardinality

1:1 → N15 (E11) after both passes complete.

## Back-edge Endpoints

None. Q-GATE is a terminal verifier for the audit pipeline.
