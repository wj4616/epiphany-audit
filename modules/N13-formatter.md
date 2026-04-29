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

1. Renders YAML frontmatter per Audit Report Schema v1 (§4.1) with v2.x extensions: `input_type`, `project_content_sha256`, `contained_types`, `detector_confidence`, `section_selector_confidence`.
2. Renders top-of-body sections in order:
   - Partial-report warning (only when `token_cap_partial: true`)
   - Resolve-before-testing punch list
   - Main body: one `## Finding F00N` section per finding with **medical-diagnostic tetrad** (presenting_symptom, underlying_cause, prognosis, confidence_interval) on every finding
3. Renders Unverified Hypotheses section below main body.
4. Uses `templates/audit-report.md.template` as the rendering guide.
5. Under `--verbose`: expands rationale sections with additional examples and remediation tradeoffs.
6. Does NOT add nitpick padding under `--verbose`.

## Medical-Diagnostic Finding Tetrad (v2.x)

Every finding MUST carry all four tetrad fields, rendered as YAML within the finding block:

```yaml
presenting_symptom: string      # observable manifestation (distinct from evidence_excerpt)
underlying_cause: string        # root mechanism (distinct from rationale)
prognosis: string               # forward-looking consequence if unfixed
confidence_interval: [number, number]  # [lower, upper] both 0.0–1.0
```

**Tetrad constraints:**
- `confidence_interval` width reflects evidence strength — narrower = more evidence
- The categorical `confidence` field (HIGH/MEDIUM/LOW) remains alongside — the interval provides resolution the category cannot
- Findings missing any tetrad element are malformed and must be regenerated (enforced by N14 Pass A)

## Falsifiability-First Creativity Check (v2.x)

For every finding tagged "creative" or "novel," N13 MUST generate the strongest available counter-argument against its own finding:

1. Generate counter-argument: what is the strongest case that this finding is a false positive?
2. Evaluate: does the finding's evidence withstand the counter-argument?
3. If yes → emit finding with `falsifiability: survived` and counter-argument recorded
4. If no → drop or downgrade finding; record in falsifiability survival log

```yaml
falsifiability:
  status: "survived"              # survived | downgraded | dropped
  counter_argument: "The observed pattern could be intentional..."
  survival_rationale: "No evidence supports intentionality; tests expect different behavior..."
```

## Multi-Trial Creativity Tournament (v2.x)

For high-impact findings (severity >= HIGH or tagged "creative"), generate 3 alternative framings and rank by:
1. **Actionability** — can the user act on this framing immediately?
2. **Preservation of original intent** — does the framing preserve what the code/doc intends?
3. **Creative leverage** — does the framing open novel improvement paths beyond the immediate fix?

Emit only the top-ranked framing in the report. Trials 2 and 3 are discarded (recorded in run log only).

## Token Budget

Scales with finding count (~200 tokens per finding for formatting).

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:1 → N14 (E10).

## Back-edge Endpoints

None.
