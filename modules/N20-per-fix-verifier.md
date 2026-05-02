# N20 — PerFixVerifier

**Type:** verifier
**Mode:** inline
**Active in:** `fix`

## Inputs

```
changed_files: string[]         // files modified by this fix attempt
baseline_metrics: object        // from N18
test_cmd: string                // resolved test command (code only)
input_type: string              // from N16 triage — selects per-type verification logic (v2.0.1)
failure_context_from_prior: object | null  // present on retry pass
```

## Outputs

```
verify_result: "PASS" | "FAIL"
failure_context: {
  failure_class: "verification-failure" | "commit-hook-failure" | "git-operation-failure"
                | "type-check-failure" | "targeted-test-failure"
                | "markdown-lint-failure" | "cross-reference-failure"
                | "schema-validation-failure" | "dependency-cycle-failure"
                | "tool-unavailable",   // v2.0.2: see Failure Classes table + Tool-Availability Semantics
  diagnostic: string
} | null
```

## Side Effects

Read-only (runs tests and type checks; does NOT commit — that is N19's responsibility).

## Halt Conditions

None. N20 emits a fail-signal; E_repair routing (not N20) decides retry vs replan vs cap-hit.

## Verification Steps (per-input-type, v2.0.1)

The verification protocol switches on `input_type` from the triage result. For multi-file fix-groups (skill type), each step runs against the full changed-file set.

### Code (`input_type: "code"`) — v1.x unchanged

1. **Targeted tests**: run tests that exercise the changed files (grep test directory for imports of changed files; run those test files only)
2. **Type check on changed files**: run type checker on the changed file set only (e.g., `mypy <files>`, `tsc --noEmit <files>`)

PASS iff: targeted tests pass AND type check has no new errors compared to baseline.

### Specification Document (`input_type: "specification-document"`)

1. **Markdown lint**: `markdownlint <file>` — no new violations vs baseline (if no markdownlint, fall back to checking heading-hierarchy validity: no jumps from `#` to `###`)
2. **Cross-reference resolution**: every `[text](#anchor)` and "see Section X" reference must resolve within the doc
3. **Frontmatter schema (if present)**: YAML frontmatter parses cleanly; required fields present

PASS iff: all 3 checks pass.

### Plan Document (`input_type: "plan-document"`)

1. **Phase-dependency cycle detection**: build dependency graph from edited content; reject cycles
2. **Checkpoint integrity**: every checkpoint references existing tasks; every task is in some phase
3. **Frontmatter schema (if present)**: parses cleanly

PASS iff: all 3 checks pass.

### Claude Code AI Agent Skill (`input_type: "skill"`)

1. **SKILL.md frontmatter validation**: parses as YAML; `name` + (`description` OR `triggers`) present
2. **Module count consistency**: if SKILL.md references `modules/N0X-*.md`, those files exist
3. **pytest run**: if `tests/` directory exists, run `pytest -q` against the skill's tests; no new failures vs baseline
4. **dimension plugin schema (if dimensions/ exists)**: each `dimensions/*.md` validates against `dimension-plugin-v1.schema.json`

PASS iff: all applicable checks pass (skip 3-4 if directories absent).

### Detailed Prompt (`input_type: "prompt"`)

1. **XML well-formedness**: if the prompt contains XML tags, they parse without errors
2. **Meta-source resolution**: every `<meta source="..."/>` reference resolves (file exists or is a known skill name)
3. **Embedded schema validation (if present)**: any embedded JSON schema parses cleanly

PASS iff: all applicable checks pass.

### Ambiguous Text (`input_type: "ambiguous-text"`)

Universal-only: no markdown lint, no schema check. Verification PASS iff the file remains valid UTF-8 and contains at least one structural marker (per N00a's check). Effectively a no-op for ambiguous text — fix-groups for this type are rare and the contract is permissive.

## Failure Classes

| Class | Trigger | Applies to |
|-------|---------|------------|
| `targeted-test-failure` | Targeted test run has new failures | code, skill |
| `type-check-failure` | Type checker reports new errors | code |
| `markdown-lint-failure` | Markdown lint or heading-hierarchy violation | spec, plan, skill, prompt |
| `cross-reference-failure` | Broken section reference, anchor, or meta-source | spec, plan, prompt, skill |
| `schema-validation-failure` | Frontmatter or embedded schema fails to parse / validate | all |
| `dependency-cycle-failure` | Plan dependency graph contains a cycle | plan |
| `commit-hook-failure` | `git commit` rejected by a pre-commit hook | all |
| `git-operation-failure` | git command fails for non-hook reason | all |
| `verification-failure` | Generic: none of the above but verification cannot complete | all |
| `tool-unavailable` | Required external tool not installed and no fallback exists (v2.0.2) | non-code types |

## Tool-Availability Semantics (v2.0.2 — F115 fix)

Per-input-type verification depends on external tools. Behavior when a tool is unavailable:

| Verification step | Required tool | Fallback | If neither available |
|-------------------|--------------|----------|----------------------|
| Spec — markdown lint | `markdownlint` | heading-hierarchy validator (in-skill, deterministic) | n/a — fallback always present |
| Spec — cross-reference resolution | (in-skill string-matcher) | n/a | n/a — always available |
| Spec/Plan/Skill/Prompt — frontmatter schema | `python-jsonschema` library | (in-skill structural check: required keys present, parseable YAML) | `tool-unavailable` failure |
| Plan — dependency-cycle detection | (in-skill graph algorithm) | n/a | n/a — always available |
| Skill — pytest run | `pytest` | n/a | `tool-unavailable` failure when `tests/` directory exists |
| Skill — dimension plugin schema | `python-jsonschema` library | (fallback: structural check on YAML frontmatter — required keys per dimension-plugin-v1) | `tool-unavailable` failure |
| Prompt — XML well-formedness | (in-skill `xml.etree.ElementTree` or equivalent) | n/a | n/a — language stdlib |
| Prompt — embedded JSON schema parse | `python-jsonschema` library | (in-skill JSON parse check) | `tool-unavailable` failure |

**Override:** the `--skip-verification-tool=<tool-name>` CLI flag (new in v2.0.2) skips the named tool's check and records the skip in the run log as `verification_tool_skipped: [<tool-name>]`. Use only when the user has explicitly verified the change manually.

**N18 PreFlight** SHOULD detect known-required tools at baseline-capture time and emit `halt-on-baseline-failure` (subreason: `required-tool-missing`) if a tool is needed for the current input_type but unavailable AND no fallback exists.

**Default behavior:** when a tool is unavailable AND no fallback applies, N20 returns `verify_result: FAIL` with `failure_class: tool-unavailable` and a diagnostic naming the missing tool. The fix-group is rolled back via the standard E_repair path. This is the "FAIL by default" choice over "PASS by default" — silent verification skipping is unsafe under `--auto`.

## Token Budget

Minimal (shell command execution).

## Backtrack / Aggregation

Emits fail-signal; E_repair routing is external to N20.

## Fan-out Cardinality

1:1 (verifies one fix-group at a time, matching N19's serial loop).

## Back-edge Endpoints

E15: N20 success → N19 (proceed to next fix-group).
E_repair: N20 fail → N19 (1st: retry) or N17 (2nd: replan).
