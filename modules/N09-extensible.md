# N09 — DimensionAnalyzer.<X> (plugin-instantiated)

**Type:** analyzer
**Mode:** inline (default); subagent under `--deep`
**Active in:** `audit`

**Note:** N09 is a template module. At runtime, R-ROUTE instantiates concrete nodes
from dimension plugins. Concrete instances receive IDs `N09.a11y`, `N09.iac-drift`,
`N09.juce-rt-safety`, etc., recorded in `graph.json` at run time.

## Inputs

```
project_model: (from N01)
file_subset: string[]
plugin_manifest: Plugin     // the loaded dimension-plugin-v1 manifest
resolved_flags: (from N01)
kb_context: string | null   // prefetched via kb-route if plugin.kb_route_query is set
```

## Outputs

```
raw_findings: Finding[]     // provenance.plugin_name = plugin.name; provenance.plugin_version = plugin.version
```

## Side Effects

Read-only. If `plugin.kb_route_query` is set, R-ROUTE prefetches KB context before N09 runs (N09 itself does not call kb-route).

## Halt Conditions

None. Plugin failures (runtime error during analysis) are caught, logged, and the node produces zero findings for that plugin instance.

## Plugin Contract

The node executes `plugin.prompt_template` with `{{project_model}}` and `{{file_subset}}` interpolated. The prompt template is responsible for defining the analysis scope. The `provenance` field on each returned finding must set `plugin_name` and `plugin_version` from the manifest.

## Token Budget

`plugin.intra_node_token_budget` (default 30k; per-plugin override in manifest).

## Backtrack / Aggregation

Participant in BACKTRACKING via N10 (single re-emit cap per plugin instance).

## Fan-out Cardinality

1:many findings per plugin instance → N10 via E05.

## Back-edge Endpoints

E06: N10 → N09.<plugin-name> (per instance).
