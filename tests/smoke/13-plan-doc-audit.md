# Smoke Test 13 — Plan Document Audit

**Scenario:** Run `/epiphany-audit --audit` targeting an implementation plan document.
Input type auto-detected as `plan-document`.

**Setup:**
- Target is a single `.md` file containing a build/implementation plan with phases, checkpoints, and dependencies
- File is git-tracked

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-plan.md>`
2. Allow N00a/N00b to detect `plan-document` type
3. Allow audit pipeline (N01–N14) to complete
4. Respond "y" to save prompt (N15)

**Expected outcomes:**
- N00b classifies input as `plan-document` with confidence ≥0.6
- N02 section-activation matrix: CORRECTNESS + MAINTAINABILITY ACTIVATE; ARCHITECTURE, PERFORMANCE, SECURITY SUPPRESS
- N03 B-FIND offers plan-specific gap dimensions (phase-dependency-completeness, checkpoint-verifiability, task-granularity, rollback-strategy)
- Code-specific finding classes suppressed
- No code-level finding classes emitted (no off-by-one, null-dereference, race-condition, resource-leak)
- Every finding has the medical-diagnostic tetrad
- Audit report frontmatter: `input_type: plan-document`
- `--fix` confirmation thresholds follow plan-document rules: auto-apply checkpoint additions, require confirmation for phase reordering or dependency corrections
