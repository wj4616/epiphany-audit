# Smoke Test 15 — Detailed Prompt Audit

**Scenario:** Run `/epiphany-audit --audit` targeting a detailed prompt document with XML tag structure.
Input type auto-detected as `prompt`.

**Setup:**
- Target is a `.md` file containing a detailed AI prompt with structured XML tags, output format spec, and verification scaffolding
- File is git-tracked

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-prompt.md>`
2. Allow N00a/N00b to detect `prompt` type (XML tag structure, system/user/tool role markers, structured output format)
3. Allow audit pipeline (N01–N14) to complete
4. Respond "y" to save prompt (N15)

**Expected outcomes:**
- N00b classifies input as `prompt` with confidence ≥0.6
- N02 section-activation matrix: CORRECTNESS + MAINTAINABILITY ACTIVATE; ARCHITECTURE SUPPRESS; PERFORMANCE SUPPRESS; SECURITY ACTIVATE
- N03 B-FIND offers prompt-specific gap dimensions (VERIFICATION-SCAFFOLDING, OUTPUT-SCHEMA-COMPLETENESS, TECHNIQUE-APPLICATION, CONSTRAINT-SATURATION)
- Code-level finding classes suppressed (off-by-one, race-condition, resource-leak, null-dereference, missing-test-coverage); prompt-specific classes active (prompt-injection-surface, schema-drift, structural-contradiction, technique-application-inconsistency, output-format-underspecification)
- Every finding has the medical-diagnostic tetrad
- Audit report frontmatter: `input_type: prompt`
- `--deep` semantics: prompt-graph traversal (trace tag nesting, role transitions, tool definitions)
- `--fix` confirmation thresholds: auto-apply `<meta>` tag additions and output-format additions; require confirmation for prompt body, frontmatter, or technique changes
