# Smoke Test 12 — Specification Document Audit

**Scenario:** Run `/epiphany-audit --audit` targeting a standalone specification document.
Input type auto-detected as `specification-document`.

**Setup:**
- Target is a single `.md` file containing a design spec with requirements and acceptance criteria
- File is git-tracked (single-file repo or within a repo)

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-spec.md>`
2. Allow N00a/N00b to detect `specification-document` type
3. Allow audit pipeline (N01–N14) to complete
4. Respond "y" to save prompt (N15)

**Expected outcomes:**
- N00b classifies input as `specification-document` with confidence ≥0.6
- N02 section-activation matrix: CORRECTNESS + MAINTAINABILITY ACTIVATE; ARCHITECTURE C(a) CONDITIONAL (activate if ≥3 subsystems or inter-component contracts); PERFORMANCE SUPPRESS; SECURITY C(e) CONDITIONAL (activate if auth, data handling, or user-input boundaries defined)
- N03 B-FIND offers spec-specific gap dimensions (REQUIREMENT-COMPLETENESS, CROSS-REFERENCE-INTEGRITY, ACCEPTANCE-CRITERIA-TESTABILITY, DOMAIN-CONSISTENCY)
- Code-specific finding classes suppressed (off-by-one, null-dereference, race-condition, resource-leak, missing-error-handling, type-error)
- Findings use document-level locations (heading paths or line numbers), not source-file paths
- Every finding has the medical-diagnostic tetrad (presenting_symptom, underlying_cause, prognosis, confidence_interval)
- Audit report frontmatter: `input_type: specification-document`
- Report slug derived from spec filename
