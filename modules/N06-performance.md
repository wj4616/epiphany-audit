# N06 — DimensionAnalyzer.PERFORMANCE

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

Hot allocations in tight loops, algorithmic complexity blowups (O(n²) where O(n log n) is available), cache-hostile data structures, false sharing between threads, unnecessary repeated computation inside loops. Only report findings with a concrete, measurable performance impact. Speculative findings (no profiling evidence) must be tagged `confidence: LOW` with `verify_by` recommending profiling.

## Activation

R-ROUTE activates PERFORMANCE only when heuristics suggest a hot-path (import grep for sort/filter/loop patterns, `project_size.total_lines > 500`, etc.). See `dimensions/performance.md` activation triggers.

## Token Budget

30k tokens per invocation.

## Backtrack / Aggregation

Participant in BACKTRACKING via N10 (single re-emit cap).

## Fan-out Cardinality

1:many findings → N10 via E05.

## Back-edge Endpoints

E06: N10 → N06.
