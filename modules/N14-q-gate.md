# N14 — Q-GATE

**Type:** verifier
**Mode:** inline (Pass A) + conditional subagent (Pass B)
**Active in:** `audit`

## Inputs

```
formatted_report_markdown: string         // from N13 via E10 (control)
location_verification_cache: Cache        // from N10 (read-only; in-memory, not edge-modeled)
detector_confidence_trace: object         // from N00b via E_trace_detector (data; v2.0.2)
section_selector_confidence: object       // from N02 via E_trace_section (data; v2.0.2)
falsifiability_survival_log: object       // from N10 via E_log_thread (data; v2.0.2 — direct edge,
                                          // bypasses N11/N12/N13 which do not carry the log)
resolved_flags: (from N01, via project_model carrier per conventions.resolved_flags_propagation)
```

## Outputs

```
q_gate_result: {
  pass_a: "pass" | "pass-minimal" | "fail" | "skipped-token-cap",
  pass_b: "pass" | "fail" | "exec-error" | "skipped-token-cap" | "skipped-low-volume",
  pass_b_lens: string | null,
  pass_b_skip_reason: string | null
}
validated_report: string                  // markdown report after Pass A/B corrections,
                                          // with v2.x top-level frontmatter fields populated
tetrad_completeness: {                    // computed during Pass A check #2
  total_findings: integer,
  tetrad_complete: integer,
  incomplete_ids: string[]
}
two_axis_scores: {                        // computed during Pass A check #8
  creativity: number,
  functional_correctness: number
}
two_axis_scores_overridden_by_user: boolean   // true if user waived the gate
```

## Side Effects

Read-only (may read source files for location verification on cache miss).

## Halt Conditions

- `halt-on-q-gate-failure` (subreason: `pass-a`): Pass A fails mandatory checks
- `halt-on-q-gate-failure` (subreason: `pass-b`): Pass B content-fail
- `halt-on-q-gate-failure` (subreason: `pass-b-exec-error`): Pass B subagent timeout or crash
- `halt-on-q-gate-failure` (subreason: `two-axis-below-threshold`): `(creativity < 7 OR functional_correctness < 7) AND (user did not override)` — explicit parentheses to disambiguate (v2.0.2 fix; without parens, AND binds tighter and `creativity < 7 OR (functional_correctness < 7 AND no_override)` would silence override on creativity failure).
- `halt-on-q-gate-failure` (subreason: `frontmatter-trace-incoherence`): Pass A check #9 detected mismatch between frontmatter dimensions_activated and section_selector_confidence

## Pass A — Mechanical Checks (inline, mandatory)

1. **Mandatory-field completeness:** every finding has all required schema fields; missing → demote to Unverified Hypotheses
2. **Tetrad-completeness check (v2.x):** verify all 4 tetrad tags (`presenting_symptom`, `underlying_cause`, `prognosis`, `confidence_interval`) are present on every finding. Missing any tetrad element → finding is malformed, demote to Unverified Hypotheses with reason `"tetrad-incomplete"`. Aggregate result into `tetrad_completeness` output.
3. **Location verification:** for each finding's `location`, check `location_verification_cache`; on cache miss, Read the file and verify; unverifiable → demote
4. **CRITICAL/HIGH × Confidence floor:** CRITICAL or HIGH severity requires Confidence ≥ MEDIUM; violation → demote or lower severity
5. **Duplicate merge:** any remaining duplicates N11 missed → merge with count
6. **No-comment-echo:** finding text must not merely quote the project's own TODO/FIXME without independent verification; violation → demote
7. **No-LOW-only warning:** if every main-body finding is LOW or INFO severity, emit a user-facing warning (not a halt) — signals possible under-sensitivity
8. **Two-axis hard gate (v2.x):** compute `creativity` and `functional_correctness` scores per the SKILL.md §18 rubric. If either < 7 AND no user override given AND mode != `--dry-run` → `halt-on-q-gate-failure` (subreason: `two-axis-below-threshold`). Under `--confirm-all` or `--dry-run`, prompt the user to override; record waiver as `two_axis_scores_overridden_by_user: true` in the validated_report frontmatter and run log.
9. **Frontmatter-trace coherence (v2.x):** verify that `dimensions_activated` in the report frontmatter matches the ACTIVATED set in `section_selector_confidence`; verify that `input_type` matches `detector_confidence_trace.classified_type`. Any mismatch → `halt-on-q-gate-failure` (subreason: `frontmatter-trace-incoherence`); diagnostic lists the divergence.

Under token-cap: run `pass-a-minimal` (mandatory-field + location + tetrad-completeness only; checks 4–9 skipped, scored as `pass-minimal`). The two-axis gate is skipped under token-cap and recorded as `two_axis_scores: {creativity: null, functional_correctness: null}` with `pass_a: "pass-minimal"`.

### Two-Axis Score Computation Rubric (v2.0.2 — mechanical)

Both axes are scored on a 0–10 integer scale by evaluating deterministic predicates against the validated_report's frontmatter and finding bodies. Each axis sums signal points; the score is `min(10, max(0, sum))`. Two implementations evaluating the same report MUST produce the same scores.

**Creativity** — sum of (each predicate worth 1 point unless noted):

| Predicate | Points | Source |
|-----------|-------:|--------|
| `tetrad_completeness.tetrad_complete == tetrad_completeness.total_findings` AND `total_findings >= 1` | 2 | frontmatter |
| `falsifiability_survival_log.survived >= 1` | 1 | frontmatter |
| `falsifiability_survival_log.survived + downgraded + dropped >= count(severity in {MEDIUM, HIGH, CRITICAL})` (full coverage) | 2 | frontmatter + finding bodies |
| At least one finding has `falsifiability.counter_argument` field present | 1 | finding body |
| `dimensions_activated` includes ≥3 of {CORRECTNESS, MAINTAINABILITY, ARCHITECTURE, PERFORMANCE, SECURITY} | 1 | frontmatter |
| `gap_dimensions_auto_added.length >= 1` (B-FIND surfaced ≥1 blindspot) | 1 | frontmatter |
| `section_selector_confidence.dimensions` records SUPPRESSED entries with reasons (matrix evaluation visible) | 1 | frontmatter |
| At least one finding has severity HIGH or CRITICAL with `falsifiability.status: "survived"` (tournament + falsifiability for high-impact) | 1 | finding body |

Maximum: 10. To pass the gate (≥7), a report must have complete tetrad coverage (2pts), full falsifiability coverage (2pts), one falsifiability counter_argument field (1pt), at least three activated dimensions (1pt), and at least one of {gap auto-added, section_selector with suppressions, surviving high-impact finding} (1pt) = 7. Stronger reports score higher.

**Functional correctness** — sum of (each predicate worth 1 point unless noted):

| Predicate | Points | Source |
|-----------|-------:|--------|
| Report validates against `audit-report-v1.schema.json` | 2 | jsonschema validation |
| `detector_confidence.confidence in {"high","marginal"}` (not "ambiguous") | 1 | frontmatter |
| `q_gate.pass_a in {"pass","pass-minimal"}` AND `q_gate.pass_b != "fail"` AND `q_gate.pass_b != "exec-error"` | 1 | frontmatter |
| Every finding's `location` resolves in `location_verification_cache` (or N14 cache-miss Read succeeded) | 1 | finding bodies |
| `dimensions_activated` includes both floor dimensions (CORRECTNESS, MAINTAINABILITY) | 1 | frontmatter |
| Report's `input_type` is one of the 6 supported values AND matches `detector_confidence.classified_type` | 1 | frontmatter — frontmatter-trace coherence |
| `tetrad_completeness.incomplete_ids.length == 0` | 1 | frontmatter |
| All findings with severity in {CRITICAL, HIGH} have `confidence in {"HIGH","MEDIUM"}` (CRITICAL/HIGH × confidence floor honored) | 1 | finding bodies |
| `subtree_grouping_applied == false` OR (true AND `subtrees.length >= 1`) (consistency) | 1 | frontmatter |

Maximum: 10. To pass the gate (≥7), a report must validate against schema (2pts), have a non-ambiguous detector classification (1pt), pass q_gate (1pt), have verified locations (1pt), include floor dimensions (1pt), and have coherent input_type (1pt) = 7. Reports failing schema validation cannot pass the gate.

**Reference implementation (Python):** `tests/integration/test_two_axis_scoring.py` — implements `TwoAxisScorer.score(report_dict)` that returns `{"creativity": int, "functional_correctness": int}`. Two calls with the same input MUST yield the same scores (determinism tests included). Each rubric predicate has a corresponding unit test.

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

## Validated Report Frontmatter Population

Before passing to N15, N14 ensures the validated_report's YAML frontmatter contains the following top-level fields (matching audit-report-v1 schema):

- `tetrad_completeness` (from check #2)
- `two_axis_scores` (from check #8)
- `falsifiability_survival_log` (passed through from N10's aggregated output)
- `detector_confidence` (passed through from N00b's trace)
- `section_selector_confidence` (passed through from N02's trace)
- `two_axis_scores_overridden_by_user` (only when override fired)

If any of these fields are absent in the markdown N13 produced, N14 inserts them in-place into the frontmatter before emitting validated_report. This is a structural fix-up, not a content edit, so it does not invalidate Pass A.

## Token Budget

Pass A: ~500-800 tokens per finding (mechanical checks ~200 + semantic checks ~400). Two-axis scoring + frontmatter coherence add ~1k tokens once per report. Pass B: one subagent spawn, budget per the spawn cap.

## Backtrack / Aggregation

Adversarial self-review. No backtracking to N04..N09.

## Fan-out Cardinality

1:1 → N15 (E11) after both passes complete.

## Back-edge Endpoints

None. Q-GATE is a terminal verifier for the audit pipeline.
