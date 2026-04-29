# N11 — FindingsAggregator

**Type:** aggregator
**Mode:** inline
**Active in:** `audit`

## Inputs

```
verified_findings: Finding[]   // from N10
```

## Outputs

```
deduplicated_findings: Finding[]
```

## Side Effects

None (pure transformation in memory).

## Halt Conditions

None.

## Aggregation Rules

1. **Dedup by pattern+location**: two findings are duplicates iff they share the same `location` (file:line-range) AND describe the same defect class (same dimension + same severity + substantively identical rationale). Merge into one finding with `count: N` in notes.
2. **Cross-dimension overlap merge**: if two findings from different dimensions describe the same root cause at the same `location`, keep the one with higher `priority_score` and list the other dimension in the merged finding's `dimensions` array.
3. **Count-collapse**: wall-of-low-severity-nitpicks at the same location → collapse into one finding with `count` in notes and the highest severity among the group.

## Token Budget

Minimal (in-memory set operations, no file reads).

## Backtrack / Aggregation

AGGREGATION owner (audit side).

## Fan-out Cardinality

N:1 (fan-in from multiple findings; emits smaller deduplicated set).

## Back-edge Endpoints

None.
