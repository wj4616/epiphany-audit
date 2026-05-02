# N04 — DimensionAnalyzer.CORRECTNESS

**Type:** analyzer
**Mode:** inline (default); subagent under `--deep` when analyzer fan-out budget allows (capped at 1 batched subagent slot for all over-cap analyzers combined)
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
file_subset: string[]       // files to analyze (from R-ROUTE + B-FIND activation map)
resolved_flags: (from N01)
```

## Outputs

```
raw_findings: Finding[]    // unverified; fed to N10 FPV
```

## Side Effects

Read-only. Reads source files via Read tool (no writes).

## Halt Conditions

None. Analysis failures are logged; the node produces whatever findings it can within budget.

## Analysis Scope

Logic errors, type/lifetime, boundary violations, concurrency, resource leaks, error paths. See `dimensions/correctness.md` for the full taxonomy and prompt template.

**Floor dimension.** Always runs regardless of R-ROUTE activation map. Cannot be disabled.

## Anti-Patterns (findings this node MUST NOT produce)

- Stylistic preferences disguised as bugs
- Findings without reading the actual code (hallucinated `file:line`)
- Generic advice applicable to any project
- Duplicate findings (N11 handles dedup, but N04 should not emit obvious duplicates)
- Echoing project's own TODO/FIXME as findings

## Token Budget

30k tokens per analyzer invocation (intra-node soft budget under `--deep`; see SKILL.md §2 `--deep` flag).

## Backtrack / Aggregation

Participant in BACKTRACKING: N10 FPV may re-emit one finding back to N04 with a re-analysis request (single cap). N04 must honor the re-analysis context and either confirm or revise the finding.

## Fan-out Cardinality

1:1 → N10 via E05 (producing many findings; the fan-in is described by E05's multi-source topology).

## Back-edge Endpoints

E06: N10 → N04 (backtrack feedback, single re-emit cap).
