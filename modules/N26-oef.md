# N26 — OverEngineeringFilter (OEF)

**Type:** filter
**Mode:** inline
**Active in:** `improve`

## Inputs

```
improvement_candidates: ImprovementCandidate[]  // from N25
```

## Outputs

```
survivors: ImprovementCandidate[]        // passed the filter
discarded_improvements: {               // for --verbose section in N27
  candidate: ImprovementCandidate,
  discard_rationale: string
}[]
```

## Side Effects

None (pure filtering in memory).

## Halt Conditions

None.

## Scoring

Each candidate receives two scores:
- `utility_score`: 1 = marginal, 2 = notable, 3 = high
- `cost_score`:    1 = trivial, 2 = modest, 3 = significant

## Filter Rules (discard when ANY of)

1. `cost > utility` (not worth the investment)
2. `utility = 1` regardless of cost (marginal-utility improvements not surfaced)
3. The candidate's `description` or `action` prose contains speculative language ("might", "could", "potentially", "may help") AND lacks any quantitative or evidentiary anchor (v2.0.2 — F117 fix: tightened to reduce false positives on legitimate hedge with concrete estimates).
   - **Discard iff** the speculative term appears AND the prose does NOT contain any of: a digit + unit (e.g., "12%", "3 days", "200ms"), a profiler/measurement marker ("measured", "verified", "profiled", "benchmarked", "based on"), or a quantified comparison ("X% faster", "from N to M").
   - **Keep iff** the speculative term appears alongside concrete evidence — "could reduce build time by 12% based on profiler" passes; "might help onboarding" alone gets discarded.

## Categorization (mutually exclusive; `notable` takes precedence)

| Category    | Criterion |
|-------------|-----------|
| `notable`   | utility = 3 AND cost ≤ 2 |
| `quick-win` | utility ≥ 2 AND cost = 1 AND NOT notable |
| `worthwhile`| all remaining survivors (utility ≥ cost ≥ 2 AND NOT notable) |

After filtering, all survivors have `utility ≥ 2`.

## Zero Survivors

If no candidates survive the filter, N27 emits a report stating: *"No improvements above the utility/cost threshold were found. This is a valid result — the project may be well-optimized in its current state."* N26 does NOT generate improvements just to have output.

## Token Budget

Moderate (~1-3k tokens; speculative-language detection in rule 3 requires LLM reading of candidate prose; utility/cost scoring is arithmetic).

## Backtrack / Aggregation

AGGREGATION owner (improvement side: candidate filtering + categorization).

## Fan-out Cardinality

1:1 → N27 via E19.

## Back-edge Endpoints

None.
