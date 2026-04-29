# N12 — Prioritizer

**Type:** scorer
**Mode:** inline
**Active in:** `audit`

## Inputs

```
deduplicated_findings: Finding[]   // from N11
```

## Outputs

```
prioritized_findings: Finding[]    // sorted by priority_score descending
punch_list: Finding[]              // CRITICAL + HIGH always; + MEDIUM until 15 total
```

## Side Effects

None.

## Halt Conditions

None.

## Priority Score Formula (deterministic)

```
severity_weight:    CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1, INFO=0
confidence_weight:  HIGH=3, MEDIUM=2, LOW=1
effort_weight:      trivial=1, modest=2, significant=3

priority_score = (severity_weight × confidence_weight) / effort_weight
```

INFO findings score 0 by definition.

## Punch List Construction

Include: all CRITICAL findings + all HIGH findings + MEDIUM findings until total reaches 15 (or all exhausted). Sorted by `priority_score` descending within each severity tier.

## Token Budget

Minimal (arithmetic only).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N13.

## Back-edge Endpoints

None.
