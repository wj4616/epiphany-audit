# N08 — DimensionAnalyzer.MAINTAINABILITY

**Type:** analyzer
**Mode:** inline (default); subagent under `--deep`
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
file_subset: string[]
resolved_flags: (from N01)
```

## Outputs

```
raw_findings: Finding[]
```

## Side Effects

Read-only.

## Halt Conditions

None.

## Analysis Scope

Dead code (unreachable branches, unused variables/functions with no callers), misleading identifiers (names that contradict behavior), stale TODOs referencing already-resolved issues, test coverage gaps on failure-mode branches, excessive function complexity (>50 lines with no natural split), magic numbers/strings without named constants.

**Floor dimension.** Always runs. Cannot be disabled.

## Token Budget

30k tokens per invocation.

## Backtrack / Aggregation

Participant in BACKTRACKING via N10 (single re-emit cap).

## Fan-out Cardinality

1:many findings → N10 via E05.

## Back-edge Endpoints

E06: N10 → N08.
