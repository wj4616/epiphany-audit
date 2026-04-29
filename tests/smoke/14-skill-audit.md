# Smoke Test 14 — Skill Audit

**Scenario:** Run `/epiphany-audit --audit` targeting a Claude Code skill directory.
Input type auto-detected as `skill`.

**Setup:**
- Target is a skill directory containing SKILL.md, modules/, schemas/, and supporting files
- Skill is git-tracked

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-skill/>`
2. Allow N00a/N00b to detect `skill` type (YAML frontmatter fingerprint, modules/ subdirectory, skill structural markers)
3. Allow audit pipeline (N01–N14) to complete
4. Respond "y" to save prompt (N15)

**Expected outcomes:**
- N00b classifies input as `skill` with confidence ≥0.6
- N01 project_model includes skill-specific fields: `skill_name` (from SKILL.md frontmatter), `module_count`, `schema_count`
- N02 section-activation matrix: CORRECTNESS + MAINTAINABILITY ACTIVATE; ARCHITECTURE, PERFORMANCE, SECURITY CONDITIONAL
- N03 B-FIND offers skill-specific gap dimensions (module-contract-completeness, cross-reference-integrity, schema-consistency, halt-state-coverage)
- Findings may span multiple files (SKILL.md + individual modules)
- Every finding has the medical-diagnostic tetrad
- Audit report frontmatter: `input_type: skill`
- `project_content_sha256` computed across all skill files (not just SKILL.md)
- `--fix` transactional scope: multi-file per fix-group (atomic commit/rollback across all files in the fix-group)
