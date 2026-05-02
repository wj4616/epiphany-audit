---
schema_version: 2
name: correctness
display_name: Correctness
version: 1.0.0
applies_to:
  languages: "*"
  project_markers: []
  input_types: [code, specification-document, plan-document, skill, prompt, ambiguous-text]
activation_triggers:
  - type: file_present
    path: "**/*"
exclusions: []
prompt_template: |
  Analyze the target for correctness issues. The input_type is {{input_type}}.
  Adapt analysis to the input kind:
  - Code: logic errors (off-by-one, inverted boolean), type/lifetime errors,
    boundary violations, concurrency bugs, resource leaks, silently swallowed errors.
  - Specification-document / Plan-document: contradictory statements, unmet
    acceptance criteria, undefined terms, structural contradictions, broken
    cross-references, constraint violations.
  - Skill: contract contradictions between SKILL.md and module files, missing
    required fields in frontmatter, module interface violations, broken
    invocation paths, schema nonconformance.
  - Prompt: missing required tags, output-format contradictions, unhandled
    edge cases declared as covered, schema violations in embedded schemas.
  For each finding, verify the file:line via Read before reporting.
  Return findings conforming to Audit Report Schema v2.
kb_route_query: null
intra_node_token_budget: 30000
priority: high
---

# Correctness Dimension

**Floor dimension — always activated regardless of project type.**

Finds defects where the code produces wrong results, crashes, or corrupts state.
Covers the full CORRECTNESS taxonomy: logic errors, type/lifetime, boundary,
concurrency, resource leaks, and error paths.

## Failure modes (non-exhaustive)

- Loop bounds (off-by-one)
- Null/None dereference on unchecked return values
- Integer wrap/overflow in size calculations
- Race conditions on shared mutable state
- File handles / DB connections not closed on exception path
- Exception caught and silently dropped with `pass` / `catch (Exception e) {}`
- Wrong operator precedence (`a & b == c` instead of `(a & b) == c`)
- Incorrect use of mutable default arguments (Python)
