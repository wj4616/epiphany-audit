# N02 — RelevanceRouter (R-ROUTE)

**Type:** router
**Mode:** inline
**Active in:** `audit`

## Inputs

```
project_model: (from N01)
dimension_plugins: Plugin[]  // loaded at N02 startup from:
                             // (1) ~/.claude/skills/epiphany-audit/dimensions/*.md
                             // (2) ~/.config/epiphany-audit/dimensions/*.md
resolved_flags: (from N01)
```

## Outputs

```
dimension_activation_map: {
  activated: string[],
  skipped: { dimension: string, reason: string }[]
}
subtrees_activation_maps: SubtreeActivationMap[]  // only for monorepos
plugin_registry: Plugin[]          // validated, ordered
kb_prefetch_results: { [dim]: string }  // for plugins with kb_route_query
```

## Side Effects

- Read: `~/.claude/skills/epiphany-audit/dimensions/*.md`
- Read: `~/.config/epiphany-audit/dimensions/*.md` (if exists)
- Write-log: one structured event per plugin load attempt (success / validation-fail / shadowed / rejected)

## Halt Conditions

- `halt-on-floor-plugin-missing`: `correctness.md` or `maintainability.md` missing from skill-bundled `dimensions/`. Subreason: `<plugin-name>`. A floor plugin that fails schema validation also triggers this halt.

Logged, not halted:
- Plugin fails schema validation → skip and log
- Two user plugins share same `name` → alphabetical loser logged and skipped
- User plugin shadows CORRECTNESS or MAINTAINABILITY → rejected with warning

## Floor Invariant

CORRECTNESS + MAINTAINABILITY are always activated regardless of plugin presence or activation triggers. R-ROUTE cannot suppress floor dimensions.

## Loading and Shadow Rules

1. Bundled plugins: `~/.claude/skills/epiphany-audit/dimensions/*.md`
2. User plugins: `~/.config/epiphany-audit/dimensions/*.md` (loaded after; may shadow by `name`)
3. User plugin with same `name` as bundled → shadows bundled entirely (no merge)
4. CORRECTNESS and MAINTAINABILITY cannot be shadowed (warning emitted, user plugin rejected)
5. Alphabetical wins between two user plugins sharing a name

## Activation Trigger Logic (per plugin)

ALL `activation_triggers` must match for activation:
- `file_present`: path glob matches any file in project tree
- `import_grep`: pattern grepped, `min_matches` met

ANY `exclusions` match → dimension skipped.

## Token Budget

Low (directory listing + YAML plugin manifest reads). No analysis.

## Backtrack / Aggregation

None. Produces activation map consumed by N03 and N04..N09.

## Fan-out Cardinality

1:1 → N03 (E02); 1:N → N04..N09 per activation map (E03).

## Back-edge Endpoints

None.
