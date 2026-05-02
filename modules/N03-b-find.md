# N03 — BlindspotFinder (B-FIND)

**Type:** meta-analyzer
**Mode:** inline
**Active in:** `audit`

## Inputs

```
project_model: (from N01 — includes input_type set by N00b)
dimension_activation_map: (from N02 — includes per-type suppressions from the section-activation matrix)
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

## Code Gap Heuristics (v1.x, unchanged)

When `input_type == "code"`, existing heuristics remain authoritative:
- WEB-ACCESSIBILITY (web projects serving HTML)
- I18N (localized strings detected)  
- DOCUMENTATION (public API with no docstrings)
- HIGH-confidence auto-add threshold: 2+ independent heuristics agree

## Per-Type Gap Dimension Taxonomy (v2.x)

### Specification Document
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| REQUIREMENT-COMPLETENESS | Spec has requirements without corresponding acceptance criteria | >=5 requirement blocks AND 0 acceptance criteria |
| CROSS-REFERENCE-INTEGRITY | Spec references other sections | >=3 cross-references detected |
| ACCEPTANCE-CRITERIA-TESTABILITY | Acceptance criteria lack concrete pass/fail predicates | >=3 criteria with no verifiable predicate |
| DOMAIN-CONSISTENCY | Terminology drift across sections | Same concept named differently in >=2 sections |

### Plan Document
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| RISK-ASSESSMENT | Plan has no risk section | "risk"/"rollback" mentioned in <=1 location |
| ROLLBACK-PROCEDURE | Plan lacks rollback steps | `has_rollback_procedure: false` AND >=3 phases |
| DEPENDENCY-TRACEABILITY | Cross-phase dependencies not explicitly mapped | >=5 phase dependencies detected |
| ESTIMATE-CALIBRATION | Task effort estimates absent or uncalibrated | >=10 tasks with no effort markers |

### Claude Code AI Agent Skill
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| MODULE-COHERENCE | Multi-module skill without interface docs | >=3 modules detected |
| TOKEN-BUDGET-COMPLIANCE | Skill mentions token budgets | SKILL.md contains "token" keyword |
| KB-QUERY-FRESHNESS | Skill queries KBs | `kb_route_query` set on any dimension |
| SKILL-REGISTRATION-CONSISTENCY | Skill name/path mismatches across references | Skill name differs in >=2 locations |

### Detailed Prompt
| Gap Dimension | Candidate Condition | HIGH-confidence Auto-add Threshold |
|---------------|-------------------|-----------------------------------|
| VERIFICATION-SCAFFOLDING | Prompt has task/output-format but no verification | `<task>` and `<output_format>` present but no `<verification>` |
| OUTPUT-SCHEMA-COMPLETENESS | Prompt defines structured output | Structured output schema detected |
| TECHNIQUE-APPLICATION | Prompt references techniques | `<meta source="..."/>` references prompt-graph |
| CONSTRAINT-SATURATION | Prompt has constraints but some edge cases unhandled | >=5 constraints but no `<edge_cases>` section |

### Ambiguous Text
No type-specific gap dimensions. Only CORRECTNESS + MAINTAINABILITY (floor) activate. B-FIND has no additional gaps to surface for ambiguous-text inputs.

## Default Mode Behavior

AUTO-ADD HIGH-confidence gap dimensions to the activation map without prompting. The HIGH-confidence threshold is per-type (see tables above). For code, the v1.x threshold (2+ independent heuristics agree) remains unchanged.

Gap dimensions added appear in `gap_dimensions_auto_added` in the audit report frontmatter.

## `--deep` Mode Behavior

Prompt the user per gap candidate: `include gap dimension <name>? (y/n/skip-all)`. Under `--deep`, ALL gap candidates are offered interactively regardless of confidence. User answers form `gap_dimensions_accepted`. ctrl-C → `halt-on-user-abort`.

## Token Budget

Low. Heuristic inspection of `project_model` only; no file reads beyond what N01 already captured. Per-type gap tables are evaluated via boolean checks on already-populated project_model fields — no additional filesystem access.

## Backtrack / Aggregation

None.

## Fan-out Cardinality

1:N → N04..N09 via E03; 1:1 → user via E04 (interactive gap-dimension prompts, --deep only).

## Back-edge Endpoints

None.
