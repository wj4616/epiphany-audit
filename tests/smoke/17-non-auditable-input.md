# Smoke Test 17 — Non-Auditable Input (N00a Gate Halt)

**Scenario:** Run `/epiphany-audit --audit` targeting an input that fails the N00a
AuditabilityPrerequisiteGate. Pipeline halts with a structured non-auditability verdict.

**Setup:**
- Target is a near-empty file, a binary file, or a file with no detectable semantic structure
- Example: a `.gitkeep` file, a 2-line stub with no content, or a compiled binary

**Actions:**
1. Invoke `/epiphany-audit --audit <path-to-non-auditable-file>`
2. N00a runs structural surface checks
3. N00a emits FAIL verdict

**Expected outcomes:**
- N00a reports at least one structural prerequisite failure (no parseable sections, insufficient content, or binary/unreadable)
- Pipeline emits `halt-on-non-auditable-input` envelope before any analysis nodes run
- No audit report saved (no findings to report)
- No fix offer emitted (E21 never reached)
- Halt envelope includes: `node: N00a`, `halt_class: non-auditable-input`, `reason` detailing which prerequisite(s) failed
- Token budget minimal — pipeline stops at gate, no analysis nodes consume tokens
