# N13 — ReportFormatter

**Type:** formatter
**Mode:** inline
**Active in:** `audit`

## Inputs

```
prioritized_findings: Finding[]
punch_list: Finding[]
project_model: (from N01)
resolved_flags: (from N01)
```

## Outputs

```
formatted_report_markdown: string   // complete audit report markdown conforming to §4.1 template
```

## Side Effects

None (pure formatting in memory; report not yet saved — N15 handles save).

## Halt Conditions

None.

## Formatting Contract

1. Renders YAML frontmatter per Audit Report Schema v1 (§4.1).
2. Renders top-of-body sections in order:
   - Partial-report warning (only when `token_cap_partial: true`)
   - Resolve-before-testing punch list
   - Main body: one `## Finding F00N` section per finding
3. Renders Unverified Hypotheses section below main body.
4. Uses `templates/audit-report.md.template` as the rendering guide.
5. Under `--verbose`: expands rationale sections with additional examples and remediation tradeoffs.
6. Does NOT add nitpick padding under `--verbose`.

## Token Budget

Scales with finding count (~200 tokens per finding for formatting).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N14 (E10).

## Back-edge Endpoints

None.
