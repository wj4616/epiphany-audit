# N05 — DimensionAnalyzer.ARCHITECTURE

**Type:** analyzer
**Mode:** inline (default); subagent under `--deep` — subject to the **shared spawn cap** declared in `graph.json` `conventions.spawn_cap`: N04..N09 share ONE subagent slot, not one per analyzer.
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

Excessive coupling, circular dependencies, god objects (>10 distinct responsibilities), duplicated non-trivial logic, invariant gaps. **Latent findings** (safe now, will break under specific future conditions) are tagged with `reachable: false` and a `notes: "reachable when: <condition>"` annotation.

## Anti-Patterns

Same as N04 plus: do not report refactors without a concrete defect; do not flag large classes unless they demonstrably have >10 distinct responsibilities.

## Token Budget

30k tokens per invocation (intra-node soft budget).

## Backtrack / Aggregation

Participant in BACKTRACKING via N10 (single re-emit cap).

## Fan-out Cardinality

1:1 → N10 via E05 (producing many findings; the fan-in is described by E05's multi-source topology).

## Back-edge Endpoints

E06: N10 → N05 (backtrack feedback, single re-emit cap).
