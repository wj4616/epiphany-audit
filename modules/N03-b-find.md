# N03 — BlindspotFinder (B-FIND)

**Type:** meta-analyzer
**Mode:** inline
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
dimension_activation_map: (from N02)
resolved_flags: (from N01)
```

## Outputs

```
updated_dimension_activation_map: {
  activated: string[],
  skipped: { dimension: string, reason: string }[]
}
gap_dimensions_auto_added: string[]   // HIGH-confidence gaps added in default mode
gap_dimensions_offered: string[]      // populated only under --deep
gap_dimensions_accepted: string[]     // subset offered that user opted into (--deep only)
```

## Side Effects

- Interactive (only under `--deep`): `include gap dimension <name>? (y/n/skip-all)` prompt per gap candidate
- Write-log: structured event per gap dimension considered

## Halt Conditions

- `halt-on-user-abort`: ctrl-C at B-FIND prompt (only under `--deep`)

Logged, not halted:
- Invalid input at B-FIND prompt → loop with format reminder, do not halt

## Default Mode Behavior

AUTO-ADD HIGH-confidence gap dimensions to the activation map without prompting. A gap dimension is HIGH-confidence when:
- The project type strongly implies the dimension (e.g., a web API project implies an accessibility dimension if the project serves HTML)
- At least 2 independent heuristics agree (language + framework marker + import grep)

Gap dimensions added appear in `gap_dimensions_auto_added` in the audit report frontmatter.

## `--deep` Mode Behavior

Prompt the user per gap candidate: `include gap dimension <name>? (y/n/skip-all)`. User answers form `gap_dimensions_accepted`. ctrl-C → `halt-on-user-abort`.

## Token Budget

Low. Heuristic inspection of `project_model` only; no file reads beyond what N01 already captured.

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:N (feeds N04..N09 via updated activation map, then E03).

## Back-edge Endpoints

None.
