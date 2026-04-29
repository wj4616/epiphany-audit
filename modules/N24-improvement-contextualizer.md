# N24 — ImprovementContextualizer (IC)

**Type:** analyzer
**Mode:** inline
**Active in:** `improve` (`--improve` only; fires via E16 after N15 save-decision)

## Inputs

```
project_model: (from N01, already in context)
validated_report: (from N14, already in context — the Q-GATE-passed findings)
```

## Outputs

```
improvement_context: {
  project_capability_map: string,    // what the project is and does
  health_summary: string,            // what audit findings reveal about structural weaknesses
  healthy_areas: string[],           // dimensions NOT flagged (worth preserving)
  improvement_search_constraints: string  // what to look for and what to avoid
}
```

## Side Effects

Read-only. Works entirely from in-memory context (N01's project_model + N14's report). Opens NO additional files.

## Halt Conditions

None. Failure (e.g., context too large) is caught; N27 emits `improvement_partial: true`.

## Purpose

Synthesizes an improvement-analysis frame BEFORE brainstorming. Prevents N25 from brainstorming improvements already addressed by audit findings (double-counting) and focuses the search on what matters for this project.

## Token Budget

Moderate (~2k tokens for synthesis from existing context).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N25 (E17).

## Back-edge Endpoints

None.
