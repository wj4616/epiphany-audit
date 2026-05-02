# N00a — AuditabilityPrerequisiteGate

**Type:** gate
**Mode:** inline
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
```

## Outputs

```
prerequisite_gate_result: "PASS" | "FAIL"
non_auditability_verdict: (on FAIL only) {
  gate_failed: "prerequisite",
  reason: string,
  fingerprints_observed: string[],
  recommended_remediation: string,
  findings_emitted: false
}
```

## Side Effects

None. This is a deterministic structural check — no LLM calls, no file writes.

## Halt Conditions

Gate FAIL does NOT halt — it emits a non-auditability verdict and routes to user via E00c. The user receives a diagnostic message with recommended remediation. No crash, no silent exit.

## Structural Surface Checks

Runs BEFORE the input-type detector. Three checks, all must pass:

### Check 1 — Minimum Token Count

Threshold: **≥ 50 tokens** of prose content.

Rationale: below 50 tokens, there is insufficient surface for any audit dimension to produce meaningful findings. The prerequisite gate is a cheap O(files) filter that prevents wasted pipeline execution.

Method: whitespace-tokenize all text files in the resolved target. Count tokens. If total < 50 → FAIL with reason `"input below minimum token threshold (<count> tokens)"`.

### Check 2 — Valid UTF-8

All text files in target must be valid UTF-8.

If any file fails UTF-8 decode → file is binary or corrupted. FAIL with reason `"binary or non-UTF-8 content detected"`.

### Check 3 — Structural Markers

At least **≥ 1 structural marker** must be present across all files:

| Marker Class | Examples |
|-------------|----------|
| Markdown heading | `#`, `##`, `###` (any level) |
| YAML frontmatter | `---\nname: ...` block at file start |
| XML tag | `<role>`, `<task>`, `<constraints>`, etc. |
| Code fence | Triple-backtick fenced block |
| Function declaration | `def `, `function `, `void <name>(`, etc. |

If no marker of any class is found → FAIL with reason `"no structural markers detected — input is plain text with no headings, frontmatter, code fences, or function declarations"`.

## PASS Path

All 3 checks pass → emit `prerequisite_gate_result: "PASS"`. Route to N00b via E00b.

## FAIL Path — Non-Auditability Verdict

Any check fails → emit `non_auditability_verdict` with:
- `gate_failed: "prerequisite"`
- `reason`: specific failure mode from the check that failed
- `fingerprints_observed`: what markers WERE observed (empty list is informative)
- `recommended_remediation`: actionable suggestion (e.g., "Add markdown headings, YAML frontmatter, or XML role/task tags to provide structural surface for audit")
- `findings_emitted: false`

Route to user via E00c. The user sees a formatted diagnostic — not a crash trace.

## Token Budget

O(files) with tiny constant. Directory listing + regex fingerprinting + YAML frontmatter parse. No LLM calls. Typical cost: < 50ms for a directory of 100 files.

## Backtrack / Aggregation

None. Single-pass gate.

## Fan-out Cardinality

E00b: 1:1 → N00b (PASS); E00c: 1:1 → user (FAIL — non-auditability verdict).

## Back-edge Endpoints

None. This node has no back-edges. It sits between N01 and N00b.
