# N25 — ImprovementBrainstormer (IB)

**Type:** analyzer
**Mode:** inline (phase 1); inline + optional subagent (phase 2 under `--deep` when ≥8 candidates)
**Active in:** `improve`

## Inputs

```
improvement_context: (from N24)
resolved_flags: (from entry)
```

## Outputs

```
improvement_candidates: ImprovementCandidate[]  // fully elaborated
```

## Side Effects

- Optional subagent spawn (phase 2 only; 0 or 1 spawn; requires `--deep` AND ≥8 phase-1 candidates)
- Write-log

## Halt Conditions

None. Subagent failures produce partial candidates; N26/N27 handle gracefully.

## Two-Phase Execution

**Phase 1 (always inline):** Generate lightweight raw candidate list. For each candidate: one-line tag + category seed — must be one of the `area` enum values from improvement-report-v1 schema: `developer-experience`, `testing`, `architecture`, `performance`, `tooling`, `dependencies`, `documentation`. No full description/action/success_measure yet — keeps phase 1 fast and token-cheap.

**Phase 2:** Elaborate each candidate with full `description`, `action`, `success_measure`.
- If `--deep` is set AND ≥8 raw candidates from phase 1: spawn one subagent to elaborate all candidates in parallel.
- Otherwise (no `--deep`, or <8 candidates): elaborate inline.

## Strict Exclusions (GoT anti-patterns to filter out at brainstorm time)

- Cosmetic-only changes (rename files, fix typos)
- Re-architectures without concrete measured benefit
- Generic "best practices" not grounded in project-specific evidence
- Improvements already implied by audit findings (those are findings, not improvements — no double-counting)

## Token Budget

Phase 1: ~500 tokens. Phase 2 inline: ~500 tokens per candidate. Phase 2 subagent: one spawn (full context).

## Backtrack / Aggregation

Participant in AGGREGATION via N26.

## Fan-out Cardinality

1 optional subagent spawn for phase 2. Produces N candidates → N26.

## Back-edge Endpoints

None.
