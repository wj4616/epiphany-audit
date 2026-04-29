# N20 — PerFixVerifier

**Type:** verifier
**Mode:** inline
**Active in:** `fix`

## Inputs

```
changed_files: string[]         // files modified by this fix attempt
baseline_metrics: object        // from N18
test_cmd: string                // resolved test command
failure_context_from_prior: object | null  // present on retry pass
```

## Outputs

```
verify_result: "PASS" | "FAIL"
failure_context: {
  failure_class: "verification-failure" | "commit-hook-failure" | "git-operation-failure" | "type-check-failure" | "targeted-test-failure",
  diagnostic: string
} | null
```

## Side Effects

Read-only (runs tests and type checks; does NOT commit — that is N19's responsibility).

## Halt Conditions

None. N20 emits a fail-signal; E_repair routing (not N20) decides retry vs replan vs cap-hit.

## Verification Steps

1. **Targeted tests**: run tests that exercise the changed files (grep test directory for imports of changed files; run those test files only)
2. **Type check on changed files**: run type checker on the changed file set only (e.g., `mypy <files>`, `tsc --noEmit <files>`)

PASS iff: targeted tests pass AND type check has no new errors compared to baseline.

## Failure Classes

| Class | Trigger |
|-------|---------|
| `targeted-test-failure` | Targeted test run has new failures (not in baseline) |
| `type-check-failure` | Type checker reports new errors (not in baseline) |
| `commit-hook-failure` | `git commit` rejected by a pre-commit hook |
| `git-operation-failure` | git command fails for non-hook reason |
| `verification-failure` | Generic: none of the above but verification cannot complete |

## Token Budget

Minimal (shell command execution).

## Backtrack / Aggregation

Emits fail-signal; E_repair routing is external to N20.

## Fan-out Cardinality

1:1 (verifies one fix-group at a time, matching N19's serial loop).

## Back-edge Endpoints

E15: N20 success → N19 (proceed to next fix-group).
E_repair: N20 fail → N19 (1st: retry) or N17 (2nd: replan).
